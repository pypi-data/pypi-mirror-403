# Facades

Facades provide a static-like interface to services in the container. Instead of manually resolving a service every time you need it, you can call methods directly on a facade class.

## How Facades Work

A facade acts as a proxy. When you call a method on a facade, it:

1. Looks up which service type it represents
2. Resolves that service from the container
3. Forwards the method call to the resolved instance
4. Returns the result

```python
from neva.support.facade import Config

# This call:
debug = Config.get("app.debug")

# Is equivalent to:
config_repository = app.make(ConfigRepository).unwrap()
debug = config_repository.get("app.debug")
```

The facade handles the resolution transparently, giving you a cleaner API.

## Built-in Facades

Neva provides several built-in facades:

### Config

Access application configuration:

```python
from neva.support.facade import Config

# Get a value with dot notation
app_name = Config.get("app.name").unwrap()

# Get with a default
debug = Config.get("app.debug", default=False).unwrap()

# Check if a key exists
if Config.has("database.host"):
    ...
```

### Log

Structured logging:

```python
from neva.support.facade import Log

Log.info("User logged in", user_id=123)
Log.warning("Rate limit approaching", current=95, max=100)
Log.error("Payment failed", order_id="abc", reason="insufficient funds")
```

### App

Access the application instance:

```python
from neva.support.facade import App

# Resolve a service
service = App.make(MyService).unwrap()
```

## Creating a Custom Facade

To create a facade for your own service, extend the `Facade` base class and implement `get_facade_accessor()`:

```python
from neva.arch import Facade

class Cache(Facade):
    @classmethod
    def get_facade_accessor(cls) -> type:
        return CacheManager
```

The `get_facade_accessor()` method returns the type that should be resolved from the container.

Now you can use the facade:

```python
# Instead of:
cache_manager = app.make(CacheManager).unwrap()
value = cache_manager.get("user:123")

# You can write:
value = Cache.get("user:123")
```

### Complete Example

```python
from neva.arch import Facade

class PaymentService:
    def charge(self, amount: float, currency: str) -> Result[str, str]:
        # Process payment
        return Ok("txn_123456")

    def refund(self, transaction_id: str) -> Result[None, str]:
        # Process refund
        return Ok(None)

class Payment(Facade):
    @classmethod
    def get_facade_accessor(cls) -> type:
        return PaymentService

# Usage
result = Payment.charge(99.99, "USD")
match result:
    case Ok(txn_id):
        print(f"Payment successful: {txn_id}")
    case Err(error):
        print(f"Payment failed: {error}")
```

## Resolution Chain

Understanding the resolution chain helps when debugging facade issues:

```
Payment.charge(99.99, "USD")
    │
    ▼
FacadeMeta.__getattr__("charge")
    │
    ▼
get_facade_root()
    ├── Get the Application instance
    └── Call app.make(PaymentService)
            │
            ▼
        Container resolves PaymentService
            │
            ▼
        Return the instance
    │
    ▼
Get "charge" attribute from instance
    │
    ▼
Return the bound method
    │
    ▼
Method is called with (99.99, "USD")
```

## Lifecycle Constraints

Facades only work during the application lifespan. Attempting to use a facade before startup or after shutdown raises an `AttributeError`:

```python
from neva.support.facade import Config

# Before app starts - raises AttributeError
Config.get("app.name")  # Error: facade root not set

async with app.lifespan():
    # During runtime - works
    Config.get("app.name")  # Ok

# After shutdown - raises AttributeError
Config.get("app.name")  # Error: facade root not set
```

This constraint exists because the container must be available to resolve services. The application sets up facade access when entering the lifespan and tears it down when exiting.

## When to Use Facades

**Use facades when:**
- You need quick access to a service in many places
- The code doesn't need to be easily testable (scripts, commands)
- You want cleaner, more readable code

**Prefer direct injection when:**
- Writing code that needs unit testing (inject mocks instead)
- Building reusable library code
- Working in route handlers (use `FromDishka` annotation)

## Type Hints and IDE Support

Due to Python's static type system limitations, facades don't provide full IDE autocompletion. The methods are resolved dynamically at runtime.

For better IDE support in critical code paths, consider using direct dependency injection instead.

## See Also

- [Dependency Injection](02-dependency-injection.md) — How services are resolved from the container
- [Application Lifecycle](05-application-lifecycle.md) — When facades become available
- [Service Providers](03-service-providers.md) — Registering the services that facades access
