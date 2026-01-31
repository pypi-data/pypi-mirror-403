"""Configuration utilities for batch OpenAI pipelines.

Pure utility functions with no infrastructure dependencies.
Can be used by both ETL-Trading and SVC-Trading for config-driven batch processing.
"""

import json
from typing import Any


def render_template(template: str, variables: dict[str, Any]) -> str:
    """Replace {placeholders} in template with values.

    Pure utility - no dependencies on Azure, Airflow, or FastAPI.
    Can be used for prompts, paths, or any string templates.

    Args:
        template: String containing {placeholder} markers
        variables: Dictionary of placeholder names to values

    Returns:
        String with all placeholders replaced

    Example:
        >>> render_template("Hello {name}!", {"name": "World"})
        'Hello World!'
        >>> render_template("{pipeline_prefix}/{date}/output.jsonl", {
        ...     "pipeline_prefix": "attachments",
        ...     "date": "2024-01-15"
        ... })
        'attachments/2024-01-15/output.jsonl'
    """
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def validate_pipeline_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate pipeline configuration structure.

    Checks required fields without loading from Azure Table.
    Returns (is_valid, errors).

    Args:
        config: Pipeline configuration dictionary

    Returns:
        Tuple of (is_valid, error_list)

    Example:
        >>> config = {"pipeline_id": "test", "is_active": True, ...}
        >>> is_valid, errors = validate_pipeline_config(config)
        >>> if not is_valid:
        ...     print(f"Errors: {errors}")
    """
    required_fields = [
        "pipeline_id",
        "is_active",
        "system_prompt",
        "response_schema",
        "output_path_template",
        "pipeline_prefix",
        "source_path",
        "id_field",
        "content_field",
        "schema_name",
    ]
    errors = []

    # Check required fields
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Check if pipeline is active
    if not errors and not config.get("is_active"):
        errors.append("Pipeline is disabled (is_active=false)")

    # Validate response_schema is valid JSON
    if "response_schema" in config:
        try:
            json.loads(config["response_schema"])
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in response_schema: {e}")

    return (len(errors) == 0, errors)


def build_batch_request(
    record: dict[str, Any], config: dict[str, Any], custom_id: str
) -> dict[str, Any]:
    """Build a single OpenAI batch request from record and config.

    Args:
        record: Source data record with content to process
        config: Pipeline config with prompts and schema
        custom_id: Unique ID for this request (used by OpenAI batch API)

    Returns:
        OpenAI batch format dict ready for JSONL serialization

    Example:
        >>> record = {
        ...     "doc_id": "123",
        ...     "filename": "report.pdf",
        ...     "ocr_content": "Price: $50/ton"
        ... }
        >>> config = {
        ...     "system_prompt": "Extract prices from: {ocr_content}",
        ...     "response_schema": '{"type": "object", "properties": {...}}',
        ...     "schema_name": "PriceExtraction"
        ... }
        >>> request = build_batch_request(record, config, "doc-123")
    """
    # Render system prompt with variables from record
    system_prompt = render_template(config["system_prompt"], record)

    # Build messages list
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Add user prompt if exists
    if config.get("user_prompt"):
        user_prompt = render_template(config["user_prompt"], record)
        messages.append({"role": "user", "content": user_prompt})

    # Parse response schema
    schema = json.loads(config["response_schema"])

    # Build OpenAI batch request format
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-5.1-mini",  # GPT-5.1 mini with reasoning
            "reasoning_effort": "none",  # Fast, low-latency responses (emulates non-reasoning)
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": config["schema_name"],
                    "schema": schema,
                    "strict": True,
                },
            },
        },
    }


__all__ = [
    "render_template",
    "validate_pipeline_config",
    "build_batch_request",
]
