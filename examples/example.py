import asyncio
from decimal import Decimal

from qpay_client.v2 import QPayClient
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

client = QPayClient()

response = asyncio.run(
    client.invoice_create(
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
)

print(response)
