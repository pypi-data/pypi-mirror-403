"""Authentication commands: dxs auth [login|logout|status|list|switch]."""

from datetime import datetime, timedelta, timezone
from typing import Any

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.auth import MSALClient, MultiIdentityTokenCache
from dxs.utils.errors import AuthenticationError
from dxs.utils.responses import list_response, single
from dxs.utils.restricted import restrict_in_restricted_mode


@click.group()
def auth() -> None:
    """Authentication commands.

    Manage authentication with Azure Entra (Azure AD) using device code flow.
    Supports multiple identities for different organizations.

    \b
    The device code flow works as follows:
    1. Run 'dxs auth login'
    2. A code and URL will be displayed
    3. Open the URL in a browser and enter the code
    4. Complete authentication in the browser
    5. The CLI will automatically receive the token
    """
    pass


@auth.command()
@pass_context
def login(ctx: DxsContext) -> None:
    """Authenticate with Azure Entra using device code flow.

    Uses device code flow for authentication. On first login, you may need
    to complete multiple authentication prompts to consent to all required
    API permissions. Subsequent logins will only require a single prompt.

    If you are already authenticated with a different identity, this will
    add a new identity and set it as active (use 'dxs auth switch' to change).

    \b
    Example:
        dxs auth login
    """
    from dxs.utils.config import get_settings

    cache = MultiIdentityTokenCache()
    settings = get_settings()

    try:
        client = MSALClient(scopes=settings.azure_scopes)
    except AuthenticationError as e:
        ctx.output_error(e)
        raise SystemExit(1) from None

    def on_device_code(device_code: dict[str, Any]) -> None:
        """Callback to display device code to user."""
        ctx.output(
            single(
                item={
                    "status": "awaiting_authentication",
                    "action_required": {
                        "type": "device_code",
                        "instructions": "Open the URL in a browser and enter the code to authenticate",
                        "url": device_code["verification_uri"],
                        "code": device_code["user_code"],
                        "expires_in_seconds": device_code["expires_in"],
                    },
                    "message": device_code.get("message", ""),
                },
                semantic_key="authentication",
            ),
            include_metadata=False,
        )

    def on_additional_consent_needed(resource_name: str, scopes: list[str]) -> None:
        """Callback when additional consent is needed for a resource."""
        ctx.log(f"Additional consent needed for: {resource_name}")
        ctx.output(
            single(
                item={
                    "status": "additional_consent_needed",
                    "message": f"Additional consent required for {resource_name}",
                    "resource": resource_name,
                    "scopes": scopes,
                },
                semantic_key="authentication",
            ),
            include_metadata=False,
        )

    try:
        ctx.log("Initiating device code authentication...")

        # Build additional scope sets, filtering out empty ones
        # (e.g., dynamics_crm_scopes is empty if dynamics_crm_url is not configured)
        additional_scope_sets = [
            scopes
            for scopes in [
                settings.azure_devops_scopes,
                settings.dynamics_crm_scopes,
                [settings.footprint_scope],
            ]
            if scopes  # Filter out empty scope lists
        ]

        result = client.authenticate_device_code_multi_resource(
            primary_scopes=settings.azure_scopes,
            additional_scope_sets=additional_scope_sets,
            on_device_code=on_device_code,
            on_additional_consent_needed=on_additional_consent_needed,
        )

        # Save identity (will be set as active)
        saved_identity = cache.save_identity(result)

        # Fetch organization info from API
        org_info = _fetch_organization_info(ctx)
        if org_info and saved_identity.account_username:
            cache.update_identity_org_info(
                saved_identity.account_username,
                org_info["id"],
                org_info["name"],
            )
            # Refresh identity after update
            saved_identity = cache.get_active_identity() or saved_identity

        # Output success
        ctx.output(
            single(
                item={
                    "status": "authenticated",
                    "message": "Successfully authenticated",
                    "account": saved_identity.account_username,
                    "organization": saved_identity.organization_name,
                    "organization_id": saved_identity.organization_id,
                    "expires_at": saved_identity.expires_at.isoformat(),
                },
                semantic_key="authentication",
            )
        )

    except AuthenticationError as e:
        ctx.output_error(e)
        raise SystemExit(1) from None


