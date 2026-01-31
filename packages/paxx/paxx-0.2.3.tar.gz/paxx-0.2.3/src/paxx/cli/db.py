"""Database CLI commands for paxx.

These commands are thin wrappers around Alembic for convenience.
They work within a generated project directory.
"""

import subprocess
from pathlib import Path

import typer

app = typer.Typer(
    name="db",
    help="Database migration commands (wraps Alembic)",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _check_alembic_setup() -> None:
    """Check that alembic.ini exists in the current directory."""
    if not Path("alembic.ini").exists():
        typer.secho(
            "Error: alembic.ini not found in current directory.\n"
            "Make sure you're running this command from your project root.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)


def _check_db_connection_error(stderr: str) -> bool:
    """Check if stderr indicates a database connection error."""
    connection_error_patterns = [
        "Connect call failed",
        "Connection refused",
        "could not connect to server",
        "connection to server at",
        "Is the server running",
        "OperationalError",
    ]
    return any(pattern in stderr for pattern in connection_error_patterns)


def _run_alembic(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run an alembic command."""
    _check_alembic_setup()
    # Use uv run to ensure alembic runs in the local project's venv
    cmd = ["uv", "run", "alembic", *args]
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Check if this is a database connection error
        if _check_db_connection_error(result.stderr):
            typer.secho(
                "\nError: Could not connect to the database.",
                fg=typer.colors.RED,
            )
            typer.echo(
                "Make sure your database is running. If using Docker:\n"
                "  docker compose up -d db"
            )
        else:
            # Print stderr for other errors
            if result.stderr:
                typer.echo(result.stderr, err=True)
        raise typer.Exit(result.returncode)
    # Print stdout if not capturing (normal behavior)
    if not capture and result.stdout:
        typer.echo(result.stdout, nl=False)
    return result


@app.command("migrate")
def migrate(
    message: str = typer.Argument(..., help="Migration message describing the changes"),
    autogenerate: bool = typer.Option(
        True,
        "--autogenerate/--no-autogenerate",
        "-a/-A",
        help="Autogenerate migration from model changes",
    ),
) -> None:
    """Create a new migration.

    Generates a new migration file in migrations/versions/.
    By default, auto-detects changes from your models (--autogenerate).

    Examples:
        paxx db migrate "add users table"
        paxx db migrate "add email index" --no-autogenerate
    """
    # Count existing migrations before
    versions_dir = Path("migrations/versions")
    before_count = len(list(versions_dir.glob("*.py"))) if versions_dir.exists() else 0

    typer.echo(f"Creating migration: {message}")
    args = ["revision", "-m", message]
    if autogenerate:
        args.extend(["--autogenerate"])
    _run_alembic(*args)

    # Check if a migration was actually created
    after_count = len(list(versions_dir.glob("*.py"))) if versions_dir.exists() else 0
    if after_count > before_count:
        typer.echo()
        typer.echo("Next step:")
        typer.echo("  Apply the migration to your database:")
        typer.echo("    uv run paxx db upgrade")


@app.command("upgrade")
def upgrade(
    revision: str = typer.Argument(
        "head",
        help="Target revision (default: head = latest)",
    ),
) -> None:
    """Apply migrations to the database.

    By default, applies all pending migrations (up to 'head').
    You can specify a specific revision to migrate to.

    Examples:
        paxx db upgrade          # Apply all pending migrations
        paxx db upgrade head     # Same as above
        paxx db upgrade +1       # Apply next migration only
        paxx db upgrade abc123   # Migrate to specific revision
    """
    typer.echo(f"Upgrading database to: {revision}")
    _run_alembic("upgrade", revision)
    typer.secho("Database upgraded successfully!", fg=typer.colors.GREEN)


@app.command("downgrade")
def downgrade(
    revision: str = typer.Argument(
        "-1",
        help="Target revision (default: -1 = previous)",
    ),
) -> None:
    """Revert migrations.

    By default, reverts the last migration (-1).
    You can specify a specific revision to downgrade to.

    Examples:
        paxx db downgrade        # Revert last migration
        paxx db downgrade -1     # Same as above
        paxx db downgrade -2     # Revert last 2 migrations
        paxx db downgrade base   # Revert all migrations
        paxx db downgrade abc123 # Downgrade to specific revision
    """
    typer.echo(f"Downgrading database to: {revision}")
    _run_alembic("downgrade", revision)
    typer.secho("Database downgraded successfully!", fg=typer.colors.GREEN)


@app.command("status")
def status() -> None:
    """Show current migration status.

    Displays the current revision and any pending migrations.
    """
    typer.echo("Current migration status:")
    _run_alembic("current", "--verbose")


@app.command("history")
def history(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed history",
    ),
) -> None:
    """Show migration history.

    Lists all migrations in order of creation.
    """
    args = ["history"]
    if verbose:
        args.append("--verbose")
    _run_alembic(*args)


@app.command("heads")
def heads() -> None:
    """Show current available heads.

    Useful when dealing with migration branches.
    """
    _run_alembic("heads", "--verbose")


if __name__ == "__main__":
    app()
