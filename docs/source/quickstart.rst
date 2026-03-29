Хурдан эхлэл
============

Суулгах
-------

``qpay-client``-ийг өөрийн ашиглаж буй package manager-аар суулгана.

.. code-block:: bash

    pip install qpay-client

эсвэл

.. code-block:: bash

    uv add qpay-client

Async клиентээр эхлэх
---------------------

Асинхрон орчинд ``AsyncQPayClient`` ашиглана.

.. code-block:: python

    from decimal import Decimal

    from qpay_client.v2 import AsyncQPayClient, QPaySettings
    from qpay_client.v2.schemas.schemas import InvoiceCreateSimpleRequest

    settings = QPaySettings.sandbox()
    client = AsyncQPayClient(settings=settings)

    async def main():
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

Sync клиентээр эхлэх
--------------------

Синхрон скрипт, background job, cron зэрэгт ``QPayClient`` ашиглахад илүү тохиромжтой.

.. code-block:: python

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

Төлбөр шалгах жишээ
-------------------

``payment_check`` endpoint нь invoice-ийн төлбөр орж ирсэн эсэхийг шалгахад түгээмэл ашиглагдана.

.. code-block:: python

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

Production тохиргоо
-------------------

Production орчинд өөрийн merchant credential-ийг ашиглана.

.. code-block:: python

    settings = QPaySettings.production(
        username="your-merchant-username",
        password="your-merchant-password",
        invoice_code="YOUR_INVOICE_CODE",
    )

Анхаарах зүйлс
--------------

- ``QPaySettings()`` нь шууд default credential үүсгэдэггүй. ``sandbox()`` эсвэл ``production()`` factory ашиглана.
- ``invoice_create`` дээр request дотор ``invoice_code`` өгөхгүй орхивол ``settings.invoice_code`` автоматаар ашиглагдана.
- Public API endpoint-ууд auth-аа өөрсдөө шалгадаг тул request бүрийн өмнө токен гараар шинэчлэх шаардлагагүй.
- ``payment_check`` нь тохиргооны дагуу polling хийж болох тул ``payment_check_retries``-ийг өөрийн хэрэгцээнд тааруулж тохируулна.


