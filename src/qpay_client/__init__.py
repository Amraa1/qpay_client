"""
Python client for the QPay API.

See the README.md for more information.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("qpay-client")
except PackageNotFoundError:  # pragma: no cover - source checkout without an install
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
