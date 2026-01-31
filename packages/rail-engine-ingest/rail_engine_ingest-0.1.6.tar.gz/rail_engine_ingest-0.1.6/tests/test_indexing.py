"""Tests for indexing API methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from railtown.engine.client import Railengine
from railtown.engine.indexing import search_index


@pytest.fixture
def mock_client(sample_pat, sample_engine_id):
    """Create a mock Railengine client."""
    with patch("railtown.engine.indexing.httpx.AsyncClient") as mock_client_class:
        mock_http_client = AsyncMock()
        mock_client_class.return_value = mock_http_client

        client = Railengine(pat=sample_pat, engine_id=sample_engine_id)
        client._client = mock_http_client
        yield client, mock_http_client


@pytest.mark.asyncio
async def test_search_index_success(mock_client):
    """Test searching index successfully."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"id": "1", "content": "apple pie"},
            {"id": "2", "content": "banana bread"},
        ],
        "Count": 2,
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)

    results = []
    async for item in search_index(
        client,
        project_id="project-123",
        engine_id=client.engine_id,
        query={"search": "apple"},
    ):
        results.append(item)

    assert len(results) == 2
    assert results[0]["id"] == "1"
    mock_http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_search_index_with_filter(mock_client):
    """Test searching index with filter function."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Items": [
            {"id": "1", "content": "apple"},
            {"id": "2", "content": "banana"},
        ],
        "Count": 2,
    }
    mock_http_client.post = AsyncMock(return_value=mock_response)

    def filter_fn(item):
        return "apple" in item.get("content", "")

    results = []
    async for item in search_index(
        client,
        project_id="project-123",
        engine_id=client.engine_id,
        query={"search": "fruit"},
        filter_fn=filter_fn,
    ):
        results.append(item)

    assert len(results) == 1
    assert results[0]["id"] == "1"


@pytest.mark.asyncio
async def test_search_index_empty_results(mock_client):
    """Test searching index with empty results."""
    client, mock_http_client = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Items": [], "Count": 0}
    mock_http_client.post = AsyncMock(return_value=mock_response)

    results = []
    async for item in search_index(
        client,
        project_id="project-123",
        engine_id=client.engine_id,
        query={"search": "nonexistent"},
    ):
        results.append(item)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_index_handles_errors_gracefully(mock_client):
    """Test search_index handles errors gracefully."""
    client, mock_http_client = mock_client

    error = httpx.RequestError("Connection error")
    mock_http_client.post = AsyncMock(side_effect=error)

    results = []
    async for item in search_index(
        client,
        project_id="project-123",
        engine_id=client.engine_id,
        query={"search": "test"},
    ):
        results.append(item)

    # Should return empty iterable on error
    assert len(results) == 0
