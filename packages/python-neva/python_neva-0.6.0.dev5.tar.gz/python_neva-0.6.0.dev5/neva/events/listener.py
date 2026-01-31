"""Event listener protocol."""

import abc
from typing import Generic, TypeVar

from neva import Result
from neva.events.event import Event

T_contra = TypeVar("T_contra", bound=Event, contravariant=True)


class EventListener(Generic[T_contra], abc.ABC):
    """Event listener protocol."""

    @abc.abstractmethod
    async def handle(self, event: T_contra) -> Result[None, str]:
        """Handle an event.

        Returns:
            A result indicating whether the event was handled successfully.
        """
