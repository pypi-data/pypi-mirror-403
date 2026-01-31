# ConfigRepository

The `ConfigRepository` class is the central storage for all configuration values. While most code accesses configuration through the `Config` facade, understanding the repository helps when you need more control.

## Core Methods

### get(key, default=None)

Retrieve a value using dot notation:

```python
from neva.config import ConfigRepository

repository = ConfigRepository()
repository.set("app.name", "MyApp")

name = repository.get("app.name").unwrap()  # "MyApp"
missing = repository.get("app.missing", default="fallback").unwrap()  # "fallback"
```

### set(key, value)

Set a value using dot notation. Intermediate dictionaries are created automatically:

```python
repository.set("database.connections.sqlite.driver", "sqlite")
# Creates: {"database": {"connections": {"sqlite": {"driver": "sqlite"}}}}
```

Returns `Err` if the path conflicts with an existing non-dict value:

```python
repository.set("app.name", "MyApp")
repository.set("app.name.sub", "value")  # Err: "app.name" is not a dictionary
```

### has(key)

Check if a key exists:

```python
if repository.has("cache.driver"):
    driver = repository.get("cache.driver").unwrap()
```

### all()

Get the entire configuration as a dictionary copy:

```python
config = repository.all()
# {"app": {"name": "MyApp"}, "database": {...}, ...}
```

### merge(key, items)

Merge a dictionary into a namespace:

```python
repository.merge("app", {
    "name": "MyApp",
    "version": "1.0.0",
})

repository.merge("app", {
    "debug": True,  # Added to existing "app" namespace
})

# Result: {"app": {"name": "MyApp", "version": "1.0.0", "debug": True}}
```

This is how the config loader populates the repository—each file's `config` dict is merged into its namespace.

## Freezing Configuration

After initialization, you can freeze the repository to prevent modifications:

```python
repository.freeze()

# Now all modifications fail
repository.set("app.name", "Other")  # Err: configuration is frozen
repository.merge("app", {"new": "value"})  # Err: configuration is frozen
```

Check frozen status:

```python
if repository.is_frozen():
    print("Configuration is locked")
```

Freezing is useful to catch accidental runtime modifications that could cause subtle bugs.

## Direct Resolution

You can resolve the repository directly from the container instead of using the facade:

```python
from neva.config import ConfigRepository

# In a route handler
@app.get("/config")
def get_config(config: FromDishka[ConfigRepository]):
    return {"app_name": config.get("app.name").unwrap()}

# Or manually from the application
config = application.make(ConfigRepository).unwrap()
```

This is useful when:
- Writing code that needs to be easily testable (inject a mock repository)
- Working outside the facade's availability window
- You need explicit dependency injection

## See Also

- [Accessing Configuration](03-accessing-configuration.md) — Using the Config facade
- [Loading Process](05-loading-process.md) — How the repository is populated
