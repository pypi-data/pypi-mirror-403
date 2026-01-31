"""Authentication decorators for CLI commands."""

import base64
import functools
import json
import logging
import os
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar

from dxs.core.auth.token_cache import CachedIdentity, MultiIdentityTokenCache
from dxs.utils.errors import AuthenticationError

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Module-level cache for refreshed tokens (avoids repeated refresh calls)
_env_token_cache: dict[str, tuple[str, datetime]] = {}


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode JWT payload without verification (for expiry check only).

    Args:
        token: JWT token string.

    Returns:
        Decoded payload dict or None if decoding fails.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (second part), adding padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


def _is_token_expired(token: str, buffer_seconds: int = 60) -> bool:
    """Check if a JWT token is expired or about to expire.

    Args:
        token: JWT token string.
        buffer_seconds: Consider expired if within this many seconds of expiry.

    Returns:
        True if expired or expiring soon, False otherwise.
    """
    payload = _decode_jwt_payload(token)
    if payload is None:
        # Can't decode - assume valid and let API reject if invalid
        return False

    exp = payload.get("exp")
    if exp is None:
        return False

    expiry_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    return now >= expiry_time - __import__("datetime").timedelta(seconds=buffer_seconds)


def _refresh_env_token(scopes: list[str] | None = None) -> str | None:
    """Refresh token using DXS_REFRESH_TOKEN environment variable.

    Args:
        scopes: OAuth scopes to request. Defaults to Datex API scopes.

    Returns:
        New access token string or None if refresh fails.
    """
    refresh_token = os.environ.get("DXS_REFRESH_TOKEN")
    if not refresh_token:
        return None

    # Check module-level cache first
    cache_key = ",".join(scopes) if scopes else "default"
    if cache_key in _env_token_cache:
        cached_token, cached_at = _env_token_cache[cache_key]
        # Use cached token if less than 5 minutes old
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age < 300 and not _is_token_expired(cached_token):
            return cached_token

    try:
        from dxs.core.auth.msal_client import MSALClient

        client = MSALClient()
        result = client.refresh_access_token(refresh_token)

        if result and "access_token" in result:
            new_token = result["access_token"]
            _env_token_cache[cache_key] = (new_token, datetime.now(timezone.utc))
            logger.debug("Successfully refreshed token via DXS_REFRESH_TOKEN")
            return new_token
    except Exception as e:
        logger.debug("Failed to refresh token via DXS_REFRESH_TOKEN: %s", e)

    return None


