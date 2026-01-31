# Testing Your Neva Application

Neva provides a set of testing utilities through the `neva.testing` module to help you write tests for your applications. These utilities integrate seamlessly with pytest and provide convenient abstractions for common testing patterns.

## What's Included

The `neva.testing` module provides:

- **TestCase**: A base class that auto-injects the application instance into your test classes
- **Fixtures**: Pre-built pytest fixtures for application lifecycle management
- **HTTP utilities**: An async HTTP client for testing your API endpoints

## Requirements

Neva's testing utilities require the following dependencies:

```toml
[
  "pytest>=9.0.2",
  "pytest-asyncio>=0.25.3",
]
```

You may install these with:

```bash
uv add neva[testing] # or neva[all]
# or
pip install neva[testing] # or neva[all]
```

## Quick Setup

To use Neva's testing fixtures in your project, register them in your `conftest.py`:

```python
# tests/conftest.py
pytest_plugins = ["neva.testing.fixtures"]
```

This makes all Neva fixtures available to your tests automatically.

## Pytest Configuration

Neva's testing utilities are designed for async tests.

You may add the following to your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
```

This configuration:

- Enables automatic async test detection (no need for `@pytest.mark.asyncio` decorators)
- Ensures each test gets a fresh event loop
- Sets the default test discovery path

## Next Steps

- [TestCase Base Class](02-test-case.md) - Learn about the base class for your tests
- [Built-in Fixtures](03-fixtures.md) - Explore the available fixtures
- [HTTP Testing](04-http-testing.md) - Test your API endpoints
- [Custom Configuration](05-custom-configuration.md) - Override config for specific test scenarios
- [Test Isolation](06-test-isolation.md) - Understand how tests are isolated
