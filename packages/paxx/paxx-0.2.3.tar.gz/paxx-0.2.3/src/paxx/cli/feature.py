"""CLI subcommands for managing features."""

import ast
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from paxx.cli.utils import (
    check_project_context,
    create_jinja_env,
    to_snake_case,
    validate_name,
)
from paxx.templates.features import get_feature_dir, list_available_features

app = typer.Typer(
    name="feature",
    help="Manage paxx features",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def _list_features() -> None:
    """Display a table of available bundled features."""
    features = list_available_features()

    if not features:
        console.print("[yellow]No features available yet.[/yellow]")
        console.print(
            "\nFeature templates are coming soon. Check the documentation for updates."
        )
        return

    table = Table(title="Available Features")
    table.add_column("Feature", style="cyan")
    table.add_column("Description", style="white")

    # Feature descriptions
    descriptions = {
        "auth": "AWS Cognito authentication & user management",
        "admin": "Admin panel for managing models",
        "permissions": "Role-based access control (RBAC)",
        "example_products": "Example CRUD feature for product catalog",
    }

    for feature in features:
        description = descriptions.get(feature, "No description available")
        table.add_row(feature, description)

    console.print(table)
    console.print("\nUsage: [bold]uv run paxx feature add <feature>[/bold]")


def _get_feature_config(source_dir: Path) -> dict[str, str | list[str]]:
    """Extract feature configuration from config.py using AST parsing.

    Args:
        source_dir: Path to the feature source directory.

    Returns:
        Dict with 'prefix' and 'tags' from the feature config.
    """
    config_file = source_dir / "config.py"
    if not config_file.exists():
        return {"prefix": "", "tags": []}

    content = config_file.read_text()
    tree = ast.parse(content)

    prefix = ""
    tags: list[str] = []

    # Find the dataclass and extract default values
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.AnnAssign):
                continue
            if not isinstance(item.target, ast.Name):
                continue
            if item.target.id == "prefix" and isinstance(item.value, ast.Constant):
                if isinstance(item.value.value, str):
                    prefix = item.value.value
            elif item.target.id == "tags" and isinstance(item.value, ast.Call):
                # Handle field(default_factory=lambda: ["tag"])
                for kw in item.value.keywords:
                    if (
                        kw.arg == "default_factory"
                        and isinstance(kw.value, ast.Lambda)
                        and isinstance(kw.value.body, ast.List)
                    ):
                        tags = [
                            elt.value
                            for elt in kw.value.body.elts
                            if isinstance(elt, ast.Constant)
                            and isinstance(elt.value, str)
                        ]

    return {"prefix": prefix, "tags": tags}


def _register_router_in_main(feature_name: str, prefix: str, tags: list[str]) -> bool:
    """Add router import and registration to main.py.

    Args:
        feature_name: Name of the feature (e.g., 'example_products').
        prefix: URL prefix for the router (e.g., '/products').
        tags: OpenAPI tags for the router.

    Returns:
        True if successful, False otherwise.
    """
    main_py = Path.cwd() / "main.py"
    if not main_py.exists():
        return False

    content = main_py.read_text()

    # Create the import alias from feature name
    # e.g., example_products -> example_products_router
    router_alias = f"{feature_name}_router"

    # Check if already registered
    if f"features.{feature_name}.routes" in content:
        console.print("  [yellow]Router already registered in main.py[/yellow]")
        return True

    # Build the import line
    import_line = f"from features.{feature_name}.routes import router as {router_alias}"

    # Build the include_router line
    tags_str = str(tags)
    include_line = (
        f'    app.include_router({router_alias}, prefix="{prefix}", tags={tags_str})'
    )

    # Find where to insert the import (after existing imports)
    lines = content.split("\n")
    new_lines = []
    import_inserted = False
    include_inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Insert import after the last 'from' import (before non-import code)
        if not import_inserted:
            is_import_line = line.strip().startswith(("from ", "import "))
            has_next_line = i + 1 < len(lines)
            next_is_not_import = (
                has_next_line
                and not lines[i + 1].strip().startswith(("from ", "import "))
            )

            if is_import_line and next_is_not_import:
                new_lines.append(import_line)
                import_inserted = True

        # Insert include_router before 'return app' in create_app
        if not include_inserted and line.strip() == "return app":
            # Insert the include_router line before return feature
            new_lines.insert(-1, include_line)
            new_lines.insert(-1, "")
            include_inserted = True

    if not import_inserted or not include_inserted:
        return False

    main_py.write_text("\n".join(new_lines))
    return True


