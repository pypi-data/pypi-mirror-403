"""Infrastructure-agnostic batch state management.

This module provides state tracking for batch operations across ETL and service layers:
- Abstract interface (BatchStateStore) for different storage backends
- Concrete implementations for Azure Table, In-Memory, Redis (future)
- High-level facade (BatchStateManager) with business logic
- Support for granular step-level state tracking
- Retry eligibility checking
- Failed batch querying

Design follows the same pattern as storage.py (StorageProvider abstraction).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Protocol
from enum import Enum


class StepStatus(str, Enum):
    """Status values for individual steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchOverallStatus(str, Enum):
    """Overall batch processing status."""

    ETL_PREP = "etl_prep"
    ETL_SUBMIT = "etl_submit"
    MONITORING_VALIDATING = "monitoring_validating"
    MONITORING_IN_PROGRESS = "monitoring_in_progress"
    MONITORING_FINALIZING = "monitoring_finalizing"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchState(Protocol):
    """Protocol defining the shape of batch state dictionary."""

    batch_id: str
    pipeline_id: str | None
    status: str
    created_at: str
    updated_at: str


class BatchStateStore(ABC):
    """Abstract base class for batch state storage backends.

    Implementations must handle persistence of batch state dictionaries.
    All datetime values should be ISO 8601 strings in UTC.
    """

    @abstractmethod
    async def get(self, batch_id: str) -> dict[str, Any] | None:
        """Get batch state by ID.

        Args:
            batch_id: Batch identifier

        Returns:
            State dictionary or None if not found
        """
        pass

    @abstractmethod
    async def upsert(self, batch_id: str, updates: dict[str, Any]) -> None:
        """Insert or update batch state.

        Args:
            batch_id: Batch identifier
            updates: Dictionary of fields to update
        """
        pass

    @abstractmethod
    async def query(self, filter_dict: dict[str, Any], max_results: int = 100) -> list[dict[str, Any]]:
        """Query batch states by filter criteria.

        Args:
            filter_dict: Dictionary of field:value pairs to filter by
            max_results: Maximum number of results

        Returns:
            List of matching state dictionaries
        """
        pass

    @abstractmethod
    async def delete(self, batch_id: str) -> bool:
        """Delete batch state.

        Args:
            batch_id: Batch identifier

        Returns:
            True if deleted, False if not found
        """
        pass


