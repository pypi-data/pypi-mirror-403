# Code Review: Facet/Paxx

## Overall Assessment

The project is **well-architected** for a scaffolding CLI tool. It follows sensible patterns for code generation tools and has good separation between CLI commands, templates, and bundled features. However, there are notable **code repetitions** that could be extracted into shared utilities.

---

## Strengths

1. **Clean CLI organization** - Each subcommand lives in its own module (`db.py`, `docker.py`, `feature.py`, etc.)
2. **Template-based generation** - Using Jinja2 for all scaffolding is the right approach
3. **Domain-driven feature structure** - Generated projects follow clean patterns (models/schemas/services/routes per feature)
4. **Good documentation** - CLI commands have detailed help text and examples
5. **Async-first** - Bundled features use modern async SQLAlchemy patterns

---

## Code Repetitions Found

### 1. `to_snake_case()` - Duplicated in 2 files

| File | Function |
|------|----------|
| `bootstrap.py:18-26` | `to_snake_case()` |
| `feature.py:29-37` | `_to_snake_case()` |

**Both are identical.**

### 2. `get_templates_dir()` - Duplicated in 2 files

| File | Function |
|------|----------|
| `bootstrap.py:13-15` | `get_templates_dir()` |
| `feature.py:24-26` | `_get_templates_dir()` |

**Identical implementations.**

### 3. `validate_project_name()` / `validate_feature_name()` - Nearly identical

| File | Function |
|------|----------|
| `bootstrap.py:29-41` | `validate_project_name()` |
| `feature.py:40-52` | `_validate_feature_name()` |

The only difference is the error message text ("Project" vs "Feature").

### 4. `_check_project_context()` - Duplicated in 3 files

| File | Lines | Checks |
|------|-------|--------|
| `feature.py` | 55-82 | main.py, settings.py, returns features_dir |
| `deploy.py` | 19-45 | main.py, settings.py, returns deploy paths |
| `start.py` | 12-27 | main.py only |

All share the same validation pattern with slight variations in return values.

### 5. Subprocess wrapper pattern - Similar in 2 files

| File | Function |
|------|----------|
| `db.py:30-43` | `_run_alembic()` |
| `docker.py:30-37` | `_run_docker_compose()` |

Both follow the exact same pattern: check setup file, run subprocess, check return code.

---

## Recommendations

### 1. Create a shared `cli/utils.py` module

Extract common utilities:

```
src/paxx/cli/utils.py
├── to_snake_case()
├── validate_name(name, entity_type="project")
├── get_templates_dir()
├── check_project_context() -> returns ProjectContext dataclass
├── run_subprocess_command()
```

### 2. Unused constant

`features/__init__.py:20` has `AVAILABLE_FEATURES: list[str] = []` which is never used. The `list_available_features()` function dynamically discovers features instead. Remove or use it.

### 3. Inconsistent function naming

Some private functions use `_` prefix (`_to_snake_case`), others don't (`to_snake_case`). Standardize the convention - either all internal functions use `_` prefix or none do.

### 4. Consider a base class for wrapper CLIs

`db.py` and `docker.py` are essentially the same pattern. A base class or factory could reduce duplication:

```python
def create_wrapper_cli(
    name: str,
    required_file: str,
    base_command: list[str],
) -> typer.Typer:
    ...
```

### 5. Error handling could be unified

Currently different modules use different patterns:
- `console.print("[red]Error:[/red] ...")`
- `typer.secho("Error: ...", fg=typer.colors.RED)`

Pick one approach for consistency.

---

## Modularity Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Separation of concerns | Good | CLI/templates/features are well-separated |
| Single responsibility | Good | Each CLI module handles one domain |
| Reusability | Needs work | Common code is duplicated instead of shared |
| Testability | Good | Functions are small and testable |
| Extensibility | Good | Easy to add new CLI commands or features |

---

## Summary

The architecture is fundamentally sound. The main improvement needed is **extracting duplicated code into a shared utilities module**. This would:
- Reduce ~100 lines of duplicated code
- Make maintenance easier (fix bugs in one place)
- Improve consistency across CLI modules

The project follows good practices for a scaffolding tool and the generated code structure is clean and professional.
