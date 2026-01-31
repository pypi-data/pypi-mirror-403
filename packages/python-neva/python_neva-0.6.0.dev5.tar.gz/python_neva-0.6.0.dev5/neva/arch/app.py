"""Main application class.

This module provides the core App class that extends FastAPI with dependency
injection. DI is handled by the dependency injection container provided by
the Application class.
"""

from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

import fastapi
import dishka
from dishka.integrations.fastapi import setup_dishka
from starlette.routing import BaseRoute
from starlette.types import StatefulLifespan, StatelessLifespan

from neva import Result
from neva.arch.application import Application
from neva.arch.service_provider import ServiceProvider


class App(fastapi.FastAPI):
    """Main application class extending FastAPI."""

    def __init__(
        self,
        *,
        routes: list[BaseRoute] | None = None,
        middlewares: Sequence[type] | None = None,
        lifespan: StatelessLifespan["App"] | StatefulLifespan["App"] | None = None,
        config_path: str | Path | None = None,
    ) -> None:
        """Initialize the application.

        Args:
            routes: List of routes to register with the application.
            middlewares: Sequence of middleware to apply to the application.
            lifespan: Custom lifespan context manager for application lifecycle.
            config_path: Path to the configuration directory. Defaults to "./config"
                relative to the current working directory.

        """
        self.application: Application = Application(config_path=config_path)

        self._lifespan: StatelessLifespan["App"] | StatefulLifespan["App"] | None = (
            lifespan
        )
        config = self.application.config

        super().__init__(
            debug=config.get("app.debug", default=False).unwrap(),
            routes=routes,
            title=config.get("app.title", default="Neva Application").unwrap(),
            version=config.get("app.version", default="0.1.0").unwrap(),
            openapi_url=config.get("app.openapi_url", default="/openapi.json").unwrap(),
            docs_url=config.get("app.docs_url", default="/docs").unwrap(),
            redoc_url=config.get("app.redoc_url", default="/redoc").unwrap(),
            lifespan=self._create_lifespan(),
        )
        for middleware in middlewares or []:
            self.add_middleware(middleware)

        setup_dishka(self.application.container, app=self)

    def register(
        self,
        provider: type[ServiceProvider],
    ) -> Result[ServiceProvider, str]:
        """Registers a service provider with the application.

        Returns:
            Result containing the registered provider instance or an error message.
        """
        return self.application.register(provider=provider)

    def bind(
        self,
        source: type | Callable[..., Any],
        *,
        interface: type | None = None,
        scope: dishka.BaseScope | None = None,
    ) -> None:
        """Binds a source to the container."""
        self.application.bind(
            source=source,
            interface=interface,
            scope=scope,
        )

    def make[T](self, interface: type[T]) -> Result[T, str]:
        """Resolve and instanciate a type from the container.

        Returns:
            Result containing the resolved type instance or an error message.
        """
        return self.application.make(interface=interface)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None, None]:
        """Manage the lifecycle of the application."""
        async with self.application.lifespan():
            yield

    def _create_lifespan(
        self,
    ) -> StatelessLifespan["App"]:
        """Create the application lifespan function.

        Composes the framework's boot sequence with any user-defined lifespan
        context manager. This ensures the framework lifecycle runs first, then
        delegates to custom application lifecycle logic if provided.

        Returns:
            A stateless lifespan context manager for the application.

        """

        @asynccontextmanager
        async def composed_lifespan(app: App) -> AsyncIterator[None]:
            async with self.lifespan():
                if self._lifespan:
                    async with self._lifespan(app):
                        yield
                else:
                    yield

        return composed_lifespan
