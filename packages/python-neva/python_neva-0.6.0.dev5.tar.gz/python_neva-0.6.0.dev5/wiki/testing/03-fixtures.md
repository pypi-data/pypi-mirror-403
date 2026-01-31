# Built-in Fixtures

Neva provides several pytest fixtures to simplify testing your applications. These fixtures handle application setup, lifecycle management, and HTTP client creation.

## Available Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `test_config` | function | Creates a temporary configuration directory |
| `application` | function | Provides an initialized `Application` with managed lifecycle |
| `webapp` | function | Provides an `App` (FastAPI) instance for HTTP testing |
| `http_client` | function | Async HTTP client for making requests to your app |

## test_config

Creates a temporary configuration directory with minimal default configuration files.

```python
from pathlib import Path


async def test_config_is_path(test_config: Path) -> None:
    assert test_config.is_dir()
    assert (test_config / "app.py").exists()
    assert (test_config / "providers.py").exists()
```

**Default configuration created:**

`app.py`:

```python
config = {
    "name": "TestApp",
    "debug": True,
    "environment": "testing"
}
```

`providers.py`:

```python
config = {
    "providers": []
}
```

This fixture is primarily used as a dependency for other fixtures, but you can also use it directly when you need to add additional configuration files for a test.

## application

Provides a fully initialized `Application` instance with proper lifecycle management. The application is started before the test and properly shut down after.

```python
from neva.arch import Application
from neva.config import ConfigRepository


async def test_application_is_ready(application: Application) -> None:
    config = application.make(ConfigRepository).unwrap()

    assert config.get("app.name").unwrap() == "TestApp"
```

**What it does:**

1. Creates an `Application` with the `test_config` fixture
2. Enters the application's async lifespan context
3. Yields the application to your test
4. Properly exits the lifespan context after the test

This fixture is also automatically injected into `TestCase` subclasses via `self.app`.

## webapp

Provides an `App` instance (Neva's FastAPI wrapper) for testing HTTP endpoints.

```python
from neva.arch import App


async def test_webapp_is_app_instance(webapp: App) -> None:
    assert isinstance(webapp, App)
```

Use this fixture when you need to:

- Register routes for testing
- Test middleware behavior
- Work with the FastAPI application directly

```python
from fastapi import Response
from neva.arch import App


async def test_custom_route(webapp: App) -> None:
    @webapp.get("/hello")
    async def hello() -> dict:
        return {"message": "Hello, World!"}

    # webapp is now ready to be tested via http_client
```

## http_client

Provides an async `httpx.AsyncClient` configured to make requests to your `webapp`. See [HTTP Testing](04-http-testing.md) for detailed usage.

```python
from httpx import AsyncClient


async def test_can_make_requests(http_client: AsyncClient) -> None:
    response = await http_client.get("/")
    # Assert on response...
```

## Fixture Dependencies

The fixtures form a dependency chain:

```
test_config
    └── application (uses test_config)
    └── webapp (uses test_config)
            └── http_client (uses webapp)
```

This means:

- `application` and `webapp` both depend on `test_config`
- `http_client` depends on `webapp`
- Overriding `test_config` affects all downstream fixtures

## Using Multiple Fixtures

You can use multiple fixtures in a single test:

```python
from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository


async def test_with_multiple_fixtures(
    test_config: Path,
    application: Application,
) -> None:
    # Add additional config file
    (test_config / "custom.py").write_text('config = {"key": "value"}')

    # Note: The application was already created with the original test_config
    # To use the new config file, you'd need to create a new Application
    new_app = Application(config_path=test_config)
    async with new_app.lifespan():
        config = new_app.make(ConfigRepository).unwrap()
        assert config.get("custom.key").unwrap() == "value"
```

## Manual Application Creation

For advanced scenarios, you can create applications manually:

```python
from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository


async def test_manual_app_creation(test_config: Path) -> None:
    # Add custom configuration
    (test_config / "database.py").write_text('''
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {"driver": "sqlite", "database": ":memory:"}
    }
}
''')

    # Create and manage application lifecycle manually
    app = Application(config_path=test_config)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()

        assert config.get("database.default").unwrap() == "sqlite"
```
