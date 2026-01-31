from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .instrumentation import get_langfuse_handler
from .openai_compat import (
    get_chat_openai_base_url_kwargs,
    get_openai_client_kwargs,
    get_openai_use_responses_api,
)


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BaseStructuredOutput(BaseModel):
    confidence: ConfidenceLevel = Field(description="Confidence level in the output")
    reasoning: str = Field(description="Brief reasoning for the output")

    class Config:
        use_enum_values = True


def validate_json_schema(schema: Dict[str, Any]) -> bool:
    try:
        if "properties" not in schema:
            raise ValueError("JSON schema must contain 'properties'")
        if not isinstance(schema["properties"], dict):
            raise ValueError("'properties' must be a dictionary")

        valid_types = {"string", "integer", "number", "boolean", "array", "object", "null"}
        for field_name, field_schema in schema["properties"].items():
            if not isinstance(field_schema, dict):
                raise ValueError(f"Property '{field_name}' must be a dictionary")
            if "type" not in field_schema:
                raise ValueError(f"Property '{field_name}' must have a 'type' field")
            field_type = field_schema["type"]
            # Handle array-style nullable types: ["string", "null"]
            if isinstance(field_type, list):
                for t in field_type:
                    if t not in valid_types:
                        raise ValueError(
                            f"Property '{field_name}' has invalid type in array: {t}"
                        )
            elif field_type not in valid_types:
                raise ValueError(
                    f"Property '{field_name}' has invalid type: {field_type}"
                )
            if field_schema.get("type") == "array" and "items" in field_schema:
                items_schema = field_schema["items"]
                if not isinstance(items_schema, dict):
                    raise ValueError(f"Array items for '{field_name}' must be a dictionary")
                if "type" not in items_schema:
                    raise ValueError(f"Array items for '{field_name}' must have a 'type' field")
        return True
    except Exception:
        return False


def _add_additional_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    s = dict(schema)

    # Handle array-style nullable types: {"type": ["string", "null"]}
    # This is JSON Schema draft-04/06 style nullable pattern
    if "type" in s and isinstance(s["type"], list):
        type_list = s["type"]
        has_null = "null" in type_list
        non_null_types = [t for t in type_list if t != "null"]
        if non_null_types:
            # Use the first non-null type
            s["type"] = non_null_types[0]
            if has_null:
                s["nullable"] = True

    # Convert anyOf to proper type for both Pydantic and OpenAI
    # anyOf: [{"type": "string"}, {"type": "null"}] should become type: "string" with nullable marker
    if "anyOf" in s and isinstance(s["anyOf"], list):
        # Extract the non-null type
        non_null_type = None
        has_null = False
        for item in s["anyOf"]:
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "null":
                    has_null = True
                else:
                    non_null_type = item["type"]

        # If we found a non-null type and null type, this is an optional field
        if non_null_type and has_null:
            s["type"] = non_null_type
            # Mark as nullable for OpenAI strict mode
            s["nullable"] = True
            del s["anyOf"]
        elif non_null_type:
            # Only non-null type, just use it
            s["type"] = non_null_type
            del s["anyOf"]

    if s.get("type") == "object":
        s["additionalProperties"] = False
    if "properties" in s and isinstance(s["properties"], dict):
        s["properties"] = {k: _add_additional_properties(v) for k, v in s["properties"].items()}
    if "items" in s:
        # Recursively process items
        items = s["items"]
        if isinstance(items, dict):
            # For nested arrays (array of arrays), ensure inner items also have explicit types
            processed_items = _add_additional_properties(items)

            # GPT-5.1 strict mode requires all schema nodes to have explicit "type"
            # If items is an object with properties but no type, it's implicitly type: "object"
            if "properties" in processed_items and "type" not in processed_items:
                processed_items["type"] = "object"
            # If items has nested items but no type, it's implicitly type: "array"
            elif "items" in processed_items and "type" not in processed_items:
                processed_items["type"] = "array"

            s["items"] = processed_items
        elif isinstance(items, list):
            # Handle tuple validation (rarely used)
            s["items"] = [_add_additional_properties(item) if isinstance(item, dict) else item for item in items]
    return s


