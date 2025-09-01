import os
from httpx import AsyncClient, BasicAuth, Response
import time
from .schemas import (
    InvoiceCreateRequest,
    InvoiceCreateSimpleRequest,
    Payment,
    PaymentCheckRequest,
    PaymentCheckResponse,
    CreateInvoiceResponse,
    TokenResponse,
    PaymentListRequest,
    EbarimtCreateRequest,
    Ebarimt,
)
from .error import QPayError, ClientConfigError
from typing import Optional
import enum
import logging


class Environment(enum.Enum):
    sandbox = 1
    production = 2


logger = logging.getLogger("qpay")


QPAY_USERNAME = os.getenv("QPAY_USERNAME", "TEST_MERCHANT")
QPAY_PASSWORD = os.getenv("QPAY_PASSWORD", "123456")
QPAY_ENV = os.getenv("QPAY_ENV", "sandbox")

if QPAY_ENV == "production":
    is_sandbox = False
elif QPAY_ENV == "sandbox":
    is_sandbox = True
else:
    raise ValueError("QPAY_ENV must either sandbox or production")


# Env based settings
if is_sandbox:
    BASE_URL = "https://merchant-sandbox.qpay.mn/v2"
else:
    BASE_URL = "https://merchant.qpay.mn/v2"

is_prod = not is_sandbox


class QPayClient:
    """
    Async QPay v2 client
    """

    def __init__(
        self,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        is_sandbox: Optional[bool] = None,
        token_leeway=60,
        timeout=30,
        logger=logger,
    ):
        if is_sandbox is None:
            is_sandbox = not is_prod

        if is_sandbox:
            self._env = Environment.sandbox
        elif not is_sandbox:
            self._env = Environment.production

        self._base_url = base_url or BASE_URL
        self._client = AsyncClient(timeout=timeout)
        self._auth_credentials = BasicAuth(
            username=username or QPAY_USERNAME,
            password=password or QPAY_PASSWORD,
        )
        self._access_token = ""
        self._access_token_expiry = 0
        self._refresh_token = ""
        self._refresh_token_expiry = 0
        self._scope = ""
        self._not_before_policy = ""
        self._session_state = ""
        self._timeout = timeout or 30
        self._token_leeway = token_leeway or 60
        self._logger = logger

    @property
    async def headers(self):
        token = await self.get_token()
        return {
            "Content-Type": "APP_JSON",
            "Authorization": f"Bearer {token}",
        }

    def _check_error(self, response: Response):
        if response.is_error:
            print(response.json())
            error_data = response.json()
            raise QPayError(
                status_code=response.status_code, error_key=error_data["message"]
            )

    # Auth
    async def authenticate(self):
        response = await self._client.post(
            BASE_URL + "/auth/token",
            auth=self._auth_credentials,
            timeout=self._timeout,
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

    async def refresh_access_token(self):
        if not self._refresh_token or time.time() >= self._refresh_token_expiry:
            await self.authenticate()
            return

        response = await self._client.post(
            BASE_URL + "/auth/refresh",
            headers={"Authorization": f"Bearer {self._refresh_token}"},
            timeout=self._timeout,
        )

        self._check_error(response)

        if response.is_success:
            data = TokenResponse.model_validate(response.json())

            self._access_token = data.access_token
            self._refresh_token = data.refresh_token
            self._access_token_expiry = data.expires_in - self._token_leeway
            self._refresh_token_expiry = data.refresh_expires_in - self._token_leeway
        else:
            await self.authenticate()

    async def get_token(self):
        if not self._access_token:
            await self.authenticate()
        elif time.time() >= self._access_token_expiry:
            await self.refresh_access_token()
        return self._access_token

    # Invoice
    async def invoice_create(
        self, create_invoice_request: InvoiceCreateRequest | InvoiceCreateSimpleRequest
    ):
        response = await self._client.post(
            BASE_URL + "/invoice",
            headers=await self.headers,
            data=create_invoice_request.model_dump(),
            timeout=self._timeout,
        )

        self._check_error(response)

        data = CreateInvoiceResponse.model_validate_json(response.json())
        return data

    async def invoice_cancel(
        self,
        invoice_id: str,
    ):
        response = await self._client.delete(
            BASE_URL + "/invoice/" + invoice_id,
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)
        
        return response.json()

    # Payment
    async def payment_get(self, payment_id: str):
        response = await self._client.get(
            BASE_URL + "/payment/" + payment_id,
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)
        
        validated_response = Payment.model_validate(response.json())
        return validated_response

    async def payment_check(self, payment_check_request: PaymentCheckRequest):
        response = await self._client.post(
            BASE_URL + "/payment/check",
            data=payment_check_request.model_dump(),
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    async def payment_cancel(self, payment_id: str):
        response = await self._client.delete(
            BASE_URL + "/payment/cancel/" + payment_id,
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)
        
        return response.json()

    async def payment_refund(self, payment_id: str):
        response = await self._client.delete(
            BASE_URL + "/payment/refund/" + payment_id,
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)
        
        return response.json()

    async def payment_list(self, payment_list_request: PaymentListRequest):
        response = await self._client.post(
            BASE_URL + "/payment/list",
            data=payment_list_request.model_dump(),
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)

        validated_response = PaymentCheckResponse.model_validate_json(response.json())
        return validated_response

    # ebarimt
    async def ebarimt_create(self, ebarimt_create_request: EbarimtCreateRequest):
        response = await self._client.post(
            BASE_URL + "/ebarimt/create",
            data=ebarimt_create_request.model_dump(),
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response

    async def ebarimt_get(self, barimt_id: str):
        response = await self._client.get(
            BASE_URL + "/ebarimt/" + barimt_id,
            headers=await self.headers,
            timeout=self._timeout,
        )
        
        self._check_error(response)

        validated_response = Ebarimt.model_validate_json(response.json())
        return validated_response
