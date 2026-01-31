"""Tests for retrieval client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from railtown.engine.client import Railengine
from railtown.engine.exceptions import (
    RailtownBadRequestError,
    RailtownError,
    RailtownNotFoundError,
    RailtownServerError,
    RailtownUnauthorizedError,
)


class FoodDiaryItem(BaseModel):
    """Test Pydantic model."""

    food_name: str
    calories: int


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    with patch("railtown.engine.client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        # Yield both class (for assertions) and instance (for method setup)
        yield type(
            "MockClient",
            (),
            {
                "class": mock_client_class,
                "instance": mock_client,
                "post": mock_client.post,
                "get": mock_client.get,
                "aclose": mock_client.aclose,
                "assert_called_once": mock_client_class.assert_called_once,
            },
        )()


@pytest.mark.asyncio
async def test_client_initialization_with_params(
    monkeypatch, sample_pat, sample_engine_id, mock_httpx_client
):
    """Test client initialization with parameters."""
    # Clear RAILTOWN_API_URL to ensure default is used
    monkeypatch.delenv("RAILTOWN_API_URL", raising=False)

    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    assert client.pat == sample_pat
    assert client.engine_id == sample_engine_id
    assert client.api_url == "https://cndr.railtown.ai"  # Normalized (no /api)
    mock_httpx_client.assert_called_once()


@pytest.mark.asyncio
async def test_client_initialization_with_env(
    monkeypatch, sample_pat, sample_engine_id, mock_httpx_client
):
    """Test client initialization with environment variables."""
    monkeypatch.setenv("ENGINE_PAT", sample_pat)
    monkeypatch.setenv("ENGINE_ID", sample_engine_id)

    client = Railengine()

    assert client.pat == sample_pat
    assert client.engine_id == sample_engine_id


@pytest.mark.asyncio
async def test_client_initialization_missing_pat(monkeypatch, mock_httpx_client):
    """Test client initialization without PAT."""
    monkeypatch.delenv("ENGINE_PAT", raising=False)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        Railengine(engine_id="test-engine-id")

    assert "PAT is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_initialization_missing_engine_id(monkeypatch, sample_pat, mock_httpx_client):
    """Test client initialization without engine ID."""
    monkeypatch.delenv("ENGINE_ID", raising=False)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        Railengine(pat=sample_pat)

    assert "engine_id is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_initialization_with_model(sample_pat, sample_engine_id, mock_httpx_client):
    """Test client initialization with Pydantic model."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id, model=FoodDiaryItem)
    assert client.model == FoodDiaryItem


