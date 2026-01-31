# Testing Strategy

## Overview

Testing is split between two concerns:
1. **paxx repo** - tests that code generation works correctly
2. **Generated projects** - tests that the generated app actually works

## Test Structure

### paxx repository

```
tests/
  unit/           # Fast, no external dependencies
  integration/    # Uses CliRunner, creates files in tmp_path
scripts/
  test-paxx.sh    # Orchestrates full e2e validation
```

#### Unit tests (`tests/unit/`)
- Template rendering (Jinja2 templates produce valid Python)
- Utility functions (`paxx.features` module)
- No filesystem I/O, no Docker, no database

Current tests to move here:
- `test_features.py`
- `test_database_template.py`
- `test_app_factory_template.py`
- `test_settings_template.py`
- `test_app_structure_template.py`
- `test_core_utilities_template.py`

#### Integration tests (`tests/integration/`)
- CLI commands via CliRunner
- Verify correct files are created with correct content
- Uses pytest `tmp_path` for isolation
- No Docker, no database, no `uv sync`

Current tests to move here:
- `test_cli.py`
- `test_cli_commands.py`

### Generated project (template)

E2E tests are part of the generated project template, not the paxx repo.

```
myproject/
  e2e/
    conftest.py          # Shared fixtures (APP_URL client)
    test_health.py       # Core app tests
    test_products_api.py # Feature e2e tests (copied when feature is added)
  features/
    example_products/
      models.py
      routes.py
      ...
```

Feature e2e tests are stored in `src/paxx/features/<feature>/e2e/` and are
copied to the project's root `/e2e/` directory when the feature is added.
This centralizes all e2e tests in one location with shared fixtures.

Configure pytest to discover tests:
```toml
[tool.pytest.ini_options]
testpaths = ["e2e"]
```

These tests:
- Assume environment already exists (app running, DB migrated)
- Take `APP_URL` as environment variable
- Can run against any environment (local, staging, prod)
- Are owned by the generated project, not paxx

Example conftest.py:
```python
import os
import httpx
import pytest

@pytest.fixture
def client():
    url = os.environ.get("APP_URL", "http://localhost:8000")
    with httpx.Client(base_url=url) as c:
        yield c
```

## Test Orchestration Script

`scripts/test-paxx.sh` orchestrates the full validation:

```bash
#!/bin/bash
set -e

# 1. Run paxx's own unit and integration tests
uv run pytest tests/

# 2. Bootstrap a test project
mkdir -p tmp && cd tmp
rm -rf test-project
paxx bootstrap test-project
cd test-project
uv sync --all-extras

# 3. Add features and run migrations
paxx feature add example_products
docker compose up db -d --wait
paxx db migrate "add example_products"
paxx db upgrade

# 4. Start app and run e2e tests
docker compose up app -d --wait
APP_URL=http://localhost:8000 uv run pytest e2e/

# 5. Cleanup
docker compose down -v
```

## Benefits of This Approach

1. **Separation of concerns**
   - paxx tests: "Did I generate valid code?"
   - Generated project tests: "Does the code work?"

2. **Self-testing projects**
   - Users get e2e tests out of the box
   - Can run against their own staging/production

3. **Centralized e2e tests**
   - All e2e tests in one location with shared fixtures
   - Feature e2e tests are copied to /e2e when feature is added
   - Easy to run all e2e tests with a single command

4. **Decoupled from infrastructure**
   - E2E tests don't care how env was created
   - Same tests work for Docker, k8s, cloud deployments

5. **CI-friendly**
   - Unit/integration tests are fast, no Docker needed
   - E2E tests run in separate stage with Docker

## Libraries

- `pytest` - test runner
- `httpx` - HTTP client for e2e tests
- `pytest-asyncio` - if testing async code
- Docker Compose - environment orchestration

## Testing Dockerized App

To test the app running inside Docker (not just DB in Docker):

1. Build and start all services: `docker compose up -d --build`
2. Wait for health check: `curl --retry 10 http://localhost:8000/health`
3. Run e2e tests: `APP_URL=http://localhost:8000 pytest e2e/`
4. Cleanup: `docker compose down -v`

This validates the Dockerfile, container networking, and production-like setup.

## Implementation Plan

### Phase 1: Reorganize existing tests ✅

- [x] Create `tests/unit/` and `tests/integration/` directories
- [x] Move template tests to `tests/unit/`:
   - [x] `test_features.py`
   - [x] `test_database_template.py`
   - [x] `test_app_factory_template.py`
   - [x] `test_settings_template.py`
   - [x] `test_app_structure_template.py`
   - [x] `test_core_utilities_template.py`
- [x] Move CLI tests to `tests/integration/`:
   - [x] `test_cli.py`
   - [x] `test_cli_commands.py`
- [x] Update imports in `conftest.py` if needed
- [x] Verify all tests still pass: `uv run pytest`

### Phase 2: Add e2e tests to project template ✅

- [x] Add `httpx` as dev dependency in generated `pyproject.toml` (already in main dependencies)
- [x] Add pytest testpaths config: `testpaths = ["e2e"]`
- [x] Create template files:
   - [x] `src/paxx/templates/project/e2e/conftest.py.jinja`
   - [x] `src/paxx/templates/project/e2e/test_health.py.jinja`
- [x] Update bootstrap command to generate e2e test files
- [x] Test: bootstrap a project and verify e2e files are created

### Phase 3: Add feature-specific e2e tests ✅

- [x] Create `src/paxx/features/example_products/e2e/test_products_api.py`
- [x] Tests are copied to project /e2e when feature is added
- [x] Tests should cover CRUD operations for the feature

### Phase 4: Update orchestration script ✅

- [x] Refactor `scripts/test-paxx.sh`:
   - [x] Remove interactive parts (`open` commands)
   - [x] Add proper cleanup trap at the start
   - [x] Add e2e test execution step
- [x] Create separate `scripts/demo-paxx.sh` for interactive demo
- [x] Ensure script is CI-compatible (no macOS-specific commands)

### Phase 5: CI integration (optional)

- [ ] Add GitHub Actions workflow for tests
- [ ] Separate jobs for unit/integration (fast) and e2e (requires Docker)
- [ ] Run e2e tests only on main branch or PR merges to save resources
