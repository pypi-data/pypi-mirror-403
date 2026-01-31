"""SQLite-based caching for explore commands.

Caches configuration data for immutable branches (INACTIVE, PUBLISHED_MAIN, WORKSPACE_HISTORY)
to avoid redundant API calls across CLI invocations. Main and WorkspaceActive branches
are never cached as they are mutable.
"""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from dxs.core.api.models import BranchStatus
from dxs.utils.paths import get_cache_path

# Schema version - increment when schema changes
CACHE_SCHEMA_VERSION = "1"


@dataclass
class CacheHitInfo:
    """Tracks cache usage during a command execution."""

    hits: int = 0
    misses: int = 0
    cached_at: str | None = None  # ISO timestamp of oldest cache hit

    def record_hit(self, cached_at: str | None = None) -> None:
        """Record a cache hit."""
        self.hits += 1
        # Track the oldest cache timestamp
        if cached_at and (self.cached_at is None or cached_at < self.cached_at):
            self.cached_at = cached_at

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1

    @property
    def used_cache(self) -> bool:
        """Whether any cache hits occurred."""
        return self.hits > 0

    def to_metadata(self) -> dict[str, Any] | None:
        """Convert to metadata dict for response, or None if no cache activity."""
        if not self.used_cache:
            return None
        return {
            "from_cache": True,
            "cache_hits": self.hits,
            "cached_at": self.cached_at,
        }


# Module-level session tracking for cache hits
_session_cache_info: CacheHitInfo | None = None


def start_cache_session() -> None:
    """Start tracking cache hits for a command session."""
    global _session_cache_info
    _session_cache_info = CacheHitInfo()


def get_cache_session_info() -> CacheHitInfo | None:
    """Get current session's cache hit info."""
    return _session_cache_info


def end_cache_session() -> dict[str, Any] | None:
    """End the cache session and return metadata dict if cache was used."""
    global _session_cache_info
    info = _session_cache_info
    _session_cache_info = None
    return info.to_metadata() if info else None


# Cacheable branch statuses (immutable branches only)
CACHEABLE_STATUSES = {
    BranchStatus.INACTIVE,  # 2 - Previous releases
    BranchStatus.PUBLISHED_MAIN,  # 3 - Current release
    BranchStatus.WORKSPACE_HISTORY,  # 4 - Frozen commit snapshots
}


