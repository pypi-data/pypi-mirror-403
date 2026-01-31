"""Base classes and metaclasses for the facade pattern.

This module provides the infrastructure for Laravel-style facades.
Facades provide a static interface to services registered in the dependency
injection container, enabling convenient access without explicit dependency injection.
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from neva import Option, Result, from_optional
from neva.support.accessors import get_attr

if TYPE_CHECKING:
    from neva.arch.application import Application


class FacadeMeta(ABCMeta):
    """Metaclass that enables static method forwarding to underlying services.

    This metaclass intercepts attribute access on facade classes and forwards
    them to the actual service instance resolved from the application container.
    It provides the magic that makes facades work as static interfaces.
    """

    _app: ClassVar["Application | None"] = None

    def __getattr__(cls, name: str) -> object:
        """Intercept attribute access and forward to the resolved service.

        Args:
            name: The attribute name being accessed.

        Returns:
            The attribute value from the underlying service.

        Raises:
            AttributeError: If the attribute cannot be resolved from the service.
        """
        instance = cls._resolve_attribute(name)

        if instance.is_err:
            raise AttributeError(instance.unwrap_err())

        return instance.unwrap()

    def _resolve_attribute(cls, name: str) -> Result[Any, str]:
        """Try to get an attribute from the facade's underlying service.

        Args:
            name: The attribute name to resolve.

        Returns:
            Result containing the attribute value or an error message.

        """
        obj = cls.get_facade_root().and_then(lambda x: get_attr(x, name))
        return obj

    @classmethod
    @abstractmethod
    def get_facade_accessor(cls) -> type:
        """Return the service identifier in the container.

        This method must be implemented by each facade to specify which
        service from the container it represents.

        Returns:
            The class to resolve.

        """
        ...

    def get_facade_application(cls) -> Option["Application"]:
        """Get the application instance behind the facades.

        Returns:
            Option containing the application instance if set.

        """
        return cls._get_app()

    def get_facade_root(cls) -> Result[Any, str]:
        """Get the resolved service instance behind the facade.

        Returns:
            Result containing the service instance or an error message.

        """
        return (
            cls._get_app()
            .ok_or(
                f"A facade root (App instance) has not been set for {cls.__name__}. "
                + "Call Facade.set_facade_application(app) first."
            )
            .and_then(
                lambda x: cls._resolve_facade_instance(
                    app=x,
                    interface=cls.get_facade_accessor(),
                )
            )
        )

    def _get_app(cls) -> Option["Application"]:
        """Get the App instance from the facade.

        Returns:
            Option containing the application instance if set.

        """
        return from_optional(cls._app)

    def _resolve_facade_instance[T](
        cls,
        app: "Application",
        interface: type[T],
    ) -> Result[T, str]:
        """Resolve the service instance from the container.

        Args:
            app: The application instance.
            interface: The interface being facaded.

        Returns:
            Result containing the resolved service or an error message.

        """
        return app.make(interface)


class Facade(ABC, metaclass=FacadeMeta):
    """Base class for all facades providing static access to container services.

    Facades provide a convenient static interface to services bound in the
    application's dependency injection container. Each facade must implement
    get_facade_accessor to specify which service it represents.
    """

    _app: ClassVar["Application | None"]

    @classmethod
    @abstractmethod
    def get_facade_accessor(cls) -> type:
        """Return the service identifier in the container.

        This method must be implemented by each facade to specify which
        service from the container it represents.

        Returns:
            The class to resolve.

        """
        ...

    @classmethod
    def set_facade_application(cls, app: "Application") -> None:
        """Set the application instance for all facades.

        This is called automatically during application boot and should
        rarely need to be called manually.

        Args:
            app: The application instance.

        """
        cls._app = app

    @classmethod
    def reset_facade_application(cls) -> None:
        """Unset the application instance from all facades.

        This is called automatically during application shutdown and should
        rarely need to be called manually.
        """
        cls._app = None
