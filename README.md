# qpay-client

![Tests](https://github.com/Amraa1/qpay_client/actions/workflows/test.yml/badge.svg)
![codecov](https://codecov.io/github/Amraa1/qpay_client/graph/badge.svg?token=TIZAF2HOWT)
![PyPI - Version](https://img.shields.io/pypi/v/qpay-client)
![Python](https://img.shields.io/pypi/pyversions/qpay-client.svg)
![PyPI - License](https://img.shields.io/pypi/l/qpay-client)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qpay-client)
![Documentation Status](https://readthedocs.org/projects/qpay-client/badge/?version=latest)

`qpay-client` нь QPay v2 API-тай Python орчноос холбогдохыг хялбарчлах клиент сан юм.
Энэ сан нь `async` болон `sync` клиент, schema validation, access token / refresh token удирдлага,
retry logic, мөн түгээмэл endpoint-уудын typed wrapper-уудыг агуулдаг.

Баримт бичиг: [qpay-client.readthedocs.io](https://qpay-client.readthedocs.io/mn/latest/)

QPay developer портал: [developer.qpay.mn](https://developer.qpay.mn)

## Гол боломжууд

- `AsyncQPayClient` болон `QPayClient` хоёуланг нь дэмжинэ
- Authentication, token refresh-ийг дотооддоо удирдана
- Pydantic schema ашиглан request/response-ийг шалгана
- Network error болон серверийн түр зуурын алдаанд retry хийж чадна
- `payment_check` polling-ийг тохиргоогоор удирдаж чадна
- `with` болон `async with` context manager дэмждэг
- QPay алдааг `QPayError` хэлбэрээр илүү ойлгомжтой буцаана

## Суулгах

`pip` ашиглах:

```bash
pip install qpay-client
```

`uv` ашиглах:

```bash
uv add qpay-client
```

`poetry` ашиглах:

```bash
poetry add qpay-client
```

## Хурдан эхлэх

### Async клиент

```python
from decimal import Decimal

from qpay_client.v2 import AsyncQPayClient, QPaySettings
from qpay_client.v2.schemas.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

async def main():
    async with AsyncQPayClient(settings=settings) as client:
        invoice = await client.invoice_create(
            InvoiceCreateSimpleRequest(
                sender_invoice_no="ORDER-1001",
                invoice_receiver_code="terminal",
                invoice_description="Туршилтын нэхэмжлэх",
                amount=Decimal("1500"),
                callback_url="https://example.com/qpay/callback?payment_id=ORDER-1001",
            )
        )

        print(invoice.invoice_id)
        print(invoice.qPay_shortUrl)
```

### Sync клиент

```python
from decimal import Decimal

from qpay_client.v2 import QPayClient, QPaySettings
from qpay_client.v2.schemas.schemas import InvoiceCreateSimpleRequest

settings = QPaySettings.sandbox()

with QPayClient(settings=settings) as client:
    invoice = client.invoice_create(
        InvoiceCreateSimpleRequest(
            sender_invoice_no="ORDER-1002",
            invoice_receiver_code="terminal",
            invoice_description="Sync туршилтын нэхэмжлэх",
            amount=Decimal("2500"),
            callback_url="https://example.com/qpay/callback?payment_id=ORDER-1002",
        )
    )

    print(invoice.invoice_id)
```

## Тохиргоо

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

### Retry болон delay тохируулах

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

## Төлбөр шалгах жишээ

```python
from qpay_client.v2.schemas.enums import ObjectType
from qpay_client.v2.schemas.schemas import Offset, PaymentCheckRequest

check_request = PaymentCheckRequest(
    object_type=ObjectType.invoice,
    object_id="YOUR_INVOICE_ID",
    offset=Offset(page_number=1, page_limit=100),
)

result = await client.payment_check(check_request)

if result.count > 0:
    print("Төлбөр олдлоо")
```

## FastAPI callback урсгал

`examples/quickstart.py` файлд callback endpoint-тэй энгийн async жишээ бий.

Үндсэн санаа нь:

1. Invoice үүсгэнэ
2. `invoice_id`-г өөрийн storage-д хадгална
3. QPay callback ирэх үед `payment_check` ашиглан төлбөрийг шалгана
4. Амжилттай боловсруулсны дараа `SUCCESS` буцаана

Жишээ файлыг ажиллуулах:

```bash
fastapi dev examples/quickstart.py
```

QPay callback endpoint-ийн хариу амжилттай байх үед HTTP 200 болон `SUCCESS` буцаах нь чухал.

## Импортын зөвлөмж

Клиент болон тохиргоог `qpay_client.v2`-оос импортлоорой:

```python
from qpay_client.v2 import AsyncQPayClient, QPayClient, QPaySettings, QPayError
```

Schema болон enum-уудыг дараах модулиудаас импортлоно:

```python
from qpay_client.v2.schemas.enums import ObjectType
from qpay_client.v2.schemas.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest
```

## Дэмжигддэг endpoint-ууд

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

## Анхаарах зүйлс

- `QPaySettings()`-ийг хоосноор нь дуудахгүй. `sandbox()` эсвэл `production()` factory ашиглана.
- Public endpoint-ууд auth-аа өөрсдөө шалгадаг тул request бүрийн өмнө токенээ гараар шинэчлэх шаардлагагүй.
- `payment_check` polling хийж болох тул timeout болон retry тохиргоогоо өөрийн хэрэглээнд тааруулж сонгоно.
- Production credential-ээ репод шууд хадгалахгүй байхыг зөвлөе.

## Лиценз

MIT License
