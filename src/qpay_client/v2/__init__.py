"""
qpay_client.v2.

This package provides the official `v2` client interfaces for integrating with
QPay`s API, consistent with the QPay v2 documentation.

Users are encouraged to **always import from `qpay_client.v2`** to ensure compatibility
with QPay`s current API version. Future versions may introduce breaking changes under
different namespaces (e.g., `v3`).

Exports:
    - AsyncQPayClient: Asynchronous client for interacting with QPay`s v2 API.
    - QPayClient: Synchronous client for interacting with QPay`s v2 API.

Example:
    >>> from qpay_client.v2 import AsyncQPayClient
    >>> async with AsyncQPayClient(...) as client:
    ...     invoice = await client.invoice_create(...)

    >>> from qpay_client.v2 import QPayClient
    >>> with QPayClient(...) as client:
    ...     invoice = client.invoice_create(...)

"""

from .clients.async_client import AsyncQPayClient
from .clients.client import QPayClient
from .error import QPayError
from .settings import QPaySettings

__all__ = [
    "AsyncQPayClient",
    "QPayClient",
    "QPayError",
    "QPaySettings",
]
