from __future__ import annotations

from typing import Any, AsyncIterator

from weav_provider_router.base import CompletionConfig, LLMBase


class MiniMaxChat(LLMBase):
    """MiniMax (海螺AI) chat adapter."""

    def __init__(self, api_key: str | None = None, group_id: str | None = None) -> None:
        try:
            import httpx  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("httpx package is required for MiniMaxChat. Install it to use this provider.") from exc
        
        self._api_key = api_key
        self._group_id = group_id
        self._client = httpx.AsyncClient(timeout=60.0)
        self._base_url = "https://api.minimax.chat/v1"

    async def chat(self, messages: list[dict[str, Any]], config: CompletionConfig) -> str:
        """Send a chat request to MiniMax."""
        if not self._api_key or not self._group_id:
            raise RuntimeError("Both api_key and group_id are required for MiniMax")
        
        url = f"{self._base_url}/text/chatcompletion_v2"
        
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
        }
        
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            payload["top_p"] = config.top_p
        if config.extra:
            payload.update(config.extra)
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        params = {"GroupId": self._group_id}
        
        response = await self._client.post(url, json=payload, headers=headers, params=params)
        result = response.json()
        
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"MiniMax API error: {result}")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        """Complete a prompt using MiniMax."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def stream(self, messages: list[dict[str, Any]], config: CompletionConfig) -> AsyncIterator[str]:
        """Stream chat responses from MiniMax."""
        if not self._api_key or not self._group_id:
            raise RuntimeError("Both api_key and group_id are required for MiniMax")
        
        url = f"{self._base_url}/text/chatcompletion_v2"
        
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "stream": True,
        }
        
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            payload["top_p"] = config.top_p
        if config.extra:
            payload.update(config.extra)
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        params = {"GroupId": self._group_id}
        
        async with self._client.stream("POST", url, json=payload, headers=headers, params=params) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available MiniMax models."""
        return [
            "abab6.5-chat",
            "abab6.5s-chat",
            "abab5.5-chat",
            "abab5.5s-chat",
        ]
