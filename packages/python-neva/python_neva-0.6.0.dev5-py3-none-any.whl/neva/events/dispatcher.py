"""Base implementation of the event dispatcher."""

from typing import override
from neva import Ok, Result
from neva.events.event import Event
from neva.events.interface import EventBus
from neva.events.listener import EventListener


class BaseEventBus(EventBus):
    """Event dispatcher implementation."""

    @override
    async def dispatch(self, event: Event) -> Result[None, str]:
        return Ok(None)

    @override
    def listen[T: Event](
        self,
        event_cls: type[T],
        listener_cls: type[EventListener[T]],
    ) -> None:
        return
