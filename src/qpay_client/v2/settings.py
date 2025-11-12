"""QPay client settings module."""

import os
import warnings

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class QPaySettings(BaseSettings):
    """QPay client settings."""

    # QPay v2 base urls
    _SANDBOX_URL = "https://merchant-sandbox.qpay.mn/v2"
    _MERCHANT_URL = "https://merchant.qpay.mn/v2"

    # Sandbox credentials for quickstart and testing
    _SANDBOX_USERNAME = "TEST_MERCHANT"
    _SANDBOX_PASSWORD = "123456"

    model_config = SettingsConfigDict(
        env_file=os.getenv("QPAY_ENV_FILE", ".env"),  # allows custom .env file
        env_file_encoding="utf-8",
        env_prefix="QPAY_",
        case_sensitive=False,
    )

    # Supplying default sandbox credentials for quickstart and testing
    username: str = Field(default="TEST_MERCHANT", description="QPay merchant username")
    password: SecretStr = Field(default_factory=lambda: SecretStr("123456"), description="QPay merchant password")
    sandbox: bool = Field(default=True, description="Use QPay sandbox environment")  # Boolean for sandbox or production
    token_leeway: float = Field(default=60, description="Seconds before expiry to refresh tokens")

    client_retries: int = 5
    client_delay: float = 0.5
    client_jitter: float = 0.5

    payment_check_retries: int = 5
    payment_check_delay: float = 0.5
    payment_check_jitter: float = 0.5

    @property
    def base_url(self) -> str:
        return self._SANDBOX_URL if self.sandbox else self._MERCHANT_URL

    @model_validator(mode="after")
    def warn_sandbox_credentials(self) -> Self:
        """Warn if using default sandbox credentials."""
        if self.sandbox and self.username == self._SANDBOX_USERNAME:
            warnings.warn("Using default QPay sandbox credentials.", UserWarning, stacklevel=2)
        return self
