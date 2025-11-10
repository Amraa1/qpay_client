import logging
import random
import time
from typing import Optional, Union

from httpx import BasicAuth, Client, Response, Timeout

from .auth import QpayAuthState
from .schemas import (
    EbarimtCreateRequest,
    EbarimtCreateResponse,
    EbarimtGetResponse,
    InvoiceCreateRequest,
    InvoiceCreateResponse,
    InvoiceCreateSimpleRequest,
    InvoiceGetResponse,
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


class QPayClientSync:
    """
    Synchronous client for QPay v2 API.

    This client handles authentication, token refresh, and provides sync
    methods for interacting with QPay v2 endpoints (invoices, payments,
    and ebarimt). It is designed to follow the official QPay v2
    documentation.

    Args:
        username (str): Merchant username. Defaults to ``"TEST_MERCHANT"``.
        password (str): Merchant password. Defaults to ``"123456"``.
        is_sandbox (bool): Use sandbox environment if True (default).
            Set to False for production.
        timeout (httpx.Timeout): HTTP timeout configuration. Defaults to
            5s connect, 10s read/write, 5s pool.
        base_url (Literal["https://merchant-sandbox.qpay.mn/v2",
                          "https://merchant.qpay.mn/v2"], optional):
            Override the default base URL if provided.
        token_leeway (int): Seconds before expiry to refresh tokens.
            Defaults to 60.
        logger (logging.Logger): Logger instance. Defaults to module logger.

    Authentication:
        The client manages token acquisition and refresh automatically.
        You should not call ``_authenticate`` directly.

    Example:
        >>> from qpay_client.v2 import QPayClientSync
        >>> client = QPayClientSync(username="YOUR_ID", password="YOUR_SECRET", \
            is_sandbox=False)
        >>> invoice = client.invoice_create(request)

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
        *,
        username: str = "TEST_MERCHANT",
        password: str = "123456",
        is_sandbox: bool = True,
        timeout: Optional[Timeout] = None,
        base_url: Optional[str] = None,
        token_leeway=60,
        logger=logger,
    ):
        self._auth_credentials = BasicAuth(
            username=username,
            password=password,
        )

        if base_url:
            # user supplied base_url
            self._base_url = base_url
        elif is_sandbox:
            # dev environment
            self._base_url = "https://merchant-sandbox.qpay.mn/v2"
        else:
            # prod environment
            self._base_url = "https://merchant.qpay.mn/v2"

        if timeout is None:
            timeout = Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)

        self._client = Client(base_url=self._base_url, timeout=timeout)

        self._auth_state = QpayAuthState()
        self._token_leeway = token_leeway or 60
        self._logger = logger

    def _request(
        self,
        method: str,
        url: str,
        *,
        retries: int = 0,
        delay: float = 0.5,
        jitter: float = 0.5,
        **kwargs,
    ) -> Response:
        """Send requests to qpay server."""
        response = self._client.request(method, url, **kwargs)

        if response.status_code == 401:
            # Try to fix
            self._refresh_access_token()
            response = self._client.request(method, url, **kwargs)

        elif response.is_server_error:
            # Retry for server errors
            for attempt in range(1, retries + 1):
                self._logger.warning(
                    f"Retrying {method}: {url} (attempt {attempt}/{retries} after {delay:.2f})",
                )
                time.sleep(delay ** (attempt - 1) + random.random() * jitter)

                response = self._client.request(method, url, **kwargs)

                if response.is_success:
                    break

        if response.is_error:
            handle_error(response, self._logger)

        return response

    def _headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
            "User-Agent": "qpay-client/2.x",
        }

    def _authenticate(self):
        """
        Used for server authentication.

        Note:
            DO NOT CALL THIS FUNCTION!
            The client manages the tokens.

        """
        response = self._request("POST", "/auth/token", auth=self._auth_credentials)

        token_response = TokenResponse.model_validate(response.json())

        self._auth_state.update(token_response)

    def _refresh_access_token(self):
        if not self._auth_state.is_access_expired(self._token_leeway):
            return

        elif self._auth_state.is_refresh_expired(self._token_leeway):
            self._authenticate()
            return

        response = self._request(
            "POST", "/auth/refresh", headers={"Authorization": self._auth_state.refresh_as_header()}
        )

        if response.is_success:
            token_response = TokenResponse.model_validate(response.json())

            self._auth_state.update(token_response)

        else:
            self._authenticate()

    def get_token(self):
        if not self._auth_state.has_access_token or self._auth_state.is_refresh_expired(self._token_leeway):
            self._authenticate()
        elif self._auth_state.is_access_expired(self._token_leeway):
            self._refresh_access_token()
        return self._auth_state.get_access_token()

    def invoice_get(self, invoice_id: str):
        """Get invoice by Id."""
        response = self._request(
            "GET",
            "/invoice/" + invoice_id,
            headers=self._headers(),
        )

        data = InvoiceGetResponse.model_validate(response.json())
        return data

    def invoice_create(self, create_invoice_request: Union[InvoiceCreateRequest, InvoiceCreateSimpleRequest]):
        """Create invoice."""
        response = self._request(
            "POST",
            "/invoice",
            headers=self._headers(),
            json=create_invoice_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = InvoiceCreateResponse.model_validate(response.json())
        return data

    def invoice_cancel(
        self,
        invoice_id: str,
    ):
        response = self._request(
            "DELETE",
            "/invoice/" + invoice_id,
            headers=self._headers(),
        )

        return response.status_code

    def payment_get(self, payment_id: str):
        response = self._request(
            "GET",
            "/payment/" + payment_id,
            headers=self._headers(),
        )

        data = PaymentGetResponse.model_validate(response.json())
        return data

    def payment_check(
        self,
        payment_check_request: PaymentCheckRequest,
        *,
        payment_retries: int = 5,
        delay: float = 0.5,
        jitter: float = 0.5,
    ):
        response = self._request(
            "POST",
            "/payment/check",
            headers=self._headers(),
            json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentCheckResponse.model_validate(response.json())

        if data.count > 0:
            return data

        for attempt in range(1, payment_retries + 1):
            self._logger.warning(
                f"Retrying POST: /payment/check (attempt {attempt}/{payment_retries} after {delay:.2f})"
            )
            time.sleep(delay ** (attempt - 1) + random.random() * jitter)

            response = self._request(
                "POST",
                "/payment/check",
                headers=self._headers(),
                json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
            )

            data = PaymentCheckResponse.model_validate(response.json())

            if data.count > 0:
                break

        return data

    def payment_cancel(self, payment_id: str):
        response = self._request(
            "DELETE",
            "/payment/cancel/" + payment_id,
            headers=self._headers(),
        )

        return response.status_code

    def payment_refund(
        self,
        payment_id: str,
        payment_refund_request: PaymentRefundRequest,
    ):
        response = self._request(
            "DELETE",
            "/payment/refund/" + payment_id,
            headers=self._headers(),
            json=payment_refund_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    def payment_list(self, payment_list_request: PaymentListRequest):
        response = self._request(
            "POST",
            "/payment/list",
            headers=self._headers(),
            json=payment_list_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentListResponse.model_validate(response.json())
        return data

    def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        response = self._request(
            "POST",
            "/ebarimt/create",
            headers=self._headers(),
            json=ebarimt_create_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        print(response.status_code)

        data = EbarimtCreateResponse.model_validate(response.json())
        return data

    def ebarimt_get(self, barimt_id: str):
        response = self._request(
            "GET",
            "/ebarimt/" + barimt_id,
            headers=self._headers(),
        )

        data = EbarimtGetResponse.model_validate(response.json())
        return data

    def subscription_get(self, subscription_id: str):
        """Send get subscription request."""
        response = self._request(
            "GET",
            "/subscription/" + subscription_id,
            headers=self._headers(),
        )

        data = SubscriptionGetResponse.model_validate(response.json())
        return data

    def subscription_cancel(self, subscription_id: str):
        """Send cancel subscription request."""
        response = self._request(
            "DELETE",
            "/subscription/" + subscription_id,
            headers=self._headers(),
        )

        return response.status_code
