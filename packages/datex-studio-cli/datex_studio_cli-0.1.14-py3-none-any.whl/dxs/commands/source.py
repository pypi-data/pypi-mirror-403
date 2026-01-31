"""Source control commands for dxs.

Commands: status, log, diff, changes, history, locks, deps, workitems, compare.
"""

import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import (
    ApiClient,
    BranchEndpoints,
    ConfigurationEndpoints,
    DependencyEndpoints,
    MarketplaceEndpoints,
    OrganizationEndpoints,
    RepoEndpoints,
    SourceControlEndpoints,
    WorkitemEndpoints,
)
from dxs.core.auth import require_auth
from dxs.core.output.yaml_fmt import LiteralString
from dxs.utils.errors import ValidationError
from dxs.utils.responses import list_response, single
from dxs.utils.restricted import check_restricted_mode_for_option

# Patterns for extracting work item IDs from commit messages
_WORKITEM_PATTERNS = [
    re.compile(r"\[(\d{5,6})\]"),  # [235423]
    re.compile(r"DevOps:\s*(\d{5,6})", re.IGNORECASE),  # DevOps: 235423
    re.compile(r"^(\d{5,6})[\s:/-]"),  # 235423: at start of line
    re.compile(r"#(\d{5,6})(?:\D|$)"),  # #235423
]


def _count_diff_lines(lines: list[str]) -> tuple[int, int]:
    """Count added and removed lines in a unified diff.

    Args:
        lines: List of diff lines (from splitlines() or difflib output)

    Returns:
        Tuple of (lines_added, lines_removed)
    """
    added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
    return added, removed


def _config_endpoint(app_id: int, config_type: str, config_id: int) -> str:
    """Build API endpoint for fetching a configuration."""
    return f"/applications/{app_id}/{config_type}configurations/{config_id}"


def _extract_config_content(data: dict | list | None) -> dict | list | None:
    """Extract config content from API response (handles json/config keys)."""
    if isinstance(data, dict):
        return data.get("json") or data.get("config") or data
    return data


def _parse_date(date_str: str) -> datetime:
    """Parse a date string in various formats to datetime.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If the date string cannot be parsed
    """
    # Handle microseconds with more than 6 digits by truncating
    # The API sometimes returns 7 digits (e.g., "2025-12-07T17:47:43.9482229+00:00")
    if "." in date_str:
        try:
            # Find the microseconds part and truncate to 6 digits
            parts = date_str.split(".")
            if len(parts) == 2:
                # parts[1] might be like "9482229+00:00" or "948222"
                frac_part = parts[1]
                # Find where the timezone starts (if present)
                tz_start = -1
                for i, c in enumerate(frac_part):
                    if c in "+-Z":
                        tz_start = i
                        break
                if tz_start > 0:
                    # Truncate microseconds to 6 digits
                    micros = frac_part[:tz_start][:6].ljust(6, "0")
                    tz = frac_part[tz_start:]
                    date_str = f"{parts[0]}.{micros}{tz}"
                elif tz_start == 0:
                    # No microseconds, just timezone (e.g., ".+00:00")
                    # This is malformed but try to handle it
                    date_str = f"{parts[0]}{frac_part}"
                else:
                    # No timezone, just truncate microseconds
                    micros = frac_part[:6].ljust(6, "0")
                    date_str = f"{parts[0]}.{micros}"
        except (IndexError, TypeError):
            # If string manipulation fails, try parsing as-is
            pass

    # Try full ISO format first
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 2025-12-07T17:47:43.948222+00:00
        "%Y-%m-%dT%H:%M:%S%z",  # 2025-12-07T17:47:43+00:00
        "%Y-%m-%dT%H:%M:%S.%f",  # 2025-12-07T17:47:43.948222
        "%Y-%m-%dT%H:%M:%S",  # 2025-12-07T17:47:43
        "%Y-%m-%d",  # 2025-12-07
    ]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")


def _filter_commits_by_date(
    commits: list[dict],
    from_date: str | None,
    to_date: str | None,
) -> list[dict]:
    """Filter commits by date range.

    Args:
        commits: List of commit dictionaries with 'commitDate' field
        from_date: Only include commits after this date (exclusive)
        to_date: Only include commits before or on this date (inclusive)

    Returns:
        Filtered list of commits
    """
    if not from_date and not to_date:
        return commits

    from_dt = _parse_date(from_date) if from_date else None
    to_dt = _parse_date(to_date) if to_date else None

    # If to_date is just a date (no time), extend to end of day
    if to_date and "T" not in to_date and to_dt is not None:
        to_dt = to_dt.replace(hour=23, minute=59, second=59)

    # Make timezone-naive for comparison
    if from_dt and from_dt.tzinfo is not None:
        from_dt = from_dt.replace(tzinfo=None)
    if to_dt and to_dt.tzinfo is not None:
        to_dt = to_dt.replace(tzinfo=None)

    filtered = []
    for commit in commits:
        commit_date_str = commit.get("commitDate")
        if not commit_date_str:
            continue

        try:
            commit_dt = _parse_date(commit_date_str)

            # Make timezone-naive for comparison
            if commit_dt.tzinfo is not None:
                commit_dt = commit_dt.replace(tzinfo=None)

            # Check date range (from is exclusive, to is inclusive)
            if from_dt and commit_dt <= from_dt:
                continue
            if to_dt and commit_dt > to_dt:
                continue

            filtered.append(commit)
        except ValueError:
            # If we can't parse the date, include the commit
            filtered.append(commit)

    return filtered


def _extract_workitem_ids_from_commits(commits: list[dict]) -> list[dict]:
    """Extract work item IDs from commit title and message.

    Args:
        commits: List of commit dictionaries

    Returns:
        List of commits with 'work_item_ids' field added
    """
    result = []
    for commit in commits:
        commit_copy = dict(commit)
        ids = set()

        # Search in title and message
        for field in ["commitTitle", "commitMessage"]:
            text = commit.get(field, "") or ""
            for pattern in _WORKITEM_PATTERNS:
                for match in pattern.finditer(text):
                    ids.add(int(match.group(1)))

        commit_copy["work_item_ids"] = sorted(ids) if ids else []
        result.append(commit_copy)

    return result


@click.group()
def source() -> None:
    """Source control commands.

    View source control information for branches and configurations.
    These commands are read-only and designed for LLM analysis.

    \b
    Use cases:
        - Generate commit messages based on pending changes
        - Create release notes from commit history
        - Review configuration version history
    """
    pass


@source.command()
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID (overrides global --branch)",
)
@click.option(
    "--repo",
    "-r",
    type=int,
    help="Repository ID (overrides global --repo)",
)
@pass_context
@require_auth
def status(ctx: DxsContext, branch: int | None, repo: int | None) -> None:
    """Show current source control status.

    Displays current locks and pending changes for a branch.

    \b
    Example:
        dxs source status --branch 100
        dxs source status --repo 10
    """
    branch_id = branch or ctx.branch
    repo_id = repo or ctx.repo

    if not repo_id and not branch_id:
        raise ValidationError(
            message="Branch ID or Repository ID is required.",
            code="DXS-VAL-002",
            suggestions=[
                "Provide --branch flag: dxs source status --branch 100",
                "Provide --repo flag: dxs source status --repo 10",
                "Set environment variable: export DXS_BRANCH=100",
            ],
        )

    client = ApiClient()
    result = {}

    # Get locks (requires repo_id)
    if repo_id:
        ctx.log(f"Fetching locks for repository {repo_id}...")
        locks_data = client.get(SourceControlEndpoints.locks(repo_id))
        result["locks"] = locks_data

    # Get feature branch changes if branch_id provided
    if branch_id:
        ctx.log(f"Fetching changes for branch {branch_id}...")
        try:
            changes_data = client.get(SourceControlEndpoints.feature_branch_changes(branch_id))
            result["pending_changes"] = changes_data
        except Exception:
            # Branch might not be a feature branch
            result["pending_changes"] = None

    result["branch_id"] = branch_id
    result["repository_id"] = repo_id

    ctx.output(
        single(
            item=result,
            semantic_key="status",
            branch_id=branch_id,
            repository_id=repo_id,
        )
    )


@source.command()
@click.option(
    "--repo",
    "-r",
    type=int,
    help="Repository ID (for repository-level history)",
)
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID (for branch-specific history)",
)
@click.option(
    "--branches",
    type=str,
    help="Comma-separated list of branch IDs for batch fetching (e.g., 63332,63299,62932)",
)
@click.option(
    "--all-repos",
    is_flag=True,
    default=False,
    help="Search commits across all repositories (ignores --repo and --branch)",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=20,
    help="Maximum number of commits to return per branch (default: 20)",
)
@click.option(
    "--from-date",
    type=str,
    help="Only include commits after this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--to-date",
    type=str,
    help="Only include commits before this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@pass_context
@require_auth
def log(
    ctx: DxsContext,
    repo: int | None,
    branch: int | None,
    branches: str | None,
    all_repos: bool,
    limit: int,
    from_date: str | None,
    to_date: str | None,
) -> None:
    """Show commit history.

    Displays commit history for a repository or specific branch.
    Use --from-date and --to-date to filter commits by date range.
    Use --branches for batch fetching logs from multiple branches at once.
    Use --all-repos to search commits across all repositories.

    \b
    Examples:
        dxs source log --repo 10 --limit 20
        dxs source log --branch 100
        dxs source log --repo 10 --from-date 2025-12-07 --to-date 2025-12-16
        dxs source log --branches 63332,63299,62932 --limit 10
        dxs source log --all-repos --from-date 2025-12-13 --limit 50
    """
    # Handle batch mode with --branches
    if branches:
        _log_batch(ctx, branches, limit, from_date, to_date)
        return

    client = ApiClient()

    # Handle --all-repos mode
    if all_repos:
        ctx.log("Fetching all repositories...")
        repos = client.get(RepoEndpoints.list())
        if not isinstance(repos, list):
            repos = [repos] if repos else []

        ctx.log(f"Fetching commit history from {len(repos)} repositories...")
        history_data = []
        repos_with_commits = 0

        for repo_data in repos:
            rid = repo_data.get("id")
            rname = repo_data.get("name", f"Repo {rid}")
            try:
                repo_commits = client.get(SourceControlEndpoints.history(rid))
                if not isinstance(repo_commits, list):
                    repo_commits = [repo_commits] if repo_commits else []

                # Add repo context to each commit
                for c in repo_commits:
                    c["repositoryId"] = rid
                    c["repositoryName"] = rname

                if repo_commits:
                    repos_with_commits += 1
                history_data.extend(repo_commits)
            except Exception as e:
                ctx.debug(f"Failed to fetch commits for repo {rid}: {e}")

        ctx.log(f"Found {len(history_data)} commits across {repos_with_commits} repositories")

        # Apply date filtering (client-side)
        if from_date or to_date:
            history_data = _filter_commits_by_date(history_data, from_date, to_date)

        # Sort by commit date descending
        history_data.sort(key=lambda x: x.get("commitDate", ""), reverse=True)

        # Parse work item IDs from commit messages
        history_data = _extract_workitem_ids_from_commits(history_data)

        # Apply limit after date filtering
        if limit > 0:
            history_data = history_data[:limit]

        ctx.output(
            list_response(
                items=history_data,
                semantic_key="commits",
                all_repos=True,
                repository_count=len(repos),
                limit=limit,
                from_date=from_date,
                to_date=to_date,
            )
        )
        return

    repo_id = repo or ctx.repo
    branch_id = branch or ctx.branch

    if not repo_id and not branch_id:
        raise ValidationError(
            message="Either --repo, --branch, --branches, or --all-repos is required.",
            code="DXS-VAL-001",
            suggestions=[
                "Use --repo for repository history: dxs source log --repo 10",
                "Use --branch for branch history: dxs source log --branch 100",
                "Use --branches for batch fetching: dxs source log --branches 100,101,102",
                "Use --all-repos for all repos: dxs source log --all-repos --from-date 2025-12-13",
            ],
        )

    if branch_id:
        # Get branch-specific history
        ctx.log(f"Fetching commit history for branch {branch_id}...")
        history_data = client.get(SourceControlEndpoints.branch_history(branch_id))
    else:
        # Get repository-level history (repo_id is guaranteed non-None here by validation above)
        assert repo_id is not None
        ctx.log(f"Fetching commit history for repository {repo_id}...")
        history_data = client.get(SourceControlEndpoints.history(repo_id))

    # Normalize to list
    if not isinstance(history_data, list):
        history_data = [history_data] if history_data else []

    # Apply date filtering (client-side)
    if from_date or to_date:
        history_data = _filter_commits_by_date(history_data, from_date, to_date)

    # Parse work item IDs from commit messages
    history_data = _extract_workitem_ids_from_commits(history_data)

    # Apply limit after date filtering
    if limit > 0:
        history_data = history_data[:limit]

    ctx.output(
        list_response(
            items=history_data,
            semantic_key="commits",
            branch_id=branch_id,
            repository_id=repo_id,
            limit=limit,
            from_date=from_date,
            to_date=to_date,
        )
    )


def _log_batch(
    ctx: DxsContext,
    branches: str,
    limit: int,
    from_date: str | None,
    to_date: str | None,
) -> None:
    """Fetch commit logs for multiple branches in batch mode.

    Args:
        ctx: CLI context
        branches: Comma-separated list of branch IDs
        limit: Maximum commits per branch
        from_date: Filter commits after this date
        to_date: Filter commits before this date
    """
    # Parse branch IDs from comma-separated string
    try:
        branch_ids = [int(b.strip()) for b in branches.split(",") if b.strip()]
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid branch ID in list: {e}",
            code="DXS-VAL-001",
            suggestions=["Use comma-separated integers: --branches 100,101,102"],
        ) from e

    if not branch_ids:
        raise ValidationError(
            message="No valid branch IDs provided",
            code="DXS-VAL-001",
            suggestions=["Provide at least one branch ID: --branches 100"],
        )

    client = ApiClient()
    branch_logs = []
    total_commits = 0

    ctx.log(f"Fetching commit history for {len(branch_ids)} branches...")

    for branch_id in branch_ids:
        ctx.log(f"  Fetching branch {branch_id}...")

        try:
            # Get branch info for the name
            branch_info = client.get(BranchEndpoints.get(branch_id))
            branch_name = (
                branch_info.get("name") or branch_info.get("referenceName") or f"Branch {branch_id}"
            )

            # Get commit history
            history_data = client.get(SourceControlEndpoints.branch_history(branch_id))

            # Normalize to list
            if not isinstance(history_data, list):
                history_data = [history_data] if history_data else []

            # Apply date filtering
            if from_date or to_date:
                history_data = _filter_commits_by_date(history_data, from_date, to_date)

            # Parse work item IDs
            history_data = _extract_workitem_ids_from_commits(history_data)

            # Apply limit
            if limit > 0:
                history_data = history_data[:limit]

            total_commits += len(history_data)

            branch_logs.append(
                {
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                    "commit_count": len(history_data),
                    "commits": history_data,
                }
            )

        except Exception as e:
            # Include error info but continue with other branches
            branch_logs.append(
                {
                    "branch_id": branch_id,
                    "branch_name": f"Branch {branch_id}",
                    "error": str(e),
                    "commits": [],
                }
            )

    ctx.output(
        list_response(
            items=branch_logs,
            semantic_key="branch_logs",
            branch_count=len(branch_ids),
            total_commits=total_commits,
            limit_per_branch=limit,
            from_date=from_date,
            to_date=to_date,
        )
    )


