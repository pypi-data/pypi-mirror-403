# Architecture Overview

Neva is a web framework that provides dependency injection, service providers, facades, and explicit error handling to help build scalable web applications.

## Core Concepts

The framework is built around five interconnected concepts:

- **Dependency Injection**: A central container manages service instantiation and resolution. Services are registered once and resolved on demand throughout the application.

- **Service Providers**: Modular units that register services into the container. They encapsulate the setup logic for a feature or component and can optionally manage async lifecycle (startup/shutdown).

- **Facades**: Static-like interfaces that proxy method calls to services resolved from the container. They provide convenient access to services without manually resolving dependencies.

- **Application Lifecycle**: A structured sequence of phases—initialization, startup, runtime, and shutdown—that ensures services are properly configured and cleaned up.

- **Result and Option Types**: Explicit error handling primitives that make success and failure states visible in the type system, avoiding implicit exceptions.

## How They Work Together

When the application starts, service providers register their services into the dependency injection container. During the startup phase, providers with lifecycle requirements initialize their resources (database connections, external services, etc.).

At runtime, facades provide a clean API to access these services. All operations that can fail return `Result` or `Option` types, making error handling explicit and composable.

On shutdown, resources are cleaned up in reverse order of initialization.

```
┌─────────────────────────────────────────────────────────────┐
│                        Application                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Provider A │    │  Provider B │    │  Provider C │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  DI Container                        │   │
│  │   ServiceA, ServiceB, ServiceC, ...                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         ▲                  ▲                  ▲             │
│         │                  │                  │             │
│  ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐     │
│  │  Facade A   │    │  Facade B   │    │  Facade C   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

- [Result and Option Types](06-result-option.md) — Start here to understand the error handling patterns used throughout the framework
- [Dependency Injection](02-dependency-injection.md) — Learn how services are registered and resolved
- [Service Providers](03-service-providers.md) — Understand how to organize service registration
- [Facades](04-facades.md) — See how to access services conveniently
- [Application Lifecycle](05-application-lifecycle.md) — Understand the startup and shutdown sequence
