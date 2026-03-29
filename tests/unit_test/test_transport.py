import logging

import httpx
import pytest
from httpx import Response

from qpay_client.v2.error import NetworkError, QPayError
from qpay_client.v2.settings import QPaySettings
from qpay_client.v2.transport import AsyncTransport, SyncTransport


def make_settings(**overrides):
    values = {
        "username": "user",
        "password": "pass",
        "invoice_code": "INV",
        "base_url": "https://merchant-sandbox.qpay.mn/v2",
        "client_retries": 1,
        "client_delay": 0.0,
        "client_jitter": 0.0,
    }
    values.update(overrides)
    return QPaySettings(**values)


def test_sync_transport_replays_after_401(monkeypatch):
    transport = SyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.sync.401"))
    monkeypatch.setattr("qpay_client.v2.transport.time.sleep", lambda *_args, **_kwargs: None)

    calls = {"count": 0, "refresh": 0}

    def fake_request(method, url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return Response(401, json={"message": "expired"})
        return Response(200, json={"ok": True})

    def refresh():
        calls["refresh"] += 1

    monkeypatch.setattr(transport.client, "request", fake_request)

    response = transport.request("GET", "/invoice/123", on_unauthorized=refresh)

    assert response.status_code == 200
    assert calls["count"] == 2
    assert calls["refresh"] == 1

    transport.close()


def test_sync_transport_retries_network_error(monkeypatch):
    transport = SyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.sync.network"))
    monkeypatch.setattr("qpay_client.v2.transport.time.sleep", lambda *_args, **_kwargs: None)

    request = httpx.Request("GET", "https://merchant-sandbox.qpay.mn/v2/invoice/123")
    calls = {"count": 0}

    def fake_request(method, url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return Response(200, json={"ok": True})

    monkeypatch.setattr(transport.client, "request", fake_request)

    response = transport.request("GET", "/invoice/123")

    assert response.status_code == 200
    assert calls["count"] == 2

    transport.close()


def test_sync_transport_raises_network_error_after_retries(monkeypatch):
    transport = SyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.sync.exhaust"))
    monkeypatch.setattr("qpay_client.v2.transport.time.sleep", lambda *_args, **_kwargs: None)

    request = httpx.Request("GET", "https://merchant-sandbox.qpay.mn/v2/invoice/123")

    def fake_request(method, url, **kwargs):
        raise httpx.ConnectError("boom", request=request)

    monkeypatch.setattr(transport.client, "request", fake_request)

    with pytest.raises(NetworkError):
        transport.request("GET", "/invoice/123")

    transport.close()


def test_sync_transport_retries_server_error_then_raises_qpay_error(monkeypatch):
    transport = SyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.sync.server"))
    monkeypatch.setattr("qpay_client.v2.transport.time.sleep", lambda *_args, **_kwargs: None)

    calls = {"count": 0}

    def fake_request(method, url, **kwargs):
        calls["count"] += 1
        return Response(500, json={"message": "INTERNAL_ERROR"})

    monkeypatch.setattr(transport.client, "request", fake_request)

    with pytest.raises(QPayError):
        transport.request("GET", "/invoice/123")

    assert calls["count"] == 2

    transport.close()


@pytest.mark.asyncio
async def test_async_transport_retries_network_error(monkeypatch):
    transport = AsyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.async.network"))

    async def immediate_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr("qpay_client.v2.transport.asyncio.sleep", immediate_sleep)

    request = httpx.Request("GET", "https://merchant-sandbox.qpay.mn/v2/invoice/123")
    calls = {"count": 0}

    async def fake_request(method, url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return Response(200, json={"ok": True})

    monkeypatch.setattr(transport.client, "request", fake_request)

    response = await transport.request("GET", "/invoice/123")

    assert response.status_code == 200
    assert calls["count"] == 2

    await transport.close()


@pytest.mark.asyncio
async def test_async_transport_replays_after_401(monkeypatch):
    transport = AsyncTransport(settings=make_settings(), logger=logging.getLogger("qpay.test.async.401"))

    async def immediate_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr("qpay_client.v2.transport.asyncio.sleep", immediate_sleep)

    calls = {"count": 0, "refresh": 0}

    async def fake_request(method, url, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return Response(401, json={"message": "expired"})
        return Response(200, json={"ok": True})

    async def refresh():
        calls["refresh"] += 1

    monkeypatch.setattr(transport.client, "request", fake_request)

    response = await transport.request("GET", "/invoice/123", on_unauthorized=refresh)

    assert response.status_code == 200
    assert calls["count"] == 2
    assert calls["refresh"] == 1

    await transport.close()
