# Configuration in Providers

Service providers often need to read configuration to set up their services. This page shows common patterns for accessing configuration within providers.

## Accessing Config During Registration

In the `register()` method, resolve the `ConfigRepository` from the application:

```python
from typing import Self
from neva.arch import ServiceProvider
from neva.config import ConfigRepository
from neva import Ok, Err, Result

class CacheServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        # Resolve config from container
        config_result = self.app.make(ConfigRepository)

        if config_result.is_err:
            return Err("ConfigRepository not available")

        config = config_result.unwrap()

        # Read cache settings
        driver = config.get("cache.driver").unwrap_or("memory")
        ttl = config.get("cache.ttl").unwrap_or(3600)

        # Create factory with configuration
        def create_cache() -> CacheManager:
            return CacheManager(driver=driver, ttl=ttl)

        self.app.bind(create_cache)
        return Ok(self)
```

## Accessing Config During Lifespan

In the `lifespan()` method, the `Config` facade is available:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from neva.support.facade import Config, Log

class DatabaseServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        self.app.bind(DatabaseManager)
        return Ok(self)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        # Facade is available here
        db_config = Config.get("database").unwrap_or({})

        if not db_config:
            Log.warning("No database configuration found, skipping initialization")
            yield
            return

        # Initialize database
        db = self.app.make(DatabaseManager).unwrap()
        await db.connect(db_config)

        yield

        # Cleanup
        await db.disconnect()
```

## Conditional Service Registration

Register services only when configuration enables them:

```python
class FeatureFlagsProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        config = self.app.make(ConfigRepository).unwrap()

        # Only register beta features if enabled
        if config.get("features.beta_enabled").unwrap_or(False):
            self.app.bind(BetaFeatureService)

        # Only register analytics if configured
        if config.has("analytics.api_key"):
            api_key = config.get("analytics.api_key").unwrap()

            def create_analytics() -> AnalyticsService:
                return AnalyticsService(api_key=api_key)

            self.app.bind(create_analytics)

        return Ok(self)
```

## Validating Required Configuration

Fail registration if required configuration is missing:

```python
class PaymentServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        config = self.app.make(ConfigRepository).unwrap()

        # Check required keys
        api_key = config.get("payment.api_key")
        if api_key.is_err:
            return Err("Payment API key is required: set payment.api_key in config")

        webhook_secret = config.get("payment.webhook_secret")
        if webhook_secret.is_err:
            return Err("Payment webhook secret is required: set payment.webhook_secret in config")

        # All required config present, bind the service
        def create_payment_service() -> PaymentService:
            return PaymentService(
                api_key=api_key.unwrap(),
                webhook_secret=webhook_secret.unwrap(),
            )

        self.app.bind(create_payment_service)
        return Ok(self)
```

## Environment-Specific Configuration

Adjust behavior based on environment:

```python
class LoggingServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        config = self.app.make(ConfigRepository).unwrap()
        environment = config.get("app.environment").unwrap_or("production")

        def create_logger() -> Logger:
            if environment == "development":
                return Logger(level="DEBUG", format="pretty")
            elif environment == "testing":
                return Logger(level="WARNING", format="simple")
            else:
                return Logger(level="INFO", format="json")

        self.app.bind(create_logger)
        return Ok(self)
```

## Passing Full Config Sections

Sometimes a service needs an entire config section:

```python
class MailServiceProvider(ServiceProvider):
    def register(self) -> Result[Self, str]:
        config = self.app.make(ConfigRepository).unwrap()

        # Get entire mail config section
        mail_config = config.get("mail").unwrap_or({
            "driver": "smtp",
            "host": "localhost",
            "port": 25,
        })

        def create_mailer() -> Mailer:
            return Mailer(**mail_config)

        self.app.bind(create_mailer)
        return Ok(self)
```

## See Also

- [Service Providers](../../architecture/03-service-providers.md) — Service provider basics
- [Accessing Configuration](03-accessing-configuration.md) — General config access patterns
- [ConfigRepository](04-config-repository.md) — Direct repository usage