@source.command()
@click.argument("reference_name")
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID",
)
@click.option(
    "--diff",
    "show_diff",
    is_flag=True,
    default=False,
    help="Show JSON diffs between versions",
)
@click.option(
    "--full",
    "show_full",
    is_flag=True,
    default=False,
    help="Include full JSON content at each version (with --diff)",
)
@pass_context
@require_auth
def history(
    ctx: DxsContext,
    reference_name: str,
    branch: int | None,
    show_diff: bool,
    show_full: bool,
) -> None:
    """Show version history for a specific configuration.

    Displays all commits that modified a specific configuration.
    Use --diff to see JSON diffs between versions.

    \b
    Arguments:
        REFERENCE_NAME  Configuration reference name (e.g., userGrid, loginForm)

    \b
    Options:
        --branch ID   Branch ID
        --diff        Show JSON diffs between versions
        --full        Include full JSON content (with --diff)

    \b
    Examples:
        dxs source history userGrid --branch 100
        dxs source history userGrid --branch 100 --diff
        dxs source history userGrid --branch 100 --diff --full
    """
    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH environment variable.",
            code="DXS-VAL-002",
            suggestions=[
                "Provide --branch flag: dxs source history userGrid --branch 100",
                "Set environment variable: export DXS_BRANCH=100",
            ],
        )

    client = ApiClient()
    ctx.log(f"Fetching history for configuration '{reference_name}' in branch {branch_id}...")

    history_data = client.get(
        SourceControlEndpoints.configuration_history(branch_id, reference_name)
    )

    # Normalize to list
    if not isinstance(history_data, list):
        history_data = [history_data] if history_data else []

    # If diff requested, fetch content and compute diffs
    if show_diff and len(history_data) > 1:
        ctx.log("Computing diffs between versions...")
        history_data = _add_diffs_to_history(
            client, branch_id, reference_name, history_data, show_full, ctx
        )

    ctx.output(
        list_response(
            items=history_data,
            semantic_key="versions",
            reference_name=reference_name,
            branch_id=branch_id,
            has_diffs=show_diff,
        )
    )


# Fields that always change but aren't meaningful for diffs
_DIFF_EXCLUDE_FIELDS = {"id", "version", "createdDate", "modifiedDate", "commitDate"}


def _clean_for_diff(
    obj: dict | list | object,
    parent_key: str | None = None,
    omit_code: bool = False,
) -> dict | list | object:
    """Remove noise fields from object for cleaner diffs.

    Args:
        obj: Object to clean
        parent_key: Key of the parent object (for context)
        omit_code: If True, replace code in executeCodeConfig with placeholder
                   (use when code is being diffed separately for flow configs)
    """
    if isinstance(obj, dict):
        result: dict[str, Any] = {}
        for k, v in obj.items():
            # Skip noise fields
            if k in _DIFF_EXCLUDE_FIELDS:
                continue
            # Skip 'code' inside executeCodeConfig only when diffing separately
            if omit_code and k == "code" and parent_key == "executeCodeConfig":
                result[k] = "[code omitted - see code_diff]"
                continue
            result[k] = _clean_for_diff(v, parent_key=k, omit_code=omit_code)
        return result
    elif isinstance(obj, list):
        return [_clean_for_diff(item, parent_key=parent_key, omit_code=omit_code) for item in obj]
    return obj


def _format_code(code: str) -> str:
    """Format code by normalizing line endings and converting tabs to spaces."""
    # Replace Windows-style CRLF with LF, then any remaining CR
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    # Replace tabs with 4 spaces (tabs cause YAML to use quoted strings instead of literal blocks)
    code = code.replace("\t", "    ")
    return code


def _extract_code_diff(
    old_content: dict[Any, Any] | list[Any] | None, new_content: dict[Any, Any] | list[Any] | None
) -> str | None:
    """Extract code from flow config nodes and return diff.

    Args:
        old_content: Older flow configuration content
        new_content: Newer flow configuration content

    Returns:
        Unified diff string if code changed, None otherwise
    """
    from difflib import unified_diff

    if not old_content or not new_content:
        return None

    # Only dicts have nodes with code
    if not isinstance(old_content, dict) or not isinstance(new_content, dict):
        return None

    # Find code in nodes - check all nodes for executeCodeConfig
    # Structure: nodes[].stepConfig.executeCodeConfig.code
    old_codes = []
    new_codes = []

    for node in old_content.get("nodes", []):
        code = node.get("stepConfig", {}).get("executeCodeConfig", {}).get("code")
        if code:
            node_id = node.get("id", "unnamed")
            # Format code: normalize line endings
            formatted_code = _format_code(code)
            old_codes.append((node_id, formatted_code))

    for node in new_content.get("nodes", []):
        code = node.get("stepConfig", {}).get("executeCodeConfig", {}).get("code")
        if code:
            node_id = node.get("id", "unnamed")
            formatted_code = _format_code(code)
            new_codes.append((node_id, formatted_code))

    # Simple case: one code block in each - compare them directly
    if len(old_codes) == 1 and len(new_codes) == 1:
        old_code = old_codes[0][1]
        new_code = new_codes[0][1]
        if old_code != new_code:
            # Split into lines for diffing (without keepends so we control line endings)
            old_lines = old_code.splitlines(keepends=True)
            new_lines = new_code.splitlines(keepends=True)
            # Ensure all lines end with \n for consistent diff output
            old_lines = [line if line.endswith("\n") else line + "\n" for line in old_lines]
            new_lines = [line if line.endswith("\n") else line + "\n" for line in new_lines]

            diff_lines = list(
                unified_diff(
                    old_lines,
                    new_lines,
                    fromfile="old",
                    tofile="new",
                    n=3,
                )
            )
            if diff_lines:
                # Strip trailing whitespace (causes YAML to use quoted style)
                # But preserve the newlines
                cleaned_lines = [
                    line.rstrip() + "\n" if line.endswith("\n") else line.rstrip()
                    for line in diff_lines
                ]
                result = "".join(cleaned_lines)
                # Ensure trailing newline for proper YAML literal block
                if not result.endswith("\n"):
                    result += "\n"
                return result

    return None


def _add_diffs_to_history(
    client: ApiClient,
    branch_id: int,
    reference_name: str,
    history_data: list,
    include_full: bool,
    ctx: DxsContext,
) -> list:
    """Add JSON diffs between consecutive versions.

    Args:
        client: API client
        branch_id: Branch ID
        reference_name: Configuration reference name
        history_data: List of history items
        include_full: Whether to include full JSON content
        ctx: CLI context for logging

    Returns:
        History data with diffs added
    """
    import json
    from difflib import unified_diff

    # Sort by commit date descending (most recent first)
    sorted_history = sorted(
        history_data,
        key=lambda x: x.get("commitDate", ""),
        reverse=True,
    )

    result = []
    prev_content = None

    for i, item in enumerate(sorted_history):
        config_id = item.get("configId")
        item_with_diff = dict(item)

        # Try to fetch config content
        current_content = None
        if config_id:
            try:
                # Determine config type from the history item
                config_type = item.get("configType", "").lower()
                # Use the applicationId from this history item, not the queried branch
                # Each historical config belongs to its own branch (commit snapshot)
                item_app_id = item.get("applicationId", branch_id)
                if config_type:
                    endpoint = (
                        f"/applications/{item_app_id}/{config_type}configurations/{config_id}"
                    )
                    content_data = client.get(endpoint)
                    # API returns 'json' key for flow configs, not 'config'
                    if isinstance(content_data, dict):
                        current_content = content_data.get("json") or content_data.get("config")
                    else:
                        current_content = content_data
            except Exception as e:
                ctx.debug(f"Could not fetch config {config_id} from app {item_app_id}: {e}")

        # Add full content if requested
        if include_full and current_content:
            item_with_diff["content"] = current_content

        # Compute diff with previous version
        config_type = item.get("configType", "").lower()
        if prev_content is not None and current_content is not None:
            try:
                has_json_changes = False
                has_code_changes = False

                # For flow configs, extract code diff first (before cleaning)
                if config_type == "flow":
                    code_diff = _extract_code_diff(current_content, prev_content)
                    if code_diff:
                        item_with_diff["code_diff"] = LiteralString(code_diff)
                        has_code_changes = True

                        # Add code diff summary
                        code_diff_lines = code_diff.splitlines()
                        code_added, code_removed = _count_diff_lines(code_diff_lines)
                        item_with_diff["code_diff_summary"] = {
                            "lines_added": code_added,
                            "lines_removed": code_removed,
                        }

                # Clean noise fields for more meaningful JSON diffs
                # Only omit code for flow configs (where it's diffed separately)
                omit_code = config_type == "flow"
                clean_old = _clean_for_diff(current_content, omit_code=omit_code)
                clean_new = _clean_for_diff(prev_content, omit_code=omit_code)

                old_str = json.dumps(clean_old, indent=2, sort_keys=True)
                new_str = json.dumps(clean_new, indent=2, sort_keys=True)

                diff_lines = list(
                    unified_diff(
                        old_str.splitlines(keepends=True),
                        new_str.splitlines(keepends=True),
                        fromfile=f"v{i + 1} (older)",
                        tofile=f"v{i} (newer)",
                        n=3,
                    )
                )

                if diff_lines:
                    diff_text = "".join(diff_lines)
                    # Use LiteralString for clean multi-line YAML output
                    item_with_diff["diff"] = LiteralString(diff_text)
                    has_json_changes = True

                    # Add summary stats
                    added, removed = _count_diff_lines(diff_lines)
                    item_with_diff["diff_summary"] = {
                        "lines_added": added,
                        "lines_removed": removed,
                    }
                else:
                    item_with_diff["diff"] = None

                # Mark as having changes if either JSON or code changed
                item_with_diff["has_changes"] = has_json_changes or has_code_changes

            except Exception as e:
                ctx.debug(f"Could not compute diff: {e}")
                item_with_diff["diff"] = None
                item_with_diff["diff_error"] = str(e)
        else:
            item_with_diff["diff"] = None
            if i == 0:
                item_with_diff["diff_note"] = "Most recent version (nothing to diff)"
            else:
                item_with_diff["diff_note"] = "Could not fetch content for diff"

        result.append(item_with_diff)
        prev_content = current_content

    return result


