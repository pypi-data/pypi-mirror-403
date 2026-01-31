"""Raw API request command: dxs api [METHOD] [URL] [PAYLOAD]."""

import json
from typing import Any

import click
import httpx

from dxs.cli import DxsContext, pass_context
from dxs.core.auth import get_access_token, require_auth
from dxs.utils.config import get_settings
from dxs.utils.config import is_restricted_mode
from dxs.utils.errors import ApiError, RestrictedModeError
from dxs.utils.responses import single


@click.command()
@click.argument(
    "method", type=click.Choice(["GET", "POST", "PUT", "PATCH", "DELETE"], case_sensitive=False)
)
@click.argument("url")
@click.argument("payload", required=False, default=None)
@click.option(
    "--headers",
    "-H",
    multiple=True,
    help="Additional headers in format 'Key: Value'",
)
@pass_context
@require_auth
def api(
    ctx: DxsContext, method: str, url: str, payload: str | None, headers: tuple[str, ...]
) -> None:
    """Make raw API requests with automatic authentication.

    Automatically adds Bearer token authentication and handles the HTTP request.
    Useful for testing and exploring API endpoints.

    \b
    Arguments:
        METHOD   HTTP method (GET, POST, PUT, PATCH, DELETE)
        URL      Full URL or relative path (e.g., /organizations/mine)
        PAYLOAD  JSON payload for POST/PUT/PATCH (optional)

    \b
    Options:
        -H, --headers  Additional headers (can be specified multiple times)

    \b
    Examples:
        dxs api GET /organizations/mine
        dxs api GET https://wavelength.host/api/organizations/1
        dxs api POST /applications '{"name": "test"}'
        dxs api GET /branches -H "X-Custom: value"
    """
    # Block mutating methods in restricted mode
    if is_restricted_mode() and method.upper() != "GET":
        raise RestrictedModeError(
            command_name=f"api {method.upper()}",
            reason="performs mutating API requests",
        )

    settings = get_settings()
    token = get_access_token()

    # Determine if URL is relative or absolute
    if url.startswith("http://") or url.startswith("https://"):
        full_url = url
    else:
        # Relative path - prepend base URL
        base_url = settings.api_base_url.rstrip("/")
        path = url if url.startswith("/") else f"/{url}"
        full_url = f"{base_url}{path}"

    ctx.log(f"Making {method} request to {full_url}")

    # Build headers
    request_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Parse additional headers
    for header in headers:
        if ":" in header:
            key, value = header.split(":", 1)
            request_headers[key.strip()] = value.strip()

    # Parse payload if provided
    payload_data = None
    if payload:
        try:
            payload_data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ApiError(
                message=f"Invalid JSON payload: {e}",
                code="DXS-API-PAYLOAD-001",
                suggestions=["Ensure the payload is valid JSON"],
            ) from e

    # Make the request
    try:
        with httpx.Client(timeout=settings.api_timeout) as client:
            response = client.request(
                method=method.upper(),
                url=full_url,
                headers=request_headers,
                json=payload_data if payload_data else None,
            )

            # Parse response
            response_data: dict[str, Any] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": str(response.url),
                "method": method.upper(),
            }

            # Try to parse body as JSON
            try:
                response_data["body"] = response.json()
            except Exception:
                # Not JSON - return as text
                response_data["body"] = response.text

            # Add request info for context
            response_data["request"] = {
                "url": full_url,
                "method": method.upper(),
                "headers": request_headers,
            }
            if payload_data:
                response_data["request"]["payload"] = payload_data

            ctx.output(
                single(
                    item=response_data,
                    semantic_key="api_response",
                )
            )

    except httpx.RequestError as e:
        raise ApiError(
            message=f"Request failed: {e}",
            code="DXS-API-REQUEST-001",
            details={"url": full_url, "error": str(e)},
        ) from e
