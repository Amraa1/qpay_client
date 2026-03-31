import asyncio
import logging
from typing import Optional, Union

from httpx import AsyncClient, BasicAuth, Response

from ..schemas import (
    Ebarimt,
    EbarimtCreateRequest,
    InvoiceCreateRequest,
    InvoiceCreateResponse,
    InvoiceCreateSimpleRequest,
    InvoiceGetResponse,
    PaymentCancelRequest,
    PaymentCheckRequest,
    PaymentCheckResponse,
    PaymentGetResponse,
    PaymentListRequest,
    PaymentListResponse,
    PaymentRefundRequest,
    SubscriptionGetResponse,
    TokenResponse,
)
from ..settings import QPaySettings
from ..transport import AsyncTransport
from ..utils import exponential_backoff
from .base import BaseClient
from .decorators import async_auth_required


class AsyncQPayClient(BaseClient):
    """
    Asynchronous client for QPay v2 API.

    This client handles authentication, token refresh, and provides async
    methods for interacting with QPay v2 endpoints (invoices, payments,
    subscriptions, and ebarimt). It is designed to follow the official QPay v2.
    """

    def __init__(
        self,
        settings: QPaySettings,
        *,
        client: Optional[AsyncClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize AsyncQPayClient object.

        Args:
            settings (Settings): QPay client settings.
            client (Optional[httpx.Client]): Optional custom httpx client.
            logger (Optional[logging.Logger]): QPay client logger.

        """
        super().__init__(settings, logger=logger)
        self._transport = AsyncTransport(settings=settings, logger=self._logger, client=client)
        self._client = self._transport.client

        self._async_lock = asyncio.Lock()

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    async def __aenter__(self):
        # client authenticates early here if not authenticated
        if not self.is_authenticated:
            await self._authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close connection."""
        await self._transport.close()

    async def authenticate(self) -> None:
        """Authenticate client."""
        if self.is_authenticated:
            return  # no need to reauthenticate

        if not self._auth_state.has_access_token() or self.is_refresh_expired:
            await self._authenticate()  # first token or refresh token expired
        else:
            await self._refresh_access_token()

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Response:
        return await self._transport.request(
            method,
            url,
            on_unauthorized=self._refresh_access_token,
            **kwargs,
        )

    async def _send(self, method: str, url: str, **kwargs) -> Response:
        return await self._transport._send(method, url, **kwargs)

    async def _authenticate(self) -> None:
        """Authenticate the client. Thread safe."""
        # locked wrapper
        async with self._async_lock:
            await self._authenticate_nolock()

    async def _refresh_access_token(self) -> None:
        """Refresh client access. Thread safe."""
        # locked wrapper
        async with self._async_lock:
            await self._refresh_access_token_nolock()

    async def _authenticate_nolock(self):
        """Authenticate the client. Not thread safe."""
        response = await self._send(
            "POST",
            "/auth/token",
            auth=BasicAuth(
                username=self._settings.username,
                password=self._settings.password,  # get password secret
            ),
        )

        token_response = TokenResponse.model_validate(response.json())

        self._auth_state.update(token_response)

    async def _refresh_access_token_nolock(self):
        """Refresh client access. Not thread safe."""
        if not self._auth_state.is_access_expired(leeway=self._token_leeway):
            return  # access token not expired

        if self._auth_state.is_refresh_expired(leeway=self._token_leeway):
            return await self._authenticate_nolock()

        # Using refresh token
        response = await self._send(
            "POST",
            "/auth/refresh",
            headers={"Authorization": self._auth_state.refresh_as_header()},
        )

        if response.is_success:
            token_response = TokenResponse.model_validate(response.json())

            self._auth_state.update(token_response)
        else:
            await self._authenticate_nolock()

    async def _get_auth_token(self) -> str:
        """Get authenticated access token."""
        if self.is_authenticated:
            return self.token
        await self.authenticate()
        return self.token

    @async_auth_required
    async def invoice_get(self, invoice_id: str):
        """Get invoice by Id."""
        response = await self._request(
            "GET",
            "/invoice/" + invoice_id,
            headers=self.headers(),
        )

        data = InvoiceGetResponse.model_validate(response.json())
        return data

    @async_auth_required
    async def invoice_create(
        self, create_invoice_request: Union[InvoiceCreateRequest, InvoiceCreateSimpleRequest]
    ) -> InvoiceCreateResponse:
        """Send invoice create request to Qpay."""
        response = await self._request(
            "POST",
            "/invoice",
            headers=self.headers(),
            json=self._invoice_create_payload(create_invoice_request),
        )

        data = InvoiceCreateResponse.model_validate(response.json())
        return data

    @async_auth_required
    async def invoice_cancel(
        self,
        invoice_id: str,
    ):
        """Send cancel invoice request to qpay. Returns status code."""
        response = await self._request(
            "DELETE",
            "/invoice/" + invoice_id,
            headers=self.headers(),
        )

        return response.status_code

    @async_auth_required
    async def payment_get(self, payment_id: str):
        """Send get payment requesst to qpay."""
        response = await self._request(
            "GET",
            "/payment/" + payment_id,
            headers=self.headers(),
        )

        data = PaymentGetResponse.model_validate(response.json())
        return data

    @async_auth_required
    async def payment_check(
        self,
        payment_check_request: PaymentCheckRequest,
    ):
        """
        Send check payment request to qpay.

        When payment retries is more than 0, client polls qpay until count > 0 or the retry amount is reached.
        """
        response = await self._request(
            "POST",
            "/payment/check",
            headers=self.headers(),
            json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentCheckResponse.model_validate(response.json())

        if data.count > 0:
            return data

        for attempt in range(1, self._settings.payment_check_retries + 1):
            self._logger.warning(
                "Retrying POST: /payment/check (attempt %d/%d)", attempt, self._settings.payment_check_retries
            )

            await asyncio.sleep(
                exponential_backoff(
                    self._settings.payment_check_delay,
                    attempt,
                    self._settings.payment_check_jitter,
                )
            )

            response = await self._request(
                "POST",
                "/payment/check",
                headers=self.headers(),
                json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
            )

            self._logger.debug(
                "Retry %s response: %s /payment/check",
                attempt,
                response.status_code,
            )

            data = PaymentCheckResponse.model_validate(response.json())

            if data.count > 0:
                break

        return data

    @async_auth_required
    async def payment_cancel(
        self,
        payment_id: str,
        payment_cancel_request: PaymentCancelRequest,
    ) -> int:
        """Send payment cancel request. Returns status code."""
        response = await self._request(
            "DELETE",
            "/payment/cancel/" + payment_id,
            headers=self.headers(),
            json=payment_cancel_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    @async_auth_required
    async def payment_refund(
        self,
        payment_id: str,
        payment_refund_request: PaymentRefundRequest,
    ):
        """Send refund payment request. Returns status code."""
        response = await self._request(
            "DELETE",
            "/payment/refund/" + payment_id,
            headers=self.headers(),
            json=payment_refund_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    @async_auth_required
    async def payment_list(self, payment_list_request: PaymentListRequest):
        """Send list payment request."""
        response = await self._request(
            "POST",
            "/payment/list",
            headers=self.headers(),
            json=payment_list_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentListResponse.model_validate(response.json())
        return data

    @async_auth_required
    async def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        """Send create ebarimt request."""
        response = await self._request(
            "POST",
            "/ebarimt/create",
            headers=self.headers(),
            json=ebarimt_create_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = Ebarimt.model_validate(response.json())
        return data

    @async_auth_required
    async def ebarimt_get(self, barimt_id: str):
        """Send get ebarimt request."""
        response = await self._request(
            "GET",
            "/ebarimt/" + barimt_id,
            headers=self.headers(),
        )

        data = Ebarimt.model_validate(response.json())
        return data

    @async_auth_required
    async def subscription_get(self, subscription_id: str):
        """Send get subscription request."""
        response = await self._request(
            "GET",
            "/subscription/" + subscription_id,
            headers=self.headers(),
        )

        data = SubscriptionGetResponse.model_validate(response.json())
        return data

    @async_auth_required
    async def subscription_cancel(self, subscription_id: str):
        """Send cancel subscription request."""
        response = await self._request(
            "DELETE",
            "/subscription/" + subscription_id,
            headers=self.headers(),
        )

        return response.status_code
