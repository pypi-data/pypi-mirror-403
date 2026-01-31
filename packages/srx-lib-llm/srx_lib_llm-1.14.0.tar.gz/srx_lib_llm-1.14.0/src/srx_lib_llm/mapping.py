"""Batch mapping persistence for tracking batch metadata.

This module provides utilities for storing and retrieving batch mapping documents
that track the relationship between batches and their storage paths.
"""

from __future__ import annotations

import io
import json
from datetime import date, datetime
from typing import Any, Dict, Optional

from srx_lib_llm.batch import BatchMapping, BatchStatus
from srx_lib_llm.storage import StorageProvider


class BatchMappingStore:
    """Store for persisting batch mapping documents."""

    def __init__(self, storage: StorageProvider, prefix: str = "mappings/batches"):
        """Initialize mapping store.

        Args:
            storage: Storage provider for persistence
            prefix: Prefix for mapping document paths
        """
        self.storage = storage
        self.prefix = prefix

    def _get_mapping_path(self, batch_id: str) -> str:
        """Get storage path for batch mapping.

        Args:
            batch_id: Batch ID

        Returns:
            Storage path for mapping document
        """
        return f"{self.prefix}/{batch_id}.json"

    def _build_output_path(
        self,
        business_date: date,
        pipeline_prefix: str = "attachments",
        output_filename: str = "batch_output.jsonl",
        use_nodash_date: bool = True,
    ) -> str:
        """Build output path from configuration.

        Args:
            business_date: Business date for directory placement
            pipeline_prefix: Pipeline folder prefix
            output_filename: Output filename
            use_nodash_date: Use YYYYMMDD format vs YYYY-MM-DD

        Returns:
            Output blob path
        """
        date_str = (
            business_date.strftime("%Y%m%d") if use_nodash_date else business_date.isoformat()
        )
        return f"{pipeline_prefix}/{date_str}/{output_filename}"

    async def save_mapping(
        self,
        batch_id: str,
        input_url: str,
        business_date: date,
        status: Optional[str] = None,
        lib_mapping: Optional[BatchMapping] = None,
        pipeline_prefix: str = "attachments",
        output_filename: str = "batch_output.jsonl",
        use_nodash_date: bool = True,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save batch mapping document.

        Args:
            batch_id: Batch ID
            input_url: Input file URL
            business_date: Business date
            status: Batch status
            lib_mapping: Optional BatchMapping from srx-lib-llm
            pipeline_prefix: Pipeline folder prefix
            output_filename: Output filename
            use_nodash_date: Use YYYYMMDD format
            extra_metadata: Additional metadata to store

        Returns:
            Path where mapping was saved
        """
        mapping_path = self._get_mapping_path(batch_id)

        # Build output path
        output_path = self._build_output_path(
            business_date, pipeline_prefix, output_filename, use_nodash_date
        )

        # Build mapping document
        mapping_doc = {
            "batch_id": batch_id,
            "status": status,
            "input_url": input_url,
            "date": business_date.isoformat(),
            "output_blob_path": output_path,
            "mapping_blob_path": mapping_path,
            "pipeline_config": {
                "pipeline_prefix": pipeline_prefix,
                "output_filename": output_filename,
                "date_format": business_date.strftime("%Y%m%d")
                if use_nodash_date
                else business_date.isoformat(),
                "use_nodash_date": use_nodash_date,
            },
            "created_at": datetime.now().isoformat(),
        }

        # Add lib mapping if available
        if lib_mapping:
            lib_map_dict = {
                "batch_id": lib_mapping.batch_id,
                "input_file_id": lib_mapping.input_file_id,
                "output_file_id": lib_mapping.output_file_id,
                "error_file_id": lib_mapping.error_file_id,
                "input_path": lib_mapping.input_path,
                "output_path": lib_mapping.output_path,
                "error_path": lib_mapping.error_path,
                "status": lib_mapping.status.value
                if isinstance(lib_mapping.status, BatchStatus)
                else lib_mapping.status,
                "created_at": lib_mapping.created_at.isoformat()
                if lib_mapping.created_at
                else None,
            }
            mapping_doc["lib_mapping"] = lib_map_dict

        # Add extra metadata
        if extra_metadata:
            mapping_doc["metadata"] = extra_metadata

        # Save to storage
        data = json.dumps(mapping_doc, indent=2).encode("utf-8")
        stream = io.BytesIO(data)
        await self.storage.upload_stream(stream, mapping_path, content_type="application/json")

        return mapping_path

    async def get_mapping(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch mapping document.

        Args:
            batch_id: Batch ID

        Returns:
            Mapping document as dict, or None if not found
        """
        mapping_path = self._get_mapping_path(batch_id)
        data = await self.storage.download_file(mapping_path)

        if not data:
            return None

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    async def get_output_path(self, batch_id: str) -> Optional[str]:
        """Get output path for a batch.

        Args:
            batch_id: Batch ID

        Returns:
            Output path, or None if not found
        """
        mapping = await self.get_mapping(batch_id)
        if not mapping:
            return None

        return mapping.get("output_blob_path")

    async def update_status(self, batch_id: str, status: str) -> bool:
        """Update batch status in mapping.

        Args:
            batch_id: Batch ID
            status: New status

        Returns:
            True if updated, False if mapping not found
        """
        mapping = await self.get_mapping(batch_id)
        if not mapping:
            return False

        mapping["status"] = status
        mapping["updated_at"] = datetime.now().isoformat()

        mapping_path = self._get_mapping_path(batch_id)
        data = json.dumps(mapping, indent=2).encode("utf-8")
        stream = io.BytesIO(data)
        await self.storage.upload_stream(stream, mapping_path, content_type="application/json")

        return True

    async def delete_mapping(self, batch_id: str) -> bool:
        """Delete batch mapping.

        Args:
            batch_id: Batch ID

        Returns:
            True if deleted, False otherwise
        """
        mapping_path = self._get_mapping_path(batch_id)
        return await self.storage.delete_file(mapping_path)


async def resolve_output_path(
    batch_id: str,
    storage: StorageProvider,
    lib_mapping: Optional[BatchMapping] = None,
    mapping_store: Optional[BatchMappingStore] = None,
) -> Optional[str]:
    """Resolve output path for a batch from various sources.

    Tries in order:
    1. lib_mapping if provided
    2. mapping_store if provided
    3. storage lookup

    Args:
        batch_id: Batch ID
        storage: Storage provider
        lib_mapping: Optional BatchMapping from srx-lib-llm
        mapping_store: Optional BatchMappingStore instance

    Returns:
        Output path, or None if not found
    """
    # Try lib mapping first
    if lib_mapping and lib_mapping.output_path:
        return lib_mapping.output_path

    # Try mapping store
    if mapping_store:
        output_path = await mapping_store.get_output_path(batch_id)
        if output_path:
            return output_path

    # Try direct storage lookup
    store = mapping_store or BatchMappingStore(storage)
    mapping = await store.get_mapping(batch_id)
    if mapping:
        return mapping.get("output_blob_path")

    return None
