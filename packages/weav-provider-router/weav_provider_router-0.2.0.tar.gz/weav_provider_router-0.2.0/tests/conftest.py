"""Pytest configuration and fixtures for weav_provider_router tests."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_google_client():
    """Mock Google client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test response"
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_client.GenerativeModel.return_value = mock_model
    return mock_client


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    mock_client = MagicMock()
    mock_response = {"message": {"content": "Test response"}}
    mock_client.chat = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_completion_config():
    """Sample completion configuration."""
    from weav_provider_router.base import CompletionConfig
    return CompletionConfig(
        model="test-model",
        temperature=0.7,
        max_tokens=100,
        top_p=1.0,
        stop=None,
        extra={}
    )


@pytest.fixture
def sample_messages():
    """Sample chat messages."""
    return [
        {"role": "user", "content": "Hello, how are you?"}
    ]


@pytest.fixture
def api_keys():
    """Get API keys from environment variables."""
    return {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GOOGLE_API_KEY"),
        "deepseek": os.getenv("DEEPSEEK_API_KEY"),
        "qwen": os.getenv("QWEN_API_KEY"),
        "zhipu": os.getenv("ZHIPU_API_KEY"),
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API keys)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no external dependencies)"
    )
