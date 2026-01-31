# Test Isolation

Neva's testing fixtures are designed to provide complete isolation between tests. Each test receives a fresh application instance with its own configuration, ensuring that tests don't affect each other.

## How Isolation Works

### Fresh Application Per Test

The `application` fixture has function scope, meaning a new `Application` instance is created for each test:

```python
from neva.arch import Application


class TestIsolation:
    async def test_first(self, application: Application) -> None:
        # This application instance is unique to this test
        application._custom_marker = "first"
        assert application._custom_marker == "first"

    async def test_second(self, application: Application) -> None:
        # This is a completely different application instance
        assert not hasattr(application, "_custom_marker")
```

### Fresh Configuration Per Test

The `test_config` fixture creates a new temporary directory for each test:

```python
from pathlib import Path


class TestConfigIsolation:
    async def test_first(self, test_config: Path) -> None:
        # Create a file in the config directory
        (test_config / "custom.py").write_text('config = {"key": "value"}')
        assert (test_config / "custom.py").exists()

    async def test_second(self, test_config: Path) -> None:
        # This test has a fresh config directory - no custom.py
        assert not (test_config / "custom.py").exists()
```

### Fresh Event Loop Per Test

With `asyncio_default_fixture_loop_scope = "function"`, each test gets its own event loop:

```python
import asyncio


class TestEventLoopIsolation:
    async def test_first(self) -> None:
        loop = asyncio.get_running_loop()
        # Store for comparison (in practice, don't do this)
        self.__class__.first_loop_id = id(loop)

    async def test_second(self) -> None:
        loop = asyncio.get_running_loop()
        # Different event loop instance
        assert id(loop) != self.__class__.first_loop_id
```

## Isolation with TestCase

The `TestCase` base class maintains isolation through its auto-injected `self.app`:

```python
from neva.testing import TestCase


class TestTestCaseIsolation(TestCase):
    async def test_first(self) -> None:
        # Modify the app instance
        self.app._test_marker = "modified"
        assert self.app._test_marker == "modified"

    async def test_second(self) -> None:
        # Fresh app instance - no marker
        assert not hasattr(self.app, "_test_marker")
```

## DI Container Isolation

Each application has its own dependency injection container. Services resolved in one test are independent of services in another:

```python
from neva.config import ConfigRepository
from neva.testing import TestCase


class TestDIIsolation(TestCase):
    async def test_first(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()
        # This is a specific ConfigRepository instance
        first_id = id(config)
        # Store for verification (demonstration only)
        self.__class__.first_config_id = first_id

    async def test_second(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()
        # Different instance from different container
        assert id(config) != self.__class__.first_config_id
```

## Why Isolation Matters

### Prevents Test Pollution

Without isolation, tests can affect each other:

```python
# BAD: Shared state between tests (hypothetical without isolation)
class TestWithoutIsolation:
    shared_app = None

    async def test_modifies_state(self) -> None:
        self.shared_app.some_setting = "modified"

    async def test_expects_clean_state(self) -> None:
        # FAILS! Previous test modified the state
        assert self.shared_app.some_setting == "default"
```

With Neva's fixtures, each test starts clean:

```python
# GOOD: Each test is isolated
class TestWithIsolation(TestCase):
    async def test_modifies_state(self) -> None:
        # Modify this test's app instance
        self.app._setting = "modified"

    async def test_expects_clean_state(self) -> None:
        # PASSES! This is a different app instance
        assert not hasattr(self.app, "_setting")
```

### Enables Parallel Test Execution

Isolation allows tests to run in parallel (with pytest-xdist) without conflicts:

```bash
# Run tests in parallel across 4 workers
pytest -n 4
```

### Makes Tests Deterministic

Each test produces the same result regardless of:
- Which tests ran before it
- The order tests are executed
- Whether tests run in parallel

## Best Practices

### Don't Share State Between Tests

```python
# BAD: Class-level state
class TestBadPattern:
    data = []

    async def test_one(self, application) -> None:
        self.data.append("one")  # Modifies shared state

    async def test_two(self, application) -> None:
        self.data.append("two")  # Order-dependent behavior
```

```python
# GOOD: Test-local state
class TestGoodPattern:
    async def test_one(self, application) -> None:
        data = ["one"]  # Local to this test
        assert data == ["one"]

    async def test_two(self, application) -> None:
        data = ["two"]  # Local to this test
        assert data == ["two"]
```

### Use Fixtures for Shared Setup

```python
import pytest

from neva.arch import Application


class TestWithSharedSetup:
    @pytest.fixture
    def user_data(self) -> dict:
        """Fixture provides fresh data for each test."""
        return {"name": "John", "email": "john@example.com"}

    async def test_one(self, application: Application, user_data: dict) -> None:
        user_data["name"] = "Modified"
        assert user_data["name"] == "Modified"

    async def test_two(self, application: Application, user_data: dict) -> None:
        # Fresh user_data, unaffected by test_one
        assert user_data["name"] == "John"
```

### Avoid Global State in Application Code

When writing application code, avoid patterns that break test isolation:

```python
# BAD: Global state in application code
_cache = {}

def get_cached_value(key: str) -> str:
    return _cache.get(key)

def set_cached_value(key: str, value: str) -> None:
    _cache[key] = value  # Persists across tests!
```

```python
# GOOD: State managed through DI
class CacheService:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value

# Register as scoped service - fresh instance per request/test
```

## Testing Multiple Applications

When you need to test interactions between multiple applications:

```python
from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository


async def test_multiple_apps(test_config: Path) -> None:
    # Create two separate application instances
    app1 = Application(config_path=test_config)
    app2 = Application(config_path=test_config)

    async with app1.lifespan():
        async with app2.lifespan():
            config1 = app1.make(ConfigRepository).unwrap()
            config2 = app2.make(ConfigRepository).unwrap()

            # These are different instances
            assert config1 is not config2

            # But have the same configuration values
            assert config1.get("app.name").unwrap() == config2.get("app.name").unwrap()
```
