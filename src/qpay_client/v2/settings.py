"""QPay client settings module."""

import logging
from dataclasses import dataclass
from typing import Union

from httpx import Limits, Timeout

from .defaults import MERCHANT_URL, SANDBOX_INVOICE_CODE, SANDBOX_PASSWORD, SANDBOX_URL, SANDBOX_USERNAME


@dataclass(frozen=True)
class QPaySettings:
    """QPay client settings."""

    username: str
    password: str
    invoice_code: str
    base_url: str

    timeout: Timeout = Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
    limits: Limits = Limits(max_connections=100, max_keepalive_connections=20)
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
        return cls(
            username=username,
            password=password,
            base_url=MERCHANT_URL,
            invoice_code=invoice_code,
            **kwargs,
        )
