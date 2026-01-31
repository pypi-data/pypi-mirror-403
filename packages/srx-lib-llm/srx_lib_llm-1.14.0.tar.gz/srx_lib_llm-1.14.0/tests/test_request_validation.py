"""Comprehensive tests for OpenAI Request Parameter Validation.

This module tests all validation scenarios for the request_validation module,
covering GPT-4.1 vs GPT-5 parameter compatibility and request sanitization.
"""

import pytest

from srx_lib_llm.request_validation import (
    RequestErrorCode,
    RequestValidationError,
    RequestValidationException,
    is_gpt5_model,
    is_gpt4_model,
    supports_reasoning_none,
    get_model_family,
    validate_request_params,
    validate_batch_request_params,
    sanitize_request,
    sanitize_batch_request,
)


class TestIsGpt5Model:
    """Test GPT-5 model detection."""

    def test_gpt5_base(self):
        """Test detection of base GPT-5 model."""
        assert is_gpt5_model("gpt-5") is True

    def test_gpt5_mini(self):
        """Test detection of GPT-5 mini."""
        assert is_gpt5_model("gpt-5-mini") is True

    def test_gpt5_nano(self):
        """Test detection of GPT-5 nano."""
        assert is_gpt5_model("gpt-5-nano") is True

    def test_gpt51(self):
        """Test detection of GPT-5.1."""
        assert is_gpt5_model("gpt-5.1") is True
        assert is_gpt5_model("gpt-5.1-mini") is True
        assert is_gpt5_model("gpt-5.1-nano") is True

    def test_gpt5_with_date_snapshot(self):
        """Test detection of GPT-5 with date snapshot."""
        assert is_gpt5_model("gpt-5-mini-2025-08-07") is True
        assert is_gpt5_model("gpt-5.1-mini-2025-08-07") is True

    def test_o1_series_is_reasoning(self):
        """Test that o1 series is detected as reasoning model."""
        assert is_gpt5_model("o1") is True
        assert is_gpt5_model("o1-preview") is True
        assert is_gpt5_model("o1-mini") is True

    def test_o3_series_is_reasoning(self):
        """Test that o3 series is detected as reasoning model."""
        assert is_gpt5_model("o3") is True
        assert is_gpt5_model("o3-mini") is True

    def test_gpt4_not_detected(self):
        """Test that GPT-4 models are not detected as GPT-5."""
        assert is_gpt5_model("gpt-4") is False
        assert is_gpt5_model("gpt-4-turbo") is False
        assert is_gpt5_model("gpt-4o") is False
        assert is_gpt5_model("gpt-4.1-mini") is False

    def test_gpt35_not_detected(self):
        """Test that GPT-3.5 models are not detected as GPT-5."""
        assert is_gpt5_model("gpt-3.5-turbo") is False

    def test_none_model(self):
        """Test None model returns False."""
        assert is_gpt5_model(None) is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_gpt5_model("") is False

    def test_case_insensitive(self):
        """Test case insensitive detection."""
        assert is_gpt5_model("GPT-5-MINI") is True
        assert is_gpt5_model("Gpt-5") is True


class TestIsGpt4Model:
    """Test GPT-4.1 model detection."""

    def test_gpt4_base(self):
        """Test detection of base GPT-4 models."""
        assert is_gpt4_model("gpt-4") is True
        assert is_gpt4_model("gpt-4-turbo") is True
        assert is_gpt4_model("gpt-4o") is True
        assert is_gpt4_model("gpt-4o-mini") is True

    def test_gpt41(self):
        """Test detection of GPT-4.1 models."""
        assert is_gpt4_model("gpt-4.1") is True
        assert is_gpt4_model("gpt-4.1-mini") is True
        assert is_gpt4_model("gpt-4.1-nano") is True

    def test_gpt35(self):
        """Test detection of GPT-3.5 models."""
        assert is_gpt4_model("gpt-3.5-turbo") is True

    def test_gpt5_not_detected(self):
        """Test that GPT-5 models are not detected as GPT-4."""
        assert is_gpt4_model("gpt-5") is False
        assert is_gpt4_model("gpt-5-mini") is False

    def test_none_model(self):
        """Test None model returns False."""
        assert is_gpt4_model(None) is False


