from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from qpay_client.v2.enums import (
    BankCode,
    Currency,
    EbarimtReceiverType,
    InvoiceStatus,
    ObjectType,
    PaymentStatus,
    TransactionType,
)

# Import from your uploaded files' package path
# Adjust if your project structure differs.
from qpay_client.v2.schemas import (
    Account,
    Address,
    CancelPaymentRequest,
    CardTransaction,
    Discount,
    Ebarimt,
    EbarimtCreateRequest,
    EbarimtCreateResponse,
    EbarimtGetResponse,
    InvoiceCreateRequest,
    InvoiceCreateResponse,
    InvoiceCreateSimpleRequest,
    InvoiceGetResponse,
    InvoiceReceiverData,
    Line,
    Offset,
    P2PTransaction,
    Payment,
    PaymentCancelRequest,
    PaymentCheckRequest,
    PaymentCheckResponse,
    PaymentGetResponse,
    PaymentList,
    PaymentListRequest,
    PaymentListResponse,
    PaymentRefundRequest,
    QPayDeeplink,
    SenderBranchData,
    SenderStaffData,
    SenderTerminalData,
    Surcharge,
    Tax,
    TokenResponse,
    Transaction,
)

# -------------------------------------------------------
# TokenResponse & field alias: not-before-policy
# -------------------------------------------------------


def test_token_response_alias_not_before_policy():
    payload = {
        "token_type": "bearer",
        "access_token": "ACCESS",
        "expires_in": 3600,
        "refresh_token": "REFRESH",
        "refresh_expires_in": 7200,
        "scope": "openid",
        "not-before-policy": "0",
        "session_state": "sess",
    }
    m = TokenResponse.model_validate(payload)
    assert m.not_before_policy == "0"


# -------------------------------------------------------
# Simple structures
# -------------------------------------------------------


def test_qpay_deeplink_and_address_and_sender_terminal_data():
    link = QPayDeeplink(name="App", description="Open app", logo="logo.png", link="https://x")
    assert link.link.startswith("https://")

    addr = Address(city="Ulaanbaatar", zipcode="15160")
    assert addr.city == "Ulaanbaatar"
    with pytest.raises(ValidationError):
        Address(city="x" * 101)  # > 100

    term = SenderTerminalData(name="POS-01")
    assert term.name == "POS-01"


def test_invoice_receiver_sender_branch_data_alias_register_and_nested_address():
    addr = Address(street="Peace Ave")
    recv = InvoiceReceiverData(register="1234567", name="Buyer", address=addr)
    assert recv.registration_number == "1234567"
    assert recv.address is not None
    assert recv.address.street == "Peace Ave"

    br = SenderBranchData(register="9876543", email="branch@example.com", address=addr)
    assert br.registration_number == "9876543"
    assert br.email == "branch@example.com"


# -------------------------------------------------------
# Totals/lines/transactions building blocks
# -------------------------------------------------------


def test_discount_surcharge_tax_models_and_line_and_transaction_and_account():
    d = Discount(description="Promo", amount=Decimal("100"))
    s = Surcharge(description="Delivery", amount=Decimal("500"))
    t = Tax(description="VAT", amount=Decimal("50"))
    acc = Account(
        account_bank_code=BankCode.khan_bank,
        account_number="123456789",
        account_name="Agmarco LLC",
        account_currency=Currency.mnt,
        is_default=True,
    )
    ln = Line(
        line_description="Chicken popcorn",
        line_quantity=Decimal("2"),
        line_unit_price=Decimal("8300"),
        discounts=[d],
        surcharges=[s],
        taxes=[t],
    )
    tr = Transaction(description="Split", amount=Decimal("17100"), accounts=[acc])

    assert ln.line_quantity == Decimal("2")
    assert tr.accounts is not None
    assert tr.accounts[0].account_currency == Currency.mnt


# -------------------------------------------------------
# Invoice create requests/responses
# -------------------------------------------------------


def test_invoice_create_simple_request_positive_amount_and_bounds():
    req = InvoiceCreateSimpleRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="INV-1",
        invoice_receiver_code="terminal",
        invoice_description="desc",
        amount=Decimal("100.00"),
        callback_url="https://example.com/cb",
    )
    assert req.amount == Decimal("100.00")

    with pytest.raises(ValidationError):
        InvoiceCreateSimpleRequest(
            invoice_code="TEST_INVOICE",
            sender_invoice_no="INV-1",
            invoice_receiver_code="terminal",
            invoice_description="desc",
            amount=Decimal("0"),
            callback_url="https://example.com/cb",
        )


