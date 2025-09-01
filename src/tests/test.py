from qpay_client.v2.qpay_client import qpay_client
from qpay_client.v2.schemas import InvoiceCreateRequest, InvoiceCreateSimpleRequest
import asyncio

# print(asyncio.run(qpay_client.headers))

print(
    qpay_client._access_token_expiry,
    qpay_client._access_token,
    qpay_client._refresh_token_expiry,
)

print(
    asyncio.run(
        qpay_client.invoice_create(
            InvoiceCreateSimpleRequest.model_validate(
                {
                    "invoice_code": "TEST_INVOICE",
                    "sender_invoice_no": "1234567",
                    "invoice_receiver_code": "terminal",
                    "invoice_description": "test",
                    "sender_branch_code": "SALBAR1",
                    "amount": 100,
                    "callback_url": "https://bd5492c3ee85.ngrok.io/payments?payment_id=1234567",
                }
            )
        )
    )
)
