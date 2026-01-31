"""Repository commands: dxs source repo [list|show|search]."""

from datetime import datetime

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, RepoEndpoints
from dxs.core.api.models import APPLICATION_DEFINITION_TYPE_ALIASES
from dxs.core.auth import require_auth
from dxs.utils import EntityResolver, ListFilter, filter_by_date_range
from dxs.utils.errors import ValidationError
from dxs.utils.responses import list_response, search_response, single


@click.group()
def repo() -> None:
    """Repository commands.

    Manage and view repositories (application definitions) in Datex Studio.
    A repository contains all branches and configurations for an application.

    \b
    Examples:
        dxs source repo list                # List all repositories
        dxs source repo list --org 1        # List repos for organization
        dxs source repo show 10             # Show repository details
        dxs source repo search "FootPrint"  # Search by name
    """
    pass


def transform_repo_output(repo: dict) -> dict:
    """Transform repository data for output.

    Removes unwanted fields, renames applicationDefinitionType to type,
    simplifies organization object, and reorders uniqueIdentifier first.

    Args:
        repo: Repository data dictionary from API

    Returns:
        Transformed repository dictionary
    """
    # Start with uniqueIdentifier first
    transformed = {}
    if "uniqueIdentifier" in repo:
        transformed["uniqueIdentifier"] = repo["uniqueIdentifier"]

    # Fields to exclude from output
    excluded_fields = {
        "organizationId",
        "applicationDefinitionTypeId",
        "applications",
        "uniqueIdentifier",  # Already added first
        "applicationDefinitionType",  # Will be renamed
        "organization",  # Will be filtered
    }

    # Copy desired fields
    for key, value in repo.items():
        if key in excluded_fields or key.startswith("azAppReg"):
            continue
        transformed[key] = value

    # Rename applicationDefinitionType -> type
    if "applicationDefinitionType" in repo:
        transformed["type"] = repo["applicationDefinitionType"]

    # Filter organization object to only include id, name, description
    if "organization" in repo and isinstance(repo["organization"], dict):
        org = repo["organization"]
        transformed["organization"] = {
            k: v for k, v in org.items() if k in ["id", "name", "description"]
        }

    return transformed


def enrich_repo_with_branches(repo: dict, client: ApiClient, ctx: DxsContext) -> dict:
    """Enrich repository with branch information.

    Fetches branches for the repository and adds:
    - lastCommit: Info from most recent History branch (applicationStatusId=4)
    - activeBranch: Info from PublishedMain branch (applicationStatusId=3)
    - workspaceActiveCount: Count of WorkspaceActive branches (applicationStatusId=5)

    Args:
        repo: Repository dictionary
        client: API client for fetching branch data
        ctx: CLI context for logging

    Returns:
        Repository dictionary enriched with branch metadata
    """
    from dxs.core.api import ApplicationGroupEndpoints, BranchEndpoints

    repo_id = repo.get("id")
    if not repo_id:
        return repo

    try:
        # Fetch branches via application groups (API requires this flow)
        groups = client.get(ApplicationGroupEndpoints.list(repo_id))
        if not isinstance(groups, list):
            groups = [groups] if groups else []

        branches: list[dict] = []
        for group in groups:
            group_id = group.get("id")
            if not group_id:
                continue
            group_branches = client.get(BranchEndpoints.list(group_id))
            if not isinstance(group_branches, list):
                group_branches = [group_branches] if group_branches else []
            branches.extend(group_branches)

        # Find branches by applicationStatusId
        history_branches = [b for b in branches if b.get("applicationStatusId") == 4]
        active_branches = [b for b in branches if b.get("applicationStatusId") == 3]
        workspace_branches = [b for b in branches if b.get("applicationStatusId") == 5]

        # Add last commit info (most recent History branch by commitDate)
        if history_branches:
            history_branches.sort(key=lambda b: b.get("commitDate", ""), reverse=True)
            last_commit = history_branches[0]
            repo["lastCommit"] = {
                "id": last_commit.get("id"),
                "name": last_commit.get("name"),
                "commitDate": last_commit.get("commitDate"),
                "commitMessage": last_commit.get("commitMessage"),
                "userId": last_commit.get("userId"),
            }

        # Add active branch info
        if active_branches:
            active = active_branches[0]
            repo["activeBranch"] = {
                "id": active.get("id"),
                "name": active.get("name"),
                "modifiedDate": active.get("modifiedDate"),
            }

        # Add workspace branch count
        repo["workspaceActiveCount"] = len(workspace_branches)

    except Exception as e:
        ctx.log(f"Warning: Could not fetch branches for repo {repo_id}: {e}")

    return repo


