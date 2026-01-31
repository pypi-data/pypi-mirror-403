"""Comprehensive tests for OpenAI Structured Outputs JSON Schema validation.

This module tests all validation scenarios for the schema_validation module,
covering every error code and edge case for GPT-5* strict mode validation.
"""

import pytest

from srx_lib_llm.schema_validation import (
    SchemaErrorCode,
    SchemaValidationError,
    SchemaValidationException,
    is_gpt5_model,
    validate_strict_schema,
    validate_batch_request,
    fix_schema_for_strict_mode,
)


class TestIsGpt5Model:
    """Test GPT-5 model detection."""

    def test_gpt5_base_model(self):
        """Test detection of base GPT-5 model."""
        assert is_gpt5_model("gpt-5") is True

    def test_gpt5_mini(self):
        """Test detection of GPT-5 mini."""
        assert is_gpt5_model("gpt-5-mini") is True

    def test_gpt5_with_version(self):
        """Test detection of GPT-5 with version."""
        assert is_gpt5_model("gpt-5.1") is True
        assert is_gpt5_model("gpt-5.1-mini") is True

    def test_gpt5_with_date_snapshot(self):
        """Test detection of GPT-5 with date snapshot."""
        assert is_gpt5_model("gpt-5-mini-2025-08-07") is True
        assert is_gpt5_model("gpt-5.1-mini-2025-08-07") is True

    def test_gpt4_not_detected(self):
        """Test that GPT-4 models are not detected."""
        assert is_gpt5_model("gpt-4") is False
        assert is_gpt5_model("gpt-4-turbo") is False
        assert is_gpt5_model("gpt-4o") is False
        assert is_gpt5_model("gpt-4o-mini") is False

    def test_gpt35_not_detected(self):
        """Test that GPT-3.5 models are not detected."""
        assert is_gpt5_model("gpt-3.5-turbo") is False

    def test_none_model(self):
        """Test None model returns False."""
        assert is_gpt5_model(None) is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_gpt5_model("") is False


class TestSchemaValidationError:
    """Test SchemaValidationError class."""

    def test_error_str_representation(self):
        """Test string representation of error."""
        error = SchemaValidationError(
            code=SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE,
            message="Object must have additionalProperties: false",
            path="properties.user",
            value={"type": "object"},
            fix="Add 'additionalProperties': false",
        )
        error_str = str(error)
        assert "[MISSING_ADDITIONAL_PROPERTIES_FALSE]" in error_str
        assert "properties.user" in error_str
        assert "additionalProperties" in error_str

    def test_error_to_dict(self):
        """Test conversion to dictionary."""
        error = SchemaValidationError(
            code=SchemaErrorCode.INVALID_TYPE,
            message="Invalid type 'foo'",
            path="properties.name.type",
            value="foo",
            fix="Use valid type",
        )
        d = error.to_dict()
        assert d["code"] == "INVALID_TYPE"
        assert d["message"] == "Invalid type 'foo'"
        assert d["path"] == "properties.name.type"


class TestSchemaValidationException:
    """Test SchemaValidationException class."""

    def test_exception_message(self):
        """Test exception message construction."""
        errors = [
            SchemaValidationError(
                code=SchemaErrorCode.MISSING_TYPE,
                message="Missing type",
                path="root",
            ),
            SchemaValidationError(
                code=SchemaErrorCode.INVALID_TYPE,
                message="Invalid type",
                path="properties.name",
            ),
        ]
        exc = SchemaValidationException(errors, model="gpt-5-mini")
        assert "2 error(s)" in str(exc)
        assert "gpt-5-mini" in str(exc)

    def test_exception_to_dict(self):
        """Test exception to dictionary conversion."""
        errors = [
            SchemaValidationError(
                code=SchemaErrorCode.MISSING_TYPE,
                message="Missing type",
                path="root",
            ),
        ]
        exc = SchemaValidationException(errors, model="gpt-5")
        d = exc.to_dict()
        assert d["error"] == "SchemaValidationException"
        assert d["model"] == "gpt-5"
        assert d["error_count"] == 1
        assert len(d["errors"]) == 1


