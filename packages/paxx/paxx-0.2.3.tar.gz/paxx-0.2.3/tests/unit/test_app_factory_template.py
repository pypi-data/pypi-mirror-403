"""Tests for the application factory templates.

These tests verify that the generated main.py, exceptions.py,
and middleware.py templates:
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
def rendered_main(template_env):
    """Render the main.py template with test values."""
    template = template_env.get_template("main.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_exceptions(template_env):
    """Render the exceptions.py template with test values."""
    template = template_env.get_template("core/exceptions.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


@pytest.fixture
def rendered_middleware(template_env):
    """Render the middleware.py template with test values."""
    template = template_env.get_template("core/middleware.py.jinja")
    return template.render(
        project_name="TestProject",
        project_name_snake="test_project",
    )


class TestMainTemplateRendering:
    """Tests for main.py template rendering."""

    def test_main_template_renders(self, rendered_main):
        """Main template should render without errors."""
        assert "create_app" in rendered_main
        assert "FastAPI" in rendered_main

    def test_main_includes_create_app_function(self, rendered_main):
        """Rendered main.py should include create_app function."""
        assert "def create_app()" in rendered_main
        assert "-> FastAPI" in rendered_main

    def test_main_includes_lifespan(self, rendered_main):
        """Rendered main.py should include lifespan context manager."""
        assert "async def lifespan" in rendered_main
        assert "@asynccontextmanager" in rendered_main
        assert "close_db()" in rendered_main

    def test_main_includes_app_configuration(self, rendered_main):
        """Rendered main.py should configure the app with settings."""
        assert "title=settings.app_name" in rendered_main
        assert "debug=settings.debug" in rendered_main
        assert "lifespan=lifespan" in rendered_main

    def test_main_includes_cors_middleware(self, rendered_main):
        """Rendered main.py should include CORS middleware configuration."""
        assert "CORSMiddleware" in rendered_main
        assert "allow_origins=settings.cors_origins" in rendered_main

    def test_main_includes_exception_handlers(self, rendered_main):
        """Rendered main.py should register exception handlers."""
        assert "register_exception_handlers(app)" in rendered_main

    def test_main_includes_middleware(self, rendered_main):
        """Rendered main.py should register custom middleware."""
        assert "register_middleware(app)" in rendered_main

    def test_main_includes_health_router(self, rendered_main):
        """Rendered main.py should register health router."""
        assert "from features.health.routes import router" in rendered_main
        assert "app.include_router(health_router" in rendered_main

    def test_main_creates_app_instance(self, rendered_main):
        """Rendered main.py should create app instance."""
        assert "app = create_app()" in rendered_main


class TestMainTemplateValidity:
    """Tests that the rendered main.py produces valid Python code."""

    def test_rendered_main_is_valid_python(self, rendered_main, tmp_path):
        """Rendered main.py should be valid Python syntax."""
        main_file = tmp_path / "main.py"
        main_file.write_text(rendered_main)

        # This will raise SyntaxError if the code is invalid
        compile(rendered_main, str(main_file), "exec")

    def test_rendered_main_has_valid_ast(self, rendered_main):
        """Rendered main.py should have a valid AST structure."""
        tree = ast.parse(rendered_main)

        # Find all function definitions
        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]

        assert "lifespan" in functions
        assert "create_app" in functions


class TestExceptionsTemplateRendering:
    """Tests for exceptions.py template rendering."""

    def test_exceptions_template_renders(self, rendered_exceptions):
        """Exceptions template should render without errors."""
        assert "class AppException" in rendered_exceptions
        assert "register_exception_handlers" in rendered_exceptions

    def test_exceptions_includes_base_exception(self, rendered_exceptions):
        """Rendered exceptions.py should include base AppException."""
        assert "class AppException(Exception):" in rendered_exceptions
        assert "status_code" in rendered_exceptions
        assert "message" in rendered_exceptions

    def test_exceptions_includes_not_found(self, rendered_exceptions):
        """Rendered exceptions.py should include NotFoundError."""
        assert "class NotFoundError(AppException):" in rendered_exceptions
        assert "HTTP_404_NOT_FOUND" in rendered_exceptions

    def test_exceptions_includes_bad_request(self, rendered_exceptions):
        """Rendered exceptions.py should include BadRequestError."""
        assert "class BadRequestError(AppException):" in rendered_exceptions
        assert "HTTP_400_BAD_REQUEST" in rendered_exceptions

    def test_exceptions_includes_unauthorized(self, rendered_exceptions):
        """Rendered exceptions.py should include UnauthorizedError."""
        assert "class UnauthorizedError(AppException):" in rendered_exceptions
        assert "HTTP_401_UNAUTHORIZED" in rendered_exceptions

    def test_exceptions_includes_forbidden(self, rendered_exceptions):
        """Rendered exceptions.py should include ForbiddenError."""
        assert "class ForbiddenError(AppException):" in rendered_exceptions
        assert "HTTP_403_FORBIDDEN" in rendered_exceptions

    def test_exceptions_includes_conflict(self, rendered_exceptions):
        """Rendered exceptions.py should include ConflictError."""
        assert "class ConflictError(AppException):" in rendered_exceptions
        assert "HTTP_409_CONFLICT" in rendered_exceptions

    def test_exceptions_includes_handler(self, rendered_exceptions):
        """Rendered exceptions.py should include exception handler."""
        assert "async def app_exception_handler" in rendered_exceptions
        assert "JSONResponse" in rendered_exceptions


class TestExceptionsTemplateValidity:
    """Tests that the rendered exceptions.py produces valid Python code."""

    def test_rendered_exceptions_is_valid_python(self, rendered_exceptions, tmp_path):
        """Rendered exceptions.py should be valid Python syntax."""
        exceptions_file = tmp_path / "exceptions.py"
        exceptions_file.write_text(rendered_exceptions)

        compile(rendered_exceptions, str(exceptions_file), "exec")

    def test_rendered_exceptions_has_valid_ast(self, rendered_exceptions):
        """Rendered exceptions.py should have expected classes."""
        tree = ast.parse(rendered_exceptions)

        classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]

        assert "AppException" in classes
        assert "NotFoundError" in classes
        assert "BadRequestError" in classes
        assert "UnauthorizedError" in classes
        assert "ForbiddenError" in classes
        assert "ConflictError" in classes


class TestMiddlewareTemplateRendering:
    """Tests for middleware.py template rendering."""

    def test_middleware_template_renders(self, rendered_middleware):
        """Middleware template should render without errors."""
        assert "request_id_middleware" in rendered_middleware
        assert "register_middleware" in rendered_middleware

    def test_middleware_includes_request_id(self, rendered_middleware):
        """Rendered middleware.py should include request ID middleware."""
        assert "async def request_id_middleware" in rendered_middleware
        assert "X-Request-ID" in rendered_middleware
        assert "uuid.uuid4()" in rendered_middleware

    def test_middleware_includes_timing(self, rendered_middleware):
        """Rendered middleware.py should include timing middleware."""
        assert "async def timing_middleware" in rendered_middleware
        assert "X-Process-Time" in rendered_middleware
        assert "time.perf_counter()" in rendered_middleware

    def test_middleware_includes_register_function(self, rendered_middleware):
        """Rendered middleware.py should include register function."""
        assert "def register_middleware(app: FastAPI)" in rendered_middleware


class TestMiddlewareTemplateValidity:
    """Tests that the rendered middleware.py produces valid Python code."""

    def test_rendered_middleware_is_valid_python(self, rendered_middleware, tmp_path):
        """Rendered middleware.py should be valid Python syntax."""
        middleware_file = tmp_path / "middleware.py"
        middleware_file.write_text(rendered_middleware)

        compile(rendered_middleware, str(middleware_file), "exec")

    def test_rendered_middleware_has_valid_ast(self, rendered_middleware):
        """Rendered middleware.py should have expected functions."""
        tree = ast.parse(rendered_middleware)

        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]

        assert "request_id_middleware" in functions
        assert "timing_middleware" in functions
        assert "register_middleware" in functions


class TestCoreModuleImportability:
    """Integration tests for rendered core modules."""

    def test_exceptions_module_structure(
        self, rendered_exceptions, tmp_path, monkeypatch
    ):
        """Exceptions module should have the expected structure when imported."""
        exceptions_file = tmp_path / "exceptions.py"
        exceptions_file.write_text(rendered_exceptions)

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("exceptions", exceptions_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "AppException")
        assert hasattr(module, "NotFoundError")
        assert hasattr(module, "BadRequestError")
        assert hasattr(module, "UnauthorizedError")
        assert hasattr(module, "ForbiddenError")
        assert hasattr(module, "ConflictError")
        assert hasattr(module, "app_exception_handler")
        assert hasattr(module, "register_exception_handlers")

        # Verify class hierarchy
        assert issubclass(module.NotFoundError, module.AppException)
        assert issubclass(module.BadRequestError, module.AppException)

    def test_middleware_module_structure(
        self, rendered_middleware, tmp_path, monkeypatch
    ):
        """Middleware module should have the expected structure when imported."""
        middleware_file = tmp_path / "middleware.py"
        middleware_file.write_text(rendered_middleware)

        # Create mock core/logging module that middleware imports
        core_dir = tmp_path / "core"
        core_dir.mkdir()
        (core_dir / "__init__.py").write_text("")
        (core_dir / "logging.py").write_text(
            "import logging\ndef get_logger(name): return logging.getLogger(name)"
        )

        monkeypatch.syspath_prepend(str(tmp_path))

        import importlib.util

        spec = importlib.util.spec_from_file_location("middleware", middleware_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify all expected exports exist
        assert hasattr(module, "request_id_middleware")
        assert hasattr(module, "timing_middleware")
        assert hasattr(module, "register_middleware")

        # Verify they are callable
        assert callable(module.request_id_middleware)
        assert callable(module.timing_middleware)
        assert callable(module.register_middleware)
