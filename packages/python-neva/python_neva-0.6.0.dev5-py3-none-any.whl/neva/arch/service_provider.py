"""Base classes and protocols for service providers.

This module defines the core abstractions for the service provider pattern.
Service providers are responsible for binding services into the dependency injection
container and optionally managing their lifecycle.
"""

import abc
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

from neva import Result

if TYPE_CHECKING:
    from neva.arch.application import Application


@runtime_checkable
class Bootable(Protocol):
    """Protocol for providers that need async startup/shutdown logic.

    Providers implementing this protocol can define lifecycle management through
    an async context manager. This is useful for services that need to establish
    connections, initialize resources, or perform cleanup on shutdown.
    """

    def lifespan(self) -> AbstractAsyncContextManager[None]:
        """Return an async context manager for the provider's lifecycle.

        Startup logic runs when entering the context, shutdown logic runs when
        exiting. This pattern is similar to FastAPI's lifespan pattern.

        Returns:
            An async context manager handling the provider's lifecycle.

        """
        ...


class ServiceProvider(abc.ABC):
    """Abstract base class for all service providers.

    Service providers are responsible for registering services into the application's
    dependency injection container. Each provider should implement the register method
    to bind its services.

    Attributes:
        app: The application instance.

    """

    app: "Application"

    def __init__(self, app: "Application") -> None:
        """Initialize the service provider.

        Args:
            app: The application instance.

        """
        self.app = app

    @abc.abstractmethod
    def register(self) -> Result[Self, str]:
        """Register services into the application container.

        This method should bind all services provided by this provider into
        the application's dependency injection container.

        Returns:
            Result containing the provider instance on success or an error message.

        """
        ...