def _add_diffs_to_changes(
    client: ApiClient,
    feature_branch_id: int,
    base_branch_id: int | None,
    config_changes: list,
    ctx: DxsContext,
    is_committed: bool = False,
) -> list:
    """Add diffs between feature branch and base branch for each changed config.

    Args:
        client: API client
        feature_branch_id: Feature branch ID
        base_branch_id: Base branch ID
        config_changes: List of changed configurations
        ctx: CLI context for logging
        is_committed: Whether this is a committed branch (WorkspaceHistory)

    Returns:
        Config changes with diffs added
    """
    import json
    from difflib import unified_diff

    if not base_branch_id:
        ctx.log("Warning: No base branch ID available, cannot compute diffs")
        return config_changes

    result = []
    for change in config_changes:
        change_with_diff = dict(change)
        config_type = change.get("configurationTypeId", "").lower()
        feature_config_id = change.get("id")
        base_config_id = change.get("baseConfigId")
        mod_type = change.get("modificationTypeId", "").lower()
        ref_name = change.get("referenceName", "unknown")

        # Skip if no config type or IDs
        if not config_type or not feature_config_id:
            change_with_diff["diff"] = None
            change_with_diff["diff_note"] = "Missing configuration metadata"
            result.append(change_with_diff)
            continue

        # For deleted configs, no diff needed
        if mod_type == "delete":
            change_with_diff["diff"] = None
            change_with_diff["diff_note"] = "Configuration deleted"
            result.append(change_with_diff)
            continue

        # For new configs, show the full content as "added"
        if mod_type == "add" or not base_config_id:
            try:
                endpoint = _config_endpoint(feature_branch_id, config_type, feature_config_id)
                feature_content = client.get(endpoint)
                feature_content = _extract_config_content(feature_content)

                # For new configs, don't omit code - show full content
                clean_feature = _clean_for_diff(feature_content, omit_code=False)
                feature_str = json.dumps(clean_feature, indent=2, sort_keys=True)
                lines = feature_str.splitlines(keepends=True)
                diff_lines = [f"+{line}" for line in lines]
                diff_text = f"--- /dev/null\n+++ {ref_name}\n" + "".join(diff_lines)
                change_with_diff["diff"] = LiteralString(diff_text)
                change_with_diff["diff_summary"] = {
                    "lines_added": len(lines),
                    "lines_removed": 0,
                }
            except Exception as e:
                ctx.debug(f"Could not fetch new config {feature_config_id}: {e}")
                change_with_diff["diff"] = None
                change_with_diff["diff_error"] = str(e)
            result.append(change_with_diff)
            continue

        # For committed branches, use history to find the previous version
        if is_committed:
            try:
                diff_result = _get_committed_diff(
                    client, feature_branch_id, ref_name, config_type, ctx
                )
                change_with_diff.update(diff_result)
            except Exception as e:
                ctx.debug(f"Could not compute committed diff for {ref_name}: {e}")
                change_with_diff["diff"] = None
                change_with_diff["diff_error"] = str(e)
            result.append(change_with_diff)
            continue

        # For updates on feature branches, diff between base and feature
        try:
            # Fetch feature branch config
            feature_endpoint = _config_endpoint(feature_branch_id, config_type, feature_config_id)
            feature_content = client.get(feature_endpoint)
            feature_content = _extract_config_content(feature_content)

            # Fetch base branch config
            base_endpoint = _config_endpoint(base_branch_id, config_type, base_config_id)
            base_content = client.get(base_endpoint)
            base_content = _extract_config_content(base_content)

            has_json_changes = False
            has_code_changes = False

            # For flow configs, extract code diff first
            if config_type == "flow":
                code_diff = _extract_code_diff(base_content, feature_content)
                if code_diff:
                    change_with_diff["code_diff"] = LiteralString(code_diff)
                    has_code_changes = True
                    code_diff_lines = code_diff.splitlines()
                    code_added, code_removed = _count_diff_lines(code_diff_lines)
                    change_with_diff["code_diff_summary"] = {
                        "lines_added": code_added,
                        "lines_removed": code_removed,
                    }

            # Clean and diff JSON
            # Only omit code for flow configs (where it's diffed separately)
            omit_code = config_type == "flow"
            clean_base = _clean_for_diff(base_content, omit_code=omit_code)
            clean_feature = _clean_for_diff(feature_content, omit_code=omit_code)

            base_str = json.dumps(clean_base, indent=2, sort_keys=True)
            feature_str = json.dumps(clean_feature, indent=2, sort_keys=True)

            diff_lines = list(
                unified_diff(
                    base_str.splitlines(keepends=True),
                    feature_str.splitlines(keepends=True),
                    fromfile=f"base ({ref_name})",
                    tofile=f"feature ({ref_name})",
                    n=3,
                )
            )

            if diff_lines:
                diff_text = "".join(diff_lines)
                change_with_diff["diff"] = LiteralString(diff_text)
                has_json_changes = True
                added, removed = _count_diff_lines(diff_lines)
                change_with_diff["diff_summary"] = {
                    "lines_added": added,
                    "lines_removed": removed,
                }
            else:
                change_with_diff["diff"] = None
                change_with_diff["diff_note"] = "No differences found (metadata-only change)"

            change_with_diff["has_changes"] = has_json_changes or has_code_changes

        except Exception as e:
            ctx.debug(f"Could not compute diff for {ref_name}: {e}")
            change_with_diff["diff"] = None
            change_with_diff["diff_error"] = str(e)

        result.append(change_with_diff)

    return result


def _get_committed_diff(
    client: ApiClient,
    branch_id: int,
    ref_name: str,
    config_type: str,
    ctx: DxsContext,
) -> dict:
    """Get diff for a committed branch by comparing to the previous version in history.

    Args:
        client: API client
        branch_id: The committed branch ID
        ref_name: Configuration reference name
        config_type: Configuration type (editor, flow, etc.)
        ctx: CLI context for logging

    Returns:
        Dict with diff, diff_summary, and has_changes keys
    """
    import json
    from difflib import unified_diff

    result: dict[str, Any] = {}

    # Fetch the configuration history
    history_endpoint = SourceControlEndpoints.configuration_history(branch_id, ref_name)
    history_data = client.get(history_endpoint)

    if not isinstance(history_data, list):
        history_data = [history_data] if history_data else []

    if len(history_data) < 2:
        result["diff"] = None
        result["diff_note"] = "No previous version available for comparison"
        result["has_changes"] = False
        return result

    # Sort by commit date descending (most recent first)
    sorted_history = sorted(
        history_data,
        key=lambda x: x.get("commitDate", ""),
        reverse=True,
    )

    # Get the current (this commit) and previous versions
    current_item = sorted_history[0]
    previous_item = sorted_history[1]

    current_config_id = current_item.get("configId")
    current_app_id = current_item.get("applicationId", branch_id)
    previous_config_id = previous_item.get("configId")
    previous_app_id = previous_item.get("applicationId")

    if not current_config_id or not previous_config_id:
        result["diff"] = None
        result["diff_note"] = "Missing config IDs for diff"
        result["has_changes"] = False
        return result

    # Fetch both config contents
    current_endpoint = _config_endpoint(current_app_id, config_type, current_config_id)
    current_content = client.get(current_endpoint)
    current_content = _extract_config_content(current_content)

    previous_endpoint = _config_endpoint(previous_app_id, config_type, previous_config_id)
    previous_content = client.get(previous_endpoint)
    previous_content = _extract_config_content(previous_content)

    has_json_changes = False
    has_code_changes = False

    # For flow configs, extract code diff first
    if config_type == "flow":
        code_diff = _extract_code_diff(previous_content, current_content)
        if code_diff:
            result["code_diff"] = LiteralString(code_diff)
            has_code_changes = True
            code_diff_lines = code_diff.splitlines()
            code_added, code_removed = _count_diff_lines(code_diff_lines)
            result["code_diff_summary"] = {
                "lines_added": code_added,
                "lines_removed": code_removed,
            }

    # Clean and diff JSON
    # Only omit code for flow configs (where it's diffed separately)
    omit_code = config_type == "flow"
    clean_previous = _clean_for_diff(previous_content, omit_code=omit_code)
    clean_current = _clean_for_diff(current_content, omit_code=omit_code)

    previous_str = json.dumps(clean_previous, indent=2, sort_keys=True)
    current_str = json.dumps(clean_current, indent=2, sort_keys=True)

    diff_lines = list(
        unified_diff(
            previous_str.splitlines(keepends=True),
            current_str.splitlines(keepends=True),
            fromfile=f"previous ({ref_name})",
            tofile=f"current ({ref_name})",
            n=3,
        )
    )

    if diff_lines:
        diff_text = "".join(diff_lines)
        result["diff"] = LiteralString(diff_text)
        has_json_changes = True
        added, removed = _count_diff_lines(diff_lines)
        result["diff_summary"] = {
            "lines_added": added,
            "lines_removed": removed,
        }
    else:
        result["diff"] = None
        result["diff_note"] = "No differences found (metadata-only change)"

    result["has_changes"] = has_json_changes or has_code_changes
    result["compared_to_commit"] = previous_item.get("commitTitle", "unknown")

    return result


def _fetch_and_diff_entity(
    client: ApiClient,
    feature_branch_id: int,
    base_branch_id: int,
    entity_name: str,
    fetch_endpoint_fn: Callable[[int], str],
    sort_key_fn: Callable[[Any], str],
    ctx: DxsContext,
) -> dict[str, Any]:
    """Generic helper to fetch and diff an entity type between branches.

    Args:
        client: API client
        feature_branch_id: Feature branch ID
        base_branch_id: Base branch ID
        entity_name: Name of the entity type (for logging)
        fetch_endpoint_fn: Function that takes branch_id and returns endpoint
        sort_key_fn: Function that takes an item and returns its sort key
        ctx: CLI context for logging

    Returns:
        Dict with diff, diff_summary, has_changes, and changes_summary keys
    """
    import json
    from difflib import unified_diff

    result: dict[str, Any] = {
        "has_changes": False,
        "diff": None,
        "diff_summary": None,
        "changes_summary": None,
    }

    try:
        # Fetch from both branches
        ctx.log(f"  Fetching {entity_name} from feature branch...")
        feature_data = client.get(fetch_endpoint_fn(feature_branch_id))
        if not isinstance(feature_data, list):
            feature_data = [feature_data] if feature_data else []

        ctx.log(f"  Fetching {entity_name} from base branch...")
        base_data = client.get(fetch_endpoint_fn(base_branch_id))
        if not isinstance(base_data, list):
            base_data = [base_data] if base_data else []

        # Sort both lists for consistent comparison
        feature_sorted = sorted(feature_data, key=sort_key_fn)
        base_sorted = sorted(base_data, key=sort_key_fn)

        # Clean for diff (remove noise fields)
        feature_clean = [_clean_for_diff(item) for item in feature_sorted]
        base_clean = [_clean_for_diff(item) for item in base_sorted]

        # Compute changes summary by comparing keys
        feature_keys = {sort_key_fn(item) for item in feature_data}
        base_keys = {sort_key_fn(item) for item in base_data}

        added_keys = list(feature_keys - base_keys)
        removed_keys = list(base_keys - feature_keys)
        common_keys = feature_keys & base_keys

        # Find modified items (same key, different content)
        feature_by_key = {sort_key_fn(item): item for item in feature_data}
        base_by_key = {sort_key_fn(item): item for item in base_data}
        modified_keys = []
        for key in common_keys:
            feature_item = _clean_for_diff(feature_by_key[key])
            base_item = _clean_for_diff(base_by_key[key])
            if feature_item != base_item:
                modified_keys.append(key)

        result["changes_summary"] = {
            "added": sorted(added_keys),
            "removed": sorted(removed_keys),
            "modified": sorted(modified_keys),
        }

        # Generate unified diff
        base_str = json.dumps(base_clean, indent=2, sort_keys=True)
        feature_str = json.dumps(feature_clean, indent=2, sort_keys=True)

        diff_lines = list(
            unified_diff(
                base_str.splitlines(keepends=True),
                feature_str.splitlines(keepends=True),
                fromfile=f"base ({entity_name})",
                tofile=f"feature ({entity_name})",
                n=3,
            )
        )

        if diff_lines:
            diff_text = "".join(diff_lines)
            result["diff"] = LiteralString(diff_text)
            result["has_changes"] = True
            added, removed = _count_diff_lines(diff_lines)
            result["diff_summary"] = {
                "lines_added": added,
                "lines_removed": removed,
            }
        else:
            result["diff_note"] = "No differences found"

    except Exception as e:
        ctx.debug(f"Could not compute {entity_name} diff: {e}")
        result["diff_error"] = str(e)

    return result


def _fetch_and_diff_entity_from_history(
    client: ApiClient,
    branch_id: int,
    entity_name: str,
    history_endpoint_fn: Callable[[int], str],
    fetch_endpoint_fn: Callable[[int], str],
    sort_key_fn: Callable[[Any], str],
    ctx: DxsContext,
) -> dict[str, Any]:
    """Fetch and diff an entity type for a committed branch using history.

    Args:
        client: API client
        branch_id: The committed branch ID
        entity_name: Name of the entity type (for logging)
        history_endpoint_fn: Function that takes branch_id and returns history endpoint
        fetch_endpoint_fn: Function that takes branch_id and returns fetch endpoint
        sort_key_fn: Function that takes an item and returns its sort key
        ctx: CLI context for logging

    Returns:
        Dict with diff, diff_summary, has_changes, and changes_summary keys
    """
    import json
    from difflib import unified_diff

    result: dict[str, Any] = {
        "has_changes": False,
        "diff": None,
        "diff_summary": None,
        "changes_summary": None,
    }

    try:
        # Fetch history
        ctx.log(f"  Fetching {entity_name} history...")
        history_data = client.get(history_endpoint_fn(branch_id))
        if not isinstance(history_data, list):
            history_data = [history_data] if history_data else []

        if len(history_data) < 2:
            result["diff_note"] = "No previous version available for comparison"
            return result

        # Sort by commit date descending
        sorted_history = sorted(
            history_data,
            key=lambda x: x.get("commitDate", ""),
            reverse=True,
        )

        # Get current and previous application IDs
        current_app_id = sorted_history[0].get("applicationId", branch_id)
        previous_app_id = sorted_history[1].get("applicationId")

        if not previous_app_id:
            result["diff_note"] = "Missing previous application ID"
            return result

        # Fetch content from both versions
        ctx.log(f"  Fetching {entity_name} from current version...")
        current_data = client.get(fetch_endpoint_fn(current_app_id))
        if not isinstance(current_data, list):
            current_data = [current_data] if current_data else []

        ctx.log(f"  Fetching {entity_name} from previous version...")
        previous_data = client.get(fetch_endpoint_fn(previous_app_id))
        if not isinstance(previous_data, list):
            previous_data = [previous_data] if previous_data else []

        # Sort both lists
        current_sorted = sorted(current_data, key=sort_key_fn)
        previous_sorted = sorted(previous_data, key=sort_key_fn)

        # Clean for diff
        current_clean = [_clean_for_diff(item) for item in current_sorted]
        previous_clean = [_clean_for_diff(item) for item in previous_sorted]

        # Compute changes summary
        current_keys = {sort_key_fn(item) for item in current_data}
        previous_keys = {sort_key_fn(item) for item in previous_data}

        added_keys = list(current_keys - previous_keys)
        removed_keys = list(previous_keys - current_keys)
        common_keys = current_keys & previous_keys

        current_by_key = {sort_key_fn(item): item for item in current_data}
        previous_by_key = {sort_key_fn(item): item for item in previous_data}
        modified_keys = []
        for key in common_keys:
            current_item = _clean_for_diff(current_by_key[key])
            previous_item = _clean_for_diff(previous_by_key[key])
            if current_item != previous_item:
                modified_keys.append(key)

        result["changes_summary"] = {
            "added": sorted(added_keys),
            "removed": sorted(removed_keys),
            "modified": sorted(modified_keys),
        }

        # Generate unified diff
        previous_str = json.dumps(previous_clean, indent=2, sort_keys=True)
        current_str = json.dumps(current_clean, indent=2, sort_keys=True)

        diff_lines = list(
            unified_diff(
                previous_str.splitlines(keepends=True),
                current_str.splitlines(keepends=True),
                fromfile=f"previous ({entity_name})",
                tofile=f"current ({entity_name})",
                n=3,
            )
        )

        if diff_lines:
            diff_text = "".join(diff_lines)
            result["diff"] = LiteralString(diff_text)
            result["has_changes"] = True
            added, removed = _count_diff_lines(diff_lines)
            result["diff_summary"] = {
                "lines_added": added,
                "lines_removed": removed,
            }
        else:
            result["diff_note"] = "No differences found"

        result["compared_to_commit"] = sorted_history[1].get("commitTitle", "unknown")

    except Exception as e:
        ctx.debug(f"Could not compute {entity_name} diff: {e}")
        result["diff_error"] = str(e)

    return result


