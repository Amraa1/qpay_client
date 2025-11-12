import asyncio
import logging
import random
from typing import Optional, Union

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
from .settings import QPaySettings
from .utils import handle_error


class QPayClient:
    """
    Asynchronous client for QPay v2 API.

    This client handles authentication, token refresh, and provides async
    methods for interacting with QPay v2 endpoints (invoices, payments,
    subscriptions, and ebarimt). It is designed to follow the official QPay v2.
    """

    def __init__(
        self,
        *,
        settings: Optional[QPaySettings] = None,
        timeout: Optional[Timeout] = None,
        logger: Optional[logging.Logger] = None,
        log_level: Optional[Union[int, str]] = None,
    ):
        """
        Initialize QPayClient object.

        Args:
            settings (Optional[Settings]): Optional Settings instance.
            timeout (Optional[httpx.Timeout]): Optional HTTPX Timeout configuration
                for requests.
            logger (logging.Logger): Logger instance.
            log_level (int): Logging level for the logger.

        """
        self._id = id(self)
        self._auth_state = QpayAuthState()
        self._settings = settings or QPaySettings()

        # If base_url is supplied use that else use settings
        self._base_url = self._settings.base_url

        self._is_sandbox = self._settings.sandbox
        self._token_leeway = self._settings.token_leeway

        # Logging config
        self._logger = logger or logging.getLogger(f"qpay.{self._id}")
        self._logger.setLevel(log_level or logging.INFO)

        # Default timeout if timeout is None
        if timeout is None:
            timeout = Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)

        # Async connections to qpay server
        self._client = AsyncClient(base_url=self._base_url, timeout=timeout)

        self._async_lock = asyncio.Lock()

    @property
    def is_authenticated(self) -> bool:
        """Returns True of authenticated and not expired."""
        return self._auth_state.has_access_token() and not self.is_access_expired

    @property
    def is_closed(self) -> bool:
        """Returns True of connection is closed."""
        return self._client.is_closed

    @property
    def is_access_expired(self) -> bool:
        """Returns True if access token is expired."""
        return self._auth_state.is_access_expired(leeway=self._token_leeway)

    @property
    def is_refresh_expired(self) -> bool:
        """Returns True if refresh token is expired."""
        return self._auth_state.is_refresh_expired(leeway=self._token_leeway)

    @property
    def is_sandbox(self) -> bool:
        """Returns True if client is in sandbox mode."""
        return self._is_sandbox

    @property
    def token(self) -> str:
        """Get client token."""
        return self._auth_state.get_access_token()

    @property
    def base_url(self) -> str:
        """Get base url."""
        return self._base_url

    async def __aenter__(self):
        # client authenticates early here if not authenticated
        if not self.is_authenticated:
            await self._authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close connection."""
        if not self.is_closed:
            await self._client.aclose()

    async def authenticate(self) -> None:
        """Authenticate client."""
        if self.is_authenticated:
            return  # Fast exit
        elif self.is_access_expired:
            await self._refresh_access_token()
        if self.is_refresh_expired:
            await self._authenticate()

    async def _request(
        self,
        method: str,
        url: str,
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
            for attempt in range(1, self._settings.client_retries + 1):
                self._logger.warning(
                    f"Retrying {method}: {url} (attempt {attempt}/{self._settings.client_retries} after {self._settings.client_delay:.2f})",
                )
                await asyncio.sleep(
                    self._settings.client_delay ** (attempt - 1) + random.random() * self._settings.client_jitter
                )
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
                "Authorization": f"Bearer {await self._get_auth_token()}",
                "User-Agent": "qpay-client",
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
            auth=BasicAuth(
                username=self._settings.username,
                password=self._settings.password.get_secret_value(),  # get password secret
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

    async def _get_auth_token(self) -> str:
        """Get authenticated access token."""
        await self.authenticate()
        return self.token

    async def invoice_get(self, invoice_id: str):
        """Get invoice by Id."""
        response = await self._request(
            "GET",
            "/invoice/" + invoice_id,
            headers=await self._headers(),
        )

        data = InvoiceGetResponse.model_validate(response.json())
        return data

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
    ):
        """
        Send check payment request to qpay.

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

        for attempt in range(1, self._settings.payment_check_retries + 1):
            self._logger.warning(
                f"Retrying POST: /payment/check (attempt {attempt}/{self._settings.payment_check_retries} after {self._settings.payment_check_delay:.2f})"
            )
            await asyncio.sleep(
                self._settings.payment_check_delay ** (attempt - 1)
                + random.random() * self._settings.payment_check_jitter
            )

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
