"""Top-level package for iranleague exporter."""

import importlib.metadata
from pathlib import Path
from typing import Any

import toml

__package_version = "unknown"  # pylint: disable=C0103


def get_package_version() -> str:
    """Find the version of this package."""
    global __package_version

    if __package_version != "unknown":
        # We already set it at some point in the past,
        # so return that previous value without any
        # extra work.
        return __package_version

    try:
        # Try to get the version of the current package if
        # it is running from a distribution.
        __package_version = importlib.metadata.version("iranleague_exporter")
    except importlib.metadata.PackageNotFoundError:
        # Fall back on getting it from a local pyproject.toml.
        # This works in a development environment where the
        # package has not been installed from a distribution.

        pyproject_toml_file = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_toml_file.exists() and pyproject_toml_file.is_file():
            __package_version = toml.load(pyproject_toml_file)["tool"]["poetry"][
                "version"
            ]

    return __package_version


def __getattr__(name: str) -> Any:
    """Get package attributes."""
    if name in ("version", "__version__"):
        return get_package_version()

    raise AttributeError(f"No attribute {name} in module {__name__}.")


__app_name__ = "iranleague-exporter"
__description__ = "Export Prometheus metrics for Iran football league"
__version__ = f"v{get_package_version()}"
__author__ = "Arash Hatami <info@arash-hatami.ir>"
__epilog__ = "Made with :heart:  in [green]Iran[/green]"
__all__ = ["__version__"]
