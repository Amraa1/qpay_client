"""Pydantic schemas for QPay v2."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from .enums import (
    BankCode,
    Currency,
    EbarimtReceiverType,
    InvoiceStatus,
    ObjectType,
    PaymentStatus,
    TaxCode,
    TaxType,
    TransactionType,
)
from .types import HttpUrlStr, SubscriptionIntervalType


class TokenResponse(BaseModel):
    """QPay Token and Refresh token response."""

    model_config = ConfigDict(validate_by_alias=True)

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
    model_config = ConfigDict(validate_by_alias=True)

    registration_number: Optional[str] = Field(default=None, alias="register", max_length=20)
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[Address] = None


class SenderBranchData(BaseModel):
    model_config = ConfigDict(validate_by_alias=True)

    registration_number: Optional[str] = Field(default=None, alias="register", max_length=20)
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
    tax_code: Optional[TaxCode] = None
    description: Optional[str] = Field(default=None, max_length=100)
    amount: Decimal
    note: Optional[str] = Field(default=None, max_length=255)


class Account(BaseModel):
    account_bank_code: BankCode
    account_number: str = Field(max_length=100)
    account_name: str = Field(max_length=100)
    account_currency: Currency
    is_default: bool


class Line(BaseModel):
    sender_product_code: Optional[str] = None
    tax_product_code: Optional[str] = None
    line_description: str = Field(max_length=255)
    line_quantity: Decimal = Field(max_digits=20)
    line_unit_price: Decimal = Field(max_digits=20)
    note: Optional[str] = Field(default=None, max_length=100)
    discounts: Optional[list[Discount]] = None
    surcharges: Optional[list[Surcharge]] = None
    taxes: Optional[list[Tax]] = None


class Transaction(BaseModel):
    description: str = Field(max_length=100)
    amount: Decimal
    accounts: Optional[list[Account]] = None


class SenderStaffData(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class InvoiceCreateSimpleRequest(BaseModel):
    """Create simple invoice."""

    invoice_code: str = Field(examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(examples=["123"], max_length=45)
    invoice_receiver_code: str = Field(max_length=45)
    invoice_description: str = Field(max_length=255)
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    amount: Decimal = Field(gt=0)
    callback_url: HttpUrlStr


class InvoiceCreateRequest(BaseModel):
    """Create full invoice."""

    invoice_code: str = Field(examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(max_length=45)
    invoice_receiver_code: str = Field(max_length=45)
    invoice_description: str = Field(max_length=255)
    callback_url: HttpUrlStr

    amount: Optional[Decimal] = Field(default=None, gt=0)
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    sender_branch_data: Optional[SenderBranchData] = None
    sender_staff_code: Optional[str] = Field(default=None, max_length=100)
    sender_staff_data: Optional[SenderStaffData] = None
    sender_terminal_code: Optional[str] = Field(default=None, max_length=45)
    sender_terminal_data: Optional[SenderTerminalData] = None
    invoice_receiver_data: Optional[InvoiceReceiverData] = None
    invoice_due_date: Optional[datetime] = None
    enable_expiry: Optional[bool] = None
    expiry_date: Optional[datetime] = None
    calculate_vat: Optional[bool] = None
    tax_type: Optional[TaxType] = None
    tax_customer_code: Optional[str] = None
    line_tax_code: Optional[str] = None
    minimum_amount: Optional[Decimal] = None
    maximum_amount: Optional[Decimal] = None
    allow_partial: Optional[bool] = None
    allow_exceed: Optional[bool] = None
    allow_subscribe: Optional[bool] = None
    subscription_interval: Optional[SubscriptionIntervalType] = None
    subscription_webhook: Optional[HttpUrlStr] = None
    note: Optional[str] = Field(default=None, max_length=1000)
    lines: Optional[list[Line]] = None
    transactions: Optional[list[Transaction]] = None

    @model_validator(mode="after")
    def check_amount_or_lines(self) -> Self:
        if self.amount or self.lines:
            return self
        else:
            raise ValueError("At least one of amount and lines must have valid value.")

    @model_validator(mode="after")
    def validate_when_subcription_allowed(self) -> Self:
        if not self.allow_subscribe:
            return self
        elif not self.subscription_interval or not self.subscription_webhook:
            raise ValueError(
                "When allow_subscription is 'True', subscription_interval and subscription_webhook must have valid values."
            )
        elif not self.lines:
            raise ValueError("When allow_subscription is 'True', lines must have atleast one value.")
        else:
            return self


class Subscription(BaseModel):
    id: str
    is_active: bool
    merchant_id: str
    g_invoice_id: str
    webhook: HttpUrlStr
    start_date: datetime
    interval: SubscriptionIntervalType
    last_interval_date: datetime
    created_date: datetime
    created_by: str
    updated_date: datetime
    updated_by: str
    status: bool
    next_payment_date: Optional[datetime] = None
    note: Optional[str] = None


class QpayInvoiceLineBase(BaseModel):
    id: str
    g_merchant_id: str
    invoice_id: str
    invoice_line_id: str
    description: str
    amount: Decimal
    note: Optional[str] = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool


class InvoiceDiscount(QpayInvoiceLineBase):
    discount_code: Optional[str] = None


class InvoiceTax(QpayInvoiceLineBase):
    tax_code: Optional[TaxCode] = None
    city_tax: Decimal


class InvoiceSurcharge(QpayInvoiceLineBase):
    surcharge_code: Optional[str] = None


class InvoiceLine(BaseModel):
    id: str
    g_merchant_id: str
    invoice_id: str
    customer_product_code: Optional[str] = None
    tax_product_code: Optional[str] = None
    barcode: Optional[str] = None
    classification_code: Optional[str] = None
    line_description: Optional[str] = None
    line_quantity: Decimal
    line_unit_price: Decimal
    note: Optional[str] = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool
    invoice_discounts: list[InvoiceDiscount]
    invoice_taxes: list[InvoiceTax]
    invoice_surcharges: list[InvoiceSurcharge]


class SubscriptionInvoice(BaseModel):
    id: str
    legacy_id: str
    g_merchant_id: str
    object_type: ObjectType
    object_id: str
    qr_linked: bool
    qr_code: str
    sender_invoice_no: str
    sender_name: str
    sender_logo: Optional[str] = None
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    sender_branch_data: Optional[SenderBranchData] = None
    sender_staff_code: Optional[str] = Field(default=None, max_length=100)
    sender_staff_data: Optional[SenderStaffData] = None
    sender_terminal_code: Optional[str] = Field(default=None, max_length=45)
    sender_terminal_data: Optional[SenderTerminalData] = None
    invoice_receiver_data: Optional[InvoiceReceiverData] = None
    invoice_description: str = Field(max_length=255)
    invoice_due_date: Optional[datetime] = None
    enable_expiry: Optional[bool] = None
    expiry_date: Optional[datetime] = None
    calculate_vat: Optional[bool] = None
    tax_type: Optional[TaxType] = None
    tax_customer_code: Optional[str] = None
    line_tax_code: Optional[str] = None
    minimum_amount: Optional[Decimal] = None
    maximum_amount: Optional[Decimal] = None
    receiver_code: str
    receiver_date: Optional[InvoiceReceiverData] = None
    invoice_no: str
    invoice_date: date
    invoice_due_date: Optional[datetime] = None
    invoice_name: Optional[str] = None
    invoice_currency: Currency
    invoice_status: InvoiceStatus
    invoice_status_date: datetime
    has_ebarimt: bool
    has_vat: bool
    ebarimt_by: Optional[str] = None
    ebarimt_customer_code: Optional[str] = None
    is_debt: bool
    allow_partial: bool
    invoice_amount: Decimal
    invoice_total_discount: Decimal
    invoice_total_surcharge: Decimal
    invoice_gross_amount: Decimal
    invoice_total_tax: Decimal
    allow_card_trx: bool
    g_card_terminal_id: str
    allow_p2p_trx: bool
    g_p2p_terminal_id: str
    has_inform: bool
    inform_id: str
    has_check: bool
    check_api: str
    callback_url: HttpUrlStr
    has_transaction: bool
    has_service_fee: bool
    service_fee_method: Optional[str] = None
    service_fee_calc_type: Optional[str] = None
    service_fee_onus: Optional[str] = None
    service_fee_offus: Optional[str] = None
    with_tag: bool
    tag: Optional[str] = None
    short_url: Optional[str] = None
    package_id: Optional[str] = None
    sub_package_id: Optional[str] = None
    note: Optional[str] = None
    district_code: Optional[str] = None
    extra: Optional[str] = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool
    invoice_lines: list[InvoiceLine]
    invoice_transactions: list
    invoice_inputs: list
    total_amount: Decimal
    gross_amount: Decimal
    tax_amount: Decimal
    surcharge_amount: Decimal
    discount_amount: Decimal
    qp_micro_cache_exp_minute: int


class SubscriptionGetResponse(Subscription):
    id: str
    is_active: bool
    merchant_id: str
    g_invoice_id: str
    webhook: HttpUrlStr
    next_payment_date: Optional[datetime] = None
    start_date: datetime
    last_interval_date: datetime
    interval: SubscriptionIntervalType
    note: Optional[str] = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool
    invoices: list[SubscriptionInvoice]
    payments: list


class InvoiceCreateResponse(BaseModel):
    subscription: Optional[Subscription] = None
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
    payment_type: TransactionType
    next_payment_date: Optional[date] = None
    next_payment_datetime: Optional[datetime] = None
    card_transactions: list[CardTransaction]
    p2p_transactions: list[P2PTransaction]


class PaymentList(BaseModel):
    payment_id: str
    payment_date: datetime
    payment_status: PaymentStatus
    payment_fee: Decimal
    payment_amount: Decimal
    payment_currency: Currency
    payment_wallet: str
    payment_name: str
    payment_description: str
    next_payment_date: Optional[date] = None
    next_payment_datetime: Optional[datetime] = None
    paid_by: TransactionType
    object_type: ObjectType
    object_id: str


class PaymentGetResponse(BaseModel):
    payment_id: str  # p2p -> Decimal | card -> str,UUID
    payment_status: PaymentStatus
    payment_amount: Decimal
    payment_fee: Decimal
    payment_currency: Currency
    payment_date: datetime
    payment_wallet: str
    transaction_type: TransactionType
    object_type: ObjectType
    object_id: str
    next_payment_date: Optional[date] = None
    next_payment_datetime: Optional[datetime] = None
    card_transactions: list[CardTransaction]
    p2p_transactions: list[P2PTransaction]


class Offset(BaseModel):
    page_number: int = Field(ge=1)
    page_limit: int = Field(ge=1, le=1000)


class PaymentRefundRequest(BaseModel):
    note: Optional[str] = Field(default=None, max_length=255)


class PaymentCheckResponse(BaseModel):
    count: int
    paid_amount: Optional[Decimal] = None
    rows: list[Payment]


class PaymentCheckRequest(BaseModel):
    object_type: ObjectType
    object_id: str = Field(max_length=50)
    offset: Offset


class CancelPaymentRequest(Payment):
    callback_url: HttpUrlStr
    note: str


class EbarimtCreateRequest(BaseModel):
    payment_id: str
    ebarimt_receiver_type: EbarimtReceiverType
    ebarimt_receiver: Optional[str] = None
    callback_url: Optional[HttpUrlStr] = None


class Ebarimt(BaseModel):
    id: str
    ebarimt_by: str
    g_wallet_id: str
    g_wallet_customer_id: str
    ebarim_receiver_type: EbarimtReceiverType
    ebarimt_receiver: Optional[str] = None
    ebarimt_district_code: str
    ebarimt_bill_type: str
    g_merchant_id: str
    merchant_branch_code: str
    merchant_terminal_code: Optional[str] = None
    merchant_staff_code: Optional[str] = None
    merchant_register: Optional[Decimal] = None
    g_payment_id: Decimal
    paid_by: TransactionType
    object_type: ObjectType
    object_id: str
    amount: Decimal
    vat_amount: Decimal
    city_tax_amount: Decimal
    ebarimt_qr_data: str
    ebarimt_lottery: str
    note: Optional[str] = None
    ebarimt_status: str
    ebarimt_status_date: datetime
    tax_type: str
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool


class EbarimtGetResponse(Ebarimt):
    pass


class EbarimtCreateResponse(Ebarimt):
    pass


class PaymentListRequest(BaseModel):
    object_type: ObjectType
    object_id: str
    start_date: datetime
    end_date: datetime
    offset: Offset


class PaymentListResponse(BaseModel):
    count: int
    rows: list[PaymentList]


class PaymentCancelRequest(BaseModel):
    callback_url: Optional[HttpUrlStr] = None
    note: Optional[str] = None


class InvoiceGetResponse(BaseModel):
    invoice_id: str
    invoice_status: InvoiceStatus
    sender_invoice_no: str = Field(max_length=45)
    sender_branch_code: Optional[str] = Field(default=None, max_length=45)
    sender_branch_data: Optional[SenderBranchData] = None
    sender_staff_code: Optional[str] = Field(default=None, max_length=100)
    sender_staff_data: Optional[SenderStaffData] = None
    sender_terminal_code: Optional[str] = Field(default=None, max_length=45)
    sender_terminal_data: Optional[SenderTerminalData] = None
    invoice_description: str = Field(max_length=255)
    invoice_due_date: Optional[datetime] = None
    enable_expiry: Optional[bool] = None
    expiry_date: Optional[datetime] = None
    minimum_amount: Optional[Decimal] = None
    maximum_amount: Optional[Decimal] = None
    allow_partial: Optional[bool] = None
    allow_exceed: Optional[bool] = None
    total_amount: Decimal
    gross_amount: Decimal
    tax_amount: Decimal
    surcharge_amount: Decimal
    callback_url: HttpUrlStr
    note: Optional[str] = None
    lines: Optional[list[Line]] = None
    transactions: Optional[list[Transaction]] = None
    inputs: list
    payments: Optional[list[Payment]] = None
