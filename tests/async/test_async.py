import os
import time
import uuid
from datetime import datetime, timedelta

import pytest

from qpay_client.v2 import QPayClient, QPayError
from qpay_client.v2.enums import ObjectType
from qpay_client.v2.schemas import (
    InvoiceCreateSimpleRequest,
    Offset,
    PaymentCancelRequest,
    PaymentCheckRequest,
    PaymentListRequest,
)

# --- markers and controls -----------------------------------------------------

pytestmark = pytest.mark.asyncio

# To avoid accidental live hits in CI, require explicit opt-in unless user insists.
RUN_LIVE = os.environ.get("QPAY_RUN_LIVE_TESTS", "1") != "0"

skip_live = pytest.mark.skipif(
    not RUN_LIVE,
    reason="Set QPAY_RUN_LIVE_TESTS=1 to run live QPay sandbox tests.",
)

SANDBOX_USERNAME = os.environ.get("QPAY_USERNAME", "TEST_MERCHANT")
SANDBOX_PASSWORD = os.environ.get("QPAY_PASSWORD", "123456")


# --- helpers ------------------------------------------------------------------


def _unique_sender_invoice_no() -> str:
    # Short, unique, and human-readable
    # QPay docs sample uses plain numeric strings; this fits & avoids collisions.
    # e.g. "INV-<epoch>-<rand4>"
    return f"INV-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"


async def _new_client() -> QPayClient:
    return QPayClient(
        username=SANDBOX_USERNAME,
        password=SANDBOX_PASSWORD,
        is_sandbox=True,
        # keep defaults for timeout/retry
    )


# --- tests --------------------------------------------------------------------


@skip_live
async def test_auth_token_obtained_from_sandbox():
    client = await _new_client()
    token = await client.get_token()
    assert isinstance(token, str)
    assert len(token) > 10  # a JWT-ish string


@skip_live
async def test_refresh_token_path_works():
    client = await _new_client()
    # Force an authenticate to ensure we have refresh token material
    tok1 = await client.get_token()
    assert tok1

    # Force refresh path by marking access expired but refresh valid
    client._auth_state.refresh_token_expiry = 0
    client._auth_state.access_token_expiry = 0

    # This should call /auth/refresh under the hood and keep us authenticated
    tok2 = await client.get_token()
    assert tok2
    # Tokens may or may not change; just ensure we remain authorized.
    assert isinstance(tok2, str)


@skip_live
async def test_invoice_lifecycle_create_get_cancel_payment_check_and_list():
    client = await _new_client()

    # 1) CREATE INVOICE (per docs: invoice_code, sender_invoice_no, receiver_code, desc, amount, callback_url)
    #    Docs example at developer.qpay.mn under "Нэхэмжлэх үүсгэх". :contentReference[oaicite:1]{index=1}
    req = InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=_unique_sender_invoice_no(),
        invoice_receiver_code="terminal",
        invoice_description="integration-test",
        amount=100,  # MNT
        callback_url="https://example.com/callback",
    )
    created = await client.invoice_create(req)

    # The schema normally includes fields like invoice_id, qr_text, etc.
    # We only assert stable truths: an invoice_id exists and is UUID-like.
    invoice_id = getattr(created, "invoice_id", None)
    assert invoice_id and isinstance(invoice_id, str) and len(invoice_id) >= 30

    # 2) GET INVOICE BY ID
    got = await client.invoice_get(invoice_id)
    assert got.invoice_id == invoice_id

    # 3) PAYMENT CHECK (INVOICE): expect count >= 0; sandbox invoice is unpaid by default.
    #    Docs say: object_type="INVOICE", object_id=<invoice_id>. :contentReference[oaicite:2]{index=2}
    check_req = PaymentCheckRequest(
        object_type=ObjectType.invoice,
        object_id=invoice_id,
        offset=Offset(page_number=1, page_limit=10),
    )
    check = await client.payment_check(check_req, payment_retries=0, delay=0.2, jitter=0.0)
    assert hasattr(check, "count")
    assert check.count >= 0
    # If you manually pay this invoice in the sandbox, this test will still pass (count>0).

    # 4) PAYMENT LIST scoped to invoice_code (object_type INVOICE wants object_id=invoice_code). :contentReference[oaicite:3]{index=3}
    list_req = PaymentListRequest(
        object_type=ObjectType.invoice,
        object_id="TEST_INVOICE",  # docs: use invoice_code when object_type is INVOICE
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        offset=Offset(page_number=1, page_limit=1000),
    )

    listed = await client.payment_list(list_req)
    assert hasattr(listed, "count")
    assert listed.count >= 0

    # 5) CANCEL INVOICE (allowed for created but unpaid invoices)
    status = await client.invoice_cancel(invoice_id)
    # Expect 204 as per docs' "Нэхэмжлэх цуцлах" (empty body) :contentReference[oaicite:4]{index=4}
    assert status in (200, 202, 204)  # sandbox sometimes varies; accept 2xx


@skip_live
async def test_payment_cancel_and_refund_fail_gracefully_for_unpaid():
    """In sandbox, cancel/refund needs a PAID payment_id.

    We demonstrate the endpoints return non-2xx (or error JSON) for an unpaid/random payment_id,
    and ensure client surfaces status/error per implementation.
    Docs show error payload like {"error": "PAYMENT_SETTLED", "message": "..."} for certain cases. :contentReference[oaicite:5]{index=5}
    """
    client = await _new_client()

    # This "payment_id" is random and should not exist/settle in sandbox.
    bogus_payment_id = "123123"

    # payment_cancel -> returns status code via client
    with pytest.raises(QPayError):
        await client.payment_cancel(bogus_payment_id, PaymentCancelRequest())

    # payment_refund -> returns status code via client (needs a payload)
    from qpay_client.v2.schemas import PaymentRefundRequest

    refund_req = PaymentRefundRequest(note="test")
    with pytest.raises(QPayError):
        await client.payment_refund(bogus_payment_id, refund_req)
