"""Event dispatcher interface."""

from typing import Protocol

from neva import Result
from neva.events.event import Event
from neva.events.listener import EventListener


class EventBus(Protocol):
    """Event bus protocol."""

    async def dispatch(self, event: Event) -> Result[None, str]:
        """Dispatch an event."""
        ...

    def listen[T: Event](
        self,
        event_cls: type[T],
        listener_cls: type[EventListener[T]],
    ) -> None:
        """Register a listener for an event."""
        ...