def _fetch_entity_diffs(
    client: ApiClient,
    feature_branch_id: int,
    base_branch_id: int,
    summary: dict,
    ctx: DxsContext,
    is_committed: bool = False,
) -> dict:
    """Fetch diffs for all entity types that have changes.

    Args:
        client: API client
        feature_branch_id: Feature branch ID
        base_branch_id: Base branch ID
        summary: Summary dict with has_* flags
        ctx: CLI context for logging
        is_committed: Whether this is a committed branch

    Returns:
        Dict with entity type keys and diff results
    """
    entity_diffs = {}

    # Define entity configurations
    entity_configs = [
        {
            "key": "replacements",
            "has_key": "has_replacements",
            "name": "replacements",
            "fetch_fn": BranchEndpoints.replacements,
            "history_fn": SourceControlEndpoints.replacements_history,
            "sort_key": lambda x: (
                x.get("referenceName", ""),
                x.get("applicationReferenceName", ""),
            ),
        },
        {
            "key": "settings",
            "has_key": "has_settings",
            "name": "settings",
            "fetch_fn": BranchEndpoints.settings,
            "history_fn": SourceControlEndpoints.settings_and_references_history,
            "sort_key": lambda x: x.get("name", ""),
        },
        {
            "key": "operations",
            "has_key": "has_operations",
            "name": "operations",
            "fetch_fn": BranchEndpoints.operations,
            "history_fn": SourceControlEndpoints.operations_and_roles_history,
            "sort_key": lambda x: x.get("name", ""),
        },
        {
            "key": "roles",
            "has_key": "has_roles",
            "name": "roles",
            "fetch_fn": BranchEndpoints.roles,
            "history_fn": SourceControlEndpoints.operations_and_roles_history,
            "sort_key": lambda x: x.get("organizationRoleId", 0),
        },
        {
            "key": "references",
            "has_key": "has_references",
            "name": "references",
            "fetch_fn": DependencyEndpoints.list,
            "history_fn": SourceControlEndpoints.settings_and_references_history,
            "sort_key": lambda x: x.get("referenceName", ""),
        },
    ]

    for config in entity_configs:
        if not summary.get(config["has_key"], False):
            continue

        ctx.log(f"Fetching {config['name']} diff...")

        # Cast config values to expected types
        entity_name = str(config["name"])
        fetch_fn: Callable[[int], str] = config["fetch_fn"]  # type: ignore[assignment]
        sort_key: Callable[[Any], str] = config["sort_key"]  # type: ignore[assignment]

        if is_committed:
            history_fn: Callable[[int], str] = config["history_fn"]  # type: ignore[assignment]
            entity_diffs[config["key"]] = _fetch_and_diff_entity_from_history(
                client,
                feature_branch_id,
                entity_name,
                history_fn,
                fetch_fn,
                sort_key,
                ctx,
            )
        else:
            entity_diffs[config["key"]] = _fetch_and_diff_entity(
                client,
                feature_branch_id,
                base_branch_id,
                entity_name,
                fetch_fn,
                sort_key,
                ctx,
            )

    return entity_diffs


@source.command()
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID - for showing upstream changes",
)
@click.option(
    "--from",
    "from_branch",
    type=int,
    help="Source branch ID - use with --to and --config for specific config diff",
)
@click.option(
    "--to",
    "to_branch",
    type=int,
    help="Target branch ID - use with --from and --config",
)
@click.option(
    "--config",
    "-c",
    "config_ref",
    type=str,
    help="Configuration reference name to diff (required with --from/--to)",
)
@pass_context
@require_auth
def diff(
    ctx: DxsContext,
    branch: int | None,
    from_branch: int | None,
    to_branch: int | None,
    config_ref: str | None,
) -> None:
    """Show configuration differences.

    Two modes of operation:

    1. Upstream changes (--branch): Shows changes in base branch that haven't
       been pulled into the feature branch.

    2. Specific config diff (--from/--to/--config): Shows the JSON diff for
       a specific configuration between two branches.

    \b
    Examples:
        dxs source diff --branch 100
        dxs source diff --from 66512 --to 67162 --config userGrid
    """
    # Validate options
    if branch and (from_branch or to_branch or config_ref):
        raise ValidationError(
            message="Cannot use --branch with --from/--to/--config",
            code="DXS-VAL-002",
            suggestions=[
                "Use --branch alone for upstream changes, or --from/--to/--config for specific diff"
            ],
        )

    if from_branch or to_branch or config_ref:
        # Specific config diff mode - all three are required
        if not (from_branch and to_branch and config_ref):
            raise ValidationError(
                message="--from, --to, and --config are all required for config diff",
                code="DXS-VAL-002",
                suggestions=["Example: dxs source diff --from 66512 --to 67162 --config userGrid"],
            )
        _diff_specific_config(ctx, from_branch, to_branch, config_ref)
        return

    # Upstream changes mode (existing behavior)
    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH environment variable.",
            code="DXS-VAL-002",
        )

    client = ApiClient()
    ctx.log(f"Fetching upstream changes for branch {branch_id}...")

    changes_data = client.get(SourceControlEndpoints.upstream_changes(branch_id))

    # Add summary information
    config_changes = changes_data.get("configs", [])
    summary = {
        "total_config_changes": len(config_changes),
        "has_replacements": changes_data.get("hasReplacements", False),
        "has_settings": changes_data.get("hasSettings", False),
        "has_operations": changes_data.get("hasOperations", False),
        "has_references": changes_data.get("hasReferences", False),
        "has_roles": changes_data.get("hasRoles", False),
    }

    ctx.output(
        single(
            item={
                "summary": summary,
                "config_changes": config_changes,
                "base_branch_id": changes_data.get("baseApplicationId"),
            },
            semantic_key="upstream_changes",
            branch_id=branch_id,
        )
    )


def _diff_specific_config(
    ctx: DxsContext, from_branch: int, to_branch: int, config_ref: str
) -> None:
    """Show diff for a specific configuration between two branches.

    Args:
        ctx: CLI context
        from_branch: Source branch ID
        to_branch: Target branch ID
        config_ref: Configuration reference name
    """
    import json
    from difflib import unified_diff

    client = ApiClient()

    # Find the config in both branches by fetching all configs
    ctx.log(f"Looking up configuration '{config_ref}'...")

    # Fetch configs from both branches (include external to find the config)
    from_configs = _fetch_branch_configs(client, from_branch, ctx, owned_only=False)
    to_configs = _fetch_branch_configs(client, to_branch, ctx, owned_only=False)

    from_cfg_info = from_configs.get(config_ref)
    to_cfg_info = to_configs.get(config_ref)

    if not from_cfg_info and not to_cfg_info:
        raise ValidationError(
            message=f"Configuration '{config_ref}' not found in either branch",
            code="DXS-VAL-003",
            suggestions=[
                "Check the reference name is correct",
                "Use 'dxs source explore configs --branch <id>' to list available configs",
            ],
        )

    if not from_cfg_info:
        # Config exists only in target (new config)
        config_type = to_cfg_info["configType"]
        to_endpoint = ConfigurationEndpoints.get_content(to_branch, config_type, to_cfg_info["id"])
        to_content = client.get(to_endpoint)
        ctx.output(
            single(
                item={
                    "change_type": "created",
                    "referenceName": config_ref,
                    "configType": config_type,
                    "note": "Configuration exists only in target branch (newly created)",
                    "content": _extract_config_content(to_content),
                },
                semantic_key="config_diff",
                from_branch_id=from_branch,
                to_branch_id=to_branch,
                config_ref=config_ref,
            )
        )
        return

    if not to_cfg_info:
        # Config exists only in source (deleted)
        config_type = from_cfg_info["configType"]
        from_endpoint = ConfigurationEndpoints.get_content(
            from_branch, config_type, from_cfg_info["id"]
        )
        from_content = client.get(from_endpoint)
        ctx.output(
            single(
                item={
                    "change_type": "deleted",
                    "referenceName": config_ref,
                    "configType": config_type,
                    "note": "Configuration exists only in source branch (deleted in target)",
                    "content": _extract_config_content(from_content),
                },
                semantic_key="config_diff",
                from_branch_id=from_branch,
                to_branch_id=to_branch,
                config_ref=config_ref,
            )
        )
        return

    # Both exist - fetch full content and compute diff
    config_type = to_cfg_info["configType"]

    from_endpoint = ConfigurationEndpoints.get_content(
        from_branch, config_type, from_cfg_info["id"]
    )
    to_endpoint = ConfigurationEndpoints.get_content(to_branch, config_type, to_cfg_info["id"])

    from_data = client.get(from_endpoint)
    to_data = client.get(to_endpoint)

    from_content = _extract_config_content(from_data)
    to_content = _extract_config_content(to_data)

    # Clean for comparison
    from_clean = _clean_for_diff(from_content, omit_code=False)
    to_clean = _clean_for_diff(to_content, omit_code=False)

    from_str = json.dumps(from_clean, indent=2, sort_keys=True)
    to_str = json.dumps(to_clean, indent=2, sort_keys=True)

    if from_str == to_str:
        ctx.output(
            single(
                item={
                    "change_type": "unchanged",
                    "referenceName": config_ref,
                    "configType": config_type,
                    "note": "Configuration content is identical in both branches",
                },
                semantic_key="config_diff",
                from_branch_id=from_branch,
                to_branch_id=to_branch,
                config_ref=config_ref,
            )
        )
        return

    diff_lines = list(
        unified_diff(
            from_str.splitlines(keepends=True),
            to_str.splitlines(keepends=True),
            fromfile=f"{config_ref} (branch {from_branch})",
            tofile=f"{config_ref} (branch {to_branch})",
        )
    )

    ctx.output(
        single(
            item={
                "change_type": "modified",
                "referenceName": config_ref,
                "configType": config_type,
                "diff": "".join(diff_lines),
                "lines_added": sum(
                    1 for line in diff_lines if line.startswith("+") and not line.startswith("+++")
                ),
                "lines_removed": sum(
                    1 for line in diff_lines if line.startswith("-") and not line.startswith("---")
                ),
            },
            semantic_key="config_diff",
            from_branch_id=from_branch,
            to_branch_id=to_branch,
            config_ref=config_ref,
        )
    )


def _fetch_branch_configs(
    client: ApiClient, branch_id: int, ctx: DxsContext, owned_only: bool = True
) -> dict[str, dict[str, Any]]:
    """Fetch all configurations for a branch and return as dict keyed by reference name.

    Args:
        client: API client
        branch_id: Branch ID to fetch configs from
        ctx: CLI context for logging
        owned_only: If True, exclude external/referenced configs

    Returns:
        Dict mapping reference_name -> config info dict
    """
    # Import here to avoid circular dependency
    from dxs.commands.explore import CONFIGURATION_TYPES

    configs: dict[str, dict[str, Any]] = {}

    for ctype in CONFIGURATION_TYPES:
        try:
            type_configs = client.get(ConfigurationEndpoints.list_all(branch_id, ctype))
            if not isinstance(type_configs, list):
                continue

            for cfg in type_configs:
                ref_name = cfg.get("referenceName")
                if not ref_name:
                    continue

                # Check if external (from a dependency)
                is_external = cfg.get("applicationId") != branch_id
                if owned_only and is_external:
                    continue

                # Don't overwrite owned configs with external ones (multiple configs
                # can share the same referenceName across the app and its dependencies)
                if ref_name in configs and not configs[ref_name]["isExternal"] and is_external:
                    continue

                configs[ref_name] = {
                    "id": cfg.get("id"),
                    "referenceName": ref_name,
                    "description": cfg.get("description"),
                    "configType": ctype,
                    "applicationId": cfg.get("applicationId"),
                    "isExternal": is_external,
                }
        except Exception:
            # Some config types may not exist or may fail - continue
            continue

    return configs


