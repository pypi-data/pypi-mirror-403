"""Service Pack commands: dxs source servicepack [list|create]."""

from typing import Any

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, ApplicationGroupEndpoints, BranchEndpoints, RepoEndpoints
from dxs.core.api.models import BranchStatus
from dxs.core.auth import require_auth, verify_org_match
from dxs.utils.errors import ValidationError
from dxs.utils.restricted import restrict_in_restricted_mode
from dxs.utils.responses import list_response, single

# Group type constants
GROUP_TYPE_DEFAULT = 0
GROUP_TYPE_SERVICE_PACK = 1


def transform_group_output(group: dict[str, Any]) -> dict[str, Any]:
    """Transform application group data for output.

    Adds human-readable type information and removes internal fields.

    Args:
        group: Application group dictionary from API

    Returns:
        Transformed group dictionary
    """
    transformed = dict(group)

    # Add human-readable group type
    group_type_id = group.get("applicationGroupTypeId")
    if group_type_id == GROUP_TYPE_DEFAULT:
        transformed["groupType"] = "Default"
    elif group_type_id == GROUP_TYPE_SERVICE_PACK:
        transformed["groupType"] = "ServicePack"

    return transformed


@click.group()
def servicepack() -> None:
    """Service Pack commands.

    Manage Service Pack groups for maintenance branches. Service Packs allow
    creating hotfix/maintenance branches from published releases.

    \b
    Examples:
        dxs source servicepack list --repo 10
        dxs source servicepack create --repo 10 -d "Hotfix for v1.0.0"
    """
    pass


@servicepack.command("list")
@click.option(
    "--repo",
    "-r",
    type=int,
    help="Repository ID (or set DXS_REPO)",
)
@pass_context
@require_auth
def list_servicepacks(ctx: DxsContext, repo: int | None) -> None:
    """List Service Pack groups for a repository.

    Shows all Service Pack groups along with their source application.

    \b
    Options:
        --repo, -r   Repository ID (or set DXS_REPO env var)

    \b
    Examples:
        dxs source servicepack list --repo 10
    """
    repo_id = repo or ctx.repo
    if not repo_id:
        raise ValidationError(
            message="Repository ID required",
            suggestions=[
                "Use --repo flag: dxs source servicepack list --repo 10",
                "Set environment variable: export DXS_REPO=10",
            ],
        )

    client = ApiClient()
    ctx.log(f"Fetching Service Pack groups for repository {repo_id}...")

    # Fetch only Service Pack groups (type 1)
    groups = client.get(
        ApplicationGroupEndpoints.list(repo_id, group_type_id=GROUP_TYPE_SERVICE_PACK)
    )

    if not isinstance(groups, list):
        groups = [groups] if groups else []

    # Transform output
    groups = [transform_group_output(g) for g in groups]

    ctx.output(
        list_response(
            items=groups,
            semantic_key="servicepacks",
            total_count=len(groups),
            repository_id=repo_id,
        )
    )


