"""Path utilities for configuration and credential storage."""

from pathlib import Path


def get_datex_home() -> Path:
    """Get the Datex home directory (~/.datex/).

    Creates the directory if it doesn't exist.
    """
    home = Path.home() / ".datex"
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_config_path() -> Path:
    """Get the path to the config file (~/.datex/config.yaml)."""
    return get_datex_home() / "config.yaml"


def get_credentials_path() -> Path:
    """Get the path to the credentials file (~/.datex/credentials.yaml)."""
    return get_datex_home() / "credentials.yaml"


def get_cache_path() -> Path:
    """Get the path to the cache database (~/.datex/cache.db)."""
    return get_datex_home() / "cache.db"


def ensure_secure_permissions(path: Path) -> None:
    """Set secure permissions (owner read/write only) on a file.

    Args:
        path: Path to the file to secure.
    """
    if path.exists():
        path.chmod(0o600)
