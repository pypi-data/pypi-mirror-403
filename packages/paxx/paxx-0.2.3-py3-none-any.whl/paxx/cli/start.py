"""CLI command for starting the development server."""

import subprocess

import typer
from rich.console import Console

from paxx.cli.utils import check_project_context

console = Console()


def start(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-H",
        help="Host to bind to",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind to",
    ),
    reload: bool = typer.Option(
        True,
        "--reload/--no-reload",
        "-r/-R",
        help="Enable auto-reload on code changes",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes (only used without --reload)",
    ),
) -> None:
    """Start the development server.

    This command starts uvicorn with sensible defaults for development.
    Auto-reload is enabled by default for a smooth development experience.

    Examples:
        paxx start                         # Start on localhost:8000 with reload
        paxx start --port 3000             # Start on port 3000
        paxx start --host 0.0.0.0          # Bind to all interfaces
        paxx start --no-reload --workers 4 # Production-like mode
    """
    check_project_context(require_settings=False)

    console.print(f"Starting server at [bold cyan]http://{host}:{port}[/bold cyan]")
    if reload:
        console.print("[grey70]Auto-reload enabled. Press Ctrl+C to stop.[/grey70]")
    console.print()

    # Build uvicorn command
    # Use uv run to ensure uvicorn runs in the local project's venv
    cmd = [
        "uv",
        "run",
        "uvicorn",
        "main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    if reload:
        cmd.append("--reload")
    else:
        cmd.extend(["--workers", str(workers)])

    # Run uvicorn
    try:
        result = subprocess.run(cmd, check=False)
        raise typer.Exit(result.returncode)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
        raise typer.Exit(0) from None
