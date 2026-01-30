from __future__ import annotations

import json
from typing import Any, AsyncIterator

from weav_provider_router.base import CompletionConfig, LLMBase


class BaiduChat(LLMBase):
    """Baidu ERNIE (文心一言) chat adapter."""

    def __init__(self, api_key: str | None = None, secret_key: str | None = None) -> None:
        try:
            import httpx  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("httpx package is required for BaiduChat. Install it to use this provider.") from exc
        
        self._api_key = api_key
        self._secret_key = secret_key
        self._client = httpx.AsyncClient(timeout=60.0)
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """Get access token from Baidu OAuth."""
        if self._access_token:
            return self._access_token
        
        if not self._api_key or not self._secret_key:
            raise RuntimeError("Both api_key and secret_key are required for Baidu ERNIE")
        
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self._api_key}&client_secret={self._secret_key}"
        response = await self._client.get(url)
        result = response.json()
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            return self._access_token
        else:
            raise RuntimeError(f"Failed to get Baidu access token: {result}")

    def _get_endpoint(self, model: str) -> str:
        """Get the endpoint URL for specific model."""
        endpoints = {
            "ernie-4.0-8k": "completions_pro",
            "ernie-3.5-8k": "completions",
            "ernie-3.5-128k": "ernie-3.5-128k",
            "ernie-speed-128k": "ernie-speed-128k",
            "ernie-lite-8k": "ernie-lite-8k",
            "ernie-tiny-8k": "ernie-tiny-8k",
        }
        endpoint = endpoints.get(model, "completions_pro")
        return f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}"

    async def chat(self, messages: list[dict[str, Any]], config: CompletionConfig) -> str:
        """Send a chat request to Baidu ERNIE."""
        access_token = await self._get_access_token()
        url = self._get_endpoint(config.model)
        
        payload = {
            "messages": messages,
        }
        
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.top_p is not None:
            payload["top_p"] = config.top_p
        if config.max_tokens:
            payload["max_output_tokens"] = config.max_tokens
        if config.extra:
            payload.update(config.extra)
        
        response = await self._client.post(
            url,
            params={"access_token": access_token},
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        
        if "result" in result:
            return result["result"]
        else:
            raise RuntimeError(f"Baidu API error: {result}")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        """Complete a prompt using Baidu ERNIE."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, config)

    async def stream(self, messages: list[dict[str, Any]], config: CompletionConfig) -> AsyncIterator[str]:
        """Stream chat responses from Baidu ERNIE."""
        access_token = await self._get_access_token()
        url = self._get_endpoint(config.model)
        
        payload = {
            "messages": messages,
            "stream": True,
        }
        
        if config.temperature is not None:
            payload["temperature"] = config.temperature
        if config.top_p is not None:
            payload["top_p"] = config.top_p
        if config.max_tokens:
            payload["max_output_tokens"] = config.max_tokens
        if config.extra:
            payload.update(config.extra)
        
        async with self._client.stream(
            "POST",
            url,
            params={"access_token": access_token},
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        chunk = json.loads(data)
                        if "result" in chunk:
                            yield chunk["result"]
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """List available Baidu ERNIE models."""
        return [
            "ernie-4.0-8k",
            "ernie-3.5-8k",
            "ernie-3.5-128k",
            "ernie-speed-128k",
            "ernie-lite-8k",
            "ernie-tiny-8k",
        ]
