from __future__ import annotations

import json
from typing import Any, AsyncIterator

from weav_provider_router.base import CompletionConfig, LLMBase


class CohereChat(LLMBase):
    """Cohere chat adapter."""

    def __init__(self, api_key: str | None = None) -> None:
        try:
            import httpx  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("httpx package is required for CohereChat. Install it to use this provider.") from exc
        
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        self._base_url = "https://api.cohere.ai/v1"

    def _convert_messages(self, messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        """Convert messages to Cohere format (chat_history + message)."""
        if not messages:
            return "", []
        
        # Last message is the current user message
        message = messages[-1]["content"]
        
        # Previous messages are chat history
        chat_history = []
        for msg in messages[:-1]:
            role = "USER" if msg["role"] == "user" else "CHATBOT"
            chat_history.append({
                "role": role,
                "message": msg["content"]
            })
        
        return message, chat_history

    async def chat(self, messages: list[dict[str, Any]], config: CompletionConfig) -> str:
        """Send a chat request to Cohere."""
        message, chat_history = self._convert_messages(messages)
        
        payload: dict[str, Any] = {
            "model": config.model,
            "message": message,
        }
        
        if chat_history:
            payload["chat_history"] = chat_history
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            payload["p"] = config.top_p
        if config.stop:
            payload["stop_sequences"] = config.stop
        if config.extra:
            payload.update(config.extra)
        
        response = await self._client.post(
            f"{self._base_url}/chat",
            json=payload
        )
        result = response.json()
        
        if "text" in result:
            return result["text"]
        else:
            raise RuntimeError(f"Cohere API error: {result}")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        """Complete a prompt using Cohere."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def stream(self, messages: list[dict[str, Any]], config: CompletionConfig) -> AsyncIterator[str]:
        """Stream chat responses from Cohere."""
        message, chat_history = self._convert_messages(messages)
        
        payload: dict[str, Any] = {
            "model": config.model,
            "message": message,
            "stream": True,
        }
        
        if chat_history:
            payload["chat_history"] = chat_history
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if config.top_p is not None:
            payload["p"] = config.top_p
        if config.stop:
            payload["stop_sequences"] = config.stop
        if config.extra:
            payload.update(config.extra)
        
        async with self._client.stream(
            "POST",
            f"{self._base_url}/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if chunk.get("event_type") == "text-generation":
                            if "text" in chunk:
                                yield chunk["text"]
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available Cohere models."""
        return [
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
        ]
