from __future__ import annotations

import json
from typing import Any, AsyncIterator
from urllib import request as urlrequest

from weav_provider_router.base import CompletionConfig, LLMBase


class OpenAIChat(LLMBase):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package is required for OpenAIChat. Install extras: weav-core[llm]") from exc
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._base_url = base_url
        self._api_key = api_key

    @staticmethod
    def _needs_completion_tokens(model: str) -> bool:
        name = (model or "").lower()
        return name.startswith(("o1", "o2", "o3", "o4", "gpt-5"))

    @staticmethod
    def _supports_temperature(model: str) -> bool:
        name = (model or "").lower()
        if name.startswith(("o1", "o2", "o3", "o4")):
            return False
        if name.startswith("gpt-5") and not name.startswith("gpt-5.1"):
            return False
        return True

    def _build_chat_kwargs(self, messages: list[dict[str, str]], config: CompletionConfig, *, stream: bool = False) -> dict:
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "top_p": config.top_p,
            "stop": config.stop,
        }
        kwargs.update(config.extra or {})

        if config.max_tokens is not None:
            if self._needs_completion_tokens(config.model):
                kwargs["max_completion_tokens"] = config.max_tokens
                kwargs.pop("max_tokens", None)
            else:
                kwargs["max_tokens"] = config.max_tokens
                kwargs.pop("max_completion_tokens", None)
        else:
            kwargs.pop("max_tokens", None)
            kwargs.pop("max_completion_tokens", None)

        if self._supports_temperature(config.model):
            kwargs["temperature"] = config.temperature
        else:
            kwargs.pop("temperature", None)

        if stream:
            kwargs["stream"] = True
        return kwargs

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        kwargs = self._build_chat_kwargs(messages, config)
        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        kwargs = self._build_chat_kwargs(messages, config, stream=True)
        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def list_models(self) -> list[str]:
        """从OpenAI API获取可用模型列表（仅使用显式传入或默认 base_url）。"""
        api_key = self._api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        base_url = self._base_url or "https://api.openai.com/v1"
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        try:
            url = f"{base_url}/models"
            req = urlrequest.Request(url, headers={"Authorization": f"Bearer {api_key}"})
            with urlrequest.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            data = payload.get("data", [])
            return [
                model_id
                for item in data
                if isinstance(item, dict) and isinstance(model_id := item.get("id"), str)
            ]
        except Exception:
            return [
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
            ]
