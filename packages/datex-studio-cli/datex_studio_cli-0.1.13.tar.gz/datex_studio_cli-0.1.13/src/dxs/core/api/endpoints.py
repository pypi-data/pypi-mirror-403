"""API endpoint path definitions for Datex Studio API.

Note: Paths are relative to the base URL (e.g., https://wavelength.host/api).
Do not include /api prefix as it's part of the base URL.
"""


class SourceControlEndpoints:
    """Source control API endpoints.

    Base: /sourcecontrol (relative to api_base_url)
    """

    @staticmethod
    def locks(repo_id: int) -> str:
        """Get all locks for a repository."""
        return f"/sourcecontrol/{repo_id}/locks"

    @staticmethod
    def history(repo_id: int) -> str:
        """Get commit history for a repository."""
        return f"/sourcecontrol/{repo_id}/history"

    @staticmethod
    def branch_history(branch_id: int) -> str:
        """Get commit history for a specific branch."""
        return f"/sourcecontrol/application/{branch_id}/history"

    @staticmethod
    def configuration_history(branch_id: int, reference_name: str) -> str:
        """Get version history for a specific configuration."""
        return f"/sourcecontrol/{branch_id}/configuration/{reference_name}/history"

    @staticmethod
    def upstream_changes(branch_id: int) -> str:
        """Get upstream (base branch) changes."""
        return f"/sourcecontrol/{branch_id}/upstreamChanges"

    @staticmethod
    def feature_branch_changes(branch_id: int) -> str:
        """Get feature branch changes compared to base."""
        return f"/sourcecontrol/{branch_id}/featureBranchChanges"

    @staticmethod
    def history_branch_changes(branch_id: int) -> str:
        """Get branch changes with commit details."""
        return f"/sourcecontrol/{branch_id}/historyBranchChanges"

    @staticmethod
    def replacements_history(branch_id: int) -> str:
        """Get history of configuration replacement changes."""
        return f"/sourcecontrol/{branch_id}/replacements/history"

    @staticmethod
    def settings_and_references_history(branch_id: int) -> str:
        """Get history of settings and references changes."""
        return f"/sourcecontrol/{branch_id}/settings-and-references/history"

    @staticmethod
    def operations_and_roles_history(branch_id: int) -> str:
        """Get history of operations and roles changes."""
        return f"/sourcecontrol/{branch_id}/operations-and-roles/history"

    # Lock operations (for future use)
    @staticmethod
    def lock_config(branch_id: int, reference_name: str) -> str:
        """Lock a specific configuration."""
        return f"/sourcecontrol/{branch_id}/config/{reference_name}/lock"

    @staticmethod
    def unlock_config(branch_id: int, reference_name: str) -> str:
        """Unlock a specific configuration."""
        return f"/sourcecontrol/{branch_id}/config/{reference_name}/unlock"

    @staticmethod
    def commit(branch_id: int) -> str:
        """Commit changes."""
        return f"/sourcecontrol/{branch_id}/commit"

    @staticmethod
    def pull(branch_id: int) -> str:
        """Pull changes from base branch."""
        return f"/sourcecontrol/{branch_id}/pull"

    @staticmethod
    def create_feature_branch(branch_id: int) -> str:
        """Create a feature branch."""
        return f"/sourcecontrol/{branch_id}/createFeatureBranch"

    @staticmethod
    def suggest(branch_id: int) -> str:
        """Get AI-suggested commit message from SideKick."""
        return f"/sourcecontrol/{branch_id}/suggest"


class OrganizationEndpoints:
    """Organization API endpoints."""

    @staticmethod
    def list() -> str:
        """List all organizations."""
        return "/organizations"

    @staticmethod
    def get(org_id: int) -> str:
        """Get organization by ID."""
        return f"/organizations/{org_id}"

    @staticmethod
    def mine() -> str:
        """Get current user's organization."""
        return "/organizations/mine"


class RepoEndpoints:
    """Repository (ApplicationDefinition) API endpoints."""

    @staticmethod
    def list(org_id: int | None = None) -> str:
        """List repositories, optionally filtered by organization."""
        if org_id:
            return f"/applicationdefinitions?organizationId={org_id}"
        return "/applicationdefinitions"

    @staticmethod
    def get(repo_id: int) -> str:
        """Get repository by ID."""
        return f"/applicationdefinitions/{repo_id}"