class TestStrictSchemaValidatorGpt5Detection:
    """Test that validation is skipped for non-GPT-5 models."""

    def test_skip_validation_for_gpt4(self):
        """Test validation is skipped for GPT-4."""
        schema = {"type": "object"}  # Invalid - no additionalProperties
        errors = validate_strict_schema(schema, model="gpt-4")
        assert len(errors) == 0

    def test_skip_validation_for_gpt35(self):
        """Test validation is skipped for GPT-3.5."""
        schema = {"type": "object"}  # Invalid - no additionalProperties
        errors = validate_strict_schema(schema, model="gpt-3.5-turbo")
        assert len(errors) == 0

    def test_skip_validation_for_none_model(self):
        """Test validation is skipped when model is None."""
        schema = {"type": "object"}
        errors = validate_strict_schema(schema, model=None)
        assert len(errors) == 0

    def test_validate_for_gpt5(self):
        """Test validation runs for GPT-5."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        errors = validate_strict_schema(schema, model="gpt-5")
        assert len(errors) > 0  # Should have errors (missing additionalProperties, required)


class TestMissingAdditionalPropertiesFalse:
    """Test MISSING_ADDITIONAL_PROPERTIES_FALSE error."""

    def test_object_without_additional_properties(self):
        """Test object missing additionalProperties."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes

    def test_object_with_additional_properties_true(self):
        """Test object with additionalProperties: true."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": True,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes

    def test_object_with_additional_properties_schema(self):
        """Test object with additionalProperties as schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": {"type": "string"},
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes

    def test_object_with_additional_properties_false_valid(self):
        """Test valid object with additionalProperties: false."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE not in error_codes

    def test_nested_object_without_additional_properties(self):
        """Test nested object missing additionalProperties."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    # Missing additionalProperties
                }
            },
            "required": ["user"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes


class TestPropertyNotInRequired:
    """Test PROPERTY_NOT_IN_REQUIRED error."""

    def test_property_not_in_required(self):
        """Test property not listed in required."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],  # age not required
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED in error_codes
        # Find the specific error
        age_errors = [e for e in errors if "age" in str(e)]
        assert len(age_errors) > 0

    def test_all_properties_in_required_valid(self):
        """Test valid case where all properties are required."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED not in error_codes

    def test_nullable_property_not_in_required(self):
        """Test nullable property not in required (still needs to be required)."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nickname": {"type": ["string", "null"]},  # nullable
            },
            "required": ["name"],  # nickname missing from required
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED in error_codes


class TestForbiddenKeywords:
    """Test FORBIDDEN_KEYWORD_* errors."""

    def test_oneof_forbidden(self):
        """Test oneOf is forbidden."""
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.FORBIDDEN_KEYWORD_ONEOF in error_codes


class TestUnsupportedConstraints:
    """Test UNSUPPORTED_*_CONSTRAINT errors."""

    def test_string_minlength_unsupported(self):
        """Test minLength is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT in error_codes

    def test_string_maxlength_unsupported(self):
        """Test maxLength is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 100},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT in error_codes

    def test_string_pattern_unsupported(self):
        """Test pattern is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "pattern": "^[a-z]+@[a-z]+\\.[a-z]+$"},
            },
            "required": ["email"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT in error_codes

    def test_string_format_unsupported(self):
        """Test format is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
            },
            "required": ["email"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT in error_codes

    def test_number_minimum_unsupported(self):
        """Test minimum is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["age"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_NUMBER_CONSTRAINT in error_codes

    def test_number_maximum_unsupported(self):
        """Test maximum is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "maximum": 100},
            },
            "required": ["score"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_NUMBER_CONSTRAINT in error_codes

    def test_number_multipleof_unsupported(self):
        """Test multipleOf is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "quantity": {"type": "integer", "multipleOf": 10},
            },
            "required": ["quantity"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_NUMBER_CONSTRAINT in error_codes

    def test_array_minitems_unsupported(self):
        """Test minItems is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            },
            "required": ["items"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_ARRAY_CONSTRAINT in error_codes

    def test_array_maxitems_unsupported(self):
        """Test maxItems is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
            },
            "required": ["items"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_ARRAY_CONSTRAINT in error_codes

    def test_array_uniqueitems_unsupported(self):
        """Test uniqueItems is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            },
            "required": ["tags"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_ARRAY_CONSTRAINT in error_codes

    def test_array_contains_unsupported(self):
        """Test contains is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "contains": {"type": "string", "const": "required"},
                },
            },
            "required": ["items"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_ARRAY_CONSTRAINT in error_codes

    def test_object_patternproperties_unsupported(self):
        """Test patternProperties is unsupported."""
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
            "patternProperties": {"^S_": {"type": "string"}},
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_OBJECT_CONSTRAINT in error_codes


class TestDefaultKeyword:
    """Test UNSUPPORTED_DEFAULT_KEYWORD error."""

    def test_default_unsupported(self):
        """Test default keyword is unsupported."""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "default": "pending"},
            },
            "required": ["status"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNSUPPORTED_DEFAULT_KEYWORD in error_codes


class TestInvalidType:
    """Test INVALID_TYPE error."""

    def test_invalid_type_string(self):
        """Test invalid type value."""
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "foo"},  # Invalid type
            },
            "required": ["data"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.INVALID_TYPE in error_codes

    def test_invalid_type_in_array(self):
        """Test invalid type in type array."""
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": ["string", "foo"]},  # foo is invalid
            },
            "required": ["data"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.INVALID_TYPE in error_codes

    def test_valid_types(self):
        """Test all valid types pass."""
        valid_types = ["object", "array", "string", "number", "integer", "boolean", "null"]
        for valid_type in valid_types:
            if valid_type == "object":
                schema = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                }
            elif valid_type == "array":
                schema = {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["items"],
                    "additionalProperties": False,
                }
            else:
                schema = {
                    "type": "object",
                    "properties": {
                        "value": {"type": valid_type},
                    },
                    "required": ["value"],
                    "additionalProperties": False,
                }
            errors = validate_strict_schema(schema, model="gpt-5")
            invalid_type_errors = [e for e in errors if e.code == SchemaErrorCode.INVALID_TYPE]
            assert len(invalid_type_errors) == 0, f"Type '{valid_type}' should be valid"


