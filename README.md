# QPay API Integration client

QPay API integration made simpler and safer with data validation and auto token refresh.

Package document at: https://pypi.org/project/qpay-client/  
QPay document at: https://developer.qpay.mn

Made with ❤️

## Features

- The client manages and refreshes access token
- Async/Await
- Pydantic data validation

## Installation

Using pip:

```bash
$ pip install qpay-client
```

Using poetry:

```bash
$ poetry install qpay-client
```

Using uv:

```bash
$ uv add qpay-client
```

## Usage

### Basic Example

```python
from decimal import Decimal
import asyncio

from qpay_client.v2 import QPayClient
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest


client = QPayClient()

response = asyncio.run(client.invoice_create(InvoiceCreateSimpleRequest(
  invoice_code = "TEST_INVOICE",
  sender_invoice_no = "1234567",
  invoice_receiver_code = "terminal",
  invoice_description = "test",
  sender_branch_code = "SALBAR1",
  amount = 1500,
  callback_url = "https://api.your-domain.mn/payments?payment_id=1234567",
)))

print(response)
```

### Methods

#### Invoice methods:

`invoice_create`

`invoice_cancel`

#### Payment methods:

`payment_get`

`payment_check`

`payment_cancel`

`payment_refund`

`payment_list`

#### Ebarimt methods:

`ebarimt_create`

`ebarimt_get`

## License

MIT License
