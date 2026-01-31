"""Docker CLI commands for paxx.

These commands are thin wrappers around docker compose for convenience.
They work within a generated project directory that has Docker files.
"""

import subprocess
from pathlib import Path

import typer

app = typer.Typer(
    name="docker",
    help="Docker development commands (wraps docker compose)",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _check_docker_setup() -> None:
    """Check that docker-compose.yml exists in the current directory."""
    if not Path("docker-compose.yml").exists():
        typer.secho(
            "Error: docker-compose.yml not found in current directory.\n"
            "Make sure you're running this command from your project root.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)


def _run_docker_compose(*args: str) -> subprocess.CompletedProcess[bytes]:
    """Run a docker compose command."""
    _check_docker_setup()
    cmd = ["docker", "compose", *args]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)
    return result


@app.command("up")
def up(
    detach: bool = typer.Option(
        False,
        "--detach",
        "-d",
        help="Run containers in the background",
    ),
    build: bool = typer.Option(
        False,
        "--build",
        "-b",
        help="Rebuild images before starting",
    ),
) -> None:
    """Start the development environment.

    Starts the app and database containers using docker compose.
    The app runs with hot-reload enabled - code changes are reflected immediately.

    Examples:
        paxx docker up           # Start in foreground (see logs)
        paxx docker up -d        # Start in background
        paxx docker up --build   # Rebuild and start
    """
    typer.echo("Starting development environment...")
    args = ["up"]
    if detach:
        args.append("--detach")
    if build:
        args.append("--build")
    _run_docker_compose(*args)


@app.command("down")
def down(
    volumes: bool = typer.Option(
        False,
        "--volumes",
        "-v",
        help="Remove named volumes (deletes database data)",
    ),
) -> None:
    """Stop the development environment.

    Stops and removes containers. By default, preserves database data.

    Examples:
        paxx docker down         # Stop containers, keep data
        paxx docker down -v      # Stop and delete all data
    """
    typer.echo("Stopping development environment...")
    args = ["down"]
    if volumes:
        args.append("--volumes")
        typer.secho(
            "Warning: This will delete your database data!",
            fg=typer.colors.YELLOW,
        )
    _run_docker_compose(*args)
    typer.secho("Development environment stopped.", fg=typer.colors.GREEN)


@app.command("build")
def build(
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Build without using cache",
    ),
) -> None:
    """Build the Docker images.

    Rebuilds the development Docker image. Useful after changing dependencies.

    Examples:
        paxx docker build            # Build with cache
        paxx docker build --no-cache # Full rebuild
    """
    typer.echo("Building Docker images...")
    args = ["build"]
    if no_cache:
        args.append("--no-cache")
    _run_docker_compose(*args)
    typer.secho("Build complete!", fg=typer.colors.GREEN)


@app.command("logs")
def logs(
    follow: bool = typer.Option(
        True,
        "--follow/--no-follow",
        "-f/-F",
        help="Follow log output",
    ),
    service: str = typer.Argument(
        None,
        help="Service to show logs for (app, db). Default: all services",
    ),
) -> None:
    """Show container logs.

    View logs from the running containers.

    Examples:
        paxx docker logs         # Follow all logs
        paxx docker logs app     # Follow app logs only
        paxx docker logs -F      # Show logs without following
    """
    args = ["logs"]
    if follow:
        args.append("--follow")
    if service:
        args.append(service)
    _run_docker_compose(*args)


@app.command("ps")
def ps() -> None:
    """Show running containers.

    Lists the status of containers in the development environment.
    """
    _run_docker_compose("ps")


@app.command("exec")
def exec_cmd(
    service: str = typer.Argument(
        "app",
        help="Service to run command in (default: app)",
    ),
    command: str = typer.Argument(
        "bash",
        help="Command to execute (default: bash)",
    ),
) -> None:
    """Execute a command in a running container.

    Opens an interactive shell or runs a command in the specified service.

    Examples:
        paxx docker exec              # Open bash in app container
        paxx docker exec app bash     # Same as above
        paxx docker exec db psql      # Open psql in database container
    """
    _run_docker_compose("exec", service, command)


if __name__ == "__main__":
    app()
