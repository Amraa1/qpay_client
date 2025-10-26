import pytest

from qpay_client.v2.auth import QpayAuthState, _normalize_to_capital
from qpay_client.v2.error import AuthError
from qpay_client.v2.schemas import TokenResponse


def test_normalize_to_capital():
    assert _normalize_to_capital("bearer") == "Bearer"
    assert _normalize_to_capital("BeArEr") == "Bearer"
    assert _normalize_to_capital("") == ""


def test_has_and_get_access_token_success():
    state = QpayAuthState(access_token="token123")
    assert state.has_access_token() is True
    assert state.get_access_token() == "token123"


def test_get_access_token_raises_when_missing():
    state = QpayAuthState()
    with pytest.raises(AuthError):
        state.get_access_token()


def test_access_and_refresh_as_header_use_normalized_token_type():
    state = QpayAuthState(token_type="bearer", access_token="a1", refresh_token="r1")
    assert state.access_as_header() == "Bearer a1"
    assert state.refresh_as_header() == "Bearer r1"

    # if already capitalized, should remain correct
    state.token_type = "Token"
    assert state.access_as_header() == "Token a1"


def test_is_access_and_refresh_expired_with_default_and_custom_leeway(monkeypatch):
    now = 1_000_000.0
    monkeypatch.setattr("time.time", lambda: now)

    state = QpayAuthState()

    # With expiry soon (now + 30) and default leeway 60 -> considered expired
    state.access_token_expiry = now + 30
    assert state.is_access_expired() is True

    # With expiry later (now + 120) and default leeway 60 -> not expired
    state.access_token_expiry = now + 120
    assert state.is_access_expired() is False

    # Custom leeway can change result
    state.access_token_expiry = now + 65
    assert state.is_access_expired(leeway=60) is False
    assert state.is_access_expired(leeway=70) is True

    # Same checks for refresh token
    state.refresh_token_expiry = now + 30
    assert state.is_refresh_expired() is True
    state.refresh_token_expiry = now + 120
    assert state.is_refresh_expired() is False


def test_update_populates_fields_from_token_response():
    token_response = TokenResponse(
        token_type="bearer",
        access_token="acc_tok",
        expires_in=1234,
        refresh_token="ref_tok",
        refresh_expires_in=2345,
        scope="read write",
        **{"not-before-policy": "0"},
        session_state="sess123",
    )

    state = QpayAuthState()
    state.update(token_response)

    assert state.token_type == "Bearer"
    assert state.access_token == "acc_tok"
    assert state.access_token_expiry == 1234
    assert state.refresh_token == "ref_tok"
    assert state.refresh_token_expiry == 2345
    assert state.scope == "read write"
    assert state.not_before_policy == "0"
    assert state.session_state == "sess123"
