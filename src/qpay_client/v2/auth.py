"""QPay client authentication state module."""

import time
from dataclasses import dataclass

from .error import AuthError
from .schemas import TokenResponse


def _normalize_to_capital(token_type: str) -> str:
    return token_type.capitalize()


@dataclass()
class QpayAuthState:
    """Contains authentication information about the client."""

    token_type: str = "Bearer"
    access_token: str = ""
    access_token_expiry: float = 0  # epoch seconds
    refresh_token: str = ""
    refresh_token_expiry: float = 0  # epoch seconds
    scope: str = ""
    not_before_policy: str = ""
    session_state: str = ""

    def has_access_token(self) -> bool:
        """Used to check if client has access_token."""
        return bool(self.access_token)

    def get_access_token(self) -> str:
        """Returns an AuthError if access_token is falsy else returns the access token."""
        if self.access_token:
            return self.access_token
        raise AuthError("User don't have access")

    def access_as_header(self) -> str:
        """Used to get access token as HTTP Header format."""
        if not self.has_access_token():
            raise AuthError("No access token.")
        return f"{_normalize_to_capital(self.token_type)} {self.access_token}"

    def refresh_as_header(self) -> str:
        """Used to get fresh token as HTTP Header format."""
        return f"{_normalize_to_capital(self.token_type)} {self.refresh_token}"

    def is_access_expired(self, leeway: float = 60) -> bool:
        """Used to check if access token is expired."""
        return time.time() >= self.access_token_expiry - leeway

    def is_refresh_expired(self, leeway: float = 60) -> bool:
        """Used to check if refresh token is expired."""
        return time.time() >= self.refresh_token_expiry - leeway

    def update(self, token_response: TokenResponse) -> None:
        """Used to update token states with token_response."""
        # QPay seem to return lowercase token type
        self.token_type = _normalize_to_capital(token_response.token_type)
        self.access_token = token_response.access_token
        self.access_token_expiry = token_response.expires_in
        self.refresh_token = token_response.refresh_token
        self.refresh_token_expiry = token_response.refresh_expires_in
        self.scope = token_response.scope
        self.not_before_policy = token_response.not_before_policy
        self.session_state = token_response.session_state
