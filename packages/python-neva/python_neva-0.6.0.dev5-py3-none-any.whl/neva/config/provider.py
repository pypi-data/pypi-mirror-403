"""Configuration service provider.

This module provides the ConfigServiceProvider which is responsible for loading
configuration files and registering the ConfigRepository into the container.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Self, override


from neva import Ok, Result
from neva.arch import ServiceProvider
from neva.config.loader import ConfigLoader
from neva.config.repository import ConfigRepository

if TYPE_CHECKING:
    from neva.arch import Application


class ConfigServiceProvider(ServiceProvider):
    """Service provider for application configuration.

    Loads configuration files from the config directory and registers
    the ConfigRepository into the application container.

    Attributes:
        config_path: Path to the configuration directory.
        repository: The ConfigRepository instance after registration.

    """

    def __init__(
        self,
        app: "Application",
        config_path: str | Path | None = None,
    ) -> None:
        """Initialize the configuration service provider.

        Args:
            app: The application instance.
            config_path: Path to the configuration directory. Defaults to "./config".

        """
        self.config_path: Path = (
            Path(config_path) if config_path else Path.cwd() / "config"
        )
        self.repository: ConfigRepository | None = None
        super().__init__(app)

    @override
    def register(self) -> Result[Self, str]:
        repository = ConfigRepository()

        def load() -> ConfigRepository:
            loader = ConfigLoader(self.config_path)
            load_result = loader.load_all()

            if load_result.is_err:
                raise RuntimeError(
                    f"Failed to load configuration: {load_result.unwrap_err()}"
                )

            configs = load_result.unwrap()

            for namespace, config_dict in configs.items():
                merge_result = repository.merge(namespace, config_dict)
                if merge_result.is_err:
                    raise RuntimeError(merge_result.unwrap_err())
            return repository

        self.app.bind(load)
        self.repository = repository

        return Ok(self)
