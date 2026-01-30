from __future__ import annotations

from typing import Any, AsyncIterator
import asyncio

from ..base import CompletionConfig, LLMBase


class GoogleChat(LLMBase):
    def __init__(self, api_key: str | None = None) -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("google-generativeai package required. Install it to use GoogleChat.") from exc
        genai.configure(api_key=api_key)
        self._genai = genai

    async def chat(self, messages: list[dict[str, str]], config: CompletionConfig) -> str:
        loop = asyncio.get_running_loop()
        content = "\n".join([m.get("content", "") for m in messages])

        def _extract_diag(resp: Any) -> str:
            try:
                fb = getattr(resp, "prompt_feedback", None)
                block = getattr(fb, "block_reason", None) if fb is not None else None
                safety = getattr(fb, "safety_ratings", None) if fb is not None else None
                finish = None
                cand = None
                cands = getattr(resp, "candidates", None)
                if isinstance(cands, list) and cands:
                    cand = cands[0]
                    finish = getattr(cand, "finish_reason", None)
                return f"block_reason={block}, finish_reason={finish}, safety={safety}"
            except Exception:
                return "no_diagnostics"

        def _call_with_model(model_name: str) -> tuple[str, str]:
            model = self._genai.GenerativeModel(model_name)
            resp = model.generate_content(content)
            text = getattr(resp, "text", "") or ""
            diag = _extract_diag(resp)
            return text, diag

        def _call_sync() -> str:
            candidates = []
            raw_model = (config.model or "").strip()
            if raw_model:
                candidates.append(raw_model)
                if not raw_model.startswith("models/"):
                    candidates.append(f"models/{raw_model}")
            for fallback in ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"):
                if fallback not in candidates:
                    candidates.append(fallback)
                    candidates.append(f"models/{fallback}")

            last_diag = ""
            last_err: Exception | None = None
            for name in candidates:
                try:
                    text, diag = _call_with_model(name)
                    last_diag = diag
                    if text and text.strip():
                        return text
                except Exception as e:
                    last_err = e
                    continue

            if last_err is not None:
                raise RuntimeError(f"google_llm_no_text: {last_err} ({last_diag})")
            note = last_diag or "unknown"
            raise RuntimeError(f"google_llm_empty_response: {note}")

        return await loop.run_in_executor(None, _call_sync)

    async def complete(self, prompt: str, config: CompletionConfig) -> str:
        loop = asyncio.get_running_loop()
        model = self._genai.GenerativeModel(config.model)
        def _call_sync() -> str:
            r = model.generate_content(prompt)
            return getattr(r, "text", "") or ""
        return await loop.run_in_executor(None, _call_sync)

    async def stream(self, messages: list[dict[str, str]], config: CompletionConfig) -> AsyncIterator[str]:
        text = await self.chat(messages, config)
        if text:
            yield text

    def list_models(self) -> list[str]:
        try:
            import google.generativeai as genai
            models = genai.list_models()
            model_names = []
            for m in models:
                name = getattr(m, 'name', '')
                if 'generative' in name or 'gemini' in name.lower():
                    model_names.append(name.split("/")[-1] if "/" in name else name)
            return model_names if model_names else self._get_default_models()
        except Exception:
            return self._get_default_models()
    
    def _get_default_models(self) -> list[str]:
        return [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
