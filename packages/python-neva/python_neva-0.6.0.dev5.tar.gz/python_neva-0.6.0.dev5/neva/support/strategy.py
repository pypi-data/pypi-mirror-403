"""Strategy pattern implementation helpers."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self, TypeVar

from neva import Nothing, Option, Some, from_optional
from neva.arch import Application
from neva.support.results import Err, Ok, Result


T = TypeVar("T")
StrategyFactory = Callable[["StrategyResolver[T]"], T]


class StrategyResolver[T](ABC):
    """Base Context class."""

    def __init__(self, app: Application) -> None:
        """Initialize the context with configuration access."""
        self._app = app
        self._strategies: dict[str, T] = {}
        self._registered: dict[str, StrategyFactory[T]] = {}

    @abstractmethod
    def default(self) -> Option[str]:
        """Determine the default strategy.

        Returns:
            An Option with the default strategy name
        """
        ...

    def use(self, name: str | None = None) -> Result[T, str]:
        """Resolve a strategy instance, creating and caching it if needed.

        Returns:
            Result containing the strategy instance or an error message.
        """
        tentative_name = from_optional(name)
        strategy_name = tentative_name if tentative_name.is_some else self.default()
        match strategy_name:
            case Nothing():
                return Err("No default strategy configured.")
            case Some(resolved_name):
                if resolved_name in self._strategies:
                    return Ok(self._strategies[resolved_name])

                return self.resolve(resolved_name).map(
                    lambda s: self._strategies.setdefault(resolved_name, s)
                )

    def resolve(self, name: str) -> Result[T, str]:
        """Resolve a strategy against available factories.

        Returns:
            Result containing the strategy instance or an error message.
        """
        if factory := self._registered.get(name):
            try:
                return Ok(factory(self))
            except Exception as e:
                return Err(f"Registered strategy '{name}' creation failed: {e}")
        return Err(f"No strategy registered with name '{name}'")

    def register(self, name: str, factory: StrategyFactory[T]) -> Self:
        """Register a strategy factory.

        Returns:
            Self for method chaining.
        """
        self._registered[name] = factory
        return self

    @property
    def strategies(self) -> dict[str, T]:
        """Return the created drivers."""
        return self._strategies

    @property
    def app(self) -> Application:
        """Return the underlying container."""
        return self._app

    def set_container(self, app: Application) -> None:
        """Set the underlying container."""
        self._app = app

    def clear(self) -> Self:
        """Clear cached strategy instances.

        Returns:
            Self for method chaining.
        """
        self._strategies.clear()
        return self
