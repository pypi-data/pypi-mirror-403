"""Main CLI entry point for Datex Studio CLI."""

import sys
from collections.abc import Callable
from typing import Any, TypeVar, cast

import click

from dxs import __app_name__, __version__
from dxs.core.output import OutputFormat, format_error, format_output
from dxs.utils.config import get_settings
from dxs.utils.errors import DxsError

F = TypeVar("F", bound=Callable[..., Any])

# Fields to strip from author objects in concise mode
_AUTHOR_VERBOSE_FIELDS = {"id", "organizationId", "externalId", "hasManagementAccess"}


def _strip_concise(data: Any, parent_key: str | None = None) -> Any:
    """Strip null values and verbose metadata from data for concise output.

    Args:
        data: Data to strip (dict, list, or other).
        parent_key: The key of the parent that contains this data.

    Returns:
        Data with nulls and verbose fields removed.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Skip null values
            if value is None:
                continue
            # Skip verbose author fields only within author objects
            if parent_key == "author" and key in _AUTHOR_VERBOSE_FIELDS:
                continue
            # Recursively process nested structures, passing the key as context
            result[key] = _strip_concise(value, parent_key=key)
        return result
    elif isinstance(data, list):
        return [_strip_concise(item, parent_key=parent_key) for item in data]
    else:
        return data


class DxsContext:
    """Shared context passed to all commands."""

    def __init__(self) -> None:
        self.output_format: OutputFormat = OutputFormat.YAML
        self.verbose: bool = False
        self.quiet: bool = False
        self.concise: bool = True  # Concise output is default
        self.org: str | None = None
        self.env: str | None = None
        self.branch: int | None = None
        self.repo: int | None = None
        self.save_path: str | None = None
        self.force_overwrite: bool = False
        self.explicit_output_format: bool = False

    def output(self, data: Any, include_metadata: bool = True) -> None:
        """Output data in the configured format.

        Args:
            data: Data to output.
            include_metadata: Include timestamp and version metadata.
        """
        from dxs.core.output.formatter import detect_format_from_extension

        # Determine format: --output flag > file extension > default
        if self.save_path and not self.explicit_output_format:
            output_format = detect_format_from_extension(self.save_path, self.output_format)
        else:
            output_format = self.output_format

        formatted = format_output(data, output_format, include_metadata, self.concise)

        # Save to file if requested (suppresses stdout)
        if self.save_path:
            self._save_to_file(formatted)
            return

        click.echo(formatted)

    def _save_to_file(self, content: str) -> None:
        """Save content to file with overwrite protection.

        Args:
            content: Formatted content to save.

        Raises:
            ValidationError: If file exists and force_overwrite is False.
            DxsError: If file write fails.
            RestrictedModeError: If restricted mode is enabled.
        """
        from pathlib import Path

        from dxs.utils.config import is_restricted_mode
        from dxs.utils.errors import RestrictedModeError, ValidationError

        # Block file saving in restricted mode
        if is_restricted_mode():
            raise RestrictedModeError(
                command_name="--save option",
                reason="writes files to the filesystem",
            )

        assert self.save_path is not None  # Caller checks this
        path = Path(self.save_path)

        if path.exists() and not self.force_overwrite:
            raise ValidationError(
                message=f"File '{self.save_path}' already exists",
                code="DXS-FILE-001",
                suggestions=[
                    "Use --force flag to overwrite the file",
                    "Specify a different filename with --save",
                ],
            )

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_text(content, encoding="utf-8")
            self.debug(f"Output saved to: {self.save_path}")
        except OSError as e:
            raise DxsError(
                code="DXS-FILE-002",
                message=f"Failed to write file '{self.save_path}': {e}",
            ) from e

    def output_error(self, error: DxsError | Exception) -> None:
        """Output an error in the configured format.

        Args:
            error: Error to output.
        """
        formatted = format_error(error, self.output_format)
        click.echo(formatted, err=True)

    def log(self, message: str) -> None:
        """Log a message (respects quiet flag).

        Args:
            message: Message to log.
        """
        if not self.quiet:
            click.echo(message, err=True)

    def debug(self, message: str) -> None:
        """Log a debug message (only in verbose mode).

        Args:
            message: Debug message to log.
        """
        if self.verbose:
            click.echo(f"[DEBUG] {message}", err=True)


# Create a pass decorator for the context
pass_context = click.make_pass_decorator(DxsContext, ensure=True)


# Global options shared across all commands
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 120,
}


class DxsGroup(click.Group):
    """Custom Group that shows global options in subcommand help."""

    def format_options(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write options to the formatter, including global options."""
        # First write local options
        super().format_options(ctx, formatter)

        # Then add global options section if we have a parent
        if ctx.parent is not None:
            # Get global options from the root command
            root_ctx = ctx
            while root_ctx.parent is not None:
                root_ctx = root_ctx.parent

            if root_ctx.command and hasattr(root_ctx.command, "params"):
                global_opts = []
                for param in root_ctx.command.params:
                    if isinstance(param, click.Option):
                        record = param.get_help_record(ctx)
                        if record:
                            global_opts.append(record)

                if global_opts:
                    with formatter.section("Global Options"):
                        formatter.write_dl(global_opts)


