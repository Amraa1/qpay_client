# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`qpay-client` is a Python library for integrating with the QPay v2 payment API (Mongolian payment provider). It provides both async and sync clients, Pydantic-validated schemas, automatic token management, and retry logic. Supports Python 3.9–3.14.

## Commands

This project uses `uv` for package management.

```bash
# Install dependencies
uv sync

# Run all unit tests
uv run pytest

# Run only unit tests (exclude integration tests)
uv run pytest tests/unit_test/

# Run a single test file
uv run pytest tests/unit_test/test_sync.py

# Run a single test by name
uv run pytest tests/unit_test/test_sync.py::test_name

# Run integration tests (requires QPay sandbox credentials)
uv run pytest -m integration

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/
```

## Architecture

### Source layout

All library code is in `src/qpay_client/v2/`. The public API is re-exported from `src/qpay_client/v2/__init__.py`.

### Key modules

- **`settings.py`** — `QPaySettings` (frozen dataclass). Never instantiate directly; use `QPaySettings.sandbox()` or `QPaySettings.production()`. Controls base URL, credentials, retry counts, delays, and jitter for both client retries and `payment_check` polling.

- **`clients/base.py`** — `BaseClient` (abstract). Holds auth state, settings, and the header-building logic. Shared by sync and async clients.

- **`clients/client.py`** — `QPayClient` (sync). Use as a context manager (`with QPayClient(...) as client`). Authenticates on `__enter__`.

- **`clients/async_client.py`** — `AsyncQPayClient` (async). Use as `async with AsyncQPayClient(...) as client`.

- **`clients/decorators.py`** — `@auth_required` / `@async_auth_required`. Applied to all public endpoint methods; automatically calls `authenticate()` before each request.

- **`transport.py`** — `SyncTransport` / `AsyncTransport`. Handles the actual HTTP requests via `httpx`. Implements retry logic for network errors (`RequestError`) and 5xx responses, and automatic token refresh on 401. Neither client nor endpoint code should call `httpx` directly.

- **`auth.py`** — `QpayAuthState`. Stores access/refresh tokens as epoch timestamps and handles expiry checks with a configurable leeway (default 60 s).

- **`schemas.py`** — All Pydantic v2 request/response models. `InvoiceCreateSimpleRequest` is the typical entry point for creating invoices; `InvoiceCreateRequest` is the full version with optional fields. Schemas use `by_alias=True, exclude_none=True, mode="json"` when serializing for API calls.

- **`error.py`** — Exception hierarchy: `QPayError` (API-level errors with `status_code` + `error_key`), `AuthError`, `NetworkError`, `ClientConfigError`. `QpayErrorDetail` maps QPay error keys to English/Mongolian descriptions.

- **`enums.py`** — QPay-specific enums (`ObjectType`, `PaymentStatus`, `InvoiceStatus`, `Currency`, etc.).

- **`types.py`** — Custom type aliases (`HttpUrlStr`, `ProviderCode`, `SubscriptionIntervalType`).

- **`utils.py`** — `exponential_backoff()` (used by both transports and `payment_check` polling) and `handle_error()` (parses error responses into `QPayError`).

### Authentication flow

1. On `__enter__` / `__aenter__`, the client calls `_authenticate()` → `POST /auth/token` with HTTP Basic auth.
2. `QpayAuthState` stores tokens and expiry timestamps.
3. Before each endpoint call, `@auth_required` calls `authenticate()`, which checks expiry and calls `_refresh_access_token()` (`POST /auth/refresh`) or re-authenticates if the refresh token is also expired.
4. If a request returns 401, the transport calls the `on_unauthorized` callback (which is `_refresh_access_token`) and retries once.

### `payment_check` polling

`payment_check` first sends one request; if `count == 0`, it retries up to `payment_check_retries` times with exponential backoff controlled by `payment_check_delay` and `payment_check_jitter` (separate from the general `client_retries` settings).

## Testing

- Unit tests are in `tests/unit_test/` and use `respx` to mock `httpx` calls.
- Integration tests are in `tests/intergartion_test/` and are marked with `@pytest.mark.integration`; they hit the real QPay sandbox.
- `pytest.toml` sets `testpaths = ["tests"]` and default addopts `-ra -q`.
