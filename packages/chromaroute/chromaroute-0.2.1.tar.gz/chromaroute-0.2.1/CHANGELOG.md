# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-24

### Changed
- Migrated from Poetry to uv/Hatchling build system
- Expanded ruff lint rules for stricter code quality

### Added
- PEP 561 `py.typed` marker for typed package compliance
- GitHub Actions CI workflow for automated testing
- Makefile with common development tasks
- Project-local `.venv` virtual environment support

## [0.1.0] - 2026-01-24

### Added
- Initial release extracted from ContextRAG project
- `OpenRouterEmbeddingFunction`: ChromaDB-compatible embedding function for OpenRouter API
- `build_embedding_function`: Factory with provider fallback (OpenRouter → Local)
- `VectorStore`: High-level ChromaDB wrapper with batched operations
- `EmbedConfig` and `load_config`: Configuration management from environment variables
