"""Configuration for chromaroute embedding providers.

This module provides a configuration dataclass and loader for managing
embedding provider settings across OpenRouter and local providers.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


def _env(key: str, default: str | None = None) -> str | None:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


@dataclass(frozen=True)
class EmbedConfig:
    """Configuration for embedding providers.

    This dataclass holds all configuration needed to instantiate embedding
    functions for different providers. It supports automatic provider
    detection based on available API keys.

    Attributes:
        openrouter_api_key: OpenRouter API key.
        openrouter_base_url: OpenRouter API base URL.
        openrouter_embeddings_model: Model name for OpenRouter embeddings.
        openrouter_referer: Optional HTTP-Referer for OpenRouter.
        openrouter_title: Optional X-Title for OpenRouter.
        openrouter_provider_json: JSON string for provider routing config.
        local_embeddings_model: Model name for local embeddings.
        embed_provider: Explicit provider selection ("auto", "openrouter", "local").
    """

    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_embeddings_model: str
    openrouter_referer: str | None
    openrouter_title: str | None
    openrouter_provider_json: str | None
    local_embeddings_model: str
    embed_provider: str

    def resolve_provider(self, explicit_provider: str | None = None) -> str:
        """Resolve which embedding provider to use.

        Provider resolution order when set to "auto":
        1. OpenRouter (if OPENROUTER_API_KEY is set)
        2. Local (always available)

        Args:
            explicit_provider: Override the configured provider.

        Returns:
            The resolved provider name ("openrouter" or "local").
        """
        provider = (explicit_provider or self.embed_provider or "auto").lower()
        if provider == "auto":
            if self.openrouter_api_key:
                return "openrouter"
            return "local"
        return provider

    def resolve_model(
        self,
        provider: str | None = None,
        explicit_model: str | None = None,
    ) -> str:
        """Resolve which embedding model to use.

        Args:
            provider: The provider to get the model for.
            explicit_model: Override the configured model.

        Returns:
            The model name for the specified provider.
        """
        if explicit_model:
            return explicit_model
        resolved_provider = (provider or self.resolve_provider()).lower()
        if resolved_provider == "openrouter":
            return self.openrouter_embeddings_model
        if resolved_provider == "local":
            return self.local_embeddings_model
        return "default"

    def openrouter_provider_config(self) -> dict[str, Any] | None:
        """Build OpenRouter provider routing configuration.

        Returns:
            Provider config dict with "order" and/or "allow_fallbacks",
            or None if no routing config is set.

        Raises:
            ValueError: If openrouter_provider_json is invalid JSON.
        """
        if not self.openrouter_provider_json:
            return None

        try:
            payload = json.loads(self.openrouter_provider_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "OPENROUTER_EMBED_PROVIDER_JSON must be valid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError("OPENROUTER_EMBED_PROVIDER_JSON must be a JSON object.")

        return payload


def load_config() -> EmbedConfig:
    """Load embedding configuration from environment variables.

    This function loads .env files and creates an EmbedConfig instance
    with values from environment variables or sensible defaults.

    Returns:
        Configured EmbedConfig instance.
    """
    load_dotenv()
    return EmbedConfig(
        openrouter_api_key=_env("OPENROUTER_API_KEY"),
        openrouter_base_url=_env(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ) or "https://openrouter.ai/api/v1",
        openrouter_embeddings_model=_env(
            "OPENROUTER_EMBEDDINGS_MODEL", "openai/text-embedding-3-small"
        ) or "openai/text-embedding-3-small",
        openrouter_referer=_env("OPENROUTER_REFERER"),
        openrouter_title=_env("OPENROUTER_TITLE"),
        openrouter_provider_json=_env("OPENROUTER_EMBED_PROVIDER_JSON"),
        local_embeddings_model=_env(
            "LOCAL_EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ) or "sentence-transformers/all-MiniLM-L6-v2",
        embed_provider=_env("EMBED_PROVIDER", "auto") or "auto",
    )
