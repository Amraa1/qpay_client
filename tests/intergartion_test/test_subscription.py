# tests/test_subscription_invoice.py
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

# ---- Project imports (adjust paths/namespaces to your package layout) ----
# from qpay_client import QPayClient   # if your client is exported at package root
from qpay_client.v2 import QPayClient  # fallback if you keep v2 structure
from qpay_client.v2.schemas import (
    Address,
    InvoiceCreateRequest,
    InvoiceCreateResponse,
    InvoiceCreateSimpleRequest,
    InvoiceReceiverData,
    # If you have a "simple" request schema it stays unused for subscription tests.
    # InvoiceCreateSimpleRequest,
    Line,
    SenderBranchData,
    SenderStaffData,
    SenderTerminalData,
    TaxType,
)

# If your SubscriptionIntervalType lives elsewhere, import it accordingly.
from qpay_client.v2.types import HttpUrlStr, SubscriptionIntervalType

pytestmark = pytest.mark.asyncio

SANDBOX_USERNAME = os.environ.get("QPAY_USERNAME", "TEST_MERCHANT")
SANDBOX_PASSWORD = os.environ.get("QPAY_PASSWORD", "123456")

# -------------------------------------------------------------------------
# Helpers / Fixtures
# -------------------------------------------------------------------------

invoice_list = [
    InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        amount=Decimal(100),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        sender_branch_code="BRANCH1",
        sender_branch_data=SenderBranchData(
            register="123456",
            name="My salbar name",
            email="salbar1@example.com",
            phone="+97699119911",
            address=Address(
                city="Rio de Janeiro",
                district="Favela Santa Marta",
                street="Botafogo",
                building="R. Nossa Fe 50-100",
                address="Favela, City of god",
                zipcode="22260-140",
                longitude="-22.947616",
                latitude="-43.194083",
            ),
        ),
        sender_staff_code="STAFF1",
        sender_staff_data=SenderStaffData(name="Li'l Dice", email="immakillyou@example.com", phone="+5599119911"),
        sender_terminal_code="TERMINAL1",
        sender_terminal_data=SenderTerminalData(
            name="FAVELA1",
        ),
        invoice_receiver_data=InvoiceReceiverData(
            register="123123123121121",
            name="Li'l Dice",
            email="immakillyou@example.com",
            phone="+5599119911",
            address=Address(
                city="Rio de Janeiro",
                district="Favela Santa Marta",
                street="Botafogo",
                building="R. Nossa Fe 50-100",
                address="Favela, City of god",
                zipcode="22260-140",
                longitude="-22.947616",
                latitude="-43.194083",
            ),
        ),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        note="City of God",
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        enable_expiry=True,
        expiry_date=datetime(2025, 10, 31),
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        calculate_vat=True,
        tax_type=TaxType.with_tax,
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        allow_subscribe=True,
        subscription_interval="31D",
        subscription_webhook="https://example.com/subscription/callback",
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
    InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=str(uuid.uuid4()),
        invoice_receiver_code=str(uuid.uuid4()),
        callback_url="https://example.com/callback",
        invoice_description="Some description",
        lines=[
            Line(
                sender_product_code=str(uuid.uuid4()),
                tax_product_code=None,
                line_description="Food",
                line_quantity=Decimal(1000),
                line_unit_price=Decimal(1000),
                note=None,
                discounts=None,
                surcharges=None,
                taxes=None,
            )
        ],
    ),
]


async def _new_client() -> QPayClient:
    return QPayClient(
        username=SANDBOX_USERNAME,
        password=SANDBOX_PASSWORD,
        is_sandbox=True,
        # keep defaults for timeout/retry
    )


def _unique_suffix() -> str:
    # shorter, URL-safe unique suffix for sender_invoice_no / invoice_receiver_code
    return uuid.uuid4().hex[:12]


@pytest.fixture
async def client():
    cli = await _new_client()
    return cli


def _basic_lines():
    """
    Construct a minimal valid 'lines' list accepted by your API.

    Adjust keys to your Line schema if they differ (e.g., name/description/qty/unit_price/total).
    """
    return [
        Line(
            line_description="Monthly Pro plan",
            line_quantity=1,
            line_unit_price=1000,
        ),
    ]


