# Application Lifecycle

The application lifecycle defines the sequence of phases from initialization to shutdown. Understanding this sequence helps you know when services are available and when to perform setup or cleanup tasks.

## Lifecycle Phases

```
┌─────────────────────────────────────────────────────────────┐
│                     INITIALIZATION                          │
│  • Create Application                                       │
│  • Load configuration                                       │
│  • Register service providers                               │
│  • Build DI container                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        STARTUP                              │
│  • Enable facade access                                     │
│  • Run provider lifespans (setup phase)                     │
│  • Run custom app lifespan (setup phase)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        RUNTIME                              │
│  • Handle requests                                          │
│  • Services are available                                   │
│  • Facades work                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       SHUTDOWN                              │
│  • Run custom app lifespan (cleanup phase)                  │
│  • Run provider lifespans (cleanup phase, reverse order)    │
│  • Disable facade access                                    │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Initialization

When you create an `Application` or `App` instance, the following happens:

```python
from neva.arch import App

app = App(config_path="./config")
```

1. **Configuration loading**: Config files are read from the specified directory
2. **ConfigServiceProvider registration**: Always registered first, provides access to configuration
3. **Base provider registration**: Core providers (logging) are registered
4. **Auto-registration**: Providers listed in `config/providers.py` or `config/app.py` are registered
5. **Container building**: The DI container is finalized with all bindings

At this point, services are registered but not yet initialized. Facades are not yet available.

## Phase 2: Startup

Startup occurs when the application lifespan context is entered. This happens automatically when running the app with a server:

```python
# When using uvicorn or similar
import uvicorn
uvicorn.run(app)  # Lifespan entered automatically
```

Or manually:

```python
async with app.lifespan():
    # Startup has completed
    ...
```

During startup:

1. **Facade access enabled**: The application instance is set on the `Facade` base class
2. **Bootable providers initialized**: Each provider implementing `Bootable` has its `lifespan()` entered
3. **Custom lifespan executed**: If you provided a custom lifespan, its setup phase runs

```python
from neva.arch import App
from contextlib import asynccontextmanager

@asynccontextmanager
async def my_lifespan(app):
    # This runs during startup
    print("Custom startup logic")
    yield
    # This runs during shutdown
    print("Custom shutdown logic")

app = App(config_path="./config", lifespan=my_lifespan)
```

### Provider Startup Order

Bootable providers are started in registration order:

```python
# In config/providers.py
config = {
    "providers": [
        DatabaseServiceProvider,  # Started first
        CacheServiceProvider,     # Started second
        SearchServiceProvider,    # Started third
    ]
}
```

This order matters when providers depend on each other. Ensure dependencies are listed before dependents.

## Phase 3: Runtime

Once startup completes, the application is ready to handle requests:

- All services are available via the container
- Facades work and resolve services correctly
- Route handlers receive injected dependencies
- Events can be dispatched and handled

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_service: FromDishka[UserService],
) -> dict:
    # Services are available, facades work
    Log.info("Fetching user", user_id=user_id)
    return user_service.get(user_id)
```

## Phase 4: Shutdown

Shutdown is triggered when the application receives a termination signal or when the lifespan context exits:

1. **Custom lifespan cleanup**: If provided, your custom lifespan's cleanup phase runs
2. **Provider cleanup**: Bootable providers have their `lifespan()` contexts exited in **reverse order**
3. **Facade access disabled**: The application instance is removed from the `Facade` base class

### Reverse Order Cleanup

Cleanup happens in reverse registration order to respect dependencies:

```python
# Registration order:
# 1. DatabaseServiceProvider
# 2. CacheServiceProvider
# 3. SearchServiceProvider

# Cleanup order:
# 1. SearchServiceProvider (depends on cache/db)
# 2. CacheServiceProvider  (depends on db)
# 3. DatabaseServiceProvider (no dependencies)
```

This ensures that services are cleaned up before their dependencies.

## Lifespan Composition

You can provide a custom lifespan that runs alongside provider lifespans:

```python
from contextlib import asynccontextmanager
from neva.arch import App

@asynccontextmanager
async def custom_lifespan(app):
    # Runs AFTER provider startups
    print("Starting background tasks...")
    task = asyncio.create_task(background_worker())

    yield

    # Runs BEFORE provider shutdowns
    print("Stopping background tasks...")
    task.cancel()
    await task

app = App(config_path="./config", lifespan=custom_lifespan)
```

The execution order is:

```
Startup:
  1. Facade access enabled
  2. Provider lifespans (setup)
  3. Custom lifespan (setup)

Shutdown:
  1. Custom lifespan (cleanup)
  2. Provider lifespans (cleanup, reverse order)
  3. Facade access disabled
```

## Error Handling During Lifecycle

### Startup Errors

If a provider's lifespan raises during startup, the application will fail to start. Previously started providers will have their cleanup run:

```python
class FaultyProvider(ServiceProvider, Bootable):
    @asynccontextmanager
    async def lifespan(self):
        raise RuntimeError("Failed to connect")
        yield

# If DatabaseProvider started successfully before FaultyProvider,
# DatabaseProvider's cleanup will run before the error propagates
```

### Shutdown Errors

Errors during shutdown are logged but don't prevent other providers from cleaning up. The framework ensures all providers get a chance to clean up their resources.

## Practical Example

Here's a complete example showing the lifecycle in action:

```python
from contextlib import asynccontextmanager
from neva.arch import App, ServiceProvider
from neva.arch.service_provider import Bootable
from neva.support.facade import Log
from neva import Ok

class DatabaseProvider(ServiceProvider, Bootable):
    def register(self):
        self.app.bind(Database)
        return Ok(self)

    @asynccontextmanager
    async def lifespan(self):
        Log.info("Connecting to database...")
        db = self.app.make(Database).unwrap()
        await db.connect()
        Log.info("Database connected")

        yield

        Log.info("Disconnecting from database...")
        await db.disconnect()
        Log.info("Database disconnected")

@asynccontextmanager
async def app_lifespan(app):
    Log.info("Application starting...")
    yield
    Log.info("Application stopping...")

app = App(config_path="./config", lifespan=app_lifespan)

# Output when running:
# INFO: Connecting to database...
# INFO: Database connected
# INFO: Application starting...
# (application handles requests)
# INFO: Application stopping...
# INFO: Disconnecting from database...
# INFO: Database disconnected
```

## See Also

- [Service Providers](03-service-providers.md) — Implementing the `Bootable` protocol
- [Facades](04-facades.md) — Understanding when facades are available
- [Dependency Injection](02-dependency-injection.md) — How the container is built during initialization
