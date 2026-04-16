"""QPay client settings module."""

import logging
from dataclasses import dataclass, field
from typing import Union

from httpx import Limits, Timeout

from .defaults import (
    MERCHANT_URL,
    SANDBOX_INVOICE_CODE,
    SANDBOX_PASSWORD,
    SANDBOX_URL,
    SANDBOX_USERNAME,
    default_limits,
    default_timeout,
)


@dataclass(frozen=True)
class QPaySettings:
    """
    Immutable configuration for QPay v2 clients.

    Prefer the factory methods over constructing this class directly:

    - ``QPaySettings.sandbox()`` — connects to the QPay sandbox with shared
      test credentials. All parameters are optional; useful for local development.
    - ``QPaySettings.production(username=..., password=..., invoice_code=...)``
      — connects to the live QPay merchant API with your own credentials.

    Retry and polling settings are independent:

    - ``client_retries`` / ``client_delay`` / ``client_jitter`` control how the
      HTTP transport retries network errors and 5xx responses.
    - ``payment_check_retries`` / ``payment_check_delay`` / ``payment_check_jitter``
      control how ``payment_check()`` polls until a payment is confirmed.

    ``token_leeway`` (default 60 s) is the window before token expiry in which
    the client proactively refreshes, preventing races at the boundary.
    """

    username: str
    password: str
    invoice_code: str
    base_url: str

    timeout: Timeout = field(default_factory=default_timeout)
    limits: Limits = field(default_factory=default_limits)
    log_level: Union[int, str] = logging.INFO

    token_leeway: float = 60.0
    client_retries: int = 5
    client_delay: float = 0.5
    client_jitter: float = 0.5
    payment_check_retries: int = 5
    payment_check_delay: float = 0.5
    payment_check_jitter: float = 0.5

    @classmethod
    def sandbox(
        cls,
        *,
        username: str = SANDBOX_USERNAME,
        password: str = SANDBOX_PASSWORD,
        invoice_code: str = SANDBOX_INVOICE_CODE,
        **kwargs,
    ) -> "QPaySettings":
        """
        Return settings pointed at the QPay sandbox environment.

        Credentials default to QPay's shared sandbox values, so calling
        ``QPaySettings.sandbox()`` with no arguments is enough for basic testing.
        Pass explicit ``username``, ``password``, or ``invoice_code`` to override.
        Any extra keyword arguments are forwarded to ``QPaySettings`` (e.g.
        ``payment_check_retries=3``).
        """
        return cls(
            username=username,
            password=password,
            base_url=SANDBOX_URL,
            invoice_code=invoice_code,
            **kwargs,
        )

    @classmethod
    def production(
        cls,
        *,
        username: str,
        password: str,
        invoice_code: str,
        **kwargs,
    ) -> "QPaySettings":
        """
        Return settings pointed at the live QPay merchant API.

        All three credential arguments are required. Any extra keyword arguments
        are forwarded to ``QPaySettings`` (e.g. ``client_retries=3``).
        """
        return cls(
            username=username,
            password=password,
            base_url=MERCHANT_URL,
            invoice_code=invoice_code,
            **kwargs,
        )
