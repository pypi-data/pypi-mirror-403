"""Logging service provider.

This module provides the LogServiceProvider which configures and registers
the logging manager into the application container.
"""

from typing import Self, override

from neva import Ok, Result
from neva.arch import ServiceProvider
from neva.obs.logging.manager import LogManager


class LogServiceProvider(ServiceProvider):
    """Service provider for application logging.

    Configures structlog-based logging and registers the LogManager
    into the application container.

    """

    @override
    def register(self) -> Result[Self, str]:
        self.app.bind(LogManager)

        return Ok(self)
