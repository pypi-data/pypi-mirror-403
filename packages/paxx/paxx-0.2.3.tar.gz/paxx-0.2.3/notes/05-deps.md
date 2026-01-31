# Dependencies

## Core Featurelication

| Package | Purpose |
|---------|---------|
| `paxx` | The main featurelication package |
| `fastapi` | Web framework for building APIs |
| `starlette` | ASGI framework (FastAPI's foundation) |
| `uvicorn` | ASGI server to run the feature |
| `pydantic` | Data validation and settings management |
| `pydantic-core` | Core validation logic for Pydantic |
| `pydantic-settings` | Settings management with env vars |

## Database

| Package | Purpose |
|---------|---------|
| `sqlalchemy` | SQL toolkit and ORM |
| `aiosqlite` | Async SQLite driver |
| `alembic` | Database migrations |
| `greenlet` | Coroutine support for SQLAlchemy async |

## Authentication

| Package | Purpose |
|---------|---------|
| `bcrypt` | Password hashing |
| `passlib` | Password hashing utilities |
| `python-jose` | JWT token encoding/decoding |
| `cryptography` | Cryptographic primitives |
| `ecdsa` | ECDSA signatures (for JWT) |
| `pyasn1` | ASN.1 parsing (crypto dependency) |
| `rsa` | RSA encryption (for JWT) |

## CLI

| Package | Purpose |
|---------|---------|
| `typer` | CLI framework |
| `click` | Command line toolkit (Typer's foundation) |
| `shellingham` | Shell detection for Typer |
| `rich` | Terminal formatting and colors |
| `pygments` | Syntax highlighting |
| `markdown-it-py` | Markdown parsing (for Rich) |
| `mdurl` | URL utilities for markdown-it |

## Configuration & Environment

| Package | Purpose |
|---------|---------|
| `python-dotenv` | Load env vars from .env files |
| `pyyaml` | YAML parsing |

## Logging

| Package | Purpose |
|---------|---------|
| `structlog` | Structured logging |

## HTTP Client

| Package | Purpose |
|---------|---------|
| `httpx` | Async HTTP client |
| `httpcore` | HTTP transport (httpx dependency) |
| `certifi` | SSL certificates |
| `idna` | Internationalized domain names |
| `h11` | HTTP/1.1 protocol |

## Server Extras

| Package | Purpose |
|---------|---------|
| `httptools` | Fast HTTP parsing for uvicorn |
| `uvloop` | Fast event loop for uvicorn |
| `watchfiles` | File watching for auto-reload |
| `websockets` | WebSocket support |
| `anyio` | Async compatibility layer |

## Templating

| Package | Purpose |
|---------|---------|
| `jinja2` | Template engine |
| `mako` | Template engine (used by Alembic) |
| `markupsafe` | Safe string escaping |

## Development Tools

| Package | Purpose |
|---------|---------|
| `pytest` | Testing framework |
| `pytest-asyncio` | Async test support |
| `mypy` | Static type checker |
| `mypy-extensions` | Mypy support extensions |
| `ruff` | Fast Python linter and formatter |
| `pre-commit` | Git hooks manager |

## Pre-commit Dependencies

| Package | Purpose |
|---------|---------|
| `cfgv` | Config file validation |
| `identify` | File type identification |
| `nodeenv` | Node.js environment manager |
| `virtualenv` | Virtual environment creation |
| `distlib` | Distribution utilities |
| `filelock` | File locking |
| `platformdirs` | Platform-specific directories |

## Type System

| Package | Purpose |
|---------|---------|
| `typing-extensions` | Backported typing features |
| `typing-inspection` | Runtime typing introspection |
| `annotated-types` | Annotated type constraints |
| `annotated-doc` | Documentation via annotations |

## Utilities

| Package | Purpose |
|---------|---------|
| `packaging` | Version parsing |
| `pathspec` | Gitignore-style path matching |
| `pluggy` | Plugin system (pytest uses it) |
| `iniconfig` | INI file parsing (pytest config) |
| `six` | Python 2/3 compatibility |
| `cffi` | C Foreign Function Interface |
| `pycparser` | C parser (cffi dependency) |
| `librt` | Runtime library utilities |
