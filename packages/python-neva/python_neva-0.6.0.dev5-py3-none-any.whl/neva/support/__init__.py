"""Support utilities.

This module provides utility types and functions including Result and Option
types for error handling, string conversions, and safe attribute access.
"""

from neva.support.results import (
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    UnwrapError,
    from_optional,
)

__all__ = [
    "Err",
    "Nothing",
    "Ok",
    "Option",
    "Result",
    "Some",
    "UnwrapError",
    "from_optional",
]
