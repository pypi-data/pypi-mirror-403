"""Marketplace commands: dxs marketplace [list|show|versions|version]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, MarketplaceEndpoints
from dxs.core.auth import require_auth
from dxs.utils.responses import list_response, search_response, single


@click.group()
def marketplace() -> None:
    """Marketplace application and version commands.

    Query marketplace applications (component packages) and their
    published versions. Useful for release note generation and
    dependency analysis.

    \b
    Examples:
        dxs marketplace list                    # List all marketplace apps
        dxs marketplace list --org 1            # List apps for organization
        dxs marketplace show 42                 # Show app details
        dxs marketplace versions 42             # List published versions
        dxs marketplace version 100             # Show version details
    """
    pass


@marketplace.command("list")
@click.option(
    "--org",
    "org_id",
    type=int,
    default=None,
    help="Filter by organization ID",
)
@pass_context
@require_auth
def marketplace_list(ctx: DxsContext, org_id: int | None) -> None:
    """List marketplace applications.

    Lists all marketplace applications (component packages) available
    in the system. Optionally filter by organization.

    \b
    Options:
        --org ID    Filter by organization ID

    \b
    Examples:
        dxs marketplace list
        dxs marketplace list --org 1
    """
    client = ApiClient()
    ctx.log("Fetching marketplace applications...")

    apps = client.get(MarketplaceEndpoints.list(org_id))

    # Normalize to list if not already
    if not isinstance(apps, list):
        apps = [apps] if apps else []

    ctx.output(
        list_response(
            items=apps,
            semantic_key="marketplace_applications",
            organization_id=org_id,
        )
    )


@marketplace.command()
@click.argument("app_id", type=int)
@pass_context
@require_auth
def show(ctx: DxsContext, app_id: int) -> None:
    """Show marketplace application details.

    \b
    Arguments:
        APP_ID  Marketplace application ID

    \b
    Example:
        dxs marketplace show 42
    """
    client = ApiClient()
    ctx.log(f"Fetching marketplace application {app_id}...")

    app_data = client.get(MarketplaceEndpoints.get(app_id))

    ctx.output(single(item=app_data, semantic_key="marketplace_application"))


@marketplace.command()
@click.argument("app_id", type=int)
@pass_context
@require_auth
def versions(ctx: DxsContext, app_id: int) -> None:
    """List published versions of a marketplace application.

    Returns all published versions of a marketplace application,
    including version codes, names, release dates, and release notes.
    Useful for tracking version history and generating changelogs.

    \b
    Arguments:
        APP_ID  Marketplace application ID

    \b
    Example:
        dxs marketplace versions 42
    """
    client = ApiClient()
    ctx.log(f"Fetching versions for marketplace application {app_id}...")

    version_list = client.get(MarketplaceEndpoints.versions(app_id))

    # Normalize to list if not already
    if not isinstance(version_list, list):
        version_list = [version_list] if version_list else []

    # Sort by release date descending (most recent first)
    version_list.sort(
        key=lambda v: v.get("releaseDate", ""),
        reverse=True,
    )

    ctx.output(
        list_response(
            items=version_list,
            semantic_key="versions",
            marketplace_application_id=app_id,
        )
    )


@marketplace.command()
@click.argument("version_id", type=int)
@pass_context
@require_auth
def version(ctx: DxsContext, version_id: int) -> None:
    """Show marketplace application version details.

    Returns detailed information about a specific published version,
    including release notes, version code, version name, and release date.

    \b
    Arguments:
        VERSION_ID  Marketplace application version ID

    \b
    Example:
        dxs marketplace version 100
    """
    client = ApiClient()
    ctx.log(f"Fetching marketplace version {version_id}...")

    version_data = client.get(MarketplaceEndpoints.version(version_id))

    ctx.output(single(item=version_data, semantic_key="version"))


@marketplace.command()
@click.argument("query")
@click.option(
    "--org",
    "org_id",
    type=int,
    default=None,
    help="Filter by organization ID",
)
@pass_context
@require_auth
def search(ctx: DxsContext, query: str, org_id: int | None) -> None:
    """Search marketplace applications by name or description.

    Performs case-insensitive search on application names and descriptions.

    \b
    Arguments:
        QUERY  Search term to match against names and descriptions

    \b
    Options:
        --org ID    Filter by organization ID

    \b
    Example:
        dxs marketplace search "Core"
        dxs marketplace search "utils" --org 1
    """
    client = ApiClient()
    ctx.log(f"Searching marketplace applications for '{query}'...")

    apps = client.get(MarketplaceEndpoints.list(org_id))

    # Normalize to list
    if not isinstance(apps, list):
        apps = [apps] if apps else []

    # Filter by name or description (case-insensitive)
    query_lower = query.lower()
    matches = [
        app
        for app in apps
        if query_lower in app.get("name", "").lower()
        or query_lower in (app.get("description") or "").lower()
        or query_lower in (app.get("uniqueIdentifier") or "").lower()
    ]

    ctx.output(
        search_response(
            items=matches,
            query=query,
            total_count=len(apps),
            semantic_key="marketplace_applications",
            organization_id=org_id,
        )
    )
