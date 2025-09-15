import json
import time

import pytest
import respx
from httpx import Response


@pytest.fixture(autouse=True)
def respx_auto_mock():
    # Automatically mock httpx for all tests
    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def token_payload():
    # Mirrors your pydantic TokenResponse shape (including alias name)
    return {
        "token_type": "bearer",
        "access_token": "access123",
        "expires_in": 3600,
        "refresh_token": "refresh123",
        "refresh_expires_in": 7200,
        "scope": "read write",
        "not-before-policy": "0",
        "session_state": "abc-session",
    }


@pytest.fixture
def frozen_time(monkeypatch):
    # Start time=0 so the set expiry (e.g., 3600 - leeway) is "in the future".
    monkeypatch.setattr(time, "time", lambda: 0)
    return lambda t: monkeypatch.setattr(time, "time", lambda: t)


def as_json_string_body(payload: dict) -> bytes:
    """
    Your clients call `model_validate_json(response.json())`, which expects a JSON string.
    We therefore make `response.json()` return a *string* (containing JSON) by
    sending a JSON-encoded string value as the HTTP body (e.g. "\"{...}\"").
    """
    # body content like: "\"{ ... }\""  => .json() -> Python str -> ok for model_validate_json
    return json.dumps(json.dumps(payload)).encode("utf-8")


def as_json_body(payload: dict) -> bytes:
    """Normal JSON body (used for error responses where .json() must be a dict)."""
    return json.dumps(payload).encode("utf-8")


@pytest.fixture
def sandbox_base() -> str:
    return "https://merchant-sandbox.qpay.mn/v2"


@pytest.fixture
def prod_base() -> str:
    return "https://merchant.qpay.mn/v2"


def expect_auth_token(mock, base_url, token_payload):
    mock.post(f"{base_url}/auth/token").mock(
        return_value=Response(200, content=as_json_body(token_payload))
    )


def expect_auth_refresh(mock, base_url, token_payload):
    mock.post(f"{base_url}/auth/refresh").mock(
        return_value=Response(200, content=as_json_body(token_payload))
    )