class InMemoryBatchStateStore(BatchStateStore):
    """In-memory implementation for testing and local development."""

    def __init__(self):
        """Initialize in-memory store."""
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, batch_id: str) -> dict[str, Any] | None:
        """Get batch state from memory."""
        return self._store.get(batch_id)

    async def upsert(self, batch_id: str, updates: dict[str, Any]) -> None:
        """Update batch state in memory."""
        if batch_id in self._store:
            self._store[batch_id].update(updates)
        else:
            self._store[batch_id] = {"batch_id": batch_id, **updates}

        self._store[batch_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    async def query(self, filter_dict: dict[str, Any], max_results: int = 100) -> list[dict[str, Any]]:
        """Query states in memory."""
        results = []
        for state in self._store.values():
            # Simple equality matching
            if all(state.get(k) == v for k, v in filter_dict.items()):
                results.append(state)
                if len(results) >= max_results:
                    break
        return results

    async def delete(self, batch_id: str) -> bool:
        """Delete from memory."""
        if batch_id in self._store:
            del self._store[batch_id]
            return True
        return False


class AzureTableBatchStateStore(BatchStateStore):
    """Azure Table Storage implementation.

    Uses monthly partitioning (PartitionKey = YYYY-MM) for efficient querying.
    RowKey = batch_id for direct access.
    """

    def __init__(self, connection_string: str | None = None, table_name: str = "BatchOperationState"):
        """Initialize Azure Table storage.

        Args:
            connection_string: Azure Storage connection string (or from env)
            table_name: Name of the Azure Table
        """
        try:
            from srx_lib_azure import AzureTableService
        except ImportError as exc:
            raise ImportError(
                "srx-lib-azure is required for AzureTableBatchStateStore. "
                "Install with: pip install srx-lib-azure"
            ) from exc

        self.table_service = AzureTableService(connection_string=connection_string)
        self.table_name = table_name

    def _get_partition_key(self) -> str:
        """Get current partition key (YYYY-MM format)."""
        return datetime.now(timezone.utc).strftime("%Y-%m")

    async def get(self, batch_id: str) -> dict[str, Any] | None:
        """Get from Azure Table."""
        partition_key = self._get_partition_key()
        try:
            entity = self.table_service.get_entity(
                table_name=self.table_name,
                partition_key=partition_key,
                row_key=batch_id,
            )
            return entity
        except Exception:
            return None

    async def upsert(self, batch_id: str, updates: dict[str, Any]) -> None:
        """Upsert to Azure Table."""
        partition_key = self._get_partition_key()

        # Get existing or create new
        existing = await self.get(batch_id)
        if existing:
            entity = {**existing, **updates}
        else:
            entity = {
                "PartitionKey": partition_key,
                "RowKey": batch_id,
                "batch_id": batch_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **updates,
            }

        entity["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.table_service.upsert_entity(table_name=self.table_name, entity=entity)

    async def query(self, filter_dict: dict[str, Any], max_results: int = 100) -> list[dict[str, Any]]:
        """Query Azure Table with filters."""
        partition_key = self._get_partition_key()

        # Build OData filter string
        filter_parts = [f"PartitionKey eq '{partition_key}'"]
        for key, value in filter_dict.items():
            if isinstance(value, str):
                filter_parts.append(f"{key} eq '{value}'")
            else:
                filter_parts.append(f"{key} eq {value}")

        filter_string = " and ".join(filter_parts)

        try:
            entities = self.table_service.query_entities(
                table_name=self.table_name,
                filter=filter_string,
            )
            return list(entities)[:max_results]
        except Exception:
            return []

    async def delete(self, batch_id: str) -> bool:
        """Delete from Azure Table."""
        partition_key = self._get_partition_key()
        try:
            self.table_service.delete_entity(
                table_name=self.table_name,
                partition_key=partition_key,
                row_key=batch_id,
            )
            return True
        except Exception:
            return False


class BatchStateManager:
    """High-level facade for batch state management with business logic.

    This class provides a clean API for tracking batch operations across
    ETL and service layers, hiding the underlying storage implementation.
    """

    def __init__(self, store: BatchStateStore):
        """Initialize manager with a storage backend.

        Args:
            store: BatchStateStore implementation (Azure Table, In-Memory, etc.)
        """
        self.store = store

    # === ETL-side methods ===

    async def init_etl_batch(
        self,
        batch_id: str,
        pipeline_id: str,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
    ) -> None:
        """Initialize batch state from ETL side."""
        await self.store.upsert(
            batch_id,
            {
                "pipeline_id": pipeline_id,
                "status": BatchOverallStatus.ETL_PREP.value,
                "etl_dag_id": dag_id,
                "etl_dag_run_id": dag_run_id,
                "etl_task_id": task_id,
                "etl_prep_status": StepStatus.PENDING.value,
                "etl_submit_status": StepStatus.PENDING.value,
                "etl_monitor_status": StepStatus.PENDING.value,
                "etl_output_status": StepStatus.PENDING.value,
            },
        )

    async def mark_etl_prep_started(self, batch_id: str) -> None:
        """Mark ETL JSONL preparation as started."""
        await self.store.upsert(
            batch_id,
            {
                "etl_prep_status": StepStatus.IN_PROGRESS.value,
                "etl_prep_started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def mark_etl_prep_completed(self, batch_id: str, file_count: int, jsonl_path: str) -> None:
        """Mark ETL JSONL preparation as completed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_prep_status": StepStatus.SUCCESS.value,
                "etl_prep_completed_at": datetime.now(timezone.utc).isoformat(),
                "etl_prep_file_count": file_count,
                "etl_prep_jsonl_path": jsonl_path,
                "status": BatchOverallStatus.ETL_SUBMIT.value,
            },
        )

    async def mark_etl_prep_failed(self, batch_id: str, error: str) -> None:
        """Mark ETL JSONL preparation as failed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_prep_status": StepStatus.FAILED.value,
                "error_step": "etl_prep",
                "error_message": error[:1000],
                "status": BatchOverallStatus.FAILED.value,
            },
        )

    async def mark_etl_submit_started(self, batch_id: str) -> None:
        """Mark batch submission to svc-trading as started."""
        await self.store.upsert(
            batch_id,
            {
                "etl_submit_status": StepStatus.IN_PROGRESS.value,
                "etl_submit_started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def mark_etl_submit_completed(self, batch_id: str) -> None:
        """Mark batch submission to svc-trading as completed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_submit_status": StepStatus.SUCCESS.value,
                "etl_submit_completed_at": datetime.now(timezone.utc).isoformat(),
                "etl_monitor_status": StepStatus.IN_PROGRESS.value,
                "status": BatchOverallStatus.MONITORING_VALIDATING.value,
            },
        )

    async def mark_etl_submit_failed(self, batch_id: str, error: str) -> None:
        """Mark batch submission to svc-trading as failed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_submit_status": StepStatus.FAILED.value,
                "error_step": "etl_submit",
                "error_message": error[:1000],
                "status": BatchOverallStatus.FAILED.value,
            },
        )

    async def mark_etl_monitor_check(self, batch_id: str, openai_status: str) -> None:
        """Record a status check during monitoring."""
        await self.store.upsert(
            batch_id,
            {
                "etl_monitor_last_check_at": datetime.now(timezone.utc).isoformat(),
                "status": f"monitoring_{openai_status}",
            },
        )

    async def mark_etl_monitor_completed(self, batch_id: str) -> None:
        """Mark monitoring as completed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_monitor_status": StepStatus.SUCCESS.value,
            },
        )

    async def mark_etl_output_retrieved(self, batch_id: str, output_path: str) -> None:
        """Mark output JSONL as retrieved from blob."""
        await self.store.upsert(
            batch_id,
            {
                "etl_output_status": StepStatus.SUCCESS.value,
                "etl_output_retrieved_at": datetime.now(timezone.utc).isoformat(),
                "blob_path": output_path,
            },
        )

    async def mark_etl_output_failed(self, batch_id: str, error: str) -> None:
        """Mark output retrieval as failed."""
        await self.store.upsert(
            batch_id,
            {
                "etl_output_status": StepStatus.FAILED.value,
                "error_step": "etl_output",
                "error_message": error[:1000],
                "status": BatchOverallStatus.PARTIAL.value,
            },
        )

    # === SVC-side methods ===

    async def init_svc_batch(
        self, batch_id: str, pipeline_id: str, output_file_id: str | None = None
    ) -> None:
        """Initialize batch state from svc-trading side."""
        await self.store.upsert(
            batch_id,
            {
                "pipeline_id": pipeline_id,
                "status": BatchOverallStatus.IN_PROGRESS.value,
                "output_file_id": output_file_id,
                "callback_received_at": datetime.now(timezone.utc).isoformat(),
                "callback_status": StepStatus.SUCCESS.value,
                "download_status": StepStatus.PENDING.value,
                "blob_upload_status": StepStatus.PENDING.value,
                "ingestion_status": StepStatus.PENDING.value,
                "retry_count": 0,
            },
        )

    async def mark_blob_upload_started(self, batch_id: str) -> None:
        """Mark blob upload as started."""
        await self.store.upsert(batch_id, {"blob_upload_status": StepStatus.IN_PROGRESS.value})

    async def mark_blob_upload_completed(self, batch_id: str, blob_path: str) -> None:
        """Mark blob upload as completed."""
        await self.store.upsert(
            batch_id,
            {
                "blob_upload_status": StepStatus.SUCCESS.value,
                "blob_upload_completed_at": datetime.now(timezone.utc).isoformat(),
                "blob_path": blob_path,
            },
        )

    async def mark_blob_upload_failed(self, batch_id: str, error: str) -> None:
        """Mark blob upload as failed."""
        await self.store.upsert(
            batch_id,
            {
                "blob_upload_status": StepStatus.FAILED.value,
                "error_step": "blob_upload",
                "error_message": error[:1000],
                "status": BatchOverallStatus.PARTIAL.value,
            },
        )

    async def mark_ingestion_started(self, batch_id: str) -> None:
        """Mark ingestion as started."""
        await self.store.upsert(
            batch_id,
            {
                "ingestion_status": StepStatus.IN_PROGRESS.value,
                "ingestion_started_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def mark_ingestion_completed(
        self, batch_id: str, records_total: int, records_success: int, records_failed: int
    ) -> None:
        """Mark ingestion as completed."""
        final_status = BatchOverallStatus.COMPLETED if records_failed == 0 else BatchOverallStatus.PARTIAL

        await self.store.upsert(
            batch_id,
            {
                "ingestion_status": StepStatus.SUCCESS.value,
                "ingestion_completed_at": datetime.now(timezone.utc).isoformat(),
                "ingestion_records_total": records_total,
                "ingestion_records_success": records_success,
                "ingestion_records_failed": records_failed,
                "status": final_status.value,
            },
        )

    async def mark_ingestion_failed(self, batch_id: str, error: str) -> None:
        """Mark ingestion as failed."""
        await self.store.upsert(
            batch_id,
            {
                "ingestion_status": StepStatus.FAILED.value,
                "error_step": "ingestion",
                "error_message": error[:1000],
                "status": BatchOverallStatus.PARTIAL.value,
            },
        )

    async def mark_ingestion_skipped(self, batch_id: str, reason: str = "ingestion_disabled") -> None:
        """Mark ingestion as skipped."""
        await self.store.upsert(
            batch_id,
            {
                "ingestion_status": StepStatus.SKIPPED.value,
                "status": BatchOverallStatus.COMPLETED.value,
            },
        )

    # === Query methods ===

    async def get_state(self, batch_id: str) -> dict[str, Any] | None:
        """Get current state for a batch."""
        return await self.store.get(batch_id)

    async def can_retry_ingestion(self, batch_id: str) -> tuple[bool, str]:
        """Check if ingestion can be retried."""
        state = await self.get_state(batch_id)
        if not state:
            return False, "Batch state not found"

        blob_status = state.get("blob_upload_status")
        ingestion_status = state.get("ingestion_status")
        blob_path = state.get("blob_path")

        if blob_status != StepStatus.SUCCESS.value:
            return False, "Blob upload not completed"

        if not blob_path:
            return False, "Blob path not recorded"

        if ingestion_status == StepStatus.SUCCESS.value:
            return False, "Ingestion already completed"

        if ingestion_status in (StepStatus.FAILED.value, StepStatus.IN_PROGRESS.value):
            return True, "Ingestion can be retried"

        return False, f"Ingestion status '{ingestion_status}' does not allow retry"

    async def get_failed_ingestions(self, max_results: int = 100) -> list[dict[str, Any]]:
        """Get all batches with failed ingestion that can be retried."""
        failed_batches = await self.store.query(
            {"ingestion_status": StepStatus.FAILED.value}, max_results=max_results
        )

        # Filter to only those that can be retried
        retryable = []
        for state in failed_batches:
            batch_id = state.get("batch_id") or state.get("RowKey")
            can_retry, _ = await self.can_retry_ingestion(batch_id)
            if can_retry:
                retryable.append(state)

        return retryable

    async def increment_retry_count(self, batch_id: str) -> int:
        """Increment retry count and return new value."""
        state = await self.get_state(batch_id)
        if not state:
            return 0

        retry_count = state.get("retry_count", 0) + 1
        await self.store.upsert(
            batch_id,
            {
                "retry_count": retry_count,
                "last_retry_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return retry_count
