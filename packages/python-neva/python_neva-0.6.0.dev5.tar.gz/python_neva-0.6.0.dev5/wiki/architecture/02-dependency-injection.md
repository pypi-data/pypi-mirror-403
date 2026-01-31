# Dependency Injection

Dependency injection (DI) is a design pattern where objects receive their dependencies from an external source rather than creating them internally. Neva provides a central container that manages service instantiation and resolution.

## The Application Container

The `Application` class serves as the DI container. It holds all registered services and provides methods to bind and resolve them.

```python
from neva.arch import Application

# Create the application with a config directory
app = Application(config_path="./config")

# The container is now ready to use
```

## Binding Services

Services are registered into the container using the `bind()` method. There are two primary binding patterns:

### Class Binding

Bind a class directly. The container will instantiate it when resolved:

```python
class EmailService:
    def send(self, to: str, subject: str, body: str) -> None:
        # Send email logic
        ...

# Register the service
app.bind(EmailService)
```

### Factory Binding

Bind a callable that returns the service instance. Useful when initialization requires configuration or other dependencies:

```python
class DatabaseConnection:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

def create_database_connection() -> DatabaseConnection:
    return DatabaseConnection(host="localhost", port=5432)

# Register using a factory
app.bind(create_database_connection)
```

### Interface Binding

Bind a concrete implementation to an abstract interface:

```python
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    def notify(self, message: str) -> None: ...

class SlackNotificationService(NotificationService):
    def notify(self, message: str) -> None:
        # Send to Slack
        ...

# Bind implementation to interface
app.bind(SlackNotificationService, interface=NotificationService)
```

## Resolving Services

Services are resolved from the container using the `make()` method. This returns a `Result` type to handle resolution failures explicitly:

```python
from neva import Ok, Err

match app.make(EmailService):
    case Ok(service):
        service.send("user@example.com", "Hello", "Welcome!")
    case Err(error):
        print(f"Failed to resolve EmailService: {error}")
```

For cases where you're confident the service exists, you can use `unwrap()`:

```python
email_service = app.make(EmailService).unwrap()
```

Or provide a fallback with `unwrap_or()`:

```python
email_service = app.make(EmailService).unwrap_or(default_email_service)
```

## Dependency Resolution in Routes

When using Neva with FastAPI, dependencies can be injected directly into route handlers. The framework integrates with FastAPI's dependency injection system:

```python
from neva.arch import App
from dishka.integrations.fastapi import FromDishka

app = App(config_path="./config")

@app.get("/send-welcome")
async def send_welcome(
    email_service: FromDishka[EmailService],
) -> dict:
    email_service.send("user@example.com", "Welcome", "Hello!")
    return {"status": "sent"}
```

The `FromDishka` annotation tells the framework to resolve the dependency from the container for each request.

## Best Practices

1. **Bind abstractions**: When possible, bind concrete implementations to abstract interfaces. This makes testing and swapping implementations easier.

2. **Use factories for complex setup**: If a service requires configuration or multiple steps to initialize, use a factory function.

3. **Handle resolution failures**: Always consider what happens if a service cannot be resolved. Use `Result` pattern matching or provide sensible defaults.

4. **Register early**: Services should be registered during application initialization, typically in service providers (see [Service Providers](03-service-providers.md)).

## See Also

- [Service Providers](03-service-providers.md) — Organize service registration into modular units
- [Facades](04-facades.md) — Access services through static-like interfaces
- [Result and Option Types](06-result-option.md) — Understand the `Result` type returned by `make()`
