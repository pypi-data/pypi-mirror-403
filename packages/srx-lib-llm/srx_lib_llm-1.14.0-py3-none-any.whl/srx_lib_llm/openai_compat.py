from __future__ import annotations

import inspect
import os
from typing import Any, Dict, Optional, Type


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _coerce_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None


def get_openai_base_url() -> Optional[str]:
    for key in ("OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_API_URL"):
        value = os.getenv(key)
        if value:
            return value.rstrip("/")
    return None


def get_openai_use_responses_api() -> bool:
    explicit = _coerce_bool(os.getenv("OPENAI_USE_RESPONSES_API"))
    if explicit is not None:
        return explicit

    mode = os.getenv("OPENAI_API_MODE")
    if mode:
        normalized = mode.strip().lower()
        if normalized in {"responses", "response", "responses_api"}:
            return True
        if normalized in {"chat", "chat_completions", "completions"}:
            return False

    # Default to chat completions when a custom base URL is configured.
    if get_openai_base_url():
        return False

    return True


def get_openai_client_kwargs() -> Dict[str, Any]:
    base_url = get_openai_base_url()
    return {"base_url": base_url} if base_url else {}


def get_chat_openai_base_url_kwargs(chat_openai_cls: Type[Any]) -> Dict[str, Any]:
    base_url = get_openai_base_url()
    if not base_url:
        return {}

    try:
        params = inspect.signature(chat_openai_cls.__init__).parameters
    except (TypeError, ValueError):
        return {}

    if "base_url" in params:
        return {"base_url": base_url}
    if "openai_api_base" in params:
        return {"openai_api_base": base_url}
    return {}
