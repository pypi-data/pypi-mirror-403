"""Unit tests for high-level API functions."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from weav_provider_router import chat, chat_async, complete, complete_async, list_models


@pytest.mark.unit
class TestChatAPI:
    """Tests for chat API functions."""

    @pytest.mark.asyncio
    async def test_chat_async_basic(self, sample_completion_config):
        """Test basic async chat functionality."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(return_value="Test response")
            mock_build.return_value = mock_provider

            response = await chat_async(
                provider="openai",
                api_key="test-key",
                question="Hello",
                model="gpt-4"
            )

            assert response == "Test response"
            mock_build.assert_called_once_with("openai", api_key="test-key", base_url=None)
            mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_async_with_parameters(self):
        """Test async chat with custom parameters."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(return_value="Custom response")
            mock_build.return_value = mock_provider

            response = await chat_async(
                provider="anthropic",
                api_key="test-key",
                question="Test question",
                model="claude-3-5-sonnet-20241022",
                temperature=0.5,
                max_tokens=500,
                top_p=0.9,
                stop=["END"]
            )

            assert response == "Custom response"
            call_args = mock_provider.chat.call_args
            config = call_args[0][1]
            assert config.model == "claude-3-5-sonnet-20241022"
            assert config.temperature == 0.5
            assert config.max_tokens == 500
            assert config.top_p == 0.9
            assert config.stop == ["END"]

    def test_chat_sync(self):
        """Test synchronous chat function."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(return_value="Sync response")
            mock_build.return_value = mock_provider

            response = chat(
                provider="openai",
                api_key="test-key",
                question="Hello sync",
                model="gpt-3.5-turbo"
            )

            assert response == "Sync response"
            mock_build.assert_called_once()

    def test_chat_with_base_url(self):
        """Test chat with custom base URL."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(return_value="Response")
            mock_build.return_value = mock_provider

            chat(
                provider="openai",
                api_key="test-key",
                question="Test",
                base_url="https://custom.api.com"
            )

            mock_build.assert_called_once_with(
                "openai",
                api_key="test-key",
                base_url="https://custom.api.com"
            )

    def test_chat_with_extra_params(self):
        """Test chat with extra parameters."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(return_value="Response")
            mock_build.return_value = mock_provider

            extra_params = {"thinking": {"enabled": True}}
            chat(
                provider="anthropic",
                api_key="test-key",
                question="Test",
                extra=extra_params
            )

            call_args = mock_provider.chat.call_args
            config = call_args[0][1]
            assert config.extra == extra_params


@pytest.mark.unit
class TestCompleteAPI:
    """Tests for completion API functions."""

    @pytest.mark.asyncio
    async def test_complete_async_basic(self):
        """Test basic async completion functionality."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.complete = AsyncMock(return_value="Completed text")
            mock_build.return_value = mock_provider

            response = await complete_async(
                provider="openai",
                api_key="test-key",
                prompt="Once upon a time",
                model="gpt-4"
            )

            assert response == "Completed text"
            mock_provider.complete.assert_called_once()

    def test_complete_sync(self):
        """Test synchronous completion function."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.complete = AsyncMock(return_value="Sync completion")
            mock_build.return_value = mock_provider

            response = complete(
                provider="openai",
                api_key="test-key",
                prompt="Complete this",
                model="gpt-3.5-turbo"
            )

            assert response == "Sync completion"

    @pytest.mark.asyncio
    async def test_complete_async_with_parameters(self):
        """Test async completion with custom parameters."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.complete = AsyncMock(return_value="Response")
            mock_build.return_value = mock_provider

            await complete_async(
                provider="openai",
                api_key="test-key",
                prompt="Test prompt",
                model="gpt-4",
                temperature=0.8,
                max_tokens=200
            )

            call_args = mock_provider.complete.call_args
            config = call_args[0][1]
            assert config.temperature == 0.8
            assert config.max_tokens == 200


@pytest.mark.unit
class TestListModelsAPI:
    """Tests for list_models API function."""

    def test_list_models_basic(self):
        """Test basic list_models functionality."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.list_models.return_value = ["model-1", "model-2", "model-3"]
            mock_build.return_value = mock_provider

            models = list_models("openai", api_key="test-key")

            assert models == ["model-1", "model-2", "model-3"]
            mock_build.assert_called_once_with("openai", api_key="test-key", base_url=None)

    def test_list_models_with_base_url(self):
        """Test list_models with custom base URL."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.list_models.return_value = ["model-a", "model-b"]
            mock_build.return_value = mock_provider

            models = list_models(
                "openai",
                api_key="test-key",
                base_url="https://custom.com"
            )

            assert len(models) == 2
            mock_build.assert_called_once_with(
                "openai",
                api_key="test-key",
                base_url="https://custom.com"
            )

    def test_list_models_ollama(self):
        """Test list_models for Ollama provider."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.list_models.return_value = ["llama3.2", "codellama"]
            mock_build.return_value = mock_provider

            models = list_models("ollama", base_url="http://localhost:11434")

            assert "llama3.2" in models
            assert "codellama" in models


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling in API functions."""

    def test_chat_with_invalid_provider(self):
        """Test chat with invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            chat(
                provider="invalid_provider",
                api_key="test-key",
                question="Test"
            )

    @pytest.mark.asyncio
    async def test_chat_async_with_api_error(self):
        """Test chat_async handles API errors properly."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.chat = AsyncMock(side_effect=Exception("API Error"))
            mock_build.return_value = mock_provider

            with pytest.raises(Exception, match="API Error"):
                await chat_async(
                    provider="openai",
                    api_key="test-key",
                    question="Test"
                )

    def test_complete_with_missing_model(self):
        """Test complete with missing model parameter."""
        with patch("weav_provider_router.api.build_provider") as mock_build:
            mock_provider = MagicMock()
            mock_provider.complete = AsyncMock(return_value="Response")
            mock_build.return_value = mock_provider

            # Should work with empty model string
            response = complete(
                provider="openai",
                api_key="test-key",
                prompt="Test"
            )

            assert response == "Response"
