from enum import Enum


class Currency(str, Enum):
    """Currency code used in QPay."""

    mnt = "MNT"
    usd = "USD"
    cny = "CNY"
    jpy = "JPY"
    rub = "RUB"
    eur = "EUR"


class InvoiceStatus(str, Enum):
    """Invoice status."""

    open = "OPEN"
    closed = "CLOSED"


class TransactionType(str, Enum):
    """The type of payment."""

    p2p = "P2P"
    card = "CARD"


class PaymentStatus(str, Enum):
    """Payment status received from payment get request."""

    new = "NEW"
    failed = "FAILED"
    paid = "PAID"
    partial = "PARTIAL"
    refund = "REFUND"


class EbarimtReceiverType(str, Enum):
    """Ebarimt receiver type."""

    citizen = "CITIZEN"
    company = "COMPANY"


class BankCode(str, Enum):
    """Bank codes provided by QPay."""

    bank_of_mongolia = "010000"
    capital_bank = "020000"
    trade_and_development_bank_of_mongolia = "040000"
    khan_bank = "050000"
    golomt_bank = "150000"
    trans_bank = "190000"
    arig_bank = "210000"
    credit_bank = "220000"
    nib_bank = "290000"
    capitron_bank = "300000"
    khas_bank = "320000"
    chingiskhan_bank = "330000"
    state_bank = "340000"
    national_development_bank = "360000"
    bogd_bank = "380000"
    state_fund = "900000"
    mobi_finance = "500000"
    m_bank = "390000"
    invescore = "993000"
    test_bank = "100000"


class ObjectType(str, Enum):
    """Object types provided by QPay."""

    invoice = "INVOICE"
    qr = "QR"
    item = "ITEM"


class TaxType(str, Enum):
    """QPay tax types."""

    with_tax = "1"
    without_tax = "2"
    exclude_tax = "3"


class TaxCode(str, Enum):
    """QPay tax code."""

    city_tax = "CITY_TAX"
    vat = "VAT"
