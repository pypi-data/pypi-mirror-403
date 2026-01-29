"""Tests for provider factory and vector store."""

import pytest

from chromaroute import EmbedConfig, VectorStore, build_embedding_function


class DummyEmbedding:
    """Mock embedding function for testing."""
    pass


def _config(**overrides) -> EmbedConfig:
    """Create a test configuration."""
    data = {
        "openrouter_api_key": "ok",
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "openrouter_embeddings_model": "openai/text-embedding-3-small",
        "openrouter_referer": None,
        "openrouter_title": None,
        "openrouter_provider_json": None,
        "local_embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embed_provider": "auto",
    }
    data.update(overrides)
    return EmbedConfig(**data)


def test_build_embedding_function_openrouter_requires_key():
    """Test OpenRouter requires API key."""
    config = _config(openrouter_api_key=None)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        build_embedding_function(config, embed_provider="openrouter")


def test_build_embedding_function_openrouter(monkeypatch):
    """Test OpenRouter embedding function creation."""
    config = _config(openrouter_api_key="ok")
    import chromaroute.embedding as embedding

    # Patch the registry entry directly since _PROVIDERS is used for dispatch
    monkeypatch.setitem(
        embedding._PROVIDERS,
        "openrouter",
        lambda cfg, model: DummyEmbedding(),
    )
    ef = build_embedding_function(config, embed_provider="openrouter")
    assert isinstance(ef, DummyEmbedding)


def test_build_embedding_function_local(monkeypatch):
    """Test local embedding function creation."""
    from chromadb.utils import embedding_functions

    config = _config(openrouter_api_key=None)
    monkeypatch.setattr(
        embedding_functions,
        "SentenceTransformerEmbeddingFunction",
        lambda model_name: DummyEmbedding(),
    )
    ef = build_embedding_function(config, embed_provider="local")
    assert isinstance(ef, DummyEmbedding)


def test_build_embedding_function_unknown_provider():
    """Test unknown provider raises ValueError."""
    config = _config()
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        build_embedding_function(config, embed_provider="unknown")


def test_vector_store_add_documents_batches():
    """Test document batching."""
    calls = []

    class FakeCollection:
        def add(self, documents, ids):
            calls.append((documents, ids))

        def count(self):
            return len(calls)

    class FakeClient:
        def get_collection(self, name, embedding_function):
            raise ValueError("not found")

        def create_collection(self, name, embedding_function, metadata):
            return FakeCollection()

    store = VectorStore.__new__(VectorStore)
    store.collection_name = "test"
    store.client = FakeClient()
    store.embedding_function = DummyEmbedding()
    store.collection = store._get_or_create_collection()

    store.add_documents(["a", "b", "c"], ids=None, batch_size=2)
    assert calls == [
        (["a", "b"], ["doc1", "doc2"]),
        (["c"], ["doc3"]),
    ]


def test_vector_store_query():
    """Test query passthrough."""
    class FakeCollection:
        def query(self, query_texts, n_results, include):
            return {"documents": [["result"]], "distances": [[0.1]]}

    store = VectorStore.__new__(VectorStore)
    store.collection = FakeCollection()
    results = store.query(query_texts=["test"], n_results=1)
    assert results["documents"][0][0] == "result"


def test_vector_store_with_embedding_function(monkeypatch):
    """Test VectorStore with provided embedding function."""
    class FakeClient:
        def get_collection(self, name, embedding_function):
            return "collection"

    import types

    monkeypatch.setattr("chromaroute.vector_store.load_config", lambda: None)
    fake_chromadb = types.SimpleNamespace(Client=lambda: FakeClient())
    monkeypatch.setitem(__import__("sys").modules, "chromadb", fake_chromadb)

    store = VectorStore(
        collection_name="test",
        embedding_function=DummyEmbedding(),
    )
    assert store.collection == "collection"


def test_vector_store_count_and_delete_collection():
    """Test count passthrough and delete_collection call."""
    class FakeCollection:
        def count(self):
            return 3

    class FakeClient:
        def __init__(self):
            self.deleted = None

        def delete_collection(self, name):
            self.deleted = name

    store = VectorStore.__new__(VectorStore)
    store.collection_name = "to-delete"
    store.collection = FakeCollection()
    store.client = FakeClient()

    assert store.count() == 3
    store.delete_collection()
    assert store.client.deleted == "to-delete"
