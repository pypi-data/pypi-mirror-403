"""CRM commands: dxs crm [case]."""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from dxs.cli import DxsContext
from markdownify import markdownify as md

from dxs.core.auth import require_auth
from dxs.core.dynamics.client import DynamicsClient
from dxs.core.output.yaml_fmt import LiteralString
from dxs.utils.responses import count_response, list_response, search_response
from dxs.utils.restricted import check_restricted_mode_for_option

# Regex pattern to extract attachment URLs from markdown
# Matches: ![...](/api/data/v9.1/msdyn_richtextfiles(UUID)/msdyn_imageblob/$value...)
_ATTACHMENT_URL_PATTERN = re.compile(
    r"!\[[^\]]*\]\((/api/data/v[\d.]+/msdyn_richtextfiles\(([a-f0-9-]+)\)/msdyn_imageblob/\$value[^)]*)\)"
)


# Case status code to human-readable mapping
_CASE_STATUS_LABELS = {
    0: "Active",
    1: "Resolved",
    2: "Cancelled",
}


def _extract_attachment_urls(markdown: str | None) -> list[dict[str, str]]:
    """Extract attachment URLs and UUIDs from markdown content.

    Parses markdown to find embedded rich text file references like:
    ![](/api/data/v9.1/msdyn_richtextfiles(uuid)/msdyn_imageblob/$value?size=full)

    Args:
        markdown: Markdown string to parse.

    Returns:
        List of dicts with 'url' (API path) and 'uuid' keys.
    """
    if not markdown:
        return []

    matches = _ATTACHMENT_URL_PATTERN.findall(markdown)
    return [{"url": url, "uuid": uuid} for url, uuid in matches]


def _replace_attachment_urls(
    markdown: str | LiteralString | None,
    url_to_path: dict[str, str],
) -> str | LiteralString | None:
    """Replace attachment URLs in markdown with local file paths.

    Args:
        markdown: Markdown string with embedded attachment URLs.
        url_to_path: Mapping of original URLs to local file paths.

    Returns:
        Updated markdown with URLs replaced by local paths.
    """
    if not markdown or not url_to_path:
        return markdown

    result = str(markdown)
    for url, path in url_to_path.items():
        result = result.replace(url, path)

    # Preserve LiteralString type for multiline content
    if isinstance(markdown, LiteralString):
        return LiteralString(result)
    return result


def _detect_file_extension(data: bytes) -> str:
    """Detect file extension from magic bytes.

    Args:
        data: Raw file bytes.

    Returns:
        File extension with leading dot (e.g., ".png"), or empty string if unknown.
    """
    # Common image magic bytes
    signatures = [
        (b"\x89PNG\r\n\x1a\n", ".png"),
        (b"\xff\xd8\xff", ".jpg"),
        (b"GIF87a", ".gif"),
        (b"GIF89a", ".gif"),
        (b"RIFF", ".webp"),  # Check for WEBP signature after RIFF
        (b"BM", ".bmp"),
        (b"\x00\x00\x01\x00", ".ico"),
        # PDF
        (b"%PDF", ".pdf"),
        # SVG (XML-based, check for svg tag)
        (b"<?xml", ".svg"),  # Needs secondary check for <svg
        (b"<svg", ".svg"),
    ]

    for magic, ext in signatures:
        if data.startswith(magic):
            # Special case: RIFF could be WEBP or other formats
            if magic == b"RIFF" and len(data) >= 12:
                if data[8:12] == b"WEBP":
                    return ".webp"
                continue  # Not WEBP, skip
            # Special case: XML could be SVG or other XML
            if magic == b"<?xml":
                if b"<svg" in data[:1000]:
                    return ".svg"
                return ".xml"
            return ext

    return ""