@servicepack.command("create")
@click.option(
    "--repo",
    "-r",
    type=int,
    help="Repository ID (or set DXS_REPO)",
)
@click.option(
    "--description",
    "-d",
    default=None,
    help="Optional description for the Service Pack",
)
@pass_context
@require_auth
@restrict_in_restricted_mode("creates service packs")
def create_servicepack(
    ctx: DxsContext,
    repo: int | None,
    description: str | None,
) -> None:
    """Create a Service Pack from the published version.

    Creates a Service Pack group from the repository's published release
    (PublishedMain). This allows creating hotfix/maintenance branches for
    a specific released version.

    \b
    Notes:
        - Service Packs can only be created from published (PublishedMain) branches
        - The service pack name is automatically derived from the version
        - Only one Service Pack can be created per published version

    \b
    Options:
        --repo, -r         Repository ID (or set DXS_REPO env var)
        --description, -d  Optional description

    \b
    Examples:
        dxs source servicepack create --repo 10
        dxs source servicepack create --repo 10 -d "Hotfix for v1.0.0 production issues"
    """
    repo_id = repo or ctx.repo
    if not repo_id:
        raise ValidationError(
            message="Repository ID required",
            suggestions=[
                "Use --repo flag: dxs source servicepack create --repo 10",
                "Set environment variable: export DXS_REPO=10",
            ],
        )

    client = ApiClient()

    # Check organization mismatch - creating service packs requires ownership
    ctx.log("Verifying organization access...")
    repo_info = client.get(RepoEndpoints.get(repo_id))
    org_id = repo_info.get("organizationId")
    org_name = repo_info.get("organization", {}).get("name") if repo_info.get("organization") else None
    if org_id:
        verify_org_match(org_id, org_name)

    # Find the PublishedMain branch for this repo
    ctx.log(f"Finding published version for repository {repo_id}...")

    # Fetch all groups for this repository
    groups = client.get(ApplicationGroupEndpoints.list(repo_id))
    if not isinstance(groups, list):
        groups = [groups] if groups else []

    # Find the Default group (type 0) and fetch its branches
    default_group = next(
        (g for g in groups if g.get("applicationGroupTypeId") == GROUP_TYPE_DEFAULT),
        None,
    )

    if not default_group:
        raise ValidationError(
            message=f"No Default group found for repository {repo_id}",
            suggestions=[
                "Verify the repository ID is correct",
            ],
        )

    # Fetch branches from the Default group
    branches = client.get(BranchEndpoints.list(default_group["id"]))
    if not isinstance(branches, list):
        branches = [branches] if branches else []

    # Find the PublishedMain branch (status 3)
    published_branch = next(
        (b for b in branches if b.get("applicationStatusId") == BranchStatus.PUBLISHED_MAIN),
        None,
    )

    if not published_branch:
        raise ValidationError(
            message=f"No published version found for repository {repo_id}",
            suggestions=[
                "The repository must have a PublishedMain branch to create a Service Pack",
                "Publish the Main branch first before creating a Service Pack",
            ],
        )

    published_branch_id = published_branch["id"]
    published_branch_name = published_branch.get("name", f"Branch {published_branch_id}")

    ctx.log(
        f"Creating Service Pack from published version '{published_branch_name}' "
        f"(ID: {published_branch_id})..."
    )

    # Create the Service Pack group
    request_data: dict[str, Any] = {
        "applicationDefinitionId": repo_id,
        "sourceApplicationId": published_branch_id,
    }
    if description:
        request_data["description"] = description

    new_group = client.post(
        ApplicationGroupEndpoints.create(),
        data=request_data,
    )

    # Transform output
    new_group = transform_group_output(new_group)

    ctx.output(
        single(
            item=new_group,
            semantic_key="servicepack",
            repository_id=repo_id,
            source_branch_id=published_branch_id,
            source_branch_name=published_branch_name,
        )
    )


@servicepack.command("delete")
@click.argument("group_id", type=int)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Skip confirmation and delete immediately",
)
@pass_context
@require_auth
@restrict_in_restricted_mode("permanently deletes service packs")
def delete_servicepack(ctx: DxsContext, group_id: int, force: bool) -> None:
    """Delete a Service Pack group.

    Permanently deletes a Service Pack group. This action cannot be undone.

    \b
    Notes:
        - Only Service Pack groups with a single main branch can be deleted
        - Service Packs with published versions cannot be deleted

    \b
    Arguments:
        GROUP_ID  Service Pack group ID to delete

    \b
    Options:
        --force, -f  Skip confirmation prompt

    \b
    Examples:
        dxs source servicepack delete 5
        dxs source servicepack delete 5 --force
    """
    client = ApiClient()

    # Get group info first
    ctx.log(f"Fetching Service Pack group {group_id}...")
    group_info = client.get(ApplicationGroupEndpoints.get(group_id))

    group_name = group_info.get("name", f"Group {group_id}")
    group_type = group_info.get("applicationGroupTypeId")

    # Verify it's a Service Pack group
    if group_type != GROUP_TYPE_SERVICE_PACK:
        raise ValidationError(
            message=f"Group {group_id} is not a Service Pack group",
            suggestions=[
                "Use 'dxs source servicepack list --repo <id>' to find Service Pack groups",
                "Only Service Pack groups can be deleted with this command",
            ],
        )

    if not force:
        # Prompt for confirmation
        if not click.confirm(
            f"Are you sure you want to delete Service Pack '{group_name}' (ID: {group_id})? "
            "This action cannot be undone."
        ):
            ctx.output(
                single(
                    item={"deleted": False, "reason": "User cancelled"},
                    semantic_key="delete_result",
                    group_id=group_id,
                )
            )
            return

    ctx.log(f"Deleting Service Pack '{group_name}' (ID: {group_id})...")
    client.delete(ApplicationGroupEndpoints.delete(group_id))

    ctx.output(
        single(
            item={
                "deleted": True,
                "group_id": group_id,
                "group_name": group_name,
            },
            semantic_key="delete_result",
        )
    )
