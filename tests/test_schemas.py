from datetime import date, datetime
from decimal import Decimal

from qpay_client.v2.enums import ObjectTypeNum
from qpay_client.v2.schemas import (CreateInvoiceResponse, Currency,
                                    InvoiceCreateSimpleRequest, Offset,
                                    Payment, PaymentCheckRequest,
                                    PaymentStatus, QPayDeeplink, TokenResponse)


def test_token_response_alias():
    t = TokenResponse(
        token_type="bearer",
        access_token="a",
        expires_in=3600,
        refresh_token="r",
        refresh_expires_in=7200,
        scope="s",
        **{"not-before-policy": "0"},
        session_state="x",
    )
    assert t.not_before_policy == "0"


def test_invoice_create_simple_request_validation():
    r = InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="123",
        invoice_receiver_code="terminal",
        invoice_description="test",
        amount=Decimal("1500"),
        callback_url="https://example.com/cb",
    )
    assert r.amount == Decimal("1500")


def test_create_invoice_response_parsing():
    resp = CreateInvoiceResponse(
        invoice_id="inv-1",
        qr_text="QR",
        qr_image="base64",
        qPay_shortUrl="https://qpay.mn/s/abc",
        urls=[QPayDeeplink(name="app", description="desc", logo="l", link="https://")],
    )
    assert resp.qPay_shortUrl.startswith("https://")


def test_payment_and_check_request_models():
    req = PaymentCheckRequest(
        object_type=ObjectTypeNum.invoice, object_id="INV", offset=Offset()
    )
    assert req.object_type == ObjectTypeNum.invoice

    # Payment response model sanity
    p = Payment(
        payment_id=Decimal("1"),
        payment_status=PaymentStatus.paid,
        payment_amount=Decimal("200.0"),
        trx_fee=Decimal("2.0"),
        payment_currency=Currency.mnt,
        payment_wallet="W",
        payment_type="CARD",
        card_transactions=[],
        p2p_transactions=[],
    )
    assert p.payment_status == PaymentStatus.paid
