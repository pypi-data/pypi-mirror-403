import asyncio
import json
import os

from srx_lib_llm import extract_structured, responses_chat


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL")

    if not api_key or not base_url or not model:
        print(
            "Missing required env vars. Set OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_MODEL."
        )
        return

    if not os.getenv("OPENAI_API_MODE") and not os.getenv("OPENAI_USE_RESPONSES_API"):
        print(
            "Tip: set OPENAI_API_MODE=chat for Qwen-compatible endpoints "
            "or OPENAI_USE_RESPONSES_API=true if Responses API is supported."
        )

    print("Running chat smoke test...")
    chat_text = await responses_chat("Hello, can you summarize your capabilities?")
    print(chat_text)

    print("\nRunning structured output smoke test...")
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "confidence": {"type": "string"},
            "reasoning": {"type": "string"},
        },
        "required": ["summary", "confidence", "reasoning"],
    }
    result = await extract_structured(
        text="Summarize the following message: Qwen is an OpenAI-compatible LLM.",
        json_schema=schema,
        schema_name="QwenSummary",
    )
    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    else:
        payload = result.dict()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
