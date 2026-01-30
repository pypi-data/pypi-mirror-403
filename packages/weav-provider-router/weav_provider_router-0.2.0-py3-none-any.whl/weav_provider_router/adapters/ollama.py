from __future__ import annotations

from typing import Any, AsyncIterator

from ..base import CompletionConfig, LLMBase


class OllamaChat(LLMBase):
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        try:
            import httpx
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("httpx is required for OllamaChat") from exc
        self._client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        resp = await self._client.post("/api/generate", json={"model": config.model, "prompt": prompt, "stream": False})
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        resp = await self._client.post("/api/generate", json={"model": config.model, "prompt": prompt, "stream": False})
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        resp = await self._client.post("/api/generate", json={"model": config.model, "prompt": prompt, "stream": True})
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            yield line

    def list_models(self) -> list[str]:
        try:
            import httpx
            client = httpx.Client(base_url=self._client.base_url, timeout=10.0)
            resp = client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            client.close()
            return [m.get("name", "") for m in models if m.get("name")]
        except Exception:
            return []