class TestSupportsReasoningNone:
    """Test reasoning_effort: 'none' support detection."""

    def test_gpt51_supports_none(self):
        """Test that GPT-5.1 supports reasoning_effort: none."""
        assert supports_reasoning_none("gpt-5.1") is True
        assert supports_reasoning_none("gpt-5.1-mini") is True
        assert supports_reasoning_none("gpt-5.1-nano") is True

    def test_gpt5_does_not_support_none(self):
        """Test that GPT-5 (without .1) does not support none."""
        assert supports_reasoning_none("gpt-5") is False
        assert supports_reasoning_none("gpt-5-mini") is False
        assert supports_reasoning_none("gpt-5-nano") is False

    def test_gpt4_does_not_support_none(self):
        """Test that GPT-4 does not support none."""
        assert supports_reasoning_none("gpt-4") is False
        assert supports_reasoning_none("gpt-4.1-mini") is False

    def test_none_model(self):
        """Test None model returns False."""
        assert supports_reasoning_none(None) is False


class TestGetModelFamily:
    """Test model family detection."""

    def test_gpt5_family(self):
        """Test GPT-5 family detection."""
        assert get_model_family("gpt-5") == "gpt5"
        assert get_model_family("gpt-5-mini") == "gpt5"
        assert get_model_family("gpt-5.1") == "gpt5"
        assert get_model_family("o1-preview") == "gpt5"

    def test_gpt4_family(self):
        """Test GPT-4 family detection."""
        assert get_model_family("gpt-4") == "gpt4"
        assert get_model_family("gpt-4.1-mini") == "gpt4"
        assert get_model_family("gpt-3.5-turbo") == "gpt4"

    def test_unknown_family(self):
        """Test unknown model family."""
        assert get_model_family("claude-3") == "unknown"
        assert get_model_family("llama-2") == "unknown"
        assert get_model_family(None) == "unknown"


class TestRequestValidationError:
    """Test RequestValidationError class."""

    def test_error_str_representation(self):
        """Test string representation of error."""
        error = RequestValidationError(
            code=RequestErrorCode.GPT5_SAMPLING_PARAMETER,
            message="GPT-5 does not support temperature",
            parameter="temperature",
            value=0.7,
            fix="Remove temperature parameter",
        )
        error_str = str(error)
        assert "[GPT5_SAMPLING_PARAMETER]" in error_str
        assert "temperature" in error_str
        assert "0.7" in error_str

    def test_error_to_dict(self):
        """Test conversion to dictionary."""
        error = RequestValidationError(
            code=RequestErrorCode.GPT4_REASONING_PARAMETER,
            message="GPT-4 does not support reasoning_effort",
            parameter="reasoning_effort",
            value="low",
            fix="Remove reasoning_effort",
        )
        d = error.to_dict()
        assert d["code"] == "GPT4_REASONING_PARAMETER"
        assert d["parameter"] == "reasoning_effort"
        assert d["value"] == "low"


class TestRequestValidationException:
    """Test RequestValidationException class."""

    def test_exception_message(self):
        """Test exception message construction."""
        errors = [
            RequestValidationError(
                code=RequestErrorCode.GPT5_SAMPLING_PARAMETER,
                message="Temperature not supported",
                parameter="temperature",
            ),
            RequestValidationError(
                code=RequestErrorCode.GPT5_SAMPLING_PARAMETER,
                message="Top_p not supported",
                parameter="top_p",
            ),
        ]
        exc = RequestValidationException(errors, model="gpt-5-mini")
        assert "2 error(s)" in str(exc)
        assert "gpt-5-mini" in str(exc)

    def test_exception_to_dict(self):
        """Test exception to dictionary conversion."""
        errors = [
            RequestValidationError(
                code=RequestErrorCode.GPT5_SAMPLING_PARAMETER,
                message="Temperature not supported",
                parameter="temperature",
            ),
        ]
        exc = RequestValidationException(errors, model="gpt-5")
        d = exc.to_dict()
        assert d["error"] == "RequestValidationException"
        assert d["model"] == "gpt-5"
        assert d["error_count"] == 1


