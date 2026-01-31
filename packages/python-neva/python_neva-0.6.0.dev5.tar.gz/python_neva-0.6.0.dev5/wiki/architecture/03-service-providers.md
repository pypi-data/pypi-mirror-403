# Service Providers

Service providers are modular units that register services into the container. They encapsulate the setup logic for a feature or component, keeping your application organized and maintainable.

## Creating a Service Provider

A service provider extends the `ServiceProvider` base class and implements the `register()` method:

```python
from typing import Self
from neva.arch import ServiceProvider
from neva import Ok, Result

class EmailServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        self.app.bind(EmailService)
        return Ok(self)
```

The `register()` method returns a `Result[Self, str]`:
- `Ok(self)` indicates successful registration
- `Err("message")` indicates a failure with an explanation

### Handling Registration Failures

If registration can fail (e.g., missing configuration), return an `Err`:

```python
from neva import Ok, Err, Result

class PaymentServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        api_key = os.environ.get("PAYMENT_API_KEY")

        if not api_key:
            return Err("PAYMENT_API_KEY environment variable is required")

        def create_payment_service() -> PaymentService:
            return PaymentService(api_key=api_key)

        self.app.bind(create_payment_service)
        return Ok(self)
```

## Lifecycle Management

Some services require async setup and teardown—database connections, external API clients, background workers. The `Bootable` protocol enables this:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Self

from neva.arch import ServiceProvider
from neva.arch.service_provider import Bootable
from neva import Ok, Result

class DatabaseServiceProvider(ServiceProvider, Bootable):
    def register(self) -> Result[Self, str]:
        self.app.bind(DatabaseManager)
        return Ok(self)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        # Startup: initialize connections
        db = self.app.make(DatabaseManager).unwrap()
        await db.connect()

        yield  # Application runs here

        # Shutdown: close connections
        await db.disconnect()
```

The `lifespan()` method is an async context manager:
- Code before `yield` runs during application startup
- Code after `yield` runs during application shutdown

## Registering Providers

### Manual Registration

Register providers explicitly when creating the application:

```python
from neva.arch import Application

app = Application(config_path="./config")
app.register_provider(EmailServiceProvider)
app.register_provider(DatabaseServiceProvider)
```

### Auto-Registration via Configuration

Providers can be automatically registered by listing them in your configuration. In `config/providers.py`:

```python
from myapp.providers import (
    EmailServiceProvider,
    DatabaseServiceProvider,
    CacheServiceProvider,
)

config = {
    "providers": [
        EmailServiceProvider,
        DatabaseServiceProvider,
        CacheServiceProvider,
    ]
}
```

Or in `config/app.py`:

```python
config = {
    "name": "My Application",
    "providers": [
        # ... provider classes
    ]
}
```

The framework reads these during initialization and registers them automatically.

## Registration Order

Providers are registered in the order they are listed. Some providers depend on others being registered first. The framework guarantees:

1. `ConfigServiceProvider` is always registered first (provides configuration access)
2. Base providers (logging) are registered next
3. Auto-registered providers follow in listed order

If your provider depends on another, ensure it appears later in the list:

```python
config = {
    "providers": [
        DatabaseServiceProvider,      # First: sets up database
        RepositoryServiceProvider,    # Second: depends on database
        BusinessLogicServiceProvider, # Third: depends on repositories
    ]
}
```

## Accessing the Application

Within a provider, `self.app` gives access to the `Application` instance:

```python
class MyServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        # Bind services
        self.app.bind(MyService)

        # Resolve other services if needed
        config = self.app.make(ConfigRepository).unwrap()
        debug_mode = config.get("app.debug").unwrap_or(False)

        return Ok(self)
```

## Example: Complete Provider

Here's a complete example of a caching service provider with lifecycle management:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Self

from neva.arch import ServiceProvider
from neva.arch.service_provider import Bootable
from neva import Ok, Err, Result

class CacheServiceProvider(ServiceProvider, Bootable):
    """Provides caching capabilities to the application."""

    def register(self) -> Result[Self, str]:
        # Get cache configuration
        config = self.app.make(ConfigRepository)

        if config.is_err:
            return Err("ConfigRepository not available")

        cache_config = config.unwrap().get("cache")

        if cache_config.is_err:
            return Err("Cache configuration not found")

        # Create factory with configuration
        def create_cache() -> CacheManager:
            return CacheManager(**cache_config.unwrap())

        self.app.bind(create_cache)
        return Ok(self)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        cache = self.app.make(CacheManager).unwrap()

        # Startup
        await cache.connect()
        await cache.warm_up()

        yield

        # Shutdown
        await cache.flush()
        await cache.disconnect()
```

## See Also

- [Dependency Injection](02-dependency-injection.md) — How services are bound and resolved
- [Application Lifecycle](05-application-lifecycle.md) — When provider lifespans are called
- [Result and Option Types](06-result-option.md) — Understanding the `Result` return type
