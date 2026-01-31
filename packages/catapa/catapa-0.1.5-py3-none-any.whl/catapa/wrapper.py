"""CATAPA Python Client - Main Wrapper Class.

This module provides an ergonomic wrapper around the auto-generated CATAPA API client
with automatic OAuth2 authentication and token management.

Authors:
    Handrian Alandi (handrian.alandi@gdplabs.id)

References:
    NONE
"""

# Add generated package to path is now handled in __init__.py

from catapa.auth.catapa_auth import CatapaAuth, CatapaConfig
from catapa.auto_refresh_api_client import AutoRefreshApiClient
from openapi_client import Configuration


class Catapa(AutoRefreshApiClient):
    """Main CATAPA wrapper class providing access to all CATAPA APIs with automatic OAuth2 authentication.

    This wrapper follows the same pattern as the TypeScript/Fetch implementation,
    providing a clean interface to all API endpoints without needing to wrap
    every single API call.

    Features:
    - Automatic OAuth2 authentication with token refresh on EVERY API call
    - Tokens are automatically refreshed when expired (5-minute buffer)
    - Thread-safe token management
    - No need to re-instantiate API objects after token expiration
    - Easy access to all 43+ CATAPA APIs

    Attributes:
        config (CatapaConfig): Configuration for CATAPA API authentication.
        _auth (CatapaAuth): Authentication instance for token management.
        _tenant_key (str): Key for the tenant header.
        default_headers (dict[str, str]): Default headers for the API client.

    Example:
        # Initialize the client
        client = Catapa(
            tenant="your-tenant",
            client_id="your-client-id",
            client_secret="your-client-secret"
        )

        # Use generated API classes with automatic authentication
        from catapa import EmployeeApi, OrganizationApi

        employee_api = EmployeeApi(client)
        employees = employee_api.list_all_employees(page=0, size=10)

        # Even after token expires, it will auto-refresh!
        time.sleep(3600)  # Wait 1 hour
        employees = employee_api.list_all_employees(page=0, size=10)  # ✅ Works!

        org_api = OrganizationApi(client)
        company = org_api.get_companies()
    """

    def __init__(
        self,
        tenant: str,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.catapa.com"
    ) -> None:
        """Initialize the CATAPA client.

        Args:
            tenant (str): Your CATAPA tenant name.
            client_id (str): OAuth2 client ID.
            client_secret (str): OAuth2 client secret.
            base_url (str, optional): API base URL. Defaults to "https://api.catapa.com".
        """
        self.config = CatapaConfig(
            tenant=tenant,
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url
        )

        self._auth = CatapaAuth(self.config)
        self._tenant_key = "Tenant"

        # Get initial access token
        access_token = self._auth.get_access_token()

        # Configure SDK
        configuration = Configuration(host=self.config.base_url)
        configuration.access_token = access_token

        # Initialize parent AutoRefreshApiClient with auto-refresh
        super().__init__(configuration, auth=self._auth)

        if not hasattr(self, "default_headers"):
            self.default_headers = {}
        tenant_value = getattr(self.config, "tenant", None)
        self.default_headers[self._tenant_key] = tenant_value


    def refresh_auth(self) -> None:
        """Force refresh the authentication token.

        This is useful when you know the token has expired or you want to
        ensure you have a fresh token.
        """
        self._auth.refresh_token()
        # Update the configuration with the fresh token
        if self.configuration:
            self.configuration.access_token = self._auth.get_access_token()

    def get_configuration(self) -> Configuration:
        """Get the underlying Configuration object for advanced usage.

        Returns:
            Configuration: The configuration object used by the API client
        """
        return self.configuration
