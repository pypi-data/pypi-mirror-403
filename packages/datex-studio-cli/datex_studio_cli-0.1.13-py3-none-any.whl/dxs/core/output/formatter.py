"""Output formatting orchestrator for YAML, JSON, and CSV output."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from dxs import __version__
from dxs.core.responses import Response
from dxs.utils.errors import DxsError


class OutputFormat(str, Enum):
    """Supported output formats."""

    YAML = "yaml"
    JSON = "json"
    CSV = "csv"


def format_output(
    data: Any,
    format: OutputFormat = OutputFormat.YAML,
    include_metadata: bool = True,
    concise: bool = False,
) -> str:
    """Format data for output.

    Args:
        data: Data to format (Response object, dict, list, or Pydantic model).
        format: Output format (yaml, json, csv).
        include_metadata: Include timestamp and version metadata.
        concise: Strip null values and verbose metadata.

    Returns:
        Formatted string output.
    """
    # All commands now use Response objects
    if not isinstance(data, Response):
        raise TypeError(
            f"Expected Response object, got {type(data).__name__}. "
            "All commands must use response builders (single, list_response, etc.)"
        )

    output_dict = data.to_output_dict()

    # Apply concise stripping if requested
    if concise:
        from dxs.cli import _strip_concise

        output_dict = _strip_concise(output_dict)

    # Format based on requested format
    if format == OutputFormat.YAML:
        from dxs.core.output.yaml_fmt import format_yaml

        return format_yaml(output_dict)
    elif format == OutputFormat.JSON:
        from dxs.core.output.json_fmt import format_json

        return format_json(output_dict)
    elif format == OutputFormat.CSV:
        from dxs.core.output.csv_fmt import format_csv

        # CSV doesn't use envelope - extract items/data
        if isinstance(data, Response):
            output = data.to_output_dict()
            # Get the data (not metadata)
            csv_data = next((v for k, v in output.items() if k != "metadata"), data)
        else:
            csv_data = data
        return format_csv(csv_data)
    else:
        # Default to YAML
        from dxs.core.output.yaml_fmt import format_yaml

        return format_yaml(output_dict)


def format_error(
    error: DxsError | Exception,
    format: OutputFormat = OutputFormat.YAML,
    include_metadata: bool = True,
) -> str:
    """Format error for output with standard envelope.

    Args:
        error: Exception to format.
        format: Output format (yaml, json, csv).
        include_metadata: Include timestamp and version metadata.

    Returns:
        Formatted error string.
    """
    if isinstance(error, DxsError):
        error_data = error.to_dict()
    else:
        error_data = {
            "code": "DXS-ERR-001",
            "message": str(error),
        }

    envelope: dict[str, Any] = {
        "error": error_data,
    }

    if include_metadata:
        envelope["metadata"] = {
            "success": False,  # MOVED HERE
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cli_version": __version__,
        }

    if format == OutputFormat.JSON:
        from dxs.core.output.json_fmt import format_json

        return format_json(envelope)
    else:
        # YAML for errors (CSV not suitable for errors)
        from dxs.core.output.yaml_fmt import format_yaml

        return format_yaml(envelope)


def parse_output_format(format_str: str) -> OutputFormat:
    """Parse output format string to enum.

    Args:
        format_str: Format string (yaml, json, csv).

    Returns:
        OutputFormat enum value.

    Raises:
        ValueError: If format string is invalid.
    """
    format_lower = format_str.lower()
    try:
        return OutputFormat(format_lower)
    except ValueError as e:
        valid_formats = ", ".join(f.value for f in OutputFormat)
        raise ValueError(
            f"Invalid output format '{format_str}'. Valid formats: {valid_formats}"
        ) from e


def detect_format_from_extension(filepath: str, fallback: OutputFormat) -> OutputFormat:
    """Detect output format from file extension.

    Args:
        filepath: Path to the file.
        fallback: Format to use if extension is unrecognized.

    Returns:
        OutputFormat enum value.
    """
    from pathlib import Path

    ext = Path(filepath).suffix.lower()
    extension_map = {
        ".yaml": OutputFormat.YAML,
        ".yml": OutputFormat.YAML,
        ".json": OutputFormat.JSON,
        ".csv": OutputFormat.CSV,
    }
    return extension_map.get(ext, fallback)
