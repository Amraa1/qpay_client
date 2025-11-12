import asyncio
from decimal import Decimal

from fastapi import FastAPI, status

from qpay_client.v2 import QPayClient, QPaySettings
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import InvoiceCreateSimpleRequest, Offset, PaymentCheckRequest

# Qpay client settings
settings = QPaySettings()

# Init async client
client = QPayClient(settings=settings)

# init FastAPI app
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
