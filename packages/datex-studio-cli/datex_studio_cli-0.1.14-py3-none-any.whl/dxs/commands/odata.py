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
from dxs.core.footprint import get_footprint_token
from dxs.core.footprint.edmx_parser import parse_edmx
from dxs.core.footprint.metadata import MetadataCache
from dxs.utils.config import get_settings
from dxs.utils.errors import ValidationError
from dxs.utils.resolvers import EntityResolver
from dxs.utils.responses import list_response, single


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

    # Step 2: Acquire Footprint token
    token = get_footprint_token()

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


@odata.group()
def metadata() -> None:
    """Explore OData $metadata for a connection.

    \b
    Examples:
        dxs odata metadata fetch --connection-id 32
        dxs odata metadata entities --connection-id 32
        dxs odata metadata describe Warehouses --connection-id 32
    """
    pass


def _fetch_metadata(
    ctx: DxsContext,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
    refresh: bool,
) -> tuple[str, int]:
    """Fetch and cache $metadata XML for a connection.

    Returns:
        Tuple of (xml_text, resolved_connection_id).
    """
    resolved_id = _resolve_connection(ctx, connection_id, connection, org)
    cache = MetadataCache()

    if not refresh and cache.is_fresh(resolved_id):
        xml = cache.get(resolved_id)
        if xml is not None:
            ctx.log("Using cached metadata.")
            return xml, resolved_id

    # Fetch connection details
    ctx.log(f"Fetching connection {resolved_id}...")
    api_client = ApiClient()
    conn_data = api_client.get(ApiConnectionEndpoints.get(resolved_id))
    connection_string = conn_data.get("connectionString", "").rstrip("/")
    connection_name = conn_data.get("name")

    if not connection_string:
        raise ValidationError(
            message=f"API connection {resolved_id} has no connectionString",
            code="DXS-ODATA-003",
            suggestions=["Verify the API connection is properly configured"],
        )

    # Fetch $metadata
    ctx.log("Downloading $metadata...")
    token = get_footprint_token()
    settings = get_settings()
    url = f"{connection_string}/$metadata"

    x_caller = base64.b64encode(json.dumps({}).encode()).decode()

    with httpx.Client(timeout=settings.api_timeout) as client:
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "x-caller": x_caller,
                "Accept": "application/xml",
            },
        )
        response.raise_for_status()
        xml = response.text

    cache.put(resolved_id, xml, connection_name=connection_name)
    ctx.log("Metadata cached.")
    return xml, resolved_id


_CONNECTION_OPTIONS = [
    click.option(
        "--connection-id",
        "-c",
        type=int,
        default=None,
        help="API connection ID",
    ),
    click.option(
        "--connection",
        type=str,
        default=None,
        help="API connection name (requires --org)",
    ),
    click.option(
        "--org",
        "-o",
        type=str,
        default=None,
        help="Organization name or ID",
    ),
    click.option(
        "--refresh",
        is_flag=True,
        default=False,
        help="Force re-download, ignoring cache",
    ),
]


def _add_connection_options(f: Any) -> Any:
    """Apply shared connection options to a command."""
    for option in reversed(_CONNECTION_OPTIONS):
        f = option(f)
    return f


@metadata.command()
@_add_connection_options
@pass_context
@require_auth
def fetch(
    ctx: DxsContext,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
    refresh: bool,
) -> None:
    """Download and cache $metadata XML for a connection.

    \b
    Examples:
        dxs odata metadata fetch --connection-id 32
        dxs odata metadata fetch --org Datex --connection Prod --refresh
    """
    xml, resolved_id = _fetch_metadata(ctx, connection_id, connection, org, refresh)
    schema = parse_edmx(xml)
    ctx.output(
        single(
            item={
                "connection_id": resolved_id,
                "entity_type_count": len(schema.entity_types),
                "entity_set_count": len(schema.entity_sets),
                "status": "cached",
            },
            semantic_key="metadata_fetch",
            connection_id=resolved_id,
        )
    )


@metadata.command()
@_add_connection_options
@pass_context
@require_auth
def entities(
    ctx: DxsContext,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
    refresh: bool,
) -> None:
    """List entity sets from cached $metadata.

    Auto-fetches metadata if not cached.

    \b
    Examples:
        dxs odata metadata entities --connection-id 32
    """
    xml, resolved_id = _fetch_metadata(ctx, connection_id, connection, org, refresh)
    schema = parse_edmx(xml)

    items = []
    for es in schema.entity_sets.values():
        et = schema.entity_types.get(es.entity_type)
        items.append(
            {
                "name": es.name,
                "entity_type": es.entity_type,
                "property_count": len(et.properties) if et else 0,
            }
        )

    ctx.output(
        list_response(
            items=items,
            semantic_key="entity_sets",
            connection_id=resolved_id,
        )
    )


@metadata.command()
@click.argument("entity_name")
@_add_connection_options
@pass_context
@require_auth
def describe(
    ctx: DxsContext,
    entity_name: str,
    connection_id: int | None,
    connection: str | None,
    org: str | None,
    refresh: bool,
) -> None:
    """Show details for a specific entity type or entity set.

    \b
    Examples:
        dxs odata metadata describe Warehouses --connection-id 32
    """
    xml, resolved_id = _fetch_metadata(ctx, connection_id, connection, org, refresh)
    schema = parse_edmx(xml)

    # Try matching as entity set name first, then entity type name
    et = None
    matched_name = entity_name

    if entity_name in schema.entity_sets:
        es = schema.entity_sets[entity_name]
        et = schema.entity_types.get(es.entity_type)
        matched_name = es.name
    else:
        # Try matching as entity type (qualified or unqualified)
        for qualified, entity_type in schema.entity_types.items():
            if entity_type.name == entity_name or qualified == entity_name:
                et = entity_type
                matched_name = qualified
                break

    if et is None:
        raise ValidationError(
            message=f"Entity '{entity_name}' not found in metadata",
            code="DXS-ODATA-META-001",
            suggestions=[
                f"Run 'dxs odata metadata entities -c {resolved_id}' to list available entities",
            ],
        )

    ctx.output(
        single(
            item={
                "name": matched_name,
                "keys": et.keys,
                "properties": [p.model_dump() for p in et.properties],
                "navigation_properties": [n.model_dump() for n in et.navigation_properties],
            },
            semantic_key="entity_detail",
            connection_id=resolved_id,
        )
    )
