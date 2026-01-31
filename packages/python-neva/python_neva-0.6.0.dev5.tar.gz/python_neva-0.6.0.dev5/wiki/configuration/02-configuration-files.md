# Configuration Files

Configuration files are Python modules that export a `config` dictionary. Each file in your config directory becomes a separate namespace.

## File Structure

A config file must define a `config` variable containing a dictionary:

```python
# config/app.py
config = {
    "name": "MyApp",
    "version": "1.0.0",
    "debug": False,
    "environment": "production",
}
```

The filename (without `.py`) becomes the namespace. Values from `app.py` are accessed with the `app.` prefix:

```python
Config.get("app.name")         # "MyApp"
Config.get("app.environment")  # "production"
```

## Directory Organization

A typical config directory might look like:

```
config/
├── app.py           # Application settings
├── database.py      # Database connections
├── cache.py         # Cache configuration
├── logging.py       # Logging settings
└── providers.py     # Service provider registration
```

Each file creates its own namespace:

| File | Namespace | Example Access |
|------|-----------|----------------|
| `app.py` | `app` | `Config.get("app.name")` |
| `database.py` | `database` | `Config.get("database.default")` |
| `cache.py` | `cache` | `Config.get("cache.driver")` |

## Nested Configuration

Dictionaries can be nested to any depth:

```python
# config/database.py
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": ":memory:",
            "options": {
                "timeout": 5,
                "check_same_thread": False,
            }
        },
        "postgres": {
            "driver": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "myapp",
            "user": "admin",
            "password": "secret",
        }
    }
}
```

Access nested values with dot notation:

```python
Config.get("database.default")                               # "sqlite"
Config.get("database.connections.sqlite.driver")             # "sqlite"
Config.get("database.connections.sqlite.options.timeout")    # 5
Config.get("database.connections.postgres.host")             # "localhost"
```

## Using Python Features

Since config files are Python modules, you can use imports, environment variables, and computed values:

```python
# config/app.py
import os

config = {
    "name": "MyApp",
    "debug": os.environ.get("DEBUG", "false").lower() == "true",
    "environment": os.environ.get("APP_ENV", "production"),
    "secret_key": os.environ["SECRET_KEY"],  # Required, will raise if missing
}
```

```python
# config/database.py
import os

config = {
    "default": os.environ.get("DB_CONNECTION", "sqlite"),
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": os.environ.get("DB_DATABASE", ":memory:"),
        },
        "postgres": {
            "driver": "postgres",
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "5432")),
            "database": os.environ.get("DB_DATABASE", "myapp"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", ""),
        }
    }
}
```

## Referencing Python Objects

Config values can be any Python object, including classes:

```python
# config/providers.py
from myapp.providers import (
    DatabaseServiceProvider,
    CacheServiceProvider,
    MailServiceProvider,
)

config = {
    "providers": [
        DatabaseServiceProvider,
        CacheServiceProvider,
        MailServiceProvider,
    ]
}
```

The application reads this list to auto-register service providers during initialization.

## Reserved Namespaces

Some namespaces have special meaning:

| Namespace | Purpose |
|-----------|---------|
| `app` | Application settings (`name`, `debug`, `title`, etc.) |
| `providers` | Service providers to auto-register (`providers` key) |

The `app` namespace is read during `App` initialization for FastAPI settings:

```python
# config/app.py
config = {
    "name": "MyApp",
    "title": "My Application API",      # FastAPI title
    "debug": False,                     # FastAPI debug mode
    "version": "1.0.0",                 # FastAPI version
    "openapi_url": "/openapi.json",     # OpenAPI schema URL
    "docs_url": "/docs",                # Swagger UI URL
    "redoc_url": "/redoc",              # ReDoc URL
}
```

## Files to Avoid

The loader ignores `__init__.py` files. Any other `.py` file will be loaded, so avoid placing non-config Python files in your config directory.

## See Also

- [Accessing Configuration](03-accessing-configuration.md) — Reading values in your application
- [Loading Process](05-loading-process.md) — How files are discovered and loaded
