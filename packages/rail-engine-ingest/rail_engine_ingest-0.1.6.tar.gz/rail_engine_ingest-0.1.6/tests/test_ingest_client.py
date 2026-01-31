"""Tests for ingestion client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from railtown.engine.exceptions import (
    RailtownBadRequestError,
    RailtownServerError,
    RailtownUnauthorizedError,
)
from railtown.engine.ingest.client import RailengineIngest


class FoodDiaryItem(BaseModel):
    """Test Pydantic model."""

    food_name: str
    calories: int
    carbs: float = 0.0
    proteins: float = 0.0
    fats: float = 0.0


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    with patch("railtown.engine.ingest.client.httpx.AsyncClient") as mock_client_class:
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
async def test_client_initialization_with_token(sample_engine_token, mock_httpx_client):
    """Test client initialization with ENGINE_TOKEN."""
    client = RailengineIngest(engine_token=sample_engine_token)

    assert client.engine_id == "test-engine-id-123"
    assert client.ingestion_url == "https://eng123.railtownlogs.com"
    assert client.ingestion_api_token == "test-auth-token"
    mock_httpx_client.assert_called_once()


@pytest.mark.asyncio
async def test_client_initialization_with_env(monkeypatch, sample_engine_token, mock_httpx_client):
    """Test client initialization with ENGINE_TOKEN from environment."""
    monkeypatch.setenv("ENGINE_TOKEN", sample_engine_token)

    client = RailengineIngest()

    assert client.engine_id == "test-engine-id-123"
    assert client.ingestion_url == "https://eng123.railtownlogs.com"


@pytest.mark.asyncio
async def test_client_initialization_missing_token(monkeypatch, mock_httpx_client):
    """Test client initialization without ENGINE_TOKEN."""
    monkeypatch.delenv("ENGINE_TOKEN", raising=False)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        RailengineIngest()

    assert "ENGINE_TOKEN is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_initialization_with_model(sample_engine_token, mock_httpx_client):
    """Test client initialization with Pydantic model."""
    client = RailengineIngest(engine_token=sample_engine_token, model=FoodDiaryItem)
    assert client._model == FoodDiaryItem


@pytest.mark.asyncio
async def test_prepare_ingestion_url_adds_protocol(sample_engine_token, mock_httpx_client):
    """Test URL preparation adds protocol if missing."""
    client = RailengineIngest(engine_token=sample_engine_token)

    # Test URL without protocol
    url = client._prepare_ingestion_url("eng123.railtownlogs.com")
    assert url.startswith("https://")


@pytest.mark.asyncio
async def test_prepare_ingestion_url_adds_path(sample_engine_token, mock_httpx_client):
    """Test URL preparation adds path if missing."""
    client = RailengineIngest(engine_token=sample_engine_token)

    # Test URL without path
    url = client._prepare_ingestion_url("https://eng123.railtownlogs.com")
    assert "/api/Engine/Storage" in url


@pytest.mark.asyncio
async def test_upsert_with_dict(sample_engine_token, mock_httpx_client, sample_food_diary_item):
    """Test upsert with dictionary data."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_httpx_client.instance.post = AsyncMock(return_value=mock_response)

    client = RailengineIngest(engine_token=sample_engine_token)

    response = await client.upsert(sample_food_diary_item)

    assert response.status_code == 200
    mock_httpx_client.instance.post.assert_called_once()
    call_args = mock_httpx_client.instance.post.call_args
    assert "x-rail-auth" in call_args[1]["headers"]
    assert call_args[1]["headers"]["x-rail-auth"] == "test-auth-token"


@pytest.mark.asyncio
async def test_upsert_with_model(sample_engine_token, mock_httpx_client):
    """Test upsert with Pydantic model instance."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_httpx_client.instance.post = AsyncMock(return_value=mock_response)

    client = RailengineIngest(engine_token=sample_engine_token, model=FoodDiaryItem)

    item = FoodDiaryItem(food_name="Apple", calories=95, carbs=25.0, proteins=0.5, fats=0.3)
    response = await client.upsert(item)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upsert_with_json_string(sample_engine_token, mock_httpx_client):
    """Test upsert with JSON string."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_httpx_client.instance.post = AsyncMock(return_value=mock_response)

    client = RailengineIngest(engine_token=sample_engine_token)

    json_data = json.dumps({"food_name": "Apple", "calories": 95})
    response = await client.upsert(json_data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upsert_with_model_validation(sample_engine_token, mock_httpx_client):
    """Test upsert validates data against model."""
    client = RailengineIngest(engine_token=sample_engine_token, model=FoodDiaryItem)

    # Invalid data (missing required field)
    invalid_data = {"calories": 95}  # Missing food_name

    with pytest.raises(RailtownBadRequestError) as exc_info:
        await client.upsert(invalid_data)

    assert "validation failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_upsert_invalid_json_string(sample_engine_token, mock_httpx_client):
    """Test upsert with invalid JSON string."""
    client = RailengineIngest(engine_token=sample_engine_token)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        await client.upsert("not valid json {")

    assert "invalid json" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_upsert_handles_400_error(
    sample_engine_token, mock_httpx_client, sample_food_diary_item
):
    """Test upsert handles 400 Bad Request error."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    error = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
    mock_httpx_client.instance.post = AsyncMock(side_effect=error)

    client = RailengineIngest(engine_token=sample_engine_token)

    with pytest.raises(RailtownBadRequestError) as exc_info:
        await client.upsert(sample_food_diary_item)

    assert "bad request" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_upsert_handles_401_error(
    sample_engine_token, mock_httpx_client, sample_food_diary_item
):
    """Test upsert handles 401 Unauthorized error."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
    mock_httpx_client.instance.post = AsyncMock(side_effect=error)

    client = RailengineIngest(engine_token=sample_engine_token)

    with pytest.raises(RailtownUnauthorizedError) as exc_info:
        await client.upsert(sample_food_diary_item)

    assert "unauthorized" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_upsert_handles_500_error(
    sample_engine_token, mock_httpx_client, sample_food_diary_item
):
    """Test upsert handles 500 Server Error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    error = httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_response)
    mock_httpx_client.instance.post = AsyncMock(side_effect=error)

    client = RailengineIngest(engine_token=sample_engine_token)

    with pytest.raises(RailtownServerError) as exc_info:
        await client.upsert(sample_food_diary_item)

    assert "server error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_client_context_manager(sample_engine_token, mock_httpx_client):
    """Test client as async context manager."""
    async with RailengineIngest(engine_token=sample_engine_token) as client:
        assert client.engine_id == "test-engine-id-123"

    # Client should be closed after context exit
    mock_httpx_client.instance.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_client_close(sample_engine_token, mock_httpx_client):
    """Test client close method."""
    client = RailengineIngest(engine_token=sample_engine_token)
    await client.close()

    mock_httpx_client.instance.aclose.assert_called_once()
