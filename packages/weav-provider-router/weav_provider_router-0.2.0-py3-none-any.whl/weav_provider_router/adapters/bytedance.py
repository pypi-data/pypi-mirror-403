from __future__ import annotations

from typing import Any, AsyncIterator

from weav_provider_router.base import CompletionConfig, LLMBase


class ByteDanceChat(LLMBase):
    """ByteDance Doubao (豆包) chat adapter using OpenAI-compatible API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package is required for ByteDanceChat. Install it to use this provider.") from exc
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://ark.cn-beijing.volces.com/api/v3"
        )
        self._base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self._api_key = api_key

    def _build_chat_kwargs(self, messages: list[dict[str, Any]], config: CompletionConfig, stream: bool = False) -> dict[str, Any]:
        """Build kwargs for ByteDance chat completion."""
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
        }

        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.max_tokens:
            kwargs["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.stop:
            kwargs["stop"] = config.stop
        if stream:
            kwargs["stream"] = True
        if config.extra:
            kwargs.update(config.extra)

        return kwargs

    async def chat(self, messages: list[dict[str, Any]], config: CompletionConfig) -> str:
        """Send a chat request to ByteDance Doubao."""
        kwargs = self._build_chat_kwargs(messages, config)
        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        """Complete a prompt using ByteDance Doubao."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def stream(self, messages: list[dict[str, Any]], config: CompletionConfig) -> AsyncIterator[str]:
        """Stream chat responses from ByteDance Doubao."""
        kwargs = self._build_chat_kwargs(messages, config, stream=True)
        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def list_models(self) -> list[str]:
        """List available ByteDance Doubao models."""
        return [
            "doubao-pro-4k",
            "doubao-pro-32k",
            "doubao-pro-128k",
            "doubao-lite-4k",
            "doubao-lite-32k",
            "doubao-lite-128k",
        ]
