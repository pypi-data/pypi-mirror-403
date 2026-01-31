"""Custom ApiClient with automatic token refresh support.

This module provides a wrapper around the generated ApiClient that automatically
refreshes OAuth2 tokens before making API requests, similar to the TypeScript SDK.

Authors:
    Handrian Alandi (handrian.alandi@gdplabs.id)

References:
    NONE
"""


from catapa.auth.catapa_auth import CatapaAuth
from openapi_client import ApiClient, Configuration, rest


class AutoRefreshApiClient(ApiClient):
    """Extended ApiClient that automatically refreshes access tokens before requests.

    This provides the same seamless auto-refresh behavior as the TypeScript SDK,
    where tokens are checked and refreshed automatically on every API call without
    requiring manual re-instantiation of API objects.

    Attributes:
        _catapa_auth (CatapaAuth | None): Authentication instance for token management.

    Example:
        auth = CatapaAuth(config)
        api_client = AutoRefreshApiClient(configuration, auth)

        # Token automatically refreshed on every call
        employee_api = EmployeeApi(api_client)
        employees = employee_api.list_all_employees()  # ✅ Auto-refresh!
    """

    def __init__(
        self,
        configuration: Configuration | None = None,
        auth: CatapaAuth | None = None,
        header_name: str | None = None,
        header_value: str | None = None,
        cookie: str | None = None
    ) -> None:
        """Initialize the auto-refresh API client.

        Args:
            configuration (Configuration | None, optional): OpenAPI Configuration object. Defaults to None.
            auth (CatapaAuth | None, optional): CatapaAuth instance for token management. Defaults to None.
            header_name (str | None, optional): Optional header name. Defaults to None.
            header_value (str | None, optional): Optional header value. Defaults to None.
            cookie (str | None, optional): Optional cookie. Defaults to None.
        """
        super().__init__(configuration, header_name, header_value, cookie)
        self._catapa_auth = auth

    def call_api(self, *args, **kwargs) -> rest.RESTResponse:
        """Override call_api to refresh token before making requests.

        This method is called by all generated API methods before making
        HTTP requests, making it the perfect place to inject token refresh logic.
        """
        # Refresh token if needed before making the request
        if self._catapa_auth:
            fresh_token = self._catapa_auth.get_access_token()
            # Update the configuration with the fresh token
            if self.configuration:
                self.configuration.access_token = fresh_token

        # Call the original method
        return super().call_api(*args, **kwargs)