def _get_commits_between_branches(
    client: ApiClient, from_branch: int, to_branch: int, ctx: DxsContext
) -> list[dict[str, Any]]:
    """Get commits between two branches with their configuration changes.

    This finds commits in the target branch's ancestry that don't exist in the
    source branch's ancestry, then fetches the configuration changes for each.

    Args:
        client: API client
        from_branch: Source branch ID (base)
        to_branch: Target branch ID (to compare)
        ctx: CLI context for logging

    Returns:
        List of commit dicts, each containing:
        - id: Commit/branch ID
        - title: Commit title
        - date: Created date
        - author: Author display name (if available)
        - changes: List of config changes (reference_name, type, modification)
    """
    # Local import to avoid circular dependency
    from dxs.commands.branch import enrich_branch_with_status

    # Get branch details to determine comparison strategy
    from_branch_data = client.get(BranchEndpoints.get(from_branch))
    to_branch_data = client.get(BranchEndpoints.get(to_branch))

    from_branch_data = enrich_branch_with_status(from_branch_data)
    to_branch_data = enrich_branch_with_status(to_branch_data)

    from_is_release = from_branch_data.get("isRelease", False)
    to_is_release = to_branch_data.get("isRelease", False)

    commits: list[dict[str, Any]] = []

    if from_is_release and to_is_release:
        # Both are releases - find commits between the two dates via application group
        group_id = from_branch_data.get("applicationGroupId") or to_branch_data.get(
            "applicationGroupId"
        )
        if group_id:
            all_branches = client.get(BranchEndpoints.list(group_id))
            if not isinstance(all_branches, list):
                all_branches = [all_branches] if all_branches else []

            from_date = from_branch_data.get("createdDate", "")
            to_date = to_branch_data.get("createdDate", "")

            if from_date and to_date:
                # Get feature branch commits (WorkspaceHistory = status 4)
                branch_commits = [b for b in all_branches if b.get("applicationStatusId") == 4]
                commits_in_range = [
                    b for b in branch_commits if from_date < b.get("createdDate", "") <= to_date
                ]
                commits_in_range.sort(key=lambda x: x.get("createdDate", ""))

                # For each commit, fetch its changes
                ctx.log(f"Fetching changes for {len(commits_in_range)} commits...")
                for commit_branch in commits_in_range:
                    commit_id = commit_branch.get("id")
                    title = commit_branch.get("description") or commit_branch.get("commitTitle")
                    commit_entry: dict[str, Any] = {
                        "id": commit_id,
                        "title": title,
                        "date": commit_branch.get("createdDate"),
                        "author": commit_branch.get("authorDisplayName"),
                        "changes": [],
                    }

                    # Fetch the changes for this commit
                    try:
                        changes_data = client.get(
                            SourceControlEndpoints.history_branch_changes(commit_id)
                        )
                        if changes_data:
                            configs = changes_data.get("configs", [])
                            if configs:
                                commit_entry["changes"] = [
                                    {
                                        "reference_name": c.get("referenceName"),
                                        "type": c.get("configurationTypeId"),
                                        "modification": c.get("modificationTypeId"),
                                    }
                                    for c in configs
                                ]
                    except Exception:
                        pass  # Skip if we can't fetch changes

                    commits.append(commit_entry)
    else:
        # Use set-based ancestry comparison for non-release branches
        from_history = client.get(SourceControlEndpoints.branch_history(from_branch))
        to_history = client.get(SourceControlEndpoints.branch_history(to_branch))

        if not isinstance(from_history, list):
            from_history = [from_history] if from_history else []
        if not isinstance(to_history, list):
            to_history = [to_history] if to_history else []

        # Find commits in target's ancestry that don't exist in source's ancestry
        from_commit_ids = {c.get("applicationId") for c in from_history if c.get("applicationId")}
        unique_in_to = [c for c in to_history if c.get("applicationId") not in from_commit_ids]

        # Fetch changes for each unique commit
        ctx.log(f"Fetching changes for {len(unique_in_to)} commits...")
        for commit in unique_in_to:
            commit_id = commit.get("applicationId")
            if not commit_id:
                continue

            entry = {
                "id": commit_id,
                "title": commit.get("commitTitle"),
                "date": commit.get("createdDate"),
                "author": commit.get("authorDisplayName"),
                "changes": [],
            }

            try:
                changes_data = client.get(SourceControlEndpoints.history_branch_changes(commit_id))
                if changes_data:
                    configs = changes_data.get("configs", [])
                    if configs:
                        entry["changes"] = [
                            {
                                "reference_name": c.get("referenceName"),
                                "type": c.get("configurationTypeId"),
                                "modification": c.get("modificationTypeId"),
                            }
                            for c in configs
                        ]
            except Exception:
                pass

            commits.append(entry)

    return commits


def _get_modified_configs_between_branches(
    client: ApiClient, from_branch: int, to_branch: int, ctx: DxsContext
) -> set[str]:
    """Get reference names of configs modified in commits between branches.

    Args:
        client: API client
        from_branch: Source branch ID (base)
        to_branch: Target branch ID (to compare)
        ctx: CLI context for logging

    Returns:
        Set of reference names of configs that were modified in commits
        between the two branches.
    """
    commits = _get_commits_between_branches(client, from_branch, to_branch, ctx)

    modified_refs: set[str] = set()
    for commit in commits:
        for change in commit.get("changes", []):
            ref_name = change.get("reference_name")
            if ref_name:
                modified_refs.add(ref_name)

    ctx.log(f"Found {len(modified_refs)} configs modified in {len(commits)} commits")
    return modified_refs


def _changes_between_branches(
    ctx: DxsContext, from_branch: int, to_branch: int, with_diffs: bool
) -> None:
    """Compare configurations between two arbitrary branches.

    Args:
        ctx: CLI context
        from_branch: Source branch ID (base)
        to_branch: Target branch ID (to compare)
        with_diffs: Whether to include actual diffs
    """
    client = ApiClient()

    ctx.log(f"Fetching configurations from branch {from_branch}...")
    from_configs = _fetch_branch_configs(client, from_branch, ctx)
    ctx.log(f"Found {len(from_configs)} configurations in source branch")

    ctx.log(f"Fetching configurations from branch {to_branch}...")
    to_configs = _fetch_branch_configs(client, to_branch, ctx)
    ctx.log(f"Found {len(to_configs)} configurations in target branch")

    # Get configs actually modified in commits between branches
    # This uses the platform's commit history rather than ID comparison
    ctx.log("Fetching commit history to identify modified configs...")
    modified_refs = _get_modified_configs_between_branches(client, from_branch, to_branch, ctx)

    # Compare configurations
    from_refs = set(from_configs.keys())
    to_refs = set(to_configs.keys())

    added_refs = to_refs - from_refs
    removed_refs = from_refs - to_refs
    common_refs = from_refs & to_refs

    # Only configs that appear in commit changes are truly "updated"
    # This avoids false positives from ID-only comparison (different branch versions
    # always have different IDs even when content is identical)
    updated_refs = common_refs & modified_refs

    # Build change lists
    changes_by_type: dict[str, list[dict[str, Any]]] = {
        "created": [],
        "updated": [],
        "deleted": [],
    }

    # Added configs
    for ref in sorted(added_refs):
        cfg = to_configs[ref]
        changes_by_type["created"].append(
            {
                "referenceName": ref,
                "configType": cfg["configType"],
                "description": cfg.get("description"),
                "id": cfg["id"],
            }
        )

    # Removed configs
    for ref in sorted(removed_refs):
        cfg = from_configs[ref]
        changes_by_type["deleted"].append(
            {
                "referenceName": ref,
                "configType": cfg["configType"],
                "description": cfg.get("description"),
                "id": cfg["id"],
            }
        )

    # Check for modified configs (present in commit history)
    for ref in sorted(updated_refs):
        from_cfg = from_configs[ref]
        to_cfg = to_configs[ref]
        change_info: dict[str, Any] = {
            "referenceName": ref,
            "configType": to_cfg["configType"],
            "description": to_cfg.get("description"),
            "from_id": from_cfg["id"],
            "to_id": to_cfg["id"],
        }

        # Add diff if requested
        if with_diffs:
            diff_result = _compute_config_diff(
                client, from_branch, to_branch, from_cfg, to_cfg, ctx
            )
            if diff_result:
                change_info["diff"] = diff_result

        changes_by_type["updated"].append(change_info)

    # Build summary
    summary = {
        "total_in_source": len(from_configs),
        "total_in_target": len(to_configs),
        "created_count": len(changes_by_type["created"]),
        "updated_count": len(changes_by_type["updated"]),
        "deleted_count": len(changes_by_type["deleted"]),
    }

    ctx.output(
        single(
            item={
                "summary": summary,
                "changes_by_type": changes_by_type,
                "from_branch_id": from_branch,
                "to_branch_id": to_branch,
            },
            semantic_key="branch_config_changes",
            from_branch_id=from_branch,
            to_branch_id=to_branch,
            includes_diffs=with_diffs,
        )
    )


def _compute_config_diff(
    client: ApiClient,
    from_branch: int,
    to_branch: int,
    from_cfg: dict[str, Any],
    to_cfg: dict[str, Any],
    ctx: DxsContext,
) -> str | None:
    """Compute diff between two config versions.

    Args:
        client: API client
        from_branch: Source branch ID
        to_branch: Target branch ID
        from_cfg: Source config info
        to_cfg: Target config info
        ctx: CLI context

    Returns:
        Unified diff string or None if unable to compute
    """
    import json
    from difflib import unified_diff

    config_type = to_cfg["configType"]
    from_id = from_cfg["id"]
    to_id = to_cfg["id"]
    ref_name = to_cfg["referenceName"]

    try:
        # Fetch config content from both branches
        from_endpoint = _config_endpoint(from_branch, config_type, from_id)
        to_endpoint = _config_endpoint(to_branch, config_type, to_id)

        from_content = client.get(from_endpoint)
        to_content = client.get(to_endpoint)

        # Extract actual config content
        from_content = _extract_config_content(from_content)
        to_content = _extract_config_content(to_content)

        # Clean for diffing (remove noise)
        from_clean = _clean_for_diff(from_content, omit_code=True)
        to_clean = _clean_for_diff(to_content, omit_code=True)

        # Generate diff
        from_str = json.dumps(from_clean, indent=2, sort_keys=True)
        to_str = json.dumps(to_clean, indent=2, sort_keys=True)

        diff_lines = list(
            unified_diff(
                from_str.splitlines(keepends=True),
                to_str.splitlines(keepends=True),
                fromfile=f"{ref_name} (branch {from_branch})",
                tofile=f"{ref_name} (branch {to_branch})",
            )
        )

        if diff_lines:
            return "".join(diff_lines)
        return None

    except Exception as e:
        ctx.log(f"Warning: Could not compute diff for {ref_name}: {e}")
        return None


@source.command()
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID (feature branch) - for comparing feature branch to its base",
)
@click.option(
    "--from",
    "from_branch",
    type=int,
    help="Source branch ID (base for comparison) - use with --to for arbitrary branch comparison",
)
@click.option(
    "--to",
    "to_branch",
    type=int,
    help="Target branch ID (compared against source) - use with --from",
)
@click.option(
    "--with-diffs",
    is_flag=True,
    default=False,
    help="Include actual diffs for each changed configuration",
)
@pass_context
@require_auth
def changes(
    ctx: DxsContext,
    branch: int | None,
    from_branch: int | None,
    to_branch: int | None,
    with_diffs: bool,
) -> None:
    """Show configuration changes between branches.

    Two modes of operation:

    1. Feature branch mode (--branch): Shows pending changes in a feature branch
       compared to its base branch. Uses the API's built-in comparison.

    2. Arbitrary branch comparison (--from/--to): Compares any two branches by
       fetching and diffing their configurations. Useful for comparing releases.

    \b
    Options:
        --branch      Feature branch to compare against its base
        --from/--to   Compare two arbitrary branches
        --with-diffs  Include actual JSON diffs for each change

    \b
    Examples:
        dxs source changes --branch 101
        dxs source changes --branch 101 --with-diffs
        dxs source changes --from 66512 --to 67162
    """
    # Validate options: either --branch OR --from/--to, not both
    if branch and (from_branch or to_branch):
        raise ValidationError(
            message="Cannot use --branch with --from/--to",
            code="DXS-VAL-002",
            suggestions=[
                "Use --branch alone for feature branch changes, or --from/--to for comparing two branches"
            ],
        )

    if (from_branch and not to_branch) or (to_branch and not from_branch):
        raise ValidationError(
            message="Both --from and --to are required for branch comparison",
            code="DXS-VAL-002",
            suggestions=["Provide both --from and --to branch IDs"],
        )

    if from_branch and to_branch:
        # Arbitrary branch comparison mode
        _changes_between_branches(ctx, from_branch, to_branch, with_diffs)
        return

    # Feature branch mode (existing behavior)
    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH environment variable.",
            code="DXS-VAL-002",
        )

    client = ApiClient()

    # Check if this is a committed branch (WorkspaceHistory) vs active feature branch
    is_committed = False
    branch_type = "feature"
    if with_diffs:
        ctx.log(f"Checking branch type for {branch_id}...")
        branch_info = client.get(BranchEndpoints.get(branch_id))
        # applicationStatusId 4 = WorkspaceHistory (committed)
        # applicationStatusId 5 = WorkspaceActive (feature branch)
        is_committed = branch_info.get("applicationStatusId") == 4
        branch_type = "committed" if is_committed else "feature"
        ctx.log(f"Branch type: {branch_type}")

    ctx.log(f"Fetching branch changes for branch {branch_id}...")

    changes_data = client.get(SourceControlEndpoints.feature_branch_changes(branch_id))
    base_branch_id = changes_data.get("baseApplicationId")

    # Add summary information
    config_changes = changes_data.get("configs", [])
    summary = {
        "total_config_changes": len(config_changes),
        "has_replacements": changes_data.get("hasReplacements", False),
        "has_settings": changes_data.get("hasSettings", False),
        "has_operations": changes_data.get("hasOperations", False),
        "has_references": changes_data.get("hasReferences", False),
        "has_roles": changes_data.get("hasRoles", False),
        "branch_type": branch_type,
    }

    # If diffs requested, enrich each change with actual diff content
    entity_diffs = {}
    if with_diffs:
        if config_changes:
            ctx.log(f"Fetching diffs for {len(config_changes)} changed configurations...")
            config_changes = _add_diffs_to_changes(
                client, branch_id, base_branch_id, config_changes, ctx, is_committed
            )

        # Fetch diffs for entity types (replacements, settings, operations, roles, references)
        entity_diffs = _fetch_entity_diffs(
            client, branch_id, base_branch_id, summary, ctx, is_committed
        )

    # Group changes by modification type for LLM consumption
    changes_by_type: dict[str, list[Any]] = {
        "created": [],
        "updated": [],
        "deleted": [],
    }
    for change in config_changes:
        mod_type = change.get("modificationTypeId", "").lower()
        if mod_type in changes_by_type:
            changes_by_type[mod_type].append(change)

    # Build output item
    output_item = {
        "summary": summary,
        "changes_by_type": changes_by_type,
        "all_changes": config_changes,
        "base_branch_id": base_branch_id,
    }

    # Include entity diffs if any were fetched
    if entity_diffs:
        output_item["entity_diffs"] = entity_diffs

    ctx.output(
        single(
            item=output_item,
            semantic_key="feature_branch_changes",
            branch_id=branch_id,
            includes_diffs=with_diffs,
        )
    )


