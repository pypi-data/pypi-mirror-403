"""Correlation middleware."""

from typing import Literal
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def is_valid_uuid(uuid_: str, version: Literal[1, 2, 3, 4] = 4) -> bool:
    """Check if a string is a valid UUID.

    Args:
        uuid_: The string to check.
        version: The UUID version to check.

    Returns:
        True if the string is a valid UUID, False otherwise.
    """
    try:
        return uuid.UUID(uuid_).version == version
    except ValueError:
        return False


CorrelationHeader = Literal["X-Request-ID", "X-Correlation-ID"]


@dataclass
class CorrelationMiddleware:
    """Middleware to add a correlation ID to outgoing requests."""

    app: ASGIApp

    header_name: CorrelationHeader = "X-Request-ID"
    generator: Callable[[], str] = field(default=lambda: uuid.uuid4().hex)
    validator: Callable[[str], bool] = field(default=is_valid_uuid)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Middleware entry point."""
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        header_value = headers.get("X-Request-ID".lower()) or headers.get(
            "X-Correlation-ID".lower()
        )
        if header_value is None or not self.validator(header_value):
            header_value = self.generator()

        scope["state"]["correlation_id"] = header_value

        async def handle_outgoing_request(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append(self.header_name, header_value)
            await send(message)

        await self.app(scope, receive, handle_outgoing_request)
        return
