"""CATAPA Python Client.

Main entry point for the CATAPA Python SDK with authentication wrapper.

This package provides:
- Catapa: Main wrapper class with automatic OAuth2 authentication.
- CatapaAuth & CatapaConfig: Authentication utilities.
- All generated API classes (EmployeeApi, OrganizationApi, etc.).
- All generated model classes (EmployeeResponse, CompanyDetailResponse, etc.).
- Core classes (Configuration, ApiClient).
- Exception classes (ApiException, etc.).

Authors:
    Handrian Alandi (handrian.alandi@gdplabs.id)

References:
    NONE
"""

# Authentication utilities
from catapa.auth.catapa_auth import CatapaAuth, CatapaConfig

# Auto-refresh API client
from catapa.auto_refresh_api_client import AutoRefreshApiClient

# Main wrapper class
from catapa.wrapper import Catapa

# Import all generated exports
# Note: openapi_client is now installed as a proper package alongside catapa
try:
    from openapi_client import *  # noqa: F401, F403
    from openapi_client import __all__ as _generated_all
except ImportError:
    # Fallback if generated code doesn't exist yet
    _generated_all = []

__version__ = "0.1.4"
__author__ = "Catapa Team"
__email__ = "dev@catapa.com"

# Explicitly define __all__ for better IDE support
# This combines wrapper-specific exports with all generated exports
__all__ = [
    # Main wrapper classes
    "Catapa",
    "CatapaAuth",
    "CatapaConfig",
    "AutoRefreshApiClient",
] + list(_generated_all)