def _copy_feature(feature_name: str, source_dir: Path, target_dir: Path) -> None:
    """Copy a bundled feature to the project features directory.

    Args:
        feature_name: Name of the feature being copied.
        source_dir: Source directory (bundled feature).
        target_dir: Target directory (in features/).
    """
    files_copied = []
    e2e_dir = source_dir / "e2e"
    project_e2e_dir = Path.cwd() / "e2e"

    for item in source_dir.iterdir():
        # Skip __pycache__ directories
        if item.name == "__pycache__":
            continue

        # Skip e2e directory - will be copied to project root separately
        if item.name == "e2e":
            continue

        target_path = target_dir / item.name

        if item.is_file():
            shutil.copy2(item, target_path)
            files_copied.append(item.name)
        elif item.is_dir():
            # Recursively copy subdirectories
            shutil.copytree(
                item, target_path, ignore=shutil.ignore_patterns("__pycache__")
            )
            files_copied.append(f"{item.name}/")

    # Display copied files
    for file_name in sorted(files_copied):
        console.print(f"  [green]Created[/green] features/{feature_name}/{file_name}")

    # Copy e2e tests to project root /e2e directory
    if e2e_dir.exists() and e2e_dir.is_dir():
        project_e2e_dir.mkdir(parents=True, exist_ok=True)
        for item in e2e_dir.iterdir():
            if item.name == "__pycache__":
                continue
            if item.is_file():
                target_path = project_e2e_dir / item.name
                shutil.copy2(item, target_path)
                console.print(f"  [green]Created[/green] e2e/{item.name}")


@app.command("list")
def list_features() -> None:
    """List all available bundled features.

    Shows a table of features that can be added to your project using
    `paxx feature add <feature>`.

    Examples:
        paxx feature list
    """
    _list_features()