def _download_attachments(
    client: DynamicsClient,
    incidents: list[dict[str, Any]],
    save_dir: Path,
    ctx: "DxsContext",
) -> list[dict[str, Any]]:
    """Download all attachments from incident descriptions.

    Downloads attachments and updates incident descriptions in-place to
    replace API URLs with local file paths.

    Args:
        client: DynamicsClient instance for API calls.
        incidents: List of formatted incidents with markdown descriptions.
            Modified in-place to update description URLs.
        save_dir: Directory to save attachments.
        ctx: CLI context for logging.

    Returns:
        List of dicts with 'uuid', 'case_id', 'path' for each downloaded file.
    """
    downloaded = []

    for incident in incidents:
        description = incident.get("description")
        if not description:
            continue

        # Handle LiteralString or regular string
        desc_str = str(description)
        attachments = _extract_attachment_urls(desc_str)

        if not attachments:
            continue

        # Track URL to path mappings for this incident
        url_to_path: dict[str, str] = {}

        for attachment in attachments:
            uuid = attachment["uuid"]
            url = attachment["url"]

            try:
                ctx.debug(f"Downloading attachment {uuid}...")
                blob_data = client.download_blob(url)
                ext = _detect_file_extension(blob_data)
                file_path = save_dir / f"{uuid}{ext}"
                file_path.write_bytes(blob_data)
                downloaded.append(
                    {
                        "uuid": uuid,
                        "case_id": incident.get("id"),
                        "ticketnumber": incident.get("ticketnumber"),
                        "path": str(file_path),
                        "size": len(blob_data),
                    }
                )
                # Map original URL to local path
                url_to_path[url] = str(file_path)
                ctx.debug(f"Saved attachment to: {file_path}")
            except Exception as e:
                ctx.log(f"Warning: Failed to download attachment {uuid}: {e}")

        # Update incident description with local paths
        if url_to_path:
            incident["description"] = _replace_attachment_urls(incident["description"], url_to_path)

    return downloaded


def _html_to_markdown(html: str | None) -> str | LiteralString | None:
    """Convert HTML content to Markdown.

    Args:
        html: HTML string to convert.

    Returns:
        Markdown string (LiteralString for multiline), or None if input was None/empty.
    """
    if not html:
        return None

    # Convert HTML to Markdown, stripping script/style tags
    markdown = md(html, strip=["script", "style"]).strip()

    # Use LiteralString for multiline content (renders as YAML block scalar)
    # LiteralString automatically handles trailing whitespace cleanup
    if "\n" in markdown:
        return LiteralString(markdown)

    return markdown


def _format_incident(incident: dict[str, Any]) -> dict[str, Any]:
    """Format a raw incident from Dynamics CRM for display.

    Args:
        incident: Raw incident data from Dynamics CRM API.

    Returns:
        Formatted incident dictionary.
    """
    # Get customer name from expanded relationship
    customer_name = None
    if incident.get("customerid_account"):
        customer_name = incident["customerid_account"].get("name")
    elif incident.get("customerid_contact"):
        customer_name = incident["customerid_contact"].get("fullname")

    # Get owner name from OData annotation (formatted value for lookup)
    owner_name = incident.get("_ownerid_value@OData.Community.Display.V1.FormattedValue")

    # Get human-readable labels from OData annotations for picklist fields
    priority_label = incident.get("prioritycode@OData.Community.Display.V1.FormattedValue")
    severity_label = incident.get("severitycode@OData.Community.Display.V1.FormattedValue")
    business_impact_label = incident.get(
        "daa_immediatebusinessimpact@OData.Community.Display.V1.FormattedValue"
    )

    # Get status label
    statecode = incident.get("statecode", 0)
    status_label = _CASE_STATUS_LABELS.get(statecode, f"Unknown ({statecode})")

    # Convert HTML description to Markdown
    description = _html_to_markdown(incident.get("description"))

    # Resolution text (may contain HTML)
    resolution = _html_to_markdown(incident.get("adx_resolution"))

    result = {
        "id": incident.get("incidentid"),
        "ticketnumber": incident.get("ticketnumber"),
        "title": incident.get("title"),
        "description": description,
        "status": status_label,
        "statecode": statecode,
        "priority": priority_label,
        "severity": severity_label,
        "business_impact": business_impact_label,
        "owner": owner_name,
        "customer": customer_name,
        "customer_id": incident.get("_customerid_value"),
        "is_escalated": incident.get("isescalated"),
        "escalated_on": incident.get("escalatedon"),
        "resolve_by": incident.get("resolveby"),
        "response_by": incident.get("responseby"),
        "resolution": resolution,
        "resolution_date": incident.get("adx_resolutiondate"),
        "created": incident.get("createdon"),
        "modified": incident.get("modifiedon"),
    }

    # Include notes if present (from $expand)
    annotations = incident.get("Incident_Annotation", [])
    if annotations:
        result["notes"] = [_format_annotation(ann) for ann in annotations]

    return result