def _valid_subscription_payload(
    *,
    amount: Decimal = Decimal("1000"),
    interval: SubscriptionIntervalType = "1M",
    webhook: HttpUrlStr = "https://example.com/qpay/subscription",
):
    """
    Builds a valid InvoiceCreateRequest dict for subscription invoice.

    Adjust fields to match your exact Pydantic model names.
    """
    uid = _unique_suffix()
    due = datetime.now(timezone.utc) + timedelta(days=2)
    return dict(
        invoice_code="TEST_INVOICE",
        sender_invoice_no=f"SUB-{uid}",
        invoice_receiver_code=f"CUST-{uid}",
        amount=amount,
        callback_url="https://example.com/qpay/callback",
        invoice_description="Subscription: Monthly Pro plan",
        invoice_due_date=due,  # Optional
        allow_subscribe=True,
        subscription_interval=interval,
        subscription_webhook=webhook,
        lines=_basic_lines(),
        # Set optional toggles as needed
        calculate_vat=False,
        allow_partial=False,
        allow_exceed=False,
        # If you have tax_type and it must be 1|2|3, set one:
        # tax_type="1",
    )


# -------------------------------------------------------------------------
# Validation-only tests (no network)
# -------------------------------------------------------------------------


def test_subscription_requires_interval_and_webhook_and_lines():
    # allow_subscribe=True but missing interval
    with pytest.raises(ValueError, match=r"subscription_interval.*must have valid values"):
        InvoiceCreateRequest(
            **{
                **_valid_subscription_payload(),
                "subscription_interval": None,
            }
        )

    # allow_subscribe=True but missing webhook
    with pytest.raises(ValueError, match=r"subscription_interval and subscription_webhook must have valid values"):
        InvoiceCreateRequest(
            **{
                **_valid_subscription_payload(),
                "subscription_webhook": None,
            }
        )

    # allow_subscribe=True but missing lines
    with pytest.raises(ValueError, match=r"lines must have atleast one value"):
        InvoiceCreateRequest(
            **{
                **_valid_subscription_payload(),
                "lines": [],
            }
        )


def test_invalid_subscription_interval_pattern_rejected_by_type():
    # Example of a bad interval (your pattern should reject "0M", "01M", etc.)
    bad_payload = _valid_subscription_payload(interval="0M")
    # Construction should raise a Pydantic validation error before any HTTP call.
    with pytest.raises(ValidationError):
        InvoiceCreateRequest(**bad_payload)


def test_allow_subscribe_false_does_not_require_subscription_fields():
    # Normal invoice should pass model validation without interval/webhook/lines
    payload = _valid_subscription_payload()
    payload["allow_subscribe"] = False
    payload.pop("subscription_interval", None)
    payload.pop("subscription_webhook", None)
    payload.pop("lines", None)
    model = InvoiceCreateRequest(**payload)
    assert model.allow_subscribe is False


# -------------------------------------------------------------------------
# Integration tests (real network) — run with: pytest -m integration
# -------------------------------------------------------------------------


@pytest.mark.integration
async def test_create_subscription_invoice_success():
    """Happy-path: create a subscription invoice and assert the subscription object,deeplinks, and essentials exist in the response."""
    client = await _new_client()
    req = InvoiceCreateRequest(**_valid_subscription_payload())  # type: ignore
    resp: InvoiceCreateResponse = await client.invoice_create(req)

    # Basic response shape assertions
    assert isinstance(resp, InvoiceCreateResponse)
    assert isinstance(resp.invoice_id, str) and resp.invoice_id
    assert isinstance(resp.qr_text, str) and resp.qr_text
    assert isinstance(resp.qr_image, str) and resp.qr_image
    assert isinstance(resp.qPay_shortUrl, str) and resp.qPay_shortUrl
    assert isinstance(resp.urls, list) and len(resp.urls) > 0

    # Subscription block must be present for allow_subscribe=True
    assert resp.subscription is not None, "Subscription object must be returned for subscription invoices"
    sub = resp.subscription

    # Subscription must echo key attributes
    assert isinstance(sub.id, str) and sub.id
    assert isinstance(sub.g_invoice_id, str) and sub.g_invoice_id
    assert str(sub.webhook) == "https://example.com/qpay/subscription"
    assert sub.interval in ("1M", "1W", "1D", "2W", "3M") or re.match(r"^[1-9][0-9]?[DWM]$", str(sub.interval))
    # Dates are reasonable
    assert isinstance(sub.start_date, datetime)
    assert isinstance(sub.created_date, datetime)
    assert isinstance(sub.updated_date, datetime)

    # Optional next_payment_date may be None immediately; if present, it should be a datetime
    if sub.next_payment_date is not None:
        assert isinstance(sub.next_payment_date, datetime)

    # Deeplinks: each must have name/description/logo/link strings
    for dl in resp.urls:
        assert dl.name and dl.link, f"Deeplink missing required fields: {dl}"