@app.command("add")
def add(
    feature: str = typer.Argument(
        None,
        help="Name of the feature to add (e.g., auth, admin, permissions)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing feature if it exists",
    ),
) -> None:
    """Add a paxx bundled feature to your project.

    Features are pre-built templates that get copied into your features/
    directory. Once added, you own the code and can customize it freely.

    Examples:
        paxx feature add auth          # Add authentication system
        paxx feature add auth --force  # Overwrite existing auth feature
    """
    # If no feature specified, show available features
    if feature is None:
        console.print(
            "[bright_red]Error:[/bright_red] "
            "Please specify a feature to add.\n"
        )
        _list_features()
        raise typer.Exit(1)

    # Validate we're in a project
    ctx = check_project_context()

    # Check if feature exists in bundled features
    available = list_available_features()
    source_dir = get_feature_dir(feature)

    if source_dir is None:
        console.print(f"[bright_red]Error: Unknown feature '{feature}'.[/bright_red]\n")
        if available:
            console.print("Available features:")
            for f in available:
                console.print(f"  - {f}")
        else:
            console.print("[yellow]No features are available yet.[/yellow]")
        raise typer.Exit(1)

    # Check if feature already exists in project
    target_dir = ctx.features_dir / feature

    if target_dir.exists():
        if force:
            console.print(
                f"[yellow]Warning:[/yellow] Overwriting existing feature '{feature}'"
            )
            shutil.rmtree(target_dir)
        else:
            console.print(
                f"[bright_red]Error:[/bright_red] Feature '{feature}' already exists.\n"
                "Use --force to overwrite."
            )
            raise typer.Exit(1)

    console.print(f"Adding feature: [bold cyan]{feature}[/bold cyan]")

    # Get feature configuration for router registration
    feature_config = _get_feature_config(source_dir)
    default_prefix = f"/{feature.replace('_', '-')}"
    prefix_value = feature_config.get("prefix", default_prefix)
    prefix = prefix_value if isinstance(prefix_value, str) else default_prefix
    tags_value = feature_config.get("tags", [feature.replace("_", " ")])
    tags = tags_value if isinstance(tags_value, list) else [str(tags_value)]

    # Create target directory and copy files
    try:
        target_dir.mkdir(parents=True)
        _copy_feature(feature, source_dir, target_dir)

        # Register router in main.py
        if _register_router_in_main(feature, prefix, tags):
            console.print("  [green]Updated[/green] main.py")
        else:
            console.print(
                "  [yellow]Could not auto-register router in main.py[/yellow]"
            )
            console.print(
                f"  Add manually: app.include_router({feature}_router, "
                f'prefix="{prefix}", tags={tags})'
            )

        # Run setup script if it exists
        setup_script = target_dir / "setup.py"
        if setup_script.exists():
            console.print()
            console.print("[bold]Running setup script...[/bold]")
            result = subprocess.run(
                ["python", str(setup_script)],
                cwd=Path.cwd(),
            )
            if result.returncode != 0:
                console.print("[bright_red]Setup script failed[/bright_red]")
                raise typer.Exit(1)

        console.print()
        console.print("[bold green]Feature added successfully![/bold green]")
        console.print()
        console.print("Next steps:")
        console.print(f"  1. Review the code in features/{feature}/")
        console.print("  2. Customize as needed for your project")
        console.print("  3. Create and apply migrations:")
        console.print(f'     uv run paxx db migrate "add {feature}"')
        console.print("     uv run paxx db upgrade")

    except Exception as e:
        console.print(f"[bright_red]Error adding feature: {e}[/bright_red]")
        # Clean up on failure
        if target_dir.exists():
            shutil.rmtree(target_dir)
        raise typer.Exit(1) from None


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Name of the new feature"),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Feature description",
    ),
) -> None:
    """Create a new domain feature within the current paxx project.

    This command scaffolds a new feature in the features/ directory with the
    standard paxx feature structure: models, schemas, services, and routes.

    Examples:
        paxx feature create users
        paxx feature create blog_posts
        paxx feature create orders --description "Order management"
    """
    # Validate we're in a project
    ctx = check_project_context()

    # Validate and normalize feature name
    validate_name(name, entity_type="Feature")
    feature_name = to_snake_case(name)

    # Check if feature already exists
    feature_dir = ctx.features_dir / feature_name

    if feature_dir.exists():
        console.print(
            f"[bright_red]Error: Feature '{feature_name}' already exists[/bright_red]"
        )
        raise typer.Exit(1)

    console.print(f"Creating new feature: [bold cyan]{feature_name}[/bold cyan]")

    # Set up Jinja environment
    env = create_jinja_env()

    # Template context
    context = {
        "feature_name": feature_name,
        "feature_description": description,
    }

    # Define feature files with templates
    feature_files: dict[str, str] = {
        "__init__.py": "features/feature_blueprint/__init__.py.jinja",
        "config.py": "features/feature_blueprint/config.py.jinja",
        "models.py": "features/feature_blueprint/models.py.jinja",
        "schemas.py": "features/feature_blueprint/schemas.py.jinja",
        "services.py": "features/feature_blueprint/services.py.jinja",
        "routes.py": "features/feature_blueprint/routes.py.jinja",
    }

    # Create feature directory and files
    try:
        feature_dir.mkdir(parents=True)

        for file_name, template_name in feature_files.items():
            file_path = feature_dir / file_name
            template = env.get_template(template_name)
            content = template.render(**context)
            file_path.write_text(content)
            console.print(
                f"  [green]Created[/green] features/{feature_name}/{file_name}"
            )

        console.print()
        console.print("[bold green]Feature created successfully![/bold green]")
        console.print()
        console.print("Next steps:")
        console.print(f"  1. Define your models in features/{feature_name}/models.py")
        console.print(f"  2. Create schemas in features/{feature_name}/schemas.py")
        console.print(
            f"  3. Implement business logic in features/{feature_name}/services.py"
        )
        console.print(f"  4. Add routes in features/{feature_name}/routes.py")
        console.print()
        console.print("Then create and apply migrations:")
        console.print(f'  uv run paxx db migrate "add {feature_name} models"')
        console.print("  uv run paxx db upgrade")

    except Exception as e:
        console.print(f"[bright_red]Error creating feature: {e}[/bright_red]")
        raise typer.Exit(1) from None
