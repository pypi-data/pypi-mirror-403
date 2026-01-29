"""ChromaDB vector store wrapper with batched operations.

This module provides a high-level wrapper around ChromaDB collections
with support for persistence, batched document ingestion, and automatic
embedding function configuration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from chromaroute.config import EmbedConfig, load_config
from chromaroute.embedding import build_embedding_function

if TYPE_CHECKING:
    from chromadb.api.types import EmbeddingFunction

logger = logging.getLogger(__name__)


class VectorStore:
    """High-level wrapper for ChromaDB vector store operations.

    This class provides a simplified interface for common vector store
    operations including document ingestion, querying, and collection
    management.

    Args:
        collection_name: Name of the ChromaDB collection.
        persist_path: Optional path for persistent storage.
        embedding_model: Optional model name override.
        embed_provider: Optional provider override.
        embedding_function: Optional pre-configured embedding function.
        client: Optional pre-configured ChromaDB client.

    Example:
        >>> from chromaroute import VectorStore
        >>> store = VectorStore("my_docs", persist_path="./chroma_db")
        >>> store.add_documents(["Hello world", "Goodbye world"])
        >>> results = store.query(["greeting"], n_results=1)
    """

    def __init__(
        self,
        collection_name: str,
        persist_path: str | None = None,
        embedding_model: str | None = None,
        embed_provider: str | None = None,
        embedding_function: EmbeddingFunction[Any] | None = None,
        client: Any | None = None,
        config: EmbedConfig | None = None,
    ) -> None:
        self.collection_name = collection_name

        import chromadb

        # Initialize ChromaDB client
        self.client = client or (
            chromadb.PersistentClient(path=persist_path)
            if persist_path
            else chromadb.Client()
        )

        # Configure embedding function
        if embedding_function is not None:
            self.embedding_function = embedding_function
        else:
            cfg = config or load_config()
            self.embedding_function = build_embedding_function(
                config=cfg,
                embedding_model=embedding_model,
                embed_provider=embed_provider,
            )

        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> Any:
        """Get an existing collection or create a new one.

        Returns:
            ChromaDB collection instance.
        """
        from chromadb.errors import NotFoundError

        try:
            collection = self.client.get_collection(
                self.collection_name,
                embedding_function=self.embedding_function,
            )
            logger.info("Loaded existing collection: %s", self.collection_name)
        except (ValueError, NotFoundError):
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Created new collection: %s", self.collection_name)
        return collection

    def add_documents(
        self,
        documents: list[str],
        ids: list[str] | None = None,
        batch_size: int = 100,
    ) -> None:
        """Add documents to the collection with batching.

        Args:
            documents: List of document strings to add.
            ids: Optional list of unique IDs. If not provided, sequential
                IDs will be generated (doc1, doc2, ...).
            batch_size: Number of documents per batch to avoid API limits.
        """
        if ids is None:
            ids = [f"doc{i+1}" for i in range(len(documents))]

        total = len(documents)
        for i in range(0, total, batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            self.collection.add(documents=batch_docs, ids=batch_ids)

        logger.info("Added %s documents to collection '%s'", total, self.collection_name)

    def query(
        self,
        query_texts: list[str],
        n_results: int = 3,
    ) -> dict[str, Any]:
        """Query the collection for similar documents.

        Args:
            query_texts: List of query strings.
            n_results: Number of results to return per query.

        Returns:
            Query results containing documents and their distances.
        """
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            include=["documents", "distances"],
        )
        return cast("dict[str, Any]", results)

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return cast("int", self.collection.count())

    def delete_collection(self) -> None:
        """Delete the collection from the database."""
        self.client.delete_collection(self.collection_name)
        logger.info("Deleted collection: %s", self.collection_name)
