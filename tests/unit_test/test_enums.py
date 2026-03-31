from qpay_client.v2.enums import (
    Currency,
    EbarimtReceiverType,
    KnownProviderCode,
    ObjectType,
    PaymentStatus,
    TaxType,
    TransactionType,
)


def test_currency_enum():
    assert Currency.mnt == "MNT"
    assert Currency.usd == "USD"
    assert Currency.cny == "CNY"
    assert Currency.jpy == "JPY"
    assert Currency.rub == "RUB"
    assert Currency.eur == "EUR"


def test_transaction_type_enum():
    assert TransactionType.p2p == "P2P"
    assert TransactionType.card == "CARD"


def test_payment_status_enum():
    assert PaymentStatus.new == "NEW"
    assert PaymentStatus.failed == "FAILED"
    assert PaymentStatus.paid == "PAID"
    assert PaymentStatus.partial == "PARTIAL"
    assert PaymentStatus.refund == "REFUND"


def test_ebarimt_receiver_type_enum():
    assert EbarimtReceiverType.citizen == "CITIZEN"
    assert EbarimtReceiverType.company == "COMPANY"


def test_bank_code_enum():
    assert KnownProviderCode.bank_of_mongolia == "010000"
    assert KnownProviderCode.capital_bank == "020000"
    assert KnownProviderCode.khan_bank == "050000"
    assert KnownProviderCode.golomt_bank == "150000"
    assert KnownProviderCode.monpay == "990000"
    assert KnownProviderCode.test_bank == "100000"


def test_known_provider_code_aliases_bank_code():
    assert KnownProviderCode is KnownProviderCode
    assert KnownProviderCode.khan_bank == KnownProviderCode.khan_bank


def test_object_type_enum():
    assert ObjectType.invoice == "INVOICE"
    assert ObjectType.qr == "QR"
    assert ObjectType.item == "ITEM"


def test_tax_type_enum():
    assert TaxType.with_tax == "1"
    assert TaxType.without_tax == "2"
    assert TaxType.exclude_tax == "3"