def require_auth(f: F) -> F:
    """Decorator that ensures valid authentication before command execution.

    Checks for a valid, non-expired token in the cache. If expired, attempts
    to refresh using the stored refresh token. If no valid token exists,
    raises an AuthenticationError with instructions to run 'dxs auth login'.

    Priority:
        1. DXS_ACCESS_TOKEN env var (with DXS_REFRESH_TOKEN for refresh if expired)
        2. File-based token cache (~/.datex/credentials.yaml)

    Usage:
        @source.command()
        @pass_context
        @require_auth
        def my_command(ctx: DxsContext) -> None:
            ...
    """

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Priority 1: Environment variables (Sidekick injection)
        env_token = os.environ.get("DXS_ACCESS_TOKEN")
        if env_token:
            # Check if token is expired
            if _is_token_expired(env_token):
                # Try to refresh using DXS_REFRESH_TOKEN
                refreshed = _refresh_env_token()
                if refreshed is None:
                    raise AuthenticationError(
                        message="DXS_ACCESS_TOKEN is expired and refresh failed",
                        code="DXS-AUTH-001",
                        suggestions=[
                            "Set DXS_REFRESH_TOKEN to enable automatic refresh",
                            "Or provide a fresh DXS_ACCESS_TOKEN",
                        ],
                    )
            return f(*args, **kwargs)

        # Priority 2: File cache (multi-identity)
        cache = MultiIdentityTokenCache()
        token = cache.get_valid_token()

        if token is None:
            # Token expired or missing - try to refresh
            refreshed_token = cache.try_refresh()
            if refreshed_token is not None:
                # Refresh succeeded, continue
                return f(*args, **kwargs)

            # Refresh failed - raise appropriate error
            identity = cache.get_active_identity()
            if identity is not None:
                raise AuthenticationError(
                    message="Authentication token expired and refresh failed",
                    code="DXS-AUTH-001",
                    details={"expired_at": identity.expires_at.isoformat()},
                    suggestions=[
                        "Run 'dxs auth login' to re-authenticate",
                    ],
                )
            else:
                raise AuthenticationError(
                    message="Not authenticated. Please log in first.",
                    code="DXS-AUTH-002",
                    suggestions=[
                        "Run 'dxs auth login' to authenticate",
                        "Use 'dxs auth status' to check authentication state",
                    ],
                )

        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def get_access_token() -> str:
    """Get the current access token for the Datex Studio API.

    Priority:
        1. DXS_ACCESS_TOKEN environment variable (with auto-refresh via DXS_REFRESH_TOKEN)
        2. Token cache with auto-refresh (multi-identity)

    Returns:
        The access token string.

    Raises:
        AuthenticationError: If not authenticated or token expired and refresh failed.
    """
    # Priority 1: Environment variables (Sidekick injection)
    env_token = os.environ.get("DXS_ACCESS_TOKEN")
    if env_token:
        # Check if token is expired
        if _is_token_expired(env_token):
            # Try to refresh using DXS_REFRESH_TOKEN
            refreshed = _refresh_env_token()
            if refreshed is not None:
                return refreshed
            raise AuthenticationError(
                message="DXS_ACCESS_TOKEN is expired and refresh failed",
                code="DXS-AUTH-001",
                suggestions=[
                    "Set DXS_REFRESH_TOKEN to enable automatic refresh",
                    "Or provide a fresh DXS_ACCESS_TOKEN",
                ],
            )
        return env_token

    # Priority 2: File cache (multi-identity)
    cache = MultiIdentityTokenCache()
    token = cache.get_valid_token()

    if token is not None:
        return token

    # Token expired or missing - try to refresh
    refreshed_token = cache.try_refresh()
    if refreshed_token is not None:
        return refreshed_token

    # Refresh failed - raise appropriate error
    identity = cache.get_active_identity()
    if identity is not None:
        raise AuthenticationError(
            message="Authentication token expired and refresh failed",
            code="DXS-AUTH-001",
            suggestions=["Run 'dxs auth login' to re-authenticate"],
        )
    else:
        raise AuthenticationError(
            message="Not authenticated. Please log in first.",
            code="DXS-AUTH-002",
            suggestions=["Run 'dxs auth login' to authenticate"],
        )


