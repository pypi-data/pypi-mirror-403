"""String conversion utilities for case transformations.

This module provides utility functions for converting between different naming
conventions commonly used in Python code (snake_case and camelCase).
"""

import re


def snake2camel(snake: str) -> str:
    """Convert a snake_case string to camelCase.

    Args:
        snake: The snake_case string to convert.

    Returns:
        The converted string in camelCase.
    """
    camel = snake.title()
    camel = re.sub(r"([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    return camel


def snake2pascal(snake: str) -> str:
    """Convert a snake_case string to PascalCase.

    Args:
        snake: The snake_case string to convert.

    Returns:
        The converted string in PascalCase.

    """
    return re.sub(r"(^_*[A-Z])", lambda m: m.group(1).lower(), snake2camel(snake))


def camel2snake(camel: str) -> str:
    """Convert a camelCase or PascalCase string to snake_case.

    Args:
        camel: The camelCase or PascalCase string to convert.

    Returns:
        The converted string in snake_case.

    """
    snake = re.sub(r"([a-zA-Z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", camel)
    snake = re.sub(r"([a-z0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    return snake.lower()