class TestGpt5SamplingParameterErrors:
    """Test GPT5_SAMPLING_PARAMETER errors."""

    def test_temperature_rejected_for_gpt5(self):
        """Test temperature is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "temperature": 0.7}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes
        param_errors = [e for e in errors if e.parameter == "temperature"]
        assert len(param_errors) > 0

    def test_top_p_rejected_for_gpt5(self):
        """Test top_p is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "top_p": 0.9}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_presence_penalty_rejected_for_gpt5(self):
        """Test presence_penalty is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "presence_penalty": 0.5}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_frequency_penalty_rejected_for_gpt5(self):
        """Test frequency_penalty is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "frequency_penalty": 0.5}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_logprobs_rejected_for_gpt5(self):
        """Test logprobs is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "logprobs": True}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_top_logprobs_rejected_for_gpt5(self):
        """Test top_logprobs is rejected for GPT-5."""
        request = {"model": "gpt-5-mini", "top_logprobs": 5}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_multiple_sampling_params_rejected(self):
        """Test multiple sampling params all rejected."""
        request = {
            "model": "gpt-5-mini",
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.5,
        }
        errors = validate_request_params(request)
        sampling_errors = [e for e in errors if e.code == RequestErrorCode.GPT5_SAMPLING_PARAMETER]
        assert len(sampling_errors) == 3

    def test_sampling_params_allowed_for_gpt4(self):
        """Test sampling params are allowed for GPT-4."""
        request = {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
        }
        errors = validate_request_params(request)
        sampling_errors = [e for e in errors if e.code == RequestErrorCode.GPT5_SAMPLING_PARAMETER]
        assert len(sampling_errors) == 0


class TestGpt4ReasoningParameterErrors:
    """Test GPT4_REASONING_PARAMETER errors."""

    def test_reasoning_effort_rejected_for_gpt4(self):
        """Test reasoning_effort is rejected for GPT-4."""
        request = {"model": "gpt-4.1-mini", "reasoning_effort": "low"}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT4_REASONING_PARAMETER in error_codes

    def test_reasoning_rejected_for_gpt4(self):
        """Test reasoning object is rejected for GPT-4."""
        request = {"model": "gpt-4.1-mini", "reasoning": {"effort": "low"}}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT4_REASONING_PARAMETER in error_codes

    def test_verbosity_rejected_for_gpt4(self):
        """Test verbosity is rejected for GPT-4."""
        request = {"model": "gpt-4.1-mini", "verbosity": "low"}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT4_REASONING_PARAMETER in error_codes

    def test_reasoning_params_allowed_for_gpt5(self):
        """Test reasoning params are allowed for GPT-5."""
        request = {
            "model": "gpt-5-mini",
            "reasoning_effort": "low",
            "verbosity": "low",
        }
        errors = validate_request_params(request)
        reasoning_errors = [e for e in errors if e.code == RequestErrorCode.GPT4_REASONING_PARAMETER]
        assert len(reasoning_errors) == 0


class TestVendorSpecificParameterErrors:
    """Test UNKNOWN_VENDOR_PARAMETER errors."""

    def test_top_k_rejected(self):
        """Test top_k is rejected (Anthropic parameter)."""
        request = {"model": "gpt-4.1-mini", "top_k": 40}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.UNKNOWN_VENDOR_PARAMETER in error_codes

    def test_best_of_rejected(self):
        """Test best_of is rejected (legacy parameter)."""
        request = {"model": "gpt-4.1-mini", "best_of": 3}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.UNKNOWN_VENDOR_PARAMETER in error_codes

    def test_vendor_params_rejected_for_all_models(self):
        """Test vendor params rejected for all model families."""
        for model in ["gpt-4.1-mini", "gpt-5-mini"]:
            request = {"model": model, "top_k": 40}
            errors = validate_request_params(request)
            error_codes = [e.code for e in errors]
            assert RequestErrorCode.UNKNOWN_VENDOR_PARAMETER in error_codes


class TestReasoningEffortValidation:
    """Test reasoning_effort value validation."""

    def test_valid_reasoning_effort_values(self):
        """Test valid reasoning_effort values pass."""
        for value in ["none", "low", "medium", "high"]:
            # Only test on gpt-5.1 which supports "none"
            request = {"model": "gpt-5.1-mini", "reasoning_effort": value}
            errors = validate_request_params(request)
            invalid_errors = [e for e in errors if e.code == RequestErrorCode.INVALID_REASONING_EFFORT]
            assert len(invalid_errors) == 0, f"'{value}' should be valid"

    def test_invalid_reasoning_effort_value(self):
        """Test invalid reasoning_effort value is rejected."""
        request = {"model": "gpt-5-mini", "reasoning_effort": "super_high"}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.INVALID_REASONING_EFFORT in error_codes

    def test_reasoning_effort_none_rejected_for_gpt5(self):
        """Test reasoning_effort: 'none' is rejected for pre-5.1 models."""
        request = {"model": "gpt-5-mini", "reasoning_effort": "none"}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.REASONING_EFFORT_NONE_NOT_SUPPORTED in error_codes

    def test_reasoning_effort_none_allowed_for_gpt51(self):
        """Test reasoning_effort: 'none' is allowed for gpt-5.1."""
        request = {"model": "gpt-5.1-mini", "reasoning_effort": "none"}
        errors = validate_request_params(request)
        none_errors = [e for e in errors if e.code == RequestErrorCode.REASONING_EFFORT_NONE_NOT_SUPPORTED]
        assert len(none_errors) == 0

    def test_reasoning_effort_in_reasoning_object(self):
        """Test reasoning effort validation in reasoning config object."""
        request = {"model": "gpt-5-mini", "reasoning": {"effort": "invalid"}}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.INVALID_REASONING_EFFORT in error_codes


class TestMissingModel:
    """Test MISSING_MODEL error."""

    def test_missing_model(self):
        """Test error when model is missing."""
        request = {"temperature": 0.7}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.MISSING_MODEL in error_codes


class TestValidateOrRaise:
    """Test validate_or_raise functionality."""

    def test_raises_on_errors(self):
        """Test that exception is raised on errors."""
        request = {"model": "gpt-5-mini", "temperature": 0.7}
        with pytest.raises(RequestValidationException) as exc_info:
            validate_request_params(request, raise_on_error=True)
        assert exc_info.value.error_count > 0

    def test_no_raise_when_valid(self):
        """Test no exception when request is valid."""
        request = {"model": "gpt-5-mini", "reasoning_effort": "low"}
        errors = validate_request_params(request, raise_on_error=True)
        assert len(errors) == 0


class TestSanitizeRequest:
    """Test sanitize_request function."""

    def test_removes_sampling_params_for_gpt5(self):
        """Test sampling params removed for GPT-5."""
        request = {
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.5,
            "reasoning_effort": "low",
        }
        clean = sanitize_request(request)
        assert "temperature" not in clean
        assert "top_p" not in clean
        assert "presence_penalty" not in clean
        assert "reasoning_effort" in clean
        assert clean["reasoning_effort"] == "low"

    def test_removes_reasoning_params_for_gpt4(self):
        """Test reasoning params removed for GPT-4."""
        request = {
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "reasoning_effort": "low",
            "verbosity": "low",
        }
        clean = sanitize_request(request)
        assert "reasoning_effort" not in clean
        assert "verbosity" not in clean
        assert "temperature" in clean
        assert clean["temperature"] == 0.7

    def test_removes_vendor_params_always(self):
        """Test vendor-specific params always removed."""
        request = {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "top_k": 40,
            "best_of": 3,
        }
        clean = sanitize_request(request)
        assert "top_k" not in clean
        assert "best_of" not in clean
        assert "temperature" in clean

    def test_original_not_modified(self):
        """Test original request is not modified."""
        request = {
            "model": "gpt-5-mini",
            "temperature": 0.7,
        }
        original = dict(request)
        sanitize_request(request)
        assert request == original

    def test_model_override(self):
        """Test model override parameter."""
        request = {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "reasoning_effort": "low",
        }
        # Override to GPT-5, should remove temperature
        clean = sanitize_request(request, model="gpt-5-mini")
        assert "temperature" not in clean
        assert "reasoning_effort" in clean

    def test_preserves_common_params(self):
        """Test common params are preserved."""
        request = {
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
            "stop": ["\n"],
            "stream": True,
            "temperature": 0.7,  # Should be removed
        }
        clean = sanitize_request(request)
        assert "messages" in clean
        assert "max_tokens" in clean
        assert "stop" in clean
        assert "stream" in clean
        assert "temperature" not in clean


class TestValidateBatchRequestParams:
    """Test validate_batch_request_params function."""

    def test_validates_body(self):
        """Test validation of batch request body."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7,  # Should fail
            },
        }
        errors = validate_batch_request_params(request)
        assert len(errors) > 0
        # Check path is prefixed with body.
        assert any("body.temperature" in e.parameter for e in errors)

    def test_model_override(self):
        """Test model override for batch request."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "temperature": 0.7,
            },
        }
        # Override to GPT-5
        errors = validate_batch_request_params(request, model="gpt-5-mini")
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_missing_model_in_body(self):
        """Test error when model missing from body."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {"temperature": 0.7},
        }
        errors = validate_batch_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.MISSING_MODEL in error_codes


