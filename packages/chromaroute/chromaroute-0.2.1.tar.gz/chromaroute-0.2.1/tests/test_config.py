"""Tests for embedding configuration."""

import pytest

from chromaroute import EmbedConfig, load_config


def _config(
    *,
    openrouter_key: str | None = None,
    embed_provider: str = "auto",
) -> EmbedConfig:
    """Helper to create test configurations."""
    return EmbedConfig(
        openrouter_api_key=openrouter_key,
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_embeddings_model="openai/text-embedding-3-small",
        openrouter_referer=None,
        openrouter_title=None,
        openrouter_provider_json=None,
        local_embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
        embed_provider=embed_provider,
    )


def test_resolve_provider_auto_falls_back_to_openrouter():
    """Test auto mode falls back to OpenRouter."""
    config = _config(openrouter_key="ok")
    assert config.resolve_provider(None) == "openrouter"


def test_resolve_provider_auto_falls_back_to_local():
    """Test auto mode falls back to local."""
    config = _config(openrouter_key=None)
    assert config.resolve_provider(None) == "local"


def test_resolve_provider_explicit_override():
    """Test explicit provider override."""
    config = _config(openrouter_key="ok")
    assert config.resolve_provider("openrouter") == "openrouter"


def test_resolve_model_prefers_explicit():
    """Test explicit model overrides config."""
    config = _config(openrouter_key="ok")
    assert config.resolve_model(provider="openrouter", explicit_model="custom") == "custom"


def test_resolve_model_by_provider():
    """Test model resolution by provider."""
    config = _config(openrouter_key="ok")
    assert config.resolve_model(provider="openrouter") == "openai/text-embedding-3-small"
    assert config.resolve_model(provider="local") == "sentence-transformers/all-MiniLM-L6-v2"


def test_resolve_model_unknown_provider_defaults():
    """Test unknown provider falls back to default model."""
    config = _config(openrouter_key=None)
    assert config.resolve_model(provider="unknown") == "default"


def test_openrouter_provider_config_none():
    """Test empty provider config."""
    config = _config(openrouter_key="ok")
    assert config.openrouter_provider_config() is None


def test_openrouter_provider_config_json():
    """Test JSON provider config."""
    config = EmbedConfig(
        openrouter_api_key="ok",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_embeddings_model="openai/text-embedding-3-small",
        openrouter_referer=None,
        openrouter_title=None,
        openrouter_provider_json='{"order": ["a", "b"], "allow_fallbacks": true}',
        local_embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
        embed_provider="auto",
    )
    assert config.openrouter_provider_config() == {
        "order": ["a", "b"],
        "allow_fallbacks": True,
    }


def test_openrouter_provider_config_invalid_json():
    """Test invalid JSON handling."""
    config = EmbedConfig(
        openrouter_api_key="ok",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_embeddings_model="openai/text-embedding-3-small",
        openrouter_referer=None,
        openrouter_title=None,
        openrouter_provider_json="{invalid}",
        local_embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
        embed_provider="auto",
    )
    with pytest.raises(ValueError, match="OPENROUTER_EMBED_PROVIDER_JSON"):
        config.openrouter_provider_config()


def test_openrouter_provider_config_requires_object():
    """Test JSON config must be an object."""
    config = EmbedConfig(
        openrouter_api_key="ok",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_embeddings_model="openai/text-embedding-3-small",
        openrouter_referer=None,
        openrouter_title=None,
        openrouter_provider_json="[]",
        local_embeddings_model="sentence-transformers/all-MiniLM-L6-v2",
        embed_provider="auto",
    )
    with pytest.raises(ValueError, match="must be a JSON object"):
        config.openrouter_provider_config()


def test_load_config_from_env(monkeypatch):
    """Test loading config from environment."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter")
    config = load_config()
    assert config.openrouter_api_key == "test-openrouter"
