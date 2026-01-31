"""Pydantic schemas for OpenAI Batch API integration.

This module provides schemas for:
- Batch request/response models
- Status and mapping models
- FastAPI integration models
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from pydantic import AnyUrl, BaseModel, Field

from srx_lib_llm.batch import BatchStatus


class BatchStartRequest(BaseModel):
    """Request model for starting a batch job."""

    jsonl_url: AnyUrl = Field(..., description="URL to the input JSONL file")
    date: datetime.date = Field(
        ..., description="Business date (YYYY-MM-DD) for directory placement"
    )
    batch_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional BatchPayload configuration as dict",
    )
    pipeline_prefix: Optional[str] = Field(
        default="attachments",
        description="Pipeline folder prefix (e.g., 'attachments', 'news', 'reports')",
    )
    output_filename: Optional[str] = Field(
        default="batch_output.jsonl",
        description="Output filename",
    )
    use_nodash_date: Optional[bool] = Field(
        default=True,
        description="Use YYYYMMDD format (True) vs YYYY-MM-DD format (False)",
    )
    preformatted_batch: Optional[bool] = Field(
        default=False,
        description="If True, JSONL is already in OpenAI Batch format (skip conversion)",
    )


class BatchStartResponse(BaseModel):
    """Response model for batch creation."""

    batch_id: str
    status: Optional[str] = None
    mapping_path: Optional[str] = Field(
        default=None, description="Storage path where the batch mapping is stored"
    )


class BatchCallbackResponse(BaseModel):
    """Response model for batch callback/webhook."""

    batch_id: str
    output_path: str
    uploaded: bool


class RequestCounts(BaseModel):
    """Batch request statistics."""

    total: Optional[int] = None
    completed: Optional[int] = None
    failed: Optional[int] = None


class BatchInfoResponse(BaseModel):
    """Detailed batch information response."""

    id: str
    status: BatchStatus
    input_file_id: Optional[str] = None
    output_file_id: Optional[str] = None
    error_file_id: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime.datetime] = None
    in_progress_at: Optional[datetime.datetime] = None
    finalizing_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    failed_at: Optional[datetime.datetime] = None
    expired_at: Optional[datetime.datetime] = None
    cancelled_at: Optional[datetime.datetime] = None

    request_counts: Optional[RequestCounts] = None
    metadata: Optional[Dict[str, str]] = None
    errors: Optional[list[Dict[str, Any]]] = None


class BatchMappingResponse(BaseModel):
    """Batch file mapping response."""

    batch_id: str
    input_file_id: Optional[str] = None
    output_file_id: Optional[str] = None
    error_file_id: Optional[str] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_path: Optional[str] = None
    status: Optional[BatchStatus] = None
    created_at: Optional[datetime.datetime] = None


class BatchStatusResponse(BatchInfoResponse):
    """Extended batch status with mapping information."""

    mapping: Optional[BatchMappingResponse] = None
    sidecar_mapping: Optional[Dict[str, Any]] = None