@auth.command()
@click.argument("identity", required=False)
@click.option("--all", "logout_all", is_flag=True, help="Logout all cached identities")
@pass_context
@restrict_in_restricted_mode("clears stored credentials")
def logout(ctx: DxsContext, identity: str | None, logout_all: bool) -> None:
    """Clear stored credentials.

    By default, removes only the currently active identity. Use --all to
    remove all cached identities.

    \b
    Examples:
        dxs auth logout              # Logout current identity
        dxs auth logout user@org.com # Logout specific identity
        dxs auth logout --all        # Logout all identities
    """
    cache = MultiIdentityTokenCache()

    if logout_all:
        # Clear all identities
        count = cache.clear_all()
        ctx.output(
            single(
                item={
                    "status": "logged_out_all",
                    "message": f"Logged out from all {count} identities",
                    "accounts_cleared": count,
                },
                semantic_key="authentication",
            )
        )
        return

    if identity:
        # Logout specific identity
        existing = cache.get_identity(identity)
        if not existing:
            ctx.output(
                single(
                    item={
                        "status": "not_found",
                        "message": f"Identity '{identity}' not found in cache",
                        "suggestion": "Run 'dxs auth list' to see available identities",
                    },
                    semantic_key="authentication",
                )
            )
            return

        was_active = cache.get_active_identity() == existing
        cache.remove_identity(identity)

        remaining = cache.list_identities()
        ctx.output(
            single(
                item={
                    "status": "logged_out",
                    "message": f"Successfully logged out from {identity}",
                    "account": identity,
                    "was_active": was_active,
                    "remaining_identities": len(remaining),
                    "hint": "Use 'dxs auth switch' to switch to another identity"
                    if remaining
                    else None,
                },
                semantic_key="authentication",
            )
        )
        return

    # Default: logout current active identity
    active = cache.get_active_identity()
    if not active:
        ctx.output(
            single(
                item={
                    "status": "not_logged_in",
                    "message": "No credentials to clear - you were not logged in",
                },
                semantic_key="authentication",
            )
        )
        return

    account_name = active.account_username
    cache.remove_identity(account_name or "")

    remaining = cache.list_identities()
    ctx.output(
        single(
            item={
                "status": "logged_out",
                "message": "Successfully logged out",
                "account": account_name,
                "remaining_identities": len(remaining),
                "hint": "Use 'dxs auth switch' to switch to another identity"
                if remaining
                else None,
            },
            semantic_key="authentication",
        )
    )


