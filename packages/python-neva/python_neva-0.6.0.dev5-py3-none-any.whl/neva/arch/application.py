"""Base application for DI and facade injection."""

from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
import os
from pathlib import Path
from typing import Any, Callable, Self

import dishka
from dishka.integrations.fastapi import FastapiProvider

from neva import Err, Ok, Result
from neva.arch.service_provider import Bootable, ServiceProvider
from neva.arch.facade import Facade


class Application:
    """Base application for DI and facade injection."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize the application and its bindings.

        Args:
            config_path: Path to the configuration directory. Defaults to "./config"
                relative to the current working directory.

        Raises:
            RuntimeError: If the application fails to initialize.
        """
        from neva.config.repository import ConfigRepository
        from neva.config.provider import ConfigServiceProvider
        from neva.config.base_providers import base_providers

        self.providers: dict[type, ServiceProvider] = {}
        self.di_provider: dishka.Provider = dishka.Provider(scope=dishka.Scope.APP)

        configuration_path = config_path or os.getenv("NEVA_CONFIG_PATH", default=None)
        config_provider = ConfigServiceProvider(
            app=self,
            config_path=configuration_path,
        ).register()
        if config_provider.is_err:
            raise RuntimeError(
                f"Failed to register config provider: {config_provider.unwrap_err()}"
            )
        self.providers[ConfigServiceProvider] = config_provider.unwrap()

        self.register_providers(base_providers())
        _ = self.di_provider.provide(source=lambda: self, provides=Application)

        self.container: dishka.Container = dishka.make_container(self.di_provider)

        config_result: Result[ConfigRepository, str] = self.make(
            interface=ConfigRepository
        )
        match config_result:
            case Ok(config):
                self.config: ConfigRepository = config
                providers_from_file = config.get("providers.providers").unwrap_or([])
                providers_from_app = config.get("app.providers").unwrap_or([])
                providers: set[type[ServiceProvider]] = set(providers_from_file).union(
                    set(providers_from_app)
                )
                _ = self.register_providers(providers)
            case Err(e):
                raise RuntimeError(f"Failed to load configuration during boot: {e}")

        self.container = dishka.make_container(self.di_provider)

    def bind_to_fastapi(self) -> None:
        """Setup the FastapiProvider for FastAPI integration."""
        self.container = dishka.make_container(self.di_provider, FastapiProvider())

    def register(self, provider: type[ServiceProvider]) -> Result[ServiceProvider, str]:
        """Registers a service provider with the application.

        Returns:
            Result containing the registered provider instance or an error message.
        """
        if provider in self.providers:
            return Ok(self.providers[provider])

        return (
            provider(self)
            .register()
            .map(lambda p: self.providers.setdefault(provider, p))
        )

    def register_providers(self, providers: set[type[ServiceProvider]]) -> None:
        """Registers a set of providers."""
        for provider in providers:
            _ = self.register(provider)

    def bind(
        self,
        source: type | Callable[..., Any],
        *,
        interface: type | None = None,
        scope: dishka.BaseScope | None = None,
    ) -> None:
        """Binds a source to the container."""
        _ = self.di_provider.provide(
            source=source,
            scope=scope,
            provides=interface,
        )

    def make[T](self, interface: type[T]) -> Result[T, str]:
        """Resolve and instanciate a type from the container.

        Returns:
            Result containing the resolved type instance or an error message.
        """
        try:
            return Ok(self.container.get(interface))
        except Exception as e:
            return Err(f"Failed to resolve service '{interface.__name__}': {e}")

    @contextmanager
    def scope(self, scope: dishka.BaseScope | None = None) -> Iterator[Self]:
        """Enter a new scope.

        Yields:
            The application instance with the new scope.
        """
        parent = self.container
        with self.container(scope=scope) as container:
            self.container = container
            try:
                yield self
            finally:
                self.container = parent

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Wire the facades and providers."""
        Facade.set_facade_application(self)

        async with AsyncExitStack() as stack:
            for provider in self.providers.values():
                if isinstance(provider, Bootable):
                    await stack.enter_async_context(provider.lifespan())

            yield

        Facade.reset_facade_application()
