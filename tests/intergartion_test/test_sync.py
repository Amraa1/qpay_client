import os
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

# ---- imports from your package; adjust path if needed
from qpay_client.v2 import QPayClientSync, QPayError, QPaySettings
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import (
    InvoiceCreateSimpleRequest,
    Offset,
    PaymentCancelRequest,
    PaymentCheckRequest,
    PaymentListRequest,
    PaymentRefundRequest,
)

# -------------------------------------------------------------------
# Live controls
# -------------------------------------------------------------------
# By default we RUN live tests since you explicitly requested integration.
RUN_LIVE = os.environ.get("QPAY_RUN_LIVE_TESTS", "1") != "0"
skip_live = pytest.mark.skipif(not RUN_LIVE, reason="Set QPAY_RUN_LIVE_TESTS=1 to run live QPay sandbox tests.")

SANDBOX_USERNAME = os.environ.get("QPAY_USERNAME", "TEST_MERCHANT")
SANDBOX_PASSWORD = os.environ.get("QPAY_PASSWORD", "123456")
SANDBOX_INVOICE_CODE = os.environ.get("QPAY_INVOICE_CODE", "TEST_INVOICE")


def _unique_sender_invoice_no() -> str:
    # short, unique, and easy to read
    return f"INV-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"


def _client() -> QPayClientSync:
    # test client settings
    settings = QPaySettings(
        client_retries=0,
        payment_check_retries=0,
    )
    return QPayClientSync(settings=settings)


# -------------------------------------------------------------------
# Auth / token
# -------------------------------------------------------------------


@skip_live
def test_auth_token_obtained_from_sandbox_live():
    c = _client()
    token = c.get_token()
    assert isinstance(token, str) and len(token) > 10  # JWT-like string


# -------------------------------------------------------------------
# Invoice lifecycle (create -> get -> cancel)
# -------------------------------------------------------------------


@skip_live
def test_invoice_create_get_cancel_live():
    c = _client()

    req = InvoiceCreateSimpleRequest(
        invoice_code=SANDBOX_INVOICE_CODE,
        sender_invoice_no=_unique_sender_invoice_no(),
        invoice_receiver_code="terminal",
        invoice_description="integration-test (sync)",
        amount=Decimal("100"),  # MNT
        callback_url="https://example.com/callback",
    )
    created = c.invoice_create(req)
    assert created.invoice_id and isinstance(created.invoice_id, str)

    invoice_id = created.invoice_id

    got = c.invoice_get(invoice_id)
    assert got.invoice_id == invoice_id
    assert got.invoice_description

    # Cancel the invoice (unpaid → cancel should work)
    status = c.invoice_cancel(invoice_id)
    # Sandbox sometimes varies codes; accept 2xx
    assert status in (200, 202, 204)


# -------------------------------------------------------------------
# Payments: check & list
# -------------------------------------------------------------------


@skip_live
def test_payment_check_and_list_live():
    c = _client()

    # Create an invoice to have a fresh invoice_id for payment_check
    created = c.invoice_create(
        InvoiceCreateSimpleRequest(
            invoice_code=SANDBOX_INVOICE_CODE,
            sender_invoice_no=_unique_sender_invoice_no(),
            invoice_receiver_code="terminal",
            invoice_description="integration-test payment_check (sync)",
            amount=Decimal("100"),
            callback_url="https://example.com/callback",
        )
    )
    invoice_id = created.invoice_id

    # payment_check expects object_type=INVOICE and object_id=<invoice_id>
    check = c.payment_check(
        PaymentCheckRequest(
            object_type=ObjectType.invoice,
            object_id=invoice_id,
            offset=Offset(page_number=1, page_limit=50),
        ),
    )
    assert hasattr(check, "count")
    assert check.count >= 0

    # payment_list expects object_type=INVOICE and object_id=<invoice_code>
    listed = c.payment_list(
        PaymentListRequest(
            object_type=ObjectType.invoice,
            object_id=SANDBOX_INVOICE_CODE,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            offset=Offset(page_number=1, page_limit=20),
        )
    )
    assert hasattr(listed, "count")
    assert listed.count >= 0


# -------------------------------------------------------------------
# Payments: cancel/refund error paths (should raise)
# -------------------------------------------------------------------


@skip_live
def test_payment_cancel_and_refund_raise_for_invalid_payment_id_live():
    c = _client()
    bogus_payment_id = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(QPayError):
        _ = c.payment_cancel(
            bogus_payment_id, PaymentCancelRequest(callback_url="https://example.com/callmesaul", note="demo")
        )

    with pytest.raises(QPayError):
        _ = c.payment_refund(
            bogus_payment_id, payment_refund_request=PaymentRefundRequest()
        )  # body is optional in your schema


# -------------------------------------------------------------------
# Ebarimt (optional) — requires a PAID payment_id
# -------------------------------------------------------------------
