"""
qpay_client.v2.

This package provides the official `v2` client interfaces for integrating with
QPay`s API, consistent with the QPay v2 documentation.

Users are encouraged to **always import from `qpay_client.v2`** to ensure compatibility
with QPay`s current API version. Future versions may introduce breaking changes under
different namespaces (e.g., `v3`).

Exports:
    - QPayClient: Asynchronous client for interacting with QPay`s v2 API.
    - QPayClientSync: Synchronous client for interacting with QPay`s v2 API.

Example:
    >>> from qpay_client.v2 import QPayClient
    >>> client = QPayClient(...)
    >>> invoice = await client.create_invoice(...)

    >>> from qpay_client.v2 import QPayClientSync
    >>> client = QPayClientSync(...)
    >>> invoice = client.create_invoice(...)

"""

from .client import QPayClient
from .error import QPayError
from .settings import QPaySettings
from .sync_client import QPayClientSync

__all__ = [
    "QPayClient",
    "QPayClientSync",
    "QPayError",
    "QPaySettings",
]
