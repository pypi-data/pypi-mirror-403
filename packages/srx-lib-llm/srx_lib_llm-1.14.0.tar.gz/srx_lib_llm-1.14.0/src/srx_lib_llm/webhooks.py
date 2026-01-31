"""OpenAI Batch API webhook handling and verification.

This module provides utilities for:
- Webhook signature verification
- Event parsing and normalization
- Callback payload handling
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


class WebhookVerificationError(Exception):
    """Raised when webhook verification fails."""

    pass


class BatchWebhookHandler:
    """Handler for OpenAI Batch API webhooks."""

    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook handler.

        Args:
            webhook_secret: OpenAI webhook secret for signature verification
        """
        self.webhook_secret = webhook_secret

    def verify_and_parse(
        self, body: str, headers: Dict[str, str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Verify webhook signature and parse event.

        Args:
            body: Raw webhook body as string
            headers: Request headers

        Returns:
            Tuple of (event_type, batch_id, status, data_section)

        Raises:
            WebhookVerificationError: If signature verification fails
        """
        event_type: Optional[str] = None
        batch_id: Optional[str] = None
        status: Optional[str] = None
        data_section: Dict[str, Any] = {}

        # Verify signature if secret is configured
        if self.webhook_secret:
            try:
                from openai import OpenAI

                client = OpenAI(webhook_secret=self.webhook_secret)
                event = client.webhooks.unwrap(body, headers)

                event_type = getattr(event, "type", None)
                data = getattr(event, "data", {})
                data_section = self._object_to_dict(data)
                batch_id = self._safe_get(data, "id") or data_section.get("id")
                status = self._safe_get(data, "status") or data_section.get("status")

            except ImportError as exc:
                raise WebhookVerificationError(
                    "OpenAI SDK required for webhook verification"
                ) from exc
            except Exception as exc:
                raise WebhookVerificationError(
                    f"Webhook signature verification failed: {exc}"
                ) from exc

        # Parse body as JSON
        parsed_body: Dict[str, Any] = {}
        if body:
            try:
                loaded = json.loads(body)
                if isinstance(loaded, dict):
                    parsed_body = loaded
            except json.JSONDecodeError as exc:
                if not data_section:  # Only fail if we didn't get verified data
                    raise WebhookVerificationError(f"Invalid JSON payload: {exc}") from exc

        # Extract from various payload formats
        batch_id, status, event_type, data_section = self._extract_from_payload(
            parsed_body, batch_id, status, event_type, data_section
        )

        return event_type, batch_id, status, data_section

    def _extract_from_payload(
        self,
        parsed_body: Dict[str, Any],
        batch_id: Optional[str],
        status: Optional[str],
        event_type: Optional[str],
        data_section: Dict[str, Any],
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Extract batch info from various payload formats."""
        # Try data section
        body_data = parsed_body.get("data")
        if isinstance(body_data, dict):
            if not data_section:
                data_section = body_data
            event_type = event_type or parsed_body.get("type")
            batch_id = batch_id or body_data.get("id") or body_data.get("batch_id")
            status = status or body_data.get("status")

        # Try payload section
        payload_section = parsed_body.get("payload")
        if isinstance(payload_section, dict):
            batch_id = batch_id or payload_section.get("batch_id")
            status = status or payload_section.get("status")

        # Try top-level fields
        if parsed_body:
            batch_id = batch_id or parsed_body.get("batch_id") or parsed_body.get("id")
            status = status or parsed_body.get("status")
            event_type = event_type or parsed_body.get("type")

        # Fallback to data_section
        if not batch_id and data_section:
            batch_id = data_section.get("batch_id") or data_section.get("id")

        if not status and data_section:
            status = data_section.get("status")

        # Normalize event_type from status if needed
        if status and not event_type:
            normalized_status = status.lower()
            event_type = {
                "completed": "batch.completed",
                "succeeded": "batch.completed",
                "failed": "batch.failed",
                "errored": "batch.failed",
                "cancelled": "batch.cancelled",
                "canceled": "batch.cancelled",
            }.get(normalized_status)

        return batch_id, status, event_type, data_section

    def _safe_get(self, obj: Any, key: str, default: Any = None) -> Any:
        """Safely get attribute or key from object."""
        try:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        except Exception:
            return default

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary."""
        if isinstance(obj, dict):
            return obj

        for attr in ("model_dump", "dict", "to_dict"):
            if hasattr(obj, attr):
                try:
                    result = getattr(obj, attr)()
                    if isinstance(result, dict):
                        return result
                except Exception:
                    continue

        if hasattr(obj, "__dict__"):
            try:
                return dict(obj.__dict__)
            except Exception:
                return {}

        return {}

    def should_upload_results(self, event_type: Optional[str], status: Optional[str]) -> bool:
        """Determine if results should be uploaded based on event and status.

        Args:
            event_type: Event type (e.g., "batch.completed")
            status: Batch status (e.g., "completed")

        Returns:
            True if results should be uploaded, False otherwise
        """
        normalized_event = (event_type or "").lower()
        normalized_status = (status or "").lower()

        completed_statuses = {"completed", "succeeded"}
        skip_statuses = {"failed", "errored", "cancelled", "canceled"}

        # Check event type first
        if normalized_event and normalized_event != "batch.completed":
            return False

        # Check status
        if normalized_status:
            if normalized_status in completed_statuses:
                return True
            elif normalized_status in skip_statuses:
                return False

        # Default to True if we have a completed event or status
        return normalized_event == "batch.completed" or normalized_status in completed_statuses


def parse_webhook_payload(
    body: str, headers: Dict[str, str], webhook_secret: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Convenience function to parse webhook payload.

    Args:
        body: Raw webhook body as string
        headers: Request headers
        webhook_secret: Optional webhook secret for verification

    Returns:
        Tuple of (event_type, batch_id, status)

    Raises:
        WebhookVerificationError: If signature verification fails
    """
    handler = BatchWebhookHandler(webhook_secret=webhook_secret)
    event_type, batch_id, status, _ = handler.verify_and_parse(body, headers)
    return event_type, batch_id, status
