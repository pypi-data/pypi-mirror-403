"""Tests for batch mapping persistence."""

import pytest
import tempfile
from datetime import date

from srx_lib_llm.mapping import BatchMappingStore, resolve_output_path
from srx_lib_llm.storage import LocalStorageProvider


@pytest.mark.asyncio
async def test_mapping_store_save_and_get():
    """Test saving and retrieving batch mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)
        store = BatchMappingStore(storage)

        # Save mapping
        batch_id = "batch_test_123"
        mapping_path = await store.save_mapping(
            batch_id=batch_id,
            input_url="https://example.com/input.jsonl",
            business_date=date(2025, 1, 15),
            status="validating",
            pipeline_prefix="test",
            output_filename="output.jsonl",
            use_nodash_date=True,
        )

        assert mapping_path == f"mappings/batches/{batch_id}.json"

        # Get mapping
        mapping = await store.get_mapping(batch_id)
        assert mapping is not None
        assert mapping["batch_id"] == batch_id
        assert mapping["status"] == "validating"
        assert mapping["input_url"] == "https://example.com/input.jsonl"


@pytest.mark.asyncio
async def test_mapping_store_get_output_path():
    """Test getting output path from mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)
        store = BatchMappingStore(storage)

        # Save mapping
        batch_id = "batch_test_456"
        await store.save_mapping(
            batch_id=batch_id,
            input_url="https://example.com/input.jsonl",
            business_date=date(2025, 1, 15),
            pipeline_prefix="reports",
            output_filename="results.jsonl",
            use_nodash_date=False,
        )

        # Get output path
        output_path = await store.get_output_path(batch_id)
        assert output_path == "reports/2025-01-15/results.jsonl"


@pytest.mark.asyncio
async def test_mapping_store_update_status():
    """Test updating batch status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)
        store = BatchMappingStore(storage)

        # Save mapping
        batch_id = "batch_test_789"
        await store.save_mapping(
            batch_id=batch_id,
            input_url="https://example.com/input.jsonl",
            business_date=date(2025, 1, 15),
            status="validating",
        )

        # Update status
        success = await store.update_status(batch_id, "completed")
        assert success is True

        # Verify updated
        mapping = await store.get_mapping(batch_id)
        assert mapping["status"] == "completed"


@pytest.mark.asyncio
async def test_resolve_output_path():
    """Test resolving output path from various sources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)
        store = BatchMappingStore(storage)

        # Save mapping
        batch_id = "batch_test_resolve"
        await store.save_mapping(
            batch_id=batch_id,
            input_url="https://example.com/input.jsonl",
            business_date=date(2025, 1, 15),
            pipeline_prefix="data",
            output_filename="batch.jsonl",
        )

        # Resolve output path
        output_path = await resolve_output_path(
            batch_id=batch_id,
            storage=storage,
            mapping_store=store,
        )

        assert output_path == "data/20250115/batch.jsonl"
