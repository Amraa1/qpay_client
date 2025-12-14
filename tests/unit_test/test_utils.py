from logging import Logger
from unittest.mock import Mock

import pytest

from qpay_client.v2.error import QPayError
from qpay_client.v2.utils import exponential_backoff, handle_error, safe_json


class DummyResponse:
    def __init__(self, json_data=None, text="", status_code=400, raise_json=False):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("Invalid JSON")
        return self._json_data


def test_safe_json_valid_json():
    resp = DummyResponse(json_data={"key": "value"})
    assert safe_json(resp) == {"key": "value"}


def test_safe_json_invalid_json():
    resp = DummyResponse(text="not json", raise_json=True)
    assert safe_json(resp) == {"message": "not json"}


def test_handle_error_logs_and_raises(monkeypatch):
    resp = DummyResponse(json_data={"message": "error occurred"}, status_code=500)
    logger = Mock(spec=Logger)
    with pytest.raises(QPayError) as exc:
        handle_error(resp, logger)
    logger.error.assert_called_once()
    assert exc.value.status_code == 500
    assert exc.value.error_key == "error occurred"


def test_handle_error_with_no_message(monkeypatch):
    resp = DummyResponse(json_data={}, status_code=404)
    logger = Mock(spec=Logger)
    with pytest.raises(QPayError) as exc:
        handle_error(resp, logger)
    logger.error.assert_called_once()
    assert exc.value.status_code == 404
    assert exc.value.error_key == ""


def test_exponential_backoff():
    base = 10
    jitter = 0.5

    for attempt in range(1, 6):
        delay = exponential_backoff(base, attempt, jitter)
        assert base * (2 ** (attempt - 1)) < delay < base * (2 ** (attempt - 1)) + jitter
