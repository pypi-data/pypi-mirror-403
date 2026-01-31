"""Type stub for App facade."""

from typing import override

from neva import Result
from neva.arch import Facade

class App(Facade):
    @classmethod
    @override
    def get_facade_accessor(cls) -> type: ...
    @classmethod
    def make[T](cls, interface: type[T]) -> Result[T, str]:
        """Resolve an interface from the container by its alias.

        Attempts to retrieve and instantiate an object from the dependency
        injection container.

        Args:
            interface: The interface to resolve.

        Returns:
            Result containing the resolved service instance or an error message.

        """
