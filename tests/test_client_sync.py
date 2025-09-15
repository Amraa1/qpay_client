import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx

from qpay_client.v2 import QPayClientSync
from qpay_client.v2.schemas import (
    InvoiceCreateSimpleRequest,
    Offset,
    PaymentListRequest,
)


def _json_string_body(payload: dict) -> str:
    return json.dumps(json.dumps(payload))


def test_base_url_selection_sync(sandbox_base, prod_base):
    c1 = QPayClientSync(is_sandbox=True)
    assert c1._base_url == sandbox_base

    c2 = QPayClientSync(is_sandbox=False)
    assert c2._base_url == prod_base

    c3 = QPayClientSync(base_url=prod_base)
    assert c3._base_url == prod_base


def test_auth_and_cached_token_sync(
    respx_auto_mock, token_payload, sandbox_base, frozen_time
):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )
    client = QPayClientSync(is_sandbox=True)

    # First call triggers auth
    token = client.get_token()
    assert token == token_payload["access_token"]

    # Still cached at t=0
    token2 = client.get_token()
    assert token2 == token


def test_token_refresh_sync(respx_auto_mock, token_payload, sandbox_base, frozen_time):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )
    respx_auto_mock.post(f"{sandbox_base}/auth/refresh").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    client = QPayClientSync(is_sandbox=True)
    client.get_token()
    frozen_time(4000)
    token_after = client.get_token()
    assert token_after == token_payload["access_token"]


def test_invoice_full_flow_sync(respx_auto_mock, token_payload, sandbox_base):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    invoice_payload = {
        "invoice_id": "inv-xyz",
        "qr_text": "QR",
        "qr_image": "base64",
        "qPay_shortUrl": "https://qpay.mn/s/xyz",
        "urls": [],
    }
    respx_auto_mock.post(f"{sandbox_base}/invoice").mock(
        return_value=httpx.Response(200, content=_json_string_body(invoice_payload))
    )
    respx_auto_mock.delete(f"{sandbox_base}/invoice/inv-xyz").mock(
        return_value=httpx.Response(200, json={})
    )

    client = QPayClientSync(is_sandbox=True)
    req = InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="123",
        invoice_receiver_code="terminal",
        invoice_description="desc",
        amount=Decimal(1),
        callback_url="https://cb",
    )
    resp = client.invoice_create(req)
    assert resp.invoice_id == "inv-xyz"

    cancelled = client.invoice_cancel("inv-xyz")
    assert cancelled == {}


def test_payment_paths_sync(respx_auto_mock, token_payload, sandbox_base):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    # payment.get -> dict JSON
    payment_payload = {
        "payment_id": 1,
        "payment_status": "PAID",
        "payment_amount": 100,
        "trx_fee": 2,
        "payment_currency": "MNT",
        "payment_wallet": "W",
        "payment_type": "CARD",
        "card_transactions": [],
        "p2p_transactions": [],
    }
    respx_auto_mock.get(f"{sandbox_base}/payment/pm-1").mock(
        return_value=httpx.Response(200, json=payment_payload)
    )

    # payment.list -> JSON string body
    pay_list_payload = {"count": 0, "paid_amount": 0, "rows": []}
    respx_auto_mock.post(f"{sandbox_base}/payment/list").mock(
        return_value=httpx.Response(200, content=_json_string_body(pay_list_payload))
    )

    # cancel/refund -> dict JSON
    respx_auto_mock.delete(f"{sandbox_base}/payment/cancel/pm-1").mock(
        return_value=httpx.Response(200, json={})
    )
    respx_auto_mock.delete(f"{sandbox_base}/payment/refund/pm-1").mock(
        return_value=httpx.Response(200, json={})
    )

    client = QPayClientSync(is_sandbox=True)

    got = client.payment_get("pm-1")
    assert str(got.payment_id) == "1"

    now = datetime.now(timezone.utc)
    req_list = PaymentListRequest(
        object_type="INVOICE",
        object_id="TEST_INVOICE",
        start_date=now - timedelta(days=30),
        end_date=now,
        offset=Offset(),
    )
    listed = client.payment_list(req_list)
    assert listed.count == 0

    cancelled = client.payment_cancel("pm-1")
    refunded = client.payment_refund("pm-1")
    assert cancelled == {}
    assert refunded == {}
