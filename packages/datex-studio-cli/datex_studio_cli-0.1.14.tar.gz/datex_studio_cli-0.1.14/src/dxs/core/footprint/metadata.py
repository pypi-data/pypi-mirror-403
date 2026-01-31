"""Disk cache for OData $metadata XML.

Stores raw XML files and an index tracking cache freshness per connection.

Cache layout:
    ~/.datex/metadata/{connection_id}.xml   — raw EDMX XML
    ~/.datex/metadata/index.json            — {connection_id: {cached_at, connection_name}}
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dxs.utils.paths import get_metadata_dir

DEFAULT_TTL_HOURS = 24


class MetadataCache:
    """Read/write cache for OData $metadata XML files."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir or get_metadata_dir()
        self._index_path = self._dir / "index.json"

    def _load_index(self) -> dict[str, Any]:
        """Load the index file, returning empty dict if missing/corrupt."""
        if not self._index_path.exists():
            return {}
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict[str, Any]) -> None:
        """Write the index file atomically."""
        self._index_path.write_text(
            json.dumps(index, indent=2, default=str),
            encoding="utf-8",
        )

    def get(self, connection_id: int) -> str | None:
        """Return cached XML for a connection, or None if missing."""
        xml_path = self._dir / f"{connection_id}.xml"
        if not xml_path.exists():
            return None
        return xml_path.read_text(encoding="utf-8")

    def is_fresh(self, connection_id: int, ttl_hours: int = DEFAULT_TTL_HOURS) -> bool:
        """Check whether the cached entry is within TTL."""
        index = self._load_index()
        entry = index.get(str(connection_id))
        if entry is None:
            return False
        try:
            cached_at = datetime.fromisoformat(entry["cached_at"])
        except (KeyError, ValueError):
            return False
        age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600
        return age_hours < ttl_hours

    def put(
        self,
        connection_id: int,
        xml: str,
        connection_name: str | None = None,
    ) -> None:
        """Write XML to disk and update the index."""
        xml_path = self._dir / f"{connection_id}.xml"
        xml_path.write_text(xml, encoding="utf-8")

        index = self._load_index()
        index[str(connection_id)] = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "connection_name": connection_name,
        }
        self._save_index(index)

    def remove(self, connection_id: int) -> None:
        """Remove a cached entry."""
        xml_path = self._dir / f"{connection_id}.xml"
        if xml_path.exists():
            xml_path.unlink()
        index = self._load_index()
        index.pop(str(connection_id), None)
        self._save_index(index)
