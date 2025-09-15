import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest

from qpay_client.v2 import QPayClient
from qpay_client.v2.enums import ObjectTypeNum
from qpay_client.v2.error import QPayError
from qpay_client.v2.schemas import (
    EbarimtCreateRequest,
    InvoiceCreateSimpleRequest,
    Offset,
    PaymentCheckRequest,
    PaymentListRequest,
)


def _json_string_body(payload: dict) -> str:
    """
    Your client uses `model_validate_json(response.json())` for several endpoints,
    which means `response.json()` must return a *string* containing JSON.
    We achieve that by returning a JSON-encoded string as the HTTP body.
    """
    return json.dumps(json.dumps(payload))


def test_base_url_selection(sandbox_base, prod_base):
    c1 = QPayClient(is_sandbox=True)
    assert c1._base_url == sandbox_base  # default

    c2 = QPayClient(is_sandbox=False)
    assert c2._base_url == prod_base

    c3 = QPayClient(base_url=prod_base)
    assert c3._base_url == prod_base


@pytest.mark.asyncio
async def test_auth_and_cached_token(
    respx_auto_mock, token_payload, sandbox_base, frozen_time
):
    # /auth/token -> dict JSON (TokenResponse.model_validate(...))
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    client = QPayClient(is_sandbox=True)

    # First call triggers /auth/token
    token = await client.get_token()
    assert token == token_payload["access_token"]

    # Still cached (time is 0), so no second call occurs
    token2 = await client.get_token()
    assert token2 == token


@pytest.mark.asyncio
async def test_token_refresh_flow(
    respx_auto_mock, token_payload, sandbox_base, frozen_time
):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )
    respx_auto_mock.post(f"{sandbox_base}/auth/refresh").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    client = QPayClient(is_sandbox=True)
    # obtain initial token (time=0)
    await client.get_token()

    # Move time forward past access expiry (expires_in - leeway = 3600-60 = 3540)
    frozen_time(4000)

    # Triggers refresh
    token_after = await client.get_token()
    assert token_after == token_payload["access_token"]


@pytest.mark.asyncio
async def test_invoice_create_and_cancel(respx_auto_mock, token_payload, sandbox_base):
    # Token
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    # Create invoice -> JSON string body path
    invoice_payload = {
        "invoice_id": "inv-123",
        "qr_text": "QR",
        "qr_image": "base64",
        "qPay_shortUrl": "https://qpay.mn/s/abc",
        "urls": [],
    }
    respx_auto_mock.post(f"{sandbox_base}/invoice").mock(
        return_value=httpx.Response(200, content=_json_string_body(invoice_payload))
    )

    # Cancel invoice -> plain dict JSON is fine (method returns response.json())
    respx_auto_mock.delete(f"{sandbox_base}/invoice/inv-123").mock(
        return_value=httpx.Response(200, json={})
    )

    client = QPayClient(is_sandbox=True)
    req = InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="123",
        invoice_receiver_code="terminal",
        invoice_description="desc",
        amount=Decimal(1),
        callback_url="https://cb",
    )

    created = await client.invoice_create(req)
    assert created.invoice_id == "inv-123"

    cancelled = await client.invoice_cancel("inv-123")
    assert cancelled == {}


