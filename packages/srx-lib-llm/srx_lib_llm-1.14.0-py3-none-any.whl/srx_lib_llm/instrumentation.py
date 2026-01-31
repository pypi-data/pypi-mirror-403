from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from langchain_core.callbacks.base import BaseCallbackHandler


logger = logging.getLogger(__name__)

_REQUIRED_ENV_VARS: Tuple[str, ...] = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
_LANGFUSE_ENABLED_FLAGS: Tuple[str, ...] = (
    "LANGFUSE_ENABLED",
    "LANGFUSE_TRACING_ENABLED",
)
_WARNED_MESSAGES: set[str] = set()


def _log_once(message: str, level: int = logging.INFO) -> None:
    if message in _WARNED_MESSAGES:
        return
    _WARNED_MESSAGES.add(message)
    logger.log(level, message)


def _env_has_required_keys() -> bool:
    return all(os.getenv(var) for var in _REQUIRED_ENV_VARS)


def _is_explicitly_disabled() -> bool:
    for flag in _LANGFUSE_ENABLED_FLAGS:
        value = os.getenv(flag)
        if value is None:
            continue
        lowered = value.strip().lower()
        if lowered in {"0", "false", "no", "off"}:
            return True
    return False


@lru_cache(maxsize=4)
def _load_langfuse_handler(*, update_trace: bool = False) -> Optional["BaseCallbackHandler"]:
    if _is_explicitly_disabled():
        _log_once("Langfuse tracing explicitly disabled via environment variable.", logging.DEBUG)
        return None

    if not _env_has_required_keys():
        missing = [var for var in _REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing:
            _log_once(
                "Langfuse tracing skipped because required environment variables are missing: "
                + ", ".join(missing),
                logging.DEBUG,
            )
        return None

    try:
        from langfuse.langchain import CallbackHandler
    except ModuleNotFoundError:
        _log_once(
            "Langfuse package not installed; skipping LangChain/LangGraph tracing.",
            logging.DEBUG,
        )
        return None
    except Exception as exc:  # pragma: no cover - unexpected import errors
        _log_once(
            f"Langfuse handler import failed; tracing disabled. Error: {exc}",
            logging.WARNING,
        )
        return None

    try:
        return CallbackHandler(update_trace=update_trace)
    except Exception as exc:  # pragma: no cover - defensive
        _log_once(
            f"Langfuse handler initialization failed; tracing disabled. Error: {exc}",
            logging.WARNING,
        )
        return None


def get_langfuse_handler(*, update_trace: bool = False) -> Optional["BaseCallbackHandler"]:
    """Return a configured Langfuse CallbackHandler or None if unavailable."""

    handler = _load_langfuse_handler(update_trace=update_trace)
    return handler


def get_langfuse_callbacks(*, update_trace: bool = False) -> List["BaseCallbackHandler"]:
    handler = get_langfuse_handler(update_trace=update_trace)
    return [handler] if handler else []


def build_langchain_config(
    *,
    update_trace: bool = False,
    base: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a LangChain RunnableConfig dict enriched with Langfuse callbacks.

    Args:
        update_trace: Whether to update the Langfuse trace with chain input/output.
        base: Base config dict to extend (e.g., {"configurable": {"thread_id": "..."}}).
        trace_id: Optional trace ID for Langfuse feedback linking. If provided, will be
            set as the run_id in the config (converted to UUID format).
        session_id: Optional Langfuse session ID for grouping traces.
        user_id: Optional Langfuse user ID for attribution.
        tags: Optional list of tags for the Langfuse trace.

    Returns:
        A RunnableConfig dict with Langfuse callbacks attached.
    """
    import uuid as uuid_module

    config: Dict[str, Any] = dict(base or {})

    # Set run_id from trace_id if provided (for Langfuse feedback linking)
    if trace_id:
        try:
            # Convert string trace_id to UUID for RunnableConfig compatibility
            config["run_id"] = uuid_module.UUID(trace_id)
        except (ValueError, TypeError):
            _log_once(
                f"Invalid trace_id format '{trace_id}'; must be a valid UUID string. Ignoring.",
                logging.WARNING,
            )

    # Add Langfuse-specific metadata for session/user/tags
    if session_id or user_id or tags:
        metadata = config.get("metadata", {})
        if session_id:
            metadata["langfuse_session_id"] = session_id
        if user_id:
            metadata["langfuse_user_id"] = user_id
        if tags:
            metadata["langfuse_tags"] = tags
        config["metadata"] = metadata

    callbacks = get_langfuse_callbacks(update_trace=update_trace)
    if not callbacks:
        return config

    existing = config.get("callbacks")
    if existing is None:
        config["callbacks"] = callbacks
        return config

    if isinstance(existing, list):
        # Extend while preserving existing callbacks
        config["callbacks"] = [*existing, *callbacks]
        return config

    # If callbacks already set via manager or custom type, leave untouched but warn once.
    _log_once(
        "Langfuse callbacks could not be attached because a non-list callback manager is already provided.",
        logging.DEBUG,
    )
    return config


def apply_callbacks_to_runnable(runnable: Any, *, update_trace: bool = False) -> Any:
    """Attach Langfuse callbacks to a Runnable if supported."""

    callbacks = get_langfuse_callbacks(update_trace=update_trace)
    if not callbacks or not hasattr(runnable, "with_config"):
        return runnable
    try:
        return runnable.with_config(callbacks=callbacks)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_once(
            f"Failed to apply Langfuse callbacks to runnable; continuing without tracing. Error: {exc}",
            logging.DEBUG,
        )
        return runnable