@repo.command("list")
@click.option(
    "--org",
    type=int,
    help="Filter by organization ID",
)
@click.option(
    "--org-name",
    type=str,
    help="Filter by organization name (resolved to ID)",
)
@click.option(
    "--type",
    type=click.Choice(
        ["web", "mobile", "componentmodule", "api", "portal"],
        case_sensitive=False,
    ),
    help="Filter by application type",
)
@click.option(
    "--with-branches",
    is_flag=True,
    default=False,
    help="Include branch information (last commit, active branch, workspace count)",
)
@click.option(
    "--published-after",
    type=click.DateTime(),
    help="Filter by publish date (after)",
)
@click.option(
    "--published-before",
    type=click.DateTime(),
    help="Filter by publish date (before)",
)
@click.option(
    "--commit-after",
    type=click.DateTime(),
    help="Filter by last commit date (after) - requires --with-branches",
)
@click.option(
    "--commit-before",
    type=click.DateTime(),
    help="Filter by last commit date (before) - requires --with-branches",
)
@click.option(
    "--branch-modified-after",
    type=click.DateTime(),
    help="Filter by branch modification date (after) - requires --with-branches",
)
@click.option(
    "--branch-modified-before",
    type=click.DateTime(),
    help="Filter by branch modification date (before) - requires --with-branches",
)
@pass_context
@require_auth
def repo_list(
    ctx: DxsContext,
    org: int | None,
    org_name: str | None,
    type: str | None,
    with_branches: bool,
    published_after: datetime | None,
    published_before: datetime | None,
    commit_after: datetime | None,
    commit_before: datetime | None,
    branch_modified_after: datetime | None,
    branch_modified_before: datetime | None,
) -> None:
    """List repositories with filtering.

    Lists all repositories, optionally filtered by organization and type.
    Use --org or --org-name to scope to an organization.

    \b
    Application Types:
        web              Web applications
        mobile           Mobile applications
        componentmodule  Reusable component modules
        api              Backend APIs
        portal           Portal applications

    \b
    Options:
        --org                    Organization ID
        --org-name               Organization name (resolved to ID)
        --type                   Filter by application type
        --with-branches          Include branch information
        --published-after        Filter by publish date (after)
        --published-before       Filter by publish date (before)
        --commit-after           Filter by last commit date (after)
        --commit-before          Filter by last commit date (before)
        --branch-modified-after  Filter by branch modification (after)
        --branch-modified-before Filter by branch modification (before)

    \b
    Examples:
        dxs source repo list
        dxs source repo list --org 1
        dxs source repo list --org-name "Datex"
        dxs source repo list --type componentmodule
        dxs source repo list --with-branches
        dxs source repo list --type web --published-after 2024-01-01
    """
    # Validate: commit/branch date filters require --with-branches
    if any([commit_after, commit_before, branch_modified_after, branch_modified_before]):
        if not with_branches:
            raise ValidationError(
                message="Commit and branch date filters require --with-branches flag",
                suggestions=["Add --with-branches to enable branch-based date filtering"],
            )

    resolver = EntityResolver()
    client = ApiClient()

    # Resolve organization ID from --org or --org-name
    org_id = org or ctx.org
    if org_name and not org_id:
        org_id = resolver.resolve_org(org_name)

    # Fetch repositories
    if org_id:
        ctx.log(f"Fetching repositories for organization {org_id}...")
    else:
        ctx.log("Fetching all repositories...")

    repos = client.get(RepoEndpoints.list(int(org_id) if org_id else None))

    # Normalize to list
    if not isinstance(repos, list):
        repos = [repos] if repos else []

    total_count = len(repos)

    # Apply type filter (client-side)
    if type:
        type_id = APPLICATION_DEFINITION_TYPE_ALIASES.get(type.lower())
        if type_id:
            ctx.log(f"Filtering by type: {type}...")
            repos = [r for r in repos if r.get("applicationDefinitionTypeId") == type_id]

    # Apply published date filters (using modifiedDate as proxy for published)
    repos = (
        ListFilter(repos)
        .by_date_range("modifiedDate", after=published_after, before=published_before)
        .result()
    )

    # Enrich with branch data if requested
    if with_branches:
        ctx.log("Fetching branch information for repositories...")
        repos = [enrich_repo_with_branches(r, client, ctx) for r in repos]

        # Apply commit date filters (only valid with branch data)
        if commit_after or commit_before:
            repos = [
                r
                for r in repos
                if "lastCommit" in r
                and filter_by_date_range(
                    [r["lastCommit"]], "commitDate", commit_after, commit_before
                )
            ]

        # Apply branch modified date filters (only valid with branch data)
        if branch_modified_after or branch_modified_before:
            repos = [
                r
                for r in repos
                if "activeBranch" in r
                and filter_by_date_range(
                    [r["activeBranch"]],
                    "modifiedDate",
                    branch_modified_after,
                    branch_modified_before,
                )
            ]

    filtered_count = len(repos)

    # Transform output (remove unwanted fields, rename, reorder)
    repos = [transform_repo_output(r) for r in repos]

    # Build metadata
    metadata_kwargs = {
        "organization_id": org_id,
        "total_count": total_count,
        "filtered_count": filtered_count,
    }

    # Add applied filters to metadata
    if type:
        metadata_kwargs["type_filter"] = type
    if published_after:
        metadata_kwargs["published_after"] = published_after.isoformat()
    if published_before:
        metadata_kwargs["published_before"] = published_before.isoformat()
    if with_branches:
        metadata_kwargs["includes_branch_info"] = True
    if commit_after:
        metadata_kwargs["commit_after"] = commit_after.isoformat()
    if commit_before:
        metadata_kwargs["commit_before"] = commit_before.isoformat()
    if branch_modified_after:
        metadata_kwargs["branch_modified_after"] = branch_modified_after.isoformat()
    if branch_modified_before:
        metadata_kwargs["branch_modified_before"] = branch_modified_before.isoformat()

    # Output results
    ctx.output(
        list_response(
            items=repos,
            semantic_key="repositories",
            **metadata_kwargs,
        )
    )


