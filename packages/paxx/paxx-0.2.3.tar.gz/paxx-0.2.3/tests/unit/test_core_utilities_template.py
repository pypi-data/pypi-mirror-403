"""Tests for the core utilities templates.

These tests verify that the generated core templates:
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
        Path(__file__).parent.parent.parent / "src" / "paxx" / "templates" / "project"
    )
    return Environment(loader=FileSystemLoader(str(template_dir)))


@pytest.fixture
def rendered_dependencies(template_env):
    """Render the dependencies.py template with test values."""
    template = template_env.get_template("core/dependencies.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_schemas(template_env):
    """Render the schemas.py template with test values."""
    template = template_env.get_template("core/schemas.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_core_init(template_env):
    """Render the core __init__.py template with test values."""
    template = template_env.get_template("core/__init__.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


class TestDependenciesTemplateRendering:
    """Tests for dependencies.py template rendering."""

    def test_dependencies_template_renders(self, rendered_dependencies):
        """Dependencies template should render without errors."""
        assert "PaginationParams" in rendered_dependencies
        assert "get_pagination" in rendered_dependencies

    def test_dependencies_includes_pagination_params(self, rendered_dependencies):
        """Rendered dependencies.py should include PaginationParams class."""
        assert "class PaginationParams(BaseModel):" in rendered_dependencies
        assert "page: int" in rendered_dependencies
        assert "page_size: int" in rendered_dependencies

    def test_dependencies_includes_offset_property(self, rendered_dependencies):
        """Rendered dependencies.py should include offset property."""
        assert "def offset(self) -> int:" in rendered_dependencies
        assert "(self.page - 1) * self.page_size" in rendered_dependencies

    def test_dependencies_includes_limit_property(self, rendered_dependencies):
        """Rendered dependencies.py should include limit property."""
        assert "def limit(self) -> int:" in rendered_dependencies
        assert "self.page_size" in rendered_dependencies

    def test_dependencies_includes_get_pagination(self, rendered_dependencies):
        """Rendered dependencies.py should include get_pagination function."""
        assert "def get_pagination(" in rendered_dependencies
        assert "-> PaginationParams:" in rendered_dependencies

    def test_dependencies_includes_query_validation(self, rendered_dependencies):
        """Rendered dependencies.py should include Query validation."""
        assert "Query(ge=1" in rendered_dependencies
        assert "le=100" in rendered_dependencies


class TestDependenciesTemplateValidity:
    """Tests that the rendered dependencies.py produces valid Python code."""

    def test_rendered_dependencies_is_valid_python(
        self, rendered_dependencies, tmp_path
    ):
        """Rendered dependencies.py should be valid Python syntax."""
        deps_file = tmp_path / "dependencies.py"
        deps_file.write_text(rendered_dependencies)

        compile(rendered_dependencies, str(deps_file), "exec")

    def test_rendered_dependencies_has_valid_ast(self, rendered_dependencies):
        """Rendered dependencies.py should have a valid AST structure."""
        tree = ast.parse(rendered_dependencies)

        # Find all class definitions
        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]
        assert "PaginationParams" in classes

        # Find all function definitions
        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        assert "get_pagination" in functions
        assert "offset" in functions
        assert "limit" in functions


class TestSchemasTemplateRendering:
    """Tests for schemas.py template rendering."""

    def test_schemas_template_renders(self, rendered_schemas):
        """Schemas template should render without errors."""
        assert "SuccessResponse" in rendered_schemas
        assert "ErrorResponse" in rendered_schemas
        assert "ListResponse" in rendered_schemas

    def test_schemas_includes_success_response(self, rendered_schemas):
        """Rendered schemas.py should include SuccessResponse."""
        assert "class SuccessResponse(BaseModel):" in rendered_schemas
        assert "message: str" in rendered_schemas

    def test_schemas_includes_error_response(self, rendered_schemas):
        """Rendered schemas.py should include ErrorResponse."""
        assert "class ErrorResponse(BaseModel):" in rendered_schemas
        assert "message: str" in rendered_schemas
        assert "detail: str | None" in rendered_schemas

    def test_schemas_includes_pagination_meta(self, rendered_schemas):
        """Rendered schemas.py should include PaginationMeta."""
        assert "class PaginationMeta(BaseModel):" in rendered_schemas
        assert "page: int" in rendered_schemas
        assert "page_size: int" in rendered_schemas
        assert "total_items: int" in rendered_schemas
        assert "total_pages: int" in rendered_schemas

    def test_schemas_includes_list_response(self, rendered_schemas):
        """Rendered schemas.py should include generic ListResponse."""
        assert "class ListResponse(BaseModel, Generic[T]):" in rendered_schemas
        assert "items: list[T]" in rendered_schemas
        assert "meta: PaginationMeta" in rendered_schemas

    def test_schemas_includes_type_var(self, rendered_schemas):
        """Rendered schemas.py should include TypeVar for generics."""
        assert 'T = TypeVar("T")' in rendered_schemas


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

        assert "SuccessResponse" in classes
        assert "ErrorResponse" in classes
        assert "PaginationMeta" in classes
        assert "ListResponse" in classes


class TestCoreInitTemplateRendering:
    """Tests for core __init__.py template rendering."""

    def test_init_template_renders(self, rendered_core_init):
        """Core __init__.py template should render without errors."""
        assert "PaginationParams" in rendered_core_init
        assert "get_pagination" in rendered_core_init

    def test_init_imports_from_dependencies(self, rendered_core_init):
        """Core __init__.py should import from dependencies."""
        assert "from core.dependencies import" in rendered_core_init

    def test_init_imports_from_schemas(self, rendered_core_init):
        """Core __init__.py should import from schemas."""
        assert "from core.schemas import" in rendered_core_init

    def test_init_includes_all_exports(self, rendered_core_init):
        """Core __init__.py should include __all__ with all exports."""
        assert "__all__" in rendered_core_init
        assert '"PaginationParams"' in rendered_core_init
        assert '"get_pagination"' in rendered_core_init
        assert '"SuccessResponse"' in rendered_core_init
        assert '"ErrorResponse"' in rendered_core_init
        assert '"ListResponse"' in rendered_core_init
        assert '"PaginationMeta"' in rendered_core_init


class TestCoreInitTemplateValidity:
    """Tests that the rendered core __init__.py produces valid Python code."""

    def test_rendered_init_is_valid_python(self, rendered_core_init, tmp_path):
        """Rendered core __init__.py should be valid Python syntax."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text(rendered_core_init)

        compile(rendered_core_init, str(init_file), "exec")


