"""Generic filtering utilities for list data."""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

T = TypeVar("T", bound=dict[str, Any])


def _make_aware(dt: datetime) -> datetime:
    """Make a naive datetime timezone-aware (assume UTC).

    Args:
        dt: A datetime object that may or may not have timezone info

    Returns:
        Timezone-aware datetime (UTC if was naive)
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_date_field(value: Any) -> datetime | None:
    """Parse a date field value to datetime.

    Handles ISO format strings and existing datetime objects.

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
            # Handle ISO format with optional timezone (Z suffix or +00:00)
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def filter_by_date_range(
    items: list[T],
    field: str,
    after: datetime | None = None,
    before: datetime | None = None,
) -> list[T]:
    """Filter items by date field within range.

    Args:
        items: List of dictionaries to filter
        field: Name of the date field (e.g., "createdDate")
        after: Include items with date >= this value
        before: Include items with date <= this value

    Returns:
        Filtered list of items
    """
    if after is None and before is None:
        return items

    # Make filter dates timezone-aware if provided
    after_aware = _make_aware(after) if after else None
    before_aware = _make_aware(before) if before else None

    result = []
    for item in items:
        item_date = parse_date_field(item.get(field))
        if item_date is None:
            continue

        # Make item date timezone-aware for comparison
        item_date_aware = _make_aware(item_date)

        if after_aware is not None and item_date_aware < after_aware:
            continue

        if before_aware is not None and item_date_aware > before_aware:
            continue

        result.append(item)

    return result


def filter_by_field_value(
    items: list[T],
    field: str,
    value: Any,
    case_insensitive: bool = False,
) -> list[T]:
    """Filter items where field equals value.

    Args:
        items: List of dictionaries to filter
        field: Name of field to match
        value: Value to match against
        case_insensitive: If True, perform case-insensitive string comparison

    Returns:
        Filtered list of items
    """
    if value is None:
        return items

    result = []
    for item in items:
        item_value = item.get(field)

        if case_insensitive and isinstance(item_value, str) and isinstance(value, str):
            if item_value.lower() == value.lower():
                result.append(item)
        elif item_value == value:
            result.append(item)

    return result


def filter_by_field_contains(
    items: list[T],
    field: str,
    substring: str,
    case_insensitive: bool = True,
) -> list[T]:
    """Filter items where field contains substring.

    Args:
        items: List of dictionaries to filter
        field: Name of field to search
        substring: Substring to search for
        case_insensitive: If True, perform case-insensitive search

    Returns:
        Filtered list of items
    """
    if not substring:
        return items

    if case_insensitive:
        substring = substring.lower()

    result = []
    for item in items:
        item_value = item.get(field, "")
        if not isinstance(item_value, str):
            continue

        if case_insensitive:
            item_value = item_value.lower()

        if substring in item_value:
            result.append(item)

    return result


class ListFilter(Generic[T]):
    """Chainable filter builder for list data.

    Example:
        filtered = (
            ListFilter(branches)
            .by_date_range("createdDate", after=some_date)
            .by_field("userId", user_id)
            .by_contains("name", "prod")
            .result()
        )
    """

    def __init__(self, items: list[T]):
        """Initialize with list of items to filter.

        Args:
            items: List of dictionaries to filter
        """
        self._items = list(items)  # Copy to avoid mutation

    def by_date_range(
        self,
        field: str,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> "ListFilter[T]":
        """Chain date range filter.

        Args:
            field: Name of the date field
            after: Include items with date >= this value
            before: Include items with date <= this value

        Returns:
            Self for chaining
        """
        self._items = filter_by_date_range(self._items, field, after, before)
        return self

    def by_field(
        self,
        field: str,
        value: Any,
        case_insensitive: bool = False,
    ) -> "ListFilter[T]":
        """Chain exact match filter.

        Args:
            field: Name of field to match
            value: Value to match against
            case_insensitive: If True, perform case-insensitive string comparison

        Returns:
            Self for chaining
        """
        self._items = filter_by_field_value(self._items, field, value, case_insensitive)
        return self

    def by_contains(
        self,
        field: str,
        substring: str,
        case_insensitive: bool = True,
    ) -> "ListFilter[T]":
        """Chain substring filter.

        Args:
            field: Name of field to search
            substring: Substring to search for
            case_insensitive: If True, perform case-insensitive search

        Returns:
            Self for chaining
        """
        self._items = filter_by_field_contains(self._items, field, substring, case_insensitive)
        return self

    def result(self) -> list[T]:
        """Return filtered results.

        Returns:
            Filtered list of items
        """
        return self._items
