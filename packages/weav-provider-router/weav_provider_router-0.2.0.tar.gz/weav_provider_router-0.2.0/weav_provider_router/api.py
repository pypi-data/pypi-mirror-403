from __future__ import annotations

import asyncio
from typing import Any, Optional

from .base import CompletionConfig
from .providers import build_provider


async def chat_async(
    provider: str,
    api_key: Optional[str],
    question: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
    stop: Optional[list[str]] = None,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    llm = build_provider(provider, api_key=api_key, base_url=base_url)
    cfg = CompletionConfig(
        model=model or "",
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop=stop,
        extra=extra or {},
    )
    messages = [{"role": "user", "content": question}]
    return await llm.chat(messages, cfg)


def chat(
    provider: str,
    api_key: Optional[str],
    question: str,
    **kwargs: Any,
) -> str:
    try:
        return asyncio.run(chat_async(provider, api_key, question, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(chat_async(provider, api_key, question, **kwargs))


async def complete_async(
    provider: str,
    api_key: Optional[str],
    prompt: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
    stop: Optional[list[str]] = None,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    llm = build_provider(provider, api_key=api_key, base_url=base_url)
    cfg = CompletionConfig(
        model=model or "",
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop=stop,
        extra=extra or {},
    )
    return await llm.complete(prompt, cfg)


def complete(
    provider: str,
    api_key: Optional[str],
    prompt: str,
    **kwargs: Any,
) -> str:
    try:
        return asyncio.run(complete_async(provider, api_key, prompt, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(complete_async(provider, api_key, prompt, **kwargs))


def list_models(
    provider: str,
    api_key: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
) -> list[str]:
    llm = build_provider(provider, api_key=api_key, base_url=base_url)
    return llm.list_models()


__all__ = [
    "chat_async",
    "chat",
    "complete_async",
    "complete",
    "list_models",
]
