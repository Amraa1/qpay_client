import requests
from requests import status_codes
import time
from .schemas import (
    CreateInvoiceRequest,
    CreateSimpleInvoiceRequest,
    PaymentGetResponse,
    PaymentCheckRequest,
    PaymentCheckResponse,
    CreateInvoiceResponse,
)
from uuid import UUID
from pydantic import ValidationError
from core.constants import APP_JSON
from core.config import settings


QPAY_AUTH_URL = settings.qpay_auth_url
QPAY_REFRESH_TOKEN_URL = settings.qpay_refresh_token_url
QPAY_CHECK_PAYMENT_URL = settings.qpay_check_payment_url
QPAY_CANCEL_INVOICE_URL = settings.qpay_cancel_invoice_url
QPAY_CREATE_INVOICE_URL = settings.qpay_create_invoice_url
QPAY_GET_PAYMENT_URL = settings.qpay_get_payment_url
QPAY_USERNAME = settings.qpay_username
QPAY_PASSWORD = settings.qpay_password


class QPayClient:
    """
    Authenticate the qPayClient instance with the QPay API.

    This method obtains a new access token and refresh token from the QPay authentication server
    using the configured username and password credentials. It also sets the token expiration times
    for both the access token and the refresh token to enable future token refreshing before expiry.

    Notes:
        - If authentication fails (e.g., wrong credentials, network issues), a requests.HTTPError will be raised.
        - Tokens are refreshed proactively 60 seconds before their official expiration time to avoid downtime.

    Raises:
        HTTPError: If the authentication request returns a non-200 status code.
    """

    __access_token, __refresh_token, __token_expiry, __refresh_token_expiry = (
        None,
        None,
        0,
        0,
    )

    def __init__(self, timeout=30):
        self.__timeout = timeout

    @property
    def headers(self):
        return {
            "Content-Type": APP_JSON,
            "Authorization": f"Bearer {self.get_token()}",
        }

    def authenticate(self):
        response = requests.post(
            QPAY_AUTH_URL,
            auth=(QPAY_USERNAME, QPAY_PASSWORD),
            timeout=self.__timeout,
        )
        response.raise_for_status()
        data = response.json()
        self.__access_token = data.get("access_token")
        self.__refresh_token = data.get("refresh_token")
        self.__token_expiry = time.time() + data.get("expires_in", 0) - 60
        self.__refresh_token_expiry = (
            time.time() + data.get("refresh_expires_in", 0) - 60
        )

    def refresh_access_token(self):
        if self.__refresh_token is None or self.__refresh_token_expiry <= time.time():
            self.authenticate()
            return

        response = requests.post(
            QPAY_REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {self.__refresh_token}"},
            timeout=self.__timeout,
        )
        if response.ok:
            data = response.json()
            self.__access_token = data["access_token"]
            self.__token_expiry = time.time() + data["expires_in"] - 60
        else:
            self.authenticate()

    def get_token(self):
        if self.__access_token and self.__token_expiry > time.time():
            self.refresh_access_token()
        elif self.__access_token is None:
            self.authenticate()
        return self.__access_token

    def create_invoice(
        self, create_invoice_request: CreateInvoiceRequest | CreateSimpleInvoiceRequest
    ):
        response = requests.post(
            QPAY_CREATE_INVOICE_URL,
            headers=self.headers,
            data=create_invoice_request.model_dump_json(),
            timeout=self.__timeout,
        )

        validated_response = CreateInvoiceResponse.model_validate(response.json())
        return validated_response

    def cancel_invoice(
        self,
        invoice_id: UUID,
    ):
        response = requests.delete(
            f"{QPAY_CANCEL_INVOICE_URL}/{invoice_id}",
            headers=self.headers,
            timeout=self.__timeout,
        )
        return response.status_code

    def get_payment(self, invoice_id):
        response = requests.get(
            QPAY_GET_PAYMENT_URL + str(invoice_id),
            headers=self.headers,
            timeout=self.__timeout,
        )
        validated_response = PaymentGetResponse.model_validate(response.json())
        return validated_response

    def check_payment(self, payment_check_request: PaymentCheckRequest):
        response = requests.post(
            QPAY_CHECK_PAYMENT_URL,
            data=payment_check_request.model_dump_json(),
            headers=self.headers,
            timeout=self.__timeout,
        )

        validated_response = PaymentCheckResponse.model_validate(response.json())
        return validated_response


# Global qpay client
qpay_client = QPayClient()
