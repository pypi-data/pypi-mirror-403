"""Azure MSAL integration for authentication."""

import logging
from collections.abc import Callable
from typing import Any, cast

import msal

from dxs.utils.config import get_settings
from dxs.utils.errors import AuthenticationError

logger = logging.getLogger(__name__)


class MSALClient:
    """Handles Azure Entra authentication via MSAL.

    This client manages authentication with Azure AD using either:
    - Interactive browser flow (preferred): Opens browser for authentication with
      support for multi-resource consent in a single prompt.
    - Device code flow (fallback): For headless environments where browser is unavailable.
    """

    def __init__(
        self,
        client_id: str | None = None,
        tenant_id: str | None = None,
        scopes: list[str] | None = None,
        authority: str | None = None,
    ) -> None:
        """Initialize the MSAL client.

        Args:
            client_id: Azure AD application client ID. Defaults to config value.
            tenant_id: Azure AD tenant ID. Defaults to config value.
            scopes: OAuth scopes to request. Defaults to config value.
            authority: Direct authority URL override. If provided, tenant_id is ignored.
        """
        settings = get_settings()

        self._client_id = client_id or settings.azure_client_id
        self._tenant_id = tenant_id or settings.azure_tenant_id
        self._scopes = scopes or settings.azure_scopes

        if not self._client_id:
            raise AuthenticationError(
                message="Azure client ID is not configured",
                code="DXS-AUTH-002",
                suggestions=[
                    "Set DXS_AZURE_CLIENT_ID environment variable",
                    "Run: dxs config set azure_client_id <your-client-id>",
                ],
            )

        # Allow direct authority override for external tenants
        if authority:
            self._authority = authority
        else:
            self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"

        # Create the MSAL public client application
        self._app = msal.PublicClientApplication(
            client_id=self._client_id,
            authority=self._authority,
        )

    @classmethod
    def for_tenant(cls, tenant_id: str, scopes: list[str] | None = None) -> "MSALClient":
        """Create an MSAL client for a specific tenant.

        Useful for authenticating against external B2C tenants.

        Args:
            tenant_id: The Azure AD tenant ID to authenticate against.
            scopes: OAuth scopes to request. Defaults to config value.

        Returns:
            MSALClient configured for the specified tenant.
        """
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        return cls(authority=authority, scopes=scopes)

    def authenticate_device_code(
        self,
        on_device_code: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Initiate device code flow authentication.

        Args:
            on_device_code: Callback to handle the device code response.
                           Receives dict with 'user_code', 'verification_uri',
                           'message', and 'expires_in'.

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            AuthenticationError: If authentication fails.
        """
        # Initiate device code flow
        flow = self._app.initiate_device_flow(scopes=self._scopes)

        if "user_code" not in flow:
            error_desc = flow.get("error_description", "Unknown error")
            raise AuthenticationError(
                message=f"Failed to initiate device code flow: {error_desc}",
                code="DXS-AUTH-003",
                details=flow,
            )

        # Call the callback with device code info
        if on_device_code:
            on_device_code(
                {
                    "user_code": flow["user_code"],
                    "verification_uri": flow["verification_uri"],
                    "message": flow.get("message", ""),
                    "expires_in": flow.get("expires_in", 900),
                }
            )

        # Wait for user to complete authentication (blocking)
        result = self._app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            error = result.get("error", "unknown_error")
            error_desc = result.get("error_description", "Authentication failed")

            if error == "authorization_pending":
                raise AuthenticationError(
                    message="Authentication timed out - user did not complete login",
                    code="DXS-AUTH-004",
                    suggestions=["Try again with: dxs auth login"],
                )
            elif error == "authorization_declined":
                raise AuthenticationError(
                    message="Authentication was declined by the user",
                    code="DXS-AUTH-005",
                    suggestions=["Try again with: dxs auth login"],
                )
            else:
                raise AuthenticationError(
                    message=f"Authentication failed: {error_desc}",
                    code="DXS-AUTH-001",
                    details={"error": error, "error_description": error_desc},
                )

        return cast(dict[str, Any], result)

    def authenticate_device_code_multi_resource(
        self,
        primary_scopes: list[str],
        additional_scopes: list[str] | None = None,
        additional_scope_sets: list[list[str]] | None = None,
        on_device_code: Callable[[dict[str, Any]], None] | None = None,
        on_additional_consent_needed: Callable[[str, list[str]], None] | None = None,
    ) -> dict[str, Any]:
        """Authenticate with multiple resources using device code flow.

        Authenticates with primary resource first, then uses refresh token
        to silently acquire tokens for additional resources. If consent is
        needed for additional resources, performs additional device code flows.

        Args:
            primary_scopes: Scopes for primary resource (e.g., Datex API)
            additional_scopes: Scopes for a single additional resource (deprecated, use additional_scope_sets)
            additional_scope_sets: List of scope lists for multiple additional resources
            on_device_code: Callback to handle the device code response
            on_additional_consent_needed: Callback when additional consent is needed (resource_name, scopes)

        Returns:
            Token response for primary resource (contains refresh_token)

        Raises:
            AuthenticationError: If authentication fails
        """
        # Initiate device flow with PRIMARY scopes only
        # Azure AD limitation: cannot acquire tokens for multiple resources at once
        flow = self._app.initiate_device_flow(scopes=primary_scopes)

        if "user_code" not in flow:
            error_desc = flow.get("error_description", "Unknown error")
            raise AuthenticationError(
                message=f"Failed to initiate device code flow: {error_desc}",
                code="DXS-AUTH-003",
            )

        # Show device code to user with consistent keys
        if on_device_code:
            on_device_code(
                {
                    "user_code": flow["user_code"],
                    "verification_uri": flow["verification_uri"],
                    "message": flow.get("message", ""),
                    "expires_in": flow.get("expires_in", 900),
                }
            )

        # Complete device code flow for primary resource
        result = self._app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            error = result.get("error", "unknown_error")
            error_desc = result.get("error_description", "Authentication failed")

            if error == "authorization_pending":
                raise AuthenticationError(
                    message="Authentication timed out - user did not complete login",
                    code="DXS-AUTH-004",
                    suggestions=["Try again with: dxs auth login"],
                )
            elif error == "authorization_declined":
                raise AuthenticationError(
                    message="Authentication was declined by the user",
                    code="DXS-AUTH-005",
                    suggestions=["Try again with: dxs auth login"],
                )
            else:
                raise AuthenticationError(
                    message=f"Authentication failed: {error_desc}",
                    code="DXS-AUTH-001",
                    details={"error": error, "error_description": error_desc},
                )

        # Build list of all additional scope sets to acquire
        all_additional_scopes: list[list[str]] = []
        if additional_scopes:
            all_additional_scopes.append(additional_scopes)
        if additional_scope_sets:
            all_additional_scopes.extend(additional_scope_sets)

        # Now use refresh token to get additional resource tokens
        # If consent is needed, perform additional device code flows
        if all_additional_scopes and "refresh_token" in result:
            for scope_set in all_additional_scopes:
                try:
                    additional_result = self._app.acquire_token_by_refresh_token(
                        refresh_token=result["refresh_token"],
                        scopes=scope_set,
                    )
                    # Check if consent is needed (AADSTS65001)
                    if additional_result and "error" in additional_result:
                        error = additional_result.get("error", "")
                        error_desc = additional_result.get("error_description", "")
                        if "AADSTS65001" in error_desc or error == "invalid_grant":
                            # Consent needed - do another device code flow for this resource
                            self._acquire_consent_for_resource(
                                scope_set, on_device_code, on_additional_consent_needed
                            )
                except Exception as e:
                    logger.debug(
                        "Failed to acquire token for additional scopes %s: %s",
                        scope_set,
                        e,
                    )

        return cast(dict[str, Any], result)

    def _acquire_consent_for_resource(
        self,
        scopes: list[str],
        on_device_code: Callable[[dict[str, Any]], None] | None = None,
        on_additional_consent_needed: Callable[[str, list[str]], None] | None = None,
    ) -> dict[str, Any] | None:
        """Perform device code flow to acquire consent for a specific resource.

        Args:
            scopes: Scopes requiring consent
            on_device_code: Callback to handle device code display
            on_additional_consent_needed: Callback to notify about additional consent

        Returns:
            Token result or None if failed
        """
        # Notify that additional consent is needed
        if on_additional_consent_needed:
            # Extract resource name from scope for display
            resource_name = scopes[0].rsplit("/", 1)[0] if scopes else "unknown"
            on_additional_consent_needed(resource_name, scopes)

        # Initiate device code flow for this resource
        flow = self._app.initiate_device_flow(scopes=scopes)

        if "user_code" not in flow:
            return None

        # Show device code to user
        if on_device_code:
            on_device_code(
                {
                    "user_code": flow["user_code"],
                    "verification_uri": flow["verification_uri"],
                    "message": flow.get("message", ""),
                    "expires_in": flow.get("expires_in", 900),
                }
            )

        # Complete device code flow
        try:
            result = self._app.acquire_token_by_device_flow(flow)
            if result and "access_token" in result:
                return cast(dict[str, Any], result)
        except Exception as e:
            logger.debug("Device code flow failed for resource consent: %s", e)

        return None

    def authenticate_interactive(
        self,
        scopes: list[str],
        extra_scopes_to_consent: list[str] | None = None,
    ) -> dict[str, Any]:
        """Authenticate interactively via browser with multi-resource consent.

        Opens a browser window for authentication. User can consent to multiple
        resources in a single prompt using extra_scopes_to_consent.

        Args:
            scopes: Primary scopes to request (token will be issued for this resource)
            extra_scopes_to_consent: Additional scopes to consent to (from other resources).
                User will consent to these but token won't be returned for them.
                Use refresh token to acquire tokens for these resources afterward.

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            AuthenticationError: If authentication fails.
        """
        try:
            result = self._app.acquire_token_interactive(
                scopes=scopes,
                extra_scopes_to_consent=extra_scopes_to_consent,
            )
        except Exception as e:
            raise AuthenticationError(
                message=f"Failed to open browser for authentication: {e}",
                code="DXS-AUTH-006",
                suggestions=[
                    "Ensure you have a default browser configured",
                    "Try using device code flow with: dxs auth login --device-code",
                ],
            ) from e

        if "access_token" not in result:
            error = result.get("error", "unknown_error")
            error_desc = result.get("error_description", "Authentication failed")

            if error == "authorization_declined" or "cancelled" in error_desc.lower():
                raise AuthenticationError(
                    message="Authentication was cancelled or declined",
                    code="DXS-AUTH-005",
                    suggestions=["Try again with: dxs auth login"],
                )
            else:
                raise AuthenticationError(
                    message=f"Authentication failed: {error_desc}",
                    code="DXS-AUTH-001",
                    details={"error": error, "error_description": error_desc},
                )

        return cast(dict[str, Any], result)

    def acquire_token_silent(self) -> dict[str, Any] | None:
        """Attempt to acquire a token silently from cache.

        This will use cached tokens and automatically refresh if needed.

        Returns:
            Token response if successful, None if no cached token or refresh fails.
        """
        accounts = self._app.get_accounts()
        if not accounts:
            return None

        # Try to get token silently for the first account
        result = self._app.acquire_token_silent(
            scopes=self._scopes,
            account=accounts[0],
        )

        if result and "access_token" in result:
            return cast(dict[str, Any], result)

        return None

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        """Refresh access token using refresh token grant.

        Args:
            refresh_token: The refresh token from a previous authentication.

        Returns:
            Token response dict if successful, None if refresh failed.
        """
        try:
            result = self._app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self._scopes,
            )
            if result and "access_token" in result:
                return cast(dict[str, Any], result)
        except Exception as e:
            logger.debug("Failed to refresh access token: %s", e)
        return None

    def get_accounts(self) -> list[dict[str, Any]]:
        """Get all cached accounts.

        Returns:
            List of account dictionaries.
        """
        return cast(list[dict[str, Any]], self._app.get_accounts())

    def get_all_cached_tokens(
        self, scope_sets: list[list[str]]
    ) -> dict[int, dict[str, Any] | None]:
        """Get all cached tokens for different scope sets.

        Args:
            scope_sets: List of scope lists to check (e.g., [datex_scopes, devops_scopes])

        Returns:
            Dictionary mapping scope set index to token info (or None if not cached)
        """
        accounts = self._app.get_accounts()
        if not accounts:
            return {}

        results: dict[int, dict[str, Any] | None] = {}
        for idx, scopes in enumerate(scope_sets):
            try:
                result = self._app.acquire_token_silent(
                    scopes=scopes,
                    account=accounts[0],
                )
                if result and "access_token" in result:
                    results[idx] = {
                        "scopes": scopes,
                        "expires_on": result.get("expires_on"),
                        "has_token": True,
                    }
                else:
                    results[idx] = None
            except Exception as e:
                logger.debug("Failed to get cached token for scopes %s: %s", scopes, e)
                results[idx] = None

        return results

    def logout(self, account: dict[str, Any] | None = None) -> bool:
        """Remove cached account(s).

        Args:
            account: Specific account to remove. If None, removes all accounts.

        Returns:
            True if any accounts were removed.
        """
        accounts = [account] if account else self._app.get_accounts()
        removed = False

        for acc in accounts:
            if acc:
                self._app.remove_account(acc)
                removed = True

        return removed

    @property
    def client_id(self) -> str:
        """Get the client ID."""
        return self._client_id

    @property
    def tenant_id(self) -> str:
        """Get the tenant ID."""
        return self._tenant_id

    @property
    def scopes(self) -> list[str]:
        """Get the configured scopes."""
        return self._scopes
