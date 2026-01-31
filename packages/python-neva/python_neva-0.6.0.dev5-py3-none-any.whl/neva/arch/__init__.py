"""Architecture module providing core application framework components.

This module contains the main application class, service provider pattern,
and facade implementations.
"""

from neva.arch.app import App
from neva.arch.application import Application
from neva.arch.facade import Facade
from neva.arch.service_provider import (
    Bootable,
    ServiceProvider,
)

__all__ = [
    "App",
    "Application",
    "Bootable",
    "Facade",
    "ServiceProvider",
]