def test_invoice_create_request_minimal_and_fullish():
    minimal = InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="S-1",
        invoice_receiver_code="terminal",
        amount=Decimal("10.0"),
        callback_url="https://ex.com",
        invoice_description="hello",
    )
    assert minimal.invoice_description == "hello"

    # A bit more fields:
    fullish = InvoiceCreateRequest(
        invoice_code="TEST_INVOICE",
        sender_invoice_no="S-2",
        invoice_receiver_code="terminal",
        amount=Decimal("12.34"),
        callback_url="https://ex.com",
        invoice_description="fullish",
        invoice_due_date=datetime.now(),
        enable_expiry=True,
        expiry_date=datetime.now() + timedelta(days=1),
        minimum_amount=Decimal("1"),
        maximum_amount=Decimal("999999"),
        allow_partial=True,
        allow_exceed=False,
        note="Note",
        lines=[
            Line(
                line_description="Item",
                line_quantity=Decimal("1"),
                line_unit_price=Decimal("12.34"),
            )
        ],
        transactions=[Transaction(description="t", amount=Decimal("12.34"))],
    )
    assert fullish.allow_partial is True


def test_invoice_create_response_shapes():
    resp = InvoiceCreateResponse(
        invoice_id="INV-UUID",
        qr_text="QRDATA",
        qr_image="data:image/png;base64,xxx",
        qPay_shortUrl="https://qpay.mn/s/abc",
        urls=[QPayDeeplink(name="App", description="open", logo="l", link="https://l")],
    )
    assert resp.urls and resp.urls[0].name == "App"


# -------------------------------------------------------
# Transactions & Payments
# -------------------------------------------------------


def _card_tx():
    return CardTransaction(
        card_type="VISA",
        is_cross_border=False,
        amount=Decimal("100"),
        currency=Currency.mnt,
        date=datetime.now(),
        status="OK",
        settlement_status="SETTLED",
        settlement_status_date=datetime.now(),
    )


def _p2p_tx():
    return P2PTransaction(
        transaction_bank_code=BankCode.khan_bank,
        account_bank_code=BankCode.khan_bank,
        account_bank_name="Khan",
        account_number="123",
        status="OK",
        amount=Decimal("50"),
        currency=Currency.mnt,
        settlement_status="SETTLED",
    )


def _payment_min():
    return Payment(
        payment_id="pid-1",
        payment_status=PaymentStatus.paid,
        payment_amount=Decimal("100"),
        trx_fee=Decimal("0"),
        payment_currency=Currency.mnt,
        payment_wallet="qpay",
        payment_type=TransactionType.card,
        card_transactions=[],
        p2p_transactions=[],
    )


def test_payment_minimum_ok_and_required_lists():
    p = _payment_min()
    assert p.payment_status == PaymentStatus.paid

    # Omit required lists — should fail
    with pytest.raises(ValidationError):
        Payment(
            payment_id="pid-2",
            payment_status=PaymentStatus.paid,
            payment_amount=Decimal("1"),
            trx_fee=Decimal("0"),
            payment_currency=Currency.mnt,
            payment_wallet="qpay",
            payment_type=TransactionType.card,
        )  # type: ignore


def test_payment_get_response_requires_tx_lists():
    payload = {
        "payment_id": "pid",
        "payment_status": PaymentStatus.paid,
        "payment_amount": Decimal("10"),
        "payment_fee": Decimal("0"),
        "payment_currency": Currency.mnt,
        "payment_date": datetime.now(),
        "payment_wallet": "qpay",
        "transaction_type": TransactionType.card,
        "object_type": ObjectType.invoice,
        "object_id": "INV-1",
        "card_transactions": [],
        "p2p_transactions": [],
    }
    ok = PaymentGetResponse.model_validate(payload)
    assert ok.object_type == ObjectType.invoice

    bad = dict(payload)
    bad.pop("card_transactions")
    with pytest.raises(ValidationError):
        PaymentGetResponse.model_validate(bad)


def test_payment_list_and_response():
    row = PaymentList(
        payment_id="p-1",
        payment_date=datetime.now(),
        payment_status=PaymentStatus.paid,
        payment_fee=Decimal("0"),
        payment_amount=Decimal("100"),
        payment_currency=Currency.mnt,
        payment_wallet="qpay",
        payment_name="Invoice Pmt",
        payment_description="desc",
        paid_by=TransactionType.card,
        object_type=ObjectType.invoice,
        object_id="INV-1",
    )
    resp = PaymentListResponse(count=1, rows=[row])
    assert resp.count == 1
    assert resp.rows[0].paid_by == TransactionType.card


# -------------------------------------------------------
# Offset & Refund request
# -------------------------------------------------------


def test_offset_bounds_and_refund_note_optional():
    ok = Offset(page_number=1, page_limit=1000)
    assert ok.page_number == 1
    with pytest.raises(ValidationError):
        Offset(page_number=0, page_limit=10)
    with pytest.raises(ValidationError):
        Offset(page_number=1, page_limit=1001)

    r1 = PaymentRefundRequest()
    r2 = PaymentRefundRequest(note="Customer requested")
    assert r1.note is None and r2.note == "Customer requested"


# -------------------------------------------------------
# Payment check (rows: [] must validate)
# -------------------------------------------------------


def test_payment_check_response_with_empty_rows_and_with_item():
    empty_ok = PaymentCheckResponse.model_validate({"count": 0, "rows": []})
    assert empty_ok.count == 0 and empty_ok.rows == []

    one = PaymentCheckResponse.model_validate({"count": 1, "rows": [_payment_min().model_dump()]})
    assert one.count == 1 and len(one.rows) == 1


