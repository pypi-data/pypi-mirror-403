# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-01-25

### Added

#### Multi-Modal Architecture
- **Image Generation Support**: Added `ImageBase` abstract class for image generation providers
- **Video Generation Support**: Added `VideoBase` abstract class for video generation providers (foundation ready)
- **Vector Embeddings Support**: Added `EmbeddingBase` abstract class for embedding providers
- New configuration classes: `ImageConfig`, `VideoConfig`, `EmbeddingConfig`
- New response classes: `ImageResponse`, `VideoResponse`

#### New LLM Providers (3)
- **MiniMax (海螺AI)**: Chinese LLM provider with abab series models
  - Special authentication: Requires both `api_key` and `group_id`
  - Models: abab6.5-chat, abab6.5s-chat, abab5.5-chat, abab5.5s-chat
- **ByteDance Doubao (豆包)**: Enterprise Chinese LLM
  - OpenAI-compatible API
  - Models: doubao-pro-4k/32k/128k, doubao-lite-4k/32k/128k
- **NVIDIA NIM**: GPU-accelerated enterprise inference
  - Enterprise-grade performance
  - Models: Llama 3.1 Nemotron, Meta Llama, Mixtral series

#### New Image Generation Providers (1)
- **OpenAI DALL-E**: Text-to-image generation
  - Models: dall-e-3 (HD quality), dall-e-2
  - Operations: generate(), edit(), variations()
  - Configurable size, quality, and style

#### New Embedding Providers (1)
- **OpenAI Embeddings**: Vector embeddings for semantic search
  - Models: text-embedding-3-large, text-embedding-3-small, text-embedding-ada-002
  - Batch and single query support
  - Configurable dimensions

#### Builder Functions
- `build_image_provider()`: Factory function for image generation providers
- `build_embedding_provider()`: Factory function for embedding providers
- Updated `build_provider()` with support for MiniMax's special authentication

#### Provider Registries
- Separated `LLM_PROVIDER_CLASSES` for LLM providers (16 total)
- Added `IMAGE_PROVIDER_CLASSES` for image providers (1 total)
- Added `EMBEDDING_PROVIDER_CLASSES` for embedding providers (1 total)
- Kept `PROVIDER_CLASSES` for backward compatibility

### Changed
- Updated package description to "multi-modal AI provider router"
- Enhanced keywords with: image-generation, embeddings, dall-e, multi-modal, minimax, bytedance, nvidia
- Provider count increased from 13 to 16 LLM providers

### Fixed
- Fixed `list_models()` in OpenAI adapter to properly raise `RuntimeError` when API key is missing
- Updated error message in `build_provider()` to "Unsupported LLM provider" for clarity
- Fixed test compatibility with separated provider registries

### Documentation
- Comprehensive updates to README.md with multi-modal examples
- Updated PROVIDERS.md reference guide with all new providers
- Added provider-specific authentication notes for MiniMax and ByteDance
- Updated provider comparison tables
- Added Quick Start examples for image generation and embeddings

### Tests
- Added unit tests for all 3 new LLM providers
- Added unit tests for image generation provider
- Added unit tests for embedding provider
- Test coverage: 42% (baseline established)

## [0.1.0] - 2026-01-25

### Added
- Initial release of weav-provider-router
- Support for OpenAI provider
- Support for Anthropic provider
- Support for Google provider
- Support for Ollama provider
- Support for DeepSeek provider
- Support for Qwen provider
- Support for Zhipu provider
- Unified chat and completion API
- Async/await support
- Streaming response support
- Model listing functionality
- Comprehensive test suite
- Full documentation

### Features
- `chat()` and `chat_async()` for synchronous and asynchronous chat
- `complete()` and `complete_async()` for text completion
- `list_models()` for retrieving available models
- `build_provider()` for direct provider instantiation
- Flexible configuration with `CompletionConfig`
- Support for custom API endpoints via `base_url`
- Provider-specific extra parameters support

### Developer Experience
- Type hints for better IDE support
- Pytest-based test suite with unit and integration tests
- Black code formatting
- Ruff linting
- MyPy type checking
- Comprehensive documentation and examples

[Unreleased]: https://github.com/zeturn/weav-provider-router/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/zeturn/weav-provider-router/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zeturn/weav-provider-router/releases/tag/v0.1.0