class TestMissingType:
    """Test MISSING_TYPE error."""

    def test_object_without_explicit_type(self):
        """Test object schema without explicit type."""
        schema = {
            "properties": {  # Missing "type": "object"
                "name": {"type": "string"},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_TYPE in error_codes

    def test_array_without_explicit_type(self):
        """Test array schema without explicit type."""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "items": {"type": "string"},  # Missing "type": "array"
                },
            },
            "required": ["data"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_TYPE in error_codes


class TestMissingItems:
    """Test MISSING_ITEMS error."""

    def test_array_without_items(self):
        """Test array without items definition."""
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "array"},  # Missing items
            },
            "required": ["data"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ITEMS in error_codes

    def test_array_with_items_valid(self):
        """Test array with items is valid."""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["data"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ITEMS not in error_codes


class TestRefValidation:
    """Test $ref validation."""

    def test_external_ref_invalid(self):
        """Test external $ref is invalid."""
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "https://example.com/schemas/user.json"},
            },
            "required": ["user"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.INVALID_REF in error_codes

    def test_unresolved_ref(self):
        """Test unresolved $ref."""
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "#/$defs/User"},
            },
            "required": ["user"],
            "additionalProperties": False,
            "$defs": {},  # Empty - User not defined
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.UNRESOLVED_REF in error_codes

    def test_ref_with_additional_keywords(self):
        """Test $ref with additional keywords (not allowed in strict mode)."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "$ref": "#/$defs/User",
                    "description": "A user",  # Additional keyword
                },
            },
            "required": ["user"],
            "additionalProperties": False,
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                }
            },
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.INVALID_REF in error_codes

    def test_valid_internal_ref(self):
        """Test valid internal $ref."""
        schema = {
            "type": "object",
            "properties": {
                "user": {"$ref": "#/$defs/User"},
            },
            "required": ["user"],
            "additionalProperties": False,
            "$defs": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                }
            },
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        # Should not have INVALID_REF or UNRESOLVED_REF
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.INVALID_REF not in error_codes
        assert SchemaErrorCode.UNRESOLVED_REF not in error_codes


class TestNullableTypes:
    """Test nullable type patterns."""

    def test_array_style_nullable_valid(self):
        """Test array-style nullable type is handled."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nickname": {"type": ["string", "null"]},
            },
            "required": ["name", "nickname"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        # Should only have valid errors (if any), not type errors
        invalid_type_errors = [e for e in errors if e.code == SchemaErrorCode.INVALID_TYPE]
        assert len(invalid_type_errors) == 0

    def test_anyof_nullable_pattern(self):
        """Test anyOf nullable pattern is handled."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nickname": {
                    "anyOf": [{"type": "string"}, {"type": "null"}]
                },
            },
            "required": ["name", "nickname"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        # anyOf nullable pattern should be recognized
        assert all(e.code != SchemaErrorCode.INVALID_TYPE for e in errors)


class TestNestedSchemas:
    """Test validation of deeply nested schemas."""

    def test_deeply_nested_objects(self):
        """Test validation of deeply nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "level3": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                    },
                                    # Missing additionalProperties, required
                                },
                            },
                            "required": ["level3"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["level2"],
                    "additionalProperties": False,
                },
            },
            "required": ["level1"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        # Should find errors at level3
        assert len(errors) > 0
        # Check that path includes nested location
        paths = [e.path for e in errors]
        assert any("level3" in path for path in paths)

    def test_array_of_objects(self):
        """Test validation of array items."""
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                        },
                        # Missing additionalProperties, required
                    },
                },
            },
            "required": ["users"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes
        assert SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED in error_codes


class TestValidateOrRaise:
    """Test validate_or_raise method."""

    def test_raises_exception_on_errors(self):
        """Test that exception is raised when errors exist."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            # Missing additionalProperties, required
        }
        with pytest.raises(SchemaValidationException) as exc_info:
            validate_strict_schema(schema, model="gpt-5", raise_on_error=True)
        assert exc_info.value.error_count > 0

    def test_no_exception_when_valid(self):
        """Test no exception when schema is valid."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        # Should not raise
        errors = validate_strict_schema(schema, model="gpt-5", raise_on_error=True)
        assert len(errors) == 0


class TestValidateBatchRequest:
    """Test validate_batch_request function."""

    def test_batch_request_with_strict_response_format(self):
        """Test batch request validation with strict response format."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "test",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            # Missing additionalProperties, required
                        },
                    },
                },
            },
        }
        errors = validate_batch_request(request)
        assert len(errors) > 0
        paths = [e.path for e in errors]
        assert any("response_format" in path for path in paths)

    def test_batch_request_missing_strict(self):
        """Test batch request without strict: true."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "test",
                        # Missing strict: true
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                            "additionalProperties": False,
                        },
                    },
                },
            },
        }
        errors = validate_batch_request(request)
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.STRICT_MODE_NOT_ENABLED in error_codes

    def test_batch_request_with_strict_tools(self):
        """Test batch request with strict tool schemas."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-5-mini",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_user",
                            "strict": True,
                            "parameters": {
                                "type": "object",
                                "properties": {"id": {"type": "string"}},
                                # Missing additionalProperties, required
                            },
                        },
                    }
                ],
                "parallel_tool_calls": True,  # Should be False with strict tools
            },
        }
        errors = validate_batch_request(request)
        error_codes = [e.code for e in errors]
        assert SchemaErrorCode.PARALLEL_TOOL_CALLS_WITH_STRICT in error_codes

    def test_batch_request_skip_validation_gpt4(self):
        """Test batch request skips validation for GPT-4."""
        request = {
            "custom_id": "req-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4",  # Not GPT-5
                "messages": [{"role": "user", "content": "Hello"}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "test",
                        "schema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                            # Invalid for strict mode, but GPT-4 skips validation
                        },
                    },
                },
            },
        }
        errors = validate_batch_request(request)
        assert len(errors) == 0


class TestFixSchemaForStrictMode:
    """Test fix_schema_for_strict_mode function."""

    def test_adds_additional_properties_false(self):
        """Test that additionalProperties: false is added."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert fixed["additionalProperties"] is False

    def test_adds_all_properties_to_required(self):
        """Test that all properties are added to required."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert set(fixed["required"]) == {"name", "age"}

    def test_makes_optional_fields_nullable(self):
        """Test that originally optional fields become nullable."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nickname": {"type": "string"},  # Not in original required
            },
            "required": ["name"],
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        # nickname should be nullable now
        nickname_type = fixed["properties"]["nickname"]["type"]
        assert isinstance(nickname_type, list)
        assert "null" in nickname_type

    def test_removes_unsupported_keywords(self):
        """Test that unsupported keywords are removed."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0},
            },
            "required": ["name", "age"],
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert "minLength" not in fixed["properties"]["name"]
        assert "maxLength" not in fixed["properties"]["name"]
        assert "minimum" not in fixed["properties"]["age"]

    def test_adds_implicit_type_object(self):
        """Test that implicit object type is made explicit."""
        schema = {
            "properties": {"name": {"type": "string"}},  # Missing type: object
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert fixed["type"] == "object"

    def test_adds_implicit_type_array(self):
        """Test that implicit array type is made explicit."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "items": {"type": "string"},  # Missing type: array
                },
            },
            "required": ["items"],
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert fixed["properties"]["items"]["type"] == "array"

    def test_fixes_nested_schemas(self):
        """Test that nested schemas are also fixed."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                },
            },
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-5")
        assert fixed["properties"]["user"]["additionalProperties"] is False
        assert "name" in fixed["properties"]["user"]["required"]

    def test_skips_fix_for_non_gpt5(self):
        """Test that fix is skipped for non-GPT-5 models."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        fixed = fix_schema_for_strict_mode(schema, model="gpt-4")
        # Should be unchanged
        assert fixed == schema

    def test_original_schema_not_modified(self):
        """Test that original schema is not modified."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        original_copy = dict(schema)
        fix_schema_for_strict_mode(schema, model="gpt-5")
        assert schema == original_copy


class TestComplexValidScenarios:
    """Test complex but valid schemas."""

    def test_valid_complex_schema(self):
        """Test a complex but valid schema passes validation."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "completed", "failed"]},
                "count": {"type": ["integer", "null"]},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "number"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["name", "value", "tags"],
                        "additionalProperties": False,
                    },
                },
                "metadata": {
                    "type": ["object", "null"],
                    "properties": {
                        "created": {"type": "string"},
                        "updated": {"type": ["string", "null"]},
                    },
                    "required": ["created", "updated"],
                    "additionalProperties": False,
                },
            },
            "required": ["id", "status", "count", "items", "metadata"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        assert len(errors) == 0, f"Expected no errors but got: {errors}"


class TestMultipleErrorsPerSchema:
    """Test that multiple errors are reported for a single schema."""

    def test_multiple_errors_reported(self):
        """Test that all errors are reported, not just the first one."""
        schema = {
            # Multiple issues:
            # 1. No type
            # 2. No additionalProperties
            # 3. Properties not in required
            "properties": {
                "name": {"type": "string", "minLength": 1},  # 4. minLength unsupported
                "email": {"type": "string", "format": "email"},  # 5. format unsupported
                "age": {"type": "integer", "minimum": 0},  # 6. minimum unsupported
            },
            "required": ["name"],  # email, age missing
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        # Should have multiple errors
        assert len(errors) >= 4  # At minimum: type, additionalProperties, 2 missing required
        error_codes = set(e.code for e in errors)
        assert SchemaErrorCode.MISSING_TYPE in error_codes
        assert SchemaErrorCode.MISSING_ADDITIONAL_PROPERTIES_FALSE in error_codes
        assert SchemaErrorCode.PROPERTY_NOT_IN_REQUIRED in error_codes
        assert SchemaErrorCode.UNSUPPORTED_STRING_CONSTRAINT in error_codes


class TestEnumAndConst:
    """Test that enum and const are allowed."""

    def test_enum_allowed(self):
        """Test that enum is allowed."""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "active", "completed"],
                },
            },
            "required": ["status"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        assert len(errors) == 0

    def test_const_allowed(self):
        """Test that const is allowed."""
        schema = {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "const": "1.0.0",
                },
            },
            "required": ["version"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        assert len(errors) == 0

    def test_description_allowed(self):
        """Test that description is allowed."""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The user's full name",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        errors = validate_strict_schema(schema, model="gpt-5")
        assert len(errors) == 0
