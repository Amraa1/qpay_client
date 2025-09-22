import asyncio
from decimal import Decimal

from qpay_client.v2 import QPayClient
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest

client = QPayClient()


async def main():
    res = await client.invoice_create(
        InvoiceCreateSimpleRequest(
            invoice_code="TEST_INVOICE",
            sender_invoice_no="12345",
            invoice_receiver_code="12345",
            invoice_description="test",
            amount=Decimal(1234),
            callback_url="https://test.mn",
        )
    )
    
    print(res)


asyncio.run(main())
