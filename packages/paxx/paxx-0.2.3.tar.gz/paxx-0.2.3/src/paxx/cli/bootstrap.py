"""CLI command for bootstrapping a new paxx project."""

from pathlib import Path

import typer
from rich.console import Console

from paxx.cli.utils import create_jinja_env, to_snake_case, validate_name

console = Console()


def is_directory_empty(path: Path) -> bool:
    """Check if a directory is empty (ignoring hidden files like .git)."""
    if not path.exists():
        return True
    # Consider directory empty if it only contains hidden files/dirs
    visible_items = [item for item in path.iterdir() if not item.name.startswith(".")]
    return len(visible_items) == 0


def get_directory_contents_summary(path: Path) -> str:
    """Get a summary of directory contents for user information."""
    if not path.exists():
        return "directory does not exist"

    items = list(path.iterdir())
    visible_items = [item for item in items if not item.name.startswith(".")]
    hidden_items = [item for item in items if item.name.startswith(".")]

    parts = []
    if visible_items:
        files = [i for i in visible_items if i.is_file()]
        dirs = [i for i in visible_items if i.is_dir()]
        if files:
            parts.append(f"{len(files)} file(s)")
        if dirs:
            parts.append(f"{len(dirs)} folder(s)")
    if hidden_items:
        parts.append(f"{len(hidden_items)} hidden item(s)")

    return ", ".join(parts) if parts else "empty"


