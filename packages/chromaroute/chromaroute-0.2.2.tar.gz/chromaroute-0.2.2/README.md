# chromaroute

[![CI](https://github.com/seanbrar/chromaroute/actions/workflows/ci.yml/badge.svg)](https://github.com/seanbrar/chromaroute/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Provider-agnostic embedding functions for ChromaDB with automatic fallback support.

## Features

- **ChromaDB-native interface**: Drop-in `EmbeddingFunction` implementations
- **Provider fallback chain**: OpenRouter → Local (SentenceTransformers)
- **OpenRouter integration**: Full support for OpenRouter's embedding API with provider routing
- **Production-ready**: Comprehensive error handling, configurable timeouts, actionable error messages

## Installation

```bash
pip install chromaroute

# With local embeddings (SentenceTransformers)
pip install chromaroute[local]

```

## Quick Start

```python
from chromaroute import build_embedding_function, load_config

# Auto-detect available providers
config = load_config()
embed_fn = build_embedding_function(config)

# Or rely on environment auto-detection
embed_fn = build_embedding_function()

# Use with ChromaDB
import chromadb
client = chromadb.Client()
collection = client.create_collection(
    name="my_collection",
    embedding_function=embed_fn,
)
collection.add(documents=["Hello world"], ids=["doc1"])
```

## Configuration

Set environment variables:

```bash
# OpenRouter (primary)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_EMBEDDINGS_MODEL=openai/text-embedding-3-small
OPENROUTER_EMBED_PROVIDER_JSON='{"order":["openai","mistral"],"allow_fallbacks":true}'

# Local fallback uses sentence-transformers/all-MiniLM-L6-v2 by default
```

## Direct OpenRouter Usage

```python
from chromaroute import OpenRouterEmbeddingFunction

embed_fn = OpenRouterEmbeddingFunction(
    model="openai/text-embedding-3-small",
    api_key="sk-or-...",
)

# Use with ChromaDB
embeddings = embed_fn(["text to embed"])
# Returns list[list[float]] with one embedding per input text.
```

## VectorStore (Optional)

For simplified collection management with automatic batching:

```python
from chromaroute import VectorStore

store = VectorStore("my_docs", persist_path="./chroma_db")
store.add_documents(["Hello world", "Goodbye world"])
results = store.query(["greeting"], n_results=1)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | OpenRouter API key (enables OpenRouter provider) |
| `OPENROUTER_EMBEDDINGS_MODEL` | `openai/text-embedding-3-small` | Model for OpenRouter embeddings |
| `OPENROUTER_EMBED_PROVIDER_JSON` | — | Provider routing config (JSON) |
| `LOCAL_EMBEDDINGS_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model for local embeddings |
| `EMBED_PROVIDER` | `auto` | Force provider: `auto`, `openrouter`, or `local` |

## License

[MIT](LICENSE)
