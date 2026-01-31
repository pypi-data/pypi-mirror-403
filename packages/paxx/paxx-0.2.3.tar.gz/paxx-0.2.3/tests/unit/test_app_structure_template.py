"""Tests for the feature structure templates.

These tests verify that the generated feature templates:
1. Render correctly with Jinja2
2. Produce valid Python code
3. Have the expected structure and components
"""

import ast
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def template_env():
    """Jinja2 environment for templates."""
    template_dir = (
        Path(__file__).parent.parent.parent
        / "src"
        / "paxx"
        / "templates"
        / "features"
        / "feature_blueprint"
    )
    return Environment(loader=FileSystemLoader(str(template_dir)))


@pytest.fixture
def feature_context():
    """Default context for feature templates."""
    return {
        "feature_name": "users",
        "feature_description": "User management functionality",
    }


@pytest.fixture
def rendered_config(template_env, feature_context):
    """Render the config.py template with test values."""
    template = template_env.get_template("config.py.jinja")
    return template.render(**feature_context)


@pytest.fixture
def rendered_models(template_env, feature_context):
    """Render the models.py template with test values."""
    template = template_env.get_template("models.py.jinja")
    return template.render(**feature_context)


@pytest.fixture
def rendered_schemas(template_env, feature_context):
    """Render the schemas.py template with test values."""
    template = template_env.get_template("schemas.py.jinja")
    return template.render(**feature_context)


@pytest.fixture
def rendered_services(template_env, feature_context):
    """Render the services.py template with test values."""
    template = template_env.get_template("services.py.jinja")
    return template.render(**feature_context)


@pytest.fixture
def rendered_routes(template_env, feature_context):
    """Render the routes.py template with test values."""
    template = template_env.get_template("routes.py.jinja")
    return template.render(**feature_context)


@pytest.fixture
def rendered_init(template_env, feature_context):
    """Render the __init__.py template with test values."""
    template = template_env.get_template("__init__.py.jinja")
    return template.render(**feature_context)


class TestConfigTemplateRendering:
    """Tests for config.py template rendering."""

    def test_config_template_renders(self, rendered_config):
        """Config template should render without errors."""
        assert "UsersFeatureConfig" in rendered_config
        assert "feature_config" in rendered_config

    def test_config_includes_dataclass(self, rendered_config):
        """Rendered config.py should use dataclass."""
        assert "@dataclass" in rendered_config
        assert "from dataclasses import dataclass" in rendered_config

    def test_config_includes_expected_fields(self, rendered_config):
        """Rendered config.py should include expected fields."""
        assert 'name: str = "users"' in rendered_config
        assert 'verbose_name: str = "Users"' in rendered_config
        assert 'prefix: str = "/users"' in rendered_config
        assert "tags: list[str]" in rendered_config

    def test_config_creates_instance(self, rendered_config):
        """Rendered config.py should create an instance."""
        assert "feature_config = UsersFeatureConfig()" in rendered_config


class TestConfigTemplateValidity:
    """Tests that the rendered config.py produces valid Python code."""

    def test_rendered_config_is_valid_python(self, rendered_config, tmp_path):
        """Rendered config.py should be valid Python syntax."""
        config_file = tmp_path / "config.py"
        config_file.write_text(rendered_config)

        compile(rendered_config, str(config_file), "exec")

    def test_rendered_config_has_valid_ast(self, rendered_config):
        """Rendered config.py should have a valid AST structure."""
        tree = ast.parse(rendered_config)

        # Find all class definitions
        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]
        assert "UsersFeatureConfig" in classes


class TestModelsTemplateRendering:
    """Tests for models.py template rendering."""

    def test_models_template_renders(self, rendered_models):
        """Models template should render without errors."""
        assert "Users models" in rendered_models
        assert "from db.database import BaseModel" in rendered_models

    def test_models_includes_example(self, rendered_models):
        """Rendered models.py should include example code."""
        assert "class Users(BaseModel):" in rendered_models
        assert '__tablename__ = "users"' in rendered_models


class TestModelsTemplateValidity:
    """Tests that the rendered models.py produces valid Python code."""

    def test_rendered_models_is_valid_python(self, rendered_models, tmp_path):
        """Rendered models.py should be valid Python syntax."""
        models_file = tmp_path / "models.py"
        models_file.write_text(rendered_models)

        compile(rendered_models, str(models_file), "exec")


class TestSchemasTemplateRendering:
    """Tests for schemas.py template rendering."""

    def test_schemas_template_renders(self, rendered_schemas):
        """Schemas template should render without errors."""
        assert "Users schemas" in rendered_schemas
        assert "from pydantic import BaseModel" in rendered_schemas

    def test_schemas_includes_base_schema(self, rendered_schemas):
        """Rendered schemas.py should include base schema."""
        assert "class UsersBase(BaseModel):" in rendered_schemas

    def test_schemas_includes_create_schema(self, rendered_schemas):
        """Rendered schemas.py should include create schema."""
        assert "class UsersCreate(UsersBase):" in rendered_schemas

    def test_schemas_includes_update_schema(self, rendered_schemas):
        """Rendered schemas.py should include update schema."""
        assert "class UsersUpdate(BaseModel):" in rendered_schemas

    def test_schemas_includes_public_schema(self, rendered_schemas):
        """Rendered schemas.py should include public schema."""
        assert "class UsersPublic(UsersBase):" in rendered_schemas
        assert "id: int" in rendered_schemas
        assert "from_attributes=True" in rendered_schemas


