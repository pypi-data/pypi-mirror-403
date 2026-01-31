"""Pydantic models for Datex Studio API responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConfigurationModificationType(str, Enum):
    """Configuration modification type."""

    CREATED = "Created"
    UPDATED = "Updated"
    DELETED = "Deleted"


class BranchStatus(int, Enum):
    """Branch/application status types.

    These represent different stages in the source control workflow:
    - MAIN: Main development branch (one per repo)
    - INACTIVE: Previous published releases
    - PUBLISHED_MAIN: Current published release
    - WORKSPACE_HISTORY: Commit snapshots (frozen after commit)
    - WORKSPACE_ACTIVE: Feature branches (active development)

    Note: Status names were updated in January 2026:
    - DRAFT -> MAIN
    - ACTIVE -> PUBLISHED_MAIN
    """

    MAIN = 1
    INACTIVE = 2
    PUBLISHED_MAIN = 3
    WORKSPACE_HISTORY = 4
    WORKSPACE_ACTIVE = 5


# Human-readable names for branch statuses
BRANCH_STATUS_NAMES: dict[int, str] = {
    1: "Main",
    2: "Inactive",
    3: "PublishedMain",
    4: "WorkspaceHistory",
    5: "WorkspaceActive",
}

# CLI-friendly aliases for filtering (maps alias -> status ID)
BRANCH_STATUS_ALIASES: dict[str, int] = {
    "main": 1,
    "inactive": 2,
    "published": 3,
    "history": 4,
    "workspace-history": 4,
    "feature": 5,
    "workspace-active": 5,
    "workspace": 5,
}

# Semantic context descriptions for LLM consumption
BRANCH_STATUS_CONTEXT: dict[int, str] = {
    1: "Main development branch - receives commits from feature branches",
    2: "Previous published release - superseded by newer published version",
    3: "Current published release - latest version available to users",
    4: "Commit snapshot - represents a single commit to the main branch",
    5: "Feature branch - active development work in progress",
}


class ApplicationDefinitionType(int, Enum):
    """Application definition type enumeration.

    These represent different types of applications:
    - WEB: Web applications
    - MOBILE: Mobile applications
    - COMPONENTMODULE: Reusable component modules
    - API: Backend APIs
    - PORTAL: Portal applications

    Note: Renamed from ApplicationType in January 2026.
    """

    WEB = 1
    MOBILE = 2
    COMPONENTMODULE = 3
    API = 6
    PORTAL = 7


# Human-readable names for application definition types
APPLICATION_DEFINITION_TYPE_NAMES: dict[int, str] = {
    1: "Web",
    2: "Mobile",
    3: "ComponentModule",
    6: "API",
    7: "Portal",
}

# CLI-friendly aliases for filtering (maps alias -> type ID)
APPLICATION_DEFINITION_TYPE_ALIASES: dict[str, int] = {
    "web": 1,
    "mobile": 2,
    "componentmodule": 3,
    "api": 6,
    "portal": 7,
}


class UserDto(BaseModel):
    """User information."""

    id: int
    email: str
    display_name: str = Field(alias="displayName")

    model_config = {"populate_by_name": True}


class LockedConfigDto(BaseModel):
    """Individual configuration lock information."""

    id: int
    application_definition_id: int = Field(alias="applicationDefinitionId")
    application_id: int = Field(alias="applicationId")
    reference_name: str = Field(alias="referenceName")
    locked_by: UserDto | None = Field(alias="lockedBy", default=None)
    modified_date: datetime = Field(alias="modifiedDate")

    model_config = {"populate_by_name": True}


class LockedAssetDto(BaseModel):
    """Application-level asset lock (replacements, settings, operations)."""

    application_id: int = Field(alias="applicationId")
    locked_by: UserDto | None = Field(alias="lockedBy", default=None)

    model_config = {"populate_by_name": True}


class LocksDto(BaseModel):
    """Complete lock state for an application definition."""

    configs: list[LockedConfigDto] = Field(default_factory=list)
    replacements: LockedAssetDto | None = None
    settings_and_references: LockedAssetDto | None = Field(
        alias="settingsAndReferences", default=None
    )
    operations_and_roles: LockedAssetDto | None = Field(alias="operationsAndRoles", default=None)

    model_config = {"populate_by_name": True}


class ConfigurationUpstreamChangesDto(BaseModel):
    """Individual configuration change details."""

    id: int | None = None
    base_config_id: int | None = Field(alias="baseConfigId", default=None)
    reference_name: str = Field(alias="referenceName")
    configuration_type_id: str = Field(alias="configurationTypeId")
    modification_type_id: ConfigurationModificationType | None = Field(
        alias="modificationTypeId", default=None
    )

    model_config = {"populate_by_name": True}


class UpstreamChangesDto(BaseModel):
    """Changes available in the base branch."""

    configs: list[ConfigurationUpstreamChangesDto] = Field(default_factory=list)
    has_replacements: bool = Field(alias="hasReplacements", default=False)
    has_settings: bool = Field(alias="hasSettings", default=False)
    has_operations: bool = Field(alias="hasOperations", default=False)
    has_references: bool = Field(alias="hasReferences", default=False)
    has_roles: bool = Field(alias="hasRoles", default=False)
    application_id: int = Field(alias="applicationId")
    base_application_id: int | None = Field(alias="baseApplicationId", default=None)
    application_definition_id: int = Field(alias="applicationDefinitionId")

    model_config = {"populate_by_name": True}


class ApplicationHistoryItemDto(BaseModel):
    """History entry for application-level commits."""

    application_id: int = Field(alias="applicationId")
    application_definition_id: int = Field(alias="applicationDefinitionId")
    commit_title: str = Field(alias="commitTitle")
    commit_message: str = Field(alias="commitMessage")
    commit_date: datetime = Field(alias="commitDate")
    author: UserDto

    model_config = {"populate_by_name": True}


class ConfigurationHistoryItemDto(BaseModel):
    """History entry for configuration-level commits."""

    config_id: int = Field(alias="configId")
    application_id: int = Field(alias="applicationId")
    application_definition_id: int = Field(alias="applicationDefinitionId")
    commit_title: str = Field(alias="commitTitle")
    commit_message: str = Field(alias="commitMessage")
    commit_date: datetime = Field(alias="commitDate")
    author: UserDto
    modification_type_id: ConfigurationModificationType = Field(alias="modificationTypeId")
    config_type: str = Field(alias="configType")

    model_config = {"populate_by_name": True}


class ReplacementsHistoryItemDto(BaseModel):
    """History entry for replacements changes."""

    application_id: int = Field(alias="applicationId")
    application_definition_id: int = Field(alias="applicationDefinitionId")
    commit_title: str = Field(alias="commitTitle")
    commit_message: str = Field(alias="commitMessage")
    commit_date: datetime = Field(alias="commitDate")
    author: UserDto

    model_config = {"populate_by_name": True}


class SettingsAndReferencesHistoryItemDto(BaseModel):
    """History entry for settings and references changes."""

    application_id: int = Field(alias="applicationId")
    application_definition_id: int = Field(alias="applicationDefinitionId")
    commit_title: str = Field(alias="commitTitle")
    commit_message: str = Field(alias="commitMessage")
    commit_date: datetime = Field(alias="commitDate")
    author: UserDto

    model_config = {"populate_by_name": True}


class OperationsAndRolesHistoryItemDto(BaseModel):
    """History entry for operations and roles changes."""

    application_id: int = Field(alias="applicationId")
    application_definition_id: int = Field(alias="applicationDefinitionId")
    commit_title: str = Field(alias="commitTitle")
    commit_message: str = Field(alias="commitMessage")
    commit_date: datetime = Field(alias="commitDate")
    author: UserDto

    model_config = {"populate_by_name": True}


# Marketplace Models (Phase 6)


class MarketplaceApplicationDto(BaseModel):
    """Marketplace application information."""

    id: int
    name: str
    description: str | None = None
    unique_identifier: str = Field(alias="uniqueIdentifier")
    organization_id: int = Field(alias="organizationId")
    application_definition_id: int | None = Field(alias="applicationDefinitionId", default=None)
    is_public: bool = Field(alias="isPublic", default=False)

    model_config = {"populate_by_name": True}


class MarketplaceVersionDto(BaseModel):
    """Marketplace application version information."""

    id: int
    marketplace_application_id: int = Field(alias="marketPlaceApplicationId")
    application_id: int | None = Field(alias="applicationId", default=None)
    version_code: str = Field(alias="versionCode")
    version_name: str = Field(alias="versionName")
    release_date: datetime = Field(alias="releaseDate")
    release_notes: str | None = Field(alias="releaseNotes", default=None)
    is_latest: bool = Field(alias="isLatest", default=False)
    is_ready: bool = Field(alias="isReady", default=False)

    model_config = {"populate_by_name": True}


# Dependency Models (Phase 6)


class ApplicationReferenceDto(BaseModel):
    """Application dependency reference information."""

    id: int
    application_id: int = Field(alias="applicationId")
    marketplace_version_id: int = Field(alias="marketPlaceApplicationVersionId")
    reference_name: str = Field(alias="referenceName")
    # Version details may be populated when expanded
    version_code: str | None = Field(alias="versionCode", default=None)
    version_name: str | None = Field(alias="versionName", default=None)

    model_config = {"populate_by_name": True}


# Work Item Models (Phase 6)


class ApplicationWorkitemDto(BaseModel):
    """Application work item link information."""

    id: int
    application_id: int = Field(alias="applicationId")
    external_id: str = Field(alias="externalId")  # Azure DevOps work item ID
    devops_organization: str = Field(alias="devOpsOrganization")
    commit_id: int | None = Field(alias="commitId", default=None)

    model_config = {"populate_by_name": True}


# Configuration Exploration Models


class ConfigurationSummaryDto(BaseModel):
    """Summary of a configuration for listing."""

    id: int
    reference_name: str = Field(alias="referenceName")
    label: str | None = None
    description: str | None = None
    access_modifier: str | None = Field(alias="accessModifier", default=None)

    model_config = {"populate_by_name": True}


class ConfigurationContentDto(BaseModel):
    """Full configuration content."""

    id: int
    reference_name: str = Field(alias="referenceName")
    label: str | None = None
    description: str | None = None
    access_modifier: str | None = Field(alias="accessModifier", default=None)
    # The actual JSON configuration - key varies by config type
    config: dict | None = None
    json_content: dict | None = Field(alias="json", default=None)

    model_config = {"populate_by_name": True}


# =============================================================================
# Configuration Output Models (for explore config command)
# =============================================================================


class OrganizationOutput(BaseModel):
    """Organization info for output with external auth support."""

    id: int
    name: str
    tenant_id: str | None = None
    external_entra_id: bool = False
    external_entra_id_domain_name: str | None = None
    home_tenant_id: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> "OrganizationOutput | None":
        """Create from API response."""
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            tenant_id=data.get("tenantId"),
            external_entra_id=data.get("externalEntraId", False),
            external_entra_id_domain_name=data.get("externalEntraIdDomainName"),
            home_tenant_id=data.get("homeTenantId"),
        )


class RepositoryOutput(BaseModel):
    """Simplified repository (applicationDefinition) info for output."""

    id: int
    name: str
    description: str | None = None
    unique_identifier: str = Field(serialization_alias="uniqueIdentifier")
    organization: OrganizationOutput | None = None

    @classmethod
    def from_api(cls, data: dict) -> "RepositoryOutput | None":
        """Create from API applicationDefinition response."""
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            description=data.get("description"),
            unique_identifier=data.get("uniqueIdentifier", ""),
            organization=OrganizationOutput.from_api(data.get("organization", {})),
        )


class BranchOutput(BaseModel):
    """Simplified branch (application) info for output."""

    id: int
    reference_name: str = Field(serialization_alias="referenceName")
    repository: RepositoryOutput | None = None

    @classmethod
    def from_api(cls, data: dict) -> "BranchOutput | None":
        """Create from API application response."""
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            reference_name=data.get("referenceName", ""),
            repository=RepositoryOutput.from_api(data.get("applicationDefinition", {})),
        )


class ConfigurationMetadata(BaseModel):
    """Metadata extracted from configuration API response.

    These fields are moved to the response metadata section
    to keep the main configuration content clean.
    """

    created_date: str | None = Field(default=None, serialization_alias="createdDate")
    modified_date: str | None = Field(default=None, serialization_alias="modifiedDate")
    commit_date: str | None = Field(default=None, serialization_alias="commitDate")
    has_customizations: bool = Field(default=False, serialization_alias="hasCustomizations")
    branch: BranchOutput | None = None

    @classmethod
    def from_api(cls, data: dict) -> "ConfigurationMetadata":
        """Extract metadata fields from API response."""
        return cls(
            created_date=data.get("createdDate"),
            modified_date=data.get("modifiedDate"),
            commit_date=data.get("commitDate"),
            has_customizations=data.get("hasCustomizations", False),
            branch=BranchOutput.from_api(data.get("application", {})),
        )

    def to_metadata_dict(self) -> dict:
        """Convert to dict for inclusion in response metadata."""
        return self.model_dump(by_alias=True, exclude_none=True)


# Fields to show first in configuration output (in this order)
CONFIG_PRIORITY_FIELDS = ["id", "referenceName", "title", "description", "configurationType"]


class ConfigurationOutput:
    """Helper for explore config command output.

    Separates the configuration content (for main output) from
    metadata fields (for response metadata section).
    """

    def __init__(self, content: dict, metadata: ConfigurationMetadata):
        self.content = content
        self.metadata = metadata

    @classmethod
    def from_api(cls, data: dict) -> "ConfigurationOutput":
        """Create from API response, separating content from metadata."""
        # Extract json content (may be in 'json' or 'config' field)
        raw_content = data.get("json") or data.get("config") or {}

        # Remove redundant configurationTypeId from content (we use outer configurationType)
        raw_content.pop("configurationTypeId", None)

        # Add configurationType from outer response (authoritative source)
        config_type = data.get("configurationType")
        if config_type and isinstance(config_type, dict):
            raw_content["configurationType"] = {
                "id": config_type.get("id"),
                "name": config_type.get("name"),
            }

        # Reorder content with priority fields first
        content = cls._reorder_content(raw_content)

        # Extract metadata fields
        metadata = ConfigurationMetadata.from_api(data)

        return cls(content=content, metadata=metadata)

    @classmethod
    def _reorder_content(cls, content: dict) -> dict:
        """Reorder content dict with priority fields first, recursively."""
        if not content:
            return content

        ordered: dict = {}

        # Add priority fields first (in order)
        for field in CONFIG_PRIORITY_FIELDS:
            if field in content:
                ordered[field] = cls._reorder_value(content[field])

        # Add remaining fields in original order
        for key, value in content.items():
            if key not in ordered:
                ordered[key] = cls._reorder_value(value)

        return ordered

    @classmethod
    def _reorder_value(cls, value: Any) -> Any:
        """Recursively reorder nested dicts and lists."""
        if isinstance(value, dict):
            # Check if this looks like a config object (has referenceName or id)
            if "referenceName" in value or "id" in value:
                return cls._reorder_content(value)
            # Otherwise just recurse into nested dicts
            return {k: cls._reorder_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [cls._reorder_value(item) for item in value]
        else:
            return value
