import asyncio
import logging
from random import random
from typing import Optional, Union, overload

from httpx import AsyncClient, BasicAuth, Headers, Response, Timeout

from .auth import QpayAuthState
from .schemas import (
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
from .utils import handle_error

logger = logging.getLogger("qpay")


class QPayClient:
    """Asynchronous client for QPay v2 API.

    This client handles authentication, token refresh, and provides async
    methods for interacting with QPay v2 endpoints (invoices, payments,
    and ebarimt). It is designed to follow the official QPay v2
    documentation.

    Args:
        username (str): Merchant username. Defaults to ``"TEST_MERCHANT"``.
        password (str): Merchant password. Defaults to ``"123456"``.
        is_sandbox (bool): Use sandbox environment if True (default).
            Set to False for production.
        timeout (httpx.Timeout): HTTP timeout configuration. Default`s to
            5s connect, 10s read/write, 5s pool.
        base_url (Literal["https://merchant-sandbox.qpay.mn/v2", "https://merchant.qpay.mn/v2"],
            optional):
            Override the default base URL if provided.
        token_leeway (int): Seconds before expiry to refresh tokens.
            Defaults to 60.
        logger (logging.Logger): Logger instance. Defaults to module logger.

    Authentication:
        The client manages token acquisition and refresh automatically. You should not call ``_authenticate`` directly.

    Example:
        >>> from qpay_client.v2 import QPayClient
        >>> client = QPayClient(username="YOUR_ID", password="YOUR_SECRET", is_sandbox=True)
        >>> invoice = await client.invoice_create(request)

    Available APIs:
        - **Invoice**
            - ``invoice_create``
            - ``invoice_cancel``
        - **Payment**
            - ``payment_get``
            - ``payment_check``
            - ``payment_cancel``
            - ``payment_refund``
            - ``payment_list``
        - **Ebarimt**
            - ``ebarimt_create``
            - ``ebarimt_get``

    """

    def __init__(
        self,
        username: str = "TEST_MERCHANT",
        password: str = "123456",
        *,
        is_sandbox: bool = True,
        timeout: Optional[Timeout] = None,
        base_url: Optional[str] = None,
        token_leeway: float = 60,
        logger=logger,
        log_level: int = logging.INFO,
    ):
        # Basic Auth setup
        self._auth_credentials = BasicAuth(
            username=username,
            password=password,
        )

        # base_url setup, base_url can also be automatically set from is_sandbox
        if base_url:
            # user supplied base_url
            self._base_url = base_url
        elif is_sandbox:
            # dev environment
            self._base_url = "https://merchant-sandbox.qpay.mn/v2"
        else:
            # prod environment
            self._base_url = "https://merchant.qpay.mn/v2"

        self._auth_state = QpayAuthState()

        self._token_leeway = token_leeway

        self._logger = logger
        self._logger.setLevel(log_level)

        # Default timeout if timeout is None
        if timeout is None:
            timeout = Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)

        # Async connections to qpay server
        self._client = AsyncClient(base_url=self._base_url, timeout=timeout)

        self._async_lock = asyncio.Lock()

        self._logger.debug(
            "QPayClient initialized",
            extra={"base_url": self._base_url, "sandbox": is_sandbox},
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        retries: int = 5,
        delay: float = 0.5,
        jitter: float = 0.5,
        **kwargs,
    ) -> Response:
        """Send requests to qpay server."""
        response = await self._client.request(method, url, **kwargs)

        if response.status_code == 401:
            # Fixable error
            await self._refresh_access_token()
            response = await self._client.request(method, url, **kwargs)

        elif response.is_server_error:
            # Retry for server errors
            for attempt in range(1, retries + 1):
                self._logger.warning(
                    f"Retrying {method}: {url} (attempt {attempt}/{retries} after {delay:.2f})",
                )
                await asyncio.sleep(delay ** (attempt - 1) + random() * jitter)
                response = await self._client.request(method, url, **kwargs)
                if response.is_success:
                    break

        if response.is_error:
            handle_error(response, self._logger)

        return response

    async def _headers(self):
        """Headers needed for communication between qpay client and qpay server."""
        return Headers(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {await self.get_token()}",
                "User-Agent": "qpay-client/2.x",
            }
        )

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
        response = await self._request(
            "POST",
            "/auth/token",
            auth=self._auth_credentials,
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
        response = await self._request(
            "POST",
            "/auth/refresh",
            headers={"Authorization": self._auth_state.refresh_as_header()},
        )

        if response.is_success:
            token_response = TokenResponse.model_validate(response.json())

            self._auth_state.update(token_response)
        else:
            await self._authenticate_nolock()

    async def get_token(self) -> str:
        """Get access token."""
        if not self._auth_state.has_access_token() or self._auth_state.is_refresh_expired(leeway=self._token_leeway):
            await self._authenticate()
        elif self._auth_state.is_access_expired(leeway=self._token_leeway):
            await self._refresh_access_token()
        return self._auth_state.get_access_token()

    async def invoice_get(self, invoice_id: str):
        """Get invoice by Id."""
        response = await self._request(
            "GET",
            "/invoice/" + invoice_id,
            headers=await self._headers(),
        )

        data = InvoiceGetResponse.model_validate(response.json())
        return data

    @overload
    async def invoice_create(self, create_invoice_request: InvoiceCreateSimpleRequest) -> InvoiceCreateResponse: ...

    @overload
    async def invoice_create(self, create_invoice_request: InvoiceCreateRequest) -> InvoiceCreateResponse: ...

    async def invoice_create(
        self, create_invoice_request: Union[InvoiceCreateRequest, InvoiceCreateSimpleRequest]
    ) -> InvoiceCreateResponse:
        """Send invoice create request to Qpay."""
        response = await self._request(
            "POST",
            "/invoice",
            headers=await self._headers(),
            json=create_invoice_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = InvoiceCreateResponse.model_validate(response.json())
        return data

    async def invoice_cancel(
        self,
        invoice_id: str,
    ):
        """Send cancel invoice request to qpay. Returns status code."""
        response = await self._request(
            "DELETE",
            "/invoice/" + invoice_id,
            headers=await self._headers(),
        )

        return response.status_code

    async def payment_get(self, payment_id: str):
        """Send get payment requesst to qpay."""
        response = await self._request(
            "GET",
            "/payment/" + payment_id,
            headers=await self._headers(),
        )

        data = PaymentGetResponse.model_validate(response.json())
        return data

    async def payment_check(
        self,
        payment_check_request: PaymentCheckRequest,
        *,
        payment_retries: int = 5,
        delay: float = 0.5,
        jitter: float = 0.5,
    ):
        """Send check payment request to qpay.

        When payment retries is more than 0, client polls qpay until count > 0 or the retry amount is reached.
        """
        response = await self._request(
            "POST",
            "/payment/check",
            headers=await self._headers(),
            json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentCheckResponse.model_validate(response.json())

        if data.count > 0:
            return data

        for attempt in range(1, payment_retries + 1):
            self._logger.warning(
                f"Retrying POST: /payment/check (attempt {attempt}/{payment_retries} after {delay:.2f})"
            )
            await asyncio.sleep(delay ** (attempt - 1) + random() * jitter)

            response = await self._request(
                "POST",
                "/payment/check",
                headers=await self._headers(),
                json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
            )

            data = PaymentCheckResponse.model_validate(response.json())

            if data.count > 0:
                break

        return data

    async def payment_cancel(
        self,
        payment_id: str,
        payment_cancel_request: PaymentCancelRequest,
    ) -> int:
        """Send payment cancel request. Returns status code."""
        response = await self._request(
            "DELETE",
            "/payment/cancel/" + payment_id,
            headers=await self._headers(),
            json=payment_cancel_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    async def payment_refund(
        self,
        payment_id: str,
        payment_refund_request: PaymentRefundRequest,
    ):
        """Send refund payment request. Returns status code."""
        response = await self._request(
            "DELETE",
            "/payment/refund/" + payment_id,
            headers=await self._headers(),
            json=payment_refund_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    async def payment_list(self, payment_list_request: PaymentListRequest):
        """Send list payment request."""
        response = await self._request(
            "POST",
            "/payment/list",
            headers=await self._headers(),
            json=payment_list_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentListResponse.model_validate(response.json())
        return data

    async def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        """Send create ebarimt request."""
        response = await self._request(
            "POST",
            "/ebarimt/create",
            headers=await self._headers(),
            json=ebarimt_create_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = Ebarimt.model_validate(response.json())
        return data

    async def ebarimt_get(self, barimt_id: str):
        """Send get ebarimt request."""
        response = await self._request(
            "GET",
            "/ebarimt/" + barimt_id,
            headers=await self._headers(),
        )

        data = Ebarimt.model_validate(response.json())
        return data

    async def subscription_get(self, subscription_id: str):
        """Send get subscription request."""
        response = await self._request(
            "GET",
            "/subscription/" + subscription_id,
            headers=await self._headers(),
        )

        data = SubscriptionGetResponse.model_validate(response.json())
        return data

    async def subscription_cancel(self, subscription_id: str):
        """Send cancel subscription request."""
        response = await self._request(
            "DELETE",
            "/subscription/" + subscription_id,
            headers=await self._headers(),
        )

        return response.status_code
