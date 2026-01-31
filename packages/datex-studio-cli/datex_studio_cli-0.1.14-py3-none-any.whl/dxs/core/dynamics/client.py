"""Dynamics CRM / Dataverse API client utilities."""

from typing import Any, cast

import httpx

from dxs.utils.config import get_settings
from dxs.utils.errors import ApiError, AuthenticationError, ConfigurationError


def get_dynamics_token() -> str:
    """Get an OAuth token for Dynamics CRM / Dataverse API.

    Uses the existing MSAL client to acquire a token with the
    org-specific Dynamics CRM scope derived from dynamics_crm_url.

    Priority:
        0. DXS_DYNAMICS_TOKEN environment variable (direct token from external auth)
        1. DXS_REFRESH_TOKEN environment variable (OBO flow)
        2. MSAL silent acquisition (cached token)
        3. File-based refresh token

    Returns:
        Access token for Dynamics CRM API

    Raises:
        AuthenticationError: If token acquisition fails
        ConfigurationError: If dynamics_crm_url is not configured
    """
    import os

    from dxs.core.auth.msal_client import MSALClient
    from dxs.core.auth.token_cache import MultiIdentityTokenCache

    # Priority 0: DXS_DYNAMICS_TOKEN environment variable (direct token)
    # Used when an external tool (e.g., Sidekick) provides a pre-acquired Dynamics token
    env_dynamics_token = os.environ.get("DXS_DYNAMICS_TOKEN")
    if env_dynamics_token:
        return env_dynamics_token

    settings = get_settings()
    dynamics_scopes = settings.dynamics_crm_scopes

    if not dynamics_scopes:
        raise ConfigurationError(
            message="Dynamics CRM URL is not configured",
            code="DXS-DYNAMICS-CONFIG-001",
            suggestions=[
                "Run: dxs config set dynamics_crm_url https://yourorg.crm.dynamics.com",
                "Then run: dxs auth login",
            ],
        )

    # Track the error from env token attempt for better error reporting
    env_token_error: str | None = None
    env_token_error_desc: str | None = None

    # Priority 1: DXS_REFRESH_TOKEN environment variable (OBO flow)
    env_refresh_token = os.environ.get("DXS_REFRESH_TOKEN")
    if env_refresh_token:
        try:
            msal_client = MSALClient(scopes=dynamics_scopes)
            result = msal_client._app.acquire_token_by_refresh_token(
                refresh_token=env_refresh_token,
                scopes=dynamics_scopes,
            )
            if result and "access_token" in result:
                return cast(str, result["access_token"])
            # Capture MSAL error response for reporting
            if result:
                env_token_error = result.get("error", "unknown_error")
                env_token_error_desc = result.get(
                    "error_description", "OBO token acquisition failed"
                )
            else:
                env_token_error = "no_result"
                env_token_error_desc = "No response from OBO token refresh"
        except Exception as e:
            env_token_error = "exception"
            env_token_error_desc = f"OBO token acquisition failed: {e}"

    # Priority 2: Try to get token from MSAL silent acquisition
    msal_client = MSALClient(scopes=dynamics_scopes)
    result = msal_client.acquire_token_silent()
    if result and "access_token" in result:
        return cast(str, result["access_token"])

    # Priority 3: Try using the stored refresh token from file cache
    cache = MultiIdentityTokenCache()
    identity = cache.get_active_identity()
    if identity and identity.refresh_token:
        try:
            result = msal_client._app.acquire_token_by_refresh_token(
                refresh_token=identity.refresh_token,
                scopes=dynamics_scopes,
            )
            if result and "access_token" in result:
                return cast(str, result["access_token"])

            error = result.get("error") if result else "no_result"
            error_desc = (
                result.get("error_description") if result else "No response from token refresh"
            )
        except Exception as e:
            error = "exception"
            error_desc = str(e)
    else:
        # If env token was tried but failed, report that error instead
        if env_token_error:
            error = env_token_error
            error_desc = env_token_error_desc
        else:
            error = "no_refresh_token"
            error_desc = (
                "No refresh token available (set DXS_REFRESH_TOKEN or run 'dxs auth login')"
            )

    raise AuthenticationError(
        message=f"Could not acquire Dynamics CRM token: {error_desc}",
        code="DXS-DYNAMICS-AUTH-001",
        details={"error": error, "error_description": error_desc},
        suggestions=[
            "Set DXS_REFRESH_TOKEN environment variable for OBO flow",
            "Run 'dxs auth login' to authenticate with refresh token",
            "Ensure your account has Dynamics CRM / Dataverse access",
        ],
    )


