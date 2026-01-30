"""
OAuth2 Authentication implementation for HTTPX.

Implements authorization code flow with PKCE and automatic token refresh.
"""

from .exceptions import OAuthFlowError, OAuthRegistrationError, OAuthTokenError
from .provider import (
    OAuthClientProvider,
    PKCEParameters,
    TokenStorage,
)
from ...types.auth import (
    OAuthClientMetadata,
    OAuthToken,
    ProtectedResourceMetadata,
    OAuthMetadata,
    OAuthClientInformationFull
)

__all__ = [
    "OAuthClientProvider",
    "OAuthFlowError",
    "OAuthRegistrationError",
    "OAuthTokenError",
    "PKCEParameters",
    "TokenStorage",
    "OAuthClientMetadata",
    "OAuthToken",
    "ProtectedResourceMetadata",
    "OAuthMetadata",
    "OAuthClientInformationFull",
]
