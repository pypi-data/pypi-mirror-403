"""Authentication module for Azure Entra integration."""

from dxs.core.auth.decorators import (
    get_access_token,
    get_access_token_for_scopes,
    get_current_identity,
    get_current_organization,
    require_auth,
    verify_org_match,
)
from dxs.core.auth.msal_client import MSALClient
from dxs.core.auth.token_cache import (
    CachedIdentity,
    CachedToken,
    MultiIdentityTokenCache,
    TokenCache,
)

__all__ = [
    "MSALClient",
    "TokenCache",
    "MultiIdentityTokenCache",
    "CachedToken",
    "CachedIdentity",
    "require_auth",
    "get_access_token",
    "get_access_token_for_scopes",
    "get_current_identity",
    "get_current_organization",
    "verify_org_match",
]
