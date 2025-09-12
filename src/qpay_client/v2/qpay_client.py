import logging
import time
from typing import Literal, Optional

from httpx import AsyncClient, BasicAuth, Response, Timeout

from .error import QPayError
from .schemas import (
    CreateInvoiceResponse,
    Ebarimt,
    EbarimtCreateRequest,
    InvoiceCreateRequest,
    InvoiceCreateSimpleRequest,
    Payment,
    PaymentCheckRequest,
    PaymentCheckResponse,
    PaymentListRequest,
    TokenResponse,
)

logger = logging.getLogger("qpay")

type QPayBaseUrl = Literal[
    "https://merchant-sandbox.qpay.mn/v2", "https://merchant.qpay.mn/v2"
]


class QPayClient:
    """
    Async QPay v2 client
    """

    def __init__(
        self,
        *,
        username: str = "TEST_MERCHANT",
        password: str = "123456",
        is_sandbox: bool = True,
        timeout=Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0),
        base_url: Optional[QPayBaseUrl] = None,
        token_leeway=60,
        logger=logger,
    ):
        self._auth_credentials = BasicAuth(
            username=username,
            password=password,
        )
        self._client = AsyncClient(timeout=timeout)

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
    async def _headers(self):
        token = await self.get_token()
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
    async def _authenticate(self):
        """
        Used for server authentication.

        Note:
            DO NOT CALL THIS FUNCTION!
            The client manages the tokens.
        """
        response = await self._client.post(
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

    async def _refresh_access_token(self):
        if not self._refresh_token or time.time() >= self._refresh_token_expiry:
            await self._authenticate()
            return

        response = await self._client.post(
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
            await self._authenticate()

    async def get_token(self):
        if not self._access_token:
            await self._authenticate()
        elif time.time() >= self._access_token_expiry:
            await self._refresh_access_token()
        return self._access_token

    # Invoice
    async def invoice_create(
        self, create_invoice_request: InvoiceCreateRequest | InvoiceCreateSimpleRequest
    ):
        response = await self._client.post(
            self._base_url + "/invoice",
            headers=await self._headers,
            data=create_invoice_request.model_dump(),
        )

        self._check_error(response)

        data = CreateInvoiceResponse.model_validate_json(response.json())
        return data

    async def invoice_cancel(
        self,
        invoice_id: str,
    ):
        response = await self._client.delete(
            self._base_url + "/invoice/" + invoice_id,
            headers=await self._headers,
        )

        self._check_error(response)

        return response.json()

    # Payment
    async def payment_get(self, payment_id: str):
        response = await self._client.get(
            self._base_url + "/payment/" + payment_id,
            headers=await self._headers,
        )

        self._check_error(response)

        validated_response = Payment.model_validate(response.json())
        return validated_response

    async def payment_check(self, payment_check_request: PaymentCheckRequest):
        response = await self._client.post(
            self._base_url + "/payment/check",
            data=payment_check_request.model_dump(),
            headers=await self._headers,
        )

        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    async def payment_cancel(self, payment_id: str):
        response = await self._client.delete(
            self._base_url + "/payment/cancel/" + payment_id,
            headers=await self._headers,
        )

        self._check_error(response)

        return response.json()

    async def payment_refund(self, payment_id: str):
        response = await self._client.delete(
            self._base_url + "/payment/refund/" + payment_id,
            headers=await self._headers,
        )

        self._check_error(response)

        return response.json()

    async def payment_list(self, payment_list_request: PaymentListRequest):
        response = await self._client.post(
            self._base_url + "/payment/list",
            data=payment_list_request.model_dump(),
            headers=await self._headers,
        )

        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    # ebarimt
    async def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        response = await self._client.post(
            self._base_url + "/ebarimt/create",
            data=ebarimt_create_request.model_dump(),
            headers=await self._headers,
        )

        self._check_error(response)

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response

    async def ebarimt_get(self, barimt_id: str):
        response = await self._client.get(
            self._base_url + "/ebarimt/" + barimt_id,
            headers=await self._headers,
        )

        self._check_error(response)

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response
