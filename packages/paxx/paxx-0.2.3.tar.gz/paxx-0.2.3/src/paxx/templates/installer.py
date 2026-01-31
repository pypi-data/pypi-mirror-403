"""Helper utilities for template installation."""

import ast
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

console = Console()


class TemplateInstaller:
    """Helper class for installing templates (infra, ext, etc).

    Provides common utilities for copying templates, merging docker services,
    adding dependencies, and modifying project files.
    """

    def __init__(self, project_path: Path | None = None):
        """Initialize the installer.

        Args:
            project_path: Path to the project root. Defaults to current directory.
        """
        self.project_path = project_path or Path.cwd()

    def copy_templates(self, templates_dir: Path, dest: Path) -> None:
        """Copy and render Jinja2 templates to destination.

        Args:
            templates_dir: Path to the templates directory.
            dest: Destination directory for rendered files.
        """
        if not templates_dir.exists():
            return

        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        dest.mkdir(exist_ok=True)

        for template_file in templates_dir.glob("*.jinja"):
            template = env.get_template(template_file.name)
            output_name = template_file.stem  # Remove .jinja extension
            output_path = dest / output_name
            output_path.write_text(template.render())
            console.print(f"  [green]Created[/green] {output_path}")

    def merge_docker_service(self, service_file: Path) -> None:
        """Add service definition to docker-compose.yml.

        Args:
            service_file: Path to the service YAML file to merge.
        """
        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        compose_path = self.project_path / "docker-compose.yml"
        if not compose_path.exists():
            console.print("  [yellow]Warning:[/yellow] docker-compose.yml not found")
            return

        if not service_file.exists():
            return

        with open(compose_path) as f:
            compose = yaml.load(f)

        with open(service_file) as f:
            new_service = yaml.load(f)

        # Skip if file is empty or has no content
        if not new_service:
            return

        service_name = list(new_service.keys())[0]

        # Check if already added
        if service_name in compose.get("services", {}):
            console.print(
                f"  [yellow]Service '{service_name}' already exists "
                "in docker-compose.yml[/yellow]"
            )
            return

        compose["services"][service_name] = new_service[service_name]

        # Add volume if service uses one
        service_config = new_service[service_name]
        if "volumes" in service_config:
            if "volumes" not in compose:
                compose["volumes"] = {}
            for vol in service_config["volumes"]:
                if ":" in vol:
                    vol_name = vol.split(":")[0]
                    if vol_name not in compose["volumes"]:
                        compose["volumes"][vol_name] = None

        with open(compose_path, "w") as f:
            yaml.dump(compose, f)

        console.print("  [green]Updated[/green] docker-compose.yml")

    def add_dependencies(self, deps_file: Path) -> None:
        """Add dependencies to pyproject.toml.

        Args:
            deps_file: Path to the dependencies.txt file.
        """
        import tomlkit

        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            console.print("  [yellow]Warning:[/yellow] pyproject.toml not found")
            return

        if not deps_file.exists():
            return

        with open(pyproject_path) as f:
            pyproject = tomlkit.load(f)

        raw_deps = deps_file.read_text().strip().split("\n")
        deps = [d.strip() for d in raw_deps if d.strip()]
        current = list(pyproject.get("project", {}).get("dependencies", []))

        added = []
        for dep in deps:
            # Check if dependency already exists (by package name)
            dep_name = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
            existing_names = [
                d.split(">=")[0].split("==")[0].split("<")[0].strip() for d in current
            ]
            if dep_name not in existing_names:
                pyproject["project"]["dependencies"].append(dep)
                added.append(dep)

        if added:
            with open(pyproject_path, "w") as f:
                tomlkit.dump(pyproject, f)
            console.print("  [green]Updated[/green] pyproject.toml")
        else:
            console.print("  [yellow]Dependencies already in pyproject.toml[/yellow]")

    def add_env_vars(self, env_vars: dict[str, str]) -> None:
        """Add environment variables to settings.py and .env.example.

        Args:
            env_vars: Dict of env var names and default values.
        """
        if not env_vars:
            return

        self._add_env_vars_to_settings(env_vars)
        self._add_env_vars_to_env_example(env_vars)

    def add_env_vars_from_file(self, env_file: Path) -> None:
        """Load environment variables from JSON file and add them.

        Args:
            env_file: Path to the env.json file.
        """
        import json

        if not env_file.exists():
            return

        with open(env_file) as f:
            env_vars = json.load(f)

        self.add_env_vars(env_vars)

    def _add_env_vars_to_settings(self, env_vars: dict[str, str]) -> None:
        """Add environment variables to settings.py using AST.

        Args:
            env_vars: Dict of env var names and default values.
        """
        settings_path = self.project_path / "settings.py"
        if not settings_path.exists():
            console.print("  [yellow]Warning:[/yellow] settings.py not found")
            return

        content = settings_path.read_text()
        tree = ast.parse(content)

        # Find the Settings class
        settings_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Settings":
                settings_class = node
                break

        if not settings_class:
            console.print("  [yellow]Warning:[/yellow] Settings class not found")
            return

        # Get existing field names
        existing_fields = set()
        for item in settings_class.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                existing_fields.add(item.target.id.lower())

        # Build new fields to add
        new_fields = []
        for var_name, default_value in env_vars.items():
            field_name = var_name.lower()
            if field_name not in existing_fields:
                new_fields.append(f'    {field_name}: str = "{default_value}"')

        if not new_fields:
            console.print("  [yellow]Settings already contain these env vars[/yellow]")
            return

        # Find the insertion point (before the first method or at end of class)
        lines = content.split("\n")
        insert_line = None

        # Find the class definition line
        class_start = None
        for i, line in enumerate(lines):
            if "class Settings" in line:
                class_start = i
                break

        if class_start is None:
            return

        # Find first method (@property, @field_validator, def) or end of class
        for i in range(class_start + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("@") or line.startswith("def "):
                insert_line = i
                break
            # Check for end of class (next class definition or end of indented block)
            if line and not line.startswith("#") and not lines[i].startswith(" "):
                insert_line = i
                break

        if insert_line is None:
            insert_line = len(lines)

        # Insert new fields with a comment
        new_content = "\n".join(new_fields)
        comment = "\n    # Infrastructure"
        lines.insert(insert_line, "")
        lines.insert(insert_line, new_content)
        lines.insert(insert_line, comment)

        settings_path.write_text("\n".join(lines))
        console.print("  [green]Updated[/green] settings.py")

    def _add_env_vars_to_env_example(self, env_vars: dict[str, str]) -> None:
        """Add environment variables to .env.example.

        Args:
            env_vars: Dict of env var names and default values.
        """
        env_example_path = self.project_path / ".env.example"
        if not env_example_path.exists():
            console.print("  [yellow]Warning:[/yellow] .env.example not found")
            return

        content = env_example_path.read_text()

        # Check which vars already exist
        new_vars = []
        for var_name, default_value in env_vars.items():
            if f"{var_name}=" not in content:
                new_vars.append(f"{var_name}={default_value}")

        if not new_vars:
            return

        # Append new vars with a section header
        if not content.endswith("\n"):
            content += "\n"

        content += "\n# Infrastructure\n"
        content += "\n".join(new_vars) + "\n"

        env_example_path.write_text(content)
        console.print("  [green]Updated[/green] .env.example")

    def print_success(self, component_name: str) -> None:
        """Print success message after installation.

        Args:
            component_name: Name of the installed component.
        """
        console.print()
        console.print(f"[bold green]Added {component_name} infrastructure[/bold green]")

    def print_next_steps(self) -> None:
        """Print common next steps after installation."""
        console.print()
        console.print("Next steps:")
        console.print("  1. Run: [bold]uv sync[/bold]")
        console.print("  2. Start services: [bold]docker compose up -d[/bold]")
