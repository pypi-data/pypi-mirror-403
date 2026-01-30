from __future__ import annotations

from typing import Any, AsyncIterator

from ..base import CompletionConfig, LLMBase


class QwenChat(LLMBase):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package required. Install it to use QwenChat.") from exc
        base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        resp = await self._client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens or 1024,
            temperature=config.temperature,
        )
        return resp.choices[0].message.content or ""

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        return await self.chat([{"role": "user", "content": prompt}], config)

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens or 1024,
            temperature=config.temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def list_models(self) -> list[str]:
        return [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-long",
            "qwen-math-plus",
            "qwen-coder-turbo",
        ]