def _format_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    """Format a raw annotation from Dynamics CRM for display.

    Args:
        annotation: Raw annotation data from Dynamics CRM API.

    Returns:
        Formatted annotation dictionary.
    """
    note_text = annotation.get("notetext") or ""

    # Convert HTML to markdown if present
    if note_text and ("<" in note_text or "&" in note_text):
        note_text = _html_to_markdown(note_text)

    # Use LiteralString for multiline content
    if note_text and "\n" in note_text:
        note_text = LiteralString(note_text)

    # The OData annotation response may include the formatted value for lookups
    # Check for the OData annotation (@OData.Community.Display.V1.FormattedValue)
    author = annotation.get("_createdby_value@OData.Community.Display.V1.FormattedValue")
    if not author:
        # Fall back to looking up ID if formatted value not available
        author = annotation.get("_createdby_value")

    result: dict[str, Any] = {
        "id": annotation.get("annotationid"),
        "subject": annotation.get("subject"),
        "text": note_text,
        "author": author,
        "created": annotation.get("createdon"),
    }

    # Include attachment info if present
    if annotation.get("filename"):
        result["attachment"] = {
            "filename": annotation.get("filename"),
            "mimetype": annotation.get("mimetype"),
            "filesize": annotation.get("filesize"),
        }

    return result


@click.group()
def crm() -> None:
    """Dynamics CRM commands.

    Commands for interacting with Dynamics CRM / Dataverse.

    \b
    Setup (one-time):
        1. Configure your CRM URL:
           dxs config set dynamics_crm_url https://yourorg.crm.dynamics.com
        2. Login to grant Dynamics CRM consent:
           dxs auth login

    \b
    Available subcommands:
        account  Account (company) management
        case     Support case (incident) management
    """
    pass


@click.group()
def case() -> None:
    """Support case commands.

    Search and view support cases (incidents) from Dynamics CRM.

    \b
    Examples:
        dxs crm case search "shipping"              # Search all cases
        dxs crm case search "CAS-001"               # Search by case number
        dxs crm case search --status active         # List active cases
        dxs crm case search "issue" --status active # Search active cases
    """
    pass


# Register case as subcommand of crm
crm.add_command(case)


