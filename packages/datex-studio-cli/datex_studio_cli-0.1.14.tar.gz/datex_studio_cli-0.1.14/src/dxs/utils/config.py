"""Configuration management for the Datex Studio CLI."""

import os
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from dxs.utils.paths import get_config_path, get_datex_home


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config file.

    Priority (highest to lowest):
    1. Environment variables (prefixed with DXS_)
    2. Config file (~/.datex/config.yaml)
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="DXS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Entra configuration
    azure_client_id: str = Field(
        default="9640be1f-31b2-4970-85a1-2fc78fab9731",
        description="Azure AD application client ID",
    )
    azure_tenant_id: str = Field(
        default="0cd4978c-db83-4ffe-8821-f01a5f8110ac",
        description="Azure AD tenant ID",
    )
    azure_scopes: list[str] = Field(
        default_factory=lambda: ["api://bcf89c41-81cc-49ef-b771-ed5ec9e1e5e4/access_as_user"],
        description="OAuth scopes to request",
    )

    # Azure DevOps configuration (Phase 6)
    azure_devops_scopes: list[str] = Field(
        default_factory=lambda: ["https://app.vssps.visualstudio.com/user_impersonation"],
        description="OAuth scopes for Azure DevOps API",
    )

    # Dynamics CRM / Dataverse configuration
    dynamics_crm_url: str | None = Field(
        default=None,
        description="Dynamics CRM instance URL (e.g., https://yourorg.crm.dynamics.com)",
    )

    @property
    def dynamics_crm_scopes(self) -> list[str]:
        """Get OAuth scopes for Dynamics CRM based on configured URL.

        Returns org-specific scope if dynamics_crm_url is configured,
        otherwise returns empty list (Dynamics auth will be skipped).
        """
        if self.dynamics_crm_url:
            # Build org-specific scope from URL
            # e.g., https://yourorg.crm.dynamics.com -> https://yourorg.crm.dynamics.com/.default
            url = self.dynamics_crm_url.rstrip("/")
            return [f"{url}/.default"]
        return []

    # Footprint OData configuration (for direct Footprint API access)
    footprint_scope: str = Field(
        default="api://e47e817f-1bdd-4d8b-b18e-984124910250/.default",
        description="OAuth scope for Footprint API",
    )

    # API configuration
    api_base_url: str = Field(
        default="https://wavelength.host/api",
        description="Base URL for Datex Studio API",
    )
    api_timeout: int = Field(default=30, description="API request timeout in seconds")

    # Default context (can be overridden by CLI flags)
    default_org: str | None = Field(default=None, description="Default organization ID")
    default_env: str | None = Field(default=None, description="Default environment ID")
    default_branch: int | None = Field(default=None, description="Default branch ID")
    default_repo: int | None = Field(default=None, description="Default repository ID")

    # Output settings
    default_output_format: str = Field(
        default="yaml", description="Default output format (yaml, json, csv)"
    )

    # Security settings
    restricted_mode: bool = Field(
        default=False,
        description="When enabled, blocks commands that write files or perform destructive operations",
    )


def load_config_file() -> dict[str, Any]:
    """Load configuration from ~/.datex/config.yaml.

    Returns:
        Dictionary of configuration values, empty dict if file doesn't exist.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return {}

    with config_path.open("r") as f:
        config = yaml.safe_load(f) or {}
    return config


def save_config_file(config: dict[str, Any]) -> None:
    """Save configuration to ~/.datex/config.yaml.

    Args:
        config: Dictionary of configuration values.
    """
    config_path = get_config_path()

    # Ensure directory exists
    get_datex_home()

    with config_path.open("w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def get_settings() -> Settings:
    """Get application settings, merging config file with environment variables.

    Returns:
        Settings instance with merged configuration.
    """
    # Load config file values
    file_config = load_config_file()

    # Convert config file keys to environment variable format for pydantic
    # This allows config file to override defaults, but env vars still take priority
    env_overrides = {}
    for key, value in file_config.items():
        env_key = f"DXS_{key.upper()}"
        if env_key not in os.environ and value is not None:
            # Only set if not already in environment
            if isinstance(value, list):
                env_overrides[env_key] = ",".join(str(v) for v in value)
            else:
                env_overrides[env_key] = str(value)

    # Temporarily set environment variables for config file values
    original_env = {}
    for key, value in env_overrides.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        settings = Settings()
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

    return settings


def get_config_value(key: str) -> Any:
    """Get a single configuration value.

    Args:
        key: Configuration key (e.g., "api_base_url").

    Returns:
        Configuration value or None if not set.
    """
    settings = get_settings()
    return getattr(settings, key, None)


def set_config_value(key: str, value: Any) -> None:
    """Set a configuration value in the config file.

    Args:
        key: Configuration key.
        value: Value to set.
    """
    config = load_config_file()
    config[key] = value
    save_config_file(config)


def list_config() -> dict[str, Any]:
    """List all configuration values.

    Returns:
        Dictionary of all configuration values with their sources.
    """
    settings = get_settings()
    file_config = load_config_file()

    result = {}
    for field_name, field_info in Settings.model_fields.items():
        value = getattr(settings, field_name)
        env_key = f"DXS_{field_name.upper()}"

        # Determine source
        if env_key in os.environ:
            source = "environment"
        elif field_name in file_config:
            source = "config_file"
        else:
            source = "default"

        result[field_name] = {
            "value": value,
            "source": source,
            "description": field_info.description,
        }

    return result


def is_restricted_mode() -> bool:
    """Check if restricted mode is enabled.

    Returns:
        True if DXS_RESTRICTED_MODE is set to true.
    """
    return get_settings().restricted_mode
