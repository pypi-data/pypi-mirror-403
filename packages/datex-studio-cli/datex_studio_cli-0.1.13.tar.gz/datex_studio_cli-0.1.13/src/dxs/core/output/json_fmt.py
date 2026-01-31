"""JSON output formatter."""

import json
from datetime import datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON.

    Args:
        data: Data to format.
        indent: Number of spaces for indentation (0 for compact).

    Returns:
        JSON-formatted string.
    """
    return json.dumps(
        data,
        cls=DateTimeEncoder,
        indent=indent if indent > 0 else None,
        ensure_ascii=False,
    )


def format_json_compact(data: Any) -> str:
    """Format data as compact JSON (no whitespace).

    Args:
        data: Data to format.

    Returns:
        Compact JSON string.
    """
    return format_json(data, indent=0)