class TestCoreModuleImportability:
    """Integration tests for rendered core modules."""

    def test_dependencies_module_structure(
        self, rendered_dependencies, tmp_path, monkeypatch
    ):
        """Dependencies module should have the expected structure when imported."""
        deps_file = tmp_path / "dependencies.py"
        deps_file.write_text(rendered_dependencies)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("dependencies", deps_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "PaginationParams")
        assert hasattr(module, "get_pagination")

        # Verify they are callable/classes
        assert callable(module.get_pagination)

        # Test PaginationParams
        params = module.PaginationParams(page=2, page_size=20)
        assert params.offset == 20
        assert params.limit == 20

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
        assert hasattr(module, "SuccessResponse")
        assert hasattr(module, "ErrorResponse")
        assert hasattr(module, "PaginationMeta")
        assert hasattr(module, "ListResponse")

        # Test SuccessResponse
        success = module.SuccessResponse(message="Test success")
        assert success.message == "Test success"

        # Test ErrorResponse
        error = module.ErrorResponse(message="Test error", detail="Some detail")
        assert error.message == "Test error"
        assert error.detail == "Some detail"

        # Test PaginationMeta
        meta = module.PaginationMeta(
            page=1, page_size=20, total_items=100, total_pages=5
        )
        assert meta.total_items == 100

        # Test ListResponse with concrete type
        list_response = module.ListResponse[dict](
            items=[{"id": 1}, {"id": 2}],
            meta=meta,
        )
        assert len(list_response.items) == 2
        assert list_response.meta.page == 1

    def test_pagination_params_calculations(
        self, rendered_dependencies, tmp_path, monkeypatch
    ):
        """PaginationParams should correctly calculate offset and limit."""
        deps_file = tmp_path / "dependencies.py"
        deps_file.write_text(rendered_dependencies)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("dependencies", deps_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Test page 1
        params = module.PaginationParams(page=1, page_size=10)
        assert params.offset == 0
        assert params.limit == 10

        # Test page 3
        params = module.PaginationParams(page=3, page_size=25)
        assert params.offset == 50  # (3-1) * 25 = 50
        assert params.limit == 25
