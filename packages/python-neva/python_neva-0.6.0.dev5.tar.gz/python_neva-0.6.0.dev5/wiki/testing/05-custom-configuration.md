# Custom Configuration in Tests

Neva's testing fixtures use a default minimal configuration, but you'll often need to customize configuration for specific test scenarios. This guide covers different approaches to providing custom configuration in your tests.

## Default Configuration

The `test_config` fixture creates a temporary directory with these default files:

**app.py:**
```python
config = {
    "name": "TestApp",
    "debug": True,
    "environment": "testing"
}
```

**providers.py:**
```python
config = {
    "providers": []
}
```

## Overriding test_config in a Test Class

Override the `test_config` fixture within a test class to provide custom configuration for all tests in that class:

```python
from pathlib import Path

import pytest

from neva.arch import Application
from neva.config import ConfigRepository


class TestWithCustomConfig:
    @pytest.fixture
    def test_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "app.py").write_text('''
config = {
    "name": "CustomApp",
    "debug": False,
    "environment": "staging",
    "feature_flags": {
        "new_dashboard": True,
        "beta_features": False,
    }
}
''')

        (config_dir / "providers.py").write_text('config = {"providers": []}')

        return config_dir

    async def test_uses_custom_app_config(self, application: Application) -> None:
        config = application.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "CustomApp"
        assert config.get("app.debug").unwrap() is False
        assert config.get("app.feature_flags.new_dashboard").unwrap() is True
```

## Overriding test_config with TestCase

When using the `TestCase` base class, override `test_config` in the same way:

```python
from pathlib import Path

import pytest

from neva.config import ConfigRepository
from neva.testing import TestCase


class TestCustomConfigWithTestCase(TestCase):
    @pytest.fixture
    def test_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "app.py").write_text('''
config = {
    "name": "MyCustomApp",
    "debug": True,
}
''')

        (config_dir / "providers.py").write_text('config = {"providers": []}')

        return config_dir

    async def test_custom_config_is_used(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "MyCustomApp"
```

## Adding Additional Config Files

Use the `test_config` fixture directly to add extra configuration files:

```python
from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository


async def test_with_database_config(test_config: Path) -> None:
    # Add a database configuration file
    (test_config / "database.py").write_text('''
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": ":memory:",
        }
    }
}
''')

    # Create a new application to pick up the new config file
    app = Application(config_path=test_config)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()

        assert config.get("database.default").unwrap() == "sqlite"
        assert config.get("database.connections.sqlite.driver").unwrap() == "sqlite"
```

## Multiple Config Files in One Test

```python
from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository


async def test_with_multiple_config_files(test_config: Path) -> None:
    # Add cache configuration
    (test_config / "cache.py").write_text('''
config = {
    "driver": "memory",
    "ttl": 3600,
}
''')

    # Add logging configuration
    (test_config / "logging.py").write_text('''
config = {
    "level": "DEBUG",
    "format": "json",
}
''')

    # Add mail configuration
    (test_config / "mail.py").write_text('''
config = {
    "driver": "log",
    "from_address": "test@example.com",
}
''')

    app = Application(config_path=test_config)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()

        # All config files are loaded
        assert config.get("cache.driver").unwrap() == "memory"
        assert config.get("logging.level").unwrap() == "DEBUG"
        assert config.get("mail.driver").unwrap() == "log"
```

## Testing with Service Providers

When testing with custom service providers:

```python
from pathlib import Path

import pytest

from neva.arch import Application
from neva.config import ConfigRepository

from myapp.providers import MyServiceProvider


class TestWithCustomProviders:
    @pytest.fixture
    def test_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        (config_dir / "app.py").write_text('''
config = {
    "name": "TestApp",
    "debug": True,
}
''')

        # Register your custom providers
        (config_dir / "providers.py").write_text('''
from myapp.providers import MyServiceProvider

config = {
    "providers": [
        MyServiceProvider,
    ]
}
''')

        return config_dir

    async def test_custom_provider_is_loaded(
        self,
        application: Application,
    ) -> None:
        # MyService should now be available via DI
        my_service = application.make(MyService).unwrap()
        assert my_service is not None
```

## Environment-Specific Configurations

Create fixtures for different environment configurations:

```python
from pathlib import Path

import pytest

from neva.arch import Application


@pytest.fixture
def production_like_config(tmp_path: Path) -> Path:
    """Configuration that mimics production settings."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "app.py").write_text('''
config = {
    "name": "MyApp",
    "debug": False,
    "environment": "production",
}
''')

    (config_dir / "providers.py").write_text('config = {"providers": []}')

    return config_dir


@pytest.fixture
def development_config(tmp_path: Path) -> Path:
    """Configuration for development testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "app.py").write_text('''
config = {
    "name": "MyApp-Dev",
    "debug": True,
    "environment": "development",
}
''')

    (config_dir / "providers.py").write_text('config = {"providers": []}')

    return config_dir


async def test_production_config(production_like_config: Path) -> None:
    app = Application(config_path=production_like_config)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()
        assert config.get("app.debug").unwrap() is False


async def test_development_config(development_config: Path) -> None:
    app = Application(config_path=development_config)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()
        assert config.get("app.debug").unwrap() is True
```

## Reusable Configuration Helpers

For complex test suites, create helper functions:

```python
from pathlib import Path


def create_test_config(
    tmp_path: Path,
    *,
    app_name: str = "TestApp",
    debug: bool = True,
    environment: str = "testing",
    extra_config: dict[str, str] | None = None,
) -> Path:
    """Create a test configuration directory with customizable options."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "app.py").write_text(f'''
config = {{
    "name": "{app_name}",
    "debug": {debug},
    "environment": "{environment}",
}}
''')

    (config_dir / "providers.py").write_text('config = {"providers": []}')

    # Write any extra config files
    if extra_config:
        for filename, content in extra_config.items():
            (config_dir / filename).write_text(content)

    return config_dir


# Usage in tests
async def test_with_helper(tmp_path: Path) -> None:
    config_path = create_test_config(
        tmp_path,
        app_name="HelperApp",
        debug=False,
        extra_config={
            "cache.py": 'config = {"driver": "redis"}',
        }
    )

    app = Application(config_path=config_path)

    async with app.lifespan():
        config = app.make(ConfigRepository).unwrap()
        assert config.get("app.name").unwrap() == "HelperApp"
        assert config.get("cache.driver").unwrap() == "redis"
```