@case.command()
@click.argument("query", required=False, default=None)
@click.option(
    "--status",
    type=click.Choice(["active", "resolved", "cancelled", "all"], case_sensitive=False),
    default="all",
    help="Filter by case status (default: all)",
)
@click.option(
    "--account",
    "-a",
    type=str,
    default=None,
    help="Filter by account name (partial match)",
)
@click.option(
    "--since",
    type=str,
    default=None,
    help="Filter to cases created on or after this date (YYYY-MM-DD)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit to N records (no auto-pagination)",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Page size for auto-pagination (default: 500)",
)
@click.option(
    "--count-only",
    is_flag=True,
    default=False,
    help="Return only the count, no records",
)
@click.option(
    "--save-attachments",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Download attachments to specified directory (requires --save)",
)
@click.option(
    "--include-notes",
    is_flag=True,
    default=False,
    help="Include notes/annotations for each case in the output.",
)
@click.pass_obj
@require_auth
def search(
    ctx: "DxsContext",
    query: str | None,
    status: str,
    account: str | None,
    since: str | None,
    limit: int | None,
    batch_size: int | None,
    count_only: bool,
    save_attachments: Path | None,
    include_notes: bool,
) -> None:
    """Search for support cases in Dynamics CRM.

    Searches case number, title, and description fields. Results are ordered
    by most recently modified.

    By default, retrieves ALL matching records using automatic pagination
    with a batch size of 500. Use --limit to get only a specific number
    of records without pagination.

    \b
    Arguments:
        QUERY  Optional search text (searches case number, title, description)

    \b
    Examples:
        dxs crm case search "shipping delay"
        dxs crm case search --account "Crane Worldwide" --since 2025-01-01
        dxs crm case search --status active --limit 50    # First 50 only
        dxs crm case search --account "Contoso" --batch-size 100
        dxs crm case search --account "Crane" --count-only
        dxs crm case search --account "Crane" --save cases.yaml
    """
    client = DynamicsClient()

    # Normalize status
    status_filter = None if status == "all" else status

    if query:
        ctx.log(f"Searching cases for '{query}'...")
    else:
        ctx.log("Fetching cases...")

    if status_filter:
        ctx.log(f"Filtering by status: {status_filter}")
    if account:
        ctx.log(f"Filtering by account: {account}")
    if since:
        ctx.log(f"Filtering by created date >= {since}")

    # Count-only mode: just get the count
    if count_only:
        result = client.search_incidents(
            query=query,
            status=status_filter,
            account=account,
            since=since,
            limit=1,  # Minimal data, we just want the count
        )
        total = result.get("@odata.count", 0)
        ctx.output(
            count_response(
                total_count=total,
                semantic_key="cases",
                status_filter=status_filter,
                account_filter=account,
                since_filter=since,
            )
        )
        return

    if limit:
        # Single request, no pagination
        result = client.search_incidents(
            query=query,
            status=status_filter,
            account=account,
            since=since,
            limit=limit,
            include_notes=include_notes,
        )
        raw_incidents = result.get("value", [])
        total_count = result.get("@odata.count", len(raw_incidents))
    else:
        # Auto-pagination: fetch all records
        page_size = batch_size or 500
        all_incidents: list[dict] = []

        result = client.search_incidents(
            query=query,
            status=status_filter,
            account=account,
            since=since,
            limit=page_size,
            include_notes=include_notes,
        )
        all_incidents.extend(result.get("value", []))
        total_count = result.get("@odata.count", len(all_incidents))

        # Follow @odata.nextLink until all records are fetched
        while "@odata.nextLink" in result:
            ctx.log(f"Fetching next page ({len(all_incidents)} of {total_count} records)...")
            result = client.get_by_next_link(result["@odata.nextLink"])
            all_incidents.extend(result.get("value", []))

        raw_incidents = all_incidents

    # Format incidents for display
    incidents = [_format_incident(inc) for inc in raw_incidents]

    # Download attachments if requested
    attachments_downloaded = []
    if save_attachments:
        check_restricted_mode_for_option("--save-attachments", "downloads files to the filesystem")
        if not ctx.save_path:
            from dxs.utils.errors import ValidationError

            raise ValidationError(
                message="--save-attachments requires --save to be specified",
                code="DXS-CRM-001",
                suggestions=[
                    "Add --save <filepath> to save output and attachments",
                    "Example: dxs --save cases.yaml crm case search --save-attachments ./attachments",
                ],
            )

        # Create attachments directory
        save_attachments.mkdir(parents=True, exist_ok=True)
        ctx.log(f"Downloading attachments to: {save_attachments}")

        attachments_downloaded = _download_attachments(client, incidents, save_attachments, ctx)

        if attachments_downloaded:
            ctx.log(f"Downloaded {len(attachments_downloaded)} attachment(s)")

    # Build search response
    response_kwargs = {
        "items": incidents,
        "query": query or "(all)",
        "total_count": total_count,
        "semantic_key": "cases",
        "status_filter": status_filter,
        "account_filter": account,
        "since_filter": since,
    }

    # Include attachment metadata if any were downloaded
    if attachments_downloaded:
        response_kwargs["attachments"] = attachments_downloaded

    ctx.output(search_response(**response_kwargs))


