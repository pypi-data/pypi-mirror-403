"""Tests for the settings template.

These tests verify that the generated settings.py template:
1. Renders correctly with Jinja2
2. Produces valid Python code that works with pydantic-settings
3. Handles environment variables and .env files correctly
"""

from pathlib import Path
from textwrap import dedent

import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def template_env():
    """Jinja2 environment for templates."""
    template_dir = (
        Path(__file__).parent.parent.parent / "src" / "paxx" / "templates" / "project"
    )
    return Environment(loader=FileSystemLoader(str(template_dir)))


@pytest.fixture
def rendered_settings(template_env):
    """Render the settings template with test values."""
    template = template_env.get_template("settings.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_env_example(template_env):
    """Render the .env.example template with test values."""
    template = template_env.get_template(".env.example.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


class TestSettingsTemplateRendering:
    """Tests for template rendering."""

    def test_settings_template_renders(self, rendered_settings):
        """Settings template should render without errors."""
        assert "class Settings" in rendered_settings
        assert "pydantic_settings" in rendered_settings

    def test_settings_includes_project_name(self, rendered_settings):
        """Rendered settings should include the project name."""
        assert 'app_name: str = "TestProject"' in rendered_settings

    def test_settings_includes_database_url(self, rendered_settings):
        """Rendered settings should include the database URL with project name."""
        assert "localhost:5432/test_project" in rendered_settings

    def test_env_example_renders(self, rendered_env_example):
        """Env example template should render without errors."""
        assert "APP_NAME=TestProject" in rendered_env_example
        assert "localhost:5432/test_project" in rendered_env_example


class TestSettingsTemplateValidity:
    """Tests that the rendered template produces valid, working Python code."""

    def test_rendered_settings_is_valid_python(self, rendered_settings, tmp_path):
        """Rendered settings should be valid Python syntax."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        # This will raise SyntaxError if the code is invalid
        compile(rendered_settings, str(settings_file), "exec")

    def test_settings_module_can_be_imported(
        self, rendered_settings, tmp_path, monkeypatch
    ):
        """Rendered settings module should be importable."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        # Add tmp_path to sys.path temporarily
        monkeypatch.syspath_prepend(str(tmp_path))

        # Import the module
        import importlib.util

        spec = importlib.util.spec_from_file_location("settings", settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify the Settings class exists and is a BaseSettings subclass
        assert hasattr(module, "Settings")
        assert hasattr(module, "get_settings")
        assert hasattr(module, "settings")

    def test_settings_instance_works(self, rendered_settings, tmp_path, monkeypatch):
        """Settings instance should be creatable with defaults."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("settings", settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get settings instance
        settings = module.get_settings()

        # Check default values
        assert settings.app_name == "TestProject"
        assert settings.debug is False
        assert settings.environment == "development"
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000

    def test_settings_respects_environment_variables(
        self, rendered_settings, tmp_path, monkeypatch
    ):
        """Settings should load values from environment variables."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        # Set environment variables
        monkeypatch.setenv("APP_NAME", "OverriddenFeature")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("PORT", "9000")

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("settings_env", settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Create a new settings instance (bypass cache)
        settings = module.Settings()

        assert settings.app_name == "OverriddenFeature"
        assert settings.debug is True
        assert settings.port == 9000

    def test_settings_loads_from_env_file(
        self, rendered_settings, tmp_path, monkeypatch
    ):
        """Settings should load values from .env file."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        # Create a .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            dedent("""
            APP_NAME=FromEnvFile
            DEBUG=true
            PORT=8888
        """).strip()
        )

        # Change to tmp_path so .env file is found
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("settings_dotenv", settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Create new settings instance
        settings = module.Settings()

        assert settings.app_name == "FromEnvFile"
        assert settings.debug is True
        assert settings.port == 8888

    def test_settings_properties(self, rendered_settings, tmp_path, monkeypatch):
        """Settings properties should work correctly."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(rendered_settings)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("settings_props", settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Test development environment
        settings_dev = module.Settings(environment="development")
        assert settings_dev.is_development is True
        assert settings_dev.is_production is False

        # Test production environment (must provide valid secret_key >= 32 chars)
        settings_prod = module.Settings(
            environment="production",
            secret_key="a-valid-production-secret-key-that-is-long-enough",
        )
        assert settings_prod.is_development is False
        assert settings_prod.is_production is True


class TestPyprojectTemplate:
    """Tests for the pyproject.toml template."""

    def test_pyproject_template_renders(self, template_env):
        """Pyproject template should render without errors."""
        template = template_env.get_template("pyproject.toml.jinja")
        rendered = template.render(
            project_name="Test Project",
            project_name_snake="test_project",
        )

        assert "[project]" in rendered
        assert 'name = "test_project"' in rendered
        assert "pydantic-settings" in rendered
        assert "fastapi" in rendered