def get_access_token_for_scopes(scopes: list[str]) -> str:
    """Get an access token for specific OAuth scopes (OBO flow).

    Use this for accessing other resources like Azure DevOps or Dynamics CRM.
    Requires DXS_REFRESH_TOKEN or file-based auth with refresh token.

    Args:
        scopes: OAuth scopes to request (e.g., Azure DevOps or Dynamics scopes).

    Returns:
        Access token for the requested scopes.

    Raises:
        AuthenticationError: If unable to acquire token for the requested scopes.
    """
    cache_key = ",".join(sorted(scopes))

    # Check in-memory cache first
    if cache_key in _env_token_cache:
        cached_token, _cached_time = _env_token_cache[cache_key]
        if not _is_token_expired(cached_token):
            logger.debug("Using in-memory cached token for scopes %s", scopes)
            return cached_token
        del _env_token_cache[cache_key]

    # Check file-based resource token cache
    file_cache = MultiIdentityTokenCache()
    cached_rt = file_cache.get_resource_token(cache_key)
    if cached_rt:
        logger.debug("Using file-cached token for scopes %s", scopes)
        _env_token_cache[cache_key] = (cached_rt, datetime.now(timezone.utc))
        return cached_rt

    logger.info("Acquiring token for scopes %s...", scopes)

    # Priority 1: Environment variable refresh token
    refresh_token = os.environ.get("DXS_REFRESH_TOKEN")
    if refresh_token:
        try:
            from dxs.core.auth.msal_client import MSALClient

            client = MSALClient(scopes=scopes)
            result = client._app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=scopes,
            )
            if result and "access_token" in result:
                token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                _env_token_cache[cache_key] = (token, datetime.now(timezone.utc))
                file_cache.save_resource_token(cache_key, token, expires_in)
                return token
        except Exception as e:
            logger.debug("Failed to acquire token for scopes %s: %s", scopes, e)

    # Priority 2: File cache with refresh token
    identity = file_cache.get_active_identity()

    if identity and identity.refresh_token:
        try:
            from dxs.core.auth.msal_client import MSALClient

            client = MSALClient(scopes=scopes)
            result = client._app.acquire_token_by_refresh_token(
                refresh_token=identity.refresh_token,
                scopes=scopes,
            )
            if result and "access_token" in result:
                token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                _env_token_cache[cache_key] = (token, datetime.now(timezone.utc))
                file_cache.save_resource_token(cache_key, token, expires_in)
                return token
        except Exception as e:
            logger.debug("Failed to acquire token for scopes %s: %s", scopes, e)

    raise AuthenticationError(
        message=f"Unable to acquire token for scopes: {scopes}",
        code="DXS-AUTH-007",
        suggestions=[
            "Ensure you have consented to the required scopes",
            "Run 'dxs auth login' to re-authenticate with full consent",
        ],
    )


def get_current_organization() -> tuple[int, str] | None:
    """Get the current organization from the active identity.

    Returns:
        Tuple of (organization_id, organization_name) if available, None otherwise.
    """
    # Environment variable mode doesn't have org info
    if os.environ.get("DXS_ACCESS_TOKEN"):
        return None

    cache = MultiIdentityTokenCache()
    identity = cache.get_active_identity()

    if identity is None:
        return None

    if identity.organization_id is None:
        return None

    return (identity.organization_id, identity.organization_name or "")


def get_current_identity() -> CachedIdentity | None:
    """Get the current active identity.

    Returns:
        The active CachedIdentity if available, None otherwise.
    """
    # Environment variable mode doesn't have identity info
    if os.environ.get("DXS_ACCESS_TOKEN"):
        return None

    cache = MultiIdentityTokenCache()
    return cache.get_active_identity()


def verify_org_match(
    resource_org_id: int,
    resource_org_name: str | None = None,
) -> None:
    """Verify the current identity matches the resource's organization.

    Args:
        resource_org_id: The organization ID of the resource being accessed.
        resource_org_name: Optional organization name for error messages.

    Raises:
        OrganizationMismatchError: If organizations don't match.
    """
    from dxs.utils.errors import OrganizationMismatchError

    # Environment variable mode - skip check (can't verify)
    if os.environ.get("DXS_ACCESS_TOKEN"):
        return

    cache = MultiIdentityTokenCache()
    identity = cache.get_active_identity()

    if identity is None:
        # Not authenticated, will be caught by @require_auth
        return

    # If identity doesn't have org info yet, skip check
    if identity.organization_id is None:
        return

    # Check for mismatch
    if identity.organization_id != resource_org_id:
        # Build helpful suggestions
        suggestions = [
            "Run 'dxs auth list' to see available identities",
            "Run 'dxs auth login' to authenticate with a different account",
        ]

        # Check if we have a cached identity for the target org
        for username, cached_identity, _ in cache.list_identities():
            if cached_identity.organization_id == resource_org_id:
                suggestions.insert(
                    0, f"Run 'dxs auth switch {username}' to switch to this organization"
                )
                break

        raise OrganizationMismatchError(
            resource_org_id=resource_org_id,
            resource_org_name=resource_org_name,
            current_org_id=identity.organization_id,
            current_org_name=identity.organization_name,
            current_username=identity.account_username,
            suggestions=suggestions,
        )
