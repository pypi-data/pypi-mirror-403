"""Tests for the database template.

These tests verify that the generated db/database.py template:
1. Renders correctly with Jinja2
2. Produces valid Python code that works with SQLAlchemy async
3. Properly defines BaseModel with id and timestamps
"""

import ast
from pathlib import Path

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
def rendered_database(template_env):
    """Render the database template with test values."""
    template = template_env.get_template("db/database.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_alembic_env(template_env):
    """Render the alembic env.py template with test values."""
    template = template_env.get_template("db/migrations/env.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_alembic_ini(template_env):
    """Render the alembic.ini template with test values."""
    template = template_env.get_template("alembic.ini.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


class TestDatabaseTemplateRendering:
    """Tests for database template rendering."""

    def test_database_template_renders(self, rendered_database):
        """Database template should render without errors."""
        assert "class Base" in rendered_database
        assert "class BaseModel" in rendered_database
        assert "async_sessionmaker" in rendered_database

    def test_database_includes_engine(self, rendered_database):
        """Rendered database should include async engine setup."""
        assert "create_async_engine" in rendered_database
        assert "settings.database_url" in rendered_database

    def test_database_includes_session_factory(self, rendered_database):
        """Rendered database should include session factory."""
        assert "async_session_factory" in rendered_database
        assert "AsyncSession" in rendered_database

    def test_database_includes_base_model(self, rendered_database):
        """Rendered database should include BaseModel with timestamps."""
        assert "class BaseModel" in rendered_database
        assert "created_at" in rendered_database
        assert "updated_at" in rendered_database
        assert "id: Mapped[UUIDPK]" in rendered_database

    def test_database_includes_get_db_dependency(self, rendered_database):
        """Rendered database should include FastAPI dependency."""
        assert "async def get_db()" in rendered_database
        assert "AsyncGenerator" in rendered_database

    def test_database_includes_naming_convention(self, rendered_database):
        """Rendered database should include naming convention for constraints."""
        assert "NAMING_CONVENTION" in rendered_database
        assert "ix_" in rendered_database
        assert "uq_" in rendered_database
        assert "fk_" in rendered_database


class TestDatabaseTemplateValidity:
    """Tests that the rendered template produces valid, working Python code."""

    def test_rendered_database_is_valid_python(self, rendered_database, tmp_path):
        """Rendered database should be valid Python syntax."""
        database_file = tmp_path / "database.py"
        database_file.write_text(rendered_database)

        # This will raise SyntaxError if the code is invalid
        compile(rendered_database, str(database_file), "exec")

    def test_rendered_database_has_valid_ast(self, rendered_database):
        """Rendered database should have a valid AST structure."""
        tree = ast.parse(rendered_database)

        # Find all class definitions
        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

        assert "Base" in classes
        assert "BaseModel" in classes
        assert "TimestampMixin" in classes

    def test_rendered_database_has_required_functions(self, rendered_database):
        """Rendered database should define required functions."""
        tree = ast.parse(rendered_database)

        # Find all function definitions
        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]

        assert "get_db" in functions
        assert "init_db" in functions
        assert "close_db" in functions


class TestAlembicTemplateRendering:
    """Tests for Alembic template rendering."""

    def test_alembic_env_template_renders(self, rendered_alembic_env):
        """Alembic env.py template should render without errors."""
        assert "import asyncio" in rendered_alembic_env
        assert "async_engine_from_config" in rendered_alembic_env

    def test_alembic_env_has_model_discovery(self, rendered_alembic_env):
        """Alembic env.py should auto-discover models from features."""
        assert "features_dir" in rendered_alembic_env
        assert "importlib.import_module" in rendered_alembic_env
        assert "models.py" in rendered_alembic_env

    def test_alembic_env_has_async_migrations(self, rendered_alembic_env):
        """Alembic env.py should support async migrations."""
        assert "async def run_async_migrations" in rendered_alembic_env
        assert "asyncio.run" in rendered_alembic_env

    def test_alembic_env_is_valid_python(self, rendered_alembic_env, tmp_path):
        """Rendered alembic env.py should be valid Python syntax."""
        env_file = tmp_path / "env.py"
        env_file.write_text(rendered_alembic_env)

        # This will raise SyntaxError if the code is invalid
        compile(rendered_alembic_env, str(env_file), "exec")

    def test_alembic_ini_template_renders(self, rendered_alembic_ini):
        """Alembic.ini template should render without errors."""
        assert "[alembic]" in rendered_alembic_ini
        assert "script_location = db/migrations" in rendered_alembic_ini
        # Project name should appear in the PostgreSQL connection URL
        assert "postgresql+asyncpg://" in rendered_alembic_ini
        assert "test_project" in rendered_alembic_ini


class TestDatabaseModuleImportability:
    """Integration tests for rendered database module."""

    def test_database_module_structure(self, rendered_database, tmp_path, monkeypatch):
        """Database module should have the expected structure when imported."""
        # Create a mock settings module
        settings_content = """
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./test.db"
    debug: bool = False

settings = Settings()
"""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(settings_content)

        # Create the database module
        database_file = tmp_path / "database.py"
        database_file.write_text(rendered_database)

        # Add tmp_path to sys.path
        monkeypatch.syspath_prepend(str(tmp_path))

        # Import and validate structure
        import importlib.util

        spec = importlib.util.spec_from_file_location("database", database_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "Base")
        assert hasattr(module, "BaseModel")
        assert hasattr(module, "TimestampMixin")
        assert hasattr(module, "get_db")
        assert hasattr(module, "init_db")
        assert hasattr(module, "close_db")
        assert hasattr(module, "engine")
        assert hasattr(module, "async_session_factory")
        assert hasattr(module, "UUIDPK")
