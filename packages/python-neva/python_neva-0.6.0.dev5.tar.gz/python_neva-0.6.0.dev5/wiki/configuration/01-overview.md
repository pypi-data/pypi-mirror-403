# Configuration Overview

Neva provides a file-based configuration system that loads Python files from a directory and makes their values accessible throughout your application.

## Key Features

- **Python files**: Configuration is written in plain Python, giving you the full power of the language (imports, environment variables, computed values)
- **Automatic loading**: All `.py` files in your config directory are discovered and loaded automatically
- **Namespace mapping**: Each file becomes a namespace (e.g., `app.py` → `app`, `database.py` → `database`)
- **Dot notation**: Access nested values with a simple syntax like `Config.get("database.connections.sqlite.driver")`
- **Type-safe access**: All operations return `Result` types for explicit error handling

## Quick Example

Given this directory structure:

```
config/
├── app.py
└── database.py
```

With these files:

```python
# config/app.py
config = {
    "name": "MyApp",
    "debug": True,
}

# config/database.py
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": ":memory:",
        }
    }
}
```

You can access values like this:

```python
from neva.support.facade import Config

app_name = Config.get("app.name").unwrap()  # "MyApp"
driver = Config.get("database.connections.sqlite.driver").unwrap()  # "sqlite"
```

## Next Steps

- [Configuration Files](02-configuration-files.md) — How to structure your config files
- [Accessing Configuration](03-accessing-configuration.md) — Reading values in your application
- [ConfigRepository](04-config-repository.md) — The underlying storage mechanism
- [Loading Process](05-loading-process.md) — How files are discovered and loaded
- [Configuration in Providers](06-configuration-in-providers.md) — Using config in service providers
