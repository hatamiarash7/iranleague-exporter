"""Utils module for iranleague_exporter."""

import os


def get_env(key: str, default: str = "") -> str:
    """Get the value of an environment variable.

    Args:
        key (str): Name of the environment variable.
        default (str, optional): Default value if the variable is not set.

    Raises:
        OSError: If the environment variable is not set.

    Returns:
        str: Value of the environment variable or the default value.
    """
    value = os.getenv(key, default)
    if value is None or value == "":
        raise OSError(f"Environment variable '{key}' is not set.")
    return value