@auth.command()
@pass_context
def status(ctx: DxsContext) -> None:
    """Show current authentication status.

    Displays the currently active identity and all cached identities
    with their organization info and token expiration status.

    \b
    Example:
        dxs auth status
    """
    import os

    from dxs.utils.config import get_settings

    # Check for environment variable authentication first
    if os.environ.get("DXS_ACCESS_TOKEN"):
        from dxs.core.auth.decorators import _decode_jwt_payload

        token = os.environ["DXS_ACCESS_TOKEN"]
        has_refresh_token = bool(os.environ.get("DXS_REFRESH_TOKEN"))

        # Show truncated token for verification (first 10 and last 4 chars)
        token_preview = f"{token[:10]}...{token[-4:]}" if len(token) > 20 else "***"

        # Decode token to get expiry info
        payload = _decode_jwt_payload(token)
        token_info: dict[str, Any] = {"preview": token_preview}

        if payload:
            exp = payload.get("exp")
            if exp:
                expiry_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                expires_in_seconds = int((expiry_time - now).total_seconds())

                token_info["expires_at"] = expiry_time.isoformat()
                token_info["expired"] = expires_in_seconds <= 0

                if expires_in_seconds > 0:
                    if expires_in_seconds < 60:
                        token_info["expires_in_human"] = f"{expires_in_seconds} seconds"
                    elif expires_in_seconds < 3600:
                        token_info["expires_in_human"] = f"{expires_in_seconds // 60} minutes"
                    else:
                        token_info["expires_in_human"] = f"{expires_in_seconds // 3600} hours"

        status_item: dict[str, Any] = {
            "authenticated": True,
            "status": "authenticated_via_env",
            "message": "Authenticated via DXS_ACCESS_TOKEN environment variable",
            "access_token": token_info,
            "refresh_token_available": has_refresh_token,
        }

        if not has_refresh_token:
            status_item["note"] = (
                "Set DXS_REFRESH_TOKEN to enable automatic token refresh and OBO flows"
            )

        ctx.output(single(item=status_item, semantic_key="authentication"))
        return

    cache = MultiIdentityTokenCache()
    active_identity = cache.get_active_identity()

    if active_identity is None:
        ctx.output(
            single(
                item={
                    "authenticated": False,
                    "status": "not_authenticated",
                    "message": "Not logged in",
                    "suggestion": "Run 'dxs auth login' to authenticate",
                },
                semantic_key="authentication",
            )
        )
        return

    now = datetime.now(timezone.utc)
    is_expired = active_identity.expires_at <= now
    expires_in_seconds = int((active_identity.expires_at - now).total_seconds())

    # If primary token is expired, try to refresh it
    if is_expired:
        ctx.log("Primary access token is expired, attempting to refresh...")
        refreshed_token = cache.try_refresh()
        if refreshed_token:
            ctx.log("Successfully refreshed access token")
            refreshed_identity = cache.get_active_identity()
            if refreshed_identity:
                active_identity = refreshed_identity
                is_expired = False
                expires_in_seconds = int((active_identity.expires_at - now).total_seconds())
        else:
            ctx.output(
                single(
                    item={
                        "authenticated": False,
                        "status": "token_expired",
                        "message": "Authentication token has expired and refresh failed",
                        "account": active_identity.account_username,
                        "expired_at": active_identity.expires_at.isoformat(),
                        "suggestion": "Run 'dxs auth login' to re-authenticate",
                    },
                    semantic_key="authentication",
                )
            )
            return

    def format_expiration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            return f"{seconds // 60} minutes"
        else:
            return f"{seconds // 3600} hours"

    # Check all cached tokens for each resource
    settings = get_settings()
    client = MSALClient()

    resources = {
        "datex_api": {
            "name": "Datex Studio API",
            "scopes": settings.azure_scopes,
        },
        "azure_devops": {
            "name": "Azure DevOps API",
            "scopes": settings.azure_devops_scopes,
        },
    }

    if settings.dynamics_crm_scopes:
        resources["dynamics_crm"] = {
            "name": "Dynamics CRM API",
            "scopes": settings.dynamics_crm_scopes,
        }

    resources["footprint"] = {
        "name": "Footprint API",
        "scopes": [settings.footprint_scope],
    }

    tokens_info = []
    if active_identity.refresh_token:
        for _resource_key, resource_info in resources.items():
            try:
                result = client._app.acquire_token_by_refresh_token(
                    refresh_token=active_identity.refresh_token,
                    scopes=resource_info["scopes"],
                )
                if result and "access_token" in result:
                    expires_in_from_response = result.get("expires_in", 3600)
                    expires_at = now + timedelta(seconds=expires_in_from_response)
                    tokens_info.append(
                        {
                            "resource": resource_info["name"],
                            "has_token": True,
                            "expires_at": expires_at.isoformat(),
                            "expires_in_human": format_expiration(expires_in_from_response),
                        }
                    )
                else:
                    error = result.get("error") if result else "no_token"
                    tokens_info.append(
                        {
                            "resource": resource_info["name"],
                            "has_token": False,
                            "error": error,
                        }
                    )
            except Exception as e:
                tokens_info.append(
                    {
                        "resource": resource_info["name"],
                        "has_token": False,
                        "error": str(e),
                    }
                )

    # List all identities
    all_identities = cache.list_identities()
    other_identities = []
    for username, identity, is_active in all_identities:
        if not is_active:
            other_identities.append(
                {
                    "username": username,
                    "organization": identity.organization_name,
                    "organization_id": identity.organization_id,
                    "status": "expired" if identity.is_expired() else "valid",
                    "expires_at": identity.expires_at.isoformat(),
                }
            )

    status_item: dict[str, Any] = {
        "authenticated": True,
        "status": "authenticated",
        "message": "You are logged in",
        "active_identity": {
            "username": active_identity.account_username,
            "organization": active_identity.organization_name,
            "organization_id": active_identity.organization_id,
            "tenant_id": active_identity.tenant_id,
            "primary_token": {
                "expires_at": active_identity.expires_at.isoformat(),
                "expires_in_seconds": expires_in_seconds,
                "expires_in_human": format_expiration(expires_in_seconds),
            },
        },
        "tokens": tokens_info if tokens_info else None,
    }

    if other_identities:
        status_item["other_identities"] = other_identities

    ctx.output(single(item=status_item, semantic_key="authentication"))


