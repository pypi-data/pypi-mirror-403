"""Tests for the paxx CLI commands (bootstrap, startfeature, add, start)."""

import os
import shutil

import pytest
from typer.testing import CliRunner

from paxx.cli.main import app
from paxx.templates.features import get_features_dir

runner = CliRunner()


class TestBootstrapCommand:
    """Tests for the `paxx bootstrap` command."""

    def test_bootstrap_help(self):
        """Test that `paxx bootstrap --help` shows help text."""
        result = runner.invoke(app, ["bootstrap", "--help"])
        assert result.exit_code == 0
        assert "Scaffold a new FastAPI project" in result.stdout

    def test_bootstrap_creates_project(self, tmp_path):
        """Test that `paxx bootstrap` creates a project with correct structure."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["bootstrap", "myproject"])

        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout

        # Check project structure
        project_dir = tmp_path / "myproject"
        assert project_dir.exists()
        assert (project_dir / "main.py").exists()
        assert (project_dir / "settings.py").exists()
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "alembic.ini").exists()
        assert (project_dir / ".env").exists()
        assert (project_dir / ".env.example").exists()
        assert (project_dir / "README.md").exists()
        assert (project_dir / ".gitignore").exists()

        # Check directories
        assert (project_dir / "core").is_dir()
        assert (project_dir / "core" / "exceptions.py").exists()
        assert (project_dir / "core" / "middleware.py").exists()
        assert (project_dir / "core" / "dependencies.py").exists()
        assert (project_dir / "core" / "schemas.py").exists()

        assert (project_dir / "db").is_dir()
        assert (project_dir / "db" / "database.py").exists()
        assert (project_dir / "db" / "migrations").is_dir()
        assert (project_dir / "db" / "migrations" / "env.py").exists()
        assert (project_dir / "db" / "migrations" / "versions").is_dir()

        assert (project_dir / "features").is_dir()

    def test_bootstrap_with_options(self, tmp_path):
        """Test `paxx bootstrap` with custom options."""
        os.chdir(tmp_path)
        result = runner.invoke(
            app,
            [
                "bootstrap",
                "testapi",
                "--description",
                "My test API",
                "--author",
                "Test Author",
            ],
        )

        assert result.exit_code == 0

        # Check pyproject.toml contains the options
        pyproject = (tmp_path / "testapi" / "pyproject.toml").read_text()
        assert "My test API" in pyproject
        assert "Test Author" in pyproject

    def test_bootstrap_fails_if_directory_exists(self, tmp_path):
        """Test that `paxx bootstrap` fails if project directory already exists."""
        os.chdir(tmp_path)
        (tmp_path / "existing").mkdir()

        result = runner.invoke(app, ["bootstrap", "existing"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_bootstrap_with_hyphenated_name(self, tmp_path):
        """Test `paxx bootstrap` with hyphenated project name."""
        os.chdir(tmp_path)
        result = runner.invoke(app, ["bootstrap", "my-api"])

        assert result.exit_code == 0
        assert (tmp_path / "my-api").exists()

        # Check snake_case is used in Python files
        settings = (tmp_path / "my-api" / "settings.py").read_text()
        assert "my_api" in settings

    def test_bootstrap_validates_name(self, tmp_path):
        """Test that `paxx bootstrap` validates project name."""
        os.chdir(tmp_path)

        # Name starting with number should fail
        result = runner.invoke(app, ["bootstrap", "123project"])
        assert result.exit_code != 0

    def test_bootstrap_output_dir_option(self, tmp_path):
        """Test `paxx bootstrap` with --output-dir option."""
        output_dir = tmp_path / "projects"
        output_dir.mkdir()

        result = runner.invoke(app, ["bootstrap", "myproject", "-o", str(output_dir)])

        assert result.exit_code == 0
        assert (output_dir / "myproject").exists()


class TestFeatureCreateCommand:
    """Tests for the `paxx feature create` command."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a minimal project structure for testing feature create."""
        os.chdir(tmp_path)
        runner.invoke(app, ["bootstrap", "testproject"])
        project = tmp_path / "testproject"
        os.chdir(project)
        return project

    def test_feature_create_help(self):
        """Test that `paxx feature create --help` shows help text."""
        result = runner.invoke(app, ["feature", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new domain feature" in result.stdout

    def test_feature_create_creates_feature(self, project_dir):
        """Test that `paxx feature create` creates a feature with correct structure."""
        result = runner.invoke(app, ["feature", "create", "users"])

        assert result.exit_code == 0
        assert "Feature created successfully" in result.stdout

        # Check feature structure
        feature_dir = project_dir / "features" / "users"
        assert feature_dir.exists()
        assert (feature_dir / "__init__.py").exists()
        assert (feature_dir / "config.py").exists()
        assert (feature_dir / "models.py").exists()
        assert (feature_dir / "schemas.py").exists()
        assert (feature_dir / "services.py").exists()
        assert (feature_dir / "routes.py").exists()

    def test_feature_create_with_description(self, project_dir):
        """Test `paxx feature create` with description option."""
        result = runner.invoke(
            app,
            ["feature", "create", "orders", "--description", "Order management"],
        )

        assert result.exit_code == 0

        config = (project_dir / "features" / "orders" / "config.py").read_text()
        assert "Order management" in config

    def test_feature_create_fails_if_feature_exists(self, project_dir):
        """Test that `paxx feature create` fails if feature already exists."""
        runner.invoke(app, ["feature", "create", "users"])

        result = runner.invoke(app, ["feature", "create", "users"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_feature_create_fails_outside_project(self, tmp_path):
        """Test that `paxx feature create` fails outside a project directory."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["feature", "create", "users"])
        assert result.exit_code == 1
        assert "Not in a paxx project" in result.stdout

    def test_feature_create_with_hyphenated_name(self, project_dir):
        """Test `paxx feature create` converts hyphenated names to snake_case."""
        result = runner.invoke(app, ["feature", "create", "user-profiles"])

        assert result.exit_code == 0

        # Should be converted to snake_case
        assert (project_dir / "features" / "user_profiles").exists()


class TestFeatureAddCommand:
    """Tests for the `paxx feature add` command."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a minimal project structure for testing feature add."""
        os.chdir(tmp_path)
        runner.invoke(app, ["bootstrap", "testproject"])
        project = tmp_path / "testproject"
        os.chdir(project)
        return project

    @pytest.fixture
    def mock_feature(self, tmp_path):
        """Create a mock feature in the bundled features directory."""
        features_dir = get_features_dir()
        feature_dir = features_dir / "testfeature"
        feature_dir.mkdir(exist_ok=True)

        # Create mock feature files
        (feature_dir / "__init__.py").write_text('"""Test feature."""\n')
        (feature_dir / "models.py").write_text("# Test models\n")
        (feature_dir / "routes.py").write_text("# Test routes\n")

        yield feature_dir

        # Cleanup
        shutil.rmtree(feature_dir)

    def test_feature_add_help(self):
        """Test that `paxx feature add --help` shows help text."""
        result = runner.invoke(app, ["feature", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a paxx bundled feature" in result.stdout

    def test_feature_add_list_shows_available_features(self):
        """Test that `paxx feature list` shows available features."""
        result = runner.invoke(app, ["feature", "list"])
        assert result.exit_code == 0
        # Should show some message about features (even if none available)
        assert "feature" in result.stdout.lower()

    def test_feature_add_fails_outside_project(self, tmp_path):
        """Test that `paxx feature add` fails outside a project directory."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["feature", "add", "auth"])
        assert result.exit_code == 1
        assert "Not in a paxx project" in result.stdout

    def test_feature_add_fails_for_unknown_feature(self, project_dir):
        """Test that `paxx feature add` fails for unknown feature."""
        result = runner.invoke(app, ["feature", "add", "nonexistent"])
        assert result.exit_code == 1
        assert "Unknown feature" in result.stdout

    def test_feature_add_copies_feature_files(self, project_dir, mock_feature):
        """Test that `paxx feature add` copies feature files to features directory."""
        result = runner.invoke(app, ["feature", "add", "testfeature"])

        assert result.exit_code == 0
        assert "Feature added successfully" in result.stdout

        # Check that files were copied
        feature_dir = project_dir / "features" / "testfeature"
        assert feature_dir.exists()
        assert (feature_dir / "__init__.py").exists()
        assert (feature_dir / "models.py").exists()
        assert (feature_dir / "routes.py").exists()

    def test_feature_add_fails_if_feature_exists(self, project_dir, mock_feature):
        """Test that `paxx feature add` fails if feature already exists."""
        # Add feature first
        runner.invoke(app, ["feature", "add", "testfeature"])

        # Try to add again
        result = runner.invoke(app, ["feature", "add", "testfeature"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_feature_add_force_overwrites_existing(self, project_dir, mock_feature):
        """Test that `paxx feature add --force` overwrites existing feature."""
        # Add feature first
        runner.invoke(app, ["feature", "add", "testfeature"])

        # Modify a file
        modified_file = project_dir / "features" / "testfeature" / "models.py"
        modified_file.write_text("# Modified\n")

        # Add again with --force
        result = runner.invoke(app, ["feature", "add", "testfeature", "--force"])
        assert result.exit_code == 0
        assert "Overwriting" in result.stdout

        # Check file was reset
        assert modified_file.read_text() == "# Test models\n"

    def test_feature_add_requires_feature_name(self):
        """Test that `paxx feature add` requires a feature name."""
        result = runner.invoke(app, ["feature", "add"])
        assert result.exit_code == 2
        assert "Missing argument 'FEATURE'" in result.output


class TestStartCommand:
    """Tests for the `paxx start` command."""

    def test_start_help(self):
        """Test that `paxx start --help` shows help text."""
        result = runner.invoke(app, ["start", "--help"])
        assert result.exit_code == 0
        assert "Start the development server" in result.stdout
        assert "--port" in result.stdout
        assert "--host" in result.stdout
        assert "--reload" in result.stdout

    def test_start_fails_outside_project(self, tmp_path):
        """Test that `paxx start` fails outside a project directory."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["start"])
        assert result.exit_code == 1
        assert "Not in a paxx project" in result.stdout


class TestDockerCommand:
    """Tests for the `paxx docker` commands."""

    def test_docker_help(self):
        """Test that `paxx docker --help` shows help text."""
        result = runner.invoke(app, ["docker", "--help"])
        assert result.exit_code == 0
        assert "Docker development commands" in result.stdout
        assert "up" in result.stdout
        assert "down" in result.stdout
        assert "build" in result.stdout
        assert "logs" in result.stdout

    def test_docker_up_help(self):
        """Test that `paxx docker up --help` shows help text."""
        result = runner.invoke(app, ["docker", "up", "--help"])
        assert result.exit_code == 0
        assert "Start the development environment" in result.stdout
        assert "--detach" in result.stdout
        assert "--build" in result.stdout

    def test_docker_down_help(self):
        """Test that `paxx docker down --help` shows help text."""
        result = runner.invoke(app, ["docker", "down", "--help"])
        assert result.exit_code == 0
        assert "Stop the development environment" in result.stdout
        assert "--volumes" in result.stdout

    def test_docker_build_help(self):
        """Test that `paxx docker build --help` shows help text."""
        result = runner.invoke(app, ["docker", "build", "--help"])
        assert result.exit_code == 0
        assert "Build the Docker images" in result.stdout
        assert "--no-cache" in result.stdout

    def test_docker_logs_help(self):
        """Test that `paxx docker logs --help` shows help text."""
        result = runner.invoke(app, ["docker", "logs", "--help"])
        assert result.exit_code == 0
        assert "Show container logs" in result.stdout
        assert "--follow" in result.stdout

    def test_docker_ps_help(self):
        """Test that `paxx docker ps --help` shows help text."""
        result = runner.invoke(app, ["docker", "ps", "--help"])
        assert result.exit_code == 0
        assert "Show running containers" in result.stdout

    def test_docker_exec_help(self):
        """Test that `paxx docker exec --help` shows help text."""
        result = runner.invoke(app, ["docker", "exec", "--help"])
        assert result.exit_code == 0
        assert "Execute a command in a running container" in result.stdout

    def test_docker_up_fails_without_compose_file(self, tmp_path):
        """Test that `paxx docker up` fails without docker-compose.yml."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["docker", "up"])
        assert result.exit_code == 1
        assert "docker-compose.yml not found" in result.stdout

    def test_docker_down_fails_without_compose_file(self, tmp_path):
        """Test that `paxx docker down` fails without docker-compose.yml."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["docker", "down"])
        assert result.exit_code == 1
        assert "docker-compose.yml not found" in result.stdout

    def test_docker_build_fails_without_compose_file(self, tmp_path):
        """Test that `paxx docker build` fails without docker-compose.yml."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["docker", "build"])
        assert result.exit_code == 1
        assert "docker-compose.yml not found" in result.stdout

    def test_docker_logs_fails_without_compose_file(self, tmp_path):
        """Test that `paxx docker logs` fails without docker-compose.yml."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["docker", "logs"])
        assert result.exit_code == 1
        assert "docker-compose.yml not found" in result.stdout

    def test_docker_ps_fails_without_compose_file(self, tmp_path):
        """Test that `paxx docker ps` fails without docker-compose.yml."""
        os.chdir(tmp_path)

        result = runner.invoke(app, ["docker", "ps"])
        assert result.exit_code == 1
        assert "docker-compose.yml not found" in result.stdout


