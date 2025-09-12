from qpay_client.v2 import QPayClient
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest
from decimal import Decimal
import asyncio


client = QPayClient()


async def test():
    token = await client.get_token()

    print(token)

    response = await client.invoice_create(
        InvoiceCreateSimpleRequest(
            invoice_code="TEST_INVOICE",
            sender_invoice_no="1234567",
            invoice_receiver_code="terminal",
            invoice_description="test",
            sender_branch_code="SALBAR1",
            amount=Decimal(1500),
            callback_url="https://bd5492c3ee85.ngrok.io/payments?payment_id=1234567",
        )
    )

    print(response)


asyncio.run(test())
