"""Token persistence to ~/.datex/credentials.yaml.

Supports multi-identity storage (v2 format) with automatic migration from v1.
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from dxs.utils.paths import get_credentials_path

# Current credentials file format version
CREDENTIALS_VERSION = 2


class CachedToken(BaseModel):
    """Persisted token data (v1 format, kept for backwards compatibility)."""

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: list[str] = Field(default_factory=list)
    account_id: str | None = None
    account_username: str | None = None


class CachedIdentity(BaseModel):
    """Persisted identity data with organization info (v2 format)."""

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime
    scope: list[str] = Field(default_factory=list)
    account_id: str | None = None
    account_username: str | None = None
    # Organization info (populated after first API call)
    organization_id: int | None = None
    organization_name: str | None = None
    tenant_id: str | None = None
    # External tenant authentication info
    external_entra_id: bool = False
    external_entra_id_domain_name: str | None = None

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if the token is expired (with optional buffer).

        Args:
            buffer_seconds: Consider expired if within this many seconds of expiration.

        Returns:
            True if expired or about to expire.
        """
        now = datetime.now(timezone.utc)
        return self.expires_at.timestamp() <= now.timestamp() + buffer_seconds

    def to_cached_token(self) -> CachedToken:
        """Convert to CachedToken for backwards compatibility."""
        return CachedToken(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            id_token=self.id_token,
            token_type=self.token_type,
            expires_at=self.expires_at,
            scope=self.scope,
            account_id=self.account_id,
            account_username=self.account_username,
        )


