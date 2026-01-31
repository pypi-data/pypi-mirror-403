"""OpenAI Request Parameter Validation and Sanitization.

This module validates and sanitizes request parameters based on model family
(GPT-4.1 vs GPT-5). The most common cause of 400 errors is mixing sampling
controls (GPT-4.1) with reasoning controls (GPT-5).

Example:
    >>> from srx_lib_llm.request_validation import (
    ...     validate_request_params,
    ...     sanitize_request,
    ...     is_gpt5_model,
    ... )
    >>>
    >>> # Validate a request
    >>> errors = validate_request_params({"model": "gpt-5-mini", "temperature": 0.7})
    >>> if errors:
    ...     for error in errors:
    ...         print(f"{error.code}: {error.message}")
    >>>
    >>> # Auto-sanitize a request
    >>> clean = sanitize_request({"model": "gpt-5-mini", "temperature": 0.7})
    >>> # Returns: {"model": "gpt-5-mini"} - temperature removed
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class RequestErrorCode(str, Enum):
    """Error codes for request parameter validation failures."""

    # Model family mismatches
    GPT5_SAMPLING_PARAMETER = "GPT5_SAMPLING_PARAMETER"
    GPT4_REASONING_PARAMETER = "GPT4_REASONING_PARAMETER"
    INCOMPATIBLE_PARAMETER_FOR_MODEL = "INCOMPATIBLE_PARAMETER_FOR_MODEL"

    # Vendor-specific parameters
    UNKNOWN_VENDOR_PARAMETER = "UNKNOWN_VENDOR_PARAMETER"

    # API issues
    LEGACY_API_NOT_RECOMMENDED = "LEGACY_API_NOT_RECOMMENDED"

    # Reasoning effort validation
    INVALID_REASONING_EFFORT = "INVALID_REASONING_EFFORT"
    REASONING_EFFORT_NONE_NOT_SUPPORTED = "REASONING_EFFORT_NONE_NOT_SUPPORTED"

    # General
    MISSING_MODEL = "MISSING_MODEL"
    INVALID_PARAMETER_VALUE = "INVALID_PARAMETER_VALUE"


@dataclass
class RequestValidationError:
    """Detailed error information for request validation failures.

    Attributes:
        code: Machine-readable error code from RequestErrorCode enum.
        message: Human-readable description of the error.
        parameter: The parameter that caused the error.
        value: The actual value that caused the error.
        fix: Suggested fix for the error.
        severity: "error" for blocking issues, "warning" for recommendations.
    """

    code: RequestErrorCode
    message: str
    parameter: str
    value: Any = None
    fix: str = ""
    severity: str = "error"

    def __str__(self) -> str:
        parts = [f"[{self.code.value}] {self.message}"]
        if self.parameter:
            parts.append(f"  Parameter: {self.parameter}")
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
            "parameter": self.parameter,
            "value": self.value,
            "fix": self.fix,
            "severity": self.severity,
        }


class RequestValidationException(Exception):
    """Exception raised when request validation fails.

    Attributes:
        errors: List of validation errors found.
        model: The model being validated for.
    """

    def __init__(
        self,
        errors: List[RequestValidationError],
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
            f"Request validation failed with {self.error_count} error(s)"
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
            "error": "RequestValidationException",
            "message": f"Request validation failed with {self.error_count} error(s)",
            "model": self.model,
            "error_count": self.error_count,
            "errors": [e.to_dict() for e in self.errors],
        }


# Model family prefixes
GPT5_PREFIXES = ("gpt-5", "o1", "o3")  # o1/o3 are also reasoning models
GPT4_PREFIXES = ("gpt-4", "gpt-3.5")

# Sampling parameters (GPT-4.1 only, rejected by GPT-5)
SAMPLING_PARAMETERS: Set[str] = {
    "temperature",
    "top_p",
    "presence_penalty",
    "frequency_penalty",
    "logprobs",
    "top_logprobs",
}

# Reasoning parameters (GPT-5 only, rejected by GPT-4.1)
REASONING_PARAMETERS: Set[str] = {
    "reasoning",
    "reasoning_effort",
    "verbosity",
}

# Vendor-specific parameters (never send to OpenAI)
VENDOR_SPECIFIC_PARAMETERS: Set[str] = {
    "top_k",  # Anthropic/others only
    "best_of",  # Legacy, not recommended
}

# Valid reasoning_effort values
VALID_REASONING_EFFORTS: Set[str] = {"none", "low", "medium", "high"}

# Models that support reasoning_effort: "none"
MODELS_SUPPORTING_NONE_REASONING: Set[str] = {
    "gpt-5.1",
    "gpt-5.1-mini",
    "gpt-5.1-nano",
    "gpt-5.1-2025-11-13",
    "gpt-5.1-chat-2025-11-13",
    "gpt-5.1-codex-2025-11-13",
}


def is_gpt5_model(model: Optional[str]) -> bool:
    """Check if model is GPT-5 family (reasoning model).

    Also includes o1/o3 series which are reasoning models.

    Args:
        model: Model name/ID string.

    Returns:
        True if model is a reasoning model (GPT-5, o1, o3), False otherwise.

    Examples:
        >>> is_gpt5_model("gpt-5")
        True
        >>> is_gpt5_model("gpt-5-mini")
        True
        >>> is_gpt5_model("gpt-5.1-mini-2025-08-07")
        True
        >>> is_gpt5_model("o1-preview")
        True
        >>> is_gpt5_model("gpt-4-turbo")
        False
        >>> is_gpt5_model(None)
        False
    """
    if not model:
        return False
    model_lower = model.lower()
    return any(model_lower.startswith(prefix) for prefix in GPT5_PREFIXES)


def is_gpt4_model(model: Optional[str]) -> bool:
    """Check if model is GPT-4.1 or GPT-3.5 family (non-reasoning).

    Args:
        model: Model name/ID string.

    Returns:
        True if model is GPT-4.1 or GPT-3.5 family, False otherwise.

    Examples:
        >>> is_gpt4_model("gpt-4")
        True
        >>> is_gpt4_model("gpt-4-turbo")
        True
        >>> is_gpt4_model("gpt-4.1-mini")
        True
        >>> is_gpt4_model("gpt-3.5-turbo")
        True
        >>> is_gpt4_model("gpt-5-mini")
        False
    """
    if not model:
        return False
    model_lower = model.lower()
    return any(model_lower.startswith(prefix) for prefix in GPT4_PREFIXES)


def supports_reasoning_none(model: Optional[str]) -> bool:
    """Check if model supports reasoning_effort: "none".

    Only gpt-5.1 and later support the "none" value for reasoning_effort.

    Args:
        model: Model name/ID string.

    Returns:
        True if model supports reasoning_effort: "none".

    Examples:
        >>> supports_reasoning_none("gpt-5.1")
        True
        >>> supports_reasoning_none("gpt-5.1-mini")
        True
        >>> supports_reasoning_none("gpt-5-mini")
        False
        >>> supports_reasoning_none("gpt-5")
        False
    """
    if not model:
        return False
    model_lower = model.lower()
    # gpt-5.1* supports none, gpt-5* (without .1) does not
    return model_lower.startswith("gpt-5.1")


def get_model_family(model: Optional[str]) -> str:
    """Get the model family for a given model.

    Args:
        model: Model name/ID string.

    Returns:
        "gpt5" for reasoning models, "gpt4" for non-reasoning, "unknown" otherwise.
    """
    if is_gpt5_model(model):
        return "gpt5"
    elif is_gpt4_model(model):
        return "gpt4"
    return "unknown"


class RequestParamValidator:
    """Validator for OpenAI request parameters based on model family.

    This validator checks request parameters against the model's supported
    parameter set and provides detailed, actionable error messages.

    Example:
        >>> validator = RequestParamValidator()
        >>> errors = validator.validate({"model": "gpt-5-mini", "temperature": 0.7})
        >>> if errors:
        ...     raise RequestValidationException(errors)
    """

    def __init__(self):
        """Initialize the validator."""
        self.errors: List[RequestValidationError] = []

    def validate(self, request: Dict[str, Any]) -> List[RequestValidationError]:
        """Validate request parameters for model compatibility.

        Args:
            request: The request body to validate.

        Returns:
            List of validation errors. Empty list if valid.
        """
        self.errors = []

        model = request.get("model")
        if not model:
            self._add_error(
                code=RequestErrorCode.MISSING_MODEL,
                message="Request must specify a model.",
                parameter="model",
                fix="Add 'model' field to the request.",
            )
            return self.errors

        # Check vendor-specific parameters (always invalid)
        self._check_vendor_parameters(request)

        # Check based on model family
        if is_gpt5_model(model):
            self._validate_gpt5_request(request, model)
        elif is_gpt4_model(model):
            self._validate_gpt4_request(request, model)
        # Unknown models pass through without validation

        return self.errors

    def validate_or_raise(self, request: Dict[str, Any]) -> None:
        """Validate request and raise exception if invalid.

        Args:
            request: The request body to validate.

        Raises:
            RequestValidationException: If validation fails.
        """
        errors = self.validate(request)
        if errors:
            model = request.get("model")
            raise RequestValidationException(errors, model=model)

    def _add_error(
        self,
        code: RequestErrorCode,
        message: str,
        parameter: str,
        value: Any = None,
        fix: str = "",
        severity: str = "error",
    ) -> None:
        """Add a validation error."""
        self.errors.append(
            RequestValidationError(
                code=code,
                message=message,
                parameter=parameter,
                value=value,
                fix=fix,
                severity=severity,
            )
        )

    def _check_vendor_parameters(self, request: Dict[str, Any]) -> None:
        """Check for vendor-specific parameters that should never be sent."""
        for param in VENDOR_SPECIFIC_PARAMETERS:
            if param in request:
                self._add_error(
                    code=RequestErrorCode.UNKNOWN_VENDOR_PARAMETER,
                    message=f"Parameter '{param}' is not supported by OpenAI.",
                    parameter=param,
                    value=request[param],
                    fix=f"Remove '{param}' from the request. This parameter is vendor-specific.",
                )

    def _validate_gpt5_request(self, request: Dict[str, Any], model: str) -> None:
        """Validate request parameters for GPT-5 models."""
        # Check for sampling parameters (not allowed for GPT-5)
        for param in SAMPLING_PARAMETERS:
            if param in request:
                self._add_error(
                    code=RequestErrorCode.GPT5_SAMPLING_PARAMETER,
                    message=f"GPT-5 models do not support sampling parameter '{param}'.",
                    parameter=param,
                    value=request[param],
                    fix=f"Remove '{param}'. Use 'reasoning_effort' and 'verbosity' instead for GPT-5.",
                )

        # Validate reasoning_effort if present
        reasoning_effort = request.get("reasoning_effort")
        if reasoning_effort is not None:
            self._validate_reasoning_effort(reasoning_effort, model)

        # Check reasoning config object
        reasoning = request.get("reasoning")
        if isinstance(reasoning, dict) and "effort" in reasoning:
            self._validate_reasoning_effort(reasoning["effort"], model)

    def _validate_gpt4_request(self, request: Dict[str, Any], model: str) -> None:
        """Validate request parameters for GPT-4.1 models."""
        # Check for reasoning parameters (not allowed for GPT-4.1)
        for param in REASONING_PARAMETERS:
            if param in request:
                self._add_error(
                    code=RequestErrorCode.GPT4_REASONING_PARAMETER,
                    message=f"GPT-4.1 models do not support reasoning parameter '{param}'.",
                    parameter=param,
                    value=request[param],
                    fix=f"Remove '{param}'. Use 'temperature' and 'top_p' instead for GPT-4.1.",
                )

    def _validate_reasoning_effort(self, value: Any, model: str) -> None:
        """Validate reasoning_effort value."""
        if not isinstance(value, str):
            self._add_error(
                code=RequestErrorCode.INVALID_PARAMETER_VALUE,
                message=f"reasoning_effort must be a string, got {type(value).__name__}.",
                parameter="reasoning_effort",
                value=value,
                fix=f"Use one of: {', '.join(sorted(VALID_REASONING_EFFORTS))}",
            )
            return

        if value not in VALID_REASONING_EFFORTS:
            self._add_error(
                code=RequestErrorCode.INVALID_REASONING_EFFORT,
                message=f"Invalid reasoning_effort value: '{value}'.",
                parameter="reasoning_effort",
                value=value,
                fix=f"Use one of: {', '.join(sorted(VALID_REASONING_EFFORTS))}",
            )
            return

        # Check if "none" is supported for this model
        if value == "none" and not supports_reasoning_none(model):
            self._add_error(
                code=RequestErrorCode.REASONING_EFFORT_NONE_NOT_SUPPORTED,
                message=f"reasoning_effort: 'none' is not supported for model '{model}'.",
                parameter="reasoning_effort",
                value=value,
                fix="Use 'low', 'medium', or 'high' for models before gpt-5.1. "
                    "Or upgrade to gpt-5.1 or later to use 'none'.",
            )


def validate_request_params(
    request: Dict[str, Any],
    raise_on_error: bool = False,
) -> List[RequestValidationError]:
    """Validate request parameters for model compatibility.

    This is the main entry point for request validation.

    Args:
        request: The request body to validate.
        raise_on_error: If True, raises RequestValidationException on errors.

    Returns:
        List of validation errors. Empty list if valid.

    Raises:
        RequestValidationException: If raise_on_error=True and validation fails.

    Example:
        >>> errors = validate_request_params({
        ...     "model": "gpt-5-mini",
        ...     "temperature": 0.7,  # Not allowed for GPT-5
        ...     "reasoning_effort": "low"
        ... })
        >>> if errors:
        ...     print(f"Found {len(errors)} error(s)")
    """
    validator = RequestParamValidator()
    errors = validator.validate(request)

    if raise_on_error and errors:
        model = request.get("model")
        raise RequestValidationException(errors, model=model)

    return errors


def sanitize_request(
    request: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Sanitize request by removing incompatible parameters.

    This function automatically removes parameters that are incompatible
    with the target model, preventing 400 errors.

    Args:
        request: The request body to sanitize.
        model: Optional model override. If not provided, uses request["model"].

    Returns:
        Sanitized request (new dict, original not modified).

    Example:
        >>> request = {
        ...     "model": "gpt-5-mini",
        ...     "messages": [{"role": "user", "content": "Hello"}],
        ...     "temperature": 0.7,  # Will be removed
        ...     "reasoning_effort": "low"  # Will be kept
        ... }
        >>> clean = sanitize_request(request)
        >>> "temperature" in clean
        False
        >>> "reasoning_effort" in clean
        True
    """
    result = deepcopy(request)
    target_model = model or result.get("model", "")

    if is_gpt5_model(target_model):
        # Remove sampling parameters for GPT-5
        for param in SAMPLING_PARAMETERS:
            result.pop(param, None)
        # Keep reasoning parameters
    elif is_gpt4_model(target_model):
        # Remove reasoning parameters for GPT-4.1
        for param in REASONING_PARAMETERS:
            result.pop(param, None)
        # Keep sampling parameters

    # Always remove vendor-specific parameters
    for param in VENDOR_SPECIFIC_PARAMETERS:
        result.pop(param, None)

    return result


