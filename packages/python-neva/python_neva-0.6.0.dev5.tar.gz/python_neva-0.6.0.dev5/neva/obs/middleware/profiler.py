"""Profiler middleware.

This module provides the ProfilerMiddleware class, which wraps an ASGI
application and profiles its execution. It generates a HTML report of the
profiling data and writes it to a file.

Uses the Pyinstrument library for profiling.
"""

from dataclasses import dataclass
from pyinstrument.profiler import AsyncMode
from starlette.types import ASGIApp, Receive, Scope, Send

from pyinstrument import Profiler

from neva.support import time


@dataclass
class ProfilerMiddleware:
    """Middleware for profiling ASGI applications.

    This middleware wraps an ASGI application and profiles its execution.
    It generates a HTML report of the profiling data and writes it to a file.
    """

    app: ASGIApp

    interval: float = 0.001
    async_mode: AsyncMode = "enabled"
    use_timing_thread: bool = False
    path: str = "./profiles"

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Wrap the application with profiling.

        Args:
            scope: The ASGI scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        correlation_id = scope["state"].get("correlation_id", None)
        filename = (
            f"profile_{correlation_id}"
            if correlation_id is not None
            else f"profile_{time.utcnow_ts()}"
        )
        self.profiler = Profiler(
            interval=self.interval,
            async_mode=self.async_mode,
            use_timing_thread=self.use_timing_thread,
        )

        self.profiler.start()
        try:
            await self.app(scope, receive, send)
        finally:
            self.profiler.stop()
            file_path = f"{self.path}/{filename}.html"
            self.profiler.write_html(file_path, timeline=True)