@auth.command("list")
@pass_context
def list_identities(ctx: DxsContext) -> None:
    """List all cached identities.

    Shows all stored authentication identities with their organization
    and token status.

    \b
    Example:
        dxs auth list
    """
    cache = MultiIdentityTokenCache()
    identities = cache.list_identities()

    if not identities:
        ctx.output(
            single(
                item={
                    "message": "No cached identities found",
                    "suggestion": "Run 'dxs auth login' to authenticate",
                },
                semantic_key="identities",
            )
        )
        return

    items = []
    for username, identity, is_active in identities:
        items.append(
            {
                "username": username,
                "organization": identity.organization_name,
                "organization_id": identity.organization_id,
                "tenant_id": identity.tenant_id,
                "active": is_active,
                "status": "expired" if identity.is_expired() else "valid",
                "expires_at": identity.expires_at.isoformat(),
            }
        )

    ctx.output(list_response(items=items, semantic_key="identities"))


@auth.command()
@click.argument("identifier")
@pass_context
def switch(ctx: DxsContext, identifier: str) -> None:
    """Switch to a different identity or organization.

    Auto-detects the identifier type:
    - Email address (contains @): switches by username to a cached identity
    - Organization name: switches to organization, authenticating if needed

    For organizations with external B2C tenant authentication (externalEntraId=true),
    this command will initiate device code flow to authenticate against the
    external tenant if no cached identity exists for that tenant.

    \b
    Examples:
        dxs auth switch user@acme.com    # Switch by username (email)
        dxs auth switch CAG              # Switch by organization name
    """
    if "@" in identifier:
        _switch_by_username(ctx, identifier)
    else:
        _switch_by_organization(ctx, identifier)


def _switch_by_username(ctx: DxsContext, username: str) -> None:
    """Switch to an identity by username (original behavior)."""
    cache = MultiIdentityTokenCache()

    # Check if identity exists
    existing = cache.get_identity(username)
    if not existing:
        # List available identities for suggestion
        available = cache.list_identities()
        available_usernames = [u for u, _, _ in available]

        suggestions = ["Run 'dxs auth list' to see available identities"]
        if available_usernames:
            suggestions.insert(0, f"Available: {', '.join(available_usernames)}")
        suggestions.append("Run 'dxs auth login' to authenticate as a new identity")

        ctx.output_error(
            AuthenticationError(
                message=f"Identity '{username}' not found in cache",
                code="DXS-AUTH-010",
                suggestions=suggestions,
            )
        )
        raise SystemExit(1)

    # Check if token is expired
    if existing.is_expired():
        # Try to refresh
        refreshed = cache.try_refresh_identity(username)
        if not refreshed:
            ctx.output_error(
                AuthenticationError(
                    message=f"Identity '{username}' has expired and refresh failed",
                    code="DXS-AUTH-011",
                    suggestions=[f"Run 'dxs auth login' to re-authenticate as {username}"],
                )
            )
            raise SystemExit(1)

    # Get previous active identity
    previous = cache.get_active_identity()
    previous_username = previous.account_username if previous else None

    # Switch to the new identity
    try:
        new_identity = cache.set_active_identity(username)
    except KeyError:
        ctx.output_error(
            AuthenticationError(
                message=f"Identity '{username}' not found",
                code="DXS-AUTH-010",
            )
        )
        raise SystemExit(1) from None

    ctx.output(
        single(
            item={
                "status": "switched",
                "message": f"Switched to {username}",
                "previous_identity": previous_username,
                "active_identity": username,
                "organization": new_identity.organization_name,
                "organization_id": new_identity.organization_id,
            },
            semantic_key="authentication",
        )
    )


