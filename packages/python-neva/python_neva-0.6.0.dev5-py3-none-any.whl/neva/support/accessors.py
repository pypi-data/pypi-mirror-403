"""Utility functions for safe attribute access using Result types.

This module provides functional alternatives to Python's builtin attribute
access methods, returning Result types instead of raising exceptions.
"""

from typing import Any

from neva.support.results import Err, Ok, Result


def get_attr(obj: object, name: str) -> Result[Any, str]:
    """Get an attribute from an object, returning a Result instead of raising.

    This is a functional alternative to Python's builtin getattr that returns
    a Result type instead of raising an AttributeError.

    Args:
        obj: The object to get the attribute from.
        name: The name of the attribute to retrieve.

    Returns:
        Result containing the attribute value or an error message if not found.
    """
    if hasattr(obj, name):
        return Ok(getattr(obj, name))
    return Err(f"'{obj.__class__.__name__}' object has no attribute '{name}'")