class DynamicsClient:
    """HTTP client for Dynamics CRM / Dataverse Web API.

    Handles authenticated requests to the Dynamics CRM Web API using
    the configured CRM instance URL and OAuth token.
    """

    # API version for Dataverse Web API
    API_VERSION = "v9.2"

    # Case status codes in Dynamics CRM
    STATUS_ACTIVE = 0
    STATUS_RESOLVED = 1
    STATUS_CANCELLED = 2

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the Dynamics client.

        Args:
            timeout: Request timeout in seconds.

        Raises:
            ConfigurationError: If dynamics_crm_url is not configured.
        """
        settings = get_settings()

        if not settings.dynamics_crm_url:
            raise ConfigurationError(
                message="Dynamics CRM URL is not configured",
                code="DXS-DYNAMICS-CONFIG-001",
                suggestions=[
                    "Run: dxs config set dynamics_crm_url https://yourorg.crm.dynamics.com",
                    "Then run: dxs auth login",
                ],
            )

        self._base_url = settings.dynamics_crm_url.rstrip("/")
        self._api_url = f"{self._base_url}/api/data/{self.API_VERSION}"
        self._timeout = timeout

    def _get_headers(self, page_size: int | None = None) -> dict[str, str]:
        """Get request headers with authorization token.

        Args:
            page_size: Optional page size for OData pagination. When specified,
                adds odata.maxpagesize to the Prefer header to enable pagination
                with @odata.nextLink.
        """
        token = get_dynamics_token()
        prefer_parts = ["odata.include-annotations=*"]
        if page_size:
            prefer_parts.append(f"odata.maxpagesize={page_size}")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": ",".join(prefer_parts),
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising appropriate errors.

        Args:
            response: The HTTP response.

        Returns:
            Parsed JSON response data.

        Raises:
            AuthenticationError: For 401/403 responses.
            ApiError: For other error responses.
        """
        if response.status_code == 401:
            raise AuthenticationError(
                message="Dynamics CRM authentication token is invalid or expired",
                code="DXS-DYNAMICS-AUTH-002",
                suggestions=[
                    "Run 'dxs auth login' to refresh credentials",
                    "Ensure dynamics_crm_url is correct",
                ],
            )

        if response.status_code == 403:
            raise AuthenticationError(
                message="You don't have permission to access this Dynamics CRM resource",
                code="DXS-DYNAMICS-AUTH-003",
                suggestions=[
                    "Check that you have the required Dynamics CRM permissions",
                    "Contact your administrator if you believe this is an error",
                ],
            )

        if response.status_code == 404:
            raise ApiError(
                message="Dynamics CRM resource not found",
                code="DXS-DYNAMICS-404",
                details={"url": str(response.url), "status_code": 404},
            )

        if response.status_code >= 400:
            # Try to parse error message from response
            try:
                error_body = response.json()
                error_info = error_body.get("error", {})
                message = error_info.get(
                    "message", f"Dynamics CRM API error: {response.status_code}"
                )
            except Exception:
                message = f"Dynamics CRM API error: {response.status_code}"

            raise ApiError(
                message=message,
                code=f"DXS-DYNAMICS-{response.status_code}",
                details={
                    "url": str(response.url),
                    "status_code": response.status_code,
                },
            )

        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return {}

        return cast(dict[str, Any], response.json())

    def get(
        self, path: str, params: dict[str, Any] | None = None, page_size: int | None = None
    ) -> dict[str, Any]:
        """Make a GET request to the Dynamics CRM API.

        Args:
            path: API endpoint path (e.g., "/incidents").
            params: Optional query parameters.
            page_size: Optional page size for OData pagination. When specified,
                adds odata.maxpagesize to the Prefer header to enable pagination
                with @odata.nextLink.

        Returns:
            Parsed JSON response.
        """
        url = f"{self._api_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(
                    url,
                    headers=self._get_headers(page_size=page_size),
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to Dynamics CRM at {self._base_url}",
                code="DXS-DYNAMICS-CONN",
                details={"url": url, "error": str(e)},
                suggestions=[
                    f"Verify dynamics_crm_url is correct: {self._base_url}",
                    "Check your network connection",
                ],
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Dynamics CRM request timed out after {self._timeout} seconds",
                code="DXS-DYNAMICS-TIMEOUT",
                details={"url": url, "timeout": self._timeout},
            ) from e

    def get_by_next_link(self, url: str) -> dict[str, Any]:
        """Fetch results from a nextLink URL (for cursor-based pagination).

        Dataverse doesn't support $skip, so pagination uses @odata.nextLink URLs.
        This method fetches the next page of results using the provided URL.

        Args:
            url: The @odata.nextLink URL from a previous response.

        Returns:
            Dictionary with 'value' containing list of records.
        """
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=self._get_headers())
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message="Cannot connect to Dynamics CRM",
                code="DXS-DYNAMICS-CONN",
                details={"url": url, "error": str(e)},
                suggestions=[
                    "Check your network connection",
                ],
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Dynamics CRM request timed out after {self._timeout} seconds",
                code="DXS-DYNAMICS-TIMEOUT",
                details={"url": url, "timeout": self._timeout},
            ) from e

    def search_incidents(
        self,
        query: str | None = None,
        status: str | None = None,
        account: str | None = None,
        since: str | None = None,
        limit: int = 500,
        include_notes: bool = False,
    ) -> dict[str, Any]:
        """Search for support cases (incidents) in Dynamics CRM.

        Args:
            query: Search text to match against case number, title, description.
            status: Filter by status ('active', 'resolved', 'cancelled', or None for all).
            account: Filter by account name (partial match).
            since: Filter to cases created on or after this date (ISO format: YYYY-MM-DD).
            limit: Maximum number of results to return per page.
            include_notes: Whether to include notes/annotations for each incident.

        Returns:
            Dictionary with 'value' containing list of incidents,
            '@odata.count' containing total matching records,
            and optionally '@odata.nextLink' for pagination.
        """
        # Build OData query parameters
        params: dict[str, str] = {}

        # Request total count for pagination
        params["$count"] = "true"

        # Select specific fields
        # Note: lookup names come back via OData annotations when
        # odata.include-annotations=* is set in Prefer header
        params["$select"] = (
            "incidentid,ticketnumber,title,description,"
            "statecode,statuscode,createdon,modifiedon,"
            "_customerid_value,_ownerid_value,"
            "prioritycode,severitycode,daa_immediatebusinessimpact,"
            "isescalated,escalatedon,resolveby,responseby,"
            "adx_resolution,adx_resolutiondate"
        )

        # Expand relationships to get names
        expand_parts = [
            "customerid_account($select=name)",
            "customerid_contact($select=fullname)",
        ]

        # Include annotations if requested
        if include_notes:
            expand_parts.append(
                "Incident_Annotation($select=annotationid,subject,notetext,createdon,_createdby_value,filename,mimetype,filesize;$orderby=createdon desc)"
            )

        params["$expand"] = ",".join(expand_parts)

        # Build filter conditions
        filters: list[str] = []

        # Status filter
        if status:
            status_lower = status.lower()
            if status_lower == "active":
                filters.append(f"statecode eq {self.STATUS_ACTIVE}")
            elif status_lower == "resolved":
                filters.append(f"statecode eq {self.STATUS_RESOLVED}")
            elif status_lower == "cancelled":
                filters.append(f"statecode eq {self.STATUS_CANCELLED}")

        # Account name filter (partial match on related account name)
        if account:
            safe_account = account.replace("'", "''")
            filters.append(f"contains(customerid_account/name,'{safe_account}')")

        # Date filter (cases created on or after the given date)
        if since:
            # OData datetime comparison - createdon is a DateTimeOffset
            filters.append(f"createdon ge {since}")

        # Text search filter
        if query:
            # Escape single quotes in query
            safe_query = query.replace("'", "''")
            search_filter = (
                f"(contains(ticketnumber,'{safe_query}') or "
                f"contains(title,'{safe_query}') or "
                f"contains(description,'{safe_query}'))"
            )
            filters.append(search_filter)

        if filters:
            params["$filter"] = " and ".join(filters)

        # Order by modified date descending
        params["$orderby"] = "modifiedon desc"

        # Use page_size header for pagination (Dataverse returns @odata.nextLink when
        # using odata.maxpagesize in Prefer header, but NOT when using $top)
        return self.get("/incidents", params=params, page_size=limit)

    def list_accounts(self, limit: int = 500) -> dict[str, Any]:
        """List accounts in Dynamics CRM.

        Args:
            limit: Maximum number of results to return per page.

        Returns:
            Dictionary with 'value' containing list of accounts,
            '@odata.count' containing total matching records,
            and optionally '@odata.nextLink' for pagination.
        """
        params: dict[str, str] = {}

        # Request total count for pagination
        params["$count"] = "true"

        # Select specific fields
        params["$select"] = (
            "accountid,name,accountnumber,telephone1,emailaddress1,"
            "address1_city,address1_stateorprovince,statecode,createdon,modifiedon"
        )

        # Only active accounts by default
        params["$filter"] = "statecode eq 0"

        # Order by name
        params["$orderby"] = "name asc"

        # Use page_size header for pagination
        return self.get("/accounts", params=params, page_size=limit)

    def search_accounts(self, query: str, limit: int = 500) -> dict[str, Any]:
        """Search for accounts in Dynamics CRM.

        Args:
            query: Search text to match against account name.
            limit: Maximum number of results to return per page.

        Returns:
            Dictionary with 'value' containing list of accounts,
            '@odata.count' containing total matching records,
            and optionally '@odata.nextLink' for pagination.
        """
        params: dict[str, str] = {}

        # Request total count for pagination
        params["$count"] = "true"

        # Select specific fields
        params["$select"] = (
            "accountid,name,accountnumber,telephone1,emailaddress1,"
            "address1_city,address1_stateorprovince,statecode,createdon,modifiedon"
        )

        # Build filter: active accounts matching query
        safe_query = query.replace("'", "''")
        params["$filter"] = f"statecode eq 0 and contains(name,'{safe_query}')"

        # Order by name
        params["$orderby"] = "name asc"

        # Use page_size header for pagination
        return self.get("/accounts", params=params, page_size=limit)

    def get_entity_fields(self, entity_name: str) -> dict[str, Any]:
        """Get field definitions for an entity.

        Uses the Dataverse metadata API to retrieve attribute definitions.

        Note: The Attributes metadata endpoint has limited OData support.
        We fetch all attributes and filter client-side.

        Args:
            entity_name: Logical name of the entity (e.g., "incident", "account").

        Returns:
            Dictionary with 'value' containing list of attribute definitions.
        """
        # Metadata endpoints don't support $select, $filter, or $orderby
        # We get all fields and filter client-side
        return self.get(
            f"/EntityDefinitions(LogicalName='{entity_name}')/Attributes",
        )

    def query_incidents(
        self,
        select: str | None = None,
        filter: str | None = None,
        orderby: str | None = None,
        expand: str | None = None,
        top: int = 500,
    ) -> dict[str, Any]:
        """Execute a custom OData query against incidents (cases).

        Allows full control over OData query parameters for AI-constructed queries.

        Args:
            select: OData $select - comma-separated field names to return.
            filter: OData $filter - filter expression.
            orderby: OData $orderby - sort expression (e.g., "modifiedon desc").
            expand: OData $expand - related entities to include.
            top: OData $top - maximum results to return per page.

        Returns:
            Dictionary with 'value' containing list of incidents,
            '@odata.count' containing total matching records,
            and optionally '@odata.nextLink' for pagination.
        """
        params: dict[str, str] = {}

        # Request total count for pagination
        params["$count"] = "true"

        if select:
            params["$select"] = select

        if filter:
            params["$filter"] = filter

        if orderby:
            params["$orderby"] = orderby

        if expand:
            params["$expand"] = expand

        # Use page_size header for pagination
        return self.get("/incidents", params=params, page_size=top)

    def list_entities(self) -> dict[str, Any]:
        """List all entity definitions in Dynamics CRM.

        Note: The EntityDefinitions metadata endpoint has limited OData support.
        $select and $orderby are not supported, so we fetch all and filter client-side.

        Returns:
            Dictionary with 'value' containing list of entity definitions.
        """
        # EntityDefinitions doesn't support $select or $orderby
        # We get all fields and filter client-side
        return self.get("/EntityDefinitions")

    def get_entity_relationships(self, entity_name: str) -> dict[str, Any]:
        """Get relationship definitions for an entity.

        Retrieves ManyToOne (lookups) and OneToMany relationships.

        Args:
            entity_name: Logical name of the entity (e.g., "incident", "account").

        Returns:
            Dictionary with 'many_to_one' and 'one_to_many' relationship lists.
        """
        # Get ManyToOne relationships (lookups - this entity references another)
        # Metadata endpoints don't support $select, we get all fields
        many_to_one = self.get(
            f"/EntityDefinitions(LogicalName='{entity_name}')/ManyToOneRelationships",
        )

        # Get OneToMany relationships (this entity is referenced by others)
        one_to_many = self.get(
            f"/EntityDefinitions(LogicalName='{entity_name}')/OneToManyRelationships",
        )

        return {
            "many_to_one": many_to_one.get("value", []),
            "one_to_many": one_to_many.get("value", []),
        }

    def download_blob(self, blob_path: str) -> bytes:
        """Download a binary blob from the Dynamics CRM API.

        Used to download rich text file attachments embedded in descriptions.

        Args:
            blob_path: The API path to the blob. Can be either:
                - Full path: "/api/data/v9.1/msdyn_richtextfiles(uuid)/..."
                - Relative path: "/msdyn_richtextfiles(uuid)/..."

        Returns:
            Raw bytes of the blob content.

        Raises:
            ApiError: If the download fails.
        """
        # If path includes /api/data/, use base URL directly to preserve version
        if blob_path.startswith("/api/data/"):
            url = f"{self._base_url}{blob_path}"
        else:
            url = f"{self._api_url}{blob_path}"
        headers = self._get_headers()
        # For binary downloads, we want the raw content
        headers["Accept"] = "*/*"

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers)

                if response.status_code == 401:
                    raise AuthenticationError(
                        message="Dynamics CRM authentication token is invalid or expired",
                        code="DXS-DYNAMICS-AUTH-002",
                        suggestions=["Run 'dxs auth login' to refresh credentials"],
                    )

                if response.status_code == 404:
                    raise ApiError(
                        message=f"Attachment not found: {blob_path}",
                        code="DXS-DYNAMICS-404",
                        details={"url": url, "status_code": 404},
                    )

                if response.status_code >= 400:
                    raise ApiError(
                        message=f"Failed to download attachment: {response.status_code}",
                        code=f"DXS-DYNAMICS-{response.status_code}",
                        details={"url": url, "status_code": response.status_code},
                    )

                return response.content

        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to Dynamics CRM at {self._base_url}",
                code="DXS-DYNAMICS-CONN",
                details={"url": url, "error": str(e)},
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Dynamics CRM request timed out after {self._timeout} seconds",
                code="DXS-DYNAMICS-TIMEOUT",
                details={"url": url, "timeout": self._timeout},
            ) from e