def _switch_by_organization(ctx: DxsContext, org_name: str) -> None:
    """Switch to an organization, authenticating against external tenant if needed."""

    cache = MultiIdentityTokenCache()

    # Step 1: Check if we have a cached identity for this org
    existing_by_org = cache.get_identity_by_org_name(org_name)
    if existing_by_org:
        # We have an identity for this org - switch to it
        _activate_existing_identity(ctx, cache, existing_by_org, org_name)
        return

    # Step 2: Fetch organization details from API
    org_info = _fetch_organization_by_name(ctx, org_name)
    if not org_info:
        ctx.output_error(
            AuthenticationError(
                message=f"Organization '{org_name}' not found",
                code="DXS-AUTH-013",
                suggestions=[
                    "Check the organization name spelling",
                    "Run 'dxs org list' to see available organizations",
                    "You may not have access to this organization",
                ],
            )
        )
        raise SystemExit(1)

    # Step 3: Check if external authentication is required
    if not org_info.external_entra_id:
        # No external auth needed - provide informative message
        ctx.output(
            single(
                item={
                    "status": "no_action_required",
                    "message": f"Organization '{org_name}' does not require external authentication",
                    "organization": org_info.name,
                    "organization_id": org_info.id,
                    "suggestion": "Your current identity should work with this organization",
                },
                semantic_key="authentication",
            )
        )
        return

    # Step 4: External auth required - check if we have identity for that tenant
    if org_info.tenant_id:
        existing_by_tenant = cache.get_identity_by_tenant(org_info.tenant_id)
        if existing_by_tenant and existing_by_tenant.account_username:
            # Update org info and activate
            cache.update_identity_org_info(
                existing_by_tenant.account_username,
                org_info.id,
                org_info.name,
            )
            _activate_existing_identity(ctx, cache, existing_by_tenant, org_name)
            return

    # Step 5: Need to authenticate against external tenant
    if not org_info.tenant_id:
        ctx.output_error(
            AuthenticationError(
                message=f"Organization '{org_name}' requires external authentication but has no tenant ID configured",
                code="DXS-AUTH-012",
                suggestions=["Contact your organization administrator to configure the tenant ID"],
            )
        )
        raise SystemExit(1)

    _authenticate_external_tenant(ctx, cache, org_info)


def _activate_existing_identity(
    ctx: DxsContext,
    cache: MultiIdentityTokenCache,
    identity: Any,
    org_name: str,
) -> None:
    """Activate an existing cached identity."""
    # Check if token is expired
    if identity.is_expired():
        refreshed = cache.try_refresh_identity(identity.account_username)
        if not refreshed:
            ctx.output_error(
                AuthenticationError(
                    message=f"Identity for '{org_name}' has expired and refresh failed",
                    code="DXS-AUTH-011",
                    suggestions=[f"Run 'dxs auth switch {org_name}' again to re-authenticate"],
                )
            )
            raise SystemExit(1)

    previous = cache.get_active_identity()
    previous_username = previous.account_username if previous else None

    cache.set_active_identity(identity.account_username)

    ctx.output(
        single(
            item={
                "status": "switched",
                "message": f"Switched to organization {org_name}",
                "previous_identity": previous_username,
                "active_identity": identity.account_username,
                "organization": identity.organization_name,
                "organization_id": identity.organization_id,
                "external_tenant": identity.external_entra_id,
            },
            semantic_key="authentication",
        )
    )


