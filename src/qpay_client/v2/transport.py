"""Reusable HTTP transports for sync and async QPay clients."""

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Optional

from httpx import AsyncClient, Client, RequestError, Response

from .error import NetworkError
from .settings import QPaySettings
from .utils import exponential_backoff, handle_error

SyncRefreshHandler = Callable[[], None]
AsyncRefreshHandler = Callable[[], Awaitable[None]]


class SyncTransport:
    """Shared synchronous HTTP transport logic."""

    def __init__(
        self,
        settings: QPaySettings,
        logger: logging.Logger,
        client: Optional[Client] = None,
    ) -> None:
        self._client = client or Client(
            base_url=settings.base_url,
            timeout=settings.timeout,
            limits=settings.limits,
        )
        self._settings = settings
        self._logger = logger

    @property
    def client(self) -> Client:
        return self._client

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    def close(self) -> None:
        if not self.is_closed:
            self._client.close()

    def _sleep(self, attempt: int) -> None:
        time.sleep(
            exponential_backoff(
                self._settings.client_delay,
                attempt,
                self._settings.client_jitter,
            )
        )

    def _send(self, method: str, url: str, **kwargs: Any) -> Response:
        self._logger.debug("Request: %s %s", method, url)
        response = self._client.request(method, url, **kwargs)
        self._logger.debug("Response: %s %s", response.status_code, url)

        return response

    def request(
        self,
        method: str,
        url: str,
        *,
        on_unauthorized: Optional[SyncRefreshHandler] = None,
        **kwargs: Any,
    ) -> Response:
        response: Optional[Response] = None

        for attempt in range(self._settings.client_retries + 1):
            try:
                response = self._send(method, url, **kwargs)

                if response.status_code == 401 and on_unauthorized is not None:
                    self._logger.info("401 received, refreshing access token")
                    on_unauthorized()
                    response = self._send(method, url, **kwargs)
                    self._logger.debug("Response after refresh: %s %s", response.status_code, url)

            except RequestError as exc:
                if attempt < self._settings.client_retries:
                    self._logger.error(
                        "Network error on %s %s: %s. Retrying (%d/%d)",
                        method,
                        url,
                        exc,
                        attempt + 1,
                        self._settings.client_retries,
                    )
                    self._sleep(attempt + 1)
                    continue

                self._logger.error("Network error on %s %s: %s", method, url, exc)
                raise NetworkError(str(exc)) from exc

            if response.is_server_error and attempt < self._settings.client_retries:
                self._logger.warning(
                    "Retrying %s %s (attempt %d/%d)",
                    method,
                    url,
                    attempt + 1,
                    self._settings.client_retries,
                )
                self._sleep(attempt + 1)
                continue

            break

        if response is None:
            raise NetworkError(f"Transport failed before receiving a response for {method} {url}")

        if response.is_error:
            handle_error(response, self._logger)

        return response


class AsyncTransport:
    """Shared asynchronous HTTP transport logic."""

    def __init__(
        self,
        *,
        settings: QPaySettings,
        logger: logging.Logger,
        client: Optional[AsyncClient] = None,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._client = client or AsyncClient(
            base_url=settings.base_url,
            timeout=settings.timeout,
            limits=settings.limits,
        )

    @property
    def client(self) -> AsyncClient:
        return self._client

    @property
    def settings(self) -> QPaySettings:
        return self._settings

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    async def close(self) -> None:
        if not self.is_closed:
            await self._client.aclose()

    async def _sleep(self, attempt: int) -> None:
        await asyncio.sleep(
            exponential_backoff(
                self._settings.client_delay,
                attempt,
                self._settings.client_jitter,
            )
        )

    async def _send(self, method: str, url: str, **kwargs: Any) -> Response:
        self._logger.debug("Request: %s %s", method, url)
        response = await self._client.request(method, url, **kwargs)
        self._logger.debug("Response: %s %s", response.status_code, url)

        return response

    async def request(
        self,
        method: str,
        url: str,
        *,
        on_unauthorized: Optional[AsyncRefreshHandler] = None,
        **kwargs: Any,
    ) -> Response:
        response: Optional[Response] = None

        for attempt in range(self._settings.client_retries + 1):
            try:
                response = await self._send(method, url, **kwargs)

                if response.status_code == 401 and on_unauthorized is not None:
                    self._logger.info("401 received, refreshing access token")
                    await on_unauthorized()
                    response = await self._send(method, url, **kwargs)
                    self._logger.debug("Response after refresh: %s %s", response.status_code, url)

            except RequestError as exc:
                if attempt < self._settings.client_retries:
                    self._logger.warning(
                        "Network error on %s %s: %s. Retrying (%d/%d)",
                        method,
                        url,
                        exc,
                        attempt + 1,
                        self._settings.client_retries,
                    )
                    await self._sleep(attempt + 1)
                    continue

                self._logger.error("Network error on %s %s: %s", method, url, exc)
                raise NetworkError(str(exc)) from exc

            if response.is_server_error and attempt < self._settings.client_retries:
                self._logger.warning(
                    "Retrying %s %s (attempt %d/%d)",
                    method,
                    url,
                    attempt + 1,
                    self._settings.client_retries,
                )
                await self._sleep(attempt + 1)
                continue

            break

        if response is None:
            raise NetworkError(f"Transport failed before receiving a response for {method} {url}")

        if response.is_error:
            handle_error(response, self._logger)

        return response
