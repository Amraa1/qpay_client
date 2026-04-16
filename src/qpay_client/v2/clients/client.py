import logging
from typing import Optional, Union

from httpx import BasicAuth, Client, Response

from ..schemas import (
    EbarimtCreateRequest,
    EbarimtCreateResponse,
    EbarimtGetResponse,
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
from ..transport import SyncTransport
from .base import BaseClient
from .decorators import auth_required, poll_until_paid


class QPayClient(BaseClient):
    """
    Synchronous client for the QPay v2 API.

    Always use as a context manager. Authentication runs on ``__enter__``
    and the HTTP connection is closed on ``__exit__``::

        settings = QPaySettings.production(
            username="...", password="...", invoice_code="..."
        )
        with QPayClient(settings) as client:
            invoice = client.invoice_create(InvoiceCreateSimpleRequest(...))
            result  = client.payment_check(PaymentCheckRequest(...))

    Available endpoints: ``invoice_create``, ``invoice_get``, ``invoice_cancel``,
    ``payment_get``, ``payment_check``, ``payment_cancel``, ``payment_refund``,
    ``payment_list``, ``ebarimt_create``, ``ebarimt_get``,
    ``subscription_get``, ``subscription_cancel``.

    Not thread-safe. Use one instance per thread or protect access with a lock.
    """

    def __init__(
        self,
        settings: QPaySettings,
        *,
        client: Optional[Client] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize QPayClient object.

        Args:
            settings (Settings): QPay client settings.
            client (Optional[httpx.Client]): Optional custom httpx client.
            logger (Optional[logging.Logger]): QPay client logger.

        """
        super().__init__(settings, logger=logger)
        self._transport = SyncTransport(settings=settings, logger=self._logger, client=client)
        self._client = self._transport.client

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    def __enter__(self):
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close connection."""
        self._transport.close()

    def authenticate(self) -> None:
        """Authenticate client."""
        if self.is_authenticated:
            return  # Fast exit
        if not self._auth_state.has_access_token() or self.is_refresh_expired:
            self._authenticate()
        else:
            self._refresh_access_token()

    def _send(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Response:
        return self._transport._send(method, url, **kwargs)

    def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Response:
        return self._transport.request(
            method,
            url,
            on_unauthorized=self._refresh_access_token,
            **kwargs,
        )

    def _authenticate(self):
        """
        Used for server authentication.

        Note:
            DO NOT CALL THIS FUNCTION!
            The client manages the tokens.

        """
        response = self._request(
            "POST",
            "/auth/token",
            auth=BasicAuth(
                username=self._settings.username,
                password=self._settings.password,
            ),
        )

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

    def get_token(self) -> str:
        if not self._auth_state.has_access_token() or self._auth_state.is_refresh_expired(self._token_leeway):
            self._authenticate()
        elif self._auth_state.is_access_expired(self._token_leeway):
            self._refresh_access_token()
        return self._auth_state.get_access_token()

    @auth_required
    def invoice_get(self, invoice_id: str) -> InvoiceGetResponse:
        """Get invoice by Id."""
        response = self._request(
            "GET",
            f"/invoice/{invoice_id}",
            headers=self.headers(),
        )

        data = InvoiceGetResponse.model_validate(response.json())
        return data

    @auth_required
    def invoice_create(self, create_invoice_request: Union[InvoiceCreateRequest, InvoiceCreateSimpleRequest]) -> InvoiceCreateResponse:
        """Create invoice."""
        response = self._request(
            "POST",
            "/invoice",
            headers=self.headers(),
            json=self._invoice_create_payload(create_invoice_request),
        )

        data = InvoiceCreateResponse.model_validate(response.json())
        return data

    @auth_required
    def invoice_cancel(
        self,
        invoice_id: str,
    ) -> int:
        response = self._request(
            "DELETE",
            f"/invoice/{invoice_id}",
            headers=self.headers(),
        )

        return response.status_code

    @auth_required
    def payment_get(self, payment_id: str) -> PaymentGetResponse:
        response = self._request(
            "GET",
            f"/payment/{payment_id}",
            headers=self.headers(),
        )

        data = PaymentGetResponse.model_validate(response.json())
        return data

    @auth_required
    @poll_until_paid
    def payment_check(self, payment_check_request: PaymentCheckRequest) -> PaymentCheckResponse:
        """Check payment status, polling until a payment is found or retries exhausted."""
        response = self._request(
            "POST",
            "/payment/check",
            headers=self.headers(),
            json=payment_check_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )
        return PaymentCheckResponse.model_validate(response.json())

    @auth_required
    def payment_cancel(
        self,
        payment_id: str,
        payment_cancel_request: PaymentCancelRequest,
    ) -> int:
        response = self._request(
            "DELETE",
            f"/payment/cancel/{payment_id}",
            headers=self.headers(),
            json=payment_cancel_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    @auth_required
    def payment_refund(
        self,
        payment_id: str,
        payment_refund_request: PaymentRefundRequest,
    ) -> int:
        response = self._request(
            "DELETE",
            f"/payment/refund/{payment_id}",
            headers=self.headers(),
            json=payment_refund_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        return response.status_code

    @auth_required
    def payment_list(self, payment_list_request: PaymentListRequest) -> PaymentListResponse:
        response = self._request(
            "POST",
            "/payment/list",
            headers=self.headers(),
            json=payment_list_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = PaymentListResponse.model_validate(response.json())
        return data

    @auth_required
    def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest) -> EbarimtCreateResponse:
        response = self._request(
            "POST",
            "/ebarimt/create",
            headers=self.headers(),
            json=ebarimt_create_request.model_dump(by_alias=True, exclude_none=True, mode="json"),
        )

        data = EbarimtCreateResponse.model_validate(response.json())
        return data

    @auth_required
    def ebarimt_get(self, barimt_id: str) -> EbarimtGetResponse:
        response = self._request(
            "GET",
            f"/ebarimt/{barimt_id}",
            headers=self.headers(),
        )

        data = EbarimtGetResponse.model_validate(response.json())
        return data

    @auth_required
    def subscription_get(self, subscription_id: str) -> SubscriptionGetResponse:
        """Send get subscription request."""
        response = self._request(
            "GET",
            f"/subscription/{subscription_id}",
            headers=self.headers(),
        )

        data = SubscriptionGetResponse.model_validate(response.json())
        return data

    @auth_required
    def subscription_cancel(self, subscription_id: str) -> int:
        """Send cancel subscription request."""
        response = self._request(
            "DELETE",
            f"/subscription/{subscription_id}",
            headers=self.headers(),
        )

        return response.status_code