class ApplicationGroupEndpoints:
    """Application Group API endpoints.

    Groups organize branches within a repository. Each repository has one or more
    groups (typically a "Default" group). Service Pack groups allow creating
    maintenance branches from published versions.

    Group Types:
        0 = Default (main development group)
        1 = ServicePack (maintenance branch from published version)
    """

    @staticmethod
    def list(repo_id: int, group_type_id: int | None = None) -> str:
        """List application groups for a repository.

        Args:
            repo_id: Repository (ApplicationDefinition) ID
            group_type_id: Optional filter by group type (0=Default, 1=ServicePack)
        """
        url = f"/applicationgroups?applicationDefinitionId={repo_id}"
        if group_type_id is not None:
            url += f"&applicationGroupTypeId={group_type_id}"
        return url

    @staticmethod
    def get(group_id: int) -> str:
        """Get application group by ID."""
        return f"/applicationgroups/{group_id}"

    @staticmethod
    def create() -> str:
        """Create a service pack group."""
        return "/applicationgroups"

    @staticmethod
    def delete(group_id: int) -> str:
        """Delete an application group."""
        return f"/applicationgroups/{group_id}"


class BranchEndpoints:
    """Branch (Application) API endpoints."""

    @staticmethod
    def list(group_id: int, status_ids: list[int] | None = None) -> str:
        """List branches by application group ID.

        Args:
            group_id: Application group ID (from ApplicationGroupEndpoints.list())
            status_ids: Optional list of status IDs to filter by (1=draft, 2=inactive, 3=active, 4=history)
        """
        url = f"/applications?applicationGroupId={group_id}"
        if status_ids:
            for status_id in status_ids:
                url += f"&applicationStatusIds={status_id}"
        return url

    @staticmethod
    def get(branch_id: int) -> str:
        """Get branch by ID."""
        return f"/applications/{branch_id}"

    @staticmethod
    def roles(branch_id: int) -> str:
        """Get branch roles."""
        return f"/applications/{branch_id}/roles"

    @staticmethod
    def shell(branch_id: int) -> str:
        """Get branch shell configuration."""
        return f"/applications/{branch_id}/shell"

    @staticmethod
    def validate(branch_id: int) -> str:
        """Validate branch."""
        return f"/applications/{branch_id}/validate"

    @staticmethod
    def candelete(branch_id: int) -> str:
        """Check if branch can be deleted."""
        return f"/applications/{branch_id}/candelete"

    @staticmethod
    def delete(branch_id: int) -> str:
        """Delete a branch."""
        return f"/applications/{branch_id}"

    @staticmethod
    def replacements(branch_id: int) -> str:
        """Get configuration replacements for a branch."""
        return f"/applications/{branch_id}/configurationreplacements"

    @staticmethod
    def settings(branch_id: int) -> str:
        """Get application settings for a branch."""
        return f"/applications/{branch_id}/settings"

    @staticmethod
    def operations(branch_id: int) -> str:
        """Get operations for a branch."""
        return f"/applications/{branch_id}/operations"

    @staticmethod
    def publish(branch_id: int) -> str:
        """Publish a branch to the marketplace."""
        return f"/applications/{branch_id}/publish"


class UserEndpoints:
    """User API endpoints."""

    @staticmethod
    def list() -> str:
        """List all users."""
        return "/users"

    @staticmethod
    def get(user_id: int) -> str:
        """Get user by ID."""
        return f"/users/{user_id}"

    @staticmethod
    def studio_access(user_id: int) -> str:
        """Update user studio access."""
        return f"/users/{user_id}/studioaccess"


class MarketplaceEndpoints:
    """Marketplace application and version API endpoints."""

    @staticmethod
    def list(org_id: int | None = None) -> str:
        """List marketplace applications, optionally filtered by organization."""
        if org_id:
            return f"/marketplaceapplications?organizationId={org_id}"
        return "/marketplaceapplications"

    @staticmethod
    def get(app_id: int) -> str:
        """Get marketplace application by ID."""
        return f"/marketplaceapplications/{app_id}"

    @staticmethod
    def versions(app_id: int) -> str:
        """List published versions of a marketplace application."""
        return f"/marketplaceapplications/{app_id}/versions"

    @staticmethod
    def version(version_id: int) -> str:
        """Get marketplace application version by ID."""
        return f"/marketplaceapplicationversions/{version_id}"


