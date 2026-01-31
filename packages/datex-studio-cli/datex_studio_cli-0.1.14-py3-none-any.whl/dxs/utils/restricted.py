"""Restricted mode utilities for the Datex Studio CLI.

When DXS_RESTRICTED_MODE=true, certain commands that write files or perform
destructive operations are blocked.
"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from dxs.utils.config import is_restricted_mode
from dxs.utils.errors import RestrictedModeError

F = TypeVar("F", bound=Callable[..., Any])


def restrict_in_restricted_mode(
    reason: str = "writes files or performs destructive operations",
) -> Callable[[F], F]:
    """Decorator that blocks command execution when restricted mode is enabled.

    Args:
        reason: Description of why this command is restricted.

    Usage:
        @source.command()
        @pass_context
        @require_auth
        @restrict_in_restricted_mode("writes files to the filesystem")
        def my_command(ctx: DxsContext) -> None:
            ...

    Note: Place this decorator AFTER @pass_context and @require_auth to ensure
    the command name is properly captured from the Click context.
    """

    def decorator(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if is_restricted_mode():
                # Get command name from function name, converting underscores to hyphens
                command_name = f.__name__.replace("_", "-")
                raise RestrictedModeError(command_name=command_name, reason=reason)
            return f(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def check_restricted_mode_for_option(
    option_name: str,
    reason: str = "writes files to the filesystem",
) -> None:
    """Check if restricted mode is enabled and raise error for a specific option.

    Use this for runtime checks on options like --save or --save-attachments.

    Args:
        option_name: Name of the option being checked (e.g., "--save").
        reason: Description of why this option is restricted.

    Raises:
        RestrictedModeError: If restricted mode is enabled.
    """
    if is_restricted_mode():
        raise RestrictedModeError(
            command_name=f"option {option_name}",
            reason=reason,
        )
