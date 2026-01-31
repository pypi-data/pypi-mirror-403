# Configuration Loading Process

This page explains how configuration files are discovered, loaded, and made available to your application.

## Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Config Directory (e.g., ./config)                          │
│  ├── app.py                                                 │
│  ├── database.py                                            │
│  └── providers.py                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ConfigLoader                                               │
│  • Scans directory for *.py files                           │
│  • Imports each file as a Python module                     │
│  • Extracts the `config` dict from each module              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ConfigRepository                                           │
│  • Each file's config is merged into its namespace          │
│  • app.py → repository["app"]                               │
│  • database.py → repository["database"]                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  DI Container                                               │
│  • Repository bound and available for resolution            │
│  • Config facade can now access values                      │
└─────────────────────────────────────────────────────────────┘
```

## Step by Step

### 1. Application Initialization

When you create an `Application` or `App`, you specify the config path:

```python
from neva.arch import App

app = App(config_path="./config")
```

If not specified, it defaults to `./config` relative to the current working directory.

### 2. ConfigServiceProvider Registration

The `ConfigServiceProvider` is always registered first. It sets up lazy loading—configuration is not loaded immediately, but when first requested from the container.

### 3. File Discovery

When configuration is first resolved, the `ConfigLoader` scans the directory:

- Finds all `.py` files (excluding `__init__.py`)
- Each filename becomes a namespace key (`app.py` → `"app"`)

### 4. Module Import

Each file is dynamically imported as a Python module:

```python
# Internally, something like:
spec = importlib.util.spec_from_file_location("app", "/path/to/config/app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

This means your config files are executed as Python code. Any imports, computations, or side effects will run.

### 5. Config Extraction

The loader looks for a `config` attribute on each module:

```python
if hasattr(module, "config") and isinstance(module.config, dict):
    # Use this config
```

Files without a `config` dict are silently skipped.

### 6. Repository Population

Each file's config is merged into the repository under its namespace:

```python
repository.merge("app", app_module.config)
repository.merge("database", database_module.config)
repository.merge("providers", providers_module.config)
```

## Error Handling

### Missing Directory

If the config directory doesn't exist, a `RuntimeError` is raised during application initialization:

```python
app = App(config_path="/nonexistent")
# RuntimeError: Failed to load configuration: Directory not found
```

### Syntax Errors

If a config file has invalid Python syntax, loading fails with a descriptive error:

```python
# config/broken.py
config = {
    "name": "missing closing brace"

# RuntimeError: Syntax error in config file 'broken.py': ...
```

### Missing Config Attribute

Files without a `config` dict are skipped without error. This allows you to have helper modules in your config directory if needed (though it's not recommended).

### Invalid Config Type

If `config` exists but isn't a dict, the file is skipped:

```python
# config/invalid.py
config = "not a dict"  # Skipped, no error
```

## Loading Order

Files are loaded in filesystem order (typically alphabetical). The order usually doesn't matter since each file populates a separate namespace.

However, if you have interdependencies between config files (e.g., one file imports from another), ensure the imported file doesn't rely on configuration being loaded yet.

## When Loading Happens

Configuration is loaded lazily—the first time `ConfigRepository` is resolved from the container. This typically happens:

1. When the application reads `app.providers` to auto-register providers
2. When your code first calls `Config.get()`
3. When a service provider accesses configuration during `register()`

After the first resolution, the repository is cached in the container.

## See Also

- [Configuration Files](02-configuration-files.md) — How to structure your config files
- [ConfigRepository](04-config-repository.md) — The storage mechanism
- [Application Lifecycle](../../architecture/05-application-lifecycle.md) — When loading happens in the app lifecycle
