"""Embedding functions and provider factory for ChromaDB.

This module provides ChromaDB-compatible embedding functions and a factory
for creating them based on configuration. Supports OpenRouter API and local
SentenceTransformers with automatic fallback.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, cast

import requests
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils.embedding_functions import register_embedding_function
from requests import exceptions as requests_exceptions

if TYPE_CHECKING:
    from chromaroute.config import EmbedConfig

# HTTP status code hints for actionable error messages
_HTTP_ERROR_HINTS: dict[int, str] = {
    401: " Verify OPENROUTER_API_KEY.",
    402: " Check OpenRouter credits.",
    404: " Verify OPENROUTER_EMBEDDINGS_MODEL.",
    429: " Rate limit exceeded; retry later.",
    529: " Provider overloaded; consider allow_fallbacks.",
}

_RETRY_BACKOFF_S = 0.5


def _should_retry(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599


def _response_detail(response: requests.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = None
    if payload not in (None, "", {}, []):
        return str(payload)
    return response.text


@register_embedding_function
class OpenRouterEmbeddingFunction(EmbeddingFunction[Any]):
    """ChromaDB-compatible embedding function using OpenRouter API.

    This class implements the ChromaDB EmbeddingFunction interface, allowing
    it to be used as a drop-in replacement for other embedding functions.

    Args:
        model: The model identifier (e.g., "openai/text-embedding-3-small").
        api_key: OpenRouter API key. If not provided, reads from environment.
        base_url: OpenRouter API base URL.
        referer: Optional HTTP-Referer header for OpenRouter.
        title: Optional X-Title header for OpenRouter.
        provider: Optional provider routing configuration dict.
        timeout_s: Request timeout in seconds.
        api_key_env_var: Environment variable name for API key.
        require_api_key: Whether to raise if no API key is found.

    Example:
        >>> embed_fn = OpenRouterEmbeddingFunction(
        ...     model="openai/text-embedding-3-small",
        ...     api_key="sk-or-...",
        ... )
        >>> embeddings = embed_fn(["Hello world"])
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        referer: str | None = None,
        title: str | None = None,
        provider: dict[str, Any] | None = None,
        timeout_s: int = 60,
        api_key_env_var: str = "OPENROUTER_API_KEY",
        require_api_key: bool = True,
    ) -> None:
        self.api_key_env_var = api_key_env_var
        self.api_key = api_key or os.getenv(self.api_key_env_var)
        if require_api_key and not self.api_key:
            raise ValueError(
                f"The {self.api_key_env_var} environment variable is not set."
            )
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.referer = referer
        self.title = title
        self.provider = provider
        self.timeout_s = timeout_s

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for the input documents.

        Args:
            input: List of text documents to embed.

        Returns:
            List of embedding vectors.

        Raises:
            ValueError: If the API request fails or returns invalid data.
        """
        inputs = list(input)
        if not inputs:
            raise ValueError("Input must be a non-empty list of documents.")

        payload: dict[str, Any] = {
            "model": self.model,
            "input": inputs,
            "encoding_format": "float",
        }
        if self.provider:
            payload["provider"] = self.provider

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-Title"] = self.title

        url = f"{self.base_url}/embeddings"
        response: requests.Response | None = None
        for attempt in range(2):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_s,
                )
            except requests_exceptions.RequestException as exc:
                message = (
                    "OpenRouter embeddings request failed. "
                    f"URL: {url}. "
                    "Check network/DNS connectivity and OPENROUTER_BASE_URL."
                )
                raise ValueError(message) from exc

            if response.status_code == 200:
                break
            if _should_retry(response.status_code) and attempt == 0:
                time.sleep(_RETRY_BACKOFF_S)
                continue
            break

        if response is None:
            raise ValueError("OpenRouter embeddings request failed with no response.")

        if response.status_code != 200:
            hint = _HTTP_ERROR_HINTS.get(response.status_code, "")
            detail = _response_detail(response)
            detail_text = f" {detail}" if detail else ""
            raise ValueError(
                f"OpenRouter embeddings failed: HTTP {response.status_code}"
                f"{detail_text}.{hint}"
            )

        data = response.json()
        if "data" not in data or not data["data"]:
            raise ValueError(f"No embedding data received: {data}")

        embeddings: list[list[float]] = []
        for item in data["data"]:
            embedding = item.get("embedding")
            if embedding is None:
                raise ValueError(f"Missing embedding in response: {item}")
            embeddings.append(embedding)

        return cast("Embeddings", embeddings)

    @staticmethod
    def name() -> str:
        """Return the registered name of this embedding function."""
        return "openrouter"

    # NOTE: build_from_config and get_config are required by ChromaDB for
    # persistence. Without them, is_legacy() returns True and collection
    # configs cannot be serialized/restored. Do not remove these methods.

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> OpenRouterEmbeddingFunction:
        """Build an instance from a configuration dictionary.

        Required by ChromaDB for restoring embedding functions from persisted
        collection configurations.

        Args:
            config: Configuration dictionary with keys matching __init__ params.

        Returns:
            Configured OpenRouterEmbeddingFunction instance.
        """
        api_key_env_var = config.get("api_key_env_var")
        model = config.get("model")
        if api_key_env_var is None or model is None:
            raise ValueError("api_key_env_var and model are required in config.")
        return OpenRouterEmbeddingFunction(
            api_key_env_var=api_key_env_var,
            model=model,
            base_url=config.get("base_url", "https://openrouter.ai/api/v1"),
            referer=config.get("referer"),
            title=config.get("title"),
            provider=config.get("provider"),
            timeout_s=config.get("timeout_s", 60),
            require_api_key=True,
        )

    def get_config(self) -> dict[str, Any]:
        """Return the configuration of this embedding function.

        Required by ChromaDB for persisting collection configurations.
        """
        return {
            "api_key_env_var": self.api_key_env_var,
            "model": self.model,
            "base_url": self.base_url,
            "referer": self.referer,
            "title": self.title,
            "provider": self.provider,
            "timeout_s": self.timeout_s,
        }

    def default_space(self) -> Literal["cosine", "l2", "ip"]:
        """Return the default distance space for this embedding function."""
        return "cosine"

    def supported_spaces(self) -> list[Literal["cosine", "l2", "ip"]]:
        """Return the list of supported distance spaces."""
        return ["cosine", "l2", "ip"]


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

# Type alias for provider factory functions
ProviderFactory = Callable[["EmbedConfig", str], EmbeddingFunction[Any]]


def _create_openrouter(config: EmbedConfig, model: str) -> EmbeddingFunction[Any]:
    """Create OpenRouter embedding function."""
    if not config.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is required for OpenRouter embeddings.")

    return OpenRouterEmbeddingFunction(
        api_key=config.openrouter_api_key,
        model=model,
        base_url=config.openrouter_base_url,
        referer=config.openrouter_referer,
        title=config.openrouter_title,
        provider=config.openrouter_provider_config(),
    )


def _create_local(_config: EmbedConfig, model: str) -> EmbeddingFunction[Any]:
    """Create local SentenceTransformers embedding function."""
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    return SentenceTransformerEmbeddingFunction(model_name=model)


# Provider registry: maps provider names to factory functions
_PROVIDERS: dict[str, ProviderFactory] = {
    "openrouter": _create_openrouter,
    "local": _create_local,
}


def build_embedding_function(
    config: EmbedConfig | None = None,
    embedding_model: str | None = None,
    embed_provider: str | None = None,
) -> EmbeddingFunction[Any]:
    """Build a ChromaDB-compatible embedding function.

    This factory function creates the appropriate embedding function based
    on the resolved provider. It supports automatic fallback from OpenRouter
    to local embeddings when no API key is configured.

    Args:
        config: Embedding configuration instance (defaults to load_config()).
        embedding_model: Optional model name override.
        embed_provider: Optional provider override ("openrouter", "local").

    Returns:
        A ChromaDB-compatible EmbeddingFunction instance.

    Raises:
        ValueError: If provider is unknown or required config is missing.

    Example:
        >>> from chromaroute import load_config, build_embedding_function
        >>> config = load_config()
        >>> embed_fn = build_embedding_function(config)
    """
    from chromaroute.config import load_config

    cfg = config or load_config()
    provider_name = cfg.resolve_provider(embed_provider)
    model = cfg.resolve_model(provider=provider_name, explicit_model=embedding_model)

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown embedding provider: {provider_name!r}. "
            f"Available: {', '.join(_PROVIDERS)}"
        )

    return _PROVIDERS[provider_name](cfg, model)