@case.command()
@click.option(
    "--select",
    type=str,
    default=None,
    help="OData $select - comma-separated field names to return",
)
@click.option(
    "--filter",
    "-f",
    type=str,
    default=None,
    help='OData $filter - filter expression (e.g., "statecode eq 0")',
)
@click.option(
    "--orderby",
    type=str,
    default=None,
    help='OData $orderby - sort expression (e.g., "modifiedon desc")',
)
@click.option(
    "--expand",
    type=str,
    default=None,
    help="OData $expand - related entities to include",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit to N records (no auto-pagination)",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Page size for auto-pagination (default: 500)",
)
@click.option(
    "--count-only",
    is_flag=True,
    default=False,
    help="Return only the count, no records",
)
@click.option(
    "--save-attachments",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Download attachments to specified directory (requires --save)",
)
@click.pass_obj
@require_auth
def query(
    ctx: "DxsContext",
    select: str | None,
    filter: str | None,
    orderby: str | None,
    expand: str | None,
    limit: int | None,
    batch_size: int | None,
    count_only: bool,
    save_attachments: Path | None,
) -> None:
    """Execute a custom OData query against cases.

    Provides full control over OData query parameters for AI-constructed queries.
    Use 'dxs crm metadata incident' to see available field names.

    By default, retrieves ALL matching records using automatic pagination
    with a batch size of 500. Use --limit to get only a specific number
    of records without pagination.

    \b
    OData Filter Operators:
        eq, ne, gt, ge, lt, le    Comparison
        and, or, not              Logical
        contains(), startswith(), endswith()  String functions

    \b
    Examples:
        dxs crm case query -s "ticketnumber,title" -f "statecode eq 0" --limit 10

        dxs crm case query -s "ticketnumber,title,prioritycode" \\
          -f "contains(title,'shipping') and statecode eq 0" \\
          -o "modifiedon desc"

        dxs crm case query -f "statecode eq 0" --count-only
    """
    client = DynamicsClient()

    ctx.log("Executing OData query...")
    if filter:
        ctx.log(f"Filter: {filter}")

    # Count-only mode: just get the count
    if count_only:
        result = client.query_incidents(
            select=select,
            filter=filter,
            orderby=orderby,
            expand=expand,
            top=1,
        )
        total = result.get("@odata.count", 0)
        ctx.output(count_response(total_count=total, semantic_key="cases"))
        return

    if limit:
        # Single request, no pagination
        result = client.query_incidents(
            select=select,
            filter=filter,
            orderby=orderby,
            expand=expand,
            top=limit,
        )
        raw_cases = result.get("value", [])
    else:
        # Auto-pagination: fetch all records
        page_size = batch_size or 500
        all_cases: list[dict] = []

        result = client.query_incidents(
            select=select,
            filter=filter,
            orderby=orderby,
            expand=expand,
            top=page_size,
        )
        all_cases.extend(result.get("value", []))
        total_count = result.get("@odata.count", len(all_cases))

        # Follow @odata.nextLink until all records are fetched
        while "@odata.nextLink" in result:
            ctx.log(f"Fetching next page ({len(all_cases)} of {total_count} records)...")
            result = client.get_by_next_link(result["@odata.nextLink"])
            all_cases.extend(result.get("value", []))

        raw_cases = all_cases

    # Light formatting: convert description HTML to markdown if present
    formatted_cases = []
    for case_data in raw_cases:
        formatted = dict(case_data)  # Copy the raw data

        # Convert description if present
        if "description" in formatted and formatted["description"]:
            formatted["description"] = _html_to_markdown(formatted["description"])

        formatted_cases.append(formatted)

    # Download attachments if requested
    attachments_downloaded = []
    if save_attachments:
        check_restricted_mode_for_option("--save-attachments", "downloads files to the filesystem")
        if not ctx.save_path:
            from dxs.utils.errors import ValidationError

            raise ValidationError(
                message="--save-attachments requires --save to be specified",
                code="DXS-CRM-001",
                suggestions=[
                    "Add --save <filepath> to save output and attachments",
                    "Example: dxs --save cases.yaml crm case query --save-attachments ./attachments",
                ],
            )

        # Create attachments directory
        save_attachments.mkdir(parents=True, exist_ok=True)
        ctx.log(f"Downloading attachments to: {save_attachments}")

        attachments_downloaded = _download_attachments(
            client, formatted_cases, save_attachments, ctx
        )

        if attachments_downloaded:
            ctx.log(f"Downloaded {len(attachments_downloaded)} attachment(s)")

    # Build response
    if attachments_downloaded:
        ctx.output(
            list_response(
                items=formatted_cases, semantic_key="cases", attachments=attachments_downloaded
            )
        )
    else:
        ctx.output(list_response(items=formatted_cases, semantic_key="cases"))


# =============================================================================
# Account Commands
# =============================================================================


def _format_account(account: dict[str, Any]) -> dict[str, Any]:
    """Format a raw account from Dynamics CRM for display.

    Args:
        account: Raw account data from Dynamics CRM API.

    Returns:
        Formatted account dictionary.
    """
    # Build location string
    city = account.get("address1_city")
    state = account.get("address1_stateorprovince")
    location = None
    if city and state:
        location = f"{city}, {state}"
    elif city:
        location = city
    elif state:
        location = state

    return {
        "id": account.get("accountid"),
        "name": account.get("name"),
        "account_number": account.get("accountnumber"),
        "phone": account.get("telephone1"),
        "email": account.get("emailaddress1"),
        "location": location,
        "created": account.get("createdon"),
        "modified": account.get("modifiedon"),
    }


@click.group()
def account() -> None:
    """Account commands.

    List and search for accounts (companies) in Dynamics CRM.

    \b
    Examples:
        dxs crm account list                  # List accounts
        dxs crm account search "Contoso"      # Search by name
        dxs crm account search "Texas" -l 10  # Search with limit
    """
    pass


