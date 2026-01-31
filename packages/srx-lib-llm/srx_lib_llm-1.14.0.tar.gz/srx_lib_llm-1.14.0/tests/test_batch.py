"""Tests for OpenAI Batch API service."""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from srx_lib_llm.batch import (
    BatchInfo,
    BatchMapping,
    BatchPayload,
    BatchRequest,
    BatchResponse,
    BatchStatus,
    OpenAIBatchService,
    check_batch_status,
    create_batch_from_url,
)


@pytest.fixture
def mock_api_key():
    """Mock API key."""
    return "test-api-key"


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace directory."""
    workspace = tmp_path / "batch_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def batch_service(mock_api_key, temp_workspace):
    """Create batch service with mocked clients."""
    with patch("srx_lib_llm.batch.OpenAI"), patch("srx_lib_llm.batch.AsyncOpenAI"):
        service = OpenAIBatchService(api_key=mock_api_key, workspace_dir=str(temp_workspace))
        return service


@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV file."""
    csv_path = tmp_path / "data.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "age", "city"])
        writer.writeheader()
        writer.writerow({"name": "Alice", "age": "30", "city": "NYC"})
        writer.writerow({"name": "Bob", "age": "25", "city": "SF"})
    return str(csv_path)


@pytest.fixture
def sample_jsonl(tmp_path):
    """Create sample JSONL file."""
    jsonl_path = tmp_path / "data.jsonl"
    with open(jsonl_path, "w") as f:
        f.write(json.dumps({"name": "Alice", "age": 30, "city": "NYC"}) + "\n")
        f.write(json.dumps({"name": "Bob", "age": 25, "city": "SF"}) + "\n")
    return str(jsonl_path)


class TestBatchPayload:
    """Test BatchPayload class."""

    def test_get_model_with_explicit_model(self):
        """Test get_model with explicit model."""
        payload = BatchPayload(model="gpt-4-turbo")
        assert payload.get_model() == "gpt-4-turbo"

    def test_get_model_with_env_var(self):
        """Test get_model with OPENAI_MODEL env var."""
        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-3.5-turbo"}):
            payload = BatchPayload()
            assert payload.get_model() == "gpt-3.5-turbo"

    def test_get_model_default(self):
        """Test get_model with default."""
        with patch.dict(os.environ, {}, clear=True):
            payload = BatchPayload()
            assert payload.get_model() == "gpt-4"


class TestBatchRequest:
    """Test BatchRequest class."""

    def test_to_jsonl(self):
        """Test converting request to JSONL format."""
        req = BatchRequest(
            custom_id="test-1",
            method="POST",
            url="/v1/chat/completions",
            body={"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
        )

        jsonl = req.to_jsonl()
        data = json.loads(jsonl)

        assert data["custom_id"] == "test-1"
        assert data["method"] == "POST"
        assert data["url"] == "/v1/chat/completions"
        assert data["body"]["model"] == "gpt-4"

    def test_from_jsonl(self):
        """Test creating request from JSONL line."""
        jsonl_line = json.dumps(
            {
                "custom_id": "test-1",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]},
            }
        )

        req = BatchRequest.from_jsonl(jsonl_line)

        assert req.custom_id == "test-1"
        assert req.method == "POST"
        assert req.url == "/v1/chat/completions"
        assert req.body["model"] == "gpt-4"


class TestBatchResponse:
    """Test BatchResponse class."""

    def test_from_jsonl_success(self):
        """Test parsing successful response."""
        jsonl_line = json.dumps(
            {
                "id": "resp-1",
                "custom_id": "test-1",
                "response": {
                    "status_code": 200,
                    "body": {"choices": [{"message": {"content": "Hello!"}}]},
                },
            }
        )

        resp = BatchResponse.from_jsonl(jsonl_line)

        assert resp.id == "resp-1"
        assert resp.custom_id == "test-1"
        assert resp.response is not None
        assert resp.error is None

    def test_from_jsonl_error(self):
        """Test parsing error response."""
        jsonl_line = json.dumps(
            {
                "id": "resp-1",
                "custom_id": "test-1",
                "error": {"code": "invalid_request", "message": "Bad request"},
            }
        )

        resp = BatchResponse.from_jsonl(jsonl_line)

        assert resp.id == "resp-1"
        assert resp.custom_id == "test-1"
        assert resp.response is None
        assert resp.error is not None