def _fetch_organization_by_name(ctx: DxsContext, org_name: str) -> Any:
    """Fetch organization details by name from API."""
    from dxs.core.api.client import ApiClient
    from dxs.core.api.endpoints import OrganizationEndpoints
    from dxs.core.api.models import OrganizationOutput

    try:
        client = ApiClient()
        response = client.get(OrganizationEndpoints.list())

        if not response or not isinstance(response, list):
            return None

        # Case-insensitive match
        org_name_lower = org_name.lower()
        for org_data in response:
            if org_data.get("name", "").lower() == org_name_lower:
                return OrganizationOutput.from_api(org_data)

        return None

    except Exception as e:
        ctx.log(f"Failed to fetch organizations: {e}")
        return None


def _authenticate_external_tenant(
    ctx: DxsContext,
    cache: MultiIdentityTokenCache,
    org_info: Any,
) -> None:
    """Authenticate against an organization's external tenant."""
    from dxs.utils.config import get_settings

    settings = get_settings()

    # Create MSAL client for the external tenant
    try:
        client = MSALClient.for_tenant(
            tenant_id=org_info.tenant_id,
            scopes=settings.azure_scopes,
        )
    except AuthenticationError as e:
        ctx.output_error(e)
        raise SystemExit(1) from None

    def on_device_code(device_code: dict[str, Any]) -> None:
        """Callback to display device code to user."""
        ctx.output(
            single(
                item={
                    "status": "awaiting_authentication",
                    "action_required": {
                        "type": "device_code",
                        "instructions": f"Authenticate with {org_info.name}'s external tenant",
                        "url": device_code["verification_uri"],
                        "code": device_code["user_code"],
                        "expires_in_seconds": device_code["expires_in"],
                        "tenant": org_info.tenant_id,
                        "domain": org_info.external_entra_id_domain_name,
                    },
                    "message": device_code.get("message", ""),
                },
                semantic_key="authentication",
            ),
            include_metadata=False,
        )

    try:
        ctx.log(f"Initiating device code authentication for {org_info.name}...")

        result = client.authenticate_device_code(on_device_code=on_device_code)

        # Save identity with org info and external tenant flag
        saved_identity = cache.save_identity(
            result,
            organization_id=org_info.id,
            organization_name=org_info.name,
            tenant_id=org_info.tenant_id,
            external_entra_id=True,
            external_entra_id_domain_name=org_info.external_entra_id_domain_name,
        )

        # Output success
        ctx.output(
            single(
                item={
                    "status": "authenticated",
                    "message": f"Successfully authenticated with {org_info.name}",
                    "account": saved_identity.account_username,
                    "organization": saved_identity.organization_name,
                    "organization_id": saved_identity.organization_id,
                    "external_tenant": True,
                    "tenant_id": org_info.tenant_id,
                    "expires_at": saved_identity.expires_at.isoformat(),
                },
                semantic_key="authentication",
            )
        )

    except AuthenticationError as e:
        ctx.output_error(e)
        raise SystemExit(1) from None


def _fetch_organization_info(ctx: DxsContext) -> dict[str, Any] | None:
    """Fetch organization info from the API for the current identity.

    Returns:
        Dict with 'id' and 'name' keys, or None if failed.
    """
    try:
        from dxs.core.api.client import ApiClient
        from dxs.core.api.endpoints import OrganizationEndpoints

        client = ApiClient()
        response = client.get(OrganizationEndpoints.mine())
        if response and isinstance(response, dict):
            return {
                "id": response.get("id"),
                "name": response.get("name"),
            }
    except Exception as e:
        ctx.log(f"Failed to fetch organization info: {e}")

    return None
