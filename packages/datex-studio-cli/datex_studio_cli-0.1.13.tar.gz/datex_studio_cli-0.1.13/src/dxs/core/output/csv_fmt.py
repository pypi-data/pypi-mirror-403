"""CSV output formatter."""

import csv
import io
from typing import Any


def format_csv(data: Any) -> str:
    """Format data as CSV.

    Handles lists of dicts, lists of Pydantic models, and single dicts.

    Args:
        data: Data to format.

    Returns:
        CSV-formatted string.
    """
    # Normalize data to list of dicts
    items = _normalize_to_list(data)

    if not items:
        return ""

    # Get headers from first item
    headers = _get_headers(items[0])

    if not headers:
        return ""

    # Write CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()

    for item in items:
        row = _item_to_row(item, headers)
        writer.writerow(row)

    return output.getvalue()


def _normalize_to_list(data: Any) -> list[dict[str, Any]]:
    """Normalize data to a list of dictionaries.

    Args:
        data: Input data.

    Returns:
        List of dictionaries.
    """
    # Handle Pydantic models
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")

    # Handle dict with common wrapper keys
    if isinstance(data, dict):
        # Check for common list keys
        for key in ["entries", "items", "data", "commits", "configs", "versions"]:
            if key in data and isinstance(data[key], list):
                return [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                    for item in data[key]
                ]

        # Single dict - wrap in list
        return [data]

    # Handle list
    if isinstance(data, list):
        return [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in data
        ]

    # Fallback - wrap in list with value key
    return [{"value": data}]


def _get_headers(item: Any) -> list[str]:
    """Get column headers from an item.

    Args:
        item: First item in the list.

    Returns:
        List of header names.
    """
    if isinstance(item, dict):
        return list(item.keys())
    elif hasattr(item, "model_fields"):
        return list(item.model_fields.keys())
    elif hasattr(item, "__dict__"):
        return list(item.__dict__.keys())
    else:
        return ["value"]


def _item_to_row(item: Any, headers: list[str]) -> dict[str, Any]:
    """Convert an item to a CSV row dictionary.

    Args:
        item: Item to convert.
        headers: Expected headers.

    Returns:
        Dictionary suitable for csv.DictWriter.
    """
    if isinstance(item, dict):
        return {h: _format_value(item.get(h)) for h in headers}
    elif hasattr(item, "model_dump"):
        d = item.model_dump(mode="json")
        return {h: _format_value(d.get(h)) for h in headers}
    else:
        return {"value": _format_value(item)}


def _format_value(value: Any) -> str:
    """Format a value for CSV output.

    Args:
        value: Value to format.

    Returns:
        String representation.
    """
    if value is None:
        return ""
    elif isinstance(value, (dict, list)):
        # Nested structures - convert to JSON-like string
        import json

        return json.dumps(value)
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)