def create_project(
    ctx: typer.Context,
    name: str | None = typer.Argument(
        None,
        help="Name of the new project (use '.' to bootstrap in current directory)",
    ),
    output_dir: Path = typer.Option(
        Path("."),
        "--output-dir",
        "-o",
        help="Directory to create the project in (default: current directory)",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Project description",
    ),
    author: str = typer.Option(
        "Author",
        "--author",
        "-a",
        help="Author name",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompts (useful for CI/scripting)",
    ),
) -> None:
    """Bootstrap a new paxx project.

    This command scaffolds a new FastAPI project following paxx conventions,
    including database setup, configuration, and the application factory pattern.

    Examples:
        paxx bootstrap myproject
        paxx bootstrap my-api --description "My awesome API"
        paxx bootstrap myproject -o /path/to/projects
        paxx bootstrap .  # Bootstrap in current directory
        paxx bootstrap . -o /path/to/existing/dir  # Bootstrap in specific existing dir
    """
    # Show help if no name provided
    if name is None:
        console.print(ctx.get_help())
        raise typer.Exit(1)

    # Handle "." as current/target directory
    if name == ".":
        project_dir = output_dir.resolve()
        # Derive project name from directory name
        name = project_dir.name
        if not name or name == "/":
            console.print(
                "[bright_red]Error: Cannot determine project name "
                "from directory[/bright_red]"
            )
            raise typer.Exit(1)
        bootstrap_in_place = True
    else:
        # Validate name for new directories
        name = validate_name(name, entity_type="Project")
        project_dir = output_dir / name
        bootstrap_in_place = False

    # Validate the derived/provided name
    try:
        name = validate_name(name, entity_type="Project")
    except typer.BadParameter as e:
        console.print(f"[bright_red]Error: {e}[/bright_red]")
        raise typer.Exit(1) from None

    snake_name = to_snake_case(name)

    # Handle existing directory
    if project_dir.exists():
        is_empty = is_directory_empty(project_dir)
        contents_summary = get_directory_contents_summary(project_dir)

        if is_empty:
            console.print(
                f"[yellow]Directory '{project_dir}' already exists "
                "but is empty.[/yellow]"
            )
            if not force and not typer.confirm("Bootstrap project in this directory?"):
                console.print("[grey70]Aborted.[/grey70]")
                raise typer.Exit(0)
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Directory '{project_dir}' already exists "
                f"and contains: {contents_summary}"
            )
            console.print(
                "[yellow]Existing files with the same names will be "
                "overwritten![/yellow]"
            )
            console.print("[cyan]Your .env file will be preserved if it exists.[/cyan]")
            if not force and not typer.confirm(
                "Are you sure you want to bootstrap in this directory?"
            ):
                console.print("[grey70]Aborted.[/grey70]")
                raise typer.Exit(0)
    elif bootstrap_in_place:
        # Directory doesn't exist but we're using "." syntax
        console.print(
            f"[bright_red]Error: Directory '{project_dir}' does not exist[/bright_red]"
        )
        raise typer.Exit(1)

    console.print(f"Creating new paxx project: [bold cyan]{name}[/bold cyan]")

    # Set up Jinja environment
    env = create_jinja_env()

    # Template context
    context = {
        "project_name": name,
        "project_name_snake": snake_name,
        "project_description": description
        or "A FastAPI application built with paxx conventions",
        "author_name": author,
    }

    # Define project structure with templates
    project_files: dict[str, str | None] = {
        # Root files
        "Makefile": "project/Makefile.jinja",
        "pyproject.toml": "project/pyproject.toml.jinja",
        "settings.py": "project/settings.py.jinja",
        ".env.example": "project/.env.example.jinja",
        ".env": "project/.env.example.jinja",  # Create initial .env from example
        "alembic.ini": "project/alembic.ini.jinja",
        "main.py": "project/main.py.jinja",
        # Core module
        "core/__init__.py": "project/core/__init__.py.jinja",
        "core/logging.py": "project/core/logging.py.jinja",
        "core/exceptions.py": "project/core/exceptions.py.jinja",
        "core/middleware.py": "project/core/middleware.py.jinja",
        "core/dependencies.py": "project/core/dependencies.py.jinja",
        "core/schemas.py": "project/core/schemas.py.jinja",
        # Database module
        "db/__init__.py": "project/db/__init__.py.jinja",
        "db/database.py": "project/db/database.py.jinja",
        "db/migrations/env.py": "project/db/migrations/env.py.jinja",
        "db/migrations/script.py.mako": "project/db/migrations/script.py.mako.jinja",
        "db/migrations/versions/.gitkeep": None,  # Empty file
        # Features directory
        "features/__init__.py": None,  # Features package
        # Health feature
        "features/health/__init__.py": None,  # Health feature package
        "features/health/routes.py": "features/health/routes.py.jinja",
        # Test fixtures and e2e tests
        "conftest.py": "project/conftest.py.jinja",
        "e2e/__init__.py": None,  # E2E test package
        "e2e/conftest.py": "project/e2e/conftest.py.jinja",
        "e2e/test_health.py": "project/e2e/test_health.py.jinja",
        # Docker files
        "Dockerfile": "project/Dockerfile.jinja",
        "Dockerfile.dev": "project/Dockerfile.dev.jinja",
        "docker-compose.yml": "project/docker-compose.yml.jinja",
        ".dockerignore": "project/.dockerignore.jinja",
        "DEPLOY.md": "project/DEPLOY.md.jinja",
        # Deploy directory (empty by default, use `paxx deploy add` to add deployments)
        "deploy/README.md": "project/deploy/README.md.jinja",
        # Documentation and config
        "README.md": "project/README.md.jinja",
        ".gitignore": "project/.gitignore.jinja",
        # Claude Code configuration
        ".claude/CLAUDE.md": "project/.claude/CLAUDE.md.jinja",
        ".claude/settings.json": "project/.claude/settings.json.jinja",
    }

    # Create directories and files
    try:
        for file_path, template_name in project_files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Never overwrite .env - it may contain user settings
            if file_path == ".env" and full_path.exists():
                console.print(
                    f"  [cyan]Preserved[/cyan] {file_path} (existing file kept)"
                )
                continue

            if template_name is None:
                # Create empty file or directory marker
                if file_path.endswith("__init__.py"):
                    full_path.write_text('"""Package."""\n')
                else:
                    full_path.touch()
            else:
                # Render template
                template = env.get_template(template_name)
                content = template.render(**context)
                full_path.write_text(content)

            console.print(f"  [green]Created[/green] {file_path}")

        console.print()
        console.print("[bold green]Project created successfully![/bold green]")
        console.print()
        console.print("Next steps:")
        if bootstrap_in_place:
            console.print("  1. docker compose up")
        else:
            console.print(f"  1. cd {name}")
            console.print("  2. docker compose up")
        console.print()
        console.print("To create a new feature:")
        console.print("  uv run paxx feature create <feature_name>")

    except Exception as e:
        console.print(f"[bright_red]Error creating project: {e}[/bright_red]")
        raise typer.Exit(1) from None
