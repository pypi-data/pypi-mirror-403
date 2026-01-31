"""HTTP client for Datex Studio API with automatic authentication."""

import json
from typing import Any

import httpx

from dxs.core.auth import get_access_token
from dxs.utils.config import get_settings
from dxs.utils.errors import ApiError, AuthenticationError, ConfigurationError


class ApiClient:
    """HTTP client with automatic token injection and error handling.

    Handles:
    - Automatic Bearer token injection
    - Response normalization
    - Error handling with DxsError types
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: API base URL. Defaults to config value.
            timeout: Request timeout in seconds. Defaults to config value.
        """
        settings = get_settings()
        self._base_url = (base_url or settings.api_base_url).rstrip("/")
        self._timeout = timeout or settings.api_timeout

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization token."""
        token = get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
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
                message="Authentication token is invalid or expired",
                code="DXS-AUTH-001",
                suggestions=["Run 'dxs auth login' to refresh credentials"],
            )

        if response.status_code == 403:
            raise AuthenticationError(
                message="You don't have permission to access this resource",
                code="DXS-AUTH-003",
                suggestions=[
                    "Check that you have the required permissions",
                    "Contact your administrator if you believe this is an error",
                ],
            )

        if response.status_code == 404:
            raise ApiError(
                message="Resource not found",
                code="DXS-404-001",
                details={"url": str(response.url), "status_code": 404},
            )

        if response.status_code >= 400:
            # Try to parse error message from response
            try:
                error_body = response.json()
                message = error_body.get("message", f"API error: {response.status_code}")
            except Exception:
                message = f"API error: {response.status_code}"

            raise ApiError(
                message=message,
                code=f"DXS-API-{response.status_code}",
                details={
                    "url": str(response.url),
                    "status_code": response.status_code,
                },
            )

        # Handle empty responses (204 No Content)
        if response.status_code == 204 or not response.content:
            return None

        # Parse JSON response with defensive error handling
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # API returned non-JSON content with success status
            content_type = response.headers.get("content-type", "")
            response_preview = response.text[:500] if response.text else "(empty)"

            raise ApiError(
                message=f"API returned non-JSON response (status {response.status_code})",
                code="DXS-API-JSON-001",
                status_code=response.status_code,
                details={
                    "url": str(response.url),
                    "content_type": content_type,
                    "response_preview": response_preview,
                    "parse_error": str(e),
                },
                suggestions=[
                    "This may indicate an API server error or misconfiguration",
                    "Verify the API endpoint URL is correct",
                    "Check that the API server is functioning properly",
                    "Contact support if this persists with error code DXS-API-JSON-001",
                ],
            ) from e

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request.

        Args:
            path: API endpoint path (e.g., "/sourcecontrol/10/locks").
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            AuthenticationError: If not authenticated or token invalid.
            ApiError: For API errors.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to API at {self._base_url}",
                code="DXS-API-CONN",
                details={"url": url, "error": str(e)},
                suggestions=[
                    "Check that the Datex Studio API server is running",
                    f"Verify api_base_url is correct: {self._base_url}",
                    "Run 'dxs config set api_base_url <url>' to update",
                ],
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Request timed out after {self._timeout} seconds",
                code="DXS-API-TIMEOUT",
                details={"url": url, "timeout": self._timeout, "error": str(e)},
                suggestions=[
                    "The API server may be slow or unresponsive",
                    "Try increasing timeout: dxs config set api_timeout 60",
                ],
            ) from e

    def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a POST request.

        Args:
            path: API endpoint path.
            data: Request body data.
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            AuthenticationError: If not authenticated or token invalid.
            ApiError: For API errors.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to API at {self._base_url}",
                code="DXS-API-CONN",
                details={"url": url, "error": str(e)},
                suggestions=[
                    "Check that the Datex Studio API server is running",
                    f"Verify api_base_url is correct: {self._base_url}",
                ],
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Request timed out after {self._timeout} seconds",
                code="DXS-API-TIMEOUT",
                details={"url": url, "timeout": self._timeout, "error": str(e)},
            ) from e

    def put(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a PUT request.

        Args:
            path: API endpoint path.
            data: Request body data.
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            AuthenticationError: If not authenticated or token invalid.
            ApiError: For API errors.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.put(
                    url,
                    headers=self._get_headers(),
                    json=data,
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to API at {self._base_url}",
                code="DXS-API-CONN",
                details={"url": url, "error": str(e)},
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Request timed out after {self._timeout} seconds",
                code="DXS-API-TIMEOUT",
                details={"url": url, "timeout": self._timeout, "error": str(e)},
            ) from e

    def delete(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a DELETE request.

        Args:
            path: API endpoint path.
            params: Optional query parameters.

        Returns:
            Parsed JSON response (usually None for DELETE).

        Raises:
            AuthenticationError: If not authenticated or token invalid.
            ApiError: For API errors.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.delete(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConfigurationError(
                message=f"Cannot connect to API at {self._base_url}",
                code="DXS-API-CONN",
                details={"url": url, "error": str(e)},
            ) from e
        except httpx.TimeoutException as e:
            raise ApiError(
                message=f"Request timed out after {self._timeout} seconds",
                code="DXS-API-TIMEOUT",
                details={"url": url, "timeout": self._timeout, "error": str(e)},
            ) from e
