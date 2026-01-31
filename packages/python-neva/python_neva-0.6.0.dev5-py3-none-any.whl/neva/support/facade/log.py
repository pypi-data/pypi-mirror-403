"""Log facade for static access to logging functionality."""

from typing import override

from neva.arch import Facade


class Log(Facade):
    """Log facade for static access to logging functionality."""

    @classmethod
    @override
    def get_facade_accessor(cls) -> type:
        from neva.obs import LogManager

        return LogManager