class TestSanitizeBatchRequest:
    """Test sanitize_batch_request function."""

    def test_sanitizes_body(self):
        """Test batch request body is sanitized."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7,
                "reasoning_effort": "low",
            },
        }
        clean = sanitize_batch_request(request)
        assert "temperature" not in clean["body"]
        assert "reasoning_effort" in clean["body"]
        assert clean["custom_id"] == "req-1"

    def test_model_override(self):
        """Test model override for batch sanitization."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "temperature": 0.7,
                "reasoning_effort": "low",
            },
        }
        # Override to GPT-5
        clean = sanitize_batch_request(request, model="gpt-5-mini")
        assert "temperature" not in clean["body"]
        assert "reasoning_effort" in clean["body"]


class TestValidRequestProfiles:
    """Test valid request profiles pass validation."""

    def test_gpt4_profile_valid(self):
        """Test GPT-4.1 profile is valid."""
        request = {
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "Hello"},
            ],
            "temperature": 0.2,
            "top_p": 1,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }
        errors = validate_request_params(request)
        assert len(errors) == 0

    def test_gpt5_profile_valid(self):
        """Test GPT-5 profile is valid."""
        request = {
            "model": "gpt-5-mini-2025-08-07",
            "messages": [
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "Hello"},
            ],
            "reasoning_effort": "low",
            "verbosity": "low",
        }
        errors = validate_request_params(request)
        assert len(errors) == 0

    def test_gpt51_no_reasoning_valid(self):
        """Test GPT-5.1 with reasoning_effort: none is valid."""
        request = {
            "model": "gpt-5.1-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "reasoning_effort": "none",
        }
        errors = validate_request_params(request)
        assert len(errors) == 0


