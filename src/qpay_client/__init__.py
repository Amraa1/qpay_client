"""
QPay Client
===========

Python client for the QPay v2 API.

- Handles authentication & token refresh automatically 🤖
- Supports both async (`QPayClient`) and sync (`QPayClientSync`) usage
- Pydantic schemas for request/response validation ✅
- Error handling with `QPayError`

👉 Always import from the versioned namespace (e.g. `qpay_client.v2`),
as QPay aligns its APIs with versioned docs.

Quick start (async)
-------------------
>>> from qpay_client.v2 import QPayClient
>>> from qpay_client.v2.schemas import InvoiceCreateSimpleRequest
>>> client = QPayClient(username="TEST_MERCHANT", password="123456", is_sandbox=True)
>>> invoice = await client.invoice_create(InvoiceCreateSimpleRequest(...))

Quick start (sync)
------------------
>>> from qpay_client.v2 import QPayClientSync
>>> client = QPayClientSync(username="MERCHANT", password="SECRET", is_sandbox=False)
>>> invoice = client.invoice_create(InvoiceCreateSimpleRequest(...))

See the README for full examples and callback flow.
"""
