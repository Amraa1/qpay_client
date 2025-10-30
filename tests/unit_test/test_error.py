import pytest

from qpay_client.v2.error import AuthError, ClientConfigError, QPayError


def test_qpay_error_attributes_and_repr():
    err = QPayError(status_code=404, error_key="not_found")
    expected = "status_code: 404, error_key: not_found, error_description: No description."
    assert err.status_code == 404
    assert err.error_key == "not_found"
    assert hasattr(err, "exception_message")
    assert err.exception_message == expected
    assert repr(err) == expected
    assert str(err) == expected


def test_qpay_error_raises_with_message():
    with pytest.raises(QPayError) as exc:
        raise QPayError(status_code=500, error_key="server_error")
    assert str(exc.value) == "status_code: 500, error_key: server_error, error_description: No description."


def test_client_config_error_message_and_str():
    ce = ClientConfigError("host", "port")
    assert hasattr(ce, "exception_message")
    assert ce.exception_message == "incorrect attributes: ('host', 'port')"
    assert str(ce) == "incorrect attributes: ('host', 'port')"

    # also when raised
    with pytest.raises(ClientConfigError) as exc:
        raise ClientConfigError("x")
    assert str(exc.value) == "incorrect attributes: ('x',)"


def test_auth_error_message_and_str():
    ae = AuthError("token expired")
    assert str(ae) == "token expired"

    with pytest.raises(AuthError) as exc:
        raise AuthError("invalid credentials")
    assert str(exc.value) == "invalid credentials"
