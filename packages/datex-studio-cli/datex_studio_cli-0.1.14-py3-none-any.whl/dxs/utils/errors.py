"""Custom exception classes for the Datex Studio CLI.

Error Code Registry:
    DXS-AUTH-001: Authentication failed (MSAL-level failure)
    DXS-AUTH-002: Not authenticated (need to login)
    DXS-AUTH-003: Token expired
    DXS-AUTH-004: Token refresh failed
    DXS-AUTH-005: Consent required
    DXS-AUTH-006: Invalid credentials configuration

    DXS-API-001: API request failed
    DXS-API-4xx: HTTP 4xx client errors (e.g., DXS-API-404)
    DXS-API-5xx: HTTP 5xx server errors

    DXS-VAL-001: Generic validation error
    DXS-VAL-002: Missing required parameter (branch/repo ID)
    DXS-VAL-003: Invalid configuration reference
    DXS-VAL-004: Resource not found

    DXS-FILE-001: File already exists (use --force)
    DXS-FILE-002: File write failed

    DXS-DOC-001: Documentation generation failed
    DXS-DOC-002: Graph analysis failed
    DXS-DOC-003: Template rendering failed

    DXS-CRM-001: Dynamics CRM API error
    DXS-DEVOPS-xxx: Azure DevOps API errors
    DXS-DYNAMICS-xxx: Dynamics CRM API errors
    DXS-CONFIG-001: Configuration error
"""

from typing import Any


class DxsError(Exception):
    """Base exception for all Datex Studio CLI errors.

    Attributes:
        code: Machine-readable error code (e.g., "DXS-AUTH-001").
        message: Human-readable error message.
        details: Additional context about the error.
        suggestions: List of actionable suggestions to resolve the error.
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        self.suggestions = suggestions or []
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for output formatting."""
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.suggestions:
            result["suggestions"] = self.suggestions
        return result


class AuthenticationError(DxsError):
    """Raised when authentication fails or token is invalid/expired."""

    def __init__(
        self,
        message: str,
        code: str = "DXS-AUTH-001",
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        if suggestions is None:
            suggestions = ["Run 'dxs auth login' to authenticate"]
        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class ConfigurationError(DxsError):
    """Raised when configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        code: str = "DXS-CONFIG-001",
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        if suggestions is None:
            suggestions = ["Run 'dxs config list' to view current configuration"]
        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class ApiError(DxsError):
    """Raised when API request fails."""

    def __init__(
        self,
        message: str,
        code: str = "DXS-API-001",
        status_code: int | None = None,
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        self.status_code = status_code
        if details is None and status_code is not None:
            details = {"status_code": status_code}
        elif status_code is not None:
            if isinstance(details, dict):
                details["status_code"] = status_code
        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class ValidationError(DxsError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        code: str = "DXS-VAL-001",
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class NotFoundError(DxsError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | int,
        code: str = "DXS-404-001",
        details: Any = None,
        suggestions: list[str] | None = None,
    ) -> None:
        message = f"{resource_type} '{resource_id}' not found"
        if details is None:
            details = {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class OrganizationMismatchError(DxsError):
    """Raised when an operation is attempted on a resource from a different organization."""

    def __init__(
        self,
        resource_org_id: int,
        resource_org_name: str | None,
        current_org_id: int | None,
        current_org_name: str | None,
        current_username: str | None = None,
        code: str = "DXS-ORG-MISMATCH",
        suggestions: list[str] | None = None,
    ) -> None:
        resource_display = resource_org_name or f"organization {resource_org_id}"
        current_display = current_org_name or (
            f"organization {current_org_id}" if current_org_id else "unknown organization"
        )

        message = (
            f"Operation not permitted: Resource belongs to '{resource_display}' "
            f"but you are authenticated as '{current_display}'"
        )

        details = {
            "resource_organization_id": resource_org_id,
            "resource_organization_name": resource_org_name,
            "current_organization_id": current_org_id,
            "current_organization_name": current_org_name,
        }

        if suggestions is None:
            suggestions = []
            if current_username:
                # Find a cached identity for the target org (caller should populate this)
                suggestions.append(
                    f"Run 'dxs auth switch <username>' to switch to an identity in '{resource_display}'"
                )
            suggestions.extend(
                [
                    "Run 'dxs auth list' to see available identities",
                    "Run 'dxs auth login' to authenticate with a different account",
                ]
            )

        super().__init__(code=code, message=message, details=details, suggestions=suggestions)


class RestrictedModeError(DxsError):
    """Raised when a command is blocked due to restricted mode being enabled."""

    def __init__(
        self,
        command_name: str,
        reason: str = "writes files or performs destructive operations",
        code: str = "DXS-RESTRICTED-001",
        suggestions: list[str] | None = None,
    ) -> None:
        message = f"Command '{command_name}' is disabled in restricted mode ({reason})"

        if suggestions is None:
            suggestions = [
                "Set DXS_RESTRICTED_MODE=false to enable this command",
                "Contact your administrator if you need access to this functionality",
            ]

        super().__init__(code=code, message=message, suggestions=suggestions)
