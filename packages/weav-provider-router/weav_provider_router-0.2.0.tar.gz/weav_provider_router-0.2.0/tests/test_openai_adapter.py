"""Unit tests for OpenAI adapter."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from weav_provider_router.adapters.openai import OpenAIChat
from weav_provider_router.base import CompletionConfig


@pytest.mark.unit
class TestOpenAIChat:
    """Tests for OpenAI adapter."""

    def test_initialization(self):
        """Test OpenAI adapter initialization."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key", base_url="https://api.openai.com")
            assert adapter._api_key == "test-key"
            assert adapter._base_url == "https://api.openai.com"

    def test_needs_completion_tokens_o1(self):
        """Test that O1 models need completion tokens."""
        assert OpenAIChat._needs_completion_tokens("o1-preview")
        assert OpenAIChat._needs_completion_tokens("o1-mini")
        assert OpenAIChat._needs_completion_tokens("o2-preview")
        assert not OpenAIChat._needs_completion_tokens("gpt-4")
        assert not OpenAIChat._needs_completion_tokens("gpt-3.5-turbo")

    def test_supports_temperature(self):
        """Test temperature support detection."""
        assert OpenAIChat._supports_temperature("gpt-4")
        assert OpenAIChat._supports_temperature("gpt-3.5-turbo")
        assert OpenAIChat._supports_temperature("gpt-4o")
        assert not OpenAIChat._supports_temperature("o1-preview")
        assert not OpenAIChat._supports_temperature("o1-mini")

    def test_build_chat_kwargs_basic(self):
        """Test building chat kwargs with basic config."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(
                model="gpt-4",
                temperature=0.7,
                max_tokens=100,
                top_p=1.0
            )
            messages = [{"role": "user", "content": "Hello"}]

            kwargs = adapter._build_chat_kwargs(messages, config)

            assert kwargs["model"] == "gpt-4"
            assert kwargs["messages"] == messages
            assert kwargs["temperature"] == 0.7
            assert kwargs["max_tokens"] == 100
            assert kwargs["top_p"] == 1.0

    def test_build_chat_kwargs_o1_model(self):
        """Test building chat kwargs for O1 model."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(
                model="o1-preview",
                temperature=0.7,
                max_tokens=100
            )
            messages = [{"role": "user", "content": "Hello"}]

            kwargs = adapter._build_chat_kwargs(messages, config)

            assert "max_completion_tokens" in kwargs
            assert "max_tokens" not in kwargs
            assert "temperature" not in kwargs

    def test_build_chat_kwargs_with_stop(self):
        """Test building chat kwargs with stop sequences."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(
                model="gpt-4",
                stop=["END", "STOP"]
            )
            messages = [{"role": "user", "content": "Hello"}]

            kwargs = adapter._build_chat_kwargs(messages, config)

            assert kwargs["stop"] == ["END", "STOP"]

    def test_build_chat_kwargs_with_extra(self):
        """Test building chat kwargs with extra parameters."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(
                model="gpt-4",
                extra={"presence_penalty": 0.5, "frequency_penalty": 0.3}
            )
            messages = [{"role": "user", "content": "Hello"}]

            kwargs = adapter._build_chat_kwargs(messages, config)

            assert kwargs["presence_penalty"] == 0.5
            assert kwargs["frequency_penalty"] == 0.3

    def test_build_chat_kwargs_streaming(self):
        """Test building chat kwargs for streaming."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(model="gpt-4")
            messages = [{"role": "user", "content": "Hello"}]

            kwargs = adapter._build_chat_kwargs(messages, config, stream=True)

            assert kwargs["stream"] is True

    @pytest.mark.asyncio
    async def test_chat(self):
        """Test chat method."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(model="gpt-4")
            messages = [{"role": "user", "content": "Hello"}]

            response = await adapter.chat(messages, config)

            assert response == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete(self):
        """Test complete method."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Completed text"))]
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(model="gpt-4")

            response = await adapter.complete("Once upon a time", config)

            assert response == "Completed text"

    @pytest.mark.asyncio
    async def test_stream(self):
        """Test streaming method."""
        with patch("openai.AsyncOpenAI") as mock_openai:
            # Create mock stream chunks
            mock_chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
            ]

            async def mock_stream_gen():
                for chunk in mock_chunks:
                    yield chunk

            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream_gen())
            mock_openai.return_value = mock_client

            adapter = OpenAIChat(api_key="test-key")
            config = CompletionConfig(model="gpt-4")
            messages = [{"role": "user", "content": "Hello"}]

            chunks = []
            async for chunk in adapter.stream(messages, config):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]

    def test_list_models(self):
        """Test list_models method."""
        with patch("openai.AsyncOpenAI"):
            with patch("weav_provider_router.adapters.openai.urlrequest.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b'{"data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]}'
                mock_urlopen.return_value.__enter__.return_value = mock_response

                adapter = OpenAIChat(api_key="test-key")
                models = adapter.list_models()

                assert "gpt-4" in models
                assert "gpt-3.5-turbo" in models

    def test_list_models_without_api_key(self):
        """Test list_models raises error without API key."""
        with patch("openai.AsyncOpenAI"):
            adapter = OpenAIChat(api_key=None)
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY is required"):
                adapter.list_models()

    def test_list_models_with_custom_base_url(self):
        """Test list_models with custom base URL."""
        with patch("openai.AsyncOpenAI"):
            with patch("weav_provider_router.adapters.openai.urlrequest.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b'{"data": [{"id": "custom-model"}]}'
                mock_urlopen.return_value.__enter__.return_value = mock_response

                adapter = OpenAIChat(api_key="test-key", base_url="https://custom.api.com")
                models = adapter.list_models()

                assert "custom-model" in models
                # Verify correct URL was used
                call_args = mock_urlopen.call_args[0][0]
                assert "custom.api.com" in call_args.full_url


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI adapter (requires API key)."""

    @pytest.mark.asyncio
    async def test_real_chat(self, api_keys):
        """Test real chat with OpenAI API."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        adapter = OpenAIChat(api_key=api_key)
        config = CompletionConfig(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=50
        )
        messages = [{"role": "user", "content": "Say 'test' and nothing else"}]

        response = await adapter.chat(messages, config)

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_real_list_models(self, api_keys):
        """Test real list_models with OpenAI API."""
        api_key = api_keys.get("openai")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        adapter = OpenAIChat(api_key=api_key)
        models = adapter.list_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert any("gpt" in model.lower() for model in models)
