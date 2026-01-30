# Contributing to Weav Provider Router

Thank you for your interest in contributing to Weav Provider Router! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, package version)
   - Any relevant code snippets or error messages

### Suggesting Features

1. Check if the feature has been suggested before
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach (if you have one)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clear, concise commit messages
   - Follow the coding style (see below)
   - Add tests for new features
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest
   pytest --cov=weav_provider_router
   ```

5. **Run linters and formatters**
   ```bash
   black .
   ruff check .
   mypy weav_provider_router
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all CI checks pass

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/weav-provider-router.git
cd weav-provider-router

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all extras
pip install -e ".[dev,all]"

# Run tests to verify setup
pytest
```

## Coding Standards

### Code Style

- **PEP 8**: Follow Python style guidelines
- **Black**: Use Black for code formatting (line length: 120)
- **Type Hints**: Add type hints to all functions
- **Docstrings**: Write clear docstrings for modules, classes, and functions

Example:
```python
def process_response(response: dict[str, Any], *, validate: bool = True) -> str:
    """
    Process and validate an API response.

    Args:
        response: The API response dictionary
        validate: Whether to validate the response

    Returns:
        Processed response text

    Raises:
        ValueError: If response is invalid and validate=True
    """
    # Implementation
    pass
```

### Project Structure

```
weav_provider_router/
├── __init__.py           # Public API
├── api.py                # High-level functions
├── providers.py          # Provider registry
├── base.py               # Base classes
└── adapters/             # Provider implementations
    ├── __init__.py
    ├── openai.py
    └── ...
```

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Separate unit tests from integration tests with markers

```python
@pytest.mark.unit
def test_feature_basic():
    """Test basic feature functionality."""
    pass

@pytest.mark.integration
def test_feature_integration(api_keys):
    """Test feature with real API."""
    pass
```

### Adding a New Provider

1. **Create adapter file** in `adapters/your_provider.py`
2. **Implement LLMBase interface**:
   ```python
   from ..base import LLMBase, CompletionConfig

   class YourProviderChat(LLMBase):
       async def chat(self, messages, config):
           # Implementation
           pass

       async def complete(self, prompt, config):
           # Implementation
           pass

       async def stream(self, messages, config):
           # Implementation
           yield chunk

       def list_models(self):
           # Implementation
           return ["model-1", "model-2"]
   ```

3. **Register in providers.py**:
   ```python
   from .adapters.your_provider import YourProviderChat

   PROVIDER_CLASSES = {
       # ...existing providers
       "your_provider": YourProviderChat,
   }
   ```

4. **Add tests** in `tests/test_your_provider.py`
5. **Update documentation**:
   - README.md (add to supported providers table)
   - Add usage examples

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Include code examples for new features
- Update CHANGELOG.md following Keep a Changelog format

## Git Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
```
Add support for Gemini 2.0 models

- Update Google adapter to handle new model names
- Add tests for Gemini 2.0
- Update documentation

Fixes #123
```

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only (requires API keys)
pytest -m integration

# With coverage
pytest --cov=weav_provider_router --cov-report=html

# Specific test file
pytest tests/test_api.py

# Verbose output
pytest -v
```

### Writing Tests

```python
# Unit test example
@pytest.mark.unit
def test_build_provider_basic():
    provider = build_provider("openai", api_key="test")
    assert isinstance(provider, OpenAIChat)

# Integration test example
@pytest.mark.integration
async def test_real_api_call(api_keys):
    if not api_keys.get("openai"):
        pytest.skip("API key not set")
    response = await chat_async(
        provider="openai",
        api_key=api_keys["openai"],
        question="test"
    )
    assert isinstance(response, str)
```

## Review Process

1. **Automated Checks**: All tests and linters must pass
2. **Code Review**: At least one maintainer review required
3. **Documentation**: Ensure docs are updated
4. **Testing**: New features need tests
5. **Backwards Compatibility**: Avoid breaking changes when possible

## Questions?

- Open an issue for general questions
- Tag maintainers for urgent matters
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Weav Provider Router! 🎉
