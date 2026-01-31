"""Main CLI entry point for paxx."""

import typer

from paxx import __version__
from paxx.cli.bootstrap import create_project
from paxx.cli.db import app as db_app
from paxx.cli.deploy import app as deploy_app
from paxx.cli.docker import app as docker_app
from paxx.cli.ext.commands import app as ext_app
from paxx.cli.feature import app as feature_app
from paxx.cli.infra.commands import app as infra_app
from paxx.cli.start import start

app = typer.Typer(
    name="paxx",
    help="paxx - a domain-oriented web framework built on top of FastAPI",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Register subcommands
app.add_typer(db_app, name="db")
app.add_typer(deploy_app, name="deploy")
app.add_typer(docker_app, name="docker")
app.add_typer(ext_app, name="ext")
app.add_typer(feature_app, name="feature")
app.add_typer(infra_app, name="infra")

# Register top-level commands
app.command(
    "bootstrap",
    help="Scaffold a new FastAPI project with database, config, and app factory.",
)(create_project)
app.command("start")(start)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    _version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show the paxx version and exit.",
    ),
) -> None:
    """paxx - a domain-oriented web framework built on top of FastAPI."""


if __name__ == "__main__":
    app()
