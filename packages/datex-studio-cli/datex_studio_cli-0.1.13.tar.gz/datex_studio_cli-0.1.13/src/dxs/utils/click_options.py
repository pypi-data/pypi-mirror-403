"""Reusable Click option decorators for common CLI patterns."""

from collections.abc import Callable
from typing import Any, TypeVar

import click

F = TypeVar("F", bound=Callable[..., Any])


def pagination_options(default_limit: int = 10) -> Callable[[F], F]:
    """Add --limit/-n option for pagination.

    Args:
        default_limit: Default limit value (use 0 for unlimited)

    Adds parameter:
        limit: int - Maximum number of results to return

    Example:
        @pagination_options(default_limit=10)
        def list_command(ctx, limit):
            items = items[:limit] if limit > 0 else items
    """

    def decorator(f: F) -> F:
        return click.option(
            "--limit",
            "-n",
            type=int,
            default=default_limit,
            show_default=True,
            help="Maximum number of results (0 for unlimited)",
        )(f)

    return decorator


def sorting_options(
    sort_choices: list[str],
    default_sort: str = "created",
    default_direction: str = "desc",
) -> Callable[[F], F]:
    """Add --sort, --asc, --desc options for sorting.

    Args:
        sort_choices: List of valid sort field names
        default_sort: Default sort field
        default_direction: Default sort direction ("asc" or "desc")

    Adds parameters:
        sort: str - Field to sort by
        sort_direction: str - Sort direction ("asc" or "desc")

    Example:
        @sorting_options(["name", "created", "modified"], default_sort="created")
        def list_command(ctx, sort, sort_direction):
            items = sort_items(items, sort, sort_direction)
    """

    def decorator(f: F) -> F:
        # Apply options in reverse order (Click reads bottom-up)
        f = click.option(
            "--desc",
            "sort_direction",
            flag_value="desc",
            default=(default_direction == "desc") or None,
            help="Sort descending" + (" (default)" if default_direction == "desc" else ""),
        )(f)
        f = click.option(
            "--asc",
            "sort_direction",
            flag_value="asc",
            default=None,
            help="Sort ascending" + (" (default)" if default_direction == "asc" else ""),
        )(f)
        f = click.option(
            "--sort",
            type=click.Choice(sort_choices, case_sensitive=False),
            default=default_sort,
            show_default=True,
            help="Field to sort by",
        )(f)
        return f

    return decorator


def date_range_options(
    created: bool = True,
    modified: bool = True,
) -> Callable[[F], F]:
    """Add date range filter options.

    Args:
        created: Include created date filters
        modified: Include modified date filters

    Adds parameters (depending on flags):
        created_after: datetime | None
        created_before: datetime | None
        modified_after: datetime | None
        modified_before: datetime | None

    Example:
        @date_range_options()
        def list_command(ctx, created_after, created_before, modified_after, modified_before):
            items = filter_by_date_range(items, "createdDate", after=created_after, before=created_before)
    """

    def decorator(f: F) -> F:
        # Apply options in reverse order (Click reads bottom-up)
        if modified:
            f = click.option(
                "--modified-before",
                type=click.DateTime(),
                default=None,
                help="Filter by modification date (before)",
            )(f)
            f = click.option(
                "--modified-after",
                type=click.DateTime(),
                default=None,
                help="Filter by modification date (after)",
            )(f)
        if created:
            f = click.option(
                "--created-before",
                type=click.DateTime(),
                default=None,
                help="Filter by creation date (before)",
            )(f)
            f = click.option(
                "--created-after",
                type=click.DateTime(),
                default=None,
                help="Filter by creation date (after)",
            )(f)
        return f

    return decorator


def author_filter_option() -> Callable[[F], F]:
    """Add --author option for filtering by user email.

    Adds parameter:
        author: str | None - Filter by author email address

    Example:
        @author_filter_option()
        def list_command(ctx, author):
            if author:
                user_id = resolver.resolve_user_email(author)
                items = [i for i in items if i.get("userId") == user_id]
    """

    def decorator(f: F) -> F:
        return click.option(
            "--author",
            type=str,
            default=None,
            help="Filter by author email address",
        )(f)

    return decorator
