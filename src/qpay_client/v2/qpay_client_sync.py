import logging
import time
from typing import Literal, Optional

from httpx import BasicAuth, Client, Response, Timeout

from .error import QPayError
from .schemas import (
    Ebarimt,
    EbarimtCreateRequest,
    InvoiceCreateRequest,
    InvoiceCreateResponse,
    InvoiceCreateSimpleRequest,
    Payment,
    PaymentCheckRequest,
    PaymentCheckResponse,
    PaymentListRequest,
    TokenResponse,
)

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
        invoice_code: str = "TEST_INVOICE",
        is_sandbox: bool = True,
        timeout=Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0),
        base_url: (
            Optional[
                Literal["https://merchant-sandbox.qpay.mn/v2"]
                | Literal["https://merchant.qpay.mn/v2"]
            ]
        ) = None,
        token_leeway=60,
        logger=logger,
    ):
        self._auth_credentials = BasicAuth(
            username=username,
            password=password,
        )
        self._invoice_code = invoice_code
        self._client = Client(timeout=timeout)

        if base_url:
            # user supplied base_url
            self._base_url = base_url
        elif is_sandbox:
            # dev environment
            self._base_url = "https://merchant-sandbox.qpay.mn/v2"
        else:
            # prod environment
            self._base_url = "https://merchant.qpay.mn/v2"

        self._access_token = ""
        self._access_token_expiry = 0
        self._refresh_token = ""
        self._refresh_token_expiry = 0
        self._scope = ""
        self._not_before_policy = ""
        self._session_state = ""
        self._token_leeway = token_leeway or 60
        self._logger = logger

    @property
    def _headers(self):
        token = self.get_token()
        return {
            "Content-Type": "APP_JSON",
            "Authorization": f"Bearer {token}",
        }

    def _check_error(self, response: Response):
        if response.is_error:
            error_data = response.json()
            self._logger.error(error_data)
            raise QPayError(
                status_code=response.status_code, error_key=error_data["message"]
            )

    # Auth
    def _authenticate(self):
        """
        Used for server authentication.

        Note:
            DO NOT CALL THIS FUNCTION!
            The client manages the tokens.
        """
        response = self._client.post(
            self._base_url + "/auth/token",
            auth=self._auth_credentials,
        )
        # Raises status error if there is error
        self._check_error(response)

        data = TokenResponse.model_validate(response.json())

        self._access_token = data.access_token
        self._refresh_token = data.refresh_token
        self._access_token_expiry = data.expires_in - self._token_leeway
        self._refresh_token_expiry = data.refresh_expires_in - self._token_leeway
        self._scope = data.scope
        self._not_before_policy = data.not_before_policy
        self._session_state = data.session_state

    def _refresh_access_token(self):
        if not self._refresh_token or time.time() >= self._refresh_token_expiry:
            self._authenticate()
            return

        response = self._client.post(
            self._base_url + "/auth/refresh",
            headers={"Authorization": f"Bearer {self._refresh_token}"},
        )

        self._check_error(response)

        if response.is_success:
            data = TokenResponse.model_validate(response.json())

            self._access_token = data.access_token
            self._refresh_token = data.refresh_token
            self._access_token_expiry = data.expires_in - self._token_leeway
            self._refresh_token_expiry = data.refresh_expires_in - self._token_leeway
        else:
            self._authenticate()

    def get_token(self):
        if not self._access_token:
            self._authenticate()
        elif time.time() >= self._access_token_expiry:
            self._refresh_access_token()
        return self._access_token

    # Invoice
    def invoice_create(
        self, create_invoice_request: InvoiceCreateRequest | InvoiceCreateSimpleRequest
    ):
        create_invoice_request.invoice_code = self._invoice_code
        response = self._client.post(
            self._base_url + "/invoice",
            headers=self._headers,
            json=create_invoice_request.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            ),
        )

        self._check_error(response)

        data = InvoiceCreateResponse.model_validate(response.json())
        return data

    def invoice_cancel(
        self,
        invoice_id: str,
    ):
        response = self._client.delete(
            self._base_url + "/invoice/" + invoice_id,
            headers=self._headers,
        )

        self._check_error(response)

        return response.json()

    # Payment
    def payment_get(self, payment_id: str):
        response = self._client.get(
            self._base_url + "/payment/" + payment_id,
            headers=self._headers,
        )

        self._check_error(response)

        validated_response = Payment.model_validate(response.json())
        return validated_response

    def payment_check(self, payment_check_request: PaymentCheckRequest):
        response = self._client.post(
            self._base_url + "/payment/check",
            json=payment_check_request.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            ),
            headers=self._headers,
        )

        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate(response.json())
        return validated_response

    def payment_cancel(self, payment_id: str):
        response = self._client.delete(
            self._base_url + "/payment/cancel/" + payment_id,
            headers=self._headers,
        )

        self._check_error(response)

        return response.json()

    def payment_refund(self, payment_id: str):
        response = self._client.delete(
            self._base_url + "/payment/refund/" + payment_id,
            headers=self._headers,
        )

        self._check_error(response)

        return response.json()

    def payment_list(self, payment_list_request: PaymentListRequest):
        response = self._client.post(
            self._base_url + "/payment/list",
            json=payment_list_request.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            ),
            headers=self._headers,
        )

        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate(response.json())
        return validated_response

    # ebarimt
    def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        response = self._client.post(
            self._base_url + "/ebarimt/create",
            json=ebarimt_create_request.model_dump(
                by_alias=True, exclude_none=True, mode="json"
            ),
            headers=self._headers,
        )

        self._check_error(response)

        validated_response = Ebarimt.model_validate(response.json())
        return validated_response

    def ebarimt_get(self, barimt_id: str):
        response = self._client.get(
            self._base_url + "/ebarimt/" + barimt_id,
            headers=self._headers,
        )

        self._check_error(response)

        validated_response = Ebarimt.model_validate(response.json())
        return validated_response