@click.group(cls=DxsGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name=__app_name__)
@click.option(
    "-o",
    "--org",
    type=str,
    envvar="DXS_ORG",
    help="Organization ID (overrides default)",
)
@click.option(
    "-e",
    "--env",
    type=str,
    envvar="DXS_ENV",
    help="Environment ID (overrides default)",
)
@click.option(
    "-b",
    "--branch",
    type=int,
    envvar="DXS_BRANCH",
    help="Branch ID (overrides default)",
)
@click.option(
    "-r",
    "--repo",
    type=int,
    envvar="DXS_REPO",
    help="Repository ID (overrides default)",
)
@click.option(
    "-t",
    "--target",
    type=click.Choice(["dev", "qa", "prod"], case_sensitive=False),
    envvar="DXS_TARGET",
    default=None,
    help="API target environment (dev, qa, or prod; default: prod)",
)
@click.option(
    "-O",
    "--output",
    "output_format",
    type=click.Choice(["yaml", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (default: yaml)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output (show progress messages)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress non-essential output (progress messages)",
)
@click.option(
    "-f",
    "--full",
    is_flag=True,
    default=False,
    help="Show full output including null values and verbose metadata",
)
@click.option(
    "-s",
    "--save",
    "save_path",
    type=click.Path(dir_okay=False, writable=True, path_type=str),
    default=None,
    help="Save output to file (format auto-detected from extension)",
)
@click.option(
    "--force",
    "force_overwrite",
    is_flag=True,
    default=False,
    help="Force overwrite existing file when using --save",
)
@click.option(
    "--diagnose-auth",
    "diagnose_auth",
    is_flag=True,
    default=False,
    help="Show authentication environment variables for debugging",
)
@click.pass_context
def cli(
    ctx: click.Context,
    org: str | None,
    env: str | None,
    branch: int | None,
    repo: int | None,
    target: str | None,
    output_format: str | None,
    verbose: bool,
    quiet: bool,
    full: bool,
    save_path: str | None,
    force_overwrite: bool,
    diagnose_auth: bool,
) -> None:
    """Datex Studio CLI - Command-line interface for Datex Studio platform.

    Designed for LLM-based AI agents. Use --output yaml (default) or --output json
    for structured, parseable responses.

    \b
    Examples:
        dxs auth login
        dxs source log --repo 10
        dxs source history userGrid --branch 100
        dxs config list

    \b
    Environment Variables:
        DXS_ORG         Default organization ID
        DXS_ENV         Default environment ID
        DXS_BRANCH      Default branch ID
        DXS_REPO        Default repository ID
        DXS_TARGET      API target environment (dev, qa, prod)

    \b
    Configuration:
        Settings are stored in ~/.datex/config.yaml
        Credentials are stored in ~/.datex/credentials.yaml
    """
    import os

    # Initialize context
    ctx.ensure_object(DxsContext)
    dxs_ctx: DxsContext = ctx.obj

    # Set API base URL based on target environment
    if target:
        target_urls = {
            "dev": "https://dev.wavelength.host/api",
            "qa": "https://qa.wavelength.host/api",
            "prod": "https://wavelength.host/api",
        }
        os.environ["DXS_API_BASE_URL"] = target_urls[target.lower()]

    # Load settings
    settings = get_settings()

    # Set output format (CLI flag > env var > config > default)
    if output_format:
        dxs_ctx.output_format = OutputFormat(output_format.lower())
        dxs_ctx.explicit_output_format = True
    elif settings.default_output_format:
        dxs_ctx.output_format = OutputFormat(settings.default_output_format.lower())

    # Set verbosity (--verbose enables debug output, --quiet suppresses progress)
    dxs_ctx.verbose = verbose
    dxs_ctx.quiet = quiet
    # Concise output is default; --full disables it
    dxs_ctx.concise = not full

    # Set save options
    dxs_ctx.save_path = save_path
    dxs_ctx.force_overwrite = force_overwrite

    # Set context values (CLI flag > env var > config)
    dxs_ctx.org = org or settings.default_org
    dxs_ctx.env = env or settings.default_env
    dxs_ctx.branch = branch or settings.default_branch
    dxs_ctx.repo = repo or settings.default_repo

    # Show auth diagnostics if requested
    if diagnose_auth:
        _show_auth_diagnostics()


def _mask_token(token: str | None, visible_chars: int = 8) -> str:
    """Mask a token for display, showing only first/last few characters.

    Args:
        token: The token to mask, or None.
        visible_chars: Number of characters to show at start and end.

    Returns:
        Masked token string or "(not set)".
    """
    if not token:
        return "(not set)"
    if len(token) <= visible_chars * 2:
        return "***"
    return f"{token[:visible_chars]}...{token[-visible_chars:]}"


def _show_auth_diagnostics() -> None:
    """Display authentication environment variables for debugging."""
    import os

    click.echo("Authentication Environment Variables:", err=True)
    click.echo("-" * 40, err=True)

    # Token environment variables
    env_vars = [
        ("DXS_ACCESS_TOKEN", os.environ.get("DXS_ACCESS_TOKEN")),
        ("DXS_REFRESH_TOKEN", os.environ.get("DXS_REFRESH_TOKEN")),
        ("DXS_DEVOPS_TOKEN", os.environ.get("DXS_DEVOPS_TOKEN")),
        ("DXS_DYNAMICS_TOKEN", os.environ.get("DXS_DYNAMICS_TOKEN")),
    ]

    for name, value in env_vars:
        if value:
            masked = _mask_token(value)
            click.echo(f"  {name}: SET ({masked})", err=True)
        else:
            click.echo(f"  {name}: NOT SET", err=True)

    click.echo("-" * 40, err=True)
    click.echo("", err=True)


# Error handler decorator
def handle_errors(f: F) -> F:
    """Decorator to handle errors and output them in the configured format."""

    @click.pass_context
    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        dxs_ctx: DxsContext = ctx.obj
        try:
            return ctx.invoke(f, *args, **kwargs)
        except DxsError as e:
            dxs_ctx.output_error(e)
            sys.exit(1)
        except click.ClickException:
            # Let Click handle its own exceptions
            raise
        except Exception as e:
            dxs_ctx.output_error(e)
            sys.exit(1)

    return cast(F, wrapper)


# Import and register command groups
# These imports are here to avoid circular imports
def register_commands() -> None:
    """Register all command groups with the CLI."""
    from dxs.commands import (
        api,
        auth,
        config,
        crm,
        devops,
        env,
        marketplace,
        odata,
        organization,
        source,
        user,
    )

    cli.add_command(api.api)
    cli.add_command(auth.auth)
    cli.add_command(config.config)
    cli.add_command(crm.crm)
    cli.add_command(devops.devops)
    cli.add_command(env.env)
    cli.add_command(marketplace.marketplace)
    cli.add_command(odata.odata)
    cli.add_command(organization.organization)
    cli.add_command(source.source)
    cli.add_command(user.user)
    # branch and repo are registered as subcommands of source in source.py


# Register commands when module loads
register_commands()


# Main entry point
def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except DxsError as e:
        # Get the output format from context or default to YAML
        output_format = OutputFormat.YAML
        formatted = format_error(e, output_format)
        click.echo(formatted, err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
