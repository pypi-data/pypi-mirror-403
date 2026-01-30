"""Unit tests for provider builder and registry."""

import pytest
from weav_provider_router.providers import build_provider, build_image_provider, build_embedding_provider, LLM_PROVIDER_CLASSES, PROVIDER_CLASSES
from weav_provider_router.adapters.openai import OpenAIChat
from weav_provider_router.adapters.anthropic import AnthropicChat
from weav_provider_router.adapters.google import GoogleChat
from weav_provider_router.adapters.ollama import OllamaChat
from weav_provider_router.adapters.deepseek import DeepSeekChat
from weav_provider_router.adapters.qwen import QwenChat
from weav_provider_router.adapters.zhipu import ZhipuChat
from weav_provider_router.adapters.moonshot import MoonshotChat
from weav_provider_router.adapters.baidu import BaiduChat
from weav_provider_router.adapters.mistral import MistralChat
from weav_provider_router.adapters.groq import GroqChat
from weav_provider_router.adapters.together import TogetherChat
from weav_provider_router.adapters.cohere import CohereChat
from weav_provider_router.adapters.minimax import MiniMaxChat
from weav_provider_router.adapters.bytedance import ByteDanceChat
from weav_provider_router.adapters.nvidia import NVIDIAChat
from weav_provider_router.adapters.openai_image import OpenAIImage
from weav_provider_router.adapters.openai_embedding import OpenAIEmbedding


@pytest.mark.unit
class TestProviderRegistry:
    """Tests for provider registry."""

    def test_all_providers_registered(self):
        """Test that all expected providers are registered."""
        expected_providers = [
            "openai",
            "anthropic",
            "google",
            "ollama",
            "deepseek",
            "qwen",
            "zhipu",
            "moonshot",
            "baidu",
            "mistral",
            "groq",
            "together",
            "cohere",
            "minimax",
            "bytedance",
            "nvidia",
        ]
        for provider in expected_providers:
            assert provider in LLM_PROVIDER_CLASSES

    def test_provider_classes_mapping(self):
        """Test that provider classes are correctly mapped."""
        assert LLM_PROVIDER_CLASSES["openai"] == OpenAIChat
        assert LLM_PROVIDER_CLASSES["anthropic"] == AnthropicChat
        assert LLM_PROVIDER_CLASSES["google"] == GoogleChat
        assert LLM_PROVIDER_CLASSES["ollama"] == OllamaChat
        assert LLM_PROVIDER_CLASSES["deepseek"] == DeepSeekChat
        assert LLM_PROVIDER_CLASSES["qwen"] == QwenChat
        assert LLM_PROVIDER_CLASSES["zhipu"] == ZhipuChat
        assert LLM_PROVIDER_CLASSES["moonshot"] == MoonshotChat
        assert LLM_PROVIDER_CLASSES["baidu"] == BaiduChat
        assert LLM_PROVIDER_CLASSES["mistral"] == MistralChat
        assert LLM_PROVIDER_CLASSES["groq"] == GroqChat
        assert LLM_PROVIDER_CLASSES["together"] == TogetherChat
        assert LLM_PROVIDER_CLASSES["cohere"] == CohereChat
        assert LLM_PROVIDER_CLASSES["minimax"] == MiniMaxChat
        assert LLM_PROVIDER_CLASSES["bytedance"] == ByteDanceChat
        assert LLM_PROVIDER_CLASSES["nvidia"] == NVIDIAChat
        assert PROVIDER_CLASSES["zhipu"] == ZhipuChat


