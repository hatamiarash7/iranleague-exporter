"""Utils module for iranleague_exporter."""

from __future__ import annotations

import logging
import os
from typing import overload


@overload
def get_env(key: str) -> str: ...


@overload
def get_env(key: str, default: str) -> str: ...


@overload
def get_env(key: str, default: None) -> str | None: ...


def get_env(key: str, default: str | None = "") -> str | None:
    """Get the value of an environment variable.

    Args:
        key: Name of the environment variable.
        default: Default value if the variable is not set.
            - If default is "" (empty string), raises OSError when not set.
            - If default is None, returns None when not set.
            - Otherwise, returns the default value when not set.

    Returns:
        Value of the environment variable or the default value.

    Raises:
        OSError: If the environment variable is not set and default is "".
    """
    value = os.getenv(key, default)

    # If value is None, return None (only when default was None)
    if value is None:
        return None

    # If value is empty and default was empty (meaning required), raise error
    if value == "" and default == "":
        raise OSError(f"Environment variable '{key}' is not set.")

    return value


class LogFilter(logging.Filter):
    """Filter to exclude health check and favicon from uvicorn access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Return False to exclude the log record."""
        message = record.getMessage()
        # Filter out /health and /favicon.ico requests
        return not any(path in message for path in ["/health", "/favicon.ico"])
