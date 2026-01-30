from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, cast

from ..base import CompletionConfig, LLMBase

logger = logging.getLogger(__name__)


class ZhipuChat(LLMBase):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package required. Install it to use ZhipuChat.") from exc

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://open.bigmodel.cn/api/paas/v4",
        )

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        model = (config.model or "").strip()
        model_l = model.lower()
        candidate_models = [m for m in (model, model_l) if m]

        last_resp = None
        last_exception = None
        for m in candidate_models:
            try:
                resp = await self._client.chat.completions.create(
                    model=m,
                    messages=cast(Any, messages),
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p,
                    stop=config.stop,
                    **config.extra,
                )
                last_resp = resp
                if not resp.choices:
                    continue
                msg = resp.choices[0].message
                text = getattr(msg, "content", None) or ""
                if isinstance(text, str) and text.strip():
                    return text
                tool_calls = getattr(msg, "tool_calls", None)
                if isinstance(tool_calls, list) and tool_calls:
                    tc = tool_calls[0]
                    fn = getattr(tc, "function", None)
                    name = getattr(fn, "name", None) if fn is not None else None
                    args_raw = getattr(fn, "arguments", None) if fn is not None else None
                    if name:
                        try:
                            args = (
                                json.loads(args_raw)
                                if isinstance(args_raw, str) and args_raw.strip()
                                else {}
                            )
                        except Exception:
                            args = {"_raw": args_raw}
                        result = json.dumps(
                            {"type": "tool_call", "tool": name, "args": args}, ensure_ascii=False
                        )
                        return result
            except Exception as e:
                last_exception = e
                continue

        finish = None
        error_msg = None
        response_info = {}
        try:
            if last_resp:
                if last_resp.choices:
                    choice = last_resp.choices[0]
                    finish = getattr(choice, "finish_reason", None)
                    response_info["finish_reason"] = finish
                    response_info["index"] = getattr(choice, "index", None)
                    response_info["logprobs"] = getattr(choice, "logprobs", None)
                response_info["id"] = getattr(last_resp, "id", None)
                response_info["model"] = getattr(last_resp, "model", None)
                response_info["object"] = getattr(last_resp, "object", None)
                response_info["created"] = getattr(last_resp, "created", None)
                if hasattr(last_resp, "error"):
                    error_msg = str(last_resp.error)
                    response_info["error"] = error_msg
        except Exception:
            pass

        error_detail = f"model={model!r}, finish_reason={finish}, response_info={response_info}"
        if error_msg:
            error_detail += f", error={error_msg}"
        if last_exception:
            error_detail += f", exception={type(last_exception).__name__}: {last_exception}"
        raise RuntimeError(f"zhipu_empty_content ({error_detail})")

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        return await self.chat([{"role": "user", "content": prompt}], config)

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=config.model,
            messages=cast(Any, messages),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            stop=config.stop,
            stream=True,
            **config.extra,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def list_models(self) -> list[str]:
        models = [
            "glm-4.6",
            "glm-4.5",
            "glm-4.5-x",
            "glm-4.5-air",
            "glm-4.5-airx",
            "glm-4-plus",
            "glm-4-air-250414",
            "glm-4-long",
            "glm-4-airx",
            "glm-4-flashx-250414",
            "glm-4.5-flash",
            "glm-4-flash-250414",
        ]
        seen = set()
        uniq: list[str] = []
        for m in models:
            if m not in seen:
                seen.add(m)
                uniq.append(m)
        return uniq