@pytest.mark.unit
class TestBuildProvider:
    """Tests for build_provider function."""

    def test_build_openai_provider(self):
        """Test building OpenAI provider."""
        provider = build_provider("openai", api_key="test-key")
        assert isinstance(provider, OpenAIChat)

    def test_build_openai_with_base_url(self):
        """Test building OpenAI provider with custom base URL."""
        provider = build_provider("openai", api_key="test-key", base_url="https://custom.com")
        assert isinstance(provider, OpenAIChat)

    def test_build_anthropic_provider(self):
        """Test building Anthropic provider."""
        provider = build_provider("anthropic", api_key="test-key")
        assert isinstance(provider, AnthropicChat)

    def test_build_google_provider(self):
        """Test building Google provider."""
        pytest.importorskip("google.generativeai", reason="google-generativeai not installed")
        provider = build_provider("google", api_key="test-key")
        assert isinstance(provider, GoogleChat)

    def test_build_ollama_provider(self):
        """Test building Ollama provider."""
        provider = build_provider("ollama")
        assert isinstance(provider, OllamaChat)

    def test_build_ollama_with_custom_url(self):
        """Test building Ollama provider with custom URL."""
        provider = build_provider("ollama", base_url="http://custom:11434")
        assert isinstance(provider, OllamaChat)

    def test_build_deepseek_provider(self):
        """Test building DeepSeek provider."""
        provider = build_provider("deepseek", api_key="test-key")
        assert isinstance(provider, DeepSeekChat)

    def test_build_qwen_provider(self):
        """Test building Qwen provider."""
        provider = build_provider("qwen", api_key="test-key")
        assert isinstance(provider, QwenChat)

    def test_build_zhipu_provider(self):
        """Test building Zhipu provider."""
        provider = build_provider("zhipu", api_key="test-key")
        assert isinstance(provider, ZhipuChat)

    def test_build_moonshot_provider(self):
        """Test building Moonshot provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("moonshot", api_key="test-key")
        assert isinstance(provider, MoonshotChat)

    def test_build_baidu_provider(self):
        """Test building Baidu provider."""
        pytest.importorskip("httpx", reason="httpx not installed")
        provider = build_provider("baidu", api_key="test-key", secret_key="test-secret")
        assert isinstance(provider, BaiduChat)

    def test_build_mistral_provider(self):
        """Test building Mistral provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("mistral", api_key="test-key")
        assert isinstance(provider, MistralChat)

    def test_build_groq_provider(self):
        """Test building Groq provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("groq", api_key="test-key")
        assert isinstance(provider, GroqChat)

    def test_build_together_provider(self):
        """Test building Together AI provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("together", api_key="test-key")
        assert isinstance(provider, TogetherChat)

    def test_build_cohere_provider(self):
        """Test building Cohere provider."""
        pytest.importorskip("httpx", reason="httpx not installed")
        provider = build_provider("cohere", api_key="test-key")
        assert isinstance(provider, CohereChat)

    def test_build_minimax_provider(self):
        """Test building MiniMax provider."""
        pytest.importorskip("httpx", reason="httpx not installed")
        provider = build_provider("minimax", api_key="test-key", group_id="test-group")
        assert isinstance(provider, MiniMaxChat)

    def test_build_bytedance_provider(self):
        """Test building ByteDance provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("bytedance", api_key="test-key")
        assert isinstance(provider, ByteDanceChat)

    def test_build_nvidia_provider(self):
        """Test building NVIDIA provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_provider("nvidia", api_key="test-key")
        assert isinstance(provider, NVIDIAChat)

    def test_case_insensitive_provider_name(self):
        """Test that provider names are case-insensitive."""
        provider1 = build_provider("OpenAI", api_key="test-key")
        provider2 = build_provider("OPENAI", api_key="test-key")
        provider3 = build_provider("openai", api_key="test-key")
        assert all(isinstance(p, OpenAIChat) for p in [provider1, provider2, provider3])

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported LLM provider: unknown"):
            build_provider("unknown", api_key="test-key")

    def test_build_provider_without_api_key(self):
        """Test building provider without API key (for Ollama)."""
        provider = build_provider("ollama")
        assert isinstance(provider, OllamaChat)


@pytest.mark.unit
class TestImageProviders:
    """Tests for image generation provider builder."""

    def test_build_openai_image_provider(self):
        """Test building OpenAI image provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_image_provider("openai", api_key="test-key")
        assert isinstance(provider, OpenAIImage)

    def test_build_dall_e_alias(self):
        """Test building with dall-e alias."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_image_provider("dall-e", api_key="test-key")
        assert isinstance(provider, OpenAIImage)

    def test_unsupported_image_provider_raises_error(self):
        """Test that unsupported image provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported image provider: unknown"):
            build_image_provider("unknown", api_key="test-key")


@pytest.mark.unit
class TestEmbeddingProviders:
    """Tests for embedding provider builder."""

    def test_build_openai_embedding_provider(self):
        """Test building OpenAI embedding provider."""
        pytest.importorskip("openai", reason="openai not installed")
        provider = build_embedding_provider("openai", api_key="test-key")
        assert isinstance(provider, OpenAIEmbedding)

    def test_unsupported_embedding_provider_raises_error(self):
        """Test that unsupported embedding provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported embedding provider: unknown"):
            build_embedding_provider("unknown", api_key="test-key")