@repo.command()
@click.argument("repo_id", type=int)
@pass_context
@require_auth
def show(ctx: DxsContext, repo_id: int) -> None:
    """Show repository details.

    \b
    Arguments:
        REPO_ID  Repository ID

    \b
    Example:
        dxs source repo show 10
    """
    client = ApiClient()
    ctx.log(f"Fetching repository {repo_id}...")

    repo_data = client.get(RepoEndpoints.get(repo_id))

    # Transform output
    repo_data = transform_repo_output(repo_data)

    # Use single helper
    ctx.output(single(item=repo_data, semantic_key="repository"))


@repo.command()
@click.argument("query")
@click.option(
    "--org",
    type=int,
    help="Filter by organization ID",
)
@click.option(
    "--org-name",
    type=str,
    help="Filter by organization name (resolved to ID)",
)
@pass_context
@require_auth
def search(ctx: DxsContext, query: str, org: int | None, org_name: str | None) -> None:
    """Search repositories by name.

    Performs case-insensitive search on repository names and descriptions.

    \b
    Arguments:
        QUERY  Search term to match against repository names

    \b
    Options:
        --org       Organization ID to filter by
        --org-name  Organization name (resolved to ID)

    \b
    Examples:
        dxs source repo search "FootPrint"
        dxs source repo search "Portal" --org 1
        dxs source repo search "Portal" --org-name "Datex"
    """
    resolver = EntityResolver()
    client = ApiClient()

    # Resolve organization ID
    org_id = org or ctx.org
    if org_name and not org_id:
        org_id = resolver.resolve_org(org_name)

    if org_id:
        ctx.log(f"Searching repositories for '{query}' in organization {org_id}...")
    else:
        ctx.log(f"Searching all repositories for '{query}'...")

    repos = client.get(RepoEndpoints.list(int(org_id) if org_id else None))

    # Normalize to list
    if not isinstance(repos, list):
        repos = [repos] if repos else []

    total_repos = len(repos)

    # Filter by name or description (case-insensitive)
    query_lower = query.lower()
    matches = [
        r
        for r in repos
        if query_lower in r.get("name", "").lower()
        or query_lower in (r.get("description") or "").lower()
    ]

    # Transform output
    matches = [transform_repo_output(r) for r in matches]

    # Use search_response with organization_id in metadata
    ctx.output(
        search_response(
            items=matches,
            query=query,
            total_count=total_repos,
            semantic_key="repositories",
            organization_id=org_id,
        )
    )
