"""Tests for OpenRouter embedding function."""

import pytest
import requests

from chromaroute import OpenRouterEmbeddingFunction


def test_openrouter_embedding_success(monkeypatch):
    """Test successful embedding generation."""
    def fake_post(url, headers, json, timeout):
        class Response:
            status_code = 200

            @staticmethod
            def json():
                return {
                    "data": [
                        {"embedding": [0.1, 0.2], "index": 0},
                        {"embedding": [0.3, 0.4], "index": 1},
                    ]
                }

        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    result = embed_fn(["a", "b"])
    assert len(result) == 2
    assert pytest.approx(result[0]) == [0.1, 0.2]
    assert pytest.approx(result[1]) == [0.3, 0.4]


def test_openrouter_embedding_http_error(monkeypatch):
    """Test HTTP error handling."""
    def fake_post(url, headers, json, timeout):
        class Response:
            status_code = 404
            text = "not found"

        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="HTTP 404"):
        embed_fn(["a"])


def test_openrouter_embedding_missing_data(monkeypatch):
    """Test handling of empty response data."""
    def fake_post(url, headers, json, timeout):
        class Response:
            status_code = 200

            @staticmethod
            def json():
                return {"data": []}

        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="No embedding data received"):
        embed_fn(["a"])


def test_openrouter_embedding_request_exception(monkeypatch):
    """Test network error handling."""
    def fake_post(url, headers, json, timeout):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="OpenRouter embeddings request failed"):
        embed_fn(["a"])


def test_openrouter_embedding_missing_embedding(monkeypatch):
    """Test handling of malformed response."""
    def fake_post(url, headers, json, timeout):
        class Response:
            status_code = 200

            @staticmethod
            def json():
                return {"data": [{"index": 0}]}

        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="Missing embedding"):
        embed_fn(["a"])


def test_openrouter_embedding_http_error_hints(monkeypatch):
    """Test HTTP error codes provide helpful hints."""
    def make_response(status_code):
        def fake_post(url, headers, json, timeout):
            class Response:
                text = "error"
            Response.status_code = status_code
            return Response()
        return fake_post

    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )

    monkeypatch.setattr("requests.post", make_response(401))
    with pytest.raises(ValueError, match="Verify OPENROUTER_API_KEY"):
        embed_fn(["a"])

    monkeypatch.setattr("requests.post", make_response(402))
    with pytest.raises(ValueError, match="Check OpenRouter credits"):
        embed_fn(["a"])

    monkeypatch.setattr("requests.post", make_response(429))
    with pytest.raises(ValueError, match="Rate limit exceeded"):
        embed_fn(["a"])


def test_openrouter_embedding_build_from_config(monkeypatch):
    """Test building from configuration dict."""
    config = {
        "api_key_env_var": "OPENROUTER_API_KEY",
        "model": "openai/text-embedding-3-small",
        "base_url": "https://openrouter.ai/api/v1",
        "referer": "https://example.com",
        "title": "test",
        "provider": {"order": ["x"]},
        "timeout_s": 30,
    }
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    embed_fn = OpenRouterEmbeddingFunction.build_from_config(config)
    assert embed_fn.model == "openai/text-embedding-3-small"
    assert embed_fn.base_url == "https://openrouter.ai/api/v1"


def test_openrouter_embedding_config_helpers():
    """Test configuration helper methods."""
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    assert embed_fn.name() == "openrouter"
    config = embed_fn.get_config()
    assert config["model"] == "openai/text-embedding-3-small"
    assert embed_fn.default_space() == "cosine"
    assert "cosine" in embed_fn.supported_spaces()


def test_openrouter_embedding_requires_api_key(monkeypatch):
    """Test API key requirement."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterEmbeddingFunction(model="openai/text-embedding-3-small", api_key=None)


def test_openrouter_embedding_empty_input():
    """Test empty input validation."""
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="non-empty"):
        embed_fn([])


def test_openrouter_embedding_not_legacy(monkeypatch):
    """Ensure embedding function is not marked as legacy by ChromaDB.

    ChromaDB requires get_config() and build_from_config() for persistence.
    Without these methods, is_legacy() returns True and collection configs
    cannot be serialized/restored. This test guards against accidental removal.
    """
    # is_legacy() calls build_from_config(get_config()), which reads from env
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    # is_legacy() checks: name(), get_config(), build_from_config(get_config())
    assert not embed_fn.is_legacy(), (
        "OpenRouterEmbeddingFunction must not be legacy. "
        "Ensure name(), get_config(), and build_from_config() are implemented."
    )


def test_openrouter_embedding_config_roundtrip(monkeypatch):
    """Test that config can be serialized and restored (ChromaDB requirement).

    This verifies the full persistence cycle that ChromaDB uses:
    1. get_config() serializes the embedding function
    2. build_from_config() restores it from the serialized config
    """
    # build_from_config reads API key from environment
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    original = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
        base_url="https://custom.example.com/v1",
        referer="https://myapp.com",
        title="MyApp",
        provider={"order": ["openai"]},
        timeout_s=120,
    )

    config = original.get_config()
    restored = OpenRouterEmbeddingFunction.build_from_config(config)

    assert restored.model == original.model
    assert restored.base_url == original.base_url
    assert restored.referer == original.referer
    assert restored.title == original.title
    assert restored.provider == original.provider
    assert restored.timeout_s == original.timeout_s


def test_openrouter_embedding_retry_on_rate_limit(monkeypatch):
    """Test retry behavior for retriable HTTP responses."""
    calls = []

    def fake_post(url, headers, json, timeout):
        calls.append(json["input"])

        class Response:
            text = "rate limited"

        if len(calls) == 1:
            Response.status_code = 429
            return Response()

        Response.status_code = 200

        def json_response():
            return {"data": [{"embedding": [0.0], "index": 0}]}

        Response.json = staticmethod(json_response)
        return Response()

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("time.sleep", fake_sleep)

    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    result = embed_fn(["retry"])

    assert result == [[0.0]]
    assert len(calls) == 2
    assert sleep_calls


def test_openrouter_embedding_build_from_config_missing_fields():
    """Test required fields for build_from_config."""
    with pytest.raises(ValueError, match="api_key_env_var and model"):
        OpenRouterEmbeddingFunction.build_from_config({"model": "x"})
    with pytest.raises(ValueError, match="api_key_env_var and model"):
        OpenRouterEmbeddingFunction.build_from_config({"api_key_env_var": "OPENROUTER_API_KEY"})


def test_openrouter_embedding_error_detail_falls_back_to_text(monkeypatch):
    """Test error detail uses response text when JSON is invalid."""
    def fake_post(url, headers, json, timeout):
        class Response:
            status_code = 500
            text = "server down"

            @staticmethod
            def json():
                raise ValueError("invalid")

        return Response()

    monkeypatch.setattr("requests.post", fake_post)
    embed_fn = OpenRouterEmbeddingFunction(
        model="openai/text-embedding-3-small",
        api_key="test-key",
    )
    with pytest.raises(ValueError, match="server down"):
        embed_fn(["a"])