def _extract_user_info(user: dict | None, org_names: dict[int, str] | None = None) -> dict | None:
    """Extract user info for the users list.

    Args:
        user: User dictionary from API
        org_names: Optional dict mapping org ID to org name

    Returns:
        User info dict with id, organization, organizationId, displayName,
        userPrincipalName, externalId
    """
    if not user:
        return None

    org_id = user.get("organizationId")
    org_name = None
    if org_names and org_id:
        org_name = org_names.get(org_id)
    if not org_name:
        org_name = user.get("organizationName") or user.get("organization")

    return {
        "id": user.get("id"),
        "organization": org_name,
        "organizationId": org_id,
        "displayName": user.get("displayName"),
        "userPrincipalName": user.get("userPrincipalName"),
        "externalId": user.get("externalId"),
    }


def _collect_users_from_locks(
    config_locks: list,
    replacements_lock: dict | None,
    settings_lock: dict | None,
    operations_lock: dict | None,
    org_names: dict[int, str] | None = None,
) -> dict[int, dict[str, Any] | None]:
    """Collect unique users from all lock types.

    Args:
        config_locks: List of config lock dicts
        replacements_lock: Replacements lock dict
        settings_lock: Settings lock dict
        operations_lock: Operations lock dict
        org_names: Optional dict mapping org ID to org name

    Returns:
        Dict mapping user ID to user info
    """
    users: dict[int, dict[str, Any] | None] = {}

    # From config locks
    for lock in config_locks:
        locked_by = lock.get("lockedBy")
        if locked_by:
            user_id = locked_by.get("id")
            if user_id and user_id not in users:
                users[user_id] = _extract_user_info(locked_by, org_names)

    # From other lock types
    for lock in [replacements_lock, settings_lock, operations_lock]:
        if lock:
            locked_by = lock.get("lockedBy")
            if locked_by:
                user_id = locked_by.get("id")
                if user_id and user_id not in users:
                    users[user_id] = _extract_user_info(locked_by, org_names)

    return users


def _collect_org_ids_from_locks(
    config_locks: list,
    replacements_lock: dict | None,
    settings_lock: dict | None,
    operations_lock: dict | None,
) -> set[int]:
    """Collect unique organization IDs from all locks.

    Args:
        config_locks: List of config lock dicts
        replacements_lock: Replacements lock dict
        settings_lock: Settings lock dict
        operations_lock: Operations lock dict

    Returns:
        Set of organization IDs
    """
    org_ids = set()

    # From config locks
    for lock in config_locks:
        locked_by = lock.get("lockedBy")
        if locked_by:
            org_id = locked_by.get("organizationId")
            if org_id:
                org_ids.add(org_id)

    # From other lock types
    for lock in [replacements_lock, settings_lock, operations_lock]:
        if lock:
            locked_by = lock.get("lockedBy")
            if locked_by:
                org_id = locked_by.get("organizationId")
                if org_id:
                    org_ids.add(org_id)

    return org_ids


@source.command()
@click.option(
    "--repo",
    "-r",
    type=int,
    help="Repository ID",
)
@pass_context
@require_auth
def locks(ctx: DxsContext, repo: int | None) -> None:
    """Show current lock status.

    Displays all current locks for a repository.
    Shows who has locked which configurations.

    \b
    Example:
        dxs source locks --repo 10
    """
    repo_id = repo or ctx.repo
    if not repo_id:
        raise ValidationError(
            message="Repository ID is required. Use --repo or set DXS_REPO.",
            code="DXS-VAL-001",
            suggestions=[
                "Provide --repo flag: dxs source locks --repo 10",
                "Set environment variable: export DXS_REPO=10",
            ],
        )

    client = ApiClient()
    ctx.log(f"Fetching locks for repository {repo_id}...")

    locks_data = client.get(SourceControlEndpoints.locks(repo_id))

    # Get raw lock data
    config_locks = locks_data.get("configs", [])
    replacements_lock = locks_data.get("replacements")
    settings_lock = locks_data.get("settingsAndReferences")
    operations_lock = locks_data.get("operationsAndRoles")

    # Collect unique organization IDs and fetch their names
    org_ids = _collect_org_ids_from_locks(
        config_locks, replacements_lock, settings_lock, operations_lock
    )
    org_names: dict[int, str] = {}
    for org_id in org_ids:
        try:
            org_data = client.get(OrganizationEndpoints.get(org_id))
            org_names[org_id] = org_data.get("name")
        except Exception:
            pass

    # Collect unique users from all locks
    users_map = _collect_users_from_locks(
        config_locks, replacements_lock, settings_lock, operations_lock, org_names
    )

    # Get user IDs for special locks
    replacements_lock_user_id = None
    settings_lock_user_id = None
    operations_lock_user_id = None
    if replacements_lock and replacements_lock.get("lockedBy"):
        replacements_lock_user_id = replacements_lock["lockedBy"].get("id")
    if settings_lock and settings_lock.get("lockedBy"):
        settings_lock_user_id = settings_lock["lockedBy"].get("id")
    if operations_lock and operations_lock.get("lockedBy"):
        operations_lock_user_id = operations_lock["lockedBy"].get("id")

    # Build locks_by_user with full user info and expanded config entries
    locks_by_user: dict[int, dict] = {}
    for lock in config_locks:
        locked_by = lock.get("lockedBy")
        if locked_by:
            user_id = locked_by.get("id")
            if user_id not in locks_by_user:
                locks_by_user[user_id] = {
                    "user": users_map.get(user_id),
                    "configs": [],
                }
            locks_by_user[user_id]["configs"].append(
                {
                    "referenceName": lock.get("referenceName"),
                    "branchId": lock.get("applicationId"),
                    "lockedDate": lock.get("modifiedDate"),
                }
            )

    # Add special locks to the users who hold them
    def add_special_lock(user_id: int | None, lock: dict | None, lock_name: str) -> None:
        if not user_id or not lock:
            return
        if user_id not in locks_by_user:
            locks_by_user[user_id] = {
                "user": users_map.get(user_id),
                "configs": [],
            }
        locks_by_user[user_id][lock_name] = {
            "branchId": lock.get("applicationId"),
            "lockedDate": lock.get("modifiedDate"),
        }

    add_special_lock(replacements_lock_user_id, replacements_lock, "replacements_lock")
    add_special_lock(settings_lock_user_id, settings_lock, "settings_lock")
    add_special_lock(operations_lock_user_id, operations_lock, "operations_lock")

    # Build summary
    summary = {
        "total_config_locks": len(config_locks),
        "has_replacements_lock": replacements_lock is not None,
        "has_settings_lock": settings_lock is not None,
        "has_operations_lock": operations_lock is not None,
    }

    ctx.output(
        single(
            item={
                "summary": summary,
                "locks_by_user": list(locks_by_user.values()) if locks_by_user else [],
            },
            semantic_key="locks",
            repository_id=repo_id,
        )
    )


@source.command()
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID",
)
@click.option(
    "--tree",
    is_flag=True,
    default=False,
    help="Show full transitive dependency tree",
)
@pass_context
@require_auth
def deps(ctx: DxsContext, branch: int | None, tree: bool) -> None:
    """List dependencies (referenced component packages).

    Shows component packages referenced by a branch. Use --tree to
    recursively show transitive dependencies.

    \b
    Options:
        --branch ID   Branch ID
        --tree        Show full transitive dependency tree

    \b
    Examples:
        dxs source deps --branch 100
        dxs source deps --branch 100 --tree
    """
    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH.",
            code="DXS-VAL-002",
            suggestions=[
                "Provide --branch flag: dxs source deps --branch 100",
                "Set environment variable: export DXS_BRANCH=100",
            ],
        )

    client = ApiClient()
    ctx.log(f"Fetching dependencies for branch {branch_id}...")

    # Get direct dependencies
    deps_data = client.get(DependencyEndpoints.list(branch_id))

    # Normalize to list
    if not isinstance(deps_data, list):
        deps_data = [deps_data] if deps_data else []

    if tree:
        # Build transitive dependency tree
        ctx.log("Building transitive dependency tree...")
        dependencies = _build_dependency_tree(client, deps_data, ctx)
    else:
        # Enrich with version info for direct dependencies
        dependencies = []
        for dep in deps_data:
            version_id = dep.get("marketPlaceApplicationVersionId")
            if version_id:
                try:
                    version_info = client.get(MarketplaceEndpoints.version(version_id))
                    dep["version_info"] = {
                        "version_code": version_info.get("versionCode"),
                        "version_name": version_info.get("versionName"),
                        "release_date": version_info.get("releaseDate"),
                        "release_notes": version_info.get("releaseNotes"),
                    }
                except Exception:
                    dep["version_info"] = None
            dependencies.append(dep)

    ctx.output(
        list_response(
            items=dependencies,
            semantic_key="dependencies",
            branch_id=branch_id,
            is_transitive=tree,
        )
    )


@source.command("deps-diff")
@click.option(
    "--from",
    "from_branch",
    type=int,
    required=True,
    help="Previous branch ID (older version)",
)
@click.option(
    "--to",
    "to_branch",
    type=int,
    required=True,
    help="Current branch ID (newer version)",
)
@pass_context
@require_auth
def deps_diff(ctx: DxsContext, from_branch: int, to_branch: int) -> None:
    """Compare dependencies between two branches.

    Shows added, removed, and updated dependencies between two branch versions.
    Useful for generating release notes without manual diff computation.

    \b
    Options:
        --from ID   Previous branch ID (older)
        --to ID     Current branch ID (newer)

    \b
    Example:
        dxs source deps-diff --from 63367 --to 63379
    """
    client = ApiClient()

    # Fetch dependencies for both branches in parallel conceptually
    ctx.log(f"Fetching dependencies for branch {from_branch}...")
    from_deps = client.get(DependencyEndpoints.list(from_branch))

    ctx.log(f"Fetching dependencies for branch {to_branch}...")
    to_deps = client.get(DependencyEndpoints.list(to_branch))

    # Normalize to lists
    if not isinstance(from_deps, list):
        from_deps = [from_deps] if from_deps else []
    if not isinstance(to_deps, list):
        to_deps = [to_deps] if to_deps else []

    # Build lookup maps by referenceName
    from_by_ref = {d.get("referenceName"): d for d in from_deps}
    to_by_ref = {d.get("referenceName"): d for d in to_deps}

    # Compute differences
    added = []
    removed = []
    updated = []
    unchanged_count = 0

    # Find added and updated
    for ref_name, to_dep in to_by_ref.items():
        if ref_name not in from_by_ref:
            # New dependency
            added.append(
                {
                    "referenceName": ref_name,
                    "name": to_dep.get("name"),
                    "description": to_dep.get("description"),
                    "versionName": to_dep.get("versionName"),
                    "versionId": to_dep.get("marketPlaceApplicationVersionId"),
                    "applicationId": to_dep.get("applicationId"),
                    "commitTitle": to_dep.get("commitTitle"),
                    "isDirect": to_dep.get("isDirect"),
                }
            )
        else:
            from_dep = from_by_ref[ref_name]
            from_version_id = from_dep.get("marketPlaceApplicationVersionId")
            to_version_id = to_dep.get("marketPlaceApplicationVersionId")

            if from_version_id != to_version_id:
                # Updated dependency
                updated.append(
                    {
                        "referenceName": ref_name,
                        "name": to_dep.get("name"),
                        "fromVersionId": from_version_id,
                        "toVersionId": to_version_id,
                        "fromApplicationId": from_dep.get("applicationId"),
                        "toApplicationId": to_dep.get("applicationId"),
                        "fromVersionName": from_dep.get("versionName"),
                        "toVersionName": to_dep.get("versionName"),
                        "fromCommitTitle": from_dep.get("commitTitle"),
                        "toCommitTitle": to_dep.get("commitTitle"),
                        "isDirect": to_dep.get("isDirect"),
                    }
                )
            else:
                unchanged_count += 1

    # Find removed
    for ref_name, from_dep in from_by_ref.items():
        if ref_name not in to_by_ref:
            removed.append(
                {
                    "referenceName": ref_name,
                    "name": from_dep.get("name"),
                    "description": from_dep.get("description"),
                    "versionName": from_dep.get("versionName"),
                    "versionId": from_dep.get("marketPlaceApplicationVersionId"),
                    "applicationId": from_dep.get("applicationId"),
                    "isDirect": from_dep.get("isDirect"),
                }
            )

    # Sort results by referenceName for consistent output
    added.sort(key=lambda x: x.get("referenceName", ""))
    removed.sort(key=lambda x: x.get("referenceName", ""))
    updated.sort(key=lambda x: x.get("referenceName", ""))

    ctx.output(
        single(
            item={
                "summary": {
                    "added_count": len(added),
                    "removed_count": len(removed),
                    "updated_count": len(updated),
                    "unchanged_count": unchanged_count,
                    "from_total": len(from_deps),
                    "to_total": len(to_deps),
                },
                "added": added,
                "removed": removed,
                "updated": updated,
            },
            semantic_key="dependency_changes",
            from_branch_id=from_branch,
            to_branch_id=to_branch,
        )
    )