@pytest.mark.asyncio
async def test_payment_check_get_list_cancel_refund(
    respx_auto_mock, token_payload, sandbox_base
):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    # payment.get -> dict JSON (Payment.model_validate(...))
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

    # payment.check -> JSON string body path
    pay_check_payload = {"count": 1, "paid_amount": 100, "rows": []}
    respx_auto_mock.post(f"{sandbox_base}/payment/check").mock(
        return_value=httpx.Response(200, content=_json_string_body(pay_check_payload))
    )

    # payment.list -> JSON string body path
    pay_list_payload = {"count": 0, "paid_amount": 0, "rows": []}
    respx_auto_mock.post(f"{sandbox_base}/payment/list").mock(
        return_value=httpx.Response(200, content=_json_string_body(pay_list_payload))
    )

    # payment.cancel / payment.refund -> plain dict JSON
    respx_auto_mock.delete(f"{sandbox_base}/payment/cancel/pm-1").mock(
        return_value=httpx.Response(200, json={})
    )
    respx_auto_mock.delete(f"{sandbox_base}/payment/refund/pm-1").mock(
        return_value=httpx.Response(200, json={})
    )

    client = QPayClient(is_sandbox=True)

    # GET payment
    got = await client.payment_get("pm-1")
    assert str(got.payment_id) == "1"

    # CHECK payment
    resp_check = await client.payment_check(
        PaymentCheckRequest(object_type=ObjectTypeNum.invoice, object_id="inv-id")
    )
    assert resp_check.count == 1
    assert resp_check.paid_amount == 100

    # LIST payments (create a valid request)
    now = datetime.now(timezone.utc)
    req_list = PaymentListRequest(
        object_type="INVOICE",
        object_id="TEST_INVOICE",
        start_date=now - timedelta(days=30),
        end_date=now,
        offset=Offset(),
    )
    resp_list = await client.payment_list(req_list)
    assert resp_list.count == 0

    # CANCEL / REFUND
    cancelled = await client.payment_cancel("pm-1")
    refunded = await client.payment_refund("pm-1")
    assert cancelled == {}
    assert refunded == {}


@pytest.mark.asyncio
async def test_ebarimt_create_and_get(respx_auto_mock, token_payload, sandbox_base):
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )

    ebarimt_payload = {
        "id": "e1",
        "ebarimt_by": "by",
        "g_wallet_id": "g1",
        "g_wallet_customer_id": "gc1",
        "ebarim_receiver_type": "CITIZEN",
        "ebarimt_receiver": "reg",
        "ebarimt_district_code": "011",
        "ebarimt_bill_type": "B",
        "g_merchant_id": "m1",
        "merchant_branch_code": "b1",
        "merchant_terminal_code": "t1",
        "merchant_staff_code": "s1",
        "merchant_register": 123,
        "g_payment_id": 456,
        "paid_by": "CARD",
        "object_type": "INVOICE",
        "object_id": "o1",
        "amount": 100,
        "vat_amount": 10,
        "city_tax_amount": 0,
        "ebarimt_qr_data": "qr",
        "ebarimt_lottery": "lot",
        "note": "",
        "ebarimt_status": "OK",
        "ebarimt_status_date": "2024-01-01T00:00:00",
        "tax_type": "VAT",
        "created_by": "c",
        "created_date": "2024-01-01T00:00:00",
        "updated_by": "u",
        "updated_date": "2024-01-01T00:00:00",
        "status": True,
    }

    # create -> JSON string body
    respx_auto_mock.post(f"{sandbox_base}/ebarimt/create").mock(
        return_value=httpx.Response(200, content=_json_string_body(ebarimt_payload))
    )
    # get -> JSON string body
    respx_auto_mock.get(f"{sandbox_base}/ebarimt/e1").mock(
        return_value=httpx.Response(200, content=_json_string_body(ebarimt_payload))
    )

    client = QPayClient(is_sandbox=True)
    created = await client.ebarimt_create(
        EbarimtCreateRequest(payment_id="pm-1", ebarimt_receiver_type="CITIZEN")
    )
    assert created.id == "e1"

    got = await client.ebarimt_get("e1")
    assert got.id == "e1"


@pytest.mark.asyncio
async def test_error_path_raises_qpay_error(
    respx_auto_mock, token_payload, sandbox_base
):
    # Token ok
    respx_auto_mock.post(f"{sandbox_base}/auth/token").mock(
        return_value=httpx.Response(200, json=token_payload)
    )
    # Endpoint returns error (must be a dict so _check_error has ["message"])
    error_payload = {"message": "INVALID"}
    respx_auto_mock.post(f"{sandbox_base}/invoice").mock(
        return_value=httpx.Response(400, json=error_payload)
    )

    client = QPayClient(is_sandbox=True)
    req = InvoiceCreateSimpleRequest(
        invoice_code="TEST",
        sender_invoice_no="1",
        invoice_receiver_code="t",
        invoice_description="d",
        amount=Decimal(1),
        callback_url="https://cb",
    )
    with pytest.raises(QPayError) as ei:
        await client.invoice_create(req)
    assert "INVALID" in str(ei.value)
