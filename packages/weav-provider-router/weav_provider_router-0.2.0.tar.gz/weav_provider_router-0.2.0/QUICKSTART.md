# Quick Start Guide for Weav Provider Router

## Installation

### From Source (Development)

```bash
cd weav-provider-router-repo
pip install -e ".[dev,all]"
```

### As a Submodule (in main project)

The package is already included as a submodule in the main project at:
```
packages/weav-core/weav_core/llm/weav_provider_router
```

## Running Tests

### Unit Tests (No API keys required)

```bash
cd weav-provider-router-repo
pytest -m unit -v
```

### Integration Tests (Requires API keys)

Set environment variables:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-key"
$env:ANTHROPIC_API_KEY="your-key"
$env:GOOGLE_API_KEY="your-key"

# Linux/Mac
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

Run integration tests:
```bash
pytest -m integration -v
```

### All Tests with Coverage

```bash
pytest --cov=weav_provider_router --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Basic Usage Examples

### Example 1: Simple Chat

```python
from weav_provider_router import chat

response = chat(
    provider="openai",
    api_key="your-api-key",
    question="What is machine learning?",
    model="gpt-4",
    temperature=0.7
)
print(response)
```

### Example 2: Async Chat

```python
import asyncio
from weav_provider_router import chat_async

async def main():
    response = await chat_async(
        provider="anthropic",
        api_key="your-api-key",
        question="Explain quantum computing",
        model="claude-3-5-sonnet-20241022"
    )
    print(response)

asyncio.run(main())
```

### Example 3: Streaming

```python
import asyncio
from weav_provider_router.providers import build_provider
from weav_provider_router.base import CompletionConfig

async def stream_example():
    llm = build_provider("openai", api_key="your-api-key")
    config = CompletionConfig(model="gpt-4", temperature=0.7)
    messages = [{"role": "user", "content": "Write a short poem"}]
    
    async for chunk in llm.stream(messages, config):
        print(chunk, end="", flush=True)

asyncio.run(stream_example())
```

### Example 4: List Models

```python
from weav_provider_router import list_models

# OpenAI
models = list_models("openai", api_key="your-key")
print("OpenAI models:", models[:5])

# Ollama (local)
models = list_models("ollama")
print("Ollama models:", models)
```

## Testing Individual Providers

### Test OpenAI

```python
from weav_provider_router import chat

response = chat(
    provider="openai",
    api_key="your-key",
    question="What is 2+2?",
    model="gpt-3.5-turbo"
)
assert "4" in response
print("✅ OpenAI working!")
```

### Test Anthropic

```python
response = chat(
    provider="anthropic",
    api_key="your-key",
    question="What is 2+2?",
    model="claude-3-5-sonnet-20241022"
)
assert "4" in response
print("✅ Anthropic working!")
```

### Test Ollama (Local)

```bash
# Make sure Ollama is running:
ollama serve

# In Python:
```python
response = chat(
    provider="ollama",
    api_key=None,
    question="Say hello",
    model="llama3.2",
    base_url="http://localhost:11434"
)
print("✅ Ollama working!")
```

## Code Quality Tools

### Format Code

```bash
black .
```

### Lint Code

```bash
ruff check .
ruff check --fix .  # Auto-fix issues
```

### Type Check

```bash
mypy weav_provider_router
```

## Project Structure

```
weav-provider-router-repo/
├── __init__.py              # Public API exports
├── api.py                   # High-level functions (chat, complete, list_models)
├── providers.py             # Provider registry and builder
├── base.py                  # Base classes (LLMBase, CompletionConfig)
├── adapters/                # Provider implementations
│   ├── __init__.py
│   ├── openai.py
│   ├── anthropic.py
│   ├── google.py
│   ├── ollama.py
│   ├── deepseek.py
│   ├── qwen.py
│   └── zhipu.py
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_api.py          # API tests
│   ├── test_providers.py    # Provider registry tests
│   ├── test_openai_adapter.py
│   └── test_integration.py  # Integration tests
├── README.md                # Full documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT License
├── pyproject.toml           # Package configuration
└── .gitignore              # Git ignore rules
```

## Common Issues and Solutions

### Issue: Import Error

```python
# Error: ModuleNotFoundError: No module named 'openai'
# Solution: Install provider extras
pip install -e ".[openai]"
```

### Issue: API Key Not Working

```python
# Make sure API key is valid and has correct permissions
# Test with a simple request first
from weav_provider_router import list_models
models = list_models("openai", api_key="your-key")
```

### Issue: Ollama Connection Error

```bash
# Make sure Ollama is running
ollama serve

# Check if it's accessible
curl http://localhost:11434/api/tags
```

### Issue: Tests Failing

```bash
# Run only unit tests (no API keys needed)
pytest -m unit

# Check if all dependencies are installed
pip install -e ".[dev,all]"
```

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Check CONTRIBUTING.md** if you want to contribute
3. **Run the test suite** to ensure everything works
4. **Try the examples** with your own API keys
5. **Build something awesome!** 🚀

## Support

- For bugs: Open an issue in the repository
- For questions: Check the README.md or open a discussion
- For contributions: See CONTRIBUTING.md

Happy coding! 🎉
