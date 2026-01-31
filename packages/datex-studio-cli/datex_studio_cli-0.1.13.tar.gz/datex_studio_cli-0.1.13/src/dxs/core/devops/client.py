"""Azure DevOps REST API client."""

import json
from typing import Any, cast

import httpx

from dxs.core.devops.models import DevOpsWorkItemDto
from dxs.utils.config import get_settings
from dxs.utils.errors import ApiError, AuthenticationError

# Azure DevOps API resource ID for OAuth
DEVOPS_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"


def get_devops_token() -> str:
    """Get an OAuth token for Azure DevOps API.

    Uses the existing MSAL client to acquire a token with the
    Azure DevOps user_impersonation scope.

    Priority:
        0. DXS_DEVOPS_TOKEN environment variable (direct token from external auth)
        1. DXS_REFRESH_TOKEN environment variable (OBO flow)
        2. MSAL silent acquisition (cached token)
        3. File-based refresh token

    Returns:
        Access token for Azure DevOps API

    Raises:
        AuthenticationError: If token acquisition fails
    """
    import os

    from dxs.core.auth.msal_client import MSALClient
    from dxs.core.auth.token_cache import MultiIdentityTokenCache

    # Priority 0: DXS_DEVOPS_TOKEN environment variable (direct token)
    # Used when an external tool (e.g., Sidekick) provides a pre-acquired DevOps token
    env_devops_token = os.environ.get("DXS_DEVOPS_TOKEN")
    if env_devops_token:
        return env_devops_token

    settings = get_settings()
    devops_scopes = settings.azure_devops_scopes

    if not devops_scopes:
        devops_scopes = [f"{DEVOPS_RESOURCE_ID}/user_impersonation"]

    # Track the error from env token attempt for better error reporting
    env_token_error: str | None = None
    env_token_error_desc: str | None = None

    # Priority 1: DXS_REFRESH_TOKEN environment variable (OBO flow)
    env_refresh_token = os.environ.get("DXS_REFRESH_TOKEN")
    if env_refresh_token:
        try:
            msal_client = MSALClient(scopes=devops_scopes)
            result = msal_client._app.acquire_token_by_refresh_token(
                refresh_token=env_refresh_token,
                scopes=devops_scopes,
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
    msal_client = MSALClient(scopes=devops_scopes)
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
                scopes=devops_scopes,
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
        message=f"Could not acquire Azure DevOps token: {error_desc}",
        code="DXS-DEVOPS-AUTH-001",
        details={"error": error, "error_description": error_desc},
        suggestions=[
            "Set DXS_REFRESH_TOKEN environment variable for OBO flow",
            "Run 'dxs auth login' to authenticate with refresh token",
            "Ensure your account has Azure DevOps access",
        ],
    )


