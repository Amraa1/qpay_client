Quickstart — Хурдан эхлэл
=========================

Суулгах
--------

Эхлээд шаардлагатай багцуудыг суулгана. `qpay-client` багц болон серверийн жишээг ажиллуулахад шаардлагатай `fastapi` болон `uvicorn`-ыг суулгаарай:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install --upgrade pip
    pip install qpay-client fastapi uvicorn

Жишээ код (async клиент)
------------------------

Доорх жишээ нь `examples/quickstart.py` файлд байрлуулсан, асинхрон клиент ашигласан энгийн пример юм. Энэ жишээ нь:
- QPay-д invoice үүсгэж qPay-ийн богино холбоосыг хэвлэх,
- callback замаар төлбөрийн төлөвийг шалгах талаар харуулж байна.

.. code-block:: python

    import asyncio
    from decimal import Decimal

    from fastapi import FastAPI, status

    from qpay_client.v2 import QPayClient
    from qpay_client.v2.enums import ObjectType
    from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest

    client = QPayClient(
        username="TEST_MERCHANT",  # or use your username
        password="123456",  # or use your password
        is_sandbox=True,  # or false for production
    )

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

Ажлуулах заавар
----------------

1. **Кодын зохион байгуулалт (зөвлөмж):** Жишээ файлыг сервер болон invoice үүсгэх логикыг зэрэг импорт хийх үед автоматаар ажиллахгүй болгохын тулд `asyncio.run(create_invoice())`-г файлын доод талд дараах байдлаар хамгаалж бичээрэй:

.. code-block:: python

    if __name__ == "__main__":
        asyncio.run(create_invoice())

   Ингэснээр та файлыг серверээр ажиллуулах үед (`uvicorn examples.quickstart:app`) `create_invoice()` автоматаар ажиллахгүй байна.

2. **Invoice үүсгэх (тест):** Хэрэв та зөвхөн invoice үүсгэхийг хүсвэл:

.. code-block:: bash

    python examples/quickstart.py

   (дээш заасан `if __name__ == "__main__":` тодорхойлогдсон бол энэ нь зөв ажиллана)

3. **Callback хүлээн авах (локал сервер):** QPay-ээс ирэх callback-уудыг хүлээн авахын тулд FastAPI апп-ыг ажиллуулна:

.. code-block:: bash

    uvicorn examples.quickstart:app --reload --host 0.0.0.0 --port 8000

   Харин хэрвээ та локал машинаар QPay-аас ирэх webhook-ийг шалгах бол `ngrok` зэрэг хэрэгслээр олон нийтийн URL үүсгэн callback URL-ээ түүнд зааж болно.

Чухал тайлбар, анхааруулга
-------------------------

- **Sandbox vs Production:** Жишээнд `is_sandbox=True` гэж тохируулсан. Бүтээгдэхүүнд шилжихэд `is_sandbox=False` болгох бөгөөд бодит `username`/`password` ашиглана. Бүтээгдэхүүний түлхүүрүүдээ нууцалж, VCS-д ил гаргахгүй байхыг анхаарна уу (орчуулах: `.env` эсвэл secret manager ашиглах).
- **Callback хариу:** QPay-ийн webhook нь амжилттай боловсруулсан тохиолдолд HTTP 200 болон биед `SUCCESS` мессеж (эсвэл таны QPay тохиргоонд заасан хариу) хүлээн авах хэрэгтэй. Жишээ дээр `return "SUCCESS"` байна.
- **Тест ба лог:** Жишээ нь `payment_database` нь дэмийн (in-memory) сан. Үйлдвэрийн орчинд өгөгдлийг тогтмол хадгалах (DB) тохиргоог ашиглана. Мөн лог бичих тохиргоог `logging` модуль ашиглан тохируулж, алдааны нөхцөлд тохиромжтой retry / error handling хийхийг зөвлөж байна.
- **Зөвлөмж:** Серверийг ажиллуулахдаа `create_invoice()`-г хост старт дээр автоматаар дуудаж invoice үүсгэхийг хүсэж байвал тус функцийг тусад нь CLI скрипт эсвэл background task хэлбэрээр зохион байгуулж, импорт үед биелэхгүй байхыг баталгаажуул.


