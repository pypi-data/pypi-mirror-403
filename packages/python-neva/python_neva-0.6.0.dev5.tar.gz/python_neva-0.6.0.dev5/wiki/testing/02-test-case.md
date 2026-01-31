# TestCase Base Class

The `TestCase` class provides a convenient base for your test classes with automatic application injection.

## Overview

```python
from neva.testing import TestCase
```

When you extend `TestCase`, the `Application` instance is automatically injected into `self.app` before each test runs. This gives you direct access to the dependency injection container and all dependencies.

## Basic Usage

```python
from neva.testing import TestCase
from neva.arch import Application


class TestMyFeature(TestCase):
    async def test_app_is_available(self) -> None:
        # self.app is automatically injected
        assert isinstance(self.app, Application)
```

## Resolving Services

You may use the `make` method on the `app` attribute to resolve dependencies.

```python
from neva.testing import TestCase
from neva.config import ConfigRepository


class TestConfigAccess(TestCase):
    async def test_can_access_config(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        app_name = config.get("app.name").unwrap()
        assert app_name == "MyApp"

    async def test_config_with_default(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        value = config.get("app.missing_key", "default").unwrap()
        assert value == "default"
```

## Creating Custom Test Helpers

You may extend `TestCase` to add reusable helper methods for your test suite:

```python
from neva.testing import TestCase
from neva.config import ConfigRepository

from myapp.services import UserService


class MyAppTestCase(TestCase):
    """Custom base test case with application-specific helpers."""

    def get_user_service(self) -> UserService:
        """Helper to resolve the UserService."""
        return self.app.make(UserService).unwrap()

    def is_debug_mode(self) -> bool:
        """Check if the app is running in debug mode."""
        config = self.get_config()
        return config.get("app.debug", False).unwrap()


class TestUserFeatures(MyAppTestCase):
    async def test_create_user(self) -> None:
        user_service = self.get_user_service()

        user = await user_service.create(name="John", email="john@example.com")

        assert user.name == "John"
```

## When to Use TestCase vs Direct Fixtures

The `TestCase` class is particularly useful for organizing your test, save on
fixture boilerplate and leverage helper functions.
In some cases, you may prefer to use direct fixtures instead. This is useful
when writing quick-and-dirty one-off tests that will be iterated upon and reorganized.
