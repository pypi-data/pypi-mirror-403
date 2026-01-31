"""Wizard CLI command.

Provides the `bpsai-pair wizard` command to start the web-based setup wizard.
"""

from __future__ import annotations

import signal
import sys
import threading
from pathlib import Path

import typer
from rich.console import Console

console = Console()

# Create wizard command group
wizard_app = typer.Typer(
    help="Setup wizard commands",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _check_dependencies() -> bool:
    """Check if wizard dependencies are installed."""
    try:
        import fastapi  # noqa: F401
        import jinja2  # noqa: F401
        import uvicorn  # noqa: F401
        return True
    except ImportError:
        return False


def _open_browser_delayed(url: str, delay: float = 1.0) -> None:
    """Open browser after a short delay to let server start."""
    import time
    from bpsai_pair.wizard.app import open_browser

    time.sleep(delay)
    open_browser(url)


def _check_api_key() -> bool:
    """Check if ANTHROPIC_API_KEY is available."""
    import os
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def run_server(port: int, no_browser: bool = False, demo: bool = False) -> None:
    """Run the wizard server.

    Args:
        port: Port to run on
        no_browser: If True, don't open browser automatically
        demo: If True, open browser with ?demo=1 for demo mode
    """
    import uvicorn
    from bpsai_pair.wizard.app import create_app

    app = create_app()
    url = f"http://localhost:{port}"
    if demo:
        url += "?demo=1"

    # Open browser in background thread
    if not no_browser:
        browser_thread = threading.Thread(
            target=_open_browser_delayed,
            args=(url,),
            daemon=True,
        )
        browser_thread.start()

    console.print()
    console.print(f"[bold blue]PairCoder Setup Wizard[/bold blue]")
    if demo:
        console.print("[yellow]Demo mode:[/yellow] Files will be written to a temp directory")
    console.print(f"Running at: [cyan]{url}[/cyan]")

    # Check for API key and warn if missing (needed for Guided Setup chat)
    if not _check_api_key():
        console.print()
        console.print("[yellow]Note:[/yellow] ANTHROPIC_API_KEY not found.")
        console.print("The [bold]Guided Setup[/bold] chat feature requires an API key.")
        console.print("You can still use [bold]Quick Setup[/bold] without it.")
        console.print()
        console.print("To enable Guided Setup:")
        console.print("  [cyan]export ANTHROPIC_API_KEY='your-key-here'[/cyan]")

    console.print()
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    # Run uvicorn with graceful shutdown
    uvicorn.run(
        app,
        host="localhost",
        port=port,
        log_level="warning",
    )


def _has_existing_config() -> bool:
    """Check if an existing .paircoder/config.yaml exists in the CWD."""
    return (Path.cwd() / ".paircoder" / "config.yaml").exists()


def _abort_missing_deps() -> None:
    """Print error message and raise exit for missing dependencies."""
    console.print("[red]Error:[/red] Wizard dependencies not installed.")
    console.print()
    console.print("Install with:")
    console.print("  [cyan]pip install bpsai-pair[wizard][/cyan]")
    console.print()
    raise typer.Exit(1)


def _abort_existing_config() -> None:
    """Print warning and raise exit when existing config is found."""
    console.print("[yellow]Warning:[/yellow] Existing .paircoder/config.yaml found.")
    console.print("The wizard may overwrite your existing configuration.")
    console.print()
    console.print("Options:")
    console.print("  [cyan]--demo[/cyan]   Run in demo mode (writes to temp directory)")
    console.print("  [cyan]--force[/cyan]  Overwrite existing config")
    console.print()
    raise typer.Exit(1)


@wizard_app.callback(invoke_without_command=True)
def wizard_main(
    ctx: typer.Context,
    port: int = typer.Option(8765, "--port", "-p", help="Port to run the wizard on"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser automatically"),
    demo: bool = typer.Option(False, "--demo", help="Run in demo mode (writes to temp directory)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config without prompting"),
) -> None:
    """Start the PairCoder setup wizard.

    Launches a web-based setup wizard at http://localhost:8765 (default).
    The wizard guides you through configuring PairCoder for your project.
    """
    if ctx.invoked_subcommand is not None:
        return

    if not _check_dependencies():
        _abort_missing_deps()

    if not demo and not force and _has_existing_config():
        _abort_existing_config()

    def signal_handler(sig, frame):
        console.print("\n[dim]Shutting down...[/dim]")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    run_server(port=port, no_browser=no_browser, demo=demo)
