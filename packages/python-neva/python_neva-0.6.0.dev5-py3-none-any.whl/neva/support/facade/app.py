"""Facade to the root application."""

from typing import override

from neva.arch import Facade


class App(Facade):
    """Facade to the root application."""

    @classmethod
    @override
    def get_facade_accessor(cls) -> type:
        from neva import arch

        return arch.Application
