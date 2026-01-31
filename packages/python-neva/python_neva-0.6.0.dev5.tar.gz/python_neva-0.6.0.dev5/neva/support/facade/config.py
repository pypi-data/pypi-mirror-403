"""Configuration facade for static access to application configuration."""

from typing import override

from neva.arch import Facade


class Config(Facade):
    """Application configuration facade."""

    @classmethod
    @override
    def get_facade_accessor(cls) -> type:
        from neva.config import ConfigRepository

        return ConfigRepository
