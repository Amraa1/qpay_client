"""QPay default values."""

from httpx import Limits, Timeout

SANDBOX_URL = "https://merchant-sandbox.qpay.mn/v2"
MERCHANT_URL = "https://merchant.qpay.mn/v2"

SANDBOX_USERNAME = "TEST_MERCHANT"
SANDBOX_PASSWORD = "123456"
SANDBOX_INVOICE_CODE = "TEST_INVOICE"


def default_timeout() -> Timeout:
    return Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)


def default_limits() -> Limits:
    return Limits(max_connections=100, max_keepalive_connections=20)
