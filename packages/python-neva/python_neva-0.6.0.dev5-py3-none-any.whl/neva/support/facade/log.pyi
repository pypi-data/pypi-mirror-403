"""Type stub for Log facade."""

from typing import override

from neva.arch import Facade

class Log(Facade):
    @classmethod
    @override
    def get_facade_accessor(cls) -> type: ...
    @classmethod
    def debug(cls, message: str, **kwargs: object) -> None:
        """Log a debug message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """

    @classmethod
    def info(cls, message: str, **kwargs: object) -> None:
        """Log an info message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """

    @classmethod
    def warning(cls, message: str, **kwargs: object) -> None:
        """Log a warning message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """

    @classmethod
    def error(cls, message: str, **kwargs: object) -> None:
        """Log an error message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """

    @classmethod
    def critical(cls, message: str, **kwargs: object) -> None:
        """Log a critical message.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """

    @classmethod
    def exception(cls, message: str, **kwargs: object) -> None:
        """Log an exception with traceback.

        Args:
            message: The log message.
            **kwargs: Additional context for this log message.

        """