def _resolve_refs(schema: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve all $ref in a JSON schema by inlining definitions.

    OpenAI's strict mode doesn't allow $ref with additional keywords, so we
    need to inline all references.
    """
    if not isinstance(schema, dict):
        return schema

    result = {}
    for key, value in schema.items():
        if key == "$ref":
            # Extract the reference name (e.g., "#/$defs/MyModel" -> "MyModel")
            ref_path = value.split("/")[-1]
            if ref_path in defs:
                # Recursively resolve the referenced schema
                resolved = _resolve_refs(defs[ref_path], defs)
                # Merge the resolved schema (skip the $ref key)
                result.update(resolved)
            else:
                result[key] = value
        elif isinstance(value, dict):
            result[key] = _resolve_refs(value, defs)
        elif isinstance(value, list):
            result[key] = [_resolve_refs(item, defs) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value

    return result


def preprocess_json_schema(
    json_schema: Dict[str, Any], enforce_all_required: bool = False
) -> Dict[str, Any]:
    s = _add_additional_properties(json_schema)
    if not enforce_all_required:
        return s

    def enforce(schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return schema
        x = dict(schema)
        if x.get("type") == "object" and isinstance(x.get("properties"), dict):
            props: Dict[str, Any] = x.get("properties", {})
            original_required = set(x.get("required", []))
            x["required"] = list(props.keys())
            for name, ps in list(props.items()):
                if name not in original_required and isinstance(ps, dict):
                    ps = dict(ps)
                    ps.setdefault("nullable", True)
                    props[name] = ps
                props[name] = enforce(props[name])
        if "items" in x:
            x["items"] = enforce(x["items"])  # type: ignore
        return x

    return enforce(s)


def build_model_from_schema(
    schema_name: str,
    json_schema: Dict[str, Any],
    base: Type[BaseModel] | None = None,
) -> Type[BaseModel]:
    base = base or BaseStructuredOutput

    class StrictBase(base):  # type: ignore
        class Config:
            extra = "forbid"

    def _py_type(t: str):
        return {"string": str, "integer": int, "number": float, "boolean": bool}.get(t, Any)

    def _build(node_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        props = schema.get("properties", {}) or {}
        required = set(schema.get("required", []))
        fields: Dict[str, tuple] = {}
        for fname, fs in props.items():
            ftype = fs.get("type")
            ann: Any
            default = ... if fname in required else None
            desc = fs.get("description", f"Field: {fname}")

            if ftype == "object":
                sub = _build(f"{node_name}_{fname.capitalize()}", fs)
                ann = sub if fname in required else Optional[sub]  # type: ignore
            elif ftype == "array":
                items = fs.get("items", {}) or {}
                if items.get("type") == "object":
                    sub = _build(f"{node_name}_{fname.capitalize()}Item", items)
                    ann = list[sub]  # type: ignore
                elif "type" in items:
                    ann = list[_py_type(items["type"])]  # type: ignore
                else:
                    ann = list[Any]
                if fname not in required:
                    from typing import Optional as Opt

                    ann = Opt[ann]  # type: ignore
            else:
                ann = _py_type(ftype)
                if fname not in required:
                    from typing import Optional as Opt

                    ann = Opt[ann]  # type: ignore
            fields[fname] = (ann, Field(default=default, description=desc))

        return create_model(node_name, __base__=StrictBase, **fields)

    payload = _build(f"{schema_name}Payload", json_schema)
    # Inline payload fields on output model so they appear at top-level
    out_fields: Dict[str, tuple] = {}
    for field_name, f in payload.model_fields.items():
        out_fields[field_name] = (
            f.annotation,
            Field(default=(... if f.is_required() else None)),
        )
    return create_model(schema_name, __base__=StrictBase, **out_fields)


def create_dynamic_schema(schema_name: str, json_schema: Dict[str, Any]) -> Type[BaseModel]:
    """Back-compat helper that mirrors existing services' API.

    Builds a strict Pydantic model from the given JSON schema that extends
    BaseStructuredOutput and forbids extra properties.
    """
    pre = preprocess_json_schema(json_schema)
    return build_model_from_schema(schema_name, pre, base=BaseStructuredOutput)


class StructuredOutputGenerator:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self._langfuse_handler = get_langfuse_handler()
        callbacks = [self._langfuse_handler] if self._langfuse_handler else None
        use_responses_api = get_openai_use_responses_api()
        llm_kwargs = {
            "model": model or "gpt-4.1-mini",
            "temperature": 0,
            "api_key": api_key,
            "use_responses_api": use_responses_api,
            "callbacks": callbacks,
            **get_chat_openai_base_url_kwargs(ChatOpenAI),
        }
        if use_responses_api:
            llm_kwargs["output_version"] = "responses/v1"
        self._llm = ChatOpenAI(**llm_kwargs)

    async def generate_from_model(
        self, prompt: str, schema_model: Type[BaseModel], system: Optional[str] = None
    ) -> BaseModel:
        tmpl = ChatPromptTemplate.from_messages(
            [
                ("system", system or "You output ONLY valid JSON for the given schema."),
                ("human", "{input}"),
            ]
        )
        chain = tmpl | self._llm.with_structured_output(schema_model)
        config = {"callbacks": [self._langfuse_handler]} if self._langfuse_handler else None
        return await chain.ainvoke({"input": prompt}, config=config)

    async def generate_from_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        schema_name: str = "StructuredOutput",
        system: Optional[str] = None,
        enforce_all_required: bool = False,
        base: Type[BaseModel] | None = None,
    ) -> BaseModel:
        pre = preprocess_json_schema(json_schema, enforce_all_required=enforce_all_required)
        model = build_model_from_schema(schema_name, pre, base=base)
        return await self.generate_from_model(prompt, model, system=system)


async def extract_structured_gpt51(
    *,
    text: str,
    json_schema: Dict[str, Any],
    schema_name: str = "DynamicSchema",
    prompt: Optional[str] = None,
    system: Optional[str] = None,
    model: str = "gpt-5.1-2025-11-13",
    api_key: Optional[str] = None,
    reasoning_effort: str = "medium",
    cache: Optional[Any] = None,
    cache_key: Optional[str] = None,
) -> BaseModel:
    """Extract structured output using GPT-5.1 with reasoning_effort control.

    This method is optimized for GPT-5.1 and uses the Responses API with
    reasoning_effort parameter for better control over speed vs. intelligence.

    Args:
        text: Input text to extract structured data from
        json_schema: JSON schema defining the structure to extract
        schema_name: Name for the dynamically created Pydantic model
        prompt: Optional additional context/instructions
        system: Optional system message (uses default if not provided)
        model: Model to use (default: "gpt-5.1")
        api_key: Optional OpenAI API key (uses env var if not provided)
        reasoning_effort: Reasoning effort level for GPT-5.1
            - "none": Fast, no reasoning (default for structured output)
            - "low": Light reasoning
            - "medium": Moderate reasoning
            - "high": Deep reasoning
        cache: Optional cache implementation
        cache_key: Optional cache key

    Returns:
        BaseModel: Pydantic model instance with extracted data

    Example:
        ```python
        schema = {
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        result = await extract_structured_gpt51(
            text="John is 25 years old",
            json_schema=schema,
            schema_name="Person",
            reasoning_effort="none"  # Fast extraction
        )
        ```
    """
    import logging
    from openai import OpenAI

    logger = logging.getLogger(__name__)

    # Try cache first (if provided)
    if cache and cache_key:
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            # For GPT-5.1 strict mode, enforce all properties as required
            pre = preprocess_json_schema(json_schema, enforce_all_required=True)
            from pydantic import BaseModel as PydanticBaseModel
            model_cls = build_model_from_schema(schema_name, pre, base=PydanticBaseModel)
            return model_cls(**cached_result)

    # Preprocess schema for GPT-5.1 strict mode
    pre = preprocess_json_schema(json_schema, enforce_all_required=True)

    # Prepare the prompt
    sys_msg = system or (
        "You are a helpful AI assistant that extracts information from text based on a provided JSON schema. "
        "You produce only valid JSON per the bound schema. If a field is not found, omit it when optional or set null if allowed. Do not invent values."
    )
    user_msg = f"Text to analyze:\n{text}"
    if prompt:
        user_msg += f"\n\n{prompt}"

    # Use OpenAI client directly for Responses API
    client = OpenAI(api_key=api_key, **get_openai_client_kwargs())

    # Use the preprocessed schema directly (bypass Pydantic to preserve nested arrays)
    # Pydantic doesn't handle array-of-arrays properly - it converts to empty items: {}
    response_format = dict(pre)

    # Resolve any $ref if present
    if '$defs' in response_format:
        defs = response_format.pop('$defs')
        response_format = _resolve_refs(response_format, defs)

    # Ensure it has title (required by OpenAI)
    if 'title' not in response_format:
        response_format['title'] = schema_name

    # OpenAI strict mode requires ALL properties to be in required array
    # Add enforce_all_required logic to the resolved schema
    def enforce_strict_required(schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return schema
        s = dict(schema)
        if s.get("type") == "object" and isinstance(s.get("properties"), dict):
            props = dict(s.get("properties", {}))
            # Make all properties required for strict mode
            s["required"] = list(props.keys())
            # Recursively enforce on nested objects
            for prop_name, prop_schema in props.items():
                props[prop_name] = enforce_strict_required(prop_schema)
            s["properties"] = props
        if "items" in s and isinstance(s["items"], dict):
            items = enforce_strict_required(s["items"])
            # GPT-5.1 strict mode requires all schema nodes to have explicit "type"
            # If items is an object with properties but no type, it's implicitly type: "object"
            if "properties" in items and "type" not in items:
                items["type"] = "object"
            # If items has nested items but no type, it's implicitly type: "array"
            elif "items" in items and "type" not in items:
                items["type"] = "array"
            s["items"] = items
        return s

    response_format = enforce_strict_required(response_format)

    # Debug: Log the final schema being sent to OpenAI
    logger.info(f"Final schema for OpenAI (after enforce_strict_required): {response_format}")

    try:
        # Use Responses API with reasoning_effort
        # Note: GPT-5.1 does not support temperature, top_p, or max_tokens
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            reasoning={"effort": reasoning_effort},
            max_output_tokens=100000,  # GPT-5.1 max output is 100K tokens
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": response_format
                }
            },
        )

        # Extract the JSON output
        output_text = response.output_text
        import json
        result_dict = json.loads(output_text)

        # Build a minimal Pydantic model to wrap the result (without BaseStructuredOutput base)
        # We use the original schema structure to maintain nested arrays
        # BaseModel is used instead of BaseStructuredOutput to avoid requiring confidence/reasoning fields
        from pydantic import BaseModel as PydanticBaseModel
        model_cls = build_model_from_schema(schema_name, pre, base=PydanticBaseModel)
        result = model_cls(**result_dict)

        # Store in cache (if provided)
        if cache and cache_key:
            result_dict_cache = result.model_dump() if hasattr(result, "model_dump") else result.dict()
            await cache.set(cache_key, result_dict_cache)
            logger.debug(f"Cached result for key: {cache_key[:16]}...")

        return result

    except Exception as e:
        logger.error(f"GPT-5.1 structured extraction failed: {e}")
        raise


async def extract_structured(
    *,
    text: str,
    json_schema: Dict[str, Any],
    schema_name: str = "DynamicSchema",
    prompt: Optional[str] = None,
    system: Optional[str] = None,
    enforce_all_required: bool = False,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    cache: Optional[Any] = None,
    cache_key: Optional[str] = None,
) -> BaseModel:
    """High-level helper: from text + JSON Schema to structured model in one call.

    - Builds a strict Pydantic model (extras=forbid) from the JSON Schema.
    - Uses a default system instruction if not provided.
    - Concatenates optional `prompt` after the text for extra guidance.

    Args:
        text: Input text to extract structured data from
        json_schema: JSON schema defining the structure to extract
        schema_name: Name for the dynamically created Pydantic model
        prompt: Optional additional context/instructions
        system: Optional system message (uses default if not provided)
        enforce_all_required: Whether to enforce all properties as required
        model: Model to use (default: "gpt-4.1-mini")
        api_key: Optional OpenAI API key (uses env var if not provided)
        reasoning_effort: Reasoning effort level (only used for GPT-5.* models)
            - If model is gpt-5.* and reasoning_effort not provided, defaults to "low"
            - Ignored for non-GPT-5.* models (e.g., gpt-4.1-mini)
        cache: Optional cache implementation (follows LLMCache protocol)
        cache_key: Optional pre-computed cache key. If not provided and cache
                   is given, caller should generate key before calling.

    Note:
        The library does NOT generate cache keys. Services should generate
        keys based on their specific needs (text, schema, prompt, etc.)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Determine which model to use
    model_to_use = model or "gpt-4.1-mini"

    # Check if this is a GPT-5.* model
    is_gpt5 = model_to_use.startswith("gpt-5")

    # For GPT-5.* models, use the specialized function with reasoning_effort
    if is_gpt5:
        # Default reasoning_effort to "low" if not provided for GPT-5.* models
        effort = reasoning_effort or "low"
        logger.debug(f"Using GPT-5.* model with reasoning_effort={effort}")
        return await extract_structured_gpt51(
            text=text,
            json_schema=json_schema,
            schema_name=schema_name,
            prompt=prompt,
            system=system,
            model=model_to_use,
            api_key=api_key,
            reasoning_effort=effort,
            cache=cache,
            cache_key=cache_key,
        )

    # For non-GPT-5.* models (e.g., gpt-4.1-mini), use the legacy path
    # reasoning_effort is ignored for these models
    if reasoning_effort:
        logger.warning(
            f"reasoning_effort={reasoning_effort} provided but model={model_to_use} "
            "does not support it. Ignoring reasoning_effort."
        )

    # Try cache first (if provided)
    if cache and cache_key:
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            # Reconstruct Pydantic model from cached dict
            pre = preprocess_json_schema(json_schema, enforce_all_required)
            model_cls = build_model_from_schema(schema_name, pre)
            return model_cls(**cached_result)

    # Cache miss or no cache - proceed with LLM call
    gen = StructuredOutputGenerator(model=model_to_use, api_key=api_key)
    pre = preprocess_json_schema(json_schema, enforce_all_required=enforce_all_required)
    model_cls = build_model_from_schema(schema_name, pre)
    sys_msg = system or (
        "You are a helpful AI assistant that extracts information from text based on a provided JSON schema. "
        "You produce only valid JSON per the bound schema. If a field is not found, omit it when optional or set null if allowed. Do not invent values."
    )
    user = f"Text to analyze:\n{text}\n\n{prompt or ''}"
    result = await gen.generate_from_model(prompt=user, schema_model=model_cls, system=sys_msg)

    # Store in cache (if provided)
    if cache and cache_key:
        # Convert Pydantic model to dict for caching
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
        await cache.set(cache_key, result_dict)
        logger.debug(f"Cached result for key: {cache_key[:16]}...")

    return result
