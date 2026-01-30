from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator
from urllib import request as urlrequest

from ..base import CompletionConfig, LLMBase


logger = logging.getLogger(__name__)


class AnthropicChat(LLMBase):
    def __init__(self, api_key: str | None = None) -> None:
        try:
            import anthropic  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("anthropic package required. Install it to use AnthropicChat.") from exc
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._api_key = api_key

    @staticmethod
    def _convert_messages(messages: list[dict[str, str]]) -> tuple[str | None, list[dict[str, Any]]]:
        system_parts: list[str] = []
        converted: list[dict[str, Any]] = []
        for msg in messages:
            role = (msg.get("role") or "user").strip()
            content = msg.get("content") or ""
            if role == "system":
                system_parts.append(str(content))
                continue
            if role not in ("user", "assistant"):
                role = "user"
            converted.append({"role": role, "content": [{"type": "text", "text": str(content)}]})
        system_prompt = "\n\n".join(system_parts) if system_parts else None
        if not converted:
            converted = [{"role": "user", "content": [{"type": "text", "text": ""}]}]
        return system_prompt, converted

    @staticmethod
    def _extract_text_from_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                text = None
                if isinstance(block, str):
                    text = block
                elif isinstance(block, dict):
                    text = block.get("text")
                else:
                    text = getattr(block, "text", None)
                if isinstance(text, str) and text:
                    parts.append(text)
            return "".join(parts)
        return ""

    @staticmethod
    def _extract_tool_call(content: Any) -> str | None:
        if not isinstance(content, list):
            return None
        for block in content:
            if isinstance(block, dict):
                block_type = block.get("type")
                name = block.get("name")
                args = block.get("input")
            else:
                block_type = getattr(block, "type", None)
                name = getattr(block, "name", None)
                args = getattr(block, "input", None)
            if block_type == "tool_use" and name:
                payload = {
                    "type": "tool_call",
                    "tool": name,
                    "args": args if isinstance(args, dict) else {"_raw": args},
                }
                return json.dumps(payload, ensure_ascii=False)
        return None

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        system_prompt, anthropic_messages = self._convert_messages(messages)
        kwargs: dict[str, Any] = {
            "model": config.model,
            "max_tokens": config.max_tokens or 1024,
            "temperature": config.temperature,
            "messages": anthropic_messages,
        }
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.stop:
            kwargs["stop_sequences"] = config.stop
        if system_prompt:
            kwargs["system"] = system_prompt

        async def _once(payload: dict[str, Any]) -> tuple[Any, Any, str, str | None]:
            resp_local = await self._client.messages.create(**payload)
            resp_content_local = (
                resp_local.get("content")
                if isinstance(resp_local, dict)
                else getattr(resp_local, "content", None)
            )
            text_local = self._extract_text_from_content(resp_content_local)
            tool_call_local = self._extract_tool_call(resp_content_local)
            return resp_local, resp_content_local, text_local, tool_call_local

        resp, resp_content, text, tool_call = await _once(kwargs)
        if isinstance(text, str) and text.strip():
            return text
        if tool_call:
            return tool_call

        retry_messages = list(anthropic_messages)
        retry_messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "上一次回复为空。请输出一个 JSON（如 {\"type\":\"continue\"}）或直接给出答案，不能留空。",
                    }
                ],
            }
        )
        retry_kwargs = dict(kwargs)
        retry_kwargs["messages"] = retry_messages
        try:
            resp, resp_content, text, tool_call = await _once(retry_kwargs)
            if isinstance(text, str) and text.strip():
                return text
            if tool_call:
                return tool_call
        except Exception:
            raise

        stop_reason = getattr(resp, "stop_reason", None)
        stop_sequence = getattr(resp, "stop_sequence", None)
        usage = getattr(resp, "usage", None)
        content_types = [
            (blk.get("type") if isinstance(blk, dict) else getattr(blk, "type", None))
            for blk in resp_content or []
        ] if isinstance(resp_content, list) else resp_content
        diag = {
            "stop_reason": stop_reason,
            "stop_sequence": stop_sequence,
            "content_types": content_types,
            "usage": getattr(usage, "model_dump", lambda: usage)(),
        }
        logger.error(f"[AnthropicChat] Empty content from response: {diag}")
        raise RuntimeError(f"anthropic_empty_content: {diag}")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        return await self.chat([{"role": "user", "content": prompt}], config)

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        system_prompt, anthropic_messages = self._convert_messages(messages)
        kwargs: dict[str, Any] = {
            "model": config.model,
            "max_tokens": config.max_tokens or 1024,
            "temperature": config.temperature,
            "messages": anthropic_messages,
            "stream": True,
        }
        if config.top_p is not None:
            kwargs["top_p"] = config.top_p
        if config.stop:
            kwargs["stop_sequences"] = config.stop
        if system_prompt:
            kwargs["system"] = system_prompt

        stream = await self._client.messages.create(**kwargs)
        async for event in stream:
            text = getattr(event, "text", None)
            if not text:
                delta = getattr(event, "delta", None)
                text = getattr(delta, "text", None) if delta is not None else None
            if not text and isinstance(event, dict):
                text = event.get("text")
                if not text and event.get("type") == "content_block_delta":
                    delta = event.get("delta") or {}
                    if isinstance(delta, dict):
                        text = delta.get("text")
            if text:
                yield text

    def list_models(self) -> list[str]:
        static_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet",
            "claude-3-opus-20250219",
            "claude-3-opus",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        api_key = self._api_key
        if not api_key:
            return static_models
        try:
            req = urlrequest.Request(
                "https://api.anthropic.com/v1/models",
                headers={
                    "X-Api-Key": api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urlrequest.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            data = payload.get("data", [])
            models = [
                item.get("id")
                for item in data
                if isinstance(item, dict) and item.get("id")
            ]
            return models or static_models
        except Exception:
            return static_models
