"""Configuration loader for discovering and loading config files.

This module provides the ConfigLoader class which scans a configuration directory
for Python files and loads their configuration dictionaries into memory.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from neva import Err, Ok, Option, Result
from neva.support.accessors import get_attr


class ConfigLoader:
    """Loads configuration files from a directory.

    Scans a configuration directory for Python files (excluding __init__.py),
    imports them as modules, and extracts their 'config' dictionaries.

    Attributes:
        config_path: Path to the configuration directory.

    """

    config_path: Path

    def __init__(self, config_path: str | Path) -> None:
        """Initialize the configuration loader.

        Args:
            config_path: Path to the directory containing configuration files.

        """
        self.config_path = Path(config_path)

    def load_all(self) -> Result[dict[str, dict[str, Any]], str]:
        """Load all configuration files from the config directory.

        Discovers all Python files in the config directory (excluding __init__.py),
        loads them as modules, and extracts their 'config' dictionaries.

        Returns:
            Result containing a dictionary mapping filenames to config dictionaries,
            or an error message if loading fails.

        """
        if not self.config_path.exists():
            return Err(f"Config directory does not exist: {self.config_path}")

        if not self.config_path.is_dir():
            return Err(f"Config path is not a directory: {self.config_path}")

        configs: dict[str, dict[str, Any]] = {}

        config_files = [
            f for f in self.config_path.glob("*.py") if f.name != "__init__.py"
        ]

        for config_file in config_files:
            file_name = config_file.stem

            result = self._load_file(config_file, file_name)
            match result:
                case Err(e):
                    return Err(e)
                case Ok(config_dict):
                    if config_dict.is_some:
                        configs[file_name] = config_dict.unwrap()

        return Ok(configs)

    def _load_file(
        self, file_path: Path, module_name: str
    ) -> Result[Option[dict[str, Any]], str]:
        """Load a single configuration file.

        Imports the file as a Python module and attempts to extract
        its configuration dictionary.

        Args:
            file_path: Path to the configuration file.
            module_name: Name to use for the imported module.

        Returns:
            Result containing an Option with the config dict, or an error message.

        """
        try:
            spec = importlib.util.spec_from_file_location(
                f"neva.config.{module_name}", file_path
            )

            if spec is None or spec.loader is None:
                return Err(f"Could not load module spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            config_dict = self._extract_config(module)
            return Ok(config_dict)

        except SyntaxError as e:
            return Err(f"Syntax error in config file: {e}")
        except Exception as e:
            return Err(f"Error loading config: {e}")

    def _extract_config(self, module: ModuleType) -> Option[dict[str, Any]]:
        """Extract configuration dictionary from a module.

        Looks for a 'config' attribute in the module that is a dictionary.

        Args:
            module: The imported module.

        Returns:
            Option containing the config dictionary if found and valid.

        """
        return get_attr(module, "config").ok().filter(lambda x: isinstance(x, dict))
