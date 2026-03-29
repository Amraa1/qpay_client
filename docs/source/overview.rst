Тойм
====

``qpay-client`` гэж юу вэ?
--------------------------

``qpay-client`` нь QPay-ийн REST API-д зориулсан Python клиент сан юм. Энэ сангийн зорилго нь
QPay-тай интеграц хийхэд давтагддаг дараах ажлуудыг нэг дор шийдэхэд оршино:

- authentication хийх
- access token болон refresh token-ийг удирдах
- request/response schema-уудыг баталгаажуулах
- sync болон async хоёр интерфейсээр нэг ижил endpoint-уудыг ашиглах
- network error болон серверийн түр зуурын алдаанд дахин оролдох

Гол экспорт
-----------

Ихэнх хэрэглээнд дараах объектууд хангалттай:

.. code-block:: python

    from qpay_client.v2 import AsyncQPayClient, QPayClient, QPaySettings

    from qpay_client.v2.schemas.enums import ObjectType
    from qpay_client.v2.schemas.schemas import (
        InvoiceCreateSimpleRequest,
        Offset,
        PaymentCheckRequest,
    )

Гол ойлголтууд:

- ``AsyncQPayClient``: ``asyncio``-д суурилсан асинхрон клиент
- ``QPayClient``: энгийн синхрон клиент
- ``QPaySettings``: base URL, credential, retry, timeout зэрэг тохиргооны объект

Яагаад хоёр клиенттэй вэ?
---------------------------

``AsyncQPayClient``-ийг дараах үед ашиглах нь тохиромжтой:

- FastAPI, Starlette, aiohttp зэрэг async framework ашиглаж байгаа бол
- нэгэн зэрэг олон request боловсруулах шаардлагатай бол

``QPayClient``-ийг дараах үед ашиглах нь тохиромжтой:

- Django management command, cron job, script зэрэг энгийн синхрон орчинд ажиллаж байгаа бол
- кодын урсгалыг аль болох энгийн байлгахыг хүсэж байвал

Тохиргоо үүсгэх
---------------

Sandbox орчин:

.. code-block:: python

    from qpay_client.v2 import QPaySettings

    settings = QPaySettings.sandbox()

Production орчин:

.. code-block:: python

    from qpay_client.v2 import QPaySettings

    settings = QPaySettings.production(
        username="your-merchant-username",
        password="your-merchant-password",
        invoice_code="YOUR_INVOICE_CODE",
    )

Мөн retry болон timeout-ийг override хийж болно:

.. code-block:: python

    settings = QPaySettings.sandbox(
        client_retries=2,
        client_delay=0.25,
        payment_check_retries=10,
    )

Клиентийн зан төлөв
--------------------

Энэ сан дараах ажлуудыг дотооддоо хийдэг:

- auth шаардлагатай endpoint дуудагдахаас өмнө токенээ шалгана
- access token хүчингүй болсон бол refresh хийхийг оролдоно
- network error болон тодорхой серверийн алдаанд дахин оролдоно
- ``payment_check`` дээр count ``0`` байвал тохиргооны дагуу polling хийнэ

Энэ нь QPay-тэй ажиллахад хэрэглэгч бүр token refresh, header бүрдүүлэх, retry хийх кодоо
дахин бичих шаардлагагүй гэсэн үг юм.

Импортын зөвлөгөө
-----------------

Клиент болон settings-ийг аль болох ``qpay_client.v2``-оос шууд импортлоорой:

.. code-block:: python

    from qpay_client.v2 import AsyncQPayClient, QPayClient, QPaySettings

Schema болон enum-уудыг дэд модулиас импортлоно:

.. code-block:: python

    from qpay_client.v2.schemas.enums import ObjectType
    from qpay_client.v2.schemas.schemas import PaymentCheckRequest
