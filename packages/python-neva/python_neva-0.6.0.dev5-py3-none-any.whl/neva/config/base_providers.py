"""Base service providers.

This module defines the core providers that are automatically registered.
These providers are essential for the framework
to function properly.
"""

from neva.arch import ServiceProvider
from neva.obs import LogServiceProvider


def base_providers() -> set[type[ServiceProvider]]:
    """Return the list of base service providers.

    These providers are automatically registered during application
    initialization and provide core framework functionality.

    Note: ConfigServiceProvider is registered separately in Application.__init__
    to allow custom config_path configuration.

    Returns:
        Set of service provider classes to register.

    """
    return {LogServiceProvider}
