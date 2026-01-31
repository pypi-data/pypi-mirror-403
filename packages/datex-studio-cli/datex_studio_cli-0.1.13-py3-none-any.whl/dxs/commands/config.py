"""Configuration commands: dxs config [get|set|list]."""

import click

from dxs.cli import DxsContext, pass_context
from dxs.utils.config import get_config_value, list_config, set_config_value
from dxs.utils.restricted import restrict_in_restricted_mode
from dxs.utils.responses import list_response, single


@click.group()
def config() -> None:
    """Configuration commands.

    Manage CLI configuration stored in ~/.datex/config.yaml.
    Configuration can also be set via environment variables (prefixed with DXS_).
    """
    pass


@config.command("get")
@click.argument("key")
@pass_context
def config_get(ctx: DxsContext, key: str) -> None:
    """Get a configuration value.

    \b
    Arguments:
        KEY  Configuration key (e.g., api_base_url, default_org)

    \b
    Example:
        dxs config get api_base_url
        dxs config get default_org
    """
    value = get_config_value(key)
    if value is None:
        ctx.output(
            single(
                item={
                    "key": key,
                    "value": None,
                    "message": f"Configuration key '{key}' is not set",
                },
                semantic_key="config",
            )
        )
    else:
        ctx.output(single(item={"key": key, "value": value}, semantic_key="config"))


@config.command("set")
@click.argument("key")
@click.argument("value")
@pass_context
@restrict_in_restricted_mode("modifies configuration files")
def config_set(ctx: DxsContext, key: str, value: str) -> None:
    """Set a configuration value.

    \b
    Arguments:
        KEY    Configuration key (e.g., api_base_url, default_org)
        VALUE  Value to set

    \b
    Example:
        dxs config set api_base_url https://api.datex.io
        dxs config set default_org my-org-id
        dxs config set default_app 100
    """
    # Convert numeric strings to integers for known integer fields
    int_fields = {"default_app", "default_app_def", "api_timeout"}
    if key in int_fields:
        try:
            parsed_value: str | int = int(value)
        except ValueError:
            ctx.output_error(Exception(f"Value for '{key}' must be an integer, got '{value}'"))
            return
    else:
        parsed_value = value

    set_config_value(key, parsed_value)
    ctx.output(
        single(
            item={
                "key": key,
                "value": parsed_value,
                "message": f"Configuration '{key}' set successfully",
            },
            semantic_key="config",
        )
    )


@config.command("list")
@pass_context
def config_list(ctx: DxsContext) -> None:
    """List all configuration values.

    Shows all configuration values with their sources (environment, config_file, or default).

    \b
    Example:
        dxs config list
    """
    all_config = list_config()

    # Format for output
    items = []
    for key, info in all_config.items():
        items.append(
            {
                "key": key,
                "value": info["value"],
                "source": info["source"],
                "description": info["description"],
            }
        )

    ctx.output(list_response(items=items, semantic_key="configuration"))
