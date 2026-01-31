"""Tests for storage providers."""

import pytest
import tempfile

from srx_lib_llm.storage import LocalStorageProvider


@pytest.mark.asyncio
async def test_local_storage_upload_download():
    """Test local storage upload and download."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)

        # Upload file
        data = b"test data"
        await storage.upload_file(data, "test/file.txt")

        # Verify file exists
        assert await storage.file_exists("test/file.txt")

        # Download file
        downloaded = await storage.download_file("test/file.txt")
        assert downloaded == data


@pytest.mark.asyncio
async def test_local_storage_delete():
    """Test local storage delete."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)

        # Upload file
        data = b"test data"
        await storage.upload_file(data, "test/file.txt")

        # Delete file
        assert await storage.delete_file("test/file.txt") is True

        # Verify deleted
        assert await storage.file_exists("test/file.txt") is False


@pytest.mark.asyncio
async def test_local_storage_upload_stream():
    """Test local storage stream upload."""
    import io

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageProvider(base_dir=tmpdir)

        # Upload from stream
        data = b"stream data"
        stream = io.BytesIO(data)
        await storage.upload_stream(stream, "test/stream.txt")

        # Download and verify
        downloaded = await storage.download_file("test/stream.txt")
        assert downloaded == data