def _build_dependency_tree(
    client: ApiClient,
    deps: list,
    ctx: DxsContext,
    depth: int = 0,
    visited: set | None = None,
) -> list:
    """Recursively build transitive dependency tree.

    Args:
        client: API client instance
        deps: List of dependency references
        ctx: CLI context for logging
        depth: Current recursion depth
        visited: Set of visited version IDs to prevent cycles

    Returns:
        List of dependency dicts with nested children
    """
    if visited is None:
        visited = set()

    result = []
    for dep in deps:
        version_id = dep.get("marketPlaceApplicationVersionId")
        if not version_id or version_id in visited:
            continue

        visited.add(version_id)

        try:
            version_info = client.get(MarketplaceEndpoints.version(version_id))
        except Exception:
            version_info = {}

        node = {
            "reference_name": dep.get("referenceName"),
            "version_id": version_id,
            "version_code": version_info.get("versionCode"),
            "version_name": version_info.get("versionName"),
            "release_notes": version_info.get("releaseNotes"),
            "depth": depth,
            "children": [],
        }

        # Get children if this version has an applicationId
        app_id = version_info.get("applicationId")
        if app_id:
            try:
                child_deps = client.get(DependencyEndpoints.list(app_id))
                if not isinstance(child_deps, list):
                    child_deps = [child_deps] if child_deps else []
                if child_deps:
                    ctx.debug(f"Found {len(child_deps)} children for {node['reference_name']}")
                    node["children"] = _build_dependency_tree(
                        client, child_deps, ctx, depth + 1, visited
                    )
            except Exception:
                pass

        result.append(node)

    return result


# ============================================================================
# Dependency Graph Helper Functions
# ============================================================================


def _fetch_graph_dependencies(
    client: ApiClient,
    branch_id: int,
    ctx: DxsContext,
) -> tuple[list[dict], list[dict]]:
    """Fetch both direct and all dependencies for a branch.

    The API returns all deps with isDirect flag. We separate them here.

    Args:
        client: API client instance
        branch_id: The branch ID to fetch dependencies for
        ctx: CLI context for logging

    Returns:
        Tuple of (direct_deps_only, all_deps)
    """
    # The references endpoint returns ALL deps with isDirect flag
    all_deps = client.get(DependencyEndpoints.list(branch_id))
    if not isinstance(all_deps, list):
        all_deps = [all_deps] if all_deps else []

    # Filter to just direct dependencies for building the tree
    direct_deps = [dep for dep in all_deps if dep.get("isDirect", False)]

    return direct_deps, all_deps


def _build_graph_adjacency_map(
    client: ApiClient,
    deps: list[dict],
    ctx: DxsContext,
    visited: set[int] | None = None,
) -> dict[int, list[dict]]:
    """Build a map of application_id -> list of direct child dependencies.

    This recursively fetches each dependency's own dependencies to build
    the complete adjacency map for the graph.

    Args:
        client: API client instance
        deps: List of dependency dictionaries
        ctx: CLI context for logging
        visited: Set of visited application IDs to prevent cycles

    Returns:
        Dict mapping application_id to list of its direct dependencies
    """
    if visited is None:
        visited = set()

    adjacency: dict[int, list[dict]] = {}

    for dep in deps:
        app_id = dep.get("applicationId")

        if not app_id or app_id in visited:
            continue

        visited.add(app_id)

        try:
            # Get the dependencies OF this package
            child_deps = client.get(DependencyEndpoints.list(app_id))
            if not isinstance(child_deps, list):
                child_deps = [child_deps] if child_deps else []
            adjacency[app_id] = child_deps

            # Recursively build for children
            if child_deps:
                child_adjacency = _build_graph_adjacency_map(client, child_deps, ctx, visited)
                adjacency.update(child_adjacency)
        except Exception as e:
            ctx.debug(f"Failed to get deps for {dep.get('referenceName')}: {e}")
            adjacency[app_id] = []

    return adjacency


def _build_graph_tree_with_paths(
    deps: list[dict],
    adjacency: dict[int, list[dict]],
    all_paths: dict[int, list[list[str]]],
    current_path: list[str],
    depth: int = 0,
    max_depth: int = 10,
) -> list[dict]:
    """Build tree structure and track all paths to each dependency.

    Args:
        deps: List of dependencies at this level
        adjacency: Map of application_id -> child dependencies
        all_paths: Dict tracking all paths to each version_id (mutated)
        current_path: Current path from root to here
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        List of tree nodes for this level
    """
    if depth > max_depth:
        return []

    result = []
    for dep in deps:
        app_id = dep.get("applicationId")
        version_id = dep.get("marketPlaceApplicationVersionId")
        name = dep.get("referenceName") or dep.get("name", "Unknown")

        # Track this path
        new_path = current_path + [name]
        if version_id:
            if version_id not in all_paths:
                all_paths[version_id] = []
            all_paths[version_id].append(new_path)

        node = {
            "name": name,
            "version": dep.get("versionName") or dep.get("commitTitle"),
            "version_id": version_id,
            "is_latest": dep.get("isLatest", False),
        }

        # Get children from adjacency map
        children_deps = adjacency.get(app_id, []) if app_id else []
        if children_deps:
            node["children"] = _build_graph_tree_with_paths(
                children_deps,
                adjacency,
                all_paths,
                new_path,
                depth + 1,
                max_depth,
            )
            node["transitive_deps"] = len(children_deps)
        else:
            node["transitive_deps"] = 0

        result.append(node)

    return result


def _find_graph_overlapping_deps(
    all_paths: dict[int, list[list[str]]],
    all_deps: list[dict],
) -> list[dict]:
    """Find dependencies that appear via multiple paths.

    Args:
        all_paths: Dict of version_id -> list of paths
        all_deps: List of all dependency dictionaries

    Returns:
        List of overlapping dependencies (name, version_id, occurrence count)
    """
    # Create lookup for dep info
    dep_info = {dep.get("marketPlaceApplicationVersionId"): dep for dep in all_deps}

    overlapping = []
    for version_id, paths in all_paths.items():
        if len(paths) > 1:
            dep = dep_info.get(version_id, {})
            overlapping.append(
                {
                    "name": dep.get("referenceName") or dep.get("name"),
                    "version_id": version_id,
                    "occurrences": len(paths),
                }
            )

    # Sort by occurrences descending, then by name
    overlapping.sort(key=lambda x: (-(x["occurrences"] or 0), x["name"] or ""))
    return overlapping


def _format_graph_output(
    root_name: str,
    branch_id: int,
    direct_deps: list[dict],
    all_deps: list[dict],
    tree: list[dict],
    overlapping: list[dict],
) -> dict:
    """Format the complete dependency graph output.

    Args:
        root_name: Name of the root branch
        branch_id: ID of the root branch
        direct_deps: List of direct dependencies
        all_deps: List of all dependencies
        tree: Tree structure of dependencies
        overlapping: List of overlapping dependencies

    Returns:
        Formatted output dictionary
    """
    from dxs import __version__

    return {
        "dependency_graph": {
            "root": {
                "name": root_name,
                "branch_id": branch_id,
            },
            "summary": {
                "total_dependencies": len(all_deps),
                "direct_dependencies": len(direct_deps),
                "transitive_dependencies": len(all_deps) - len(direct_deps),
                "overlapping_dependencies": len(overlapping),
            },
            "direct": tree,
            "overlapping": overlapping if overlapping else None,
        },
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cli_version": __version__,
            "branch_id": branch_id,
        },
    }


def _format_flat_graph(
    all_deps: list[dict],
    branch_id: int,
    root_name: str,
) -> dict:
    """Format dependencies as flat list with isDirect flag.

    Args:
        all_deps: List of all dependencies
        branch_id: ID of the root branch
        root_name: Name of the root branch

    Returns:
        Formatted flat output dictionary
    """
    from dxs import __version__

    deps_list = []
    for dep in all_deps:
        deps_list.append(
            {
                "name": dep.get("referenceName") or dep.get("name"),
                "version": dep.get("versionName") or dep.get("commitTitle"),
                "version_id": dep.get("marketPlaceApplicationVersionId"),
                "application_id": dep.get("applicationId"),
                "is_direct": dep.get("isDirect", False),
                "is_latest": dep.get("isLatest", False),
            }
        )

    return {
        "dependency_graph": {
            "root": {"name": root_name, "branch_id": branch_id},
            "format": "flat",
            "dependencies": deps_list,
        },
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cli_version": __version__,
            "branch_id": branch_id,
        },
    }


def _save_graph_to_file(output: dict, path: str, ctx: DxsContext) -> None:
    """Save graph output to file.

    Args:
        output: The formatted output dictionary
        path: File path to save to
        ctx: CLI context for logging
    """
    from dxs.core.output.yaml_fmt import format_yaml

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    content = format_yaml(output)
    file_path.write_text(content, encoding="utf-8")

    ctx.log(f"Dependency graph saved to: {path}")


# ============================================================================
# End Dependency Graph Helper Functions
# ============================================================================


def _enrich_workitems_with_devops_data(
    ctx: DxsContext,
    workitems_data: list[dict],
    include_description: bool = False,
    include_comments: bool = False,
) -> list[dict]:
    """Enrich ApplicationWorkitem data with Azure DevOps fields.

    Args:
        ctx: CLI context for logging
        workitems_data: List of ApplicationWorkitemDto dictionaries
        include_description: Whether to fetch and include descriptions
        include_comments: Whether to fetch and include comments

    Returns:
        List of enriched work item dictionaries
    """
    from dxs.core.devops.client import AzureDevOpsClient

    # Skip enrichment if no work items
    if not workitems_data:
        return []

    # Group work items by DevOps organization
    by_org: dict[str, list[dict]] = {}
    items_without_org = []
    for item in workitems_data:
        org = item.get("devOpsOrganization")
        if org:
            if org not in by_org:
                by_org[org] = []
            by_org[org].append(item)
        else:
            # Work item has no DevOps organization - can't enrich
            items_without_org.append(item)

    enriched_items = []

    # Add items without org (no enrichment possible)
    enriched_items.extend(items_without_org)

    # Process each organization separately
    for org, org_items in by_org.items():
        ctx.log(f"Fetching {len(org_items)} work items from {org}...")

        # Extract external IDs (DevOps work item IDs)
        try:
            external_ids = [
                int(ext_id) for item in org_items if (ext_id := item.get("externalId")) is not None
            ]
        except ValueError:
            ctx.log(f"Warning: Invalid work item IDs for organization {org}, skipping")
            # Add items without DevOps enrichment
            enriched_items.extend(org_items)
            continue

        if not external_ids:
            enriched_items.extend(org_items)
            continue

        # Determine which fields to fetch
        fields = [
            "System.Id",
            "System.Title",
            "System.WorkItemType",
            "System.State",
            "System.AssignedTo",
            "System.Tags",
            "System.AreaPath",
            "System.IterationPath",
            "System.CreatedDate",
            "System.ChangedDate",
        ]
        if include_description:
            fields.append("System.Description")

        # Batch fetch work items from DevOps (up to 200 at a time)
        devops_items_map = {}
        try:
            with AzureDevOpsClient(org) as client:
                # Split into batches of 200
                for i in range(0, len(external_ids), 200):
                    batch_ids = external_ids[i : i + 200]
                    batch_items = client.get_workitems_batch(batch_ids, fields=fields)

                    # If comments requested, fetch them individually
                    if include_comments:
                        for devops_item in batch_items:
                            discussions = client.get_workitem_discussions(devops_item.id)
                            devops_item.discussions = discussions

                    # Build lookup map
                    for devops_item in batch_items:
                        devops_items_map[str(devops_item.id)] = devops_item

        except Exception as e:
            ctx.log(f"Warning: Failed to fetch DevOps data for {org}: {e}")
            # Continue with original data (graceful degradation)
            enriched_items.extend(org_items)
            continue

        # Merge ApplicationWorkitem data with DevOps data
        for app_item in org_items:
            external_id = app_item.get("externalId")
            matched_devops_item = devops_items_map.get(str(external_id))

            if matched_devops_item:
                # Create enriched item with both datasets
                enriched = {
                    **app_item,  # Start with ApplicationWorkitem fields
                    "devops_data": matched_devops_item.to_summary(
                        include_description=include_description,
                        include_discussions=include_comments,
                    ),
                }
                enriched_items.append(enriched)
            else:
                # DevOps item not found, add warning
                ctx.log(f"Warning: Work item {external_id} not found in DevOps")
                enriched_items.append(
                    {
                        **app_item,
                        "devops_data": None,
                        "warning": f"Work item {external_id} not found in Azure DevOps",
                    }
                )

    return enriched_items


@source.command()
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID",
)
@click.option(
    "--commits",
    is_flag=True,
    default=False,
    help="Group work items by commit",
)
@click.option(
    "--description",
    is_flag=True,
    default=False,
    help="Include work item description from Azure DevOps",
)
@click.option(
    "--comments",
    is_flag=True,
    default=False,
    help="Include work item comments/discussion from Azure DevOps",
)
@pass_context
@require_auth
def workitems(
    ctx: DxsContext,
    branch: int | None,
    commits: bool,
    description: bool,
    comments: bool,
) -> None:
    """List work items linked to a branch with Azure DevOps integration.

    Automatically fetches work item titles from Azure DevOps. Use --description
    and --comments flags for additional detail.

    \b
    Options:
        --branch ID     Branch ID
        --commits       Group work items by commit
        --description   Include work item descriptions
        --comments      Include work item comments/discussion

    \b
    Examples:
        dxs source workitems --branch 100
        dxs source workitems --branch 100 --description
        dxs source workitems --branch 100 --comments
        dxs source workitems --branch 100 --commits --description
    """
    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH.",
            code="DXS-VAL-002",
            suggestions=[
                "Provide --branch flag: dxs source workitems --branch 100",
                "Set environment variable: export DXS_BRANCH=100",
            ],
        )

    client = ApiClient()
    ctx.log(f"Fetching work items for branch {branch_id}...")

    workitems_data = client.get(WorkitemEndpoints.list(branch_id))

    # Normalize to list
    if not isinstance(workitems_data, list):
        workitems_data = [workitems_data] if workitems_data else []

    # Always enrich with DevOps data (at minimum, title)
    enriched_items = _enrich_workitems_with_devops_data(
        ctx,
        workitems_data,
        include_description=description,
        include_comments=comments,
    )

    if commits:
        # Group by commit
        by_commit: dict = {}
        unlinked = []
        for item in enriched_items:
            commit_id = item.get("commitId")
            if commit_id:
                if commit_id not in by_commit:
                    by_commit[commit_id] = []
                by_commit[commit_id].append(item)
            else:
                unlinked.append(item)

        ctx.output(
            single(
                item={
                    "workitems_by_commit": by_commit,
                    "unlinked_workitems": unlinked,
                    "total_count": len(enriched_items),
                    "commit_count": len(by_commit),
                },
                semantic_key="workitems_by_commit",
                branch_id=branch_id,
                includes_description=description,
                includes_comments=comments,
            )
        )
    else:
        # Extract unique DevOps organizations
        organizations = list(
            {
                item.get("devOpsOrganization")
                for item in enriched_items
                if item.get("devOpsOrganization")
            }
        )

        ctx.output(
            list_response(
                items=enriched_items,
                semantic_key="workitems",
                branch_id=branch_id,
                devops_organizations=organizations,
                includes_description=description,
                includes_comments=comments,
            )
        )


