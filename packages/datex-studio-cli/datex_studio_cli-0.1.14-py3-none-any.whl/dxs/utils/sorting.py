"""Generic sorting utilities for list data."""

from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T", bound=dict[str, Any])


class SortDirection(str, Enum):
    """Sort direction enumeration."""

    ASC = "asc"
    DESC = "desc"


# Field mappings for common sort field aliases
BRANCH_SORT_FIELDS = {
    "name": "name",
    "created": "createdDate",
    "modified": "modifiedDate",
    "commit-date": "commitDate",
    "status": "applicationStatusId",
    "changes": "change_count",  # Requires --with-changes flag
}

REPO_SORT_FIELDS = {
    "name": "name",
    "created": "createdDate",
    "modified": "modifiedDate",
}

ORG_SORT_FIELDS = {
    "name": "name",
    "created": "createdDate",
}


def _parse_date_for_sort(value: Any) -> datetime | None:
    """Parse a date value for sorting purposes.

    Args:
        value: Date string (ISO format) or datetime object

    Returns:
        datetime object or None if parsing fails
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Handle ISO format with optional timezone
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def sort_items(
    items: list[T],
    field: str,
    direction: str | SortDirection = SortDirection.DESC,
    none_position: str = "last",
) -> list[T]:
    """Sort items by field with null handling.

    Args:
        items: List of dictionaries to sort
        field: Name of field to sort by
        direction: Sort direction ("asc" or "desc")
        none_position: Where to place None values ("first" or "last")

    Returns:
        Sorted list of items
    """
    if not items:
        return items

    if isinstance(direction, str):
        direction = SortDirection(direction.lower())

    reverse = direction == SortDirection.DESC

    def sort_key(item: T) -> tuple[bool, Any]:
        value = item.get(field)

        # Handle date fields
        if field.endswith("Date") or "date" in field.lower():
            value = _parse_date_for_sort(value)

        # Handle None values - place them according to none_position
        if value is None:
            # When sorting descending with none_position="last":
            # - None should sort after all real values
            # - Use (True, ...) so None items sort after (False, ...)
            if none_position == "last":
                return (not reverse, "")
            else:
                return (reverse, "")

        return (reverse if none_position == "last" else not reverse, value)

    return sorted(items, key=sort_key, reverse=reverse)


def get_mapped_sort_field(alias: str, field_mapping: dict[str, str]) -> str:
    """Get the actual field name from an alias.

    Args:
        alias: User-provided sort field name (e.g., "created")
        field_mapping: Dictionary mapping aliases to actual field names

    Returns:
        Actual field name (e.g., "createdDate")
    """
    return field_mapping.get(alias, alias)
