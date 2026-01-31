"""Studio command: dxs studio — launch local web UI for OData exploration."""

import click


@click.command()
@click.option("--port", "-p", type=int, default=5051, help="Port to run the server on")
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Don't auto-open browser on startup",
)
def studio(port: int, no_browser: bool) -> None:
    """Launch a local web UI for OData data exploration.

    Opens a browser-based interface for visually exploring OData data
    from Footprint API connections. Requires prior authentication
    via 'dxs auth login'.

    \b
    Examples:
        dxs studio
        dxs studio --port 5050
        dxs studio --no-browser
    """
    try:
        import uvicorn  # noqa: F401
    except ImportError as e:
        raise click.ClickException(
            "Studio requires extra dependencies. Install with:\n\n"
            "  uv pip install 'datex-studio-cli[studio]'\n\n"
            "Or if developing locally:\n\n"
            "  uv sync --extra studio"
        ) from e

    from dxs.core.auth.token_cache import MultiIdentityTokenCache

    # Verify auth before starting server
    cache = MultiIdentityTokenCache()
    identity = cache.get_active_identity()
    if identity is None:
        raise click.ClickException(
            "Not authenticated. Run 'dxs auth login' first."
        )

    click.echo(f"Starting Datex Studio on http://127.0.0.1:{port}", err=True)

    if not no_browser:
        import threading
        import webbrowser

        def _open_browser() -> None:
            import time

            time.sleep(1)
            webbrowser.open(f"http://127.0.0.1:{port}")

        threading.Thread(target=_open_browser, daemon=True).start()

    from dxs.web.app import create_app

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
