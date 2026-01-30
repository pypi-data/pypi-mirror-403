"""Integration tests for all providers (requires API keys)."""

import pytest
from weav_provider_router import chat, chat_async, complete, list_models
from weav_provider_router.providers import build_provider
from weav_provider_router.base import CompletionConfig


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI provider."""

    def test_openai_chat(self, api_keys):
        """Test OpenAI chat."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        response = chat(
            provider="openai",
            api_key=api_key,
            question="What is 2+2? Answer with just the number.",
            model="gpt-3.5-turbo",
            temperature=0.0,
            max_tokens=10
        )

        assert isinstance(response, str)
        assert "4" in response

    @pytest.mark.asyncio
    async def test_openai_chat_async(self, api_keys):
        """Test OpenAI async chat."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        response = await chat_async(
            provider="openai",
            api_key=api_key,
            question="Say 'hello'",
            model="gpt-3.5-turbo",
            max_tokens=10
        )

        assert isinstance(response, str)
        assert len(response) > 0

    def test_openai_list_models(self, api_keys):
        """Test OpenAI list models."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        models = list_models("openai", api_key=api_key)

        assert isinstance(models, list)
        assert len(models) > 0


@pytest.mark.integration
class TestAnthropicIntegration:
    """Integration tests for Anthropic provider."""

    def test_anthropic_chat(self, api_keys):
        """Test Anthropic chat."""
        api_key = api_keys.get("anthropic")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        response = chat(
            provider="anthropic",
            api_key=api_key,
            question="What is 2+2? Answer with just the number.",
            model="claude-3-5-sonnet-20241022",
            temperature=0.0,
            max_tokens=10
        )

        assert isinstance(response, str)
        assert "4" in response

    @pytest.mark.asyncio
    async def test_anthropic_streaming(self, api_keys):
        """Test Anthropic streaming."""
        api_key = api_keys.get("anthropic")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        llm = build_provider("anthropic", api_key=api_key)
        config = CompletionConfig(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=50
        )
        messages = [{"role": "user", "content": "Count from 1 to 5"}]

        chunks = []
        async for chunk in llm.stream(messages, config):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0


@pytest.mark.integration
class TestGoogleIntegration:
    """Integration tests for Google provider."""

    def test_google_chat(self, api_keys):
        """Test Google chat."""
        api_key = api_keys.get("google")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set")

        response = chat(
            provider="google",
            api_key=api_key,
            question="What is the capital of France? One word answer.",
            model="gemini-pro",
            max_tokens=10
        )

        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests for Ollama provider."""

    def test_ollama_chat(self):
        """Test Ollama chat (requires local Ollama running)."""
        try:
            response = chat(
                provider="ollama",
                api_key=None,
                question="Say 'hello'",
                model="llama3.2",
                base_url="http://localhost:11434",
                max_tokens=10
            )
            assert isinstance(response, str)
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")

    def test_ollama_list_models(self):
        """Test Ollama list models."""
        try:
            models = list_models("ollama", base_url="http://localhost:11434")
            assert isinstance(models, list)
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


@pytest.mark.integration
class TestDeepSeekIntegration:
    """Integration tests for DeepSeek provider."""

    def test_deepseek_chat(self, api_keys):
        """Test DeepSeek chat."""
        api_key = api_keys.get("deepseek")
        if not api_key:
            pytest.skip("DEEPSEEK_API_KEY not set")

        response = chat(
            provider="deepseek",
            api_key=api_key,
            question="What is 1+1?",
            model="deepseek-chat",
            max_tokens=10
        )

        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestQwenIntegration:
    """Integration tests for Qwen provider."""

    def test_qwen_chat(self, api_keys):
        """Test Qwen chat."""
        api_key = api_keys.get("qwen")
        if not api_key:
            pytest.skip("QWEN_API_KEY not set")

        response = chat(
            provider="qwen",
            api_key=api_key,
            question="你好",
            model="qwen-plus",
            max_tokens=10
        )

        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestZhipuIntegration:
    """Integration tests for Zhipu provider."""

    def test_zhipu_chat(self, api_keys):
        """Test Zhipu chat."""
        api_key = api_keys.get("zhipu")
        if not api_key:
            pytest.skip("ZHIPU_API_KEY not set")

        response = chat(
            provider="zhipu",
            api_key=api_key,
            question="你好",
            model="glm-4",
            max_tokens=10
        )

        assert isinstance(response, str)
        assert len(response) > 0


@pytest.mark.integration
class TestCrossProviderComparison:
    """Cross-provider comparison tests."""

    @pytest.mark.parametrize("provider,model", [
        ("openai", "gpt-3.5-turbo"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
    ])
    def test_same_question_multiple_providers(self, api_keys, provider, model):
        """Test same question across multiple providers."""
        api_key = api_keys.get(provider)
        if not api_key:
            pytest.skip(f"{provider.upper()}_API_KEY not set")

        question = "What is 5+5? Answer with just the number."
        response = chat(
            provider=provider,
            api_key=api_key,
            question=question,
            model=model,
            temperature=0.0,
            max_tokens=10
        )

        assert isinstance(response, str)
        assert "10" in response


@pytest.mark.integration
class TestErrorCases:
    """Integration tests for error cases."""

    def test_invalid_api_key(self):
        """Test handling of invalid API key."""
        with pytest.raises(Exception):
            chat(
                provider="openai",
                api_key="invalid-key-12345",
                question="Test",
                model="gpt-3.5-turbo"
            )

    def test_invalid_model(self, api_keys):
        """Test handling of invalid model."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        with pytest.raises(Exception):
            chat(
                provider="openai",
                api_key=api_key,
                question="Test",
                model="non-existent-model-xyz"
            )

    def test_empty_question(self, api_keys):
        """Test handling of empty question."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        # Should not raise, but might return empty or error message
        response = chat(
            provider="openai",
            api_key=api_key,
            question="",
            model="gpt-3.5-turbo"
        )
        assert isinstance(response, str)
