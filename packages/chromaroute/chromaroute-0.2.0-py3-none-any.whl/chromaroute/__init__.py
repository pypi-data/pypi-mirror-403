"""chromaroute: Provider-agnostic embedding functions for ChromaDB."""

from chromaroute.config import EmbedConfig, load_config
from chromaroute.embedding import OpenRouterEmbeddingFunction, build_embedding_function
from chromaroute.vector_store import VectorStore

__version__ = "0.2.0"

__all__ = [
    "OpenRouterEmbeddingFunction",
    "build_embedding_function",
    "EmbedConfig",
    "load_config",
    "VectorStore",
    "__version__",
]

