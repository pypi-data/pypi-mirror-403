"""Tests for retrieval authentication module."""

from railtown.engine.auth import get_api_url, get_engine_id, get_pat, normalize_base_url


def test_get_pat_from_env(monkeypatch):
    """Test getting PAT from environment variable."""
    pat = "test-pat-from-env"
    monkeypatch.setenv("ENGINE_PAT", pat)

    result = get_pat()
    assert result == pat


def test_get_pat_from_parameter():
    """Test getting PAT from parameter."""
    pat = "test-pat-from-param"
    result = get_pat(pat)
    assert result == pat


def test_get_pat_parameter_overrides_env(monkeypatch):
    """Test that parameter overrides environment variable."""
    env_pat = "env-pat"
    param_pat = "param-pat"
    monkeypatch.setenv("ENGINE_PAT", env_pat)

    result = get_pat(param_pat)
    assert result == param_pat


def test_get_pat_not_found(monkeypatch):
    """Test getting PAT when not set."""
    monkeypatch.delenv("ENGINE_PAT", raising=False)

    result = get_pat()
    assert result is None


def test_get_engine_id_from_env(monkeypatch):
    """Test getting engine ID from environment variable."""
    engine_id = "test-engine-id-from-env"
    monkeypatch.setenv("ENGINE_ID", engine_id)

    result = get_engine_id()
    assert result == engine_id


def test_get_engine_id_from_parameter():
    """Test getting engine ID from parameter."""
    engine_id = "test-engine-id-from-param"
    result = get_engine_id(engine_id)
    assert result == engine_id


def test_get_engine_id_not_found(monkeypatch):
    """Test getting engine ID when not set."""
    monkeypatch.delenv("ENGINE_ID", raising=False)

    result = get_engine_id()
    assert result is None


def test_get_api_url_from_env(monkeypatch):
    """Test getting API URL from environment variable."""
    api_url = "https://custom.api.url/api"
    monkeypatch.setenv("RAILTOWN_API_URL", api_url)

    result = get_api_url()
    assert result == api_url


def test_get_api_url_from_parameter():
    """Test getting API URL from parameter."""
    api_url = "https://custom.api.url/api"
    result = get_api_url(api_url)
    assert result == api_url


def test_get_api_url_defaults_to_production(monkeypatch):
    """Test getting API URL defaults to production."""
    monkeypatch.delenv("RAILTOWN_API_URL", raising=False)

    result = get_api_url()
    assert result == "https://cndr.railtown.ai/api"


def test_normalize_base_url_strips_api_suffix():
    """Test normalize_base_url strips /api suffix."""
    url = "https://cndr.railtown.ai/api"
    result = normalize_base_url(url)
    assert result == "https://cndr.railtown.ai"


def test_normalize_base_url_preserves_url_without_suffix():
    """Test normalize_base_url preserves URL without /api suffix."""
    url = "https://cndr.railtown.ai"
    result = normalize_base_url(url)
    assert result == url


def test_normalize_base_url_handles_trailing_slash():
    """Test normalize_base_url handles trailing slash."""
    url = "https://cndr.railtown.ai/api/"
    result = normalize_base_url(url)
    # Should strip /api/ including trailing slash
    assert result == "https://cndr.railtown.ai"