class ExploreCache:
    """SQLite cache for explore command data.

    Caches:
    - Branch info (status, metadata)
    - Config index (ref_name -> type, id, app_ref, is_external mapping)
    - Full config content
    - Extracted references

    Only caches data for immutable branches (INACTIVE, PUBLISHED_MAIN, WORKSPACE_HISTORY).
    Main and WorkspaceActive branches are never cached.
    """

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or get_cache_path()
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist, handle migrations."""
        with self._connection() as conn:
            # Check if cache_meta table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cache_meta'"
            )
            if not cursor.fetchone():
                self._create_schema(conn)
            else:
                # Check version and migrate if needed
                version = self._get_schema_version(conn)
                if version != CACHE_SCHEMA_VERSION:
                    self._migrate_schema(conn, version)

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """Create all cache tables."""
        conn.executescript("""
            CREATE TABLE cache_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE branch_info (
                branch_id INTEGER PRIMARY KEY,
                status INTEGER NOT NULL,
                data TEXT NOT NULL,
                cached_at TEXT NOT NULL
            );

            CREATE TABLE config_index (
                branch_id INTEGER NOT NULL,
                ref_name_lower TEXT NOT NULL,
                config_type TEXT NOT NULL,
                config_id INTEGER NOT NULL,
                app_ref_name TEXT NOT NULL,
                is_external INTEGER NOT NULL,
                cached_at TEXT NOT NULL,
                PRIMARY KEY (branch_id, ref_name_lower)
            );

            CREATE INDEX idx_config_index_branch ON config_index(branch_id);

            CREATE TABLE config_content (
                branch_id INTEGER NOT NULL,
                config_type TEXT NOT NULL,
                config_id INTEGER NOT NULL,
                ref_name TEXT NOT NULL,
                content TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                PRIMARY KEY (branch_id, config_type, config_id)
            );

            CREATE INDEX idx_config_content_branch ON config_content(branch_id);
            CREATE INDEX idx_config_content_ref ON config_content(branch_id, ref_name);

            CREATE TABLE config_references (
                branch_id INTEGER NOT NULL,
                config_type TEXT NOT NULL,
                config_id INTEGER NOT NULL,
                refs TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                PRIMARY KEY (branch_id, config_type, config_id)
            );

            CREATE INDEX idx_config_references_branch ON config_references(branch_id);
        """)
        conn.execute(
            "INSERT INTO cache_meta (key, value) VALUES (?, ?)",
            ("schema_version", CACHE_SCHEMA_VERSION),
        )

    def _get_schema_version(self, conn: sqlite3.Connection) -> str:
        """Get current schema version."""
        cursor = conn.execute("SELECT value FROM cache_meta WHERE key = 'schema_version'")
        row = cursor.fetchone()
        return row["value"] if row else "0"

    def _migrate_schema(self, conn: sqlite3.Connection, from_version: str) -> None:
        """Migrate schema from older version.

        For v1, we simply drop and recreate. Cache data is ephemeral and can be rebuilt.
        """
        conn.executescript("""
            DROP TABLE IF EXISTS config_references;
            DROP TABLE IF EXISTS config_content;
            DROP TABLE IF EXISTS config_index;
            DROP TABLE IF EXISTS branch_info;
            DROP TABLE IF EXISTS cache_meta;
        """)
        self._create_schema(conn)

    def is_cacheable_branch(self, branch_status: int) -> bool:
        """Check if a branch status is cacheable (immutable)."""
        try:
            status = BranchStatus(branch_status)
            return status in CACHEABLE_STATUSES
        except ValueError:
            return False

    def _now_iso(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def _record_hit(self, cached_at: str | None) -> None:
        """Record a cache hit in the session tracker."""
        if _session_cache_info is not None:
            _session_cache_info.record_hit(cached_at)

    def _record_miss(self) -> None:
        """Record a cache miss in the session tracker."""
        if _session_cache_info is not None:
            _session_cache_info.record_miss()

    # === Branch Info Methods ===

    def get_branch_info(self, branch_id: int) -> dict[str, Any] | None:
        """Get cached branch info."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT data, cached_at FROM branch_info WHERE branch_id = ?", (branch_id,)
            )
            row = cursor.fetchone()
            if row:
                self._record_hit(row["cached_at"])
                return cast(dict[str, Any], json.loads(row["data"]))
            self._record_miss()
            return None

    def set_branch_info(self, branch_id: int, status: int, data: dict[str, Any]) -> None:
        """Cache branch info (only if status is cacheable)."""
        if not self.is_cacheable_branch(status):
            return
        with self._connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO branch_info
                   (branch_id, status, data, cached_at) VALUES (?, ?, ?, ?)""",
                (branch_id, status, json.dumps(data), self._now_iso()),
            )

    # === Config Index Methods ===

    def get_config_index(self, branch_id: int) -> dict[str, tuple[str, int, str, bool]] | None:
        """Get cached config index for a branch.

        Returns:
            Dict mapping ref_name_lower -> (type, id, app_ref_name, is_external)
            or None if not cached.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT ref_name_lower, config_type, config_id, app_ref_name, is_external, cached_at
                   FROM config_index WHERE branch_id = ? LIMIT 1""",
                (branch_id,),
            )
            first_row = cursor.fetchone()
            if not first_row:
                self._record_miss()
                return None

            # Record the hit with the cached_at timestamp
            self._record_hit(first_row["cached_at"])

            # Fetch all rows
            cursor = conn.execute(
                """SELECT ref_name_lower, config_type, config_id, app_ref_name, is_external
                   FROM config_index WHERE branch_id = ?""",
                (branch_id,),
            )
            rows = cursor.fetchall()
            return {
                row["ref_name_lower"]: (
                    row["config_type"],
                    row["config_id"],
                    row["app_ref_name"],
                    bool(row["is_external"]),
                )
                for row in rows
            }

    def set_config_index(
        self,
        branch_id: int,
        branch_status: int,
        index: dict[str, tuple[str, int, str, bool]],
    ) -> None:
        """Cache config index for a branch (only if branch is cacheable)."""
        if not self.is_cacheable_branch(branch_status):
            return
        with self._connection() as conn:
            # Clear existing entries for this branch
            conn.execute("DELETE FROM config_index WHERE branch_id = ?", (branch_id,))
            # Insert new entries
            now = self._now_iso()
            conn.executemany(
                """INSERT INTO config_index
                   (branch_id, ref_name_lower, config_type, config_id, app_ref_name, is_external, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (branch_id, ref_lower, ctype, cid, app_ref or "", int(is_ext), now)
                    for ref_lower, (ctype, cid, app_ref, is_ext) in index.items()
                ],
            )

    # === Config Content Methods ===

    def get_config_content(
        self, branch_id: int, config_type: str, config_id: int
    ) -> dict[str, Any] | None:
        """Get cached config content."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT content, cached_at FROM config_content
                   WHERE branch_id = ? AND config_type = ? AND config_id = ?""",
                (branch_id, config_type, config_id),
            )
            row = cursor.fetchone()
            if row:
                self._record_hit(row["cached_at"])
                return cast(dict[str, Any], json.loads(row["content"]))
            self._record_miss()
            return None

    def set_config_content(
        self,
        branch_id: int,
        branch_status: int,
        config_type: str,
        config_id: int,
        ref_name: str,
        content: dict[str, Any],
    ) -> None:
        """Cache config content (only if branch is cacheable)."""
        if not self.is_cacheable_branch(branch_status):
            return
        with self._connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO config_content
                   (branch_id, config_type, config_id, ref_name, content, cached_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (branch_id, config_type, config_id, ref_name, json.dumps(content), self._now_iso()),
            )

    # === References Methods ===

    def get_references(
        self, branch_id: int, config_type: str, config_id: int
    ) -> dict[str, list[str]] | None:
        """Get cached extracted references."""
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT refs, cached_at FROM config_references
                   WHERE branch_id = ? AND config_type = ? AND config_id = ?""",
                (branch_id, config_type, config_id),
            )
            row = cursor.fetchone()
            if row:
                self._record_hit(row["cached_at"])
                return cast(dict[str, list[str]], json.loads(row["refs"]))
            self._record_miss()
            return None

    def set_references(
        self,
        branch_id: int,
        branch_status: int,
        config_type: str,
        config_id: int,
        references: dict[str, list[str]],
    ) -> None:
        """Cache extracted references (only if branch is cacheable)."""
        if not self.is_cacheable_branch(branch_status):
            return
        with self._connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO config_references
                   (branch_id, config_type, config_id, refs, cached_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (branch_id, config_type, config_id, json.dumps(references), self._now_iso()),
            )

    # === Cache Management ===

    def clear_branch(self, branch_id: int) -> int:
        """Clear all cached data for a specific branch.

        Returns number of entries cleared.
        """
        total = 0
        with self._connection() as conn:
            for table in ["branch_info", "config_index", "config_content", "config_references"]:
                cursor = conn.execute(f"DELETE FROM {table} WHERE branch_id = ?", (branch_id,))
                total += cursor.rowcount
        return total

    def clear_all(self) -> dict[str, int]:
        """Clear entire cache.

        Returns dict with counts per table.
        """
        counts: dict[str, int] = {}
        with self._connection() as conn:
            for table in ["branch_info", "config_index", "config_content", "config_references"]:
                cursor = conn.execute(f"DELETE FROM {table}")
                counts[table] = cursor.rowcount
        return counts

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats: dict[str, Any] = {"branches": {}}

        with self._connection() as conn:
            # Count branches
            cursor = conn.execute("SELECT COUNT(*) FROM branch_info")
            stats["branch_count"] = cursor.fetchone()[0]

            # Count indexed branches
            cursor = conn.execute("SELECT COUNT(DISTINCT branch_id) FROM config_index")
            stats["indexed_branches"] = cursor.fetchone()[0]

            # Count configs
            cursor = conn.execute("SELECT COUNT(*) FROM config_content")
            stats["config_count"] = cursor.fetchone()[0]

            # Count references
            cursor = conn.execute("SELECT COUNT(*) FROM config_references")
            stats["reference_count"] = cursor.fetchone()[0]

            # Per-branch breakdown from config_index
            cursor = conn.execute("""
                SELECT ci.branch_id,
                       bi.status,
                       COUNT(*) as index_count
                FROM config_index ci
                LEFT JOIN branch_info bi ON ci.branch_id = bi.branch_id
                GROUP BY ci.branch_id
            """)
            for row in cursor.fetchall():
                branch_id = row["branch_id"]
                stats["branches"][branch_id] = {
                    "status": row["status"],
                    "index_count": row["index_count"],
                }

            # Add content counts per branch (including branches not in config_index)
            cursor = conn.execute("""
                SELECT cc.branch_id, bi.status, COUNT(*) as content_count
                FROM config_content cc
                LEFT JOIN branch_info bi ON cc.branch_id = bi.branch_id
                GROUP BY cc.branch_id
            """)
            for row in cursor.fetchall():
                branch_id = row["branch_id"]
                if branch_id in stats["branches"]:
                    stats["branches"][branch_id]["content_count"] = row["content_count"]
                else:
                    # Branch has content but no index entries
                    stats["branches"][branch_id] = {
                        "status": row["status"],
                        "index_count": 0,
                        "content_count": row["content_count"],
                    }

        # Database file size
        if self._db_path.exists():
            stats["db_size_bytes"] = self._db_path.stat().st_size
            stats["db_size_mb"] = round(stats["db_size_bytes"] / (1024 * 1024), 2)

        return stats


# Module-level singleton instance
_cache_instance: ExploreCache | None = None


def get_cache() -> ExploreCache:
    """Get the singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ExploreCache()
    return _cache_instance
