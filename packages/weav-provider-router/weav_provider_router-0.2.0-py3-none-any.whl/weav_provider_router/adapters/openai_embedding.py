from __future__ import annotations

from typing import Any

from weav_provider_router.base import EmbeddingBase, EmbeddingConfig


class OpenAIEmbedding(EmbeddingBase):
    """OpenAI text embeddings adapter."""

    def __init__(self, api_key: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package is required for OpenAIEmbedding. Install it to use this provider.") from exc
        
        self._client = AsyncOpenAI(api_key=api_key)
        self._api_key = api_key

    async def embed(self, texts: list[str], config: EmbeddingConfig) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        kwargs: dict[str, Any] = {
            "model": config.model,
            "input": texts,
        }
        
        if config.dimensions:
            kwargs["dimensions"] = config.dimensions
        if config.encoding_format:
            kwargs["encoding_format"] = config.encoding_format
        if config.extra:
            kwargs.update(config.extra)
        
        response = await self._client.embeddings.create(**kwargs)
        
        # Sort by index to ensure correct order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    async def embed_query(self, text: str, config: EmbeddingConfig) -> list[float]:
        """Generate embedding for a single query text."""
        results = await self.embed([text], config)
        return results[0]

    def list_models(self) -> list[str]:
        """List available embedding models."""
        return [
            "text-embedding-3-large",
            "text-embedding-3-small",
            "text-embedding-ada-002",
        ]