class AzureDevOpsClient:
    """Client for Azure DevOps REST API.

    Provides methods to fetch work items from Azure DevOps using
    OAuth authentication.
    """

    API_VERSION = "7.0"

    def __init__(self, organization: str):
        """Initialize the Azure DevOps client.

        Args:
            organization: Azure DevOps organization name
        """
        self.organization = organization
        self.base_url = f"https://dev.azure.com/{organization}"
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            token = get_devops_token()
            self._client = httpx.Client(
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to Azure DevOps API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            params: Query parameters
            json_data: JSON body for POST requests

        Returns:
            Response JSON as dict

        Raises:
            ApiError: If the request fails
        """
        client = self._get_client()

        # Always include API version
        if params is None:
            params = {}
        params["api-version"] = self.API_VERSION

        try:
            if method.upper() == "GET":
                response = client.get(url, params=params)
            elif method.upper() == "POST":
                response = client.post(url, params=params, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code == 401:
                raise AuthenticationError(
                    message="Azure DevOps authentication failed",
                    code="DXS-DEVOPS-AUTH-002",
                    suggestions=[
                        "Re-authenticate with 'dxs auth login'",
                        "Verify you have access to the Azure DevOps organization",
                    ],
                )

            if response.status_code == 404:
                raise ApiError(
                    message="Resource not found in Azure DevOps",
                    code="DXS-DEVOPS-404",
                    details={"url": url, "status_code": 404},
                )

            if response.status_code >= 400:
                raise ApiError(
                    message=f"Azure DevOps API error: {response.status_code}",
                    code="DXS-DEVOPS-API-001",
                    details={
                        "status_code": response.status_code,
                        "response": response.text[:500] if response.text else None,
                    },
                )

            # Parse JSON response with defensive error handling
            try:
                return cast(dict[str, Any], response.json())
            except (json.JSONDecodeError, ValueError) as e:
                # DevOps API returned non-JSON content
                content_type = response.headers.get("content-type", "")
                response_preview = response.text[:500] if response.text else "(empty)"

                raise ApiError(
                    message=f"Azure DevOps API returned non-JSON response (status {response.status_code})",
                    code="DXS-DEVOPS-JSON-001",
                    status_code=response.status_code,
                    details={
                        "url": str(response.url),
                        "content_type": content_type,
                        "response_preview": response_preview,
                        "parse_error": str(e),
                    },
                    suggestions=[
                        "This may indicate an Azure DevOps API error",
                        "Verify your Azure DevOps organization URL is correct",
                        "Check your Personal Access Token (PAT) permissions",
                        "Contact support if this persists with error code DXS-DEVOPS-JSON-001",
                    ],
                ) from e

        except httpx.TimeoutException as e:
            raise ApiError(
                message="Azure DevOps API request timed out",
                code="DXS-DEVOPS-TIMEOUT",
                suggestions=["Check your network connection", "Try again later"],
            ) from e
        except httpx.RequestError as e:
            raise ApiError(
                message=f"Azure DevOps API request failed: {e}",
                code="DXS-DEVOPS-REQUEST",
                details={"error": str(e)},
            ) from e

    def get_workitem(
        self,
        workitem_id: int,
        fields: list[str] | None = None,
        expand: str | None = None,
    ) -> DevOpsWorkItemDto:
        """Fetch a single work item by ID.

        Args:
            workitem_id: Work item ID
            fields: List of field names to return (None for all)
            expand: Expand options (None, Links, Relations, All)

        Returns:
            Work item data

        Raises:
            ApiError: If the request fails
        """
        url = f"{self.base_url}/_apis/wit/workitems/{workitem_id}"

        params: dict[str, Any] = {}
        if fields:
            params["$fields"] = ",".join(fields)
        if expand:
            params["$expand"] = expand

        data = self._make_request("GET", url, params=params)
        return DevOpsWorkItemDto(**data)

    def get_workitems_batch(
        self,
        ids: list[int],
        fields: list[str] | None = None,
    ) -> list[DevOpsWorkItemDto]:
        """Fetch multiple work items by IDs (batch request).

        Args:
            ids: List of work item IDs (max 200)
            fields: List of field names to return (None for default set)

        Returns:
            List of work item data

        Raises:
            ApiError: If the request fails
            ValueError: If more than 200 IDs provided
        """
        if len(ids) > 200:
            raise ValueError("Maximum of 200 work items can be fetched in a single batch")

        if not ids:
            return []

        url = f"{self.base_url}/_apis/wit/workitemsbatch"

        # Default fields to fetch if not specified
        if fields is None:
            fields = [
                "System.Id",
                "System.Title",
                "System.WorkItemType",
                "System.State",
                "System.Description",
                "System.AssignedTo",
                "System.CreatedDate",
                "System.ChangedDate",
                "System.Tags",
                "System.AreaPath",
                "System.IterationPath",
            ]

        body = {
            "ids": ids,
            "fields": fields,
        }

        data = self._make_request("POST", url, json_data=body)

        # Response format: {"count": N, "value": [...]}
        items = data.get("value", [])
        return [DevOpsWorkItemDto(**item) for item in items]

    def get_workitem_discussions(
        self,
        workitem_id: int,
    ) -> list[dict[str, Any]]:
        """Fetch discussions for a work item.

        Uses the work item updates API to extract discussion entries
        from the System.History field, which is where Azure DevOps
        stores discussions.

        Args:
            workitem_id: Work item ID

        Returns:
            List of discussion objects with text, createdBy, createdDate

        Raises:
            ApiError: If the request fails
        """
        # Use updates API to get discussion history (System.History field)
        url = f"{self.base_url}/_apis/wit/workitems/{workitem_id}/updates"

        try:
            data = self._make_request("GET", url)
            updates = data.get("value", [])

            # Extract discussion entries from System.History changes
            discussions = []
            for update in updates:
                fields = update.get("fields", {})
                history = fields.get("System.History", {})
                text = history.get("newValue", "")

                if text:
                    discussions.append(
                        {
                            "text": text,
                            "createdBy": update.get("revisedBy", {}),
                            "createdDate": update.get("revisedDate", ""),
                        }
                    )

            return discussions
        except Exception:
            # If fetching fails, return empty list for graceful degradation
            return []

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "AzureDevOpsClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
