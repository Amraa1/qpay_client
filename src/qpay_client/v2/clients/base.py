import logging
from abc import ABC, abstractmethod
from typing import Optional

from httpx import Headers
from pydantic import BaseModel

from ..auth import QpayAuthState
from ..settings import QPaySettings


class BaseClient(ABC):
    """
    Synchronous client for QPay v2 API.

    This client handles authentication, token refresh, and provides async
    methods for interacting with QPay v2 endpoints (invoices, payments,
    subscriptions, and ebarimt). It is designed to follow the official QPay v2.

    Note:
        QPayClientSync is not thread-safe.
        Use one instance per thread or protect externally.

    """

    def __init__(
        self,
        settings: QPaySettings,
        *,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize QPayClientSync object.

        Args:
            settings (Settings): QPay client settings.
            client (Optional[httpx.Client]): Optional custom httpx client.
            logger (Optional[logging.Logger]): QPay client logger.


        """
        self._id = id(self)
        self._settings = settings
        self._auth_state = QpayAuthState()

        # If base_url is supplied use that else use settings
        self._base_url = self._settings.base_url
        self._token_leeway = self._settings.token_leeway

        # Logging config
        self._logger = logger or logging.getLogger(f"qpay.{self._id}")
        self._logger.setLevel(settings.log_level)

        self._logger.debug(f"QPayClient initialized with id: {self._id}.")

    @property
    def is_authenticated(self) -> bool:
        """Returns True of authenticated and not expired."""
        return self._auth_state.has_access_token() and not self.is_access_expired

    @property
    def is_access_expired(self) -> bool:
        """Returns True if access token is expired."""
        return self._auth_state.is_access_expired(leeway=self._token_leeway)

    @property
    def is_refresh_expired(self) -> bool:
        """Returns True if refresh token is expired."""
        return self._auth_state.is_refresh_expired(leeway=self._token_leeway)

    @property
    def token(self) -> str:
        """Get client token."""
        return self._auth_state.get_access_token()

    @property
    def base_url(self) -> str:
        """Get base url."""
        return self._base_url

    @property
    def auth_state(self) -> QpayAuthState:
        return self._auth_state

    def headers(self):
        """Headers needed for communication between qpay client and qpay server."""
        header = Headers(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "qpay-client",
            }
        )
        if self.is_authenticated:
            header.update({"Authorization": f"Bearer {self.token}"})
        return header

    def _invoice_create_payload(self, request_model: BaseModel) -> dict:
        """Build invoice-create payload and default invoice_code from settings when omitted."""
        payload = request_model.model_dump(by_alias=True, exclude_none=True, mode="json")
        payload.setdefault("invoice_code", self._settings.invoice_code)
        return payload

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Returns True of connection is closed."""
        ...
