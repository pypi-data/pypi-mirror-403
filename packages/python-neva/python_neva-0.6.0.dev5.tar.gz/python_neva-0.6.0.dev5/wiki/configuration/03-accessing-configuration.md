# Accessing Configuration

The `Config` facade provides a convenient way to read configuration values anywhere in your application.

## Basic Usage

Import the facade and call `get()` with a dot-notation key:

```python
from neva.support.facade import Config

app_name = Config.get("app.name").unwrap()
debug = Config.get("app.debug").unwrap()
```

The `get()` method returns a `Result` type. Use `unwrap()` to extract the value, or `unwrap_or()` to provide a default if the key doesn't exist.

## Providing Defaults

When a key might not exist, provide a default value:

```python
# Using the default parameter
timeout = Config.get("cache.timeout", default=3600).unwrap()

# Or using unwrap_or
timeout = Config.get("cache.timeout").unwrap_or(3600)
```

Both approaches return `3600` if `cache.timeout` is not defined.

## Dot Notation

Access nested values by chaining keys with dots:

```python
# Given this config:
# config = {
#     "database": {
#         "connections": {
#             "sqlite": {
#                 "driver": "sqlite",
#                 "options": {"timeout": 5}
#             }
#         }
#     }
# }

driver = Config.get("database.connections.sqlite.driver").unwrap()
# "sqlite"

timeout = Config.get("database.connections.sqlite.options.timeout").unwrap()
# 5
```

## Checking Key Existence

Use `has()` to check if a key exists before accessing it:

```python
if Config.has("features.beta_mode"):
    beta_enabled = Config.get("features.beta_mode").unwrap()
    if beta_enabled:
        enable_beta_features()
```

## Retrieving Entire Sections

Get an entire configuration section as a dictionary:

```python
# Get all database config
db_config = Config.get("database").unwrap()
# {"default": "sqlite", "connections": {...}}

# Get all connections
connections = Config.get("database.connections").unwrap()
# {"sqlite": {...}, "postgres": {...}}
```

## Getting All Configuration

Retrieve the entire configuration as a dictionary:

```python
all_config = Config.all()
# {"app": {...}, "database": {...}, "cache": {...}, ...}
```

## Error Handling

All `Config` methods return `Result` types. For detailed information on handling these, see [Result and Option Types](../../architecture/06-result-option.md).

Common patterns:

```python
# Unwrap (raises if key missing)
value = Config.get("app.name").unwrap()

# Unwrap with default
value = Config.get("app.name").unwrap_or("DefaultApp")

# Check before access
if Config.get("app.name").is_ok:
    value = Config.get("app.name").unwrap()
```

## Availability

The `Config` facade is only available during the application lifespan. Attempting to use it before startup or after shutdown will raise an `AttributeError`.

```python
# During application runtime — works
@app.get("/info")
def get_info():
    return {"app": Config.get("app.name").unwrap()}

# Outside lifespan — raises AttributeError
Config.get("app.name")  # Error: facade root not set
```

For more details on facades, see [Facades](../../architecture/04-facades.md).

## See Also

- [Configuration Files](02-configuration-files.md) — How to structure your config files
- [ConfigRepository](04-config-repository.md) — The underlying storage mechanism
- [Result and Option Types](../../architecture/06-result-option.md) — Error handling patterns
- [Facades](../../architecture/04-facades.md) — How facades work
