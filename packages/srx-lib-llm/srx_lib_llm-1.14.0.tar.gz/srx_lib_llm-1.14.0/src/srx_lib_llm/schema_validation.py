"""OpenAI Structured Outputs JSON Schema Validation.

This module provides comprehensive validation for JSON schemas used with OpenAI's
Structured Outputs feature (Batch API, Chat Completions API, Assistants API).

Validation is ONLY enforced for GPT-5* models. Other models pass through unchanged.

Example:
    >>> from srx_lib_llm.schema_validation import validate_strict_schema, StrictSchemaValidator
    >>>
    >>> # Validate a schema for GPT-5 strict mode
    >>> errors = validate_strict_schema(my_schema, model="gpt-5-mini")
    >>> if errors:
    ...     for error in errors:
    ...         print(f"{error.code}: {error.message}")
    ...         print(f"  Path: {error.path}")
    ...         print(f"  Fix: {error.fix}")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class SchemaErrorCode(str, Enum):
    """Error codes for schema validation failures.

    Each code maps to a specific validation rule violation in OpenAI's
    strict mode for Structured Outputs.
    """

    # Strict mode configuration
    STRICT_MODE_NOT_ENABLED = "STRICT_MODE_NOT_ENABLED"

    # Object structure
    MISSING_ADDITIONAL_PROPERTIES_FALSE = "MISSING_ADDITIONAL_PROPERTIES_FALSE"
    PROPERTY_NOT_IN_REQUIRED = "PROPERTY_NOT_IN_REQUIRED"
    OPTIONAL_FIELD_NOT_NULLABLE = "OPTIONAL_FIELD_NOT_NULLABLE"

    # Tool configuration
    PARALLEL_TOOL_CALLS_WITH_STRICT = "PARALLEL_TOOL_CALLS_WITH_STRICT"

    # Forbidden keywords
    FORBIDDEN_KEYWORD_ONEOF = "FORBIDDEN_KEYWORD_ONEOF"

    # Unsupported constraints
    UNSUPPORTED_STRING_CONSTRAINT = "UNSUPPORTED_STRING_CONSTRAINT"
    UNSUPPORTED_NUMBER_CONSTRAINT = "UNSUPPORTED_NUMBER_CONSTRAINT"
    UNSUPPORTED_OBJECT_CONSTRAINT = "UNSUPPORTED_OBJECT_CONSTRAINT"
    UNSUPPORTED_ARRAY_CONSTRAINT = "UNSUPPORTED_ARRAY_CONSTRAINT"
    UNSUPPORTED_DEFAULT_KEYWORD = "UNSUPPORTED_DEFAULT_KEYWORD"

    # Type issues
    INVALID_TYPE = "INVALID_TYPE"
    MISSING_TYPE = "MISSING_TYPE"
    MISSING_ITEMS = "MISSING_ITEMS"

    # Reference issues
    INVALID_REF = "INVALID_REF"
    UNRESOLVED_REF = "UNRESOLVED_REF"

    # Schema structure
    MISSING_PROPERTIES = "MISSING_PROPERTIES"
    EMPTY_REQUIRED_ARRAY = "EMPTY_REQUIRED_ARRAY"
    INVALID_SCHEMA_STRUCTURE = "INVALID_SCHEMA_STRUCTURE"


@dataclass
class SchemaValidationError:
    """Detailed error information for schema validation failures.

    Attributes:
        code: Machine-readable error code from SchemaErrorCode enum.
        message: Human-readable description of the error.
        path: JSON path to the problematic location (e.g., "properties.user.properties.name").
        value: The actual value that caused the error.
        fix: Suggested fix for the error.
        severity: "error" for blocking issues, "warning" for recommendations.
    """

    code: SchemaErrorCode
    message: str
    path: str
    value: Any = None
    fix: str = ""
    severity: str = "error"

    def __str__(self) -> str:
        parts = [f"[{self.code.value}] {self.message}"]
        if self.path:
            parts.append(f"  Path: {self.path}")
        if self.value is not None:
            value_str = str(self.value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            parts.append(f"  Value: {value_str}")
        if self.fix:
            parts.append(f"  Fix: {self.fix}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "path": self.path,
            "value": self.value,
            "fix": self.fix,
            "severity": self.severity,
        }


class SchemaValidationException(Exception):
    """Exception raised when schema validation fails.

    Attributes:
        errors: List of validation errors found.
        model: The model being validated for.
    """

    def __init__(
        self,
        errors: List[SchemaValidationError],
        model: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.errors = errors
        self.model = model
        self.error_count = len(errors)

        if message:
            self.message = message
        else:
            self.message = self._build_message()

        super().__init__(self.message)

    def _build_message(self) -> str:
        """Build detailed error message."""
        lines = [
            f"Schema validation failed with {self.error_count} error(s)"
            + (f" for model '{self.model}'" if self.model else "")
            + ":",
            "",
        ]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"Error {i}:")
            lines.append(str(error))
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "SchemaValidationException",
            "message": f"Schema validation failed with {self.error_count} error(s)",
            "model": self.model,
            "error_count": self.error_count,
            "errors": [e.to_dict() for e in self.errors],
        }


# Valid JSON Schema types for OpenAI strict mode
VALID_TYPES: Set[str] = {"object", "array", "string", "number", "integer", "boolean", "null"}

# Forbidden keywords that cause hard errors
FORBIDDEN_KEYWORDS: Set[str] = {"oneOf"}

# String constraints not supported in strict mode
UNSUPPORTED_STRING_KEYWORDS: Set[str] = {"minLength", "maxLength", "pattern", "format"}

# Number constraints not supported in strict mode
UNSUPPORTED_NUMBER_KEYWORDS: Set[str] = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"}

# Object constraints not supported in strict mode
UNSUPPORTED_OBJECT_KEYWORDS: Set[str] = {
    "patternProperties",
    "unevaluatedProperties",
    "propertyNames",
    "minProperties",
    "maxProperties",
}

# Array constraints not supported in strict mode
UNSUPPORTED_ARRAY_KEYWORDS: Set[str] = {"contains", "minItems", "maxItems", "uniqueItems", "unevaluatedItems", "minContains", "maxContains"}


def is_gpt5_model(model: Optional[str]) -> bool:
    """Check if model is GPT-5 family (requires strict mode validation).

    Args:
        model: Model name/ID string.

    Returns:
        True if model is GPT-5 family, False otherwise.

    Examples:
        >>> is_gpt5_model("gpt-5")
        True
        >>> is_gpt5_model("gpt-5-mini")
        True
        >>> is_gpt5_model("gpt-5.1-mini-2025-08-07")
        True
        >>> is_gpt5_model("gpt-4-turbo")
        False
        >>> is_gpt5_model("gpt-4o")
        False
        >>> is_gpt5_model(None)
        False
    """
    if not model:
        return False
    return model.startswith("gpt-5")


class StrictSchemaValidator:
    """Validator for OpenAI Structured Outputs strict mode schemas.

    This validator checks JSON schemas against OpenAI's strict mode requirements
    and provides detailed, actionable error messages.

    Only validates for GPT-5* models. Other models bypass validation.

    Example:
        >>> validator = StrictSchemaValidator(model="gpt-5-mini")
        >>> errors = validator.validate(my_schema)
        >>> if errors:
        ...     raise SchemaValidationException(errors, model="gpt-5-mini")
    """

    def __init__(self, model: Optional[str] = None, strict: bool = True):
        """Initialize the validator.

        Args:
            model: Model name. If not GPT-5*, validation is skipped.
            strict: Whether strict mode is enabled. Default True.
        """
        self.model = model
        self.strict = strict
        self.errors: List[SchemaValidationError] = []
        self._defs: Dict[str, Any] = {}

    def validate(self, schema: Dict[str, Any]) -> List[SchemaValidationError]:
        """Validate a JSON schema for OpenAI strict mode compatibility.

        Args:
            schema: The JSON schema to validate.

        Returns:
            List of validation errors. Empty list if valid.
        """
        self.errors = []

        # Skip validation for non-GPT-5 models
        if not is_gpt5_model(self.model):
            return []

        # Store $defs for reference resolution
        self._defs = schema.get("$defs", schema.get("definitions", {}))

        # Validate the schema recursively
        self._validate_schema_node(schema, "")

        return self.errors

    def validate_or_raise(self, schema: Dict[str, Any]) -> None:
        """Validate schema and raise exception if invalid.

        Args:
            schema: The JSON schema to validate.

        Raises:
            SchemaValidationException: If validation fails.
        """
        errors = self.validate(schema)
        if errors:
            raise SchemaValidationException(errors, model=self.model)

    def _add_error(
        self,
        code: SchemaErrorCode,
        message: str,
        path: str,
        value: Any = None,
        fix: str = "",
        severity: str = "error",
    ) -> None:
        """Add a validation error."""
        self.errors.append(
            SchemaValidationError(
                code=code,
                message=message,
                path=path,
                value=value,
                fix=fix,
                severity=severity,
            )
        )

    def _validate_schema_node(self, node: Any, path: str) -> None:
        """Recursively validate a schema node.

        Args:
            node: The schema node to validate.
            path: JSON path to this node.
        """
        if not isinstance(node, dict):
            return

        # Check for $ref
        if "$ref" in node:
            self._validate_ref(node, path)
            return

        # Check for forbidden keywords
        self._check_forbidden_keywords(node, path)

        # Check for unsupported constraints
        self._check_unsupported_constraints(node, path)

        # Check for default keyword
        if "default" in node:
            self._add_error(
                code=SchemaErrorCode.UNSUPPORTED_DEFAULT_KEYWORD,
                message="The 'default' keyword is not supported in strict mode.",
                path=path,
                value=node["default"],
                fix="Remove the 'default' keyword. Handle defaults in application code.",
            )

        # Get the type(s) for this node
        node_type = node.get("type")

        # Handle array-style types: ["string", "null"]
        if isinstance(node_type, list):
            # Validate each type in the array
            for t in node_type:
                if t not in VALID_TYPES:
                    self._add_error(
                        code=SchemaErrorCode.INVALID_TYPE,
                        message=f"Invalid type '{t}' in type array.",
                        path=f"{path}.type",
                        value=node_type,
                        fix=f"Use one of: {', '.join(sorted(VALID_TYPES))}",
                    )
            # Use the first non-null type for further validation
            non_null_types = [t for t in node_type if t != "null"]
            if non_null_types:
                node_type = non_null_types[0]
            else:
                node_type = "null"

        # Validate based on type
        if node_type == "object":
            self._validate_object(node, path)
        elif node_type == "array":
            self._validate_array(node, path)
        elif node_type and node_type not in VALID_TYPES:
            self._add_error(
                code=SchemaErrorCode.INVALID_TYPE,
                message=f"Invalid type '{node_type}'.",
                path=f"{path}.type" if path else "type",
                value=node_type,
                fix=f"Use one of: {', '.join(sorted(VALID_TYPES))}",
            )

        # Check if schema has properties but no type (implicit object)
        if "properties" in node and "type" not in node:
            self._add_error(
                code=SchemaErrorCode.MISSING_TYPE,
                message="Schema with 'properties' must have explicit 'type: object'.",
                path=path,
                value={"has_properties": True, "type": None},
                fix="Add 'type': 'object' to the schema.",
            )
            # Still validate as object
            self._validate_object(node, path)

        # Check if schema has items but no type (implicit array)
        if "items" in node and "type" not in node:
            self._add_error(
                code=SchemaErrorCode.MISSING_TYPE,
                message="Schema with 'items' must have explicit 'type: array'.",
                path=path,
                value={"has_items": True, "type": None},
                fix="Add 'type': 'array' to the schema.",
            )

        # Handle anyOf (check if it's a nullable pattern)
        if "anyOf" in node:
            self._validate_anyof(node, path)

    def _validate_object(self, node: Dict[str, Any], path: str) -> None:
        """Validate an object schema node.

        Args:
            node: Object schema node.
            path: JSON path to this node.
        """
        properties = node.get("properties", {})
        required = set(node.get("required", []))

        # Check for additionalProperties: false
        if "additionalProperties" not in node:
            self._add_error(
                code=SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE,
                message="Object schema must have 'additionalProperties: false' in strict mode.",
                path=path,
                value={"properties": list(properties.keys()), "additionalProperties": "missing"},
                fix="Add 'additionalProperties': false to the object schema.",
            )
        elif node.get("additionalProperties") is not False:
            self._add_error(
                code=SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE,
                message="Object schema must have 'additionalProperties: false' (not true or schema) in strict mode.",
                path=f"{path}.additionalProperties",
                value=node.get("additionalProperties"),
                fix="Set 'additionalProperties': false.",
            )

        # Check that all properties are in required
        if properties:
            missing_required = set(properties.keys()) - required
            if missing_required:
                for prop_name in sorted(missing_required):
                    prop_path = f"{path}.properties.{prop_name}" if path else f"properties.{prop_name}"
                    prop_schema = properties[prop_name]

                    # Check if the property allows null
                    prop_type = prop_schema.get("type") if isinstance(prop_schema, dict) else None
                    is_nullable = (
                        isinstance(prop_type, list) and "null" in prop_type
                    ) or prop_schema.get("nullable", False)

                    if is_nullable:
                        # Property is nullable but not in required - this is the correct pattern
                        # but OpenAI strict mode still requires it in required array
                        self._add_error(
                            code=SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED,
                            message=f"Property '{prop_name}' must be in 'required' array (it's nullable, which is correct for optional fields).",
                            path=f"{path}.required" if path else "required",
                            value={"property": prop_name, "type": prop_type, "nullable": True},
                            fix=f"Add '{prop_name}' to the 'required' array. The nullable type already allows null values.",
                        )
                    else:
                        self._add_error(
                            code=SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED,
                            message=f"Property '{prop_name}' is in 'properties' but not in 'required'. In strict mode, ALL properties must be required.",
                            path=f"{path}.required" if path else "required",
                            value={"property": prop_name, "in_required": False},
                            fix=f"Add '{prop_name}' to the 'required' array. If it should be optional, also change its type to [\"<type>\", \"null\"].",
                        )

        # Recursively validate properties
        for prop_name, prop_schema in properties.items():
            prop_path = f"{path}.properties.{prop_name}" if path else f"properties.{prop_name}"
            self._validate_schema_node(prop_schema, prop_path)

    def _validate_array(self, node: Dict[str, Any], path: str) -> None:
        """Validate an array schema node.

        Args:
            node: Array schema node.
            path: JSON path to this node.
        """
        if "items" not in node:
            self._add_error(
                code=SchemaErrorCode.MISSING_ITEMS,
                message="Array schema must have 'items' definition in strict mode.",
                path=path,
                value={"type": "array", "items": "missing"},
                fix="Add 'items' schema defining the array element type.",
            )
            return

        items = node["items"]
        items_path = f"{path}.items" if path else "items"

        # Handle items as an array (tuple validation)
        if isinstance(items, list):
            for i, item_schema in enumerate(items):
                self._validate_schema_node(item_schema, f"{items_path}[{i}]")
        else:
            self._validate_schema_node(items, items_path)

    def _validate_anyof(self, node: Dict[str, Any], path: str) -> None:
        """Validate anyOf constructs.

        OpenAI strict mode has limited support for anyOf. The common pattern
        is using it for nullable types: anyOf: [{type: X}, {type: null}].

        Args:
            node: Schema node containing anyOf.
            path: JSON path to this node.
        """
        any_of = node.get("anyOf", [])

        # Check if this is a simple nullable pattern
        if len(any_of) == 2:
            types = [item.get("type") for item in any_of if isinstance(item, dict)]
            if "null" in types:
                # This is a nullable pattern - validate the non-null type
                for item in any_of:
                    if isinstance(item, dict) and item.get("type") != "null":
                        self._validate_schema_node(item, path)
                return

        # More complex anyOf - validate each branch but warn
        for i, item in enumerate(any_of):
            self._validate_schema_node(item, f"{path}.anyOf[{i}]")

    def _validate_ref(self, node: Dict[str, Any], path: str) -> None:
        """Validate $ref usage.

        Args:
            node: Schema node containing $ref.
            path: JSON path to this node.
        """
        ref = node.get("$ref", "")

        # Check for external references
        if ref.startswith("http://") or ref.startswith("https://"):
            self._add_error(
                code=SchemaErrorCode.INVALID_REF,
                message="External $ref URLs are not supported. Only internal references allowed.",
                path=f"{path}.$ref",
                value=ref,
                fix="Use internal references to $defs only (e.g., '#/$defs/MyType').",
            )
            return

        # Check if it's a valid internal reference
        if ref.startswith("#/$defs/") or ref.startswith("#/definitions/"):
            ref_name = ref.split("/")[-1]
            if ref_name not in self._defs:
                self._add_error(
                    code=SchemaErrorCode.UNRESOLVED_REF,
                    message=f"Reference '{ref}' not found in $defs.",
                    path=f"{path}.$ref",
                    value=ref,
                    fix=f"Ensure '{ref_name}' is defined in $defs or definitions.",
                )
        elif ref.startswith("#/"):
            # Other internal reference - might be valid
            pass
        else:
            self._add_error(
                code=SchemaErrorCode.INVALID_REF,
                message=f"Invalid $ref format: '{ref}'.",
                path=f"{path}.$ref",
                value=ref,
                fix="Use format '#/$defs/TypeName' for internal references.",
            )

        # Check if $ref has additional keywords (not supported in strict mode)
        extra_keys = set(node.keys()) - {"$ref"}
        if extra_keys:
            self._add_error(
                code=SchemaErrorCode.INVALID_REF,
                message=f"$ref cannot have additional keywords in strict mode: {sorted(extra_keys)}",
                path=path,
                value={"ref": ref, "extra_keys": list(extra_keys)},
                fix="Inline the referenced schema instead of using $ref with overrides.",
            )

    def _check_forbidden_keywords(self, node: Dict[str, Any], path: str) -> None:
        """Check for forbidden keywords.

        Args:
            node: Schema node to check.
            path: JSON path to this node.
        """
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in node:
                self._add_error(
                    code=SchemaErrorCode.FORBIDDEN_KEYWORD_ONEOF,
                    message=f"The '{keyword}' keyword is not supported in strict mode.",
                    path=f"{path}.{keyword}" if path else keyword,
                    value=node[keyword],
                    fix=f"Remove '{keyword}' and restructure the schema. Consider using separate schemas or enum types.",
                )

    def _check_unsupported_constraints(self, node: Dict[str, Any], path: str) -> None:
        """Check for unsupported constraint keywords.

        Args:
            node: Schema node to check.
            path: JSON path to this node.
        """
        node_type = node.get("type")

        # Handle array-style types
        if isinstance(node_type, list):
            non_null_types = [t for t in node_type if t != "null"]
            node_type = non_null_types[0] if non_null_types else None

        # String constraints
        for keyword in UNSUPPORTED_STRING_KEYWORDS:
            if keyword in node:
                self._add_error(
                    code=SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT,
                    message=f"String constraint '{keyword}' is not supported in strict mode.",
                    path=f"{path}.{keyword}" if path else keyword,
                    value=node[keyword],
                    fix=f"Remove '{keyword}'. Validate string constraints in application code after parsing.",
                )

        # Number constraints
        for keyword in UNSUPPORTED_NUMBER_KEYWORDS:
            if keyword in node:
                self._add_error(
                    code=SchemaErrorCode.UNSUPPORTED_NUMBER_CONSTRAINT,
                    message=f"Number constraint '{keyword}' is not supported in strict mode.",
                    path=f"{path}.{keyword}" if path else keyword,
                    value=node[keyword],
                    fix=f"Remove '{keyword}'. Validate number constraints in application code after parsing.",
                )

        # Object constraints
        for keyword in UNSUPPORTED_OBJECT_KEYWORDS:
            if keyword in node:
                self._add_error(
                    code=SchemaErrorCode.UNSUPPORTED_OBJECT_CONSTRAINT,
                    message=f"Object constraint '{keyword}' is not supported in strict mode.",
                    path=f"{path}.{keyword}" if path else keyword,
                    value=node[keyword],
                    fix=f"Remove '{keyword}'. Validate object constraints in application code after parsing.",
                )

        # Array constraints
        for keyword in UNSUPPORTED_ARRAY_KEYWORDS:
            if keyword in node:
                self._add_error(
                    code=SchemaErrorCode.UNSUPPORTED_ARRAY_CONSTRAINT,
                    message=f"Array constraint '{keyword}' is not supported in strict mode.",
                    path=f"{path}.{keyword}" if path else keyword,
                    value=node[keyword],
                    fix=f"Remove '{keyword}'. Validate array constraints in application code after parsing.",
                )


def validate_strict_schema(
    schema: Dict[str, Any],
    model: Optional[str] = None,
    raise_on_error: bool = False,
) -> List[SchemaValidationError]:
    """Validate a JSON schema for OpenAI strict mode compatibility.

    This is the main entry point for schema validation. It only applies
    validation rules for GPT-5* models.

    Args:
        schema: The JSON schema to validate.
        model: Model name. If not GPT-5*, validation is skipped.
        raise_on_error: If True, raises SchemaValidationException on errors.

    Returns:
        List of validation errors. Empty list if valid or non-GPT-5 model.

    Raises:
        SchemaValidationException: If raise_on_error=True and validation fails.

    Example:
        >>> errors = validate_strict_schema(
        ...     {
        ...         "type": "object",
        ...         "properties": {"name": {"type": "string"}},
        ...         "required": ["name"]
        ...     },
        ...     model="gpt-5-mini"
        ... )
        >>> if errors:
        ...     print(f"Found {len(errors)} error(s)")
    """
    validator = StrictSchemaValidator(model=model)
    errors = validator.validate(schema)

    if raise_on_error and errors:
        raise SchemaValidationException(errors, model=model)

    return errors


def validate_batch_request(
    request: Dict[str, Any],
    model: Optional[str] = None,
) -> List[SchemaValidationError]:
    """Validate a Batch API request for strict mode compatibility.

    Checks both the request structure and any embedded JSON schemas
    in response_format or tool definitions.

    Args:
        request: Batch API request body.
        model: Model name override. If not provided, extracted from request.

    Returns:
        List of validation errors.

    Example:
        >>> request = {
        ...     "custom_id": "req-1",
        ...     "method": "POST",
        ...     "url": "/v1/chat/completions",
        ...     "body": {
        ...         "model": "gpt-5-mini",
        ...         "messages": [...],
        ...         "response_format": {...}
        ...     }
        ... }
        >>> errors = validate_batch_request(request)
    """
    errors: List[SchemaValidationError] = []

    body = request.get("body", {})
    request_model = model or body.get("model")

    # Skip validation for non-GPT-5 models
    if not is_gpt5_model(request_model):
        return errors

    # Validate response_format schema
    response_format = body.get("response_format", {})
    if response_format.get("type") == "json_schema":
        json_schema = response_format.get("json_schema", {})
        schema = json_schema.get("schema", {})

        # Check strict mode
        if not json_schema.get("strict", False):
            errors.append(
                SchemaValidationError(
                    code=SchemaErrorCode.STRICT_MODE_NOT_ENABLED,
                    message="response_format.json_schema.strict must be true for GPT-5 models.",
                    path="body.response_format.json_schema.strict",
                    value=json_schema.get("strict"),
                    fix="Set 'strict': true in json_schema configuration.",
                )
            )

        # Validate the schema itself
        validator = StrictSchemaValidator(model=request_model)
        schema_errors = validator.validate(schema)
        for err in schema_errors:
            err.path = f"body.response_format.json_schema.schema.{err.path}".rstrip(".")
        errors.extend(schema_errors)

    # Validate tool schemas
    tools = body.get("tools", [])
    parallel_tool_calls = body.get("parallel_tool_calls", True)
    has_strict_tools = False

    for i, tool in enumerate(tools):
        if tool.get("type") == "function":
            func = tool.get("function", {})
            if func.get("strict", False):
                has_strict_tools = True
                parameters = func.get("parameters", {})

                validator = StrictSchemaValidator(model=request_model)
                schema_errors = validator.validate(parameters)
                for err in schema_errors:
                    err.path = f"body.tools[{i}].function.parameters.{err.path}".rstrip(".")
                errors.extend(schema_errors)

    # Check parallel_tool_calls with strict tools
    if has_strict_tools and parallel_tool_calls:
        errors.append(
            SchemaValidationError(
                code=SchemaErrorCode.PARALLEL_TOOL_CALLS_WITH_STRICT,
                message="parallel_tool_calls must be false when using strict tool schemas.",
                path="body.parallel_tool_calls",
                value=parallel_tool_calls,
                fix="Set 'parallel_tool_calls': false in the request body.",
            )
        )

    return errors


def fix_schema_for_strict_mode(
    schema: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Attempt to automatically fix a schema for strict mode compatibility.

    This function applies common fixes:
    - Adds additionalProperties: false to all objects
    - Adds all properties to required array
    - Converts optional fields to nullable types
    - Removes unsupported keywords

    Args:
        schema: The JSON schema to fix.
        model: Model name. If not GPT-5*, returns schema unchanged.

    Returns:
        Fixed schema (new dict, original not modified).

    Warning:
        This is a best-effort fix. Always validate the result and review
        the changes. Some schema semantics may change.
    """
    if not is_gpt5_model(model):
        return schema

    import copy
    result = copy.deepcopy(schema)

    def fix_node(node: Any, path: str = "") -> Any:
        if not isinstance(node, dict):
            return node

        # Remove unsupported keywords
        for keyword in (
            UNSUPPORTED_STRING_KEYWORDS
            | UNSUPPORTED_NUMBER_KEYWORDS
            | UNSUPPORTED_OBJECT_KEYWORDS
            | UNSUPPORTED_ARRAY_KEYWORDS
            | {"default"}
            | FORBIDDEN_KEYWORDS
        ):
            node.pop(keyword, None)

        node_type = node.get("type")

        # Handle implicit object type
        if "properties" in node and "type" not in node:
            node["type"] = "object"
            node_type = "object"

        # Handle implicit array type
        if "items" in node and "type" not in node:
            node["type"] = "array"
            node_type = "array"

        if node_type == "object" or "properties" in node:
            # Add additionalProperties: false
            node["additionalProperties"] = False

            properties = node.get("properties", {})
            original_required = set(node.get("required", []))

            # Make all properties required
            node["required"] = list(properties.keys())

            # Make originally non-required properties nullable
            for prop_name, prop_schema in properties.items():
                if prop_name not in original_required and isinstance(prop_schema, dict):
                    prop_type = prop_schema.get("type")
                    if prop_type and prop_type != "null":
                        if isinstance(prop_type, list):
                            if "null" not in prop_type:
                                prop_type.append("null")
                        else:
                            prop_schema["type"] = [prop_type, "null"]

            # Recursively fix properties
            for prop_name, prop_schema in properties.items():
                properties[prop_name] = fix_node(prop_schema, f"{path}.properties.{prop_name}")

        if node_type == "array" or "items" in node:
            items = node.get("items")
            if isinstance(items, dict):
                node["items"] = fix_node(items, f"{path}.items")
            elif isinstance(items, list):
                node["items"] = [fix_node(item, f"{path}.items[{i}]") for i, item in enumerate(items)]

        # Handle anyOf
        if "anyOf" in node:
            node["anyOf"] = [fix_node(item, f"{path}.anyOf[{i}]") for i, item in enumerate(node["anyOf"])]

        return node

    return fix_node(result)


# Convenience aliases
validate_schema = validate_strict_schema
ValidationError = SchemaValidationError
ValidationException = SchemaValidationException
