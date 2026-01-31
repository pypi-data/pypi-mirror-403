# OpenAI Structured Outputs JSON Schema Validation Guide

**For Coding Agents: Validating Structured Output and Batch API Inputs**

This guide provides comprehensive validation rules for OpenAI's Structured Outputs feature
across the Batch API, Chat Completions API, and Assistants API. Use this as a reference
when validating JSON schemas before submission.

---

## Table of Contents

1. [Quick Decision Rule](#quick-decision-rule)
2. [When Validation Applies](#when-validation-applies)
3. [Universal JSON Schema Essentials](#universal-json-schema-essentials)
4. [OpenAI Strict Mode Requirements](#openai-strict-mode-requirements)
5. [Forbidden Keywords](#forbidden-keywords)
6. [API-Specific Requirements](#api-specific-requirements)
7. [Model Requirements](#model-requirements)
8. [Error Codes Reference](#error-codes-reference)
9. [Copy-Paste Templates](#copy-paste-templates)

---

## Quick Decision Rule

Choose ONE approach for structured outputs:

| Goal | Configuration |
|------|---------------|
| **Strict response schema** (final answer) | `response_format.type = "json_schema"` with `strict: true` |
| **Strict tool arguments** (actions) | `tools[].function.strict = true` + `parallel_tool_calls: false` |

---

## When Validation Applies

**IMPORTANT**: Strict mode validation rules ONLY apply to GPT-5* models.

| Model Pattern | Strict Mode Rules Apply |
|---------------|------------------------|
| `gpt-5*` (e.g., `gpt-5`, `gpt-5-mini`, `gpt-5.1`, `gpt-5.1-mini`) | **YES** |
| `gpt-4*` (e.g., `gpt-4`, `gpt-4-turbo`, `gpt-4o`) | NO - pass through as-is |
| `gpt-3.5*` | NO - pass through as-is |
| Other models | NO - pass through as-is |

When using non-GPT-5 models, the validator will skip strict mode checks and pass
the schema through unchanged.

---

## Universal JSON Schema Essentials

### Supported Types

```
object, array, string, number, integer, boolean, null
```

### Core Keywords

| Category | Supported Keywords |
|----------|-------------------|
| **Objects** | `properties`, `required`, `additionalProperties` |
| **Arrays** | `items`, `prefixItems` (if supported) |
| **Reuse** | `$defs`/`definitions` with internal `$ref` only |
| **Constraints** | `enum`, `const`, `description` |

---

## OpenAI Strict Mode Requirements

These rules MUST be followed for GPT-5* models with `strict: true`:

### 1. Enable Strict Mode

```json
// Response schema
{
  "response_format": {
    "json_schema": {
      "strict": true,
      ...
    }
  }
}

// Tool schema
{
  "tools": [{
    "function": {
      "strict": true,
      ...
    }
  }]
}
```

**Error Code**: `STRICT_MODE_NOT_ENABLED`

### 2. Lock Extra Keys on All Objects

Every object with `properties` MUST have `additionalProperties: false`.

```json
// CORRECT
{
  "type": "object",
  "additionalProperties": false,
  "properties": { ... }
}

// WRONG - will cause 400 error
{
  "type": "object",
  "properties": { ... }
}
```

**Error Code**: `MISSING_ADDITIONAL_PROPERTIES_FALSE`

### 3. All Properties Must Be Required

In strict mode, ALL keys in `properties` MUST be listed in `required`.

```json
// CORRECT
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "integer" }
  },
  "required": ["name", "age"]
}

// WRONG - "age" not in required
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "integer" }
  },
  "required": ["name"]
}
```

**Error Code**: `PROPERTY_NOT_IN_REQUIRED`

### 4. Optional Fields Use Nullable Types

Model optional fields by keeping them in `required` but allowing `null`:

```json
// CORRECT - optional field pattern
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "nickname": { "type": ["string", "null"] }
  },
  "required": ["name", "nickname"],
  "additionalProperties": false
}

// WRONG - missing from required
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "nickname": { "type": "string" }
  },
  "required": ["name"]
}
```

**Error Code**: `OPTIONAL_FIELD_NOT_NULLABLE`

### 5. Disable Parallel Tool Calls

When using strict tool schemas:

```json
{
  "parallel_tool_calls": false,
  "tools": [...]
}
```

**Error Code**: `PARALLEL_TOOL_CALLS_WITH_STRICT`

### 6. Handle Refusals

Even with strict schemas, the API may return a refusal. Your code must handle:

```json
{
  "refusal": "I cannot provide that information."
}
```

---

## Forbidden Keywords

These keywords will cause hard errors or are frequently rejected in strict mode:

### Hard Errors (Never Use)

| Keyword | Error Code |
|---------|------------|
| `oneOf` | `FORBIDDEN_KEYWORD_ONEOF` |

### Frequently Rejected (Avoid)

| Category | Keywords | Error Code |
|----------|----------|------------|
| **Strings** | `minLength`, `maxLength`, `pattern`, `format` | `UNSUPPORTED_STRING_CONSTRAINT` |
| **Numbers** | `minimum`, `maximum`, `multipleOf` | `UNSUPPORTED_NUMBER_CONSTRAINT` |
| **Objects** | `patternProperties`, `unevaluatedProperties`, `propertyNames`, `minProperties`, `maxProperties` | `UNSUPPORTED_OBJECT_CONSTRAINT` |
| **Arrays** | `contains`, `minItems`, `maxItems`, `uniqueItems`, `unevaluatedItems` | `UNSUPPORTED_ARRAY_CONSTRAINT` |
| **Other** | `default` | `UNSUPPORTED_DEFAULT_KEYWORD` |

### Recommendation

Use `enum` and `description` for constraints. Validate advanced rules in application
code after parsing.

---

## API-Specific Requirements

### Chat Completions API

```json
{
  "model": "gpt-5-mini-2025-08-07",
  "messages": [...],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "my_schema",
      "strict": true,
      "schema": { ... }
    }
  }
}
```

### Assistants API

```json
{
  "model": "gpt-5-mini",
  "tools": [{
    "type": "function",
    "function": {
      "name": "my_tool",
      "strict": true,
      "parameters": { ... }
    }
  }]
}
```

### Batch API

The Batch API wraps the underlying endpoint. Include the same `response_format`
or strict tool schemas you would send to Chat Completions:

```json
{
  "custom_id": "request-1",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [...],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "extraction_result",
        "strict": true,
        "schema": { ... }
      }
    }
  }
}
```

---

## Model Requirements

For production repeatability, use pinned model snapshots:

```json
{ "model": "gpt-5-mini-2025-08-07" }
```

### Model Detection Pattern

```python
def is_gpt5_model(model: str) -> bool:
    """Check if model is GPT-5 family (requires strict mode validation)."""
    return model.startswith("gpt-5")
```

---

## Error Codes Reference

| Error Code | Description | Fix |
|------------|-------------|-----|
| `STRICT_MODE_NOT_ENABLED` | Missing `strict: true` | Add `strict: true` to json_schema or function |
| `MISSING_ADDITIONAL_PROPERTIES_FALSE` | Object missing `additionalProperties: false` | Add to every object with properties |
| `PROPERTY_NOT_IN_REQUIRED` | Property in `properties` not in `required` | Add all property keys to required array |
| `OPTIONAL_FIELD_NOT_NULLABLE` | Optional field should use nullable type | Change type to `["string", "null"]` pattern |
| `PARALLEL_TOOL_CALLS_WITH_STRICT` | `parallel_tool_calls` not disabled | Set `parallel_tool_calls: false` |
| `FORBIDDEN_KEYWORD_ONEOF` | Schema contains `oneOf` | Remove and restructure schema |
| `UNSUPPORTED_STRING_CONSTRAINT` | Using minLength/maxLength/pattern/format | Remove and validate in application code |
| `UNSUPPORTED_NUMBER_CONSTRAINT` | Using minimum/maximum/multipleOf | Remove and validate in application code |
| `UNSUPPORTED_OBJECT_CONSTRAINT` | Using patternProperties/etc. | Remove and validate in application code |
| `UNSUPPORTED_ARRAY_CONSTRAINT` | Using contains/minItems/maxItems/etc. | Remove and validate in application code |
| `UNSUPPORTED_DEFAULT_KEYWORD` | Using `default` keyword | Remove default values |
| `INVALID_TYPE` | Unknown type value | Use: object, array, string, number, integer, boolean, null |
| `MISSING_TYPE` | Schema node missing `type` | Add explicit type to all schema nodes |
| `MISSING_ITEMS` | Array missing `items` definition | Add items schema for array types |
| `INVALID_REF` | External $ref or invalid reference | Use only internal references to $defs |

---

## Copy-Paste Templates

### Strict Response Schema (Final Answer)

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "your_schema_name",
      "strict": true,
      "schema": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "status": { "type": "string", "enum": ["ok", "error"] },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "id": { "type": "string" },
                "title": { "type": ["string", "null"] }
              },
              "required": ["id", "title"]
            }
          }
        },
        "required": ["status", "items"]
      }
    }
  }
}
```

### Strict Tool Arguments (Actions)

```json
{
  "parallel_tool_calls": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "your_tool",
        "description": "One sentence.",
        "strict": true,
        "parameters": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "query": { "type": "string" },
            "limit": { "type": ["integer", "null"] }
          },
          "required": ["query", "limit"]
        }
      }
    }
  ]
}
```

### Batch API Request with Structured Output

```json
{
  "custom_id": "req-001",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [
      {"role": "system", "content": "Extract data per schema."},
      {"role": "user", "content": "John Doe, age 30, NYC"}
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "person",
        "strict": true,
        "schema": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "name": {"type": "string"},
            "age": {"type": ["integer", "null"]},
            "city": {"type": ["string", "null"]}
          },
          "required": ["name", "age", "city"]
        }
      }
    }
  }
}
```

---

## References

- [OpenAI Structured Outputs Introduction](https://openai.com/index/introducing-structured-outputs-in-the-api/)
- [OpenAI Cookbook: Structured Outputs](https://cookbook.openai.com/examples/structured_outputs_intro)
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Developer Community: Schema Support](https://community.openai.com/t/official-documentation-for-supported-schemas-for-response-format-parameter-in-calls-to-client-beta-chats-completions-parse/932422)
