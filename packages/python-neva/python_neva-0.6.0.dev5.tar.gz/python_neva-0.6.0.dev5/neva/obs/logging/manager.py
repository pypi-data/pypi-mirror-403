"""Logging manager using structlog.

This module provides a logging manager that wraps structlog with sensible defaults
and integrations with the framework architecture
(correlation IDs, request context, etc.).
"""

from typing import final


from structlog.stdlib import get_logger


@final
class LogManager:
    """Manager for application logging using structlog.

    Configures and manages structured logging with support for different
    output formats, context binding, and integration with observability features.

    Attributes:
        logger: The bound structlog logger instance.
        debug_mode: Whether debug mode is enabled.

    """

    def __init__(
        self,
    ) -> None:
        """Initialize the logging manager."""
        self.logger = get_logger()

    def debug(self, message: str, **kwargs: object) -> None:
        """Log a debug message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: object) -> None:
        """Log an info message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: object) -> None:
        """Log a warning message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: object) -> None:
        """Log an error message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: object) -> None:
        """Log a critical message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs: object) -> None:
        """Log an exception with traceback.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
        self.logger.exception(message, **kwargs)
