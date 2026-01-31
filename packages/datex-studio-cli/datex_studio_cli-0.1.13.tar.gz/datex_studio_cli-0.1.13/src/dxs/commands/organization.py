"""Organization commands: dxs organization [list|show|mine|search|app|connection]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, OrganizationEndpoints, RepoEndpoints
from dxs.core.api.endpoints import ApiConnectionEndpoints
from dxs.core.auth import require_auth
from dxs.utils.responses import list_response, search_response, single


@click.group()
def organization() -> None:
    """Organization commands.

    Manage and view organizations in Datex Studio.

    \b
    Examples:
        dxs organization list              # List all organizations
        dxs organization mine              # Show your organization
        dxs organization show 1            # Show organization by ID
        dxs organization search "Datex"    # Search by name
    """
    pass


@organization.command("list")
@pass_context
@require_auth
def org_list(ctx: DxsContext) -> None:
    """List all organizations.

    \b
    Example:
        dxs organization list
    """
    client = ApiClient()
    ctx.log("Fetching organizations...")

    orgs = client.get(OrganizationEndpoints.list())

    # Normalize to list if not already
    if not isinstance(orgs, list):
        orgs = [orgs] if orgs else []

    # Use list_response helper
    ctx.output(list_response(items=orgs, semantic_key="organizations"))


@organization.command()
@click.argument("org_id", type=int)
@pass_context
@require_auth
def show(ctx: DxsContext, org_id: int) -> None:
    """Show organization details.

    \b
    Arguments:
        ORG_ID  Organization ID

    \b
    Example:
        dxs organization show 1
    """
    client = ApiClient()
    ctx.log(f"Fetching organization {org_id}...")

    org_data = client.get(OrganizationEndpoints.get(org_id))

    # Use single helper
    ctx.output(single(item=org_data, semantic_key="organization"))


@organization.command()
@pass_context
@require_auth
def mine(ctx: DxsContext) -> None:
    """Show your organization.

    Returns the organization associated with the current user, including
    full details (description, createdDate, modifiedDate, devOpsOrganization).

    \b
    Example:
        dxs organization mine
    """
    client = ApiClient()
    ctx.log("Fetching your organization...")

    # First get the org ID from /organizations/mine
    org_basic = client.get(OrganizationEndpoints.mine())
    org_id = org_basic.get("id")

    if not org_id:
        # Fallback to basic response if no ID
        ctx.output(single(item=org_basic, semantic_key="organization"))
        return

    # Fetch full organization details with all fields
    ctx.log(f"Fetching full details for organization {org_id}...")
    org_data = client.get(OrganizationEndpoints.get(org_id))

    # Use single helper
    ctx.output(single(item=org_data, semantic_key="organization"))


@organization.command()
@click.argument("query")
@pass_context
@require_auth
def search(ctx: DxsContext, query: str) -> None:
    """Search organizations by name or description.

    Performs case-insensitive search on organization names and descriptions.

    \b
    Arguments:
        QUERY  Search term to match against organization names and descriptions

    \b
    Example:
        dxs organization search "Datex"
    """
    client = ApiClient()
    ctx.log(f"Searching organizations for '{query}'...")

    orgs = client.get(OrganizationEndpoints.list())

    # Normalize to list
    if not isinstance(orgs, list):
        orgs = [orgs] if orgs else []

    total_orgs = len(orgs)

    # Filter by name or description (case-insensitive)
    query_lower = query.lower()
    matches = [
        org
        for org in orgs
        if query_lower in org.get("name", "").lower()
        or query_lower in (org.get("description") or "").lower()
    ]

    # Use search_response helper
    ctx.output(
        search_response(
            items=matches,
            query=query,
            total_count=total_orgs,
            semantic_key="organizations",
        )
    )


# =============================================================================
# App subgroup: dxs organization app [list|get]
# =============================================================================


@organization.group()
def app() -> None:
    """Application definition commands.

    Manage and view application definitions (repos) within organizations.

    \b
    Examples:
        dxs organization app list --org 1     # List apps for organization
        dxs organization app list             # List all apps
        dxs organization app get 123          # Show app by ID
    """
    pass


@app.command("list")
@click.option("--org", "-o", type=int, default=None, help="Filter by organization ID")
@pass_context
@require_auth
def app_list(ctx: DxsContext, org: int | None) -> None:
    """List application definitions.

    Lists application definitions, optionally filtered by organization.
    Application definitions contain Azure app registration details needed
    for OData query execution.

    \b
    Examples:
        dxs organization app list --org 1     # List apps for organization 1
        dxs organization app list             # List all apps
    """
    client = ApiClient()

    if org:
        ctx.log(f"Fetching application definitions for organization {org}...")
    else:
        ctx.log("Fetching all application definitions...")

    apps = client.get(RepoEndpoints.list(org_id=org))

    # Normalize to list
    if not isinstance(apps, list):
        apps = [apps] if apps else []

    ctx.output(
        list_response(
            items=apps,
            semantic_key="application_definitions",
            organization_id=org,
        )
    )


@app.command("get")
@click.argument("app_id", type=int)
@pass_context
@require_auth
def app_get(ctx: DxsContext, app_id: int) -> None:
    """Get application definition by ID.

    Returns full details including Azure app registration IDs and secrets
    needed for OData query authentication.

    \b
    Arguments:
        APP_ID  Application definition ID

    \b
    Example:
        dxs organization app get 123
    """
    client = ApiClient()
    ctx.log(f"Fetching application definition {app_id}...")

    app_data = client.get(RepoEndpoints.get(app_id))

    ctx.output(single(item=app_data, semantic_key="application_definition"))


# =============================================================================
# Connection subgroup: dxs organization connection [list|get]
# =============================================================================


@organization.group()
def connection() -> None:
    """Footprint connection commands.

    Manage and view Footprint API connections for OData query execution.

    \b
    Examples:
        dxs organization connection list --org 1   # List connections for org
        dxs organization connection list           # List all connections
        dxs organization connection get 456        # Show connection by ID
    """
    pass


@connection.command("list")
@click.option("--org", "-o", type=int, default=None, help="Filter by organization ID")
@pass_context
@require_auth
def connection_list(ctx: DxsContext, org: int | None) -> None:
    """List Footprint connections.

    Lists Footprint API connections, optionally filtered by organization.
    Connections provide the OData endpoint URL for query execution.

    \b
    Examples:
        dxs organization connection list --org 1   # List for organization 1
        dxs organization connection list           # List all connections
    """
    client = ApiClient()

    if org:
        ctx.log(f"Fetching Footprint connections for organization {org}...")
    else:
        ctx.log("Fetching all Footprint connections...")

    connections = client.get(ApiConnectionEndpoints.list(org_id=org))

    # Normalize to list
    if not isinstance(connections, list):
        connections = [connections] if connections else []

    ctx.output(
        list_response(
            items=connections,
            semantic_key="footprint_connections",
            organization_id=org,
        )
    )


@connection.command("get")
@click.argument("connection_id", type=int)
@pass_context
@require_auth
def connection_get(ctx: DxsContext, connection_id: int) -> None:
    """Get Footprint connection by ID.

    Returns full connection details including the connection string
    (OData endpoint URL) needed for query execution.

    \b
    Arguments:
        CONNECTION_ID  Footprint connection ID

    \b
    Example:
        dxs organization connection get 456
    """
    client = ApiClient()
    ctx.log(f"Fetching Footprint connection {connection_id}...")

    conn_data = client.get(ApiConnectionEndpoints.get(connection_id))

    ctx.output(single(item=conn_data, semantic_key="footprint_connection"))
