Resync paxx in scaffolded project:

```bash
uv sync --reinstall-package paxx
```

Recreate tmp feature:

```bash
sh scripts/paxx-reboot.sh
```

Test

```bash
uv run pytest
```

Test full paxx flow:

```bash
sh scripts/test-paxx.sh
```

Check package name:

```bash
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/NAME/json
```

Publishing:

```bash
# Build the package
uv build

# Upload to TestPyPI
uv run twine upload --repository testpypi dist/*

# Publish to PyPI:
uv run twine upload dist/*
```

Docs: To preview the docs locally:

```bash
uv sync --extra docs
uv run mkdocs serve
```

Then visit `http://127.0.0.1:8000`

To deploy to GitHub Pages:

```bash
uv run mkdocs gh-deploy
```

Don't forget to update the repo_url and site_url in mkdocs.yml with your actual GitHub username/repo.

Docker: From scaffolded project:
```bash
docker compose up
```

Stop local postgres

```bash
brew services list
brew services stop service-name
```


Potential paxx app structure:

```bash
feature/
├── main.py                # Feature initialization
├── api/                   # Versioning and routing aggregation
│   └── api_v1/
│       └── api.py         # Includes all domain routers
├── core/                  # Global config, security/JWT
├── domains/               # Domain-specific logic
│   ├── items/
│   │   ├── router.py      # Endpoints
│   │   ├── service.py     # "CRUD" and logic
│   │   ├── models.py      # SQLAlchemy/Tortoise models
│   │   └── schemas.py     # Pydantic models
│   └── users/
│       └── ...
└── db/                    # Session management and migrations
```