@pytest.mark.asyncio
async def test_client_initialization_with_custom_api_url(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test client initialization with custom API URL."""
    custom_url = "https://custom.api.url/api"
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id, api_url=custom_url)

    assert client.api_url == "https://custom.api.url"  # Normalized


@pytest.mark.asyncio
async def test_client_get_headers(sample_pat, sample_engine_id, mock_httpx_client):
    """Test _get_headers method."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    headers = client._get_headers()

    assert "Authorization" in headers
    assert headers["Authorization"] == sample_pat
    assert "Content-Type" in headers
    assert "charset=utf-8" in headers["Content-Type"]


@pytest.mark.asyncio
async def test_client_context_manager(sample_pat, sample_engine_id, mock_httpx_client):
    """Test client as async context manager."""
    async with Railengine(pat=sample_pat, engine_id=sample_engine_id) as client:
        assert client.engine_id == sample_engine_id

    # Client should be closed after context exit
    mock_httpx_client.instance.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_client_close(sample_pat, sample_engine_id, mock_httpx_client):
    """Test client close method."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)
    await client.close()

    mock_httpx_client.instance.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_success(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test getting storage document by EventId successfully."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple"}',
    }
    mock_httpx_client.instance.get = AsyncMock(return_value=mock_response)

    result = await client.get_storage_document_by_event_id(event_id="event-123")

    assert result is not None
    assert result["EventId"] == "event-123"
    mock_httpx_client.instance.get.assert_called_once()
    # Verify EventId parameter was used
    call_args = mock_httpx_client.instance.get.call_args
    assert "EventId" in call_args.kwargs["params"]
    assert call_args.kwargs["params"]["EventId"] == "event-123"


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_not_found(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test getting storage document by EventId when not found."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.instance.get = AsyncMock(return_value=mock_response)

    result = await client.get_storage_document_by_event_id(event_id="event-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_with_filter(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test getting storage document by EventId with filter."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple", "calories": 95}',
    }
    mock_httpx_client.instance.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        return doc.get("Content", "").find("Apple") != -1

    result = await client.get_storage_document_by_event_id(
        event_id="event-123",
        filter_fn=filter_fn,
    )

    assert result is not None


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_with_model(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test getting storage document by EventId with model override."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "food_name": "Apple",
        "calories": 95,
    }
    mock_httpx_client.instance.get = AsyncMock(return_value=mock_response)

    result = await client.get_storage_document_by_event_id(
        event_id="event-123",
        model=FoodDiaryItem,
    )

    assert result is not None
    assert isinstance(result, FoodDiaryItem)
    assert result.food_name == "Apple"
    assert result.calories == 95


@pytest.mark.asyncio
async def test_get_storage_document_by_event_id_filter_rejects(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test get_storage_document_by_event_id with filter function that returns False."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "EngineDocumentId": "doc-123",
        "EventId": "event-123",
        "Content": '{"food_name": "Apple", "calories": 95}',
    }
    mock_httpx_client.instance.get = AsyncMock(return_value=mock_response)

    def filter_fn(doc):
        # Filter out documents with calories < 100
        return doc.get("Content", "").find('"calories": 200') != -1

    result = await client.get_storage_document_by_event_id(
        event_id="event-123",
        filter_fn=filter_fn,
    )

    # Filter should reject this document (calories is 95, not 200)
    assert result is None


# Delete event tests
@pytest.mark.asyncio
async def test_delete_event_success_204(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event returns 204 when event is deleted immediately."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    response = await client.delete_event(event_id=event_id)

    assert response.status_code == 204
    mock_httpx_client.instance.delete.assert_called_once()
    call_args = mock_httpx_client.instance.delete.call_args
    assert event_id in call_args.args[0] or event_id in str(call_args.kwargs.get("url", ""))


@pytest.mark.asyncio
async def test_delete_event_success_202(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event returns 202 when event deletion is accepted."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    response = await client.delete_event(event_id=event_id)

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_delete_event_idempotent(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event succeeds with 204 when event was already deleted (idempotent)."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    # First delete
    response1 = await client.delete_event(event_id=event_id)
    assert response1.status_code == 204

    # Second delete (idempotent)
    response2 = await client.delete_event(event_id=event_id)
    assert response2.status_code == 204


@pytest.mark.asyncio
async def test_delete_event_uses_engine_id_parameter(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event uses engine_id parameter when provided."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    custom_engine_id = "custom-engine-id"
    await client.delete_event(event_id=event_id, engine_id=custom_engine_id)

    call_args = mock_httpx_client.instance.delete.call_args
    endpoint = call_args.args[0]
    assert custom_engine_id in endpoint
    assert sample_engine_id not in endpoint


@pytest.mark.asyncio
async def test_delete_event_uses_client_engine_id(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event uses client's engine_id when parameter is not provided."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    await client.delete_event(event_id=event_id)

    call_args = mock_httpx_client.instance.delete.call_args
    endpoint = call_args.args[0]
    assert sample_engine_id in endpoint


@pytest.mark.asyncio
async def test_delete_event_constructs_correct_endpoint(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event constructs correct endpoint URL."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    await client.delete_event(event_id=event_id)

    call_args = mock_httpx_client.instance.delete.call_args
    endpoint = call_args.args[0]
    assert f"/api/Engine/{sample_engine_id}/Event/{event_id}" in endpoint
    assert client.api_url in endpoint


@pytest.mark.asyncio
async def test_delete_event_includes_pat_authentication(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event includes PAT authentication in headers."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.text = ""
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    await client.delete_event(event_id=event_id)

    call_args = mock_httpx_client.instance.delete.call_args
    headers = call_args.kwargs["headers"]
    assert "Authorization" in headers
    assert headers["Authorization"] == sample_pat


@pytest.mark.asyncio
async def test_delete_event_raises_bad_request_empty_event_id(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event raises RailtownBadRequestError when event_id is empty."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        await client.delete_event(event_id="")

    assert "event_id is required" in str(exc_info.value).lower()
    mock_httpx_client.instance.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_event_raises_bad_request_none_event_id(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event raises RailtownBadRequestError when event_id is None."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        await client.delete_event(event_id=None)

    assert "event_id is required" in str(exc_info.value).lower()
    mock_httpx_client.instance.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_event_raises_not_found_404(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event raises RailtownNotFoundError when engine is not found (404)."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Engine not found"
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownNotFoundError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_delete_event_raises_server_error_503(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event raises RailtownServerError when server error occurs (503)."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service unavailable"
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownServerError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_delete_event_raises_server_error_5xx(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event raises RailtownServerError for other 5xx errors."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownServerError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_delete_event_raises_unauthorized_401(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event raises RailtownUnauthorizedError when authentication fails (401)."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownUnauthorizedError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_delete_event_raises_error_other_4xx(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event raises RailtownError for other HTTP errors."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_httpx_client.instance.delete = AsyncMock(return_value=mock_response)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_event_handles_httpx_status_error(
    sample_pat, sample_engine_id, mock_httpx_client
):
    """Test delete_event handles httpx.HTTPStatusError and converts to custom exception."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    http_status_error = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.instance.delete = AsyncMock(side_effect=http_status_error)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownNotFoundError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_handles_request_error(sample_pat, sample_engine_id, mock_httpx_client):
    """Test delete_event handles httpx.RequestError and converts to RailtownError."""
    client = Railengine(pat=sample_pat, engine_id=sample_engine_id)

    import httpx

    request_error = httpx.RequestError("Connection error", request=MagicMock())
    mock_httpx_client.instance.delete = AsyncMock(side_effect=request_error)

    event_id = "123e4567-e89b-12d3-a456-426614174000"
    with pytest.raises(RailtownError) as exc_info:
        await client.delete_event(event_id=event_id)

    assert "Request error" in str(exc_info.value)
