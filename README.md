# qpay-client

![Tests](https://github.com/Amraa1/qpay_client/actions/workflows/test.yml/badge.svg)
![codecov](https://codecov.io/github/Amraa1/qpay_client/graph/badge.svg?token=TIZAF2HOWT)
![PyPI - Version](https://img.shields.io/pypi/v/qpay-client)
![Python](https://img.shields.io/pypi/pyversions/qpay-client.svg)
![PyPI - License](https://img.shields.io/pypi/l/qpay-client)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qpay-client)
![Documentation Status](https://readthedocs.org/projects/qpay-client/badge/?version=latest)

> [Монгол хувилбар — README_MN.md](README_MN.md)

`qpay-client` is a production-ready Python client for the QPay v2 payment API — Mongolia's leading payment provider.
Built and used in production systems, it supports both async and sync clients, Pydantic v2-validated schemas, automatic
token management, retry logic with exponential backoff, and typed wrappers for all common endpoints.

Documentation: [qpay-client.readthedocs.io](https://qpay-client.readthedocs.io/en/latest/)

QPay developer portal: [developer.qpay.mn](https://developer.qpay.mn)

## Features

- Both `AsyncQPayClient` and `QPayClient` (sync) supported
- Authentication and token refresh managed automatically
- Request/response validation via Pydantic v2 schemas
- Retry logic for network errors and transient server failures
- Configurable `payment_check` polling with exponential backoff
- `with` and `async with` context manager support
- Structured `QPayError` exceptions with error codes and descriptions

## Installation

Using `pip`:

```bash
pip install qpay-client
```

Using `uv`:

```bash
uv add qpay-client
```

Using `poetry`:

```bash
poetry add qpay-client
```

## Quickstart

### Async client

```python
from decimal import Decimal

from qpay_client.v2 import AsyncQPayClient, QPaySettings
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

async def main():
    async with AsyncQPayClient(settings=settings) as client:
        invoice = await client.invoice_create(
            InvoiceCreateSimpleRequest(
                sender_invoice_no="ORDER-1001",
                invoice_receiver_code="terminal",
                invoice_description="Test invoice",
                amount=Decimal("1500"),
                callback_url="https://example.com/qpay/callback?payment_id=ORDER-1001",
            )
        )

        print(invoice.invoice_id)
        print(invoice.qPay_shortUrl)
```

### Sync client

```python
from decimal import Decimal

from qpay_client.v2 import QPayClient, QPaySettings
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

with QPayClient(settings=settings) as client:
    invoice = client.invoice_create(
        InvoiceCreateSimpleRequest(
            sender_invoice_no="ORDER-1002",
            invoice_receiver_code="terminal",
            invoice_description="Sync test invoice",
            amount=Decimal("2500"),
            callback_url="https://example.com/qpay/callback?payment_id=ORDER-1002",
        )
    )

    print(invoice.invoice_id)
```

## Configuration

### Sandbox

```python
from qpay_client.v2 import QPaySettings

settings = QPaySettings.sandbox()
```

### Production

```python
from qpay_client.v2 import QPaySettings

settings = QPaySettings.production(
    username="your-merchant-username",
    password="your-merchant-password",
    invoice_code="YOUR_INVOICE_CODE",
)
```

### Retry and delay settings

```python
settings = QPaySettings.sandbox(
    client_retries=2,
    client_delay=0.25,
    client_jitter=0.1,
    payment_check_retries=8,
    payment_check_delay=0.5,
    payment_check_jitter=0.2,
)
```

## Checking a payment

```python
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import Offset, PaymentCheckRequest

check_request = PaymentCheckRequest(
    object_type=ObjectType.invoice,
    object_id="YOUR_INVOICE_ID",
    offset=Offset(page_number=1, page_limit=100),
)

result = await client.payment_check(check_request)

if result.count > 0:
    print("Payment found")
```

## FastAPI callback flow

`examples/quickstart.py` contains a working async example with a QPay callback endpoint.

The general pattern is:

1. Create an invoice
2. Store the `invoice_id` in your database
3. On QPay callback, call `payment_check` to verify the payment
4. Return `"SUCCESS"` with HTTP 200

To run the example:

```bash
fastapi dev examples/quickstart.py
```

Returning HTTP 200 with body `"SUCCESS"` from your callback endpoint is required by QPay.

## Import paths

Import clients and settings from `qpay_client.v2`:

```python
from qpay_client.v2 import AsyncQPayClient, QPayClient, QPaySettings, QPayError
```

Import schemas and enums from their respective modules:

```python
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest
```

## Supported endpoints

### Authentication

- `token`
- `refresh`

### Invoice

- `invoice_get`
- `invoice_create`
- `invoice_cancel`

### Payment

- `payment_get`
- `payment_list`
- `payment_check`
- `payment_cancel`
- `payment_refund`

### Ebarimt

- `ebarimt_get`
- `ebarimt_create`

### Subscription

- `subscription_get`
- `subscription_cancel`

## Notes

- Never call `QPaySettings()` directly — use `sandbox()` or `production()` factory methods.
- All public endpoint methods check and refresh authentication automatically; no need to manage tokens manually.
- `payment_check` polls with exponential backoff — tune retry/delay settings to your use case.
- Do not commit production credentials to source control.

## License

MIT License
