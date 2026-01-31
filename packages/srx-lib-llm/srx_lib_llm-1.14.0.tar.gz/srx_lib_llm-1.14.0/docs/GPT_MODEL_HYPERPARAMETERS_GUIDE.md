# GPT Model Hyperparameters Guide

**For Coding Agents: Understanding GPT-4.1 vs GPT-5 Parameter Differences**

This guide documents the critical differences between GPT-4.1 (non-reasoning) and GPT-5 (reasoning)
model families regarding supported hyperparameters. Mixing incompatible parameters is the most
common cause of 400 errors when working with these models.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Model Families](#model-families)
3. [Parameter Compatibility Matrix](#parameter-compatibility-matrix)
4. [GPT-4.1 Parameters (Sampling Controls)](#gpt-41-parameters-sampling-controls)
5. [GPT-5 Parameters (Reasoning Controls)](#gpt-5-parameters-reasoning-controls)
6. [API-Specific Rules](#api-specific-rules)
7. [Error Codes Reference](#error-codes-reference)
8. [Safe Request Profiles](#safe-request-profiles)
9. [Request Sanitization](#request-sanitization)

---

## Quick Reference

| Model Family | Use These | Do NOT Use These |
|--------------|-----------|------------------|
| **GPT-4.1** (gpt-4.1-*) | `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `logprobs` | `reasoning_effort`, `reasoning`, `verbosity` |
| **GPT-5** (gpt-5-*) | `reasoning_effort`, `verbosity` | `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `logprobs` |

---

## Model Families

### GPT-4.1 Family (Non-Reasoning)

Classic sampling-driven generation without explicit reasoning steps.

| Model | Description |
|-------|-------------|
| `gpt-4.1` | Full GPT-4.1 model |
| `gpt-4.1-mini` | Low latency, no reasoning step |
| `gpt-4.1-nano` | Smallest, fastest variant |

**Characteristic**: Uses traditional sampling controls (`temperature`, `top_p`) to control output randomness.

### GPT-5 Family (Reasoning)

Reasoning models with explicit controls for thinking depth and verbosity.

| Model | Description |
|-------|-------------|
| `gpt-5` | Full GPT-5 reasoning model |
| `gpt-5-mini` | Balanced reasoning model |
| `gpt-5-nano` | Lightweight reasoning model |
| `gpt-5.1` | Latest GPT-5 variant |
| `gpt-5.1-mini` | Latest mini variant |

**Characteristic**: Uses reasoning controls (`reasoning_effort`, `verbosity`) to control thinking depth.

---

## Parameter Compatibility Matrix

### Parameters GPT-4.1 Supports but GPT-5 Rejects

| Parameter | GPT-4.1 | GPT-5 | Notes |
|-----------|---------|-------|-------|
| `temperature` | Supported | **Rejected** | Sampling randomness control |
| `top_p` | Supported | **Rejected** | Nucleus sampling |
| `presence_penalty` | Supported | **Rejected** | Penalize new topics |
| `frequency_penalty` | Supported | **Rejected** | Penalize repetition |
| `logprobs` | Supported | **Rejected** | Return log probabilities |
| `top_logprobs` | Supported | **Rejected** | Number of top logprobs |

### Parameters GPT-5 Supports but GPT-4.1 Rejects

| Parameter | GPT-4.1 | GPT-5 | Notes |
|-----------|---------|-------|-------|
| `reasoning_effort` | **Rejected** | Supported | Controls reasoning depth |
| `reasoning` | **Rejected** | Supported | Reasoning configuration object |
| `verbosity` | **Rejected** | Supported | Controls response verbosity |

### Parameters Both Support

| Parameter | GPT-4.1 | GPT-5 | Notes |
|-----------|---------|-------|-------|
| `max_tokens` | Supported | Supported | Maximum output tokens |
| `max_completion_tokens` | Supported | Supported | Alias for max_tokens |
| `stop` | Supported | Supported | Stop sequences |
| `stream` | Supported | Supported | Streaming response |
| `response_format` | Supported | Supported | JSON mode / structured output |
| `tools` | Supported | Supported | Function calling |
| `tool_choice` | Supported | Supported | Tool selection strategy |

### Parameters to Never Send (Vendor-Specific)

| Parameter | Notes |
|-----------|-------|
| `top_k` | Not supported by OpenAI (Anthropic/others only) |
| `best_of` | Legacy parameter, not recommended |

---

## GPT-4.1 Parameters (Sampling Controls)

### temperature

Controls randomness in output generation.

```json
{
  "model": "gpt-4.1-mini",
  "temperature": 0.7
}
```

| Value | Behavior |
|-------|----------|
| `0.0` | Deterministic, always picks most likely token |
| `0.5` | Balanced randomness |
| `1.0` | More creative/random |
| `2.0` | Maximum randomness (may be incoherent) |

**Default**: `1.0`
**Range**: `0.0` to `2.0`

### top_p

Nucleus sampling - considers tokens comprising the top_p probability mass.

```json
{
  "model": "gpt-4.1-mini",
  "top_p": 0.9
}
```

**Default**: `1.0`
**Range**: `0.0` to `1.0`
**Note**: Generally recommend altering `temperature` OR `top_p`, not both.

### presence_penalty / frequency_penalty

Control repetition in generated text.

```json
{
  "model": "gpt-4.1-mini",
  "presence_penalty": 0.5,
  "frequency_penalty": 0.5
}
```

| Parameter | Effect |
|-----------|--------|
| `presence_penalty` | Penalizes new tokens based on whether they appear in text so far |
| `frequency_penalty` | Penalizes tokens based on their frequency in text so far |

**Default**: `0.0`
**Range**: `-2.0` to `2.0`

### logprobs / top_logprobs

Return log probabilities of output tokens.

```json
{
  "model": "gpt-4.1-mini",
  "logprobs": true,
  "top_logprobs": 5
}
```

**logprobs**: `true` or `false`
**top_logprobs**: `0` to `20`

---

## GPT-5 Parameters (Reasoning Controls)

### reasoning_effort

Controls how much reasoning/thinking the model does before responding.

```json
{
  "model": "gpt-5-mini",
  "reasoning_effort": "low"
}
```

| Value | Behavior | Use Case |
|-------|----------|----------|
| `none` | No reasoning step | Fast extraction, simple tasks |
| `low` | Light reasoning | Quick analysis |
| `medium` | Moderate reasoning | Balanced tasks (default for gpt-5) |
| `high` | Deep reasoning | Complex analysis, math, coding |

**Default**: `medium` (for models before gpt-5.1)
**Note**: `none` is only supported on gpt-5.1 and later.

### reasoning (Configuration Object)

Full reasoning configuration for the Responses API.

```json
{
  "model": "gpt-5-mini",
  "reasoning": {
    "effort": "low"
  }
}
```

### verbosity

Controls response verbosity level.

```json
{
  "model": "gpt-5-mini",
  "verbosity": "low"
}
```

| Value | Behavior |
|-------|----------|
| `low` | Concise responses |
| `medium` | Balanced verbosity |
| `high` | Detailed, verbose responses |

---

## API-Specific Rules

### Batch API

Each line in a batch request must be valid for the target model. Unsupported parameters
will fail the individual line item.

```json
{
  "custom_id": "req-1",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "gpt-5-mini",
    "messages": [...],
    "reasoning_effort": "low"
  }
}
```

**Error Code**: `INCOMPATIBLE_PARAMETER_FOR_MODEL`

### Chat Completions API

Same rules apply - use sampling controls for GPT-4.1, reasoning controls for GPT-5.

### Assistants API

`reasoning_effort` is part of Assistants configuration with the same model family constraints.

### Legacy Completions API

**Avoid entirely** for both GPT-4.1 and GPT-5. Use Chat Completions instead.

**Error Code**: `LEGACY_API_NOT_RECOMMENDED`

---

## Error Codes Reference

| Error Code | Description | Fix |
|------------|-------------|-----|
| `GPT5_SAMPLING_PARAMETER` | GPT-5 request contains sampling parameter | Remove temperature/top_p/penalties/logprobs |
| `GPT4_REASONING_PARAMETER` | GPT-4.1 request contains reasoning parameter | Remove reasoning_effort/reasoning/verbosity |
| `INCOMPATIBLE_PARAMETER_FOR_MODEL` | Parameter not compatible with model | Check model family and use correct controls |
| `UNKNOWN_VENDOR_PARAMETER` | Vendor-specific parameter not supported | Remove top_k/best_of/etc |
| `LEGACY_API_NOT_RECOMMENDED` | Using legacy Completions API | Switch to Chat Completions |
| `INVALID_REASONING_EFFORT` | Invalid reasoning_effort value | Use: none, low, medium, high |
| `REASONING_EFFORT_NONE_NOT_SUPPORTED` | `none` not supported for this model | Use low/medium/high for pre-5.1 models |

---

## Safe Request Profiles

### GPT-4.1 Profile (Sampling Controls)

```json
{
  "model": "gpt-4.1-mini",
  "messages": [
    {"role": "system", "content": "You are a concise assistant."},
    {"role": "user", "content": "Classify this text into tags."}
  ],
  "temperature": 0.2,
  "top_p": 1,
  "presence_penalty": 0,
  "frequency_penalty": 0
}
```

### GPT-5 Profile (Reasoning Controls)

```json
{
  "model": "gpt-5-mini-2025-08-07",
  "messages": [
    {"role": "system", "content": "You are a concise assistant."},
    {"role": "user", "content": "Classify this text into tags."}
  ],
  "reasoning_effort": "low",
  "verbosity": "low"
}
```

### GPT-5.1 Profile (No Reasoning for Fast Tasks)

```json
{
  "model": "gpt-5.1-mini",
  "messages": [
    {"role": "system", "content": "You are a concise assistant."},
    {"role": "user", "content": "Extract the name from: John Doe"}
  ],
  "reasoning_effort": "none"
}
```

### GPT-5.1 with Medium Reasoning (Recommended for Complex Analysis)

```json
{
  "model": "gpt-5.1-2025-11-13",
  "messages": [
    {"role": "system", "content": "You are an expert competency assessor using systematic reasoning."},
    {"role": "user", "content": "Analyze candidate assessment documents through sequential reasoning..."}
  ],
  "reasoning_effort": "medium"
}
```

**Use cases:**
- Complex multi-step analysis requiring deeper thinking
- Competency assessments with evidence triangulation
- 6-task agentic reasoning chains
- Situations requiring systematic problem decomposition

**Benefits over lower reasoning:**
- Higher accuracy on complex analysis tasks (target: 80%+ vs 65-70% baseline)
- Better handling of multi-document evidence synthesis
- More consistent pattern matching across diverse inputs

**Trade-offs:**
- 3-5x cost increase vs gpt-4.1-mini
- Higher latency (typically 10-30s vs 2-5s)
- Best for quality-critical use cases where accuracy justifies cost

---

## Request Sanitization

### Python Implementation

```python
from srx_lib_llm import sanitize_request, is_gpt5_model

# Automatically removes incompatible parameters
request = {
    "model": "gpt-5-mini",
    "messages": [...],
    "temperature": 0.7,  # Will be removed for GPT-5
    "reasoning_effort": "low"  # Will be kept
}

clean_request = sanitize_request(request)
# Result: {"model": "gpt-5-mini", "messages": [...], "reasoning_effort": "low"}
```

### Validation Only (No Modification)

```python
from srx_lib_llm import validate_request_params, RequestValidationException

try:
    validate_request_params(request, raise_on_error=True)
except RequestValidationException as e:
    print(f"Found {e.error_count} parameter issues:")
    for error in e.errors:
        print(f"  - {error.code}: {error.message}")
```

---

## Operational Checklist

1. **Schema Validation**: Use `validate_strict_schema()` for JSON schema compliance
2. **Parameter Validation**: Use `validate_request_params()` for hyperparameter compatibility
3. **Auto-Sanitization**: Use `sanitize_request()` for automatic cleanup
4. **Model Pinning**: Use exact snapshots (e.g., `gpt-5-mini-2025-08-07`) in production

---

## References

- [OpenAI API Reference - Chat](https://platform.openai.com/docs/api-reference/chat)
- [OpenAI API Reference - Responses](https://platform.openai.com/docs/api-reference/responses)
- [Using GPT-5.1 Guide](https://platform.openai.com/docs/guides/latest-model)
- [OpenAI Graders Guide](https://platform.openai.com/docs/guides/graders)
