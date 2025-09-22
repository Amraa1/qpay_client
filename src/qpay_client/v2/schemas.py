"""
Pydantic schemas for QPay v2.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import BankCode, Currency, ObjectTypeNum, PaymentStatus


class TokenResponse(BaseModel):
    token_type: str
    access_token: str
    expires_in: float
    refresh_token: str
    refresh_expires_in: float
    scope: str
    not_before_policy: str = Field(..., alias="not-before-policy")
    session_state: str


class QPayDeeplink(BaseModel):
    name: str
    description: str
    logo: str
    link: str


class Address(BaseModel):
    city: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    street: Optional[str] = Field(default=None, max_length=100)
    building: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=100)
    zipcode: Optional[str] = Field(default=None, max_length=20)
    longitude: Optional[str] = Field(default=None, max_length=20)
    latitude: Optional[str] = Field(default=None, max_length=20)


class SenderTerminalData(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)


class InvoiceReceiverData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    registration_number: Optional[str] = Field(
        default=None, alias="register", max_length=20
    )
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[Address] = None


class SenderBranchData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    registration_number: Optional[str] = Field(
        default=None, alias="register", max_length=20
    )
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[Address] = None


class Discount(BaseModel):
    discount_code: Optional[str] = Field(default=None, max_length=45)
    description: str = Field(max_length=100)
    amount: Decimal = Field(max_digits=20)
    note: Optional[str] = Field(default=None, max_length=255)


class Surcharge(BaseModel):
    surcharge_code: Optional[str] = Field(default=None, max_length=45)
    description: str = Field(max_length=100)
    amount: Decimal = Field(max_digits=20)
    note: Optional[str] = Field(default=None, max_length=255)


class Tax(BaseModel):
    tax_code: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=100)
    amount: Decimal
    note: Optional[str] = Field(default=None, max_length=255)


class Line(BaseModel):
    sender_product_code: Optional[str]
    tax_product_code: Optional[str]
    line_description: str = Field(max_length=255)
    line_quantity: Decimal = Field(max_digits=20)
    line_unit_price: Decimal = Field(max_digits=20)
    note: Optional[str] = Field(default=None, max_length=100)
    discounts: Optional[list[Discount]] = None
    surcharges: Optional[list[Surcharge]] = None
    taxes: Optional[list[Tax]] = None


class SenderStaffData(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class InvoiceCreateSimpleRequest(BaseModel):
    invoice_code: str = Field(examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(examples=["123"], max_length=45)
    invoice_receiver_code: str = Field(max_length=45)
    invoice_description: str = Field(max_length=255)
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    amount: Decimal = Field(gt=0)
    callback_url: str = Field(max_length=255)


class InvoiceCreateRequest(BaseModel):
    invoice_code: str = Field(examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(max_length=45)
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    sender_branch_data: Optional[SenderBranchData] = None
    sender_staff_code: Optional[str] = Field(default=None, max_length=100)
    sender_staff_data: Optional[SenderStaffData] = None
    sender_terminal_code: Optional[str] = Field(default=None, max_length=45)
    sender_terminal_data: Optional[SenderTerminalData] = None
    invoice_receiver_code: str = Field(max_length=45)
    invoice_receiver_data: Optional[InvoiceReceiverData] = None
    invoice_description: str = Field(max_length=255)
    invoice_due_date: Optional[date] = None
    enable_expiry: Optional[bool] = None
    expiry_date: Optional[date] = None
    calculate_vat: Optional[bool] = Field(default=None)
    tax_customer_code: Optional[str] = None
    line_tax_code: Optional[str] = Field(default=None)
    allow_partial: Optional[bool] = Field(default=None)
    minimum_amount: Optional[Decimal] = None
    allow_exceed: Optional[bool] = Field(default=None)
    maximum_amount: Optional[Decimal] = None
    amount: Optional[Decimal] = Field(default=None)
    callback_url: str = Field(max_length=255)
    note: Optional[str] = Field(default=None, max_length=1000)
    lines: Optional[list[Line]] = None
    transactions: Optional[list] = None


class InvoiceCreateResponse(BaseModel):
    invoice_id: str
    qr_text: str
    qr_image: str
    qPay_shortUrl: str
    urls: list[QPayDeeplink]


class CardTransaction(BaseModel):
    card_type: str
    is_cross_border: bool
    amount: Decimal
    currency: Currency
    date: datetime
    status: str
    settlement_status: str
    settlement_status_date: datetime


class P2PTransaction(BaseModel):
    transaction_bank_code: BankCode
    account_bank_code: BankCode
    account_bank_name: str
    account_number: str
    status: str
    amount: Decimal
    currency: Currency
    settlement_status: str


class Payment(BaseModel):
    payment_id: str
    payment_status: PaymentStatus
    payment_amount: Decimal
    trx_fee: Decimal
    payment_currency: Currency
    payment_wallet: str
    payment_type: str
    next_payment_date: Optional[date] = None
    next_payment_datetime: Optional[datetime] = None
    card_transactions: list[CardTransaction]
    p2p_transactions: list[P2PTransaction]


class Offset(BaseModel):
    page_number: Decimal = Field(default=Decimal(1), ge=1, le=100)
    page_limit: Decimal = Field(default=Decimal(10), ge=1, le=100)


class PaymentCheckResponse(BaseModel):
    count: int
    paid_amount: Optional[Decimal] = None
    rows: list[Payment]


class PaymentCheckRequest(BaseModel):
    object_type: ObjectTypeNum
    object_id: str = Field(max_length=50)
    offset: Optional[Offset] = Field(default_factory=Offset)


class CancelPaymentRequest(Payment):
    callback_url: str
    note: str


class EbarimtCreateRequest(BaseModel):
    payment_id: str
    ebarimt_receiver_type: str
    ebarimt_receiver: Optional[str] = None
    callback_url: Optional[str] = None


class Ebarimt(BaseModel):
    id: str
    ebarimt_by: str
    g_wallet_id: str
    g_wallet_customer_id: str
    ebarim_receiver_type: str
    ebarimt_receiver: str
    ebarimt_district_code: str
    ebarimt_bill_type: str
    g_merchant_id: str
    merchant_branch_code: str
    merchant_terminal_code: str
    merchant_staff_code: str
    merchant_register: Decimal
    g_payment_id: Decimal
    paid_by: str
    object_type: str
    object_id: str
    amount: Decimal
    vat_amount: Decimal
    city_tax_amount: Decimal
    ebarimt_qr_data: str
    ebarimt_lottery: str
    note: str
    ebarimt_status: str
    ebarimt_status_date: datetime
    tax_type: str
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool


class PaymentListRequest(BaseModel):
    object_type: str
    object_id: str
    start_date: datetime
    end_date: datetime
    offset: Offset


class PaymentCancelRequest(BaseModel):
    callback_url: Optional[str] = None
    note: Optional[str] = None
