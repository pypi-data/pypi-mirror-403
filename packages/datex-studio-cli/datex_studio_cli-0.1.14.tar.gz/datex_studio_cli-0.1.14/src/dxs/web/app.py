"""FastAPI application for Datex Studio web UI."""

import base64
import csv
import io
import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dxs.core.api import ApiClient
from dxs.core.api.endpoints import ApiConnectionEndpoints, OrganizationEndpoints
from dxs.core.footprint import get_footprint_token
from dxs.utils.config import get_settings

WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"

# Module-level cache for last query results (single-user local server)
_last_results: list[dict[str, Any]] = []


class QueryRequest(BaseModel):
    connection_id: int
    query: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Datex Studio", docs_url=None, redoc_url=None)

    @app.get("/api/organizations")
    async def list_organizations() -> dict[str, Any]:
        try:
            api_client = ApiClient()
            organizations = api_client.get(OrganizationEndpoints.list())
            if not isinstance(organizations, list):
                organizations = organizations.get("value", []) if isinstance(organizations, dict) else []
            mine_data = api_client.get(OrganizationEndpoints.mine())
            mine_id = mine_data.get("id") if isinstance(mine_data, dict) else None
        except Exception as e:
            return {"organizations": [], "mine_id": None, "error": str(e)}
        return {"organizations": organizations, "mine_id": mine_id}

    @app.get("/api/connections")
    async def list_connections(
        org_id: int | None = Query(default=None),
    ) -> dict[str, Any]:
        try:
            api_client = ApiClient()
            connections = api_client.get(ApiConnectionEndpoints.list(org_id=org_id, connection_type_id=1))
            if not isinstance(connections, list):
                connections = connections.get("value", []) if isinstance(connections, dict) else []
        except Exception as e:
            return {"connections": [], "error": str(e)}
        return {"connections": connections}

    @app.post("/api/query")
    async def execute_query(body: QueryRequest) -> dict[str, Any]:
        global _last_results
        try:
            api_client = ApiClient()
            conn_data = api_client.get(ApiConnectionEndpoints.get(body.connection_id))
            connection_string = conn_data.get("connectionString", "").rstrip("/")

            if not connection_string:
                return {
                    "rows": [],
                    "columns": [],
                    "error": f"Connection {body.connection_id} has no connectionString",
                    "count": 0,
                }

            token = get_footprint_token()
            result = _execute_odata(connection_string, body.query, token)

            rows = result.get("value", []) if isinstance(result, dict) else []
            if isinstance(result, dict) and "value" not in result:
                rows = [result]

            columns = list(rows[0].keys()) if rows else []
            _last_results = rows

        except Exception as e:
            return {"rows": [], "columns": [], "error": str(e), "count": 0}

        return {"rows": rows, "columns": columns, "count": len(rows)}

    @app.get("/api/export")
    async def export_results(
        fmt: str = Query(default="csv", alias="format"),
    ) -> StreamingResponse:
        if fmt == "json":
            content = json.dumps(_last_results, indent=2, default=str)
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=results.json"},
            )
        # CSV
        if not _last_results:
            content = ""
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(_last_results[0].keys()))
            writer.writeheader()
            writer.writerows(_last_results)
            content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=results.csv"},
        )

    @app.get("/api/metadata/entities")
    async def list_metadata_entities(
        connection_id: int = Query(...),
        refresh: bool = Query(default=False),
    ) -> dict[str, Any]:
        try:
            from dxs.core.footprint.edmx_parser import parse_edmx
            from dxs.core.footprint.metadata import MetadataCache

            cache = MetadataCache()
            xml = None

            if not refresh and cache.is_fresh(connection_id):
                xml = cache.get(connection_id)

            if xml is None:
                api_client = ApiClient()
                conn_data = api_client.get(ApiConnectionEndpoints.get(connection_id))
                connection_string = conn_data.get("connectionString", "").rstrip("/")
                if not connection_string:
                    return {"entities": [], "error": f"Connection {connection_id} has no connectionString"}

                token = get_footprint_token()
                url = f"{connection_string}/$metadata"
                x_caller = base64.b64encode(json.dumps({}).encode()).decode()

                with httpx.Client(timeout=settings.api_timeout if (settings := get_settings()) else 30) as client:
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

                conn_name = conn_data.get("name")
                cache.put(connection_id, xml, connection_name=conn_name)

            schema = parse_edmx(xml)
            entities = [
                {"name": es.name, "entity_type": es.entity_type}
                for es in schema.entity_sets.values()
            ]
        except Exception as e:
            return {"entities": [], "error": str(e)}
        return {"entities": entities}

    # Serve static files (Next.js export) at root — must be after API routes
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def _execute_odata(
    connection_string: str,
    query: str,
    token: str,
) -> dict[str, Any]:
    """Execute an OData GET request against the Footprint API."""
    settings = get_settings()
    url = f"{connection_string}/{query}"
    x_caller = base64.b64encode(json.dumps({}).encode()).decode()

    with httpx.Client(timeout=settings.api_timeout) as client:
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
