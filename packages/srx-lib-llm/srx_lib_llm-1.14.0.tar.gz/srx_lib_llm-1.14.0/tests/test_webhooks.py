"""Tests for webhook handling."""

import json

from srx_lib_llm.webhooks import BatchWebhookHandler, parse_webhook_payload


def test_webhook_handler_basic_parsing():
    """Test basic webhook payload parsing."""
    handler = BatchWebhookHandler()

    body = json.dumps(
        {"type": "batch.completed", "data": {"id": "batch_123", "status": "completed"}}
    )
    headers = {}

    event_type, batch_id, status, data = handler.verify_and_parse(body, headers)

    assert event_type == "batch.completed"
    assert batch_id == "batch_123"
    assert status == "completed"


def test_webhook_handler_nested_payload():
    """Test parsing nested payload format."""
    handler = BatchWebhookHandler()

    body = json.dumps({"payload": {"batch_id": "batch_456", "status": "failed"}})
    headers = {}

    event_type, batch_id, status, _ = handler.verify_and_parse(body, headers)

    assert batch_id == "batch_456"
    assert status == "failed"


def test_webhook_handler_should_upload_results():
    """Test result upload decision logic."""
    handler = BatchWebhookHandler()

    # Should upload on completed
    assert handler.should_upload_results("batch.completed", "completed") is True

    # Should not upload on failed
    assert handler.should_upload_results("batch.failed", "failed") is False

    # Should not upload on cancelled
    assert handler.should_upload_results("batch.cancelled", "cancelled") is False


def test_parse_webhook_payload():
    """Test convenience function."""
    body = json.dumps(
        {"type": "batch.completed", "data": {"id": "batch_789", "status": "completed"}}
    )
    headers = {}

    event_type, batch_id, status = parse_webhook_payload(body, headers)

    assert event_type == "batch.completed"
    assert batch_id == "batch_789"
    assert status == "completed"
