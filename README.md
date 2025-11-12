# QPay API Integration client

![Tests](https://github.com/Amraa1/qpay_client/actions/workflows/test.yml/badge.svg)
![codecov](https://codecov.io/github/Amraa1/qpay_client/graph/badge.svg?token=TIZAF2HOWT)
![PyPI - Version](https://img.shields.io/pypi/v/qpay-client)
![Python](https://img.shields.io/pypi/pyversions/qpay-client.svg)
![PyPI - License](https://img.shields.io/pypi/l/qpay-client)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qpay-client)
![Documentation Status](https://readthedocs.org/projects/qpay-client/badge/?version=latest)

QPay API integration made simpler and safer with data validation and auto token refresh.

This python package includes async and sync client. You can choose which ever suits your project.

Visit links:  
[Package document](https://qpay-client.readthedocs.io/mn/latest/)  
[QPay document](https://developer.qpay.mn)

## Features

- Client manages the access & refresh tokens.
- Both sync and async/await support.
- Data validation with Pydantic.
- Retries on payment check failures.
- Retries on server error >=500.
- Retries on network error.
- Clear QPay error code and with details.
- QPay Client settings with .env support.

## API coverage

All QPay APIs on their official document is supported.

### Authentication

- ✅ **token**
- ✅ **refresh**

### Invoice

- ✅ **Get invoice**
- ✅ **Create simple invoice**
- ✅ **Create detailed invoice**
- ✅ **Create subscription invoice**
- ✅ **Cancel invoice**

### Payment

- ✅ **get**
- ✅ **list**
- ✅ **check**
- ✅ **cancel**
- ✅ **refund**

### Ebarimt

- ✅ **get**
- ✅ **create**

### Subscription

- ✅ **Get subscription**
- ✅ **Cancel subscription**

## Installation

Using pip:

```bash
pip install qpay-client
```

Using poetry:

```bash
poetry add qpay-client
```

Using uv:

```bash
uv add qpay-client
```

## Usage

### Basic Example

Lets implement basic payment flow described in QPay developer document.

![Process diagram image](https://raw.githubusercontent.com/Amraa1/qpay_client/1ae82fced964d3959fee8e610d26903bcc075fa5/images/qpay_payment_process.svg "QPay process diagram")

**Important to note:**

> You are _free to implement the callback API's URI and query/params_ in anyway you want. But the callback you implement must return `Response(status_code = 200, body="SUCCESS")`.

### How to implement (Async example)

You don't have to worry about authentication and managing tokens. QPay client manages this behind the scene so you can focus on the important parts.

You can use any web framework. I am using [Fastapi](https://fastapi.tiangolo.com/) for the example just to create a simple callback API.

```python

import asyncio
from decimal import Decimal

from fastapi import FastAPI, status

from qpay_client.v2 import QPayClient, QPaySettings
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest

# Qpay client settings
settings = QPaySettings()

# Init async client
client = QPayClient(settings=settings)

# init FastAPI app
app = FastAPI()

# Just a dummy db
payment_database = {}


async def create_invoice():
    response = await client.invoice_create(
        InvoiceCreateSimpleRequest(
            invoice_code="TEST_INVOICE",
            sender_invoice_no="1234567",
            invoice_receiver_code="terminal",
            invoice_description="test",
            sender_branch_code="SALBAR1",
            amount=Decimal(1500),
            callback_url="https://api.your-domain.mn/payments?payment_id=1234567",
        )
    )

    # keep the qpay invoice_id in database, used for checking payment later!
    payment_database["1234567"] = {
        "id": "1234567",
        "invoice_id": response.invoice_id,
        "amount": Decimal(1500),
    }

    # Showing QPay invoice to the user ...
    print(response.qPay_shortUrl)


# You define the uri and query/param of your callback
# Your callback API must return
#   Response(status_code=200, body="SUCCESS")
@app.get("/payments", status_code=status.HTTP_200_OK)
async def qpay_callback(payment_id: str):
    data = payment_database.get(payment_id)
    if not data:
        raise ValueError("Payment not found")
    invoice_id = str(data["invoice_id"])
    response = await client.payment_check(
        PaymentCheckRequest(
            object_type=ObjectType.invoice, object_id=invoice_id, offset=Offset(page_number=1, page_limit=100)
        )
    )

    # do something with payment ...

    print(response)

    # This is important !
    return "SUCCESS"


if __name__ == "__main__":
    asyncio.run(create_invoice())


```

Run with fastapi.

`fastapi dev main.py`

### Sync client

There is also sync flavour of the client which you can simply use as follows. All the implementation in Async client is also in the Sync client.

```python
from qpay_client.v2 import QPayClientSync

client = QPayClientSync()

...
```

## License

MIT License