class TestSchemasTemplateValidity:
    """Tests that the rendered schemas.py produces valid Python code."""

    def test_rendered_schemas_is_valid_python(self, rendered_schemas, tmp_path):
        """Rendered schemas.py should be valid Python syntax."""
        schemas_file = tmp_path / "schemas.py"
        schemas_file.write_text(rendered_schemas)

        compile(rendered_schemas, str(schemas_file), "exec")

    def test_rendered_schemas_has_valid_ast(self, rendered_schemas):
        """Rendered schemas.py should have expected classes."""
        tree = ast.parse(rendered_schemas)

        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

        assert "UsersBase" in classes
        assert "UsersCreate" in classes
        assert "UsersUpdate" in classes
        assert "UsersPublic" in classes


class TestServicesTemplateRendering:
    """Tests for services.py template rendering."""

    def test_services_template_renders(self, rendered_services):
        """Services template should render without errors."""
        assert "Users business logic" in rendered_services
        assert "from sqlalchemy.ext.asyncio import AsyncSession" in rendered_services

    def test_services_includes_example(self, rendered_services):
        """Rendered services.py should include example code."""
        assert "async def get_users(" in rendered_services
        assert "async def create_users(" in rendered_services


class TestServicesTemplateValidity:
    """Tests that the rendered services.py produces valid Python code."""

    def test_rendered_services_is_valid_python(self, rendered_services, tmp_path):
        """Rendered services.py should be valid Python syntax."""
        services_file = tmp_path / "services.py"
        services_file.write_text(rendered_services)

        compile(rendered_services, str(services_file), "exec")


class TestRoutesTemplateRendering:
    """Tests for routes.py template rendering."""

    def test_routes_template_renders(self, rendered_routes):
        """Routes template should render without errors."""
        assert "Users API routes" in rendered_routes
        assert "from fastapi import APIRouter" in rendered_routes

    def test_routes_creates_router(self, rendered_routes):
        """Rendered routes.py should create a router."""
        assert "router = APIRouter()" in rendered_routes

    def test_routes_includes_example(self, rendered_routes):
        """Rendered routes.py should include example code."""
        assert "async def list_users(" in rendered_routes
        assert "async def get_users(" in rendered_routes
        assert "async def create_users(" in rendered_routes
        assert "async def update_users(" in rendered_routes
        assert "async def delete_users(" in rendered_routes


class TestRoutesTemplateValidity:
    """Tests that the rendered routes.py produces valid Python code."""

    def test_rendered_routes_is_valid_python(self, rendered_routes, tmp_path):
        """Rendered routes.py should be valid Python syntax."""
        routes_file = tmp_path / "routes.py"
        routes_file.write_text(rendered_routes)

        compile(rendered_routes, str(routes_file), "exec")


class TestInitTemplateRendering:
    """Tests for __init__.py template rendering."""

    def test_init_template_renders(self, rendered_init):
        """Init template should render without errors."""
        assert "users feature module" in rendered_init

    def test_init_imports_config(self, rendered_init):
        """Rendered __init__.py should import config."""
        assert "from users.config import UsersFeatureConfig" in rendered_init
        assert "UsersFeatureConfig" in rendered_init


class TestInitTemplateValidity:
    """Tests that the rendered __init__.py produces valid Python code."""

    def test_rendered_init_is_valid_python(self, rendered_init, tmp_path):
        """Rendered __init__.py should be valid Python syntax."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text(rendered_init)

        compile(rendered_init, str(init_file), "exec")


class TestFeatureModuleImportability:
    """Integration tests for rendered feature modules."""

    def test_config_module_structure(self, rendered_config, tmp_path, monkeypatch):
        """Config module should have the expected structure when imported."""
        config_file = tmp_path / "config.py"
        config_file.write_text(rendered_config)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("config", config_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "UsersFeatureConfig")
        assert hasattr(module, "feature_config")

        # Test feature_config instance
        config = module.feature_config
        assert config.name == "users"
        assert config.prefix == "/users"
        assert "users" in config.tags

    def test_schemas_module_structure(self, rendered_schemas, tmp_path, monkeypatch):
        """Schemas module should have the expected structure when imported."""
        schemas_file = tmp_path / "schemas.py"
        schemas_file.write_text(rendered_schemas)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("schemas", schemas_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "UsersBase")
        assert hasattr(module, "UsersCreate")
        assert hasattr(module, "UsersUpdate")
        assert hasattr(module, "UsersPublic")


class TestFeatureTemplateWithDifferentNames:
    """Test that templates work correctly with different feature names."""

    def test_snake_case_feature_name(self, template_env):
        """Templates should handle snake_case feature names."""
        context = {
            "feature_name": "user_profiles",
            "feature_description": "User profiles",
        }
        template = template_env.get_template("config.py.jinja")
        rendered = template.render(**context)

        assert "User_profilesFeatureConfig" in rendered
        assert 'name: str = "user_profiles"' in rendered
        assert 'prefix: str = "/user-profiles"' in rendered

    def test_single_word_feature_name(self, template_env):
        """Templates should handle single word feature names."""
        context = {"feature_name": "posts", "feature_description": "Blog posts"}
        template = template_env.get_template("config.py.jinja")
        rendered = template.render(**context)

        assert "PostsFeatureConfig" in rendered
        assert 'name: str = "posts"' in rendered
        assert 'prefix: str = "/posts"' in rendered

    def test_default_description(self, template_env):
        """Templates should use default description if not provided."""
        context = {"feature_name": "orders"}
        template = template_env.get_template("config.py.jinja")
        rendered = template.render(**context)

        assert "Orders management" in rendered
