"""Azure DevOps commands: dxs devops [workitem|workitems]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.auth import require_auth
from dxs.core.devops import AzureDevOpsClient
from dxs.utils.errors import ValidationError
from dxs.utils.responses import list_response, single


@click.group()
def devops() -> None:
    """Azure DevOps work item commands.

    Query work items from Azure DevOps. Requires that the Azure
    app registration has delegated permissions for Azure DevOps.

    \b
    Examples:
        dxs devops workitem 1234 --org myorg
        dxs devops workitems 1234,1235,1236 --org myorg
    """
    pass


@devops.command()
@click.argument("workitem_id", type=int)
@click.option(
    "--org",
    "organization",
    required=True,
    help="Azure DevOps organization name",
)
@click.option(
    "--expand",
    type=click.Choice(["None", "Relations", "Links", "All"], case_sensitive=False),
    default=None,
    help="Expand options for related data",
)
@pass_context
@require_auth
def workitem(
    ctx: DxsContext,
    workitem_id: int,
    organization: str,
    expand: str | None,
) -> None:
    """Get a single work item by ID.

    Fetches detailed information about an Azure DevOps work item
    including title, type, state, description, and metadata.

    \b
    Arguments:
        WORKITEM_ID  Azure DevOps work item ID

    \b
    Options:
        --org ORG    Azure DevOps organization name (required)
        --expand     Expand options (None, Relations, Links, All)

    \b
    Example:
        dxs devops workitem 1234 --org myorg
        dxs devops workitem 1234 --org myorg --expand Relations
    """
    ctx.log(f"Fetching work item {workitem_id} from {organization}...")

    with AzureDevOpsClient(organization) as client:
        item = client.get_workitem(workitem_id, expand=expand)

    ctx.output(
        single(
            item={"summary": item.to_summary(), "fields": item.fields},
            semantic_key="workitem",
            organization=organization,
        )
    )


@devops.command()
@click.argument("ids", type=str)
@click.option(
    "--org",
    "organization",
    required=True,
    help="Azure DevOps organization name",
)
@click.option(
    "--description",
    is_flag=True,
    default=False,
    help="Include work item description (HTML)",
)
@click.option(
    "--discussions",
    is_flag=True,
    default=False,
    help="Include work item discussions",
)
@pass_context
@require_auth
def workitems(
    ctx: DxsContext,
    ids: str,
    organization: str,
    description: bool,
    discussions: bool,
) -> None:
    """Get multiple work items by IDs (batch).

    Fetches detailed information about multiple Azure DevOps work
    items in a single request. Maximum 200 work items per request.

    \b
    Arguments:
        IDS  Comma-separated work item IDs (e.g., 1234,1235,1236)

    \b
    Options:
        --org ORG       Azure DevOps organization name (required)
        --description   Include work item descriptions
        --discussions   Include work item discussions

    \b
    Examples:
        dxs devops workitems 1234,1235,1236 --org myorg
        dxs devops workitems 1234 --org myorg --description
        dxs devops workitems 1234 --org myorg --description --discussions
    """
    # Parse comma-separated IDs
    try:
        id_list = [int(id_str.strip()) for id_str in ids.split(",") if id_str.strip()]
    except ValueError as e:
        raise ValidationError(
            message="Invalid work item IDs. Must be comma-separated integers.",
            code="DXS-VAL-002",
            suggestions=["Use format: 1234,1235,1236"],
        ) from e

    if not id_list:
        raise ValidationError(
            message="At least one work item ID is required.",
            code="DXS-VAL-003",
        )

    if len(id_list) > 200:
        raise ValidationError(
            message="Maximum 200 work items can be fetched in a single request.",
            code="DXS-VAL-004",
            suggestions=["Split your request into multiple batches"],
        )

    ctx.log(f"Fetching {len(id_list)} work items from {organization}...")

    with AzureDevOpsClient(organization) as client:
        items = client.get_workitems_batch(id_list)

        # Fetch discussions if requested
        if discussions:
            ctx.log(f"Fetching discussions for {len(items)} work items...")
            for item in items:
                item.discussions = client.get_workitem_discussions(item.id)

    # Convert to summaries with optional fields
    summaries = [
        item.to_summary(include_description=description, include_discussions=discussions)
        for item in items
    ]

    # Group IDs by type for metadata (avoid duplicating full data)
    ids_by_type: dict[str, list[int]] = {}
    for item in items:
        item_type = item.work_item_type
        if item_type not in ids_by_type:
            ids_by_type[item_type] = []
        ids_by_type[item_type].append(item.id)

    ctx.output(
        list_response(
            items=summaries,
            semantic_key="workitems",
            organization=organization,
            requested_ids=id_list,
            ids_by_type=ids_by_type,
            type_summary={k: len(v) for k, v in ids_by_type.items()},
            includes_description=description,
            includes_discussions=discussions,
        )
    )


@devops.command()
@click.argument("query")
@click.option(
    "--org",
    "organization",
    required=True,
    help="Azure DevOps organization name",
)
@click.option(
    "--project",
    default=None,
    help="Azure DevOps project name (optional)",
)
@pass_context
@require_auth
def search(
    ctx: DxsContext,
    query: str,
    organization: str,
    project: str | None,
) -> None:
    """Search work items by title (simplified search).

    Note: This is a simplified search that fetches recent work items
    and filters client-side. For complex queries, use WIQL directly
    through the Azure DevOps web interface.

    \b
    Arguments:
        QUERY  Search term to match against work item titles

    \b
    Options:
        --org ORG        Azure DevOps organization name (required)
        --project PROJ   Azure DevOps project name (optional)

    \b
    Example:
        dxs devops search "login bug" --org myorg
    """
    ctx.output(
        single(
            item={
                "message": "Work item search is not yet implemented",
                "suggestion": "Use 'dxs devops workitem <id>' with known work item IDs",
            },
            semantic_key="search_status",
            query=query,
            organization=organization,
            project=project,
        )
    )
