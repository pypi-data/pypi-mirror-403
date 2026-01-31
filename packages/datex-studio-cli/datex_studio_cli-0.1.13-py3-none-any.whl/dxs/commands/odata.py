"""OData commands: dxs odata [execute].

Implements OData query execution against Footprint API connections
using the user's delegated access token.

Flow:
1. Fetch connection details (connectionString) from Wavelength
2. Acquire Footprint API token via refresh token (delegated permissions)
3. Execute OData query directly against the Footprint API
"""

import base64
import json
from typing import Any

import click
import httpx

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient
from dxs.core.api.endpoints import ApiConnectionEndpoints
from dxs.core.auth import require_auth
from dxs.core.auth.decorators import get_access_token_for_scopes
from dxs.utils.config import get_settings
from dxs.utils.errors import ValidationError
from dxs.utils.resolvers import EntityResolver
from dxs.utils.responses import single


@click.group()
def odata() -> None:
    """OData query execution commands.

    Execute OData queries directly against Footprint API connections
    using delegated user authentication.

    \b
    Examples:
        dxs odata execute --connection-id 32 -q 'Warehouses?$top=10'
        dxs odata execute --org Datex --connection Prod -q 'Warehouses?$top=10'
    """
    pass


@odata.command()
@click.option(
    "--connection-id",
    "-c",
    type=int,
    default=None,
    help="API connection ID (use 'dxs organization connection list' to find IDs)",
)
@click.option(
    "--connection",
    type=str,
    default=None,
    help="API connection name (requires --org)",
)
@click.option(
    "--org",
    "-o",
    type=str,
    default=None,
    help="Organization name or ID (required when using --connection by name)",
)
@click.option(
    "--query",
    "-q",
    type=str,
    required=True,
    help="OData query string (e.g., 'Warehouses?$select=Code,Name&$top=10')",
)
@pass_context
@require_auth
def execute(
    ctx: DxsContext,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
    query: str,
) -> None:
    """Execute an OData query against a Footprint API connection.

    Uses the logged-in user's delegated permissions to authenticate
    with the Footprint API.

    \b
    Examples:
        dxs odata execute --connection-id 32 -q 'Warehouses?$top=5'
        dxs odata execute --org Datex --connection Demo -q 'Warehouses?$top=5'
    """
    # Resolve connection ID
    resolved_connection_id = _resolve_connection(ctx, connection_id, connection, org)

    settings = get_settings()

    # Step 1: Fetch connection details
    ctx.log(f"Fetching API connection {resolved_connection_id}...")
    api_client = ApiClient()
    conn_data = api_client.get(ApiConnectionEndpoints.get(resolved_connection_id))
    connection_string = conn_data.get("connectionString", "").rstrip("/")

    if not connection_string:
        ctx.output_error(
            ValidationError(
                message=f"API connection {resolved_connection_id} has no connectionString",
                code="DXS-ODATA-003",
                suggestions=["Verify the API connection is properly configured"],
            )
        )
        raise SystemExit(1)

    # Step 2: Acquire Footprint token via delegated permissions
    token = get_access_token_for_scopes([settings.footprint_scope])

    # Step 3: Execute OData query against Footprint
    ctx.log(f"Executing OData query: {query[:80]}{'...' if len(query) > 80 else ''}")
    result = _execute_footprint_odata(
        connection_string=connection_string,
        query=query,
        token=token,
        timeout=settings.api_timeout,
    )

    ctx.output(
        single(
            item=result,
            semantic_key="odata_result",
            query=query,
            connection_id=resolved_connection_id,
        )
    )


def _resolve_connection(
    ctx: DxsContext,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
) -> int:
    """Resolve connection from either --connection-id or --org + --connection."""
    if connection_id is not None and connection is not None:
        raise click.UsageError("Use either --connection-id or --connection, not both.")

    if connection_id is not None:
        return connection_id

    if connection is not None:
        if org is None:
            raise click.UsageError("--org is required when using --connection by name.")
        resolver = EntityResolver()
        org_id = resolver.resolve_org(org)
        return resolver.resolve_connection(connection, org_id=org_id)

    raise click.UsageError("Provide either --connection-id or --connection (with --org).")


def _execute_footprint_odata(
    connection_string: str,
    query: str,
    token: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """Execute an OData GET request against the Footprint API."""
    url = f"{connection_string}/{query}"

    # Build x-caller header (empty user context)
    x_caller = base64.b64encode(json.dumps({}).encode()).decode()

    with httpx.Client(timeout=timeout) as client:
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-caller": x_caller,
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
