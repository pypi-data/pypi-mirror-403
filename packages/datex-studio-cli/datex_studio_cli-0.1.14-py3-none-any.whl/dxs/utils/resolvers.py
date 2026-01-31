"""Name-to-ID resolution utilities for organizations, repositories, and users."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dxs.utils.errors import NotFoundError, ValidationError

if TYPE_CHECKING:
    from dxs.core.api import ApiClient


class EntityResolver:
    """Resolves entity names to IDs with caching.

    This class provides methods to resolve human-readable names (like organization
    names, repository names, or user emails) to their numeric IDs. Results are
    cached to minimize API calls when resolving multiple entities.

    Example:
        resolver = EntityResolver()
        org_id = resolver.resolve_org("Datex")  # Returns numeric ID
        repo_id = resolver.resolve_repo("FootprintManager", org_id=org_id)
        user_id = resolver.resolve_user_email("user@example.com")
    """

    def __init__(self, client: ApiClient | None = None):
        """Initialize the resolver.

        Args:
            client: Optional API client. If not provided, a new one will be created.
        """
        # Lazy import to avoid circular dependencies
        if client is None:
            from dxs.core.api import ApiClient

            client = ApiClient()

        self._client = client
        self._org_cache: dict[str, int] | None = None
        self._user_cache: dict[str, int] | None = None

    def resolve_org(self, name_or_id: str | int) -> int:
        """Resolve organization name to ID.

        Accepts either a numeric ID or organization name. If a numeric ID is
        provided (as int or numeric string), it is returned directly. Otherwise,
        the organization name is looked up (case-insensitive).

        Args:
            name_or_id: Organization name (string) or ID (int or numeric string)

        Returns:
            Organization ID as integer

        Raises:
            NotFoundError: If organization not found
            ValidationError: If multiple organizations match (ambiguous)
        """
        # If already int, return it
        if isinstance(name_or_id, int):
            return name_or_id

        # If string that looks like int, return int
        if name_or_id.isdigit():
            return int(name_or_id)

        # Search orgs by name (case-insensitive)
        if self._org_cache is None:
            self._build_org_cache()
        assert self._org_cache is not None  # Guaranteed after _build_org_cache()

        name_lower = name_or_id.lower()
        matches = [
            (name, id_) for name, id_ in self._org_cache.items() if name_lower == name.lower()
        ]

        # If no exact match, try substring match
        if not matches:
            matches = [
                (name, id_) for name, id_ in self._org_cache.items() if name_lower in name.lower()
            ]

        if not matches:
            raise NotFoundError(
                resource_type="Organization",
                resource_id=name_or_id,
                suggestions=[
                    "Use 'dxs org list' to see available organizations",
                    "Use 'dxs org search <name>' to search by name",
                ],
            )

        if len(matches) > 1:
            match_list = ", ".join(f"{name} (ID: {id_})" for name, id_ in matches[:5])
            raise ValidationError(
                message=f"Ambiguous organization name '{name_or_id}' matches: {match_list}",
                suggestions=[
                    "Use the numeric ID instead",
                    "Use a more specific name",
                ],
            )

        return matches[0][1]

    def resolve_repo(self, name_or_id: str | int, org_id: int | None = None) -> int:
        """Resolve repository name to ID.

        Accepts either a numeric ID or repository name. If a numeric ID is
        provided (as int or numeric string), it is returned directly. Otherwise,
        the repository name is looked up (case-insensitive), optionally scoped
        to a specific organization.

        Args:
            name_or_id: Repository name (string) or ID (int or numeric string)
            org_id: Optional organization ID to narrow search scope

        Returns:
            Repository ID as integer

        Raises:
            NotFoundError: If repository not found
            ValidationError: If multiple repositories match (ambiguous)
        """
        # If already int, return it
        if isinstance(name_or_id, int):
            return name_or_id

        # If string that looks like int, return int
        if name_or_id.isdigit():
            return int(name_or_id)

        # Fetch repos, optionally filtered by org
        from dxs.core.api import RepoEndpoints

        repos = self._client.get(RepoEndpoints.list(org_id))
        if not isinstance(repos, list):
            repos = [repos] if repos else []

        name_lower = name_or_id.lower()

        # First try exact match
        matches = [r for r in repos if r.get("name", "").lower() == name_lower]

        # If no exact match, try substring match
        if not matches:
            matches = [r for r in repos if name_lower in r.get("name", "").lower()]

        if not matches:
            raise NotFoundError(
                resource_type="Repository",
                resource_id=name_or_id,
                suggestions=[
                    "Use 'dxs source repo list' to see available repositories",
                    "Use 'dxs source repo search <name>' to search by name",
                    "Try scoping search with --org flag",
                ],
            )

        if len(matches) > 1:
            match_list = ", ".join(f"{r['name']} (ID: {r['id']})" for r in matches[:5])
            raise ValidationError(
                message=f"Ambiguous repository name '{name_or_id}' matches: {match_list}",
                suggestions=[
                    "Use the numeric ID instead",
                    "Use a more specific name",
                    "Scope search with --org to reduce matches",
                ],
            )

        return int(matches[0]["id"])

    def resolve_connection(self, name_or_id: str | int, org_id: int | None = None) -> int:
        """Resolve API connection name to ID.

        Accepts either a numeric ID or connection name. If a numeric ID is
        provided (as int or numeric string), it is returned directly. Otherwise,
        the connection name is looked up (case-insensitive), optionally scoped
        to a specific organization.

        Args:
            name_or_id: Connection name (string) or ID (int or numeric string)
            org_id: Optional organization ID to narrow search scope

        Returns:
            Connection ID as integer

        Raises:
            NotFoundError: If connection not found
            ValidationError: If multiple connections match (ambiguous)
        """
        if isinstance(name_or_id, int):
            return name_or_id

        if name_or_id.isdigit():
            return int(name_or_id)

        from dxs.core.api.endpoints import ApiConnectionEndpoints

        connections = self._client.get(ApiConnectionEndpoints.list(org_id=org_id))
        if not isinstance(connections, list):
            connections = [connections] if connections else []

        name_lower = name_or_id.lower()

        # First try exact match
        matches = [c for c in connections if c.get("name", "").lower() == name_lower]

        # If no exact match, try substring match
        if not matches:
            matches = [c for c in connections if name_lower in c.get("name", "").lower()]

        if not matches:
            raise NotFoundError(
                resource_type="API Connection",
                resource_id=name_or_id,
                suggestions=[
                    "Use 'dxs organization connection list' to see available connections",
                    "Try scoping search with --org flag",
                ],
            )

        if len(matches) > 1:
            match_list = ", ".join(f"{c['name']} (ID: {c['id']})" for c in matches[:5])
            raise ValidationError(
                message=f"Ambiguous connection name '{name_or_id}' matches: {match_list}",
                suggestions=[
                    "Use --connection-id with the numeric ID instead",
                    "Use a more specific name",
                ],
            )

        return int(matches[0]["id"])

    def resolve_user_email(self, email: str) -> int | None:
        """Resolve user email to userId.

        Looks up users by email address (case-insensitive).

        Args:
            email: User's email address

        Returns:
            User ID as integer, or None if not found
        """
        if self._user_cache is None:
            self._build_user_cache()
        assert self._user_cache is not None  # Guaranteed after _build_user_cache()

        return self._user_cache.get(email.lower())

    def _build_org_cache(self) -> None:
        """Build organization name-to-ID cache."""
        from dxs.core.api import OrganizationEndpoints

        orgs = self._client.get(OrganizationEndpoints.list())
        if not isinstance(orgs, list):
            orgs = [orgs] if orgs else []
        self._org_cache = {org["name"]: org["id"] for org in orgs if "name" in org}

    def _build_user_cache(self) -> None:
        """Build user email-to-ID cache."""
        from dxs.core.api import UserEndpoints

        users = self._client.get(UserEndpoints.list())
        if not isinstance(users, list):
            users = [users] if users else []
        # API returns userPrincipalName instead of email
        self._user_cache = {
            u["userPrincipalName"].lower(): u["id"]
            for u in users
            if "userPrincipalName" in u and "id" in u
        }