# Register account as subcommand of crm
crm.add_command(account)


@account.command("list")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit to N records (no auto-pagination)",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=None,
    help="Page size for auto-pagination (default: 500)",
)
@click.option(
    "--count-only",
    is_flag=True,
    default=False,
    help="Return only the count, no records",
)
@click.pass_obj
@require_auth
def account_list(
    ctx: "DxsContext", limit: int | None, batch_size: int | None, count_only: bool
) -> None:
    """List accounts in Dynamics CRM.

    Returns active accounts ordered by name.

    By default, retrieves ALL accounts using automatic pagination
    with a batch size of 500. Use --limit to get only a specific number
    of records without pagination.

    \b
    Examples:
        dxs crm account list
        dxs crm account list --limit 100
        dxs crm account list --count-only
    """
    client = DynamicsClient()

    ctx.log("Fetching accounts...")

    # Count-only mode
    if count_only:
        result = client.list_accounts(limit=1)
        total = result.get("@odata.count", 0)
        ctx.output(count_response(total_count=total, semantic_key="accounts"))
        return

    if limit:
        # Single request, no pagination
        result = client.list_accounts(limit=limit)
        raw_accounts = result.get("value", [])
    else:
        # Auto-pagination: fetch all records
        page_size = batch_size or 500
        all_accounts: list[dict] = []

        result = client.list_accounts(limit=page_size)
        all_accounts.extend(result.get("value", []))
        total_count = result.get("@odata.count", len(all_accounts))

        while "@odata.nextLink" in result:
            ctx.log(f"Fetching next page ({len(all_accounts)} of {total_count} records)...")
            result = client.get_by_next_link(result["@odata.nextLink"])
            all_accounts.extend(result.get("value", []))

        raw_accounts = all_accounts

    # Format accounts for display
    accounts = [_format_account(acc) for acc in raw_accounts]

    ctx.output(list_response(items=accounts, semantic_key="accounts"))


@account.command("search")
@click.argument("query")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit to N records (no auto-pagination)",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=None,
    help="Page size for auto-pagination (default: 500)",
)
@click.option(
    "--count-only",
    is_flag=True,
    default=False,
    help="Return only the count, no records",
)
@click.pass_obj
@require_auth
def account_search(
    ctx: "DxsContext", query: str, limit: int | None, batch_size: int | None, count_only: bool
) -> None:
    """Search for accounts in Dynamics CRM.

    Searches account names for the given query.

    By default, retrieves ALL matching accounts using automatic pagination
    with a batch size of 500. Use --limit to get only a specific number
    of records without pagination.

    \b
    Arguments:
        QUERY  Search text to match against account name

    \b
    Examples:
        dxs crm account search "Contoso"
        dxs crm account search "Texas" --limit 10
        dxs crm account search "Corp" --count-only
    """
    client = DynamicsClient()

    ctx.log(f"Searching accounts for '{query}'...")

    # Count-only mode
    if count_only:
        result = client.search_accounts(query=query, limit=1)
        total = result.get("@odata.count", 0)
        ctx.output(count_response(total_count=total, semantic_key="accounts"))
        return

    if limit:
        # Single request, no pagination
        result = client.search_accounts(query=query, limit=limit)
        raw_accounts = result.get("value", [])
        total_count = result.get("@odata.count", len(raw_accounts))
    else:
        # Auto-pagination: fetch all records
        page_size = batch_size or 500
        all_accounts: list[dict] = []

        result = client.search_accounts(query=query, limit=page_size)
        all_accounts.extend(result.get("value", []))
        total_count = result.get("@odata.count", len(all_accounts))

        while "@odata.nextLink" in result:
            ctx.log(f"Fetching next page ({len(all_accounts)} of {total_count} records)...")
            result = client.get_by_next_link(result["@odata.nextLink"])
            all_accounts.extend(result.get("value", []))

        raw_accounts = all_accounts

    # Format accounts for display
    accounts = [_format_account(acc) for acc in raw_accounts]

    ctx.output(
        search_response(
            items=accounts,
            query=query,
            total_count=total_count,
            semantic_key="accounts",
        )
    )


# =============================================================================
# Metadata Commands
# =============================================================================


