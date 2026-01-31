"""Time support functions."""

import datetime as dt


def utcnow() -> dt.datetime:
    """Get current UTC datetime.

    Returns:
        Current UTC datetime.
    """
    return dt.datetime.now(dt.UTC)


def utcnow_ts() -> float:
    """Get current UTC timestamp.

    Returns:
        Current UTC timestamp.
    """
    return utcnow().timestamp()
