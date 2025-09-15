import pytest

from qpay_client.v2.enums import (BankCode, Currency, ObjectTypeNum,  # noqa
                                  PaymentStatus)
from qpay_client.v2.error import ClientConfigError, QPayError  # noqa


def test_enums_values():
    # Sanity: ensure values (partial check)
    assert Currency.mnt == "MNT"
    assert PaymentStatus.paid == "PAID"
    assert BankCode.khan_bank == "050000"
    assert ObjectTypeNum.invoice == "INVOICE"


def test_qpay_error_repr():
    err = QPayError(status_code=401, error_key="INVALID_CREDENTIALS")
    assert "status_code: 401" in repr(err)
    assert "INVALID_CREDENTIALS" in repr(err)
    assert err.status_code == 401
    assert err.error_key == "INVALID_CREDENTIALS"


def test_client_config_error_repr():
    err = ClientConfigError("base_url")
    assert "incorrect attributes" in str(err)