class TestUnknownModels:
    """Test behavior with unknown models."""

    def test_unknown_model_passes_through(self):
        """Test unknown models pass through without validation."""
        request = {
            "model": "claude-3-opus",
            "temperature": 0.7,
            "reasoning_effort": "low",
        }
        errors = validate_request_params(request)
        # Should only have vendor-specific errors if any
        family_errors = [
            e for e in errors
            if e.code in (RequestErrorCode.GPT5_SAMPLING_PARAMETER, RequestErrorCode.GPT4_REASONING_PARAMETER)
        ]
        assert len(family_errors) == 0

    def test_unknown_model_sanitization(self):
        """Test unknown models are not modified during sanitization."""
        request = {
            "model": "llama-2-70b",
            "temperature": 0.7,
            "reasoning_effort": "low",
            "top_k": 40,  # Vendor param still removed
        }
        clean = sanitize_request(request)
        # Sampling and reasoning params preserved
        assert "temperature" in clean
        assert "reasoning_effort" in clean
        # Vendor param removed
        assert "top_k" not in clean


class TestO1AndO3Series:
    """Test o1 and o3 reasoning models."""

    def test_o1_rejects_sampling_params(self):
        """Test o1 series rejects sampling parameters."""
        request = {"model": "o1-preview", "temperature": 0.7}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_o3_rejects_sampling_params(self):
        """Test o3 series rejects sampling parameters."""
        request = {"model": "o3-mini", "temperature": 0.7}
        errors = validate_request_params(request)
        error_codes = [e.code for e in errors]
        assert RequestErrorCode.GPT5_SAMPLING_PARAMETER in error_codes

    def test_o1_accepts_reasoning_params(self):
        """Test o1 series accepts reasoning parameters."""
        request = {"model": "o1-preview", "reasoning_effort": "high"}
        errors = validate_request_params(request)
        reasoning_errors = [e for e in errors if e.code == RequestErrorCode.GPT4_REASONING_PARAMETER]
        assert len(reasoning_errors) == 0