def test_payment_check_request_shape():
    req = PaymentCheckRequest(
        object_type=ObjectType.invoice,
        object_id="INV-1",
        offset=Offset(page_number=1, page_limit=10),
    )
    assert req.object_type == ObjectType.invoice


# -------------------------------------------------------
# CancelPaymentRequest (subclass of Payment)
# -------------------------------------------------------


def test_cancel_payment_request_inherits_payment_and_adds_fields():
    c = CancelPaymentRequest(
        **_payment_min().model_dump(),
        callback_url="https://ex.com/cb",
        note="Fraud suspected",
    )
    assert c.callback_url == "https://ex.com/cb"
    assert c.note.startswith("Fraud")


# -------------------------------------------------------
# Ebarimt models
# -------------------------------------------------------


def test_ebarimt_create_and_models_and_responses():
    ecr = EbarimtCreateRequest(
        payment_id="pid",
        ebarimt_receiver_type=EbarimtReceiverType.citizen,
        callback_url="https://ex.com",
    )
    assert ecr.ebarimt_receiver_type == EbarimtReceiverType.citizen

    eb = Ebarimt(
        id="e1",
        ebarimt_by="SYS",
        g_wallet_id="gw",
        g_wallet_customer_id="gcid",
        ebarim_receiver_type=EbarimtReceiverType.citizen,
        ebarimt_district_code="1510",
        ebarimt_bill_type="REG",
        g_merchant_id="gm",
        merchant_branch_code="mb",
        g_payment_id=Decimal("1"),
        paid_by=TransactionType.card,
        object_type=ObjectType.invoice,
        object_id="INV-1",
        amount=Decimal("100"),
        vat_amount=Decimal("10"),
        city_tax_amount=Decimal("0"),
        ebarimt_qr_data="qr",
        ebarimt_lottery="lot",
        ebarimt_status="OK",
        ebarimt_status_date=datetime.now(),
        tax_type="VAT",
        created_by="me",
        created_date=datetime.now(),
        updated_by="me",
        updated_date=datetime.now(),
        status=True,
    )
    assert eb.paid_by == TransactionType.card
    assert EbarimtGetResponse.model_validate(eb.model_dump()).id == "e1"
    assert EbarimtCreateResponse.model_validate(eb.model_dump()).status is True


# -------------------------------------------------------
# Payment list request
# -------------------------------------------------------


def test_payment_list_request_minimal_shape():
    req = PaymentListRequest(
        object_type=ObjectType.invoice,
        object_id="TEST_INVOICE",
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now(),
        offset=Offset(page_number=1, page_limit=20),
    )
    assert req.object_type == ObjectType.invoice


# -------------------------------------------------------
# PaymentCancelRequest (separate from CancelPaymentRequest)
# -------------------------------------------------------


def test_payment_cancel_request_optional_fields():
    r1 = PaymentCancelRequest()
    r2 = PaymentCancelRequest(callback_url="https://ex.com", note="please")
    assert r1.callback_url is None and r2.note == "please"


# -------------------------------------------------------
# InvoiceGetResponse (a lot of fields + inputs list)
# -------------------------------------------------------


def test_invoice_get_response_minimal_required_fields():
    inv = InvoiceGetResponse(
        invoice_id="INV-1",
        invoice_status=InvoiceStatus.open,
        sender_invoice_no="S-1",
        invoice_description="hello",
        total_amount=Decimal("100"),
        gross_amount=Decimal("100"),
        tax_amount=Decimal("0"),
        surcharge_amount=Decimal("0"),
        callback_url="https://ex.com",
        inputs=[],  # required list
    )
    assert inv.invoice_status == InvoiceStatus.open
    assert inv.inputs == []


def test_invoice_get_response_with_nested_optional_fields_and_payments():
    inv = InvoiceGetResponse(
        invoice_id="INV-2",
        invoice_status=InvoiceStatus.closed,
        sender_invoice_no="S-2",
        sender_branch_code="BR-1",
        sender_branch_data=SenderBranchData(register="123"),
        sender_staff_code="ST-1",
        sender_staff_data=SenderStaffData(name="Alice"),
        sender_terminal_code="T-1",
        sender_terminal_data=SenderTerminalData(name="POS"),
        invoice_description="desc",
        invoice_due_date=datetime.now(),
        enable_expiry=True,
        expiry_date=datetime.now() + timedelta(days=1),
        minimum_amount=Decimal("1"),
        maximum_amount=Decimal("1000"),
        allow_partial=False,
        allow_exceed=False,
        total_amount=Decimal("100"),
        gross_amount=Decimal("110"),
        tax_amount=Decimal("10"),
        surcharge_amount=Decimal("0"),
        callback_url="https://ex.com",
        note="n",
        lines=[
            Line(
                line_description="Item",
                line_quantity=Decimal("1"),
                line_unit_price=Decimal("100"),
            )
        ],
        transactions=[Transaction(description="t", amount=Decimal("100"))],
        inputs=[],
        payments=[_payment_min()],
    )
    assert inv.payments and inv.payments[0].payment_id == "pid-1"