def _get_localized_label(obj: dict[str, Any] | None) -> str | None:
    """Extract localized label from Dynamics metadata object."""
    if not obj:
        return None
    localized_labels = obj.get("LocalizedLabels", [])
    if localized_labels:
        label = localized_labels[0].get("Label")
        return str(label) if label is not None else None
    return None


def _list_entities(ctx: "DxsContext") -> None:
    """List all entity definitions in Dynamics CRM."""
    client = DynamicsClient()

    ctx.log("Fetching entity definitions...")

    result = client.list_entities()

    # Extract, format, and sort entities by logical name
    raw_entities = result.get("value", [])
    raw_entities.sort(key=lambda e: e.get("LogicalName", ""))

    formatted_entities = []
    for entity in raw_entities:
        formatted_entities.append(
            {
                "name": entity.get("LogicalName"),
                "display_name": _get_localized_label(entity.get("DisplayName")),
                "description": _get_localized_label(entity.get("Description")),
                "is_custom": entity.get("IsCustomEntity"),
            }
        )

    ctx.output(list_response(items=formatted_entities, semantic_key="entities"))


def _get_entity_metadata(ctx: "DxsContext", entity_name: str, relationships: bool) -> None:
    """Get metadata for a specific entity."""
    client = DynamicsClient()

    ctx.log(f"Fetching metadata for '{entity_name}'...")

    result = client.get_entity_fields(entity_name)

    # Extract and format fields (filter to readable attributes only, sort by name)
    raw_fields = result.get("value", [])
    readable_fields = [f for f in raw_fields if f.get("IsValidForRead")]
    readable_fields.sort(key=lambda f: f.get("LogicalName", ""))

    formatted_fields = []
    for field in readable_fields:
        formatted_fields.append(
            {
                "name": field.get("LogicalName"),
                "display_name": _get_localized_label(field.get("DisplayName")),
                "type": field.get("AttributeType"),
                "description": _get_localized_label(field.get("Description")),
            }
        )

    # Output fields
    ctx.output(list_response(items=formatted_fields, semantic_key="fields"))

    # Add relationships if requested
    if relationships:
        ctx.log("Fetching relationships...")
        rels = client.get_entity_relationships(entity_name)

        formatted_relationships = []

        # Format ManyToOne relationships (lookups - this entity references another)
        for rel in rels.get("many_to_one", []):
            formatted_relationships.append(
                {
                    "name": rel.get("ReferencingAttribute"),
                    "schema_name": rel.get("SchemaName"),
                    "target_entity": rel.get("ReferencedEntity"),
                    "target_attribute": rel.get("ReferencedAttribute"),
                    "type": "ManyToOne",
                }
            )

        # Format OneToMany relationships (this entity is referenced by others)
        for rel in rels.get("one_to_many", []):
            formatted_relationships.append(
                {
                    "name": rel.get("SchemaName"),
                    "referencing_entity": rel.get("ReferencingEntity"),
                    "referencing_attribute": rel.get("ReferencingAttribute"),
                    "type": "OneToMany",
                }
            )

        ctx.output(list_response(items=formatted_relationships, semantic_key="relationships"))


@click.command("metadata")
@click.argument("entity_name", required=False, default=None)
@click.option(
    "--relationships",
    "-r",
    is_flag=True,
    default=False,
    help="Include navigation properties (relationships to other entities)",
)
@click.pass_obj
@require_auth
def metadata(ctx: "DxsContext", entity_name: str | None, relationships: bool) -> None:
    """Entity metadata exploration.

    Explore Dynamics CRM entity definitions, fields, and relationships.
    Useful for understanding the data model and constructing OData queries.

    Use "entities" as the argument to list all available entities.
    Use any other entity name to show its fields.

    \b
    Arguments:
        ENTITY_NAME  "entities" to list all, or an entity name (e.g., "incident")

    \b
    Examples:
        dxs crm metadata entities                    # List all entities
        dxs crm metadata incident                    # Fields for cases
        dxs crm metadata account                     # Fields for accounts
        dxs crm metadata incident --relationships    # Include navigation properties
        dxs crm metadata incident -r                 # Short form
    """
    if entity_name is None:
        # Show help if no argument provided
        click.echo(click.get_current_context().get_help())
        return

    if entity_name == "entities":
        # Special case: list all entities
        _list_entities(ctx)
    else:
        # Show fields for the specified entity
        _get_entity_metadata(ctx, entity_name, relationships)


# Register metadata as subcommand of crm
crm.add_command(metadata)
