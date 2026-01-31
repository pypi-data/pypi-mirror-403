"""OpenAI Batch API service for asynchronous batch processing.

This module provides a comprehensive wrapper around OpenAI's Batch API,
enabling batch processing with features like:
- Support for CSV, JSONL, and NDJSON data files
- Smart prompt handling (row-level or global)
- Downloading files from URLs
- Creating and managing batch jobs
- Checking batch status
- Retrieving and mapping batch results
- Tracking batch/input/output relationships

The Batch API offers 50% cost savings compared to synchronous APIs
and processes requests within 24 hours.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from openai import AsyncOpenAI, OpenAI

from .openai_compat import get_openai_client_kwargs


class BatchStatus(str, Enum):
    """Batch processing status."""

    VALIDATING = "validating"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


class BatchEndpoint(str, Enum):
    """Supported batch API endpoints."""

    CHAT_COMPLETIONS = "/v1/chat/completions"
    EMBEDDINGS = "/v1/embeddings"
    COMPLETIONS = "/v1/completions"


@dataclass
class BatchPayload:
    """Configuration for creating batch requests.

    This payload defines how to process data rows into OpenAI batch requests.
    If the data file contains a 'prompt' column, row-level prompts will be used.
    Otherwise, the global prompt will be applied to all rows.
    """

    prompt: Optional[str] = None
    """Global prompt to apply to all rows. Supports variable interpolation like {column_name}.
    If data has a 'prompt' column, that takes precedence."""

    model: Optional[str] = None
    """OpenAI model to use. Defaults to OPENAI_MODEL env var or gpt-4."""

    endpoint: BatchEndpoint = BatchEndpoint.CHAT_COMPLETIONS
    """API endpoint for batch processing."""

    custom_id_prefix: str = "req"
    """Prefix for auto-generated custom IDs."""

    system_message: Optional[str] = None
    """System message for chat completions."""

    temperature: float = 0.7
    """Sampling temperature."""

    max_tokens: Optional[int] = None
    """Maximum tokens to generate."""

    top_p: float = 1.0
    """Nucleus sampling parameter."""

    frequency_penalty: float = 0.0
    """Frequency penalty."""

    presence_penalty: float = 0.0
    """Presence penalty."""

    extra_body_params: Dict[str, Any] = field(default_factory=dict)
    """Additional parameters to include in the request body."""

    def get_model(self) -> str:
        """Get the model to use, with fallback to env var."""
        if self.model:
            return self.model
        return os.getenv("OPENAI_MODEL", "gpt-4")


@dataclass
class BatchRequest:
    """Represents a single batch request in JSONL format."""

    custom_id: str
    method: str
    url: str
    body: Dict[str, Any]

    def to_jsonl(self) -> str:
        """Convert to JSONL format."""
        return json.dumps(
            {
                "custom_id": self.custom_id,
                "method": self.method,
                "url": self.url,
                "body": self.body,
            }
        )

    @classmethod
    def from_jsonl(cls, line: str) -> BatchRequest:
        """Create from JSONL line."""
        data = json.loads(line)
        return cls(
            custom_id=data["custom_id"],
            method=data["method"],
            url=data["url"],
            body=data["body"],
        )


@dataclass
class BatchResponse:
    """Represents a single batch response."""

    id: str
    custom_id: str
    response: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_jsonl(cls, line: str) -> BatchResponse:
        """Create from JSONL line."""
        data = json.loads(line)
        return cls(
            id=data.get("id", ""),
            custom_id=data["custom_id"],
            response=data.get("response"),
            error=data.get("error"),
        )


@dataclass
class BatchInfo:
    """Information about a batch job."""

    id: str
    status: BatchStatus
    input_file_id: str
    output_file_id: Optional[str] = None
    error_file_id: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    request_counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    errors: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> BatchInfo:
        """Create from API response."""
        return cls(
            id=data["id"],
            status=BatchStatus(data["status"]),
            input_file_id=data["input_file_id"],
            output_file_id=data.get("output_file_id"),
            error_file_id=data.get("error_file_id"),
            created_at=datetime.fromtimestamp(data["created_at"])
            if data.get("created_at")
            else None,
            completed_at=datetime.fromtimestamp(data["completed_at"])
            if data.get("completed_at")
            else None,
            failed_at=datetime.fromtimestamp(data["failed_at"]) if data.get("failed_at") else None,
            expired_at=datetime.fromtimestamp(data["expired_at"])
            if data.get("expired_at")
            else None,
            cancelled_at=datetime.fromtimestamp(data["cancelled_at"])
            if data.get("cancelled_at")
            else None,
            request_counts=data.get("request_counts", {}),
            metadata=data.get("metadata", {}),
            errors=data.get("errors"),
        )


@dataclass
class BatchMapping:
    """Maps a batch to its input and output files."""

    batch_id: str
    input_file_id: str
    output_file_id: Optional[str]
    error_file_id: Optional[str]
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_path: Optional[str] = None
    status: BatchStatus = BatchStatus.VALIDATING
    created_at: Optional[datetime] = None


class OpenAIBatchService:
    """Service for managing OpenAI Batch API operations.

    This service provides a high-level interface for:
    - Creating batches from CSV, JSONL, or NDJSON files (local or URL)
    - Smart prompt handling (row-level or global with interpolation)
    - Monitoring batch status
    - Retrieving batch results
    - Managing batch/input/output mappings

    Uses OPENAI_API_KEY from environment by default.
    Uses OPENAI_MODEL from environment for model selection.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_dir: Optional[str] = None,
    ):
        """Initialize the batch service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            workspace_dir: Directory for storing batch files (defaults to ./batch_workspace)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY must be set")

        client_kwargs = get_openai_client_kwargs()
        self.client = OpenAI(api_key=self.api_key, **client_kwargs)
        self.async_client = AsyncOpenAI(api_key=self.api_key, **client_kwargs)

        self.workspace_dir = Path(workspace_dir or "./batch_workspace")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Track batch mappings
        self._mappings: Dict[str, BatchMapping] = {}

    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return "csv"
        elif suffix in [".jsonl", ".ndjson"]:
            return "jsonl"
        else:
            # Try to detect from content
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
                try:
                    json.loads(first_line)
                    return "jsonl"
                except json.JSONDecodeError:
                    return "csv"

    def _read_data_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read data from CSV, JSONL, or NDJSON file.

        Args:
            file_path: Path to data file

        Returns:
            List of data rows as dictionaries
        """
        file_format = self._detect_file_format(file_path)

        if file_format == "csv":
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        else:  # jsonl/ndjson
            rows = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
            return rows

    def _interpolate_prompt(self, prompt: str, data: Dict[str, Any]) -> str:
        """Interpolate variables in prompt template.

        Supports {variable_name} syntax for variable substitution.

        Args:
            prompt: Prompt template with {variables}
            data: Dictionary of data to interpolate

        Returns:
            Interpolated prompt string
        """
        result = prompt
        # Find all {variable} patterns
        for match in re.finditer(r"\{(\w+)\}", prompt):
            var_name = match.group(1)
            if var_name in data:
                value = str(data[var_name])
                result = result.replace(f"{{{var_name}}}", value)
        return result

    def _build_batch_requests(
        self, data_rows: List[Dict[str, Any]], payload: BatchPayload
    ) -> List[BatchRequest]:
        """Build batch requests from data rows and payload.

        Smart prompt handling:
        - If data row has 'prompt' column, use that (row-level wins)
        - Otherwise, use global prompt from payload with variable interpolation
        - If data row has 'custom_id', use that, otherwise generate one

        Args:
            data_rows: List of data dictionaries
            payload: Batch configuration payload

        Returns:
            List of BatchRequest objects
        """
        requests = []

        for idx, row in enumerate(data_rows):
            # Handle custom_id
            if "custom_id" in row:
                custom_id = str(row["custom_id"])
            else:
                custom_id = f"{payload.custom_id_prefix}-{idx + 1}"

            # Handle prompt - row-level wins
            if "prompt" in row:
                user_message = str(row["prompt"])
            elif payload.prompt:
                user_message = self._interpolate_prompt(payload.prompt, row)
            else:
                raise ValueError(
                    f"No prompt found for row {idx}. Provide either a 'prompt' column in data "
                    "or a global prompt in BatchPayload."
                )

            # Build request body based on endpoint
            body: Dict[str, Any] = {
                "model": payload.get_model(),
                "temperature": payload.temperature,
                "top_p": payload.top_p,
                "frequency_penalty": payload.frequency_penalty,
                "presence_penalty": payload.presence_penalty,
            }

            if payload.max_tokens:
                body["max_tokens"] = payload.max_tokens

            # Add endpoint-specific fields
            if payload.endpoint == BatchEndpoint.CHAT_COMPLETIONS:
                messages = []
                if payload.system_message:
                    messages.append({"role": "system", "content": payload.system_message})
                messages.append({"role": "user", "content": user_message})
                body["messages"] = messages
            elif payload.endpoint == BatchEndpoint.COMPLETIONS:
                body["prompt"] = user_message
            elif payload.endpoint == BatchEndpoint.EMBEDDINGS:
                body["input"] = user_message
                # Embeddings don't use temperature, etc.
                body = {"model": payload.get_model(), "input": user_message}

            # Add extra params
            body.update(payload.extra_body_params)

            # Create batch request
            request = BatchRequest(
                custom_id=custom_id, method="POST", url=payload.endpoint.value, body=body
            )
            requests.append(request)

        return requests

    async def download_file_from_url(self, url: str, output_path: Optional[str] = None) -> str:
        """Download data file from URL.

        Args:
            url: URL to download from
            output_path: Optional local path to save file (auto-generated if not provided)

        Returns:
            Path to downloaded file

        Raises:
            httpx.HTTPError: If download fails
            ValueError: If URL is invalid
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        if not output_path:
            filename = Path(parsed.path).name or "batch_data.csv"
            output_path = str(self.workspace_dir / filename)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

        return output_path

    async def create_batch_from_url(
        self,
        url: str,
        payload: BatchPayload,
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
    ) -> BatchMapping:
        """Create a batch job from a data file at a URL.

        Downloads the file first, then creates the batch.

        Args:
            url: URL of CSV/JSONL/NDJSON data file
            payload: Batch configuration (prompt, model, etc.)
            completion_window: Time window for completion (default: 24h)
            metadata: Optional metadata to attach to the batch

        Returns:
            BatchMapping with batch information
        """
        # Download file
        local_path = await self.download_file_from_url(url)

        # Create batch from local file
        return await self.create_batch_from_file(
            file_path=local_path,
            payload=payload,
            completion_window=completion_window,
            metadata=metadata,
        )

    async def create_batch_from_file(
        self,
        file_path: str,
        payload: BatchPayload,
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
    ) -> BatchMapping:
        """Create a batch job from a local data file.

        Supports CSV, JSONL, and NDJSON formats.

        Args:
            file_path: Path to local CSV/JSONL/NDJSON data file
            payload: Batch configuration (prompt, model, etc.)
            completion_window: Time window for completion (default: 24h)
            metadata: Optional metadata to attach to the batch

        Returns:
            BatchMapping with batch information
        """
        # Read data file
        data_rows = self._read_data_file(file_path)

        # Build batch requests
        requests = self._build_batch_requests(data_rows, payload)

        # Create batch from requests
        return await self._create_batch_from_requests_internal(
            requests=requests,
            endpoint=payload.endpoint,
            completion_window=completion_window,
            metadata=metadata,
            original_file_path=file_path,
        )

    async def create_batch_from_data(
        self,
        data: List[Dict[str, Any]],
        payload: BatchPayload,
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
    ) -> BatchMapping:
        """Create a batch job from in-memory data.

        Args:
            data: List of data dictionaries
            payload: Batch configuration (prompt, model, etc.)
            completion_window: Time window for completion (default: 24h)
            metadata: Optional metadata to attach to the batch

        Returns:
            BatchMapping with batch information
        """
        # Build batch requests
        requests = self._build_batch_requests(data, payload)

        # Create batch from requests
        return await self._create_batch_from_requests_internal(
            requests=requests,
            endpoint=payload.endpoint,
            completion_window=completion_window,
            metadata=metadata,
        )

    async def _create_batch_from_requests_internal(
        self,
        requests: List[BatchRequest],
        endpoint: BatchEndpoint,
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
        original_file_path: Optional[str] = None,
    ) -> BatchMapping:
        """Internal method to create batch from BatchRequest objects.

        Args:
            requests: List of BatchRequest objects
            endpoint: API endpoint for batch processing
            completion_window: Time window for completion (default: 24h)
            metadata: Optional metadata to attach to the batch
            original_file_path: Optional path to original data file

        Returns:
            BatchMapping with batch information
        """
        # Create JSONL file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.workspace_dir / f"batch_input_{timestamp}.jsonl"

        with open(file_path, "w") as f:
            for req in requests:
                f.write(req.to_jsonl() + "\n")

        # Determine filename to use for OpenAI upload
        # Preserve original filename if provided, otherwise use local filename
        if original_file_path:
            upload_filename = Path(original_file_path).name
        else:
            upload_filename = file_path.name

        # Upload file to OpenAI with custom filename
        with open(file_path, "rb") as f:
            file_obj = await self.async_client.files.create(
                file=(upload_filename, f), purpose="batch"
            )

        # Create batch
        batch = await self.async_client.batches.create(
            input_file_id=file_obj.id,
            endpoint=endpoint.value,
            completion_window=completion_window,
            metadata=metadata or {},
        )

        # Create mapping
        mapping = BatchMapping(
            batch_id=batch.id,
            input_file_id=file_obj.id,
            output_file_id=None,
            error_file_id=None,
            input_path=str(file_path),
            status=BatchStatus(batch.status),
            created_at=datetime.fromtimestamp(batch.created_at),
        )

        self._mappings[batch.id] = mapping
        return mapping

    async def get_batch_status(self, batch_id: str) -> BatchInfo:
        """Get the current status of a batch.

        Args:
            batch_id: ID of the batch

        Returns:
            BatchInfo with current batch information
        """
        batch = await self.async_client.batches.retrieve(batch_id)
        info = BatchInfo.from_api_response(batch.model_dump())

        # Update mapping if exists
        if batch_id in self._mappings:
            mapping = self._mappings[batch_id]
            mapping.status = info.status
            mapping.output_file_id = info.output_file_id
            mapping.error_file_id = info.error_file_id

        return info

    async def wait_for_completion(
        self,
        batch_id: str,
        poll_interval: int = 60,
        max_wait_time: Optional[int] = None,
    ) -> BatchInfo:
        """Wait for a batch to complete.

        Args:
            batch_id: ID of the batch
            poll_interval: Seconds between status checks (default: 60)
            max_wait_time: Maximum seconds to wait (None = wait indefinitely)

        Returns:
            BatchInfo when batch completes

        Raises:
            TimeoutError: If max_wait_time is exceeded
            RuntimeError: If batch fails
        """
        import asyncio

        elapsed = 0
        while True:
            info = await self.get_batch_status(batch_id)

            if info.status in [
                BatchStatus.COMPLETED,
                BatchStatus.FAILED,
                BatchStatus.EXPIRED,
                BatchStatus.CANCELLED,
            ]:
                if info.status == BatchStatus.FAILED:
                    raise RuntimeError(f"Batch {batch_id} failed: {info.errors}")
                elif info.status == BatchStatus.EXPIRED:
                    raise RuntimeError(f"Batch {batch_id} expired")
                elif info.status == BatchStatus.CANCELLED:
                    raise RuntimeError(f"Batch {batch_id} was cancelled")
                return info

            if max_wait_time and elapsed >= max_wait_time:
                raise TimeoutError(
                    f"Batch {batch_id} did not complete within {max_wait_time} seconds"
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

    async def get_batch_results(
        self, batch_id: str, output_path: Optional[str] = None
    ) -> List[BatchResponse]:
        """Get results from a completed batch.

        Args:
            batch_id: ID of the batch
            output_path: Optional path to save results (auto-generated if not provided)

        Returns:
            List of BatchResponse objects

        Raises:
            RuntimeError: If batch is not completed or has no output file
        """
        info = await self.get_batch_status(batch_id)

        if info.status != BatchStatus.COMPLETED:
            raise RuntimeError(f"Batch {batch_id} is not completed (status: {info.status})")

        if not info.output_file_id:
            raise RuntimeError(f"Batch {batch_id} has no output file")

        # Download output file (use sync client for reliable bytes in OpenAI 2.x)
        content = self.client.files.content(info.output_file_id)
        output_data = content.content

        # Save to file
        if not output_path:
            output_path = str(self.workspace_dir / f"batch_output_{batch_id}.jsonl")

        with open(output_path, "wb") as f:
            f.write(output_data)

        # Update mapping
        if batch_id in self._mappings:
            self._mappings[batch_id].output_path = output_path

        # Parse responses
        results = []
        for line in output_data.decode("utf-8").strip().split("\n"):
            if line:
                results.append(BatchResponse.from_jsonl(line))

        return results

    async def get_batch_errors(
        self, batch_id: str, output_path: Optional[str] = None
    ) -> List[BatchResponse]:
        """Get error details from a batch (if any).

        Args:
            batch_id: ID of the batch
            output_path: Optional path to save errors (auto-generated if not provided)

        Returns:
            List of BatchResponse objects with errors
        """
        info = await self.get_batch_status(batch_id)

        if not info.error_file_id:
            return []

        # Download error file (use sync client for reliable bytes in OpenAI 2.x)
        content = self.client.files.content(info.error_file_id)
        error_data = content.content

        # Save to file
        if not output_path:
            output_path = str(self.workspace_dir / f"batch_errors_{batch_id}.jsonl")

        with open(output_path, "wb") as f:
            f.write(error_data)

        # Update mapping
        if batch_id in self._mappings:
            self._mappings[batch_id].error_path = output_path

        # Parse errors
        errors = []
        for line in error_data.decode("utf-8").strip().split("\n"):
            if line:
                errors.append(BatchResponse.from_jsonl(line))

        return errors

    async def cancel_batch(self, batch_id: str) -> BatchInfo:
        """Cancel a running batch.

        Args:
            batch_id: ID of the batch

        Returns:
            BatchInfo with updated status
        """
        batch = await self.async_client.batches.cancel(batch_id)
        info = BatchInfo.from_api_response(batch.model_dump())

        # Update mapping
        if batch_id in self._mappings:
            self._mappings[batch_id].status = info.status

        return info

    async def list_batches(self, limit: int = 20) -> List[BatchInfo]:
        """List recent batches.

        Args:
            limit: Maximum number of batches to return

        Returns:
            List of BatchInfo objects
        """
        batches = await self.async_client.batches.list(limit=limit)
        return [BatchInfo.from_api_response(batch.model_dump()) for batch in batches.data]

    def get_mapping(self, batch_id: str) -> Optional[BatchMapping]:
        """Get the mapping for a batch.

        Args:
            batch_id: ID of the batch

        Returns:
            BatchMapping if exists, None otherwise
        """
        return self._mappings.get(batch_id)

    def get_all_mappings(self) -> Dict[str, BatchMapping]:
        """Get all batch mappings.

        Returns:
            Dictionary of batch_id -> BatchMapping
        """
        return self._mappings.copy()


# Convenience functions for quick usage


async def create_batch_from_url(
    url: str,
    payload: BatchPayload,
    api_key: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> BatchMapping:
    """Convenience function to create a batch from a URL.

    Args:
        url: URL of CSV/JSONL/NDJSON data file
        payload: Batch configuration (prompt, model, etc.)
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        metadata: Optional metadata to attach to the batch

    Returns:
        BatchMapping with batch information
    """
    service = OpenAIBatchService(api_key=api_key)
    return await service.create_batch_from_url(url, payload, metadata=metadata)


async def create_batch_from_file(
    file_path: str,
    payload: BatchPayload,
    api_key: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> BatchMapping:
    """Convenience function to create a batch from a local file.

    Args:
        file_path: Path to local CSV/JSONL/NDJSON data file
        payload: Batch configuration (prompt, model, etc.)
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        metadata: Optional metadata to attach to the batch

    Returns:
        BatchMapping with batch information
    """
    service = OpenAIBatchService(api_key=api_key)
    return await service.create_batch_from_file(file_path, payload, metadata=metadata)


async def check_batch_status(batch_id: str, api_key: Optional[str] = None) -> BatchInfo:
    """Convenience function to check batch status.

    Args:
        batch_id: ID of the batch
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)

    Returns:
        BatchInfo with current batch information
    """
    service = OpenAIBatchService(api_key=api_key)
    return await service.get_batch_status(batch_id)
