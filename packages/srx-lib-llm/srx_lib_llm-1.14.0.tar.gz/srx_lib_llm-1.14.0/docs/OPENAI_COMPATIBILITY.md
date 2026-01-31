# OpenAI-Compatible Providers (Qwen Example)

This library defaults to OpenAI's official API, but you can point it at
OpenAI-compatible endpoints by setting environment variables.

## Minimal Configuration

Set the base URL, model, and key:

```
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://d3hip1bjwcdu0p.cloudfront.net/api"
export OPENAI_MODEL="ds-news-aggregator"
export OPENAI_API_MODE="chat"
```

Notes:
- `OPENAI_BASE_URL` should be the root URL (the client appends `/chat/completions`).
- `OPENAI_API_MODE="chat"` disables Responses API usage, which many compatible
  providers do not implement.
- If your provider *does* support Responses API, set `OPENAI_USE_RESPONSES_API=true`.

## Structured Outputs

Structured outputs keep working as long as the provider supports OpenAI-style
`response_format` / JSON schema output.

Example (async):

```
from srx_lib_llm import extract_structured

schema = {
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "score": {"type": "number"}
  },
  "required": ["title"]
}

result = await extract_structured(
    text="Analyze this passage...", json_schema=schema, schema_name="Scorecard"
)
print(result.model_dump())
```

## Known Limitations

- `extract_structured_gpt51` uses the Responses API and is intended for OpenAI GPT-5.*
- The OpenAI Batch API helpers are OpenAI-specific and may not work on other providers.
