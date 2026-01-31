"""Event/listener registry."""

from neva.events.event import Event
from neva.events.listener import EventListener


class EventRegistry:
    """Event/listener registry."""

    listeners: dict[type[Event], set[type[EventListener[Event]]]]

    def __init__(self) -> None:
        """Initialize the registry."""
        self.listeners = {}

    def register(
        self, event_cls: type[Event], listener_cls: type[EventListener[Event]]
    ) -> None:
        """Register a listener for an event."""
        self.listeners.setdefault(event_cls, set()).add(listener_cls)
