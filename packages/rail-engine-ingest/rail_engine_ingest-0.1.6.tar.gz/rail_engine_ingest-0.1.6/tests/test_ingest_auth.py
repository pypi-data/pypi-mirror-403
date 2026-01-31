"""Tests for ingestion authentication module."""

import base64
import json

import pytest

from railtown.engine.exceptions import RailtownBadRequestError
from railtown.engine.ingest.auth import decode_engine_token, get_engine_token


def test_decode_engine_token_valid(sample_engine_token, sample_engine_token_data):
    """Test decoding a valid ENGINE_TOKEN."""
    result = decode_engine_token(sample_engine_token)

    assert result == sample_engine_token_data
    assert result["ingestion_url"] == "https://eng123.railtownlogs.com"
    assert result["ingestion_api_token"] == "test-auth-token"
    assert result["engine_id"] == "test-engine-id-123"


def test_decode_engine_token_missing_fields():
    """Test decoding ENGINE_TOKEN with missing required fields."""
    token_data = {
        "IngestionUrl": "https://eng123.railtownlogs.com",
        # Missing IngestionApiToken and EngineId
    }
    token = base64.b64encode(json.dumps(token_data).encode()).decode()

    with pytest.raises(RailtownBadRequestError) as exc_info:
        decode_engine_token(token)

    assert "missing required fields" in str(exc_info.value).lower()


def test_decode_engine_token_invalid_base64():
    """Test decoding invalid base64 ENGINE_TOKEN."""
    with pytest.raises(RailtownBadRequestError) as exc_info:
        decode_engine_token("not-valid-base64!!!")

    assert "not valid base64" in str(exc_info.value).lower()


def test_decode_engine_token_invalid_json():
    """Test decoding ENGINE_TOKEN with invalid JSON."""
    invalid_json = base64.b64encode(b"not valid json {").decode()

    with pytest.raises(RailtownBadRequestError) as exc_info:
        decode_engine_token(invalid_json)

    assert "does not contain valid json" in str(exc_info.value).lower()


def test_decode_engine_token_empty():
    """Test decoding empty ENGINE_TOKEN."""
    with pytest.raises(RailtownBadRequestError) as exc_info:
        decode_engine_token("")

    assert "required" in str(exc_info.value).lower()


def test_get_engine_token_from_env(monkeypatch):
    """Test getting ENGINE_TOKEN from environment variable."""
    token = "test-token-from-env"
    monkeypatch.setenv("ENGINE_TOKEN", token)

    result = get_engine_token()
    assert result == token


def test_get_engine_token_from_parameter():
    """Test getting ENGINE_TOKEN from parameter."""
    token = "test-token-from-param"
    result = get_engine_token(token)
    assert result == token


def test_get_engine_token_parameter_overrides_env(monkeypatch):
    """Test that parameter overrides environment variable."""
    env_token = "env-token"
    param_token = "param-token"
    monkeypatch.setenv("ENGINE_TOKEN", env_token)

    result = get_engine_token(param_token)
    assert result == param_token


def test_get_engine_token_not_found(monkeypatch):
    """Test getting ENGINE_TOKEN when not set."""
    monkeypatch.delenv("ENGINE_TOKEN", raising=False)

    result = get_engine_token()
    assert result is None
