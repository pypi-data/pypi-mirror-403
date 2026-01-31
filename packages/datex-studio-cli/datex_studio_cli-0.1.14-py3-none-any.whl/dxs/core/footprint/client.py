"""Footprint API token acquisition."""

from typing import cast

from dxs.utils.config import get_settings
from dxs.utils.errors import AuthenticationError


def get_footprint_token() -> str:
    """Get an OAuth token for Footprint API.

    Uses the existing MSAL client to acquire a token with the
    Footprint API scope.

    Priority:
        0. DXS_FOOTPRINT_TOKEN environment variable (direct token from external auth)
        1. DXS_REFRESH_TOKEN environment variable (OBO flow)
        2. MSAL silent acquisition (cached token)
        3. File-based refresh token

    Returns:
        Access token for Footprint API

    Raises:
        AuthenticationError: If token acquisition fails
    """
    import os

    from dxs.core.auth.msal_client import MSALClient
    from dxs.core.auth.token_cache import MultiIdentityTokenCache

    # Priority 0: DXS_FOOTPRINT_TOKEN environment variable (direct token)
    # Used when an external tool (e.g., Sidekick) provides a pre-acquired Footprint token
    env_footprint_token = os.environ.get("DXS_FOOTPRINT_TOKEN")
    if env_footprint_token:
        return env_footprint_token

    settings = get_settings()
    footprint_scopes = [settings.footprint_scope]

    # Track the error from env token attempt for better error reporting
    env_token_error: str | None = None
    env_token_error_desc: str | None = None

    # Priority 1: DXS_REFRESH_TOKEN environment variable (OBO flow)
    env_refresh_token = os.environ.get("DXS_REFRESH_TOKEN")
    if env_refresh_token:
        try:
            msal_client = MSALClient(scopes=footprint_scopes)
            result = msal_client._app.acquire_token_by_refresh_token(
                refresh_token=env_refresh_token,
                scopes=footprint_scopes,
            )
            if result and "access_token" in result:
                return cast(str, result["access_token"])
            # Capture MSAL error response for reporting
            if result:
                env_token_error = result.get("error", "unknown_error")
                env_token_error_desc = result.get(
                    "error_description", "OBO token acquisition failed"
                )
            else:
                env_token_error = "no_result"
                env_token_error_desc = "No response from OBO token refresh"
        except Exception as e:
            env_token_error = "exception"
            env_token_error_desc = f"OBO token acquisition failed: {e}"

    # Priority 2: Try to get token from MSAL silent acquisition
    msal_client = MSALClient(scopes=footprint_scopes)
    result = msal_client.acquire_token_silent()
    if result and "access_token" in result:
        return cast(str, result["access_token"])

    # Priority 3: Try using the stored refresh token from file cache
    cache = MultiIdentityTokenCache()
    identity = cache.get_active_identity()
    if identity and identity.refresh_token:
        try:
            result = msal_client._app.acquire_token_by_refresh_token(
                refresh_token=identity.refresh_token,
                scopes=footprint_scopes,
            )
            if result and "access_token" in result:
                return cast(str, result["access_token"])

            error = result.get("error") if result else "no_result"
            error_desc = (
                result.get("error_description") if result else "No response from token refresh"
            )
        except Exception as e:
            error = "exception"
            error_desc = str(e)
    else:
        # If env token was tried but failed, report that error instead
        if env_token_error:
            error = env_token_error
            error_desc = env_token_error_desc
        else:
            error = "no_refresh_token"
            error_desc = (
                "No refresh token available (set DXS_REFRESH_TOKEN or run 'dxs auth login')"
            )

    raise AuthenticationError(
        message=f"Could not acquire Footprint API token: {error_desc}",
        code="DXS-FOOTPRINT-AUTH-001",
        details={"error": error, "error_description": error_desc},
        suggestions=[
            "Set DXS_FOOTPRINT_TOKEN environment variable for direct token injection",
            "Set DXS_REFRESH_TOKEN environment variable for OBO flow",
            "Run 'dxs auth login' to authenticate with refresh token",
            "Ensure your account has Footprint API access",
        ],
    )
