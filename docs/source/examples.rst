Жишээнүүд
=========

FastAPI callback урсгал
-----------------------

Доорх жишээ нь invoice үүсгэж, callback endpoint дээрээ ``payment_check`` хийж төлбөрийн мэдээлэл авах
энгийн урсгалыг харуулна.

.. literalinclude:: ../../examples/quickstart.py
   :language: python
   :caption: examples/quickstart.py

Энэ жишээнд:

- sandbox тохиргоогоор ``AsyncQPayClient`` үүсгэнэ
- invoice үүсгэсний дараа ``invoice_id``-г өөрийн storage-д хадгална
- callback ирэх үед ``payment_check`` ашиглан тухайн invoice-ийн төлбөрийг шалгана

Context manager ашиглах
-----------------------

Синхрон клиент:

.. code-block:: python

    from qpay_client.v2 import QPayClient, QPaySettings

    settings = QPaySettings.sandbox()

    with QPayClient(settings=settings) as client:
        invoice = client.invoice_get("your-invoice-id")
        print(invoice.invoice_status)

Асинхрон клиент:

.. code-block:: python

    from qpay_client.v2 import AsyncQPayClient, QPaySettings

    settings = QPaySettings.sandbox()

    async with AsyncQPayClient(settings=settings) as client:
        invoice = await client.invoice_get("your-invoice-id")
        print(invoice.invoice_status)

Алдаа боловсруулах
------------------

QPay талын алдаа гарвал ``QPayError`` exception шидэгдэнэ.

.. code-block:: python

    from qpay_client.v2 import QPayError

    try:
        invoice = await client.invoice_get("missing-id")
    except QPayError as exc:
        print(exc)

Retry тохируулах
----------------

Network retry болон ``payment_check`` polling-ийг тохиргоогоор удирдаж болно.

.. code-block:: python

    from qpay_client.v2 import QPaySettings

    settings = QPaySettings.sandbox(
        client_retries=2,
        client_delay=0.25,
        client_jitter=0.1,
        payment_check_retries=8,
        payment_check_delay=0.5,
        payment_check_jitter=0.2,
    )
