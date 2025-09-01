from httpx import AsyncClient
import httpx
import time
from .schemas import (
    InvoiceCreateRequest,
    InvoiceCreateSimpleRequest,
    PaymentGetResponse,
    PaymentCheckRequest,
    PaymentCheckResponse,
    CreateInvoiceResponse,
    TokenResponse,
    PaymentListRequest,
    EbarimtCreateRequest,
    Ebarimt,
)


INVOICE_CODE = "TEST_INVOICE"
QPAY_USERNAME = "TEST_MERCHANT"
QPAY_PASSWORD = "123456"

BASE_URL = "https://merchant-sandbox.qpay.mn/v2"


class QPayClient:
    """
    Async QPay v2 client
    """

    def __init__(self, timeout=30):
        self._timeout = timeout
        self._access_token = None
        self._access_token_expiry = 0
        self._refresh_token = None
        self._refresh_token_expiry = 0
        self.scope = ""
        self.not_before_policy = ""
        self.session_state = ""
        self._token_leeway = 60

    @property
    def headers(self):
        return {
            "Content-Type": "APP_JSON",
            "Authorization": f"Bearer {self.get_token()}",
        }

    # Auth
    def authenticate(self):
        response = httpx.post(
            BASE_URL + "/auth/token",
            auth=(QPAY_USERNAME, QPAY_PASSWORD),
            timeout=self._timeout,
        )
        # Raises status error if there is error
        response.raise_for_status()

        data = TokenResponse.model_validate(response.json())

        self._access_token = data.access_token
        self._refresh_token = data.refresh_token
        self._token_expiry = data.expires_in - self._token_leeway
        self._refresh_token_expiry = data.refresh_expires_in - self._token_leeway
        self.scope = data.scope
        self.not_before_policy = data.not_before_policy
        self.session_state = data.session_state

    def refresh_access_token(self):
        if self._refresh_token is None or self._refresh_token_expiry > time.time():
            self.authenticate()
            return

        response = httpx.post(
            BASE_URL + "/auth/refresh",
            headers={"Authorization": f"Bearer {self._refresh_token}"},
            timeout=self._timeout,
        )

        if response.is_success:
            data = TokenResponse.model_validate(response.json())

            self._access_token = data.access_token
            self._refresh_token = data.refresh_token
            self._token_expiry = data.expires_in - self._token_leeway
            self._refresh_token_expiry = data.refresh_expires_in - self._token_leeway
        else:
            self.authenticate()

    def get_token(self):
        if self._access_token is None:
            self.authenticate()
        elif self._token_expiry > time.time():
            self.refresh_access_token()
        return self._access_token

    # Invoice
    def invoice_create(
        self, create_invoice_request: InvoiceCreateRequest | InvoiceCreateSimpleRequest
    ):
        response = httpx.post(
            BASE_URL + "/invoice",
            headers=self.headers,
            data=create_invoice_request.model_dump(),
            timeout=self._timeout,
        )

        data = CreateInvoiceResponse.model_validate_json(response.json())
        return data

    def invoice_cancel(
        self,
        invoice_id: str,
    ):
        response = httpx.delete(
            BASE_URL + "/invoice/" + invoice_id,
            headers=self.headers,
            timeout=self._timeout,
        )
        return response.json()

    # Payment
    def payment_get(self, payment_id: str):
        response = httpx.get(
            BASE_URL + "/payment/" + payment_id,
            headers=self.headers,
            timeout=self._timeout,
        )
        validated_response = PaymentGetResponse.model_validate(response.json())
        return validated_response

    def payment_check(self, payment_check_request: PaymentCheckRequest):
        response = httpx.post(
            BASE_URL + "/payment/check",
            data=payment_check_request.model_dump(),
            headers=self.headers,
            timeout=self._timeout,
        )

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    def payment_cancel(self, payment_id: str):
        response = httpx.delete(
            BASE_URL + "/payment/cancel/" + payment_id,
            headers=self.headers,
            timeout=self._timeout,
        )
        return response.json()

    def payment_refund(self, payment_id: str):
        response = httpx.delete(
            BASE_URL + "/payment/refund/" + payment_id,
            headers=self.headers,
            timeout=self._timeout,
        )
        return response.json()

    def payment_list(self, payment_list_request: PaymentListRequest):
        response = httpx.post(
            BASE_URL + "/payment/list",
            data=payment_list_request.model_dump(),
            headers=self.headers,
            timeout=self._timeout,
        )

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    # ebarimt
    def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        response = httpx.post(
            BASE_URL + "/ebarimt/create",
            data=ebarimt_create_request.model_dump(),
            headers=self.headers,
            timeout=self._timeout,
        )

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response

    def ebarimt_get(self, barimt_id: str):
        response = httpx.get(
            BASE_URL + "/ebarimt/" + barimt_id,
            headers=self.headers,
            timeout=self._timeout,
        )

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response


# Global qpay client
qpay_client = QPayClient()
