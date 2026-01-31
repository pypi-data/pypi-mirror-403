"""YAML output formatter."""

from typing import Any

import yaml


class LiteralString(str):
    """String that should be rendered as a literal block in YAML.

    Automatically strips trailing whitespace from each line, which is required
    for PyYAML to use literal block style (|) instead of falling back to quoted strings.
    """

    def __new__(cls, value: str) -> "LiteralString":
        # Strip trailing whitespace from each line - required for YAML literal blocks
        # PyYAML falls back to quoted strings if any line has trailing whitespace
        lines = [line.rstrip() for line in value.split("\n")]
        cleaned = "\n".join(lines).strip()
        return super().__new__(cls, cleaned)


def literal_str_representer(dumper: yaml.Dumper, data: LiteralString) -> yaml.Node:
    """Custom representer for literal strings."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


# Register the custom representer
yaml.add_representer(LiteralString, literal_str_representer)


def convert_code_to_literal(data: Any) -> Any:
    """Recursively convert 'code' fields to LiteralString for multiline YAML display.

    Walks through dicts and lists, converting any 'code' field containing
    a string to a LiteralString which will render as a YAML literal block (|).
    Also normalizes line endings from \\r\\n to \\n.

    Args:
        data: Data structure to process (dict, list, or scalar).

    Returns:
        Same structure with 'code' fields converted to LiteralString.
    """
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key == "code" and isinstance(value, str):
                # Convert \r\n to \n and use LiteralString for multiline display
                cleaned = value.replace("\r\n", "\n").replace("\r", "\n")
                result[key] = LiteralString(cleaned)
            else:
                result[key] = convert_code_to_literal(value)
        return result
    elif isinstance(data, list):
        return [convert_code_to_literal(item) for item in data]
    else:
        return data


def format_yaml(data: Any, default_flow_style: bool = False) -> str:
    """Format data as YAML.

    Args:
        data: Data to format.
        default_flow_style: Use flow style for collections (compact).

    Returns:
        YAML-formatted string.
    """
    return yaml.dump(
        data,
        default_flow_style=default_flow_style,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