class DependencyEndpoints:
    """Application dependency (references) API endpoints."""

    @staticmethod
    def list(branch_id: int) -> str:
        """List direct dependencies for a branch."""
        return f"/applications/{branch_id}/references"

    @staticmethod
    def all_references(branch_id: int) -> str:
        """List all references including transitive dependencies."""
        return f"/applications/{branch_id}/allreferences"


class WorkitemEndpoints:
    """Application work items API endpoints."""

    @staticmethod
    def list(branch_id: int) -> str:
        """List work items linked to a branch."""
        return f"/applications/{branch_id}/applicationworkitems"


class ConfigurationEndpoints:
    """Configuration content API endpoints."""

    @staticmethod
    def list_all(branch_id: int, config_type: str) -> str:
        """List all configurations of a type for a branch."""
        return f"/applications/{branch_id}/{config_type}configurations"

    @staticmethod
    def get_content(branch_id: int, config_type: str, config_id: int) -> str:
        """Get configuration content by ID."""
        return f"/applications/{branch_id}/{config_type}configurations/{config_id}"

    @staticmethod
    def get_by_reference(branch_id: int, config_type: str, ref_name: str) -> str:
        """Get configuration by reference name."""
        return f"/applications/{branch_id}/{config_type}configurations/referenceName/{ref_name}"


class EnvironmentEndpoints:
    """Environment API endpoints."""

    @staticmethod
    def list(org_id: int | None = None) -> str:
        """List environments, optionally filtered by organization."""
        if org_id:
            return f"/environments?organizationId={org_id}"
        return "/environments"

    @staticmethod
    def get(env_id: int) -> str:
        """Get environment by ID."""
        return f"/environments/{env_id}"


class EnvironmentComponentsEndpoints:
    """Environment components API endpoints."""

    @staticmethod
    def list(env_id: int | None = None) -> str:
        """List environment components, optionally filtered by environment."""
        if env_id:
            return f"/environmentcomponents?environmentId={env_id}"
        return "/environmentcomponents"

    @staticmethod
    def get(component_id: int) -> str:
        """Get environment component by ID."""
        return f"/environmentcomponents/{component_id}"

    @staticmethod
    def active_authorized() -> str:
        """Get active environment components the user is authorized to access."""
        return "/environmentcomponents/active/authorized"

    @staticmethod
    def deploy(component_id: int) -> str:
        """Deploy to an environment component."""
        return f"/environmentcomponents/{component_id}/deploy"


class ApiConnectionEndpoints:
    """API Connection endpoints for OData query execution.

    Uses:
    - /apiconnections for listing all connection types
    - /footprintapiconnections/{id} for getting Footprint connection details
    """

    @staticmethod
    def list(org_id: int | None = None, connection_type_id: int | None = None) -> str:
        """List API connections, optionally filtered by organization or type.

        Args:
            org_id: Filter by organization ID
            connection_type_id: Filter by connection type ID (e.g., Footprint type)
        """
        params = []
        if org_id:
            params.append(f"organizationId={org_id}")
        if connection_type_id:
            params.append(f"apiConnectionTypeId={connection_type_id}")
        if params:
            return f"/apiconnections?{'&'.join(params)}"
        return "/apiconnections"

    @staticmethod
    def get(connection_id: int) -> str:
        """Get API connection info by ID (includes connectionString)."""
        return f"/apiconnections/{connection_id}/info"

    @staticmethod
    def footprint_metadata(connection_id: int) -> str:
        """Get Footprint API connection full metadata (OData schema)."""
        return f"/footprintapiconnections/{connection_id}"

    @staticmethod
    def footprint_info(connection_id: int) -> str:
        """Get Footprint API connection info."""
        return f"/footprintapiconnections/{connection_id}/info"


class ODataEndpoints:
    """OData query execution endpoints."""

    @staticmethod
    def execute() -> str:
        """Execute an OData query."""
        return "/odata/execute"
