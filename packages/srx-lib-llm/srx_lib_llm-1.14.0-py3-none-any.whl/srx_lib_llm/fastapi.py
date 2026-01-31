"""FastAPI integration helpers for OpenAI Batch API.

This module provides utilities and route builders for integrating
batch processing into FastAPI applications.
"""

from __future__ import annotations

import io
import json
import os
from typing import Any, Dict, Optional

from srx_lib_llm.batch import BatchEndpoint, BatchPayload, OpenAIBatchService
from srx_lib_llm.openai_compat import get_openai_client_kwargs
from srx_lib_llm.mapping import BatchMappingStore, resolve_output_path
from srx_lib_llm.schemas import (
    BatchCallbackResponse,
    BatchMappingResponse,
    BatchStartRequest,
    BatchStartResponse,
    BatchStatusResponse,
)
from srx_lib_llm.storage import StorageProvider
from srx_lib_llm.webhooks import BatchWebhookHandler


class BatchAPIHandler:
    """Handler for batch API operations in FastAPI."""

    def __init__(
        self,
        storage: StorageProvider,
        batch_service: Optional[OpenAIBatchService] = None,
        webhook_secret: Optional[str] = None,
        mapping_prefix: str = "mappings/batches",
    ):
        """Initialize batch API handler.

        Args:
            storage: Storage provider for files
            batch_service: Optional OpenAIBatchService instance
            webhook_secret: Optional webhook secret for verification
            mapping_prefix: Prefix for mapping documents
        """
        self.storage = storage
        self.batch_service = batch_service or OpenAIBatchService()
        self.webhook_handler = BatchWebhookHandler(webhook_secret=webhook_secret)
        self.mapping_store = BatchMappingStore(storage, prefix=mapping_prefix)

    async def start_batch(self, request: BatchStartRequest) -> BatchStartResponse:
        """Start a new batch job.

        Args:
            request: Batch start request

        Returns:
            Batch start response with batch ID and mapping path
        """
        # Handle pre-formatted batch JSONL (already in OpenAI format)
        if request.preformatted_batch:
            import httpx
            from openai import AsyncOpenAI

            # Download pre-formatted JSONL
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(str(request.jsonl_url))
                response.raise_for_status()
                jsonl_content = response.content

            # Upload directly to OpenAI
            openai_client = AsyncOpenAI(**get_openai_client_kwargs())
            import io

            file_obj = await openai_client.files.create(
                file=io.BytesIO(jsonl_content), purpose="batch"
            )

            # Create batch directly
            batch = await openai_client.batches.create(
                input_file_id=file_obj.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
            )

            # Create mapping for tracking
            from srx_lib_llm.batch import BatchMapping, BatchStatus
            from datetime import datetime

            mapping = BatchMapping(
                batch_id=batch.id,
                input_file_id=file_obj.id,
                output_file_id=None,
                error_file_id=None,
                input_path=str(request.jsonl_url),
                status=BatchStatus(batch.status),
                created_at=datetime.fromtimestamp(batch.created_at),
            )

            batch_id = batch.id
            status = batch.status
        else:
            # Build BatchPayload from request
            payload_dict = request.batch_payload or {}
            payload = BatchPayload(
                endpoint=BatchEndpoint.CHAT_COMPLETIONS,
                **payload_dict,
            )

            # Create batch
            mapping = await self.batch_service.create_batch_from_url(
                url=str(request.jsonl_url),
                payload=payload,
            )

            batch_id = mapping.batch_id
            status = mapping.status.value if mapping.status else None

        # Save mapping document
        mapping_path = await self.mapping_store.save_mapping(
            batch_id=batch_id,
            input_url=str(request.jsonl_url),
            business_date=request.date,
            status=status,
            lib_mapping=mapping,
            pipeline_prefix=request.pipeline_prefix or "attachments",
            output_filename=request.output_filename or "batch_output.jsonl",
            use_nodash_date=request.use_nodash_date or True,
        )

        return BatchStartResponse(
            batch_id=batch_id,
            status=status,
            mapping_path=mapping_path,
        )

    async def handle_callback(self, body: str, headers: Dict[str, str]) -> BatchCallbackResponse:
        """Handle batch callback webhook.

        Args:
            body: Raw request body
            headers: Request headers

        Returns:
            Callback response with upload status
        """
        # Parse webhook
        event_type, batch_id, status, _ = self.webhook_handler.verify_and_parse(body, headers)

        if not batch_id:
            raise ValueError("batch_id is required in webhook payload")

        # Resolve output path
        lib_mapping = self.batch_service.get_mapping(batch_id)
        output_path = await resolve_output_path(
            batch_id=batch_id,
            storage=self.storage,
            lib_mapping=lib_mapping,
            mapping_store=self.mapping_store,
        )

        if not output_path:
            raise ValueError(f"Output path not found for batch {batch_id}")

        # Check if we should upload results
        should_upload = self.webhook_handler.should_upload_results(event_type, status)

        uploaded = False
        if should_upload:
            # Get batch results
            results = await self.batch_service.get_batch_results(batch_id)

            # Serialize results
            lines = []
            for result in results:
                try:
                    obj = {
                        "custom_id": result.custom_id,
                        "response": result.response,
                        "error": result.error,
                    }
                    lines.append(json.dumps(obj))
                except Exception:
                    lines.append(json.dumps({"raw": str(result)}))

            data = "\n".join(lines).encode("utf-8")

            # Upload to storage
            stream = io.BytesIO(data)
            await self.storage.upload_stream(
                stream, output_path, content_type="application/x-ndjson"
            )
            uploaded = True

            # Update mapping status
            if status:
                await self.mapping_store.update_status(batch_id, status)

        return BatchCallbackResponse(
            batch_id=batch_id,
            output_path=output_path,
            uploaded=uploaded,
        )

    async def get_status(self, batch_id: str) -> BatchStatusResponse:
        """Get batch status.

        Args:
            batch_id: Batch ID

        Returns:
            Batch status response
        """
        # Get status from OpenAI
        info = await self.batch_service.get_batch_status(batch_id)

        # Get mapping
        lib_mapping = self.batch_service.get_mapping(batch_id)
        sidecar_mapping = await self.mapping_store.get_mapping(batch_id)

        # Build response
        mapping_response = None
        if lib_mapping:
            mapping_response = BatchMappingResponse(
                batch_id=lib_mapping.batch_id,
                input_file_id=lib_mapping.input_file_id,
                output_file_id=lib_mapping.output_file_id,
                error_file_id=lib_mapping.error_file_id,
                input_path=lib_mapping.input_path,
                output_path=lib_mapping.output_path,
                error_path=lib_mapping.error_path,
                status=lib_mapping.status,
                created_at=lib_mapping.created_at,
            )

        return BatchStatusResponse(
            id=info.id,
            status=info.status,
            input_file_id=info.input_file_id,
            output_file_id=info.output_file_id,
            error_file_id=info.error_file_id,
            created_at=info.created_at,
            completed_at=info.completed_at,
            failed_at=info.failed_at,
            expired_at=info.expired_at,
            cancelled_at=info.cancelled_at,
            request_counts=info.request_counts,
            metadata=info.metadata,
            errors=info.errors,
            mapping=mapping_response,
            sidecar_mapping=sidecar_mapping,
        )