class CachedResourceToken(BaseModel):
    """Cached access token for a specific resource/scope."""

    access_token: str
    expires_at: datetime

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if the token is expired (with buffer)."""
        now = datetime.now(timezone.utc)
        return self.expires_at.timestamp() <= now.timestamp() + buffer_seconds


class CredentialsFile(BaseModel):
    """Root model for credentials.yaml (v2 format)."""

    version: int = CREDENTIALS_VERSION
    active_identity: str | None = None
    identities: dict[str, CachedIdentity] = Field(default_factory=dict)
    resource_tokens: dict[str, CachedResourceToken] = Field(default_factory=dict)


class TokenCache:
    """Manages token persistence to disk.

    Tokens are stored in ~/.datex/credentials.yaml with secure permissions
    (owner read/write only).
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the token cache.

        Args:
            path: Custom path for credentials file. Defaults to ~/.datex/credentials.yaml.
        """
        self._path = path or get_credentials_path()

    def save_token(self, token_response: dict[str, Any]) -> CachedToken:
        """Save a token response to disk.

        Args:
            token_response: Token response from MSAL.

        Returns:
            The cached token object.
        """
        # Calculate expiration time
        expires_in = token_response.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in

        # Extract account info if available
        account_id = None
        account_username = None
        if "id_token_claims" in token_response:
            claims = token_response["id_token_claims"]
            account_id = claims.get("oid") or claims.get("sub")
            account_username = claims.get("preferred_username") or claims.get("email")

        # Parse scope
        scope_str = token_response.get("scope", "")
        if isinstance(scope_str, str):
            scope = scope_str.split() if scope_str else []
        else:
            scope = scope_str or []

        cached = CachedToken(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            id_token=token_response.get("id_token"),
            token_type=token_response.get("token_type", "Bearer"),
            expires_at=datetime.fromtimestamp(expires_at, timezone.utc),
            scope=scope,
            account_id=account_id,
            account_username=account_username,
        )

        self._write_cache(cached)
        return cached

    def get_token(self) -> CachedToken | None:
        """Get the cached token.

        Returns:
            Cached token if exists, None otherwise.
        """
        return self._read_cache()

    def get_valid_token(self) -> str | None:
        """Get the access token if it exists and is not expired.

        Returns:
            Access token string if valid, None otherwise.
        """
        cached = self._read_cache()
        if cached is None:
            return None

        # Check if expired (with 5-minute buffer)
        now = datetime.now(timezone.utc)
        buffer_seconds = 300  # 5 minutes
        if cached.expires_at.timestamp() <= now.timestamp() + buffer_seconds:
            return None  # Token is expired or about to expire

        return cached.access_token

    def is_expired(self) -> bool:
        """Check if the cached token is expired.

        Returns:
            True if expired or no token cached.
        """
        cached = self._read_cache()
        if cached is None:
            return True

        now = datetime.now(timezone.utc)
        buffer_seconds = 300  # 5 minutes
        return cached.expires_at.timestamp() <= now.timestamp() + buffer_seconds

    def get_expiration(self) -> datetime | None:
        """Get the token expiration time.

        Returns:
            Expiration datetime or None if no token cached.
        """
        cached = self._read_cache()
        return cached.expires_at if cached else None

    def get_account_info(self) -> dict[str, str | None] | None:
        """Get cached account information.

        Returns:
            Dict with account_id and account_username, or None.
        """
        cached = self._read_cache()
        if cached is None:
            return None

        return {
            "account_id": cached.account_id,
            "account_username": cached.account_username,
        }

    def clear(self) -> bool:
        """Remove cached credentials.

        Returns:
            True if credentials were removed, False if none existed.
        """
        if self._path.exists():
            self._path.unlink()
            return True
        return False

    def try_refresh(self) -> str | None:
        """Attempt to refresh the token using stored refresh token.

        Returns:
            New access token if refresh succeeded, None otherwise.
        """
        cached = self._read_cache()
        if cached is None or not cached.refresh_token:
            return None

        try:
            # Import here to avoid circular imports
            from dxs.core.auth.msal_client import MSALClient

            client = MSALClient()
            result = client.refresh_access_token(cached.refresh_token)
            if result:
                new_cached = self.save_token(result)
                return new_cached.access_token
        except Exception:
            pass

        return None

    def _write_cache(self, cached: CachedToken) -> None:
        """Write the cache to disk with atomic write for security.

        Uses a temporary file with secure permissions, then atomically
        renames to the final path. This prevents a race condition where
        credentials could be briefly exposed with default permissions.
        """
        # Ensure parent directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        data = cached.model_dump(mode="json")

        # Convert datetime to ISO string
        if isinstance(data.get("expires_at"), str):
            pass  # Already a string from mode="json"
        elif data.get("expires_at"):
            data["expires_at"] = data["expires_at"].isoformat()

        # Write atomically: temp file with secure permissions, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=".credentials_",
            suffix=".tmp",
        )
        try:
            # Set secure permissions BEFORE writing sensitive content
            os.chmod(temp_path, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(yaml.safe_dump(data, default_flow_style=False))
            # Atomic rename to final path
            os.replace(temp_path, self._path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _read_cache(self) -> CachedToken | None:
        """Read the cache from disk."""
        if not self._path.exists():
            return None

        try:
            data = yaml.safe_load(self._path.read_text())
            if not data:
                return None

            # Parse datetime string back to datetime
            if isinstance(data.get("expires_at"), str):
                data["expires_at"] = datetime.fromisoformat(data["expires_at"])

            return CachedToken.model_validate(data)
        except (yaml.YAMLError, ValueError, KeyError):
            return None


class MultiIdentityTokenCache:
    """Manages multi-identity token persistence to disk.

    Supports multiple Azure AD identities with automatic migration from v1 format.
    Tokens are stored in ~/.datex/credentials.yaml with secure permissions.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the multi-identity token cache.

        Args:
            path: Custom path for credentials file. Defaults to ~/.datex/credentials.yaml.
        """
        self._path = path or get_credentials_path()

    def save_identity(
        self,
        token_response: dict[str, Any],
        organization_id: int | None = None,
        organization_name: str | None = None,
        tenant_id: str | None = None,
        external_entra_id: bool = False,
        external_entra_id_domain_name: str | None = None,
        set_active: bool = True,
    ) -> CachedIdentity:
        """Save a token response as an identity.

        Args:
            token_response: Token response from MSAL.
            organization_id: Organization ID from API.
            organization_name: Organization name from API.
            tenant_id: Azure AD tenant ID.
            external_entra_id: Whether this identity uses external B2C tenant.
            external_entra_id_domain_name: Domain name for external B2C tenant.
            set_active: Whether to set this as the active identity.

        Returns:
            The cached identity object.
        """
        # Calculate expiration time
        expires_in = token_response.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in

        # Extract account info if available
        account_id = None
        account_username = None
        extracted_tenant_id = tenant_id
        if "id_token_claims" in token_response:
            claims = token_response["id_token_claims"]
            account_id = claims.get("oid") or claims.get("sub")
            account_username = claims.get("preferred_username") or claims.get("email")
            if not extracted_tenant_id:
                extracted_tenant_id = claims.get("tid")

        # Parse scope
        scope_str = token_response.get("scope", "")
        if isinstance(scope_str, str):
            scope = scope_str.split() if scope_str else []
        else:
            scope = scope_str or []

        identity = CachedIdentity(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            id_token=token_response.get("id_token"),
            token_type=token_response.get("token_type", "Bearer"),
            expires_at=datetime.fromtimestamp(expires_at, timezone.utc),
            scope=scope,
            account_id=account_id,
            account_username=account_username,
            organization_id=organization_id,
            organization_name=organization_name,
            tenant_id=extracted_tenant_id,
            external_entra_id=external_entra_id,
            external_entra_id_domain_name=external_entra_id_domain_name,
        )

        # Load existing credentials file
        creds = self._read_credentials()

        # Use username as key (or account_id as fallback)
        identity_key = account_username or account_id or "unknown"

        # Update or add identity
        creds.identities[identity_key] = identity

        # Set as active if requested
        if set_active:
            creds.active_identity = identity_key

        self._write_credentials(creds)
        return identity

    def get_active_identity(self) -> CachedIdentity | None:
        """Get the currently active identity.

        Returns:
            Active identity if exists, None otherwise.
        """
        creds = self._read_credentials()
        if not creds.active_identity or creds.active_identity not in creds.identities:
            return None
        return creds.identities[creds.active_identity]

    def get_identity(self, username: str) -> CachedIdentity | None:
        """Get an identity by username.

        Args:
            username: The account username (email).

        Returns:
            Identity if found, None otherwise.
        """
        creds = self._read_credentials()
        return creds.identities.get(username)

    def get_identity_by_tenant(self, tenant_id: str) -> CachedIdentity | None:
        """Get an identity by Azure AD tenant ID.

        Useful for finding if we have a cached identity for an external tenant.

        Args:
            tenant_id: The Azure AD tenant ID.

        Returns:
            Identity if found for this tenant, None otherwise.
        """
        creds = self._read_credentials()
        for identity in creds.identities.values():
            if identity.tenant_id == tenant_id:
                return identity
        return None

    def get_identity_by_org_name(self, org_name: str) -> CachedIdentity | None:
        """Get an identity by organization name (case-insensitive).

        Args:
            org_name: The organization name.

        Returns:
            Identity if found for this organization, None otherwise.
        """
        creds = self._read_credentials()
        org_name_lower = org_name.lower()
        for identity in creds.identities.values():
            if identity.organization_name and identity.organization_name.lower() == org_name_lower:
                return identity
        return None

    def set_active_identity(self, username: str) -> CachedIdentity:
        """Set the active identity by username.

        Args:
            username: The account username (email) to set as active.

        Returns:
            The newly active identity.

        Raises:
            KeyError: If the identity is not found.
        """
        creds = self._read_credentials()
        if username not in creds.identities:
            raise KeyError(f"Identity '{username}' not found in cache")

        creds.active_identity = username
        self._write_credentials(creds)
        return creds.identities[username]

    def list_identities(self) -> list[tuple[str, CachedIdentity, bool]]:
        """List all cached identities.

        Returns:
            List of tuples: (username, identity, is_active).
        """
        creds = self._read_credentials()
        result = []
        for username, identity in creds.identities.items():
            is_active = username == creds.active_identity
            result.append((username, identity, is_active))
        return result

    def remove_identity(self, username: str) -> bool:
        """Remove an identity from the cache.

        Args:
            username: The account username (email) to remove.

        Returns:
            True if removed, False if not found.
        """
        creds = self._read_credentials()
        if username not in creds.identities:
            return False

        del creds.identities[username]

        # If we removed the active identity, clear it or set to another
        if creds.active_identity == username:
            if creds.identities:
                # Set to first remaining identity
                creds.active_identity = next(iter(creds.identities.keys()))
            else:
                creds.active_identity = None

        self._write_credentials(creds)
        return True

    def clear_all(self) -> int:
        """Remove all cached identities.

        Returns:
            Number of identities that were removed.
        """
        creds = self._read_credentials()
        count = len(creds.identities)

        if self._path.exists():
            self._path.unlink()

        return count

    def update_identity_org_info(
        self,
        username: str,
        organization_id: int,
        organization_name: str,
    ) -> CachedIdentity | None:
        """Update organization info for an identity.

        Args:
            username: The account username (email).
            organization_id: Organization ID from API.
            organization_name: Organization name from API.

        Returns:
            Updated identity or None if not found.
        """
        creds = self._read_credentials()
        if username not in creds.identities:
            return None

        identity = creds.identities[username]
        identity.organization_id = organization_id
        identity.organization_name = organization_name
        self._write_credentials(creds)
        return identity

    def try_refresh_identity(self, username: str | None = None) -> str | None:
        """Attempt to refresh a token using stored refresh token.

        Args:
            username: Identity to refresh. If None, refreshes active identity.

        Returns:
            New access token if refresh succeeded, None otherwise.
        """
        creds = self._read_credentials()

        # Determine which identity to refresh
        target_username = username or creds.active_identity
        if not target_username or target_username not in creds.identities:
            return None

        identity = creds.identities[target_username]
        if not identity.refresh_token:
            return None

        try:
            # Import here to avoid circular imports
            from dxs.core.auth.msal_client import MSALClient

            client = MSALClient()
            result = client.refresh_access_token(identity.refresh_token)
            if result:
                # Preserve org info when refreshing
                new_identity = self.save_identity(
                    result,
                    organization_id=identity.organization_id,
                    organization_name=identity.organization_name,
                    tenant_id=identity.tenant_id,
                    set_active=(target_username == creds.active_identity),
                )
                return new_identity.access_token
        except Exception:
            pass

        return None

    def get_resource_token(self, scope_key: str) -> str | None:
        """Get a cached resource token if valid.

        Args:
            scope_key: Cache key (e.g., comma-separated sorted scopes).

        Returns:
            Access token string if valid, None otherwise.
        """
        creds = self._read_credentials()
        cached = creds.resource_tokens.get(scope_key)
        if cached and not cached.is_expired():
            return cached.access_token
        return None

    def save_resource_token(self, scope_key: str, access_token: str, expires_in: int = 3600) -> None:
        """Cache a resource token to disk.

        Args:
            scope_key: Cache key (e.g., comma-separated sorted scopes).
            access_token: The access token to cache.
            expires_in: Token lifetime in seconds (default 3600).
        """
        creds = self._read_credentials()
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in
        creds.resource_tokens[scope_key] = CachedResourceToken(
            access_token=access_token,
            expires_at=datetime.fromtimestamp(expires_at, timezone.utc),
        )
        self._write_credentials(creds)

    def get_valid_token(self) -> str | None:
        """Get the access token for active identity if valid.

        Returns:
            Access token string if valid, None otherwise.
        """
        identity = self.get_active_identity()
        if identity is None:
            return None

        if identity.is_expired():
            return None

        return identity.access_token

    def is_expired(self) -> bool:
        """Check if the active identity's token is expired.

        Returns:
            True if expired or no identity active.
        """
        identity = self.get_active_identity()
        if identity is None:
            return True
        return identity.is_expired()

    # Backwards-compatible methods for TokenCache interface

    def get_token(self) -> CachedToken | None:
        """Get the active identity as a CachedToken (backwards compat).

        Returns:
            CachedToken if active identity exists, None otherwise.
        """
        identity = self.get_active_identity()
        return identity.to_cached_token() if identity else None

    def save_token(self, token_response: dict[str, Any]) -> CachedToken:
        """Save a token response (backwards compat).

        Args:
            token_response: Token response from MSAL.

        Returns:
            The cached token object.
        """
        identity = self.save_identity(token_response)
        return identity.to_cached_token()

    def clear(self) -> bool:
        """Remove active identity (backwards compat).

        Returns:
            True if identity was removed, False if none existed.
        """
        creds = self._read_credentials()
        if not creds.active_identity:
            return False
        return self.remove_identity(creds.active_identity)

    def get_account_info(self) -> dict[str, Any] | None:
        """Get active identity account info (backwards compat).

        Returns:
            Dict with account_id, account_username, and org info, or None.
        """
        identity = self.get_active_identity()
        if identity is None:
            return None

        return {
            "account_id": identity.account_id,
            "account_username": identity.account_username,
            "organization_id": identity.organization_id,
            "organization_name": identity.organization_name,
            "tenant_id": identity.tenant_id,
        }

    def try_refresh(self) -> str | None:
        """Attempt to refresh active identity token (backwards compat).

        Returns:
            New access token if refresh succeeded, None otherwise.
        """
        return self.try_refresh_identity()

    def get_expiration(self) -> datetime | None:
        """Get active identity token expiration (backwards compat).

        Returns:
            Expiration datetime or None if no active identity.
        """
        identity = self.get_active_identity()
        return identity.expires_at if identity else None

    def _read_credentials(self) -> CredentialsFile:
        """Read credentials from disk, auto-migrating v1 format."""
        if not self._path.exists():
            return CredentialsFile()

        try:
            data = yaml.safe_load(self._path.read_text())
            if not data:
                return CredentialsFile()

            # Check for v2 format
            if data.get("version") == CREDENTIALS_VERSION:
                return self._parse_v2_credentials(data)

            # Check for v1 format (no version field, has access_token at root)
            if "access_token" in data and "version" not in data:
                return self._migrate_v1_to_v2(data)

            # Unknown format, start fresh
            return CredentialsFile()

        except (yaml.YAMLError, ValueError, KeyError):
            return CredentialsFile()

    def _parse_v2_credentials(self, data: dict[str, Any]) -> CredentialsFile:
        """Parse v2 format credentials file."""
        identities = {}
        for username, identity_data in data.get("identities", {}).items():
            # Parse datetime string back to datetime
            if isinstance(identity_data.get("expires_at"), str):
                identity_data["expires_at"] = datetime.fromisoformat(identity_data["expires_at"])
            identities[username] = CachedIdentity.model_validate(identity_data)

        resource_tokens = {}
        for scope_key, token_data in data.get("resource_tokens", {}).items():
            if isinstance(token_data.get("expires_at"), str):
                token_data["expires_at"] = datetime.fromisoformat(token_data["expires_at"])
            resource_tokens[scope_key] = CachedResourceToken.model_validate(token_data)

        return CredentialsFile(
            version=data.get("version", CREDENTIALS_VERSION),
            active_identity=data.get("active_identity"),
            identities=identities,
            resource_tokens=resource_tokens,
        )

    def _migrate_v1_to_v2(self, data: dict[str, Any]) -> CredentialsFile:
        """Migrate v1 format to v2 format."""
        # Parse datetime string back to datetime
        if isinstance(data.get("expires_at"), str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])

        # Create identity from v1 token
        identity = CachedIdentity(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=data["expires_at"],
            scope=data.get("scope", []),
            account_id=data.get("account_id"),
            account_username=data.get("account_username"),
            # Org info not available in v1, will be populated on next API call
            organization_id=None,
            organization_name=None,
            tenant_id=None,
        )

        # Use username as key
        username = identity.account_username or identity.account_id or "migrated"

        creds = CredentialsFile(
            version=CREDENTIALS_VERSION,
            active_identity=username,
            identities={username: identity},
        )

        # Write migrated credentials back to disk
        self._write_credentials(creds)

        return creds

    def _write_credentials(self, creds: CredentialsFile) -> None:
        """Write credentials to disk with atomic write for security."""
        # Ensure parent directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        data: dict[str, Any] = {
            "version": creds.version,
            "active_identity": creds.active_identity,
            "identities": {},
        }

        for username, identity in creds.identities.items():
            identity_data = identity.model_dump(mode="json")
            # Ensure datetime is ISO string
            if isinstance(identity_data.get("expires_at"), str):
                pass  # Already a string from mode="json"
            elif identity_data.get("expires_at"):
                identity_data["expires_at"] = identity_data["expires_at"].isoformat()
            data["identities"][username] = identity_data

        if creds.resource_tokens:
            data["resource_tokens"] = {}
            for scope_key, rt in creds.resource_tokens.items():
                rt_data = rt.model_dump(mode="json")
                data["resource_tokens"][scope_key] = rt_data

        # Write atomically: temp file with secure permissions, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=".credentials_",
            suffix=".tmp",
        )
        try:
            # Set secure permissions BEFORE writing sensitive content
            os.chmod(temp_path, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(yaml.safe_dump(data, default_flow_style=False))
            # Atomic rename to final path
            os.replace(temp_path, self._path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