def validate_batch_request_params(
    request: Dict[str, Any],
    model: Optional[str] = None,
) -> List[RequestValidationError]:
    """Validate a Batch API request for parameter compatibility.

    Extracts the body and validates parameters based on the model.

    Args:
        request: Batch API request with custom_id, method, url, body.
        model: Model override. If not provided, extracted from body.

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
        ...         "temperature": 0.7
        ...     }
        ... }
        >>> errors = validate_batch_request_params(request)
    """
    body = request.get("body", {})
    target_model = model or body.get("model")

    if not target_model:
        return [
            RequestValidationError(
                code=RequestErrorCode.MISSING_MODEL,
                message="Batch request body must specify a model.",
                parameter="body.model",
                fix="Add 'model' field to the request body.",
            )
        ]

    # If model is overridden, create a temporary body with the override
    if model and model != body.get("model"):
        validation_body = dict(body)
        validation_body["model"] = model
    else:
        validation_body = body

    # Validate the body
    errors = validate_request_params(validation_body)

    # Prefix paths with "body."
    for error in errors:
        error.parameter = f"body.{error.parameter}"

    return errors


def sanitize_batch_request(
    request: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Sanitize a Batch API request by removing incompatible parameters.

    Args:
        request: Batch API request with custom_id, method, url, body.
        model: Model override. If not provided, extracted from body.

    Returns:
        Sanitized request (new dict, original not modified).
    """
    result = deepcopy(request)
    body = result.get("body", {})
    target_model = model or body.get("model")

    if body and target_model:
        result["body"] = sanitize_request(body, model=target_model)

    return result


# Convenience aliases
validate_params = validate_request_params
sanitize = sanitize_request
ValidationError = RequestValidationError
ValidationException = RequestValidationException
