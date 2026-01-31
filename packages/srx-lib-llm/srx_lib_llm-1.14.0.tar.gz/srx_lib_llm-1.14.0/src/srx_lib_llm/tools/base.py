from __future__ import annotations

from typing import List, Callable
from langchain_core.tools import BaseTool

from ..instrumentation import apply_callbacks_to_runnable, get_langfuse_handler


_strategies: list["ToolStrategyBase"] = []


class ToolStrategyBase:
    """Base class for tool strategies.

    Implement `make_tools()` to return a list of LangChain tools.
    Optionally implement `fallback(question: str)` for error fallback.
    """

    def make_tools(self) -> List[BaseTool]:  # pragma: no cover - abstract
        return []

    async def fallback(self, question: str) -> str:  # pragma: no cover - optional
        return ""

    @staticmethod
    def build_agent_for_tools(tools: List[BaseTool]) -> Callable:
        # Minimal agent builder using LangGraph's create_react_agent (LangChain v1 compatible)
        # Kept generic; users can customize at service level.
        from langgraph.prebuilt import create_react_agent
        from langchain_openai import ChatOpenAI
        import os

        # Use official OpenAI only
        langfuse_handler = get_langfuse_handler()
        callbacks = [langfuse_handler] if langfuse_handler else None
        from ..openai_compat import (
            get_chat_openai_base_url_kwargs,
            get_openai_use_responses_api,
        )

        use_responses_api = get_openai_use_responses_api()
        llm_kwargs = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0,
            "callbacks": callbacks,
            "use_responses_api": use_responses_api,
            **get_chat_openai_base_url_kwargs(ChatOpenAI),
        }
        if use_responses_api:
            llm_kwargs["output_version"] = "responses/v1"
        llm = ChatOpenAI(**llm_kwargs)

        # create_react_agent returns a LangGraph graph that can be invoked directly
        graph = create_react_agent(llm, tools)
        return apply_callbacks_to_runnable(graph)


def register_strategy(strategy: "ToolStrategyBase") -> None:
    _strategies.append(strategy)


def get_strategies() -> list["ToolStrategyBase"]:
    return list(_strategies)
