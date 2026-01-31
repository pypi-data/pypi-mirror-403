"""CATAPA Authentication Module.

This module handles OAuth2 authentication for the CATAPA API,
supporting client credentials flow with automatic token refresh.

Authors:
    Handrian Alandi (handrian.alandi@gdplabs.id)

References:
    [1] https://developer.catapa.com/#section/Authentication
"""

import time
from dataclasses import dataclass
from typing import Any

import requests
from catapa.auth.constant import ONE_HOUR_IN_SECONDS, TOKEN_EXPIRATION_BUFFER_SECONDS
from requests.auth import HTTPBasicAuth


class CatapaAuthError(Exception):
    """Exception raised for CATAPA authentication errors.

    This exception is raised when authentication fails, such as when
    the OAuth2 token request fails or returns an error response.
    """

    pass

@dataclass
class CatapaConfig:
    """Configuration for CATAPA API authentication."""
    tenant: str
    client_id: str
    client_secret: str
    base_url: str = "https://api.catapa.com"


@dataclass
class TokenInfo:
    """Internal token storage with expiration tracking."""
    access_token: str
    token_type: str
    expires_at: float  # timestamp in seconds


class CatapaAuth:
    """Handles OAuth2 authentication for CATAPA API.

    Features:
    - Automatic token refresh with 5-minute buffer
    - Thread-safe token management
    - Client credentials flow support

    Attributes:
        config (CatapaConfig): Configuration for CATAPA API authentication.
        _token_info (TokenInfo | None): Internal token storage with expiration tracking.

    Example:
        auth = CatapaAuth(CatapaConfig(
            tenant="your-tenant",
            client_id="your-client-id",
            client_secret="your-client-secret"
        ))

        token = auth.get_access_token()
    """

    def __init__(self, config: CatapaConfig) -> None:
        """Initialize the CATAPA authentication instance.

        Args:
            config (CatapaConfig): Configuration for CATAPA API authentication.
        """
        self.config = config
        self._token_info: TokenInfo | None = None

    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            str: Valid access token

        Raises:
            CatapaAuthError: If authentication fails
        """
        # If we have a valid token, return it
        if self._token_info and self._is_token_valid():
            return self._token_info.access_token

        # Refresh the token
        return self._fetch_new_token()

    def refresh_token(self) -> None:
        """Force refresh the access token."""
        self._token_info = None
        self.get_access_token()

    def _is_token_valid(self) -> bool:
        """Check if current token is valid (not expired).

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self._token_info:
            return False

        # Add buffer before expiration to ensure token is refreshed in time
        return time.time() < (self._token_info.expires_at - TOKEN_EXPIRATION_BUFFER_SECONDS)

    def _fetch_new_token(self) -> str:
        """Fetch a new access token from the OAuth2 endpoint.

        Returns:
            str: New access token

        Raises:
            CatapaAuthError: If authentication fails
        """
        url = f"{self.config.base_url}/oauth/token"

        headers = {
            "Tenant": self.config.tenant,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        data = {
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=HTTPBasicAuth(self.config.client_id, self.config.client_secret)
            )
            response.raise_for_status()

            token_response = response.json()

            # Store token with expiration info
            self._token_info = TokenInfo(
                access_token=token_response["access_token"],
                token_type=token_response.get("token_type", "Bearer"),
                expires_at=time.time() + token_response.get("expires_in", ONE_HOUR_IN_SECONDS)
            )

            return self._token_info.access_token

        except requests.exceptions.RequestException as e:
            raise CatapaAuthError(f"Failed to obtain access token: {str(e)}") from e

    def validate_token(self, access_token: str | None = None) -> bool:
        """Validate access token using dedicated endpoint.

        Args:
            access_token (str | None, optional): Token to validate. If None, uses current token. Defaults to None.

        Returns:
            bool: True if token is valid, False otherwise
        """
        token = access_token or (self._token_info.access_token if self._token_info else None)
        if not token:
            return False

        url = f"{self.config.base_url}/v1/oauth-clients/validate-access-token"

        try:
            response = requests.get(
                url,
                headers={
                    "Tenant": self.config.tenant,
                    "Authorization": f"Bearer {token}"
                }
            )
            return response.ok  # 200 OK means valid, 401 means invalid
        except requests.exceptions.RequestException:
            # If validation endpoint fails, assume token is invalid
            return False

    def get_token_info(self) -> dict[str, Any] | None:
        """Get current token info for debugging/monitoring.

        Returns:
            dict[str, Any] | None: Token information or None if no token
        """
        if not self._token_info:
            return None

        return {
            "access_token": self._token_info.access_token[:5] + "..." + self._token_info.access_token[-5:],
            "token_type": self._token_info.token_type,
            "expires_at": self._token_info.expires_at,
            "is_valid": self._is_token_valid()
        }

    def clear_token(self) -> None:
        """Clear stored token (useful for logout)."""
        self._token_info = None