def create_batch_router(
    storage: StorageProvider,
    batch_service: Optional[OpenAIBatchService] = None,
    webhook_secret: Optional[str] = None,
    prefix: str = "",
    tags: Optional[list[str]] = None,
) -> Any:
    """Create FastAPI router with batch endpoints.

    Args:
        storage: Storage provider
        batch_service: Optional OpenAIBatchService instance
        webhook_secret: Optional webhook secret
        prefix: Router prefix
        tags: Router tags

    Returns:
        FastAPI APIRouter

    Example:
        ```python
        from fastapi import FastAPI
        from srx_lib_llm.fastapi import create_batch_router
        from srx_lib_llm.storage import LocalStorageProvider

        app = FastAPI()
        storage = LocalStorageProvider()
        router = create_batch_router(storage, tags=["Batch"])
        app.include_router(router, prefix="/api/batch")
        ```
    """
    try:
        from fastapi import APIRouter, HTTPException, Request
    except ImportError as exc:
        raise ImportError(
            "FastAPI required for router creation. Install with: pip install fastapi"
        ) from exc

    router = APIRouter(prefix=prefix, tags=tags or ["Batch"])
    handler = BatchAPIHandler(
        storage=storage,
        batch_service=batch_service,
        webhook_secret=webhook_secret or os.getenv("OPENAI_WEBHOOK_SECRET"),
    )

    @router.post("/start", response_model=BatchStartResponse)
    async def start_batch(payload: BatchStartRequest) -> BatchStartResponse:
        """Start a new batch job."""
        try:
            return await handler.start_batch(payload)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to create batch: {exc}") from exc

    @router.post("/callback", response_model=BatchCallbackResponse)
    async def batch_callback(request: Request) -> BatchCallbackResponse:
        """Handle batch callback webhook."""
        body = await request.body()
        body_text = body.decode("utf-8") if body else ""
        headers = dict(request.headers)

        try:
            return await handler.handle_callback(body_text, headers)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Failed to process callback: {exc}"
            ) from exc

    @router.post("/webhook")
    async def batch_webhook(request: Request) -> Dict[str, str]:
        """Handle OpenAI webhook (Standard Webhooks format)."""
        body = await request.body()
        body_text = body.decode("utf-8") if body else ""
        headers = dict(request.headers)

        try:
            result = await handler.handle_callback(body_text, headers)
            return {"status": "ok", "batch_id": result.batch_id}
        except Exception:
            # Always return 200 to avoid webhook retries
            return {"status": "acknowledged"}

    @router.get("/status/{batch_id}", response_model=BatchStatusResponse)
    async def get_batch_status(batch_id: str) -> BatchStatusResponse:
        """Get batch status."""
        try:
            return await handler.get_status(batch_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to get status: {exc}") from exc

    return router


# Utility functions for custom integrations


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get attribute or key from object.

    Args:
        obj: Object to get from
        key: Key or attribute name
        default: Default value if not found

    Returns:
        Value or default
    """
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default


def object_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert object to dictionary.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation
    """
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