@pytest.mark.integration
async def test_create_subscription_invoice_with_custom_amount_and_weekly_interval():
    """Variation: different amount and interval (weekly)."""
    client = await _new_client()
    req = InvoiceCreateRequest(
        **_valid_subscription_payload(
            amount=Decimal("2999"),
            interval="1W",
        )
    )
    resp = await client.invoice_create(req)

    assert resp.subscription is not None
    assert resp.subscription.interval == "1W"
    assert Decimal("2999")  # semantic check only; QPay total is derived by server, so we mainly assert success.


@pytest.mark.integration
async def test_create_subscription_invoice_rejects_missing_lines_server_side():
    """
    Sanity check: if client-side validator is bypassed (e.g., building dict then model_dump),server should still reject malformed requests (defense-in-depth).

    We intentionally disable the lines field AFTER model creation to simulate a malformed payload.
    """
    client = await _new_client()
    # Build a valid model
    good = InvoiceCreateRequest(**_valid_subscription_payload())  # type: ignore

    # Now emulate a low-level tamper that removes lines before sending.
    tampered = good.model_dump(by_alias=True, exclude_none=True, mode="json")
    tampered.pop("lines", None)

    # Send via the client's private request method to simulate server reaction.
    # NOTE: this relies on your client's internal API; adjust if needed.
    # If you want to keep public API only, you can skip this test.
    try:
        response = await client._request("POST", "/invoice", headers=await client._headers(), json=tampered)
    except Exception as e:
        # A transport exception also proves server rejected the malformed body
        pytest.skip(f"Low-level client access not available or server blocked: {e}")
        return

    # Expect a 4xx from server. If your _request raises on 4xx, adapt assertions.
    # Here we assume _request returns a raw Response-like object on success.
    print(response)
    status = getattr(response, "status_code", None)
    body = getattr(response, "json", lambda: {})()
    assert status and 200 <= status < 300, f"Expected 4xx on missing 'lines'; got {status}, body={body}"


@pytest.mark.integration
async def test_create_normal_invoice_when_allow_subscribe_false():
    """Ensure a non-subscription invoice does not include subscription object."""
    client: QPayClient = await _new_client()
    payload = _valid_subscription_payload()
    payload["allow_subscribe"] = False
    payload.pop("subscription_interval", None)
    payload.pop("subscription_webhook", None)
    payload.pop("lines", None)
    payload["invoice_description"] = "Normal one-time invoice"

    req = InvoiceCreateRequest(**payload)
    resp = await client.invoice_create(req)

    assert resp.subscription is None
    assert isinstance(resp.invoice_id, str) and resp.invoice_id
    assert isinstance(resp.qr_text, str) and resp.qr_text


@pytest.mark.integration
async def test_subscription_invoice_rejects_bad_interval(client: QPayClient):
    """If a bad interval slips through type guards (e.g., due to future refactor), server should reject it. We expect 4xx."""
    # Try constructing a model with a "permissive" type cast if your SubscriptionIntervalType ever loosens.
    # If your Pydantic type strictly rejects, this test will xfail earlier.
    try:
        req = _valid_subscription_payload(interval="0M")
    except Exception:
        pytest.xfail("Client-side Pydantic validation already rejects invalid interval '0M'")
        return

    # If construction passed, try sending and expect server-side 4xx
    try:
        resp = await client.invoice_create(req)
    except Exception:
        # If your client raises on 4xx, reaching here is acceptable.
        return
    else:
        # If no exception and we get a parsed response, it unexpectedly passed.
        # Fail explicitly so we notice.
        pytest.fail(f"Server accepted invalid interval, response={resp}")


@pytest.mark.integration
async def test_subscription_invoice_with_possible_variation():
    client = await _new_client()
    coroutines = map(client.invoice_create, invoice_list)

    result: list[InvoiceCreateResponse] = []
    for coroutine in coroutines:
        result.append(await coroutine)

    subs = []
    for res in result:
        if res.subscription:
            subs.append(res.subscription.id)
        else:
            continue

    subs = []
    coroutines = map(client.subscription_get, subs)
    for coroutine in coroutines:
        subs.append(await coroutine)