class TestBatchInfo:
    """Test BatchInfo class."""

    def test_from_api_response(self):
        """Test creating BatchInfo from API response."""
        api_data = {
            "id": "batch_123",
            "status": "completed",
            "input_file_id": "file_input",
            "output_file_id": "file_output",
            "created_at": 1704067200,
            "completed_at": 1704153600,
            "request_counts": {"total": 100, "completed": 100, "failed": 0},
            "metadata": {"project": "test"},
        }

        info = BatchInfo.from_api_response(api_data)

        assert info.id == "batch_123"
        assert info.status == BatchStatus.COMPLETED
        assert info.input_file_id == "file_input"
        assert info.output_file_id == "file_output"
        assert isinstance(info.created_at, datetime)
        assert info.request_counts["total"] == 100
        assert info.metadata["project"] == "test"


class TestOpenAIBatchService:
    """Test OpenAIBatchService class."""

    def test_init_with_api_key(self, mock_api_key, temp_workspace):
        """Test service initialization with API key."""
        with patch("srx_lib_llm.batch.OpenAI"), patch("srx_lib_llm.batch.AsyncOpenAI"):
            service = OpenAIBatchService(api_key=mock_api_key, workspace_dir=str(temp_workspace))

            assert service.api_key == mock_api_key
            assert service.workspace_dir == temp_workspace

    def test_init_without_api_key(self, temp_workspace):
        """Test service initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY must be set"):
                OpenAIBatchService(workspace_dir=str(temp_workspace))

    def test_detect_file_format_csv(self, batch_service, sample_csv):
        """Test detecting CSV format."""
        fmt = batch_service._detect_file_format(sample_csv)
        assert fmt == "csv"

    def test_detect_file_format_jsonl(self, batch_service, sample_jsonl):
        """Test detecting JSONL format."""
        fmt = batch_service._detect_file_format(sample_jsonl)
        assert fmt == "jsonl"

    def test_read_data_file_csv(self, batch_service, sample_csv):
        """Test reading CSV file."""
        data = batch_service._read_data_file(sample_csv)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_read_data_file_jsonl(self, batch_service, sample_jsonl):
        """Test reading JSONL file."""
        data = batch_service._read_data_file(sample_jsonl)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_interpolate_prompt(self, batch_service):
        """Test prompt interpolation."""
        prompt = "Hello {name}, you are {age} years old"
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        result = batch_service._interpolate_prompt(prompt, data)
        assert result == "Hello Alice, you are 30 years old"

    def test_build_batch_requests_with_global_prompt(self, batch_service):
        """Test building requests with global prompt."""
        data_rows = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        payload = BatchPayload(
            prompt="Hello {name}, age {age}",
            model="gpt-4",
        )

        requests = batch_service._build_batch_requests(data_rows, payload)

        assert len(requests) == 2
        assert requests[0].custom_id == "req-1"
        assert requests[0].body["messages"][0]["content"] == "Hello Alice, age 30"
        assert requests[1].body["messages"][0]["content"] == "Hello Bob, age 25"

    def test_build_batch_requests_with_row_level_prompt(self, batch_service):
        """Test building requests with row-level prompts (row wins)."""
        data_rows = [
            {"prompt": "Custom prompt 1", "data": "foo"},
            {"prompt": "Custom prompt 2", "data": "bar"},
        ]
        payload = BatchPayload(
            prompt="Global prompt {data}",  # Should be ignored
            model="gpt-4",
        )

        requests = batch_service._build_batch_requests(data_rows, payload)

        assert len(requests) == 2
        assert requests[0].body["messages"][0]["content"] == "Custom prompt 1"
        assert requests[1].body["messages"][0]["content"] == "Custom prompt 2"

    def test_build_batch_requests_with_custom_ids(self, batch_service):
        """Test building requests with custom IDs."""
        data_rows = [
            {"custom_id": "my-id-1", "prompt": "Test 1"},
            {"custom_id": "my-id-2", "prompt": "Test 2"},
        ]
        payload = BatchPayload(model="gpt-4")

        requests = batch_service._build_batch_requests(data_rows, payload)

        assert requests[0].custom_id == "my-id-1"
        assert requests[1].custom_id == "my-id-2"

    def test_build_batch_requests_no_prompt_raises_error(self, batch_service):
        """Test building requests without prompt raises error."""
        data_rows = [{"name": "Alice"}]
        payload = BatchPayload(model="gpt-4")  # No prompt

        with pytest.raises(ValueError, match="No prompt found"):
            batch_service._build_batch_requests(data_rows, payload)

    def test_build_batch_requests_with_system_message(self, batch_service):
        """Test building requests with system message."""
        data_rows = [{"prompt": "Hello"}]
        payload = BatchPayload(
            model="gpt-4",
            system_message="You are helpful",
        )

        requests = batch_service._build_batch_requests(data_rows, payload)

        messages = requests[0].body["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_download_file_from_url(self, batch_service):
        """Test downloading file from URL."""
        test_content = b"name,age\nAlice,30\nBob,25"
        mock_response = Mock()
        mock_response.content = test_content

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_response.raise_for_status = Mock()

            url = "https://example.com/data.csv"
            result_path = await batch_service.download_file_from_url(url)

            assert Path(result_path).exists()
            with open(result_path, "rb") as f:
                assert f.read() == test_content

    @pytest.mark.asyncio
    async def test_create_batch_from_file(self, batch_service, sample_csv):
        """Test creating batch from file."""
        # Mock file upload
        mock_file = Mock()
        mock_file.id = "file_123"
        batch_service.async_client.files.create = AsyncMock(return_value=mock_file)

        # Mock batch creation
        mock_batch = Mock()
        mock_batch.id = "batch_123"
        mock_batch.status = "validating"
        mock_batch.created_at = 1704067200
        batch_service.async_client.batches.create = AsyncMock(return_value=mock_batch)

        payload = BatchPayload(prompt="Analyze {name}, age {age}, from {city}")

        mapping = await batch_service.create_batch_from_file(sample_csv, payload)

        assert mapping.batch_id == "batch_123"
        assert mapping.input_file_id == "file_123"
        assert mapping.status == BatchStatus.VALIDATING

    @pytest.mark.asyncio
    async def test_create_batch_from_data(self, batch_service):
        """Test creating batch from in-memory data."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]

        # Mock file upload
        mock_file = Mock()
        mock_file.id = "file_123"
        batch_service.async_client.files.create = AsyncMock(return_value=mock_file)

        # Mock batch creation
        mock_batch = Mock()
        mock_batch.id = "batch_123"
        mock_batch.status = "validating"
        mock_batch.created_at = 1704067200
        batch_service.async_client.batches.create = AsyncMock(return_value=mock_batch)

        payload = BatchPayload(prompt="Process {name}, age {age}")

        mapping = await batch_service.create_batch_from_data(data, payload)

        assert mapping.batch_id == "batch_123"
        assert mapping.input_file_id == "file_123"

    @pytest.mark.asyncio
    async def test_get_batch_status(self, batch_service):
        """Test getting batch status."""
        mock_batch = Mock()
        mock_batch.model_dump.return_value = {
            "id": "batch_123",
            "status": "in_progress",
            "input_file_id": "file_input",
            "output_file_id": None,
            "created_at": 1704067200,
            "request_counts": {"total": 100, "completed": 50},
        }
        batch_service.async_client.batches.retrieve = AsyncMock(return_value=mock_batch)

        info = await batch_service.get_batch_status("batch_123")

        assert info.id == "batch_123"
        assert info.status == BatchStatus.IN_PROGRESS
        assert info.request_counts["completed"] == 50

    @pytest.mark.asyncio
    async def test_get_batch_results(self, batch_service):
        """Test getting batch results."""
        # Mock batch status
        mock_batch = Mock()
        mock_batch.model_dump.return_value = {
            "id": "batch_123",
            "status": "completed",
            "input_file_id": "file_input",
            "output_file_id": "file_output",
            "created_at": 1704067200,
            "completed_at": 1704153600,
        }
        batch_service.async_client.batches.retrieve = AsyncMock(return_value=mock_batch)

        # Mock file content
        result_jsonl = (
            '{"id": "resp-1", "custom_id": "req-1", "response": {"status_code": 200, "body": {}}}\n'
            '{"id": "resp-2", "custom_id": "req-2", "response": {"status_code": 200, "body": {}}}\n'
        )
        mock_content = Mock()
        mock_content.content = result_jsonl.encode("utf-8")
        batch_service.client.files.content = Mock(return_value=mock_content)

        results = await batch_service.get_batch_results("batch_123")

        assert len(results) == 2
        assert results[0].custom_id == "req-1"
        assert results[1].custom_id == "req-2"

    @pytest.mark.asyncio
    async def test_cancel_batch(self, batch_service):
        """Test canceling a batch."""
        mock_batch = Mock()
        mock_batch.model_dump.return_value = {
            "id": "batch_123",
            "status": "cancelling",
            "input_file_id": "file_input",
            "created_at": 1704067200,
        }
        batch_service.async_client.batches.cancel = AsyncMock(return_value=mock_batch)

        info = await batch_service.cancel_batch("batch_123")

        assert info.id == "batch_123"
        assert info.status == BatchStatus.CANCELLING

    def test_get_mapping(self, batch_service):
        """Test getting batch mapping."""
        mapping = BatchMapping(
            batch_id="batch_123",
            input_file_id="file_input",
            output_file_id=None,
            error_file_id=None,
        )
        batch_service._mappings["batch_123"] = mapping

        result = batch_service.get_mapping("batch_123")

        assert result == mapping
        assert result.batch_id == "batch_123"


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_create_batch_from_url(self, mock_api_key):
        """Test convenience function for creating batch from URL."""
        with patch("srx_lib_llm.batch.OpenAIBatchService") as mock_service_class:
            mock_service = Mock()
            mock_mapping = BatchMapping(
                batch_id="batch_123",
                input_file_id="file_123",
                output_file_id=None,
                error_file_id=None,
            )
            mock_service.create_batch_from_url = AsyncMock(return_value=mock_mapping)
            mock_service_class.return_value = mock_service

            payload = BatchPayload(prompt="Test {data}")
            result = await create_batch_from_url(
                "https://example.com/data.csv", payload, api_key=mock_api_key
            )

            assert result.batch_id == "batch_123"
            mock_service_class.assert_called_once_with(api_key=mock_api_key)

    @pytest.mark.asyncio
    async def test_check_batch_status(self, mock_api_key):
        """Test convenience function for checking batch status."""
        with patch("srx_lib_llm.batch.OpenAIBatchService") as mock_service_class:
            mock_service = Mock()
            mock_info = BatchInfo(
                id="batch_123",
                status=BatchStatus.COMPLETED,
                input_file_id="file_input",
                output_file_id="file_output",
            )
            mock_service.get_batch_status = AsyncMock(return_value=mock_info)
            mock_service_class.return_value = mock_service

            result = await check_batch_status("batch_123", api_key=mock_api_key)

            assert result.id == "batch_123"
            assert result.status == BatchStatus.COMPLETED
