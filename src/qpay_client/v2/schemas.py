"""Pydantic schemas for QPay v2."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from .enums import (
    Currency,
    EbarimtReceiverType,
    InvoiceStatus,
    ObjectType,
    PaymentStatus,
    TaxCode,
    TaxType,
    TransactionType,
)
from .types import HttpUrlStr, ProviderCode, SubscriptionIntervalType


class TokenResponse(BaseModel):
    """
    QPay Token and Refresh token response.

    Note on token expiry fields:
        Despite being named `expires_in` and `refresh_expires_in`, the QPay v2 API
        returns **Unix epoch timestamps** (seconds since 1970-01-01 UTC), NOT
        relative seconds-until-expiry as defined by the OAuth 2.0 spec (RFC 6749).

        These values are stored as `access_expires_at` and `refresh_expires_at` to
        reflect their true meaning and are compared directly against `time.time()`
        in `QpayAuthState.is_access_expired()` and `is_refresh_expired()`.
    """

    model_config = ConfigDict(validate_by_alias=True)

    token_type: str
    access_token: str
    # QPay returns a Unix epoch timestamp here, not relative seconds (non-standard OAuth).
    access_expires_at: float = Field(..., alias="expires_in")
    refresh_token: str
    # QPay returns a Unix epoch timestamp here, not relative seconds (non-standard OAuth).
    refresh_expires_at: float = Field(..., alias="refresh_expires_in")
    scope: str
    not_before_policy: str = Field(..., alias="not-before-policy")
    session_state: str


class QPayDeeplink(BaseModel):
    name: str
    description: str
    logo: str
    link: str


class Address(BaseModel):
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    street: str | None = Field(default=None, max_length=100)
    building: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=100)
    zipcode: str | None = Field(default=None, max_length=20)
    longitude: str | None = Field(default=None, max_length=20)
    latitude: str | None = Field(default=None, max_length=20)


class SenderTerminalData(BaseModel):
    name: str | None = Field(default=None, max_length=100)


class InvoiceReceiverData(BaseModel):
    model_config = ConfigDict(validate_by_alias=True)

    registration_number: str | None = Field(default=None, alias="register", max_length=20)
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    address: Address | None = None


class SenderBranchData(BaseModel):
    model_config = ConfigDict(validate_by_alias=True)

    registration_number: str | None = Field(default=None, alias="register", max_length=20)
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    address: Address | None = None


class Discount(BaseModel):
    discount_code: str | None = Field(default=None, max_length=45)
    description: str = Field(max_length=100)
    amount: Decimal = Field(max_digits=20)
    note: str | None = Field(default=None, max_length=255)


class Surcharge(BaseModel):
    surcharge_code: str | None = Field(default=None, max_length=45)
    description: str = Field(max_length=100)
    amount: Decimal = Field(max_digits=20)
    note: str | None = Field(default=None, max_length=255)


class Tax(BaseModel):
    tax_code: TaxCode | None = None
    description: str | None = Field(default=None, max_length=100)
    amount: Decimal
    note: str | None = Field(default=None, max_length=255)


class Account(BaseModel):
    account_bank_code: ProviderCode = Field(
        description="QPay provider code. Use BankCode/KnownProviderCode for known values when convenient."
    )
    account_number: str = Field(max_length=100)
    account_name: str = Field(max_length=100)
    account_currency: Currency
    is_default: bool


class Line(BaseModel):
    sender_product_code: str | None = None
    tax_product_code: str | None = None
    line_description: str = Field(max_length=255)
    line_quantity: Decimal = Field(max_digits=20)
    line_unit_price: Decimal = Field(max_digits=20)
    note: str | None = Field(default=None, max_length=100)
    discounts: list[Discount] | None = None
    surcharges: list[Surcharge] | None = None
    taxes: list[Tax] | None = None


class Transaction(BaseModel):
    description: str = Field(max_length=100)
    amount: Decimal
    accounts: list[Account] | None = None


class SenderStaffData(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)


class InvoiceCreateSimpleRequest(BaseModel):
    """Create simple invoice."""

    invoice_code: str | None = Field(default=None, examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(examples=["123"], max_length=45)
    invoice_receiver_code: str = Field(max_length=45)
    invoice_description: str = Field(max_length=255)
    sender_branch_code: str | None = Field(default=None, max_length=45)
    amount: Decimal = Field(gt=0)
    callback_url: HttpUrlStr


class InvoiceCreateRequest(BaseModel):
    """Create full invoice."""

    invoice_code: str | None = Field(default=None, examples=["TEST_INVOICE"], max_length=45)
    sender_invoice_no: str = Field(max_length=45)
    invoice_receiver_code: str = Field(max_length=45)
    invoice_description: str = Field(max_length=255)
    callback_url: HttpUrlStr

    amount: Decimal | None = Field(default=None, gt=0)
    sender_branch_code: str | None = Field(default=None, max_length=45)
    sender_branch_data: SenderBranchData | None = None
    sender_staff_code: str | None = Field(default=None, max_length=100)
    sender_staff_data: SenderStaffData | None = None
    sender_terminal_code: str | None = Field(default=None, max_length=45)
    sender_terminal_data: SenderTerminalData | None = None
    invoice_receiver_data: InvoiceReceiverData | None = None
    invoice_due_date: datetime | None = None
    enable_expiry: bool | None = None
    expiry_date: datetime | None = None
    calculate_vat: bool | None = None
    tax_type: TaxType | None = None
    tax_customer_code: str | None = None
    line_tax_code: str | None = None
    minimum_amount: Decimal | None = None
    maximum_amount: Decimal | None = None
    allow_partial: bool | None = None
    allow_exceed: bool | None = None
    allow_subscribe: bool | None = None
    subscription_interval: SubscriptionIntervalType | None = None
    subscription_webhook: HttpUrlStr | None = None
    note: str | None = Field(default=None, max_length=1000)
    lines: list[Line] | None = None
    transactions: list[Transaction] | None = None

    @model_validator(mode="after")
    def check_amount_or_lines(self) -> Self:
        if self.amount or self.lines:
            return self
        else:
            raise ValueError("At least one of amount and lines must have valid value.")

    @model_validator(mode="after")
    def validate_when_subcription_allowed(self) -> Self:
        if self.allow_subscribe:
            if not self.subscription_interval or not self.subscription_webhook:
                raise ValueError(
                    "When allow_subscription is 'True', subscription_interval and subscription_webhook must have valid values."
                )
            elif not self.lines:
                raise ValueError("When allow_subscription is 'True', lines must have atleast one value.")
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
    next_payment_date: datetime | None = None
    note: str | None = None


class QpayInvoiceLineBase(BaseModel):
    id: str
    g_merchant_id: str
    invoice_id: str
    invoice_line_id: str
    description: str
    amount: Decimal
    note: str | None = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool


class InvoiceDiscount(QpayInvoiceLineBase):
    discount_code: str | None = None


class InvoiceTax(QpayInvoiceLineBase):
    tax_code: TaxCode | None = None
    city_tax: Decimal


class InvoiceSurcharge(QpayInvoiceLineBase):
    surcharge_code: str | None = None


class InvoiceLine(BaseModel):
    id: str
    g_merchant_id: str
    invoice_id: str
    customer_product_code: str | None = None
    tax_product_code: str | None = None
    barcode: str | None = None
    classification_code: str | None = None
    line_description: str | None = None
    line_quantity: Decimal
    line_unit_price: Decimal
    note: str | None = None
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
    sender_logo: str | None = None
    sender_branch_code: str | None = Field(default=None, max_length=45)
    sender_branch_data: SenderBranchData | None = None
    sender_staff_code: str | None = Field(default=None, max_length=100)
    sender_staff_data: SenderStaffData | None = None
    sender_terminal_code: str | None = Field(default=None, max_length=45)
    sender_terminal_data: SenderTerminalData | None = None
    invoice_receiver_data: InvoiceReceiverData | None = None
    invoice_description: str = Field(max_length=255)
    invoice_due_date: datetime | None = None
    enable_expiry: bool | None = None
    expiry_date: datetime | None = None
    calculate_vat: bool | None = None
    tax_type: TaxType | None = None
    tax_customer_code: str | None = None
    line_tax_code: str | None = None
    minimum_amount: Decimal | None = None
    maximum_amount: Decimal | None = None
    receiver_code: str
    receiver_date: InvoiceReceiverData | None = None
    invoice_no: str
    invoice_date: date
    invoice_name: str | None = None
    invoice_currency: Currency
    invoice_status: InvoiceStatus
    invoice_status_date: datetime
    has_ebarimt: bool
    has_vat: bool
    ebarimt_by: str | None = None
    ebarimt_customer_code: str | None = None
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
    service_fee_method: str | None = None
    service_fee_calc_type: str | None = None
    service_fee_onus: str | None = None
    service_fee_offus: str | None = None
    with_tag: bool
    tag: str | None = None
    short_url: str | None = None
    package_id: str | None = None
    sub_package_id: str | None = None
    note: str | None = None
    district_code: str | None = None
    extra: str | None = None
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
    next_payment_date: datetime | None = None
    start_date: datetime
    last_interval_date: datetime
    interval: SubscriptionIntervalType
    note: str | None = None
    created_by: str
    created_date: datetime
    updated_by: str
    updated_date: datetime
    status: bool
    invoices: list[SubscriptionInvoice]
    payments: list


class InvoiceCreateResponse(BaseModel):
    subscription: Subscription | None = None
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
    transaction_bank_code: ProviderCode = Field(
        description="QPay provider code. Use BankCode/KnownProviderCode for known values when convenient."
    )
    account_bank_code: ProviderCode = Field(
        description="QPay provider code. Use BankCode/KnownProviderCode for known values when convenient."
    )
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
    next_payment_date: date | None = None
    next_payment_datetime: datetime | None = None
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
    next_payment_date: date | None = None
    next_payment_datetime: datetime | None = None
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
    next_payment_date: date | None = None
    next_payment_datetime: datetime | None = None
    card_transactions: list[CardTransaction]
    p2p_transactions: list[P2PTransaction]


class Offset(BaseModel):
    page_number: int = Field(ge=1)
    page_limit: int = Field(ge=1, le=1000)


class PaymentRefundRequest(BaseModel):
    note: str | None = Field(default=None, max_length=255)


class PaymentCheckResponse(BaseModel):
    count: int
    paid_amount: Decimal | None = None
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
    ebarimt_receiver: str | None = None
    callback_url: HttpUrlStr | None = None


class Ebarimt(BaseModel):
    id: str
    ebarimt_by: str
    g_wallet_id: str
    g_wallet_customer_id: str
    ebarim_receiver_type: EbarimtReceiverType
    ebarimt_receiver: str | None = None
    ebarimt_district_code: str
    ebarimt_bill_type: str
    g_merchant_id: str
    merchant_branch_code: str
    merchant_terminal_code: str | None = None
    merchant_staff_code: str | None = None
    merchant_register: Decimal | None = None
    g_payment_id: Decimal
    paid_by: TransactionType
    object_type: ObjectType
    object_id: str
    amount: Decimal
    vat_amount: Decimal
    city_tax_amount: Decimal
    ebarimt_qr_data: str
    ebarimt_lottery: str
    note: str | None = None
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
    callback_url: HttpUrlStr | None = None
    note: str | None = None


class InvoiceGetResponse(BaseModel):
    invoice_id: str
    invoice_status: InvoiceStatus
    sender_invoice_no: str = Field(max_length=45)
    sender_branch_code: str | None = Field(default=None, max_length=45)
    sender_branch_data: SenderBranchData | None = None
    sender_staff_code: str | None = Field(default=None, max_length=100)
    sender_staff_data: SenderStaffData | None = None
    sender_terminal_code: str | None = Field(default=None, max_length=45)
    sender_terminal_data: SenderTerminalData | None = None
    invoice_description: str = Field(max_length=255)
    invoice_due_date: datetime | None = None
    enable_expiry: bool | None = None
    expiry_date: datetime | None = None
    minimum_amount: Decimal | None = None
    maximum_amount: Decimal | None = None
    allow_partial: bool | None = None
    allow_exceed: bool | None = None
    total_amount: Decimal
    gross_amount: Decimal
    tax_amount: Decimal
    surcharge_amount: Decimal
    callback_url: HttpUrlStr
    note: str | None = None
    lines: list[Line] | None = None
    transactions: list[Transaction] | None = None
    inputs: list
    payments: list[Payment] | None = None
