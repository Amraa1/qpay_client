import json
import time as _time
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
import pytest

import src.qpay_client.v2.enums as E
import src.qpay_client.v2.schemas as S
import src.qpay_client.v2.sync_client as client_mod

# ---------- Adjust these imports to your actual package path ----------
from src.qpay_client.v2.sync_client import QPayClientSync as _QPayClientSync

# ---------------------------------------------------------------------

# ==========================
# Test infrastructure
# ==========================


class FakeHttpxClient:
    """
    Minimal synchronous httpx-like client with a queue of responses.

    Each .request() pops the next response and records the call.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self._responses:
            raise AssertionError("No more fake responses left in queue")
        return self._responses.pop(0)


def make_response(status_code: int, json_body=None, method="GET", url="https://merchant-sandbox.qpay.mn/v2/x"):
    req = httpx.Request(method, url)
    headers = {}
    content = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        content = json.dumps(json_body).encode()
    return httpx.Response(status_code, request=req, headers=headers, content=content)


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    """Make backoffs instant."""
    monkeypatch.setattr(_time, "sleep", lambda *_a, **_k: None)
    yield


# ---- Fake QpayAuthState (sync client uses attribute + methods) ----


class FakeAuthState:
    def __init__(self):
        # treat has_access_token like a property in your sync client
        self.has_access_token = False
        self._access_expired = True
        self._refresh_expired = True
        self._access = "ACCESS"
        self._refresh = "REFRESH"

    # methods used by client
    def is_access_expired(self, leeway=0):
        return self._access_expired

    def is_refresh_expired(self, leeway=0):
        return self._refresh_expired

    def get_access_token(self):
        return self._access

    def access_as_header(self):
        return f"Bearer {self._access}"

    def refresh_as_header(self):
        return f"Bearer {self._refresh}"

    # schema update
    def update(self, token_response: S.TokenResponse):
        self._access = token_response.access_token
        self._refresh = token_response.refresh_token
        self.has_access_token = True
        self._access_expired = False
        self._refresh_expired = False


# ==========================
# Fixtures to get a patched client
# ==========================


@pytest.fixture
def Client(monkeypatch):
    """
    QPayClientSync class.

    - QpayAuthState patched to FakeAuthState
    - handle_error replaced with a raiser so we can assert it ran
    """
    # Patch state
    monkeypatch.setattr(client_mod, "QpayAuthState", FakeAuthState)

    # Patch schemas we rely on directly (real ones are fine)
    # Patch handle_error: raise a sentinel error so tests can assert
    class HandledError(RuntimeError):
        pass

    def _handle_error(resp, logger):
        raise HandledError(f"handled status={resp.status_code}")

    monkeypatch.setattr(client_mod, "handle_error", _handle_error)

    # Return subclass for easier introspection if needed
    class Patched(_QPayClientSync):
        pass

    return Patched


# ==========================
# Helpers to build minimal-valid payloads
# ==========================


def minimal_invoice_get_payload():
    return {
        "invoice_id": "INV-1",
        "invoice_status": E.InvoiceStatus.open,
        "sender_invoice_no": "S-1",
        "invoice_description": "desc",
        "total_amount": str(Decimal("100")),
        "gross_amount": str(Decimal("100")),
        "tax_amount": str(Decimal("0")),
        "surcharge_amount": str(Decimal("0")),
        "callback_url": "https://cb.com",
        "inputs": [],
    }


def minimal_invoice_create_response():
    return {
        "invoice_id": "INV-NEW",
        "qr_text": "QRDATA",
        "qr_image": "base64...",
        "qPay_shortUrl": "https://qpay.mn/s/abc",
        "urls": [{"name": "App", "description": "open", "logo": "l", "link": "https://l"}],
    }


def minimal_payment_get_payload():
    return {
        "payment_id": "pid",
        "payment_status": E.PaymentStatus.paid,
        "payment_amount": "100",
        "payment_fee": "0",
        "payment_currency": E.Currency.mnt,
        "payment_date": datetime.utcnow().isoformat(),
        "payment_wallet": "qpay",
        "transaction_type": E.TransactionType.card,
        "object_type": E.ObjectType.invoice,
        "object_id": "INV-1",
        "card_transactions": [],
        "p2p_transactions": [],
    }


def minimal_payment_in_rows():
    return {
        "payment_id": "pid-1",
        "payment_status": E.PaymentStatus.paid,
        "payment_amount": "100",
        "trx_fee": "0",
        "payment_currency": E.Currency.mnt,
        "payment_wallet": "qpay",
        "payment_type": E.TransactionType.card,
        "card_transactions": [],
        "p2p_transactions": [],
    }


def minimal_payment_list_response():
    return {
        "count": 1,
        "rows": [
            {
                "payment_id": "p-1",
                "payment_date": datetime.utcnow().isoformat(),
                "payment_status": E.PaymentStatus.paid,
                "payment_fee": "0",
                "payment_amount": "100",
                "payment_currency": E.Currency.mnt,
                "payment_wallet": "qpay",
                "payment_name": "Invoice Pmt",
                "payment_description": "desc",
                "paid_by": E.TransactionType.card,
                "object_type": E.ObjectType.invoice,
                "object_id": "INV-1",
            }
        ],
    }


def minimal_ebarimt_payload():
    return {
        "id": "e1",
        "ebarimt_by": "SYS",
        "g_wallet_id": "gw",
        "g_wallet_customer_id": "gcid",
        "ebarim_receiver_type": E.EbarimtReceiverType.citizen,
        "ebarimt_district_code": "1510",
        "ebarimt_bill_type": "REG",
        "g_merchant_id": "gm",
        "merchant_branch_code": "mb",
        "g_payment_id": "1",
        "paid_by": E.TransactionType.card,
        "object_type": E.ObjectType.invoice,
        "object_id": "INV-1",
        "amount": "100",
        "vat_amount": "10",
        "city_tax_amount": "0",
        "ebarimt_qr_data": "qr",
        "ebarimt_lottery": "lot",
        "ebarimt_status": "OK",
        "ebarimt_status_date": datetime.utcnow().isoformat(),
        "tax_type": "VAT",
        "created_by": "me",
        "created_date": datetime.utcnow().isoformat(),
        "updated_by": "me",
        "updated_date": datetime.utcnow().isoformat(),
        "status": True,
    }


# ==========================
# Tests for internal plumbing
# ==========================


def test_headers_and_get_token_paths(Client, monkeypatch):
    c = Client()
    # Provide fake http client (unused here)
    c._client = FakeHttpxClient([])
    # Start with no token -> _authenticate should be called
    calls = {"auth": 0, "refresh": 0}

    def fake_auth():
        calls["auth"] += 1
        # simulate /auth/token result path inside _authenticate
        resp = make_response(
            200,
            {
                "token_type": "bearer",
                "access_token": "A1",
                "expires_in": 3600,
                "refresh_token": "R1",
                "refresh_expires_in": 7200,
                "scope": "openid",
                "not-before-policy": "0",
                "session_state": "s",
            },
            method="POST",
            url="https://merchant-sandbox.qpay.mn/v2/auth/token",
        )
        # shortcut: inject directly through state
        c._auth_state.update(S.TokenResponse.model_validate(resp.json()))

    monkeypatch.setattr(c, "_authenticate", fake_auth)

    def fake_refresh():
        calls["refresh"] += 1

    monkeypatch.setattr(c, "_refresh_access_token", fake_refresh)

    # get headers -> get_token -> _authenticate should run once
    h = c._headers()
    assert h["Authorization"].startswith("Bearer ")
    assert calls["auth"] == 1 and calls["refresh"] == 0

    # Force access expired -> refresh path
    c._auth_state._access_expired = True
    c.get_token()
    assert calls["refresh"] == 1


def test_request_401_triggers_refresh_and_retry(Client, monkeypatch):
    c = Client()
    # token present to avoid auth on headers
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    # Queue: 401 then 200
    r1 = make_response(401, method="GET", url="https://merchant-sandbox.qpay.mn/v2/x")
    r2 = make_response(200, {"ok": True}, method="GET", url="https://merchant-sandbox.qpay.mn/v2/x")
    c._client = FakeHttpxClient([r1, r2])

    called = {"refresh": 0}

    def fake_refresh():
        called["refresh"] += 1

    monkeypatch.setattr(c, "_refresh_access_token", fake_refresh)

    res = c._request("GET", "/x", headers=c._headers())
    assert res.status_code == 200
    assert called["refresh"] == 1
    assert len(c._client.calls) == 2


def test_request_retries_on_5xx_then_succeeds(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    r1 = make_response(500, method="GET", url="https://merchant-sandbox.qpay.mn/v2/y")
    r2 = make_response(200, {"ok": True}, method="GET", url="https://merchant-sandbox.qpay.mn/v2/y")
    c._client = FakeHttpxClient([r1, r2])

    res = c._request("GET", "/y", headers=c._headers(), retries=3, delay=0.01)
    assert res.status_code == 200


def test_request_calls_handle_error_on_4xx(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    # 400 should invoke handle_error -> raises our sentinel
    r = make_response(400, {"error": "bad"}, method="GET", url="https://merchant-sandbox.qpay.mn/v2/z")
    c._client = FakeHttpxClient([r])

    with pytest.raises(RuntimeError) as exc:
        c._request("GET", "/z", headers=c._headers())
    assert "handled status=400" in str(exc.value)


# ==========================
# Public API: Invoice
# ==========================


def test_invoice_get_create_cancel(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    inv_get = make_response(
        200, minimal_invoice_get_payload(), method="GET", url="https://merchant-sandbox.qpay.mn/v2/invoice/INV-1"
    )
    inv_create = make_response(
        200, minimal_invoice_create_response(), method="POST", url="https://merchant-sandbox.qpay.mn/v2/invoice"
    )
    inv_cancel = make_response(204, None, method="DELETE", url="https://merchant-sandbox.qpay.mn/v2/invoice/INV-1")
    c._client = FakeHttpxClient([inv_get, inv_create, inv_cancel])

    # invoice_get
    got = c.invoice_get("INV-1")
    assert got.invoice_id == "INV-1"

    # invoice_create
    req = S.InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="S-1",
        invoice_receiver_code="terminal",
        invoice_description="desc",
        amount=Decimal("100"),
        callback_url="https://cb.com",
    )
    created = c.invoice_create(req)
    assert created.invoice_id == "INV-NEW"

    # invoice_cancel
    status = c.invoice_cancel("INV-1")
    assert status == 204


# ==========================
# Public API: Payments
# ==========================


def test_payment_get_list(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    pget = make_response(
        200, minimal_payment_get_payload(), method="GET", url="https://merchant-sandbox.qpay.mn/v2/payment/PID"
    )
    plist = make_response(
        200, minimal_payment_list_response(), method="POST", url="https://merchant-sandbox.qpay.mn/v2/payment/list"
    )
    c._client = FakeHttpxClient([pget, plist])

    g = c.payment_get("PID")
    assert g.object_type == E.ObjectType.invoice

    req = S.PaymentListRequest(
        object_type=E.ObjectType.invoice,
        object_id="TEST_INVOICE",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow(),
        offset=S.Offset(page_number=1, page_limit=10),
    )
    listed = c.payment_list(req)
    assert listed.count == 1
    assert listed.rows[0].payment_id == "p-1"


def test_payment_check_polls_until_count_positive(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    # First count=0, then count=1 with one row
    r1 = make_response(
        200, {"count": 0, "rows": []}, method="POST", url="https://merchant-sandbox.qpay.mn/v2/payment/check"
    )
    r2 = make_response(
        200,
        {"count": 1, "rows": [minimal_payment_in_rows()]},
        method="POST",
        url="https://merchant-sandbox.qpay.mn/v2/payment/check",
    )
    c._client = FakeHttpxClient([r1, r2])

    req = S.PaymentCheckRequest(
        object_type=E.ObjectType.invoice,
        object_id="INV-1",
        offset=S.Offset(page_number=1, page_limit=10),
    )
    out = c.payment_check(req)
    assert out.count == 1
    assert len(out.rows) == 1


def test_payment_cancel_and_refund_success_status(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    cancel = make_response(204, None, method="DELETE", url="https://merchant-sandbox.qpay.mn/v2/payment/cancel/PID")
    refund = make_response(204, None, method="DELETE", url="https://merchant-sandbox.qpay.mn/v2/payment/refund/PID")
    c._client = FakeHttpxClient([cancel, refund])

    assert c.payment_cancel("PID") == 204
    assert c.payment_refund("PID", S.PaymentRefundRequest()) == 204


def test_payment_cancel_raises_on_4xx_via_handle_error(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    bad = make_response(
        404, {"error": "NF"}, method="DELETE", url="https://merchant-sandbox.qpay.mn/v2/payment/cancel/BAD"
    )
    c._client = FakeHttpxClient([bad])

    with pytest.raises(RuntimeError) as exc:
        c.payment_cancel("BAD")
    assert "handled status=404" in str(exc.value)


# ==========================
# Public API: Ebarimt
# ==========================


def test_ebarimt_create_and_get(Client):
    c = Client()
    c._auth_state.has_access_token = True
    c._auth_state._access_expired = False
    c._auth_state._refresh_expired = False

    create_resp = make_response(
        200, minimal_ebarimt_payload(), method="POST", url="https://merchant-sandbox.qpay.mn/v2/ebarimt/create"
    )
    get_resp = make_response(
        200, minimal_ebarimt_payload(), method="GET", url="https://merchant-sandbox.qpay.mn/v2/ebarimt/BARIMT-1"
    )
    c._client = FakeHttpxClient([create_resp, get_resp])

    created = c.ebarimt_create(
        S.EbarimtCreateRequest(
            payment_id="PID",
            ebarimt_receiver_type=E.EbarimtReceiverType.citizen,
            callback_url="https://callback.com",
        )
    )
    assert created.id == "e1"

    got = c.ebarimt_get("BARIMT-1")
    assert got.object_type == E.ObjectType.invoice