@source.command()
@click.option(
    "--from",
    "from_branch",
    type=int,
    required=True,
    help="Source branch ID (base for comparison)",
)
@click.option(
    "--to",
    "to_branch",
    type=int,
    required=True,
    help="Target branch ID (compared against source)",
)
@pass_context
@require_auth
def compare(ctx: DxsContext, from_branch: int, to_branch: int) -> None:
    """Compare changes between two branches.

    Shows releases, committed branches, work items, and dependency
    changes between two branch IDs. In Wavelength, a branch IS a commit -
    branch_history returns the linear ancestry of all commits leading up
    to that branch.

    When comparing releases, the output includes:
    - releases: Intermediate releases between the two dates
    - committed_branches: Feature branch commits with their configuration changes

    \b
    Options:
        --from ID        Source branch ID (base for comparison)
        --to ID          Target branch ID (compared against source)

    \b
    Examples:
        dxs source compare --from 65445 --to 67134
        dxs source compare --from 67079 --to 67162
    """
    # Validate: cannot compare a branch to itself
    if from_branch == to_branch:
        raise ValidationError(
            message="Cannot compare a branch to itself",
            code="DXS-VAL-002",
            suggestions=["Provide different --from and --to branch IDs"],
        )

    # Local import to avoid circular dependency (branch.py imports from cli.py)
    from dxs.commands.branch import enrich_branch_with_status

    client = ApiClient()

    # Get branch details
    ctx.log("Fetching branch details...")
    from_branch_data = client.get(BranchEndpoints.get(from_branch))
    to_branch_data = client.get(BranchEndpoints.get(to_branch))

    # Enrich with LLM-friendly status fields
    from_branch_data = enrich_branch_with_status(from_branch_data)
    to_branch_data = enrich_branch_with_status(to_branch_data)

    # Determine comparison strategy based on branch types
    # For releases (PublishedMain/Inactive), use date-based filtering on repo history
    # For other branches, use set-based ancestry comparison
    from_is_release = from_branch_data.get("isRelease", False)
    to_is_release = to_branch_data.get("isRelease", False)

    ctx.log("Fetching commit histories...")
    releases_list: list[dict[str, Any]] = []
    committed_branches_list: list[dict[str, Any]] = []
    unique_commits: list[dict[str, Any]] = []

    if from_is_release and to_is_release:
        # Both are releases - find branches between the two dates via application group
        group_id = from_branch_data.get("applicationGroupId") or to_branch_data.get(
            "applicationGroupId"
        )
        if group_id:
            # Get all branches for this app group
            all_branches = client.get(BranchEndpoints.list(group_id))
            if not isinstance(all_branches, list):
                all_branches = [all_branches] if all_branches else []

            from_date = from_branch_data.get("createdDate", "")
            to_date = to_branch_data.get("createdDate", "")

            if from_date and to_date:
                # Get releases (status 2=Inactive, 3=PublishedMain)
                releases = [b for b in all_branches if b.get("applicationStatusId") in (2, 3)]
                releases_in_range = [
                    b for b in releases if from_date < b.get("createdDate", "") <= to_date
                ]
                releases_in_range.sort(key=lambda x: x.get("createdDate", ""))
                releases_list = [
                    {
                        "id": b.get("id"),
                        "title": b.get("description") or b.get("commitTitle"),
                        "date": b.get("createdDate"),
                    }
                    for b in releases_in_range
                ]

                # Get feature branch commits (WorkspaceHistory = status 4)
                ctx.log("Fetching feature branch commits...")
                commits = [b for b in all_branches if b.get("applicationStatusId") == 4]
                commits_in_range = [
                    b for b in commits if from_date < b.get("createdDate", "") <= to_date
                ]
                commits_in_range.sort(key=lambda x: x.get("createdDate", ""))

                # For each commit, fetch its changes
                ctx.log(f"Fetching changes for {len(commits_in_range)} commits...")
                for commit_branch in commits_in_range:
                    commit_id = commit_branch.get("id")
                    title = commit_branch.get("description") or commit_branch.get("commitTitle")
                    commit_entry: dict[str, Any] = {
                        "id": commit_id,
                        "title": title,
                        "date": commit_branch.get("createdDate"),
                        "author": commit_branch.get("authorDisplayName"),
                    }

                    # Fetch the changes for this commit
                    try:
                        changes_data = client.get(
                            SourceControlEndpoints.history_branch_changes(commit_id)
                        )
                        if changes_data:
                            configs = changes_data.get("configs", [])
                            if configs:
                                commit_entry["changes"] = [
                                    {
                                        "reference_name": c.get("referenceName"),
                                        "type": c.get("configurationTypeId"),
                                        "modification": c.get("modificationTypeId"),
                                    }
                                    for c in configs
                                ]
                    except Exception:
                        pass  # Skip if we can't fetch changes

                    committed_branches_list.append(commit_entry)
    else:
        # Use set-based ancestry comparison for non-release branches
        from_history = client.get(SourceControlEndpoints.branch_history(from_branch))
        to_history = client.get(SourceControlEndpoints.branch_history(to_branch))

        # Normalize to lists
        if not isinstance(from_history, list):
            from_history = [from_history] if from_history else []
        if not isinstance(to_history, list):
            to_history = [to_history] if to_history else []

        # Find commits in target's ancestry that don't exist in source's ancestry
        from_commit_ids = {c.get("applicationId") for c in from_history if c.get("applicationId")}
        unique_commits = [c for c in to_history if c.get("applicationId") not in from_commit_ids]

    # Get dependency changes
    dep_changes: dict[str, list[Any]] = {"added": [], "removed": [], "updated": []}
    ctx.log("Comparing dependencies...")
    try:
        from_deps = client.get(DependencyEndpoints.list(from_branch))
        to_deps = client.get(DependencyEndpoints.list(to_branch))

        if not isinstance(from_deps, list):
            from_deps = [from_deps] if from_deps else []
        if not isinstance(to_deps, list):
            to_deps = [to_deps] if to_deps else []

        # Build lookup by reference name
        from_by_ref = {d.get("referenceName"): d for d in from_deps}
        to_by_ref = {d.get("referenceName"): d for d in to_deps}

        # Find added, removed, and updated
        for ref, dep in to_by_ref.items():
            if ref not in from_by_ref:
                dep_changes["added"].append(dep)
            else:
                from_dep = from_by_ref[ref]
                from_dep_ver = from_dep.get("marketPlaceApplicationVersionId")
                to_dep_ver = dep.get("marketPlaceApplicationVersionId")
                if from_dep_ver != to_dep_ver:
                    dep_changes["updated"].append(
                        {
                            "reference_name": ref,
                            "from_branch_id": from_dep.get("applicationId"),
                            "to_branch_id": dep.get("applicationId"),
                        }
                    )

        for ref, dep in from_by_ref.items():
            if ref not in to_by_ref:
                dep_changes["removed"].append(dep)
    except Exception:
        pass

    # Collect work item IDs from target branch
    workitem_ids: set[str] = set()
    try:
        workitems_data = client.get(WorkitemEndpoints.list(to_branch))
        if not isinstance(workitems_data, list):
            workitems_data = [workitems_data] if workitems_data else []
        workitem_ids = {w.get("externalId") for w in workitems_data if w.get("externalId")}
    except Exception:
        pass

    ctx.output(
        single(
            item={
                "from_branch": {
                    "id": from_branch_data.get("id"),
                    "name": from_branch_data.get("name"),
                    "reference_name": from_branch_data.get("referenceName"),
                    "status": from_branch_data.get("statusName"),
                    "is_release": from_branch_data.get("isRelease"),
                    "is_latest": from_branch_data.get("isLatest"),
                    "is_feature_branch": from_branch_data.get("isFeatureBranch"),
                    "modified_date": from_branch_data.get("modifiedDate"),
                },
                "to_branch": {
                    "id": to_branch_data.get("id"),
                    "name": to_branch_data.get("name"),
                    "reference_name": to_branch_data.get("referenceName"),
                    "status": to_branch_data.get("statusName"),
                    "is_release": to_branch_data.get("isRelease"),
                    "is_latest": to_branch_data.get("isLatest"),
                    "is_feature_branch": to_branch_data.get("isFeatureBranch"),
                    "modified_date": to_branch_data.get("modifiedDate"),
                },
                "releases": releases_list,
                "release_count": len(releases_list),
                "committed_branches": committed_branches_list,
                "committed_branch_count": len(committed_branches_list),
                "commits": unique_commits,
                "commit_count": len(unique_commits),
                "dependency_changes": dep_changes,
                "dependency_change_summary": {
                    "added": len(dep_changes["added"]),
                    "removed": len(dep_changes["removed"]),
                    "updated": len(dep_changes["updated"]),
                },
                "workitem_ids": list(workitem_ids),
                "workitem_count": len(workitem_ids),
            },
            semantic_key="branch_comparison",
            from_branch_id=from_branch,
            to_branch_id=to_branch,
        )
    )


@source.command("graph")
@click.option(
    "--branch",
    "-b",
    type=int,
    help="Branch ID (overrides global --branch)",
)
@click.option(
    "--max-depth",
    "-d",
    type=int,
    default=10,
    help="Maximum recursion depth (default: 10)",
)
@click.option(
    "--save-to",
    "-s",
    type=click.Path(dir_okay=False, writable=True),
    help="Save output to file",
)
@click.option(
    "--flat",
    is_flag=True,
    help="Output flat list instead of tree (shows all deps with isDirect flag)",
)
@pass_context
@require_auth
def graph(
    ctx: DxsContext,
    branch: int | None,
    max_depth: int,
    save_to: str | None,
    flat: bool,
) -> None:
    """Generate dependency graph for a branch.

    Shows the full dependency tree including both direct and transitive
    dependencies. Overlapping dependencies (those appearing via multiple
    paths) are explicitly identified.

    \b
    Examples:
        dxs source graph --branch 63588
        dxs source graph --branch 100 --save-to deps.yaml
        dxs source graph --branch 100 --flat

    \b
    Output includes:
        - Root application info
        - Summary of total/direct/transitive/overlapping deps
        - Full dependency tree with version info
        - Overlapping dependencies with all paths
    """
    from dxs.core.output.yaml_fmt import format_yaml

    branch_id = branch or ctx.branch
    if not branch_id:
        raise ValidationError(
            message="Branch ID is required. Use --branch or set DXS_BRANCH.",
            code="DXS-VAL-002",
            suggestions=[
                "Provide --branch flag: dxs source graph --branch 100",
                "Set environment variable: export DXS_BRANCH=100",
            ],
        )

    client = ApiClient()

    # Get branch info for root name
    ctx.log(f"Fetching branch info for {branch_id}...")
    branch_info = client.get(BranchEndpoints.get(branch_id))
    # Try referenceName first, then applicationDefinition.name, then fallback
    root_name = branch_info.get("referenceName")
    if not root_name:
        app_def = branch_info.get("applicationDefinition") or {}
        root_name = app_def.get("name", f"Branch-{branch_id}")

    # Fetch dependency data
    ctx.log("Fetching dependencies...")
    direct_deps, all_deps = _fetch_graph_dependencies(client, branch_id, ctx)

    if flat:
        # Simple flat output
        output = _format_flat_graph(all_deps, branch_id, root_name)
    else:
        # Build the full graph
        ctx.log("Building dependency graph...")
        adjacency = _build_graph_adjacency_map(client, direct_deps, ctx)

        all_paths: dict[int, list[list[str]]] = {}
        tree = _build_graph_tree_with_paths(
            direct_deps, adjacency, all_paths, [root_name], depth=0, max_depth=max_depth
        )

        # Find overlapping dependencies
        overlapping = _find_graph_overlapping_deps(all_paths, all_deps)

        output = _format_graph_output(
            root_name=root_name,
            branch_id=branch_id,
            direct_deps=direct_deps,
            all_deps=all_deps,
            tree=tree,
            overlapping=overlapping,
        )

    # Handle output destination
    if save_to:
        check_restricted_mode_for_option("--save-to")
        _save_graph_to_file(output, save_to, ctx)
    else:
        # Output directly (not through standard envelope)
        click.echo(format_yaml(output))


# Import and register subgroups (late imports to avoid circular dependencies)
from dxs.commands.branch import branch  # noqa: E402
from dxs.commands.document import document  # noqa: E402
from dxs.commands.explore import explore  # noqa: E402
from dxs.commands.repo import repo  # noqa: E402
from dxs.commands.servicepack import servicepack  # noqa: E402

source.add_command(branch)
source.add_command(document)
source.add_command(explore)
source.add_command(repo)
source.add_command(servicepack)
