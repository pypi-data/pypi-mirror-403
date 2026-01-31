"""User commands: dxs user [list|studio-access]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.core.api import ApiClient, UserEndpoints
from dxs.core.auth import require_auth
from dxs.utils.errors import ValidationError
from dxs.utils.responses import list_response, single


@click.group()
def user() -> None:
    """User commands.

    Manage user settings and permissions in Datex Studio.

    \b
    Examples:
        dxs user list                                  # List all users
        dxs user list --search "john"                  # Search users by name/email
        dxs user studio-access --user-id 123 --grant   # Grant studio access
        dxs user studio-access --user-id 123 --revoke  # Revoke studio access
    """
    pass


@user.command("list")
@click.option(
    "--search",
    "-s",
    type=str,
    default=None,
    help="Search users by name or email (case-insensitive)",
)
@pass_context
@require_auth
def list_users(ctx: DxsContext, search: str | None) -> None:
    """List all users.

    Returns a list of all users in the system. Use --search to filter
    by display name or email address.

    \b
    Options:
        --search, -s   Filter by name or email (case-insensitive)

    \b
    Examples:
        dxs user list
        dxs user list --search "john"
        dxs user list -s "@example.com"
    """
    client = ApiClient()
    ctx.log("Fetching users...")

    users = client.get(UserEndpoints.list())

    # Normalize to list
    if not isinstance(users, list):
        users = [users] if users else []

    total_count = len(users)

    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        users = [
            u
            for u in users
            if search_lower in u.get("displayName", "").lower()
            or search_lower in u.get("email", "").lower()
        ]

    ctx.output(
        list_response(
            items=users,
            semantic_key="users",
            total_count=total_count,
            filtered_count=len(users),
            search=search,
        )
    )


@user.command("studio-access")
@click.option(
    "--user-id",
    type=int,
    required=True,
    help="User ID to update",
)
@click.option(
    "--grant",
    "action",
    flag_value="grant",
    help="Grant studio access to the user",
)
@click.option(
    "--revoke",
    "action",
    flag_value="revoke",
    help="Revoke studio access from the user",
)
@pass_context
@require_auth
def studio_access(ctx: DxsContext, user_id: int, action: str | None) -> None:
    """Update user studio access.

    Grants or revokes studio access for a user. Requires admin permissions.

    \b
    Options:
        --user-id   User ID to update (required)
        --grant     Grant studio access
        --revoke    Revoke studio access

    \b
    Examples:
        dxs user studio-access --user-id 123 --grant
        dxs user studio-access --user-id 123 --revoke
    """
    if not action:
        raise ValidationError(
            message="Must specify either --grant or --revoke",
            suggestions=[
                "Grant access: dxs user studio-access --user-id 123 --grant",
                "Revoke access: dxs user studio-access --user-id 123 --revoke",
            ],
        )

    client = ApiClient()
    has_access = action == "grant"

    ctx.log(f"{'Granting' if has_access else 'Revoking'} studio access for user {user_id}...")

    result = client.put(
        UserEndpoints.studio_access(user_id),
        data={"hasStudioAccess": has_access},
    )

    ctx.output(
        single(
            item={
                "user_id": user_id,
                "action": action,
                "has_studio_access": has_access,
                "result": result,
            },
            semantic_key="studio_access",
        )
    )
