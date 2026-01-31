# paxx Plugin System

## Overview

paxx provides optional, reusable functionality through **contrib plugins**—pre-built features for common features like authentication, admin panels, and permissions. Unlike Django's magic-heavy featureroach, paxx plugins are designed to be **scaffolded into your project**, giving you full ownership and transparency.

## Philosophy

**"Eject and own"** - Plugins are templates, not dependencies.

When you install a plugin, paxx copies the code into your `features/` directory. This means:

- You can read every line of code
- You can modify anything without fighting the framework
- Your auth code won't break when paxx updates
- It's tracked in your git repo like any other code

This follows the same pattern as `create-react-feature`, `rails generate`, and Django's own `startfeature`.

## Quick Start

```bash
# Add the auth plugin to your project
paxx feature add auth

# This creates features/auth/ with:
# - models.py (User model)
# - schemas.py (registration, login, profile)
# - services.py (password hashing, tokens)
# - routes.py (endpoints)
# - dependencies.py (get_current_user)

# Run migrations
paxx db migrate "add users"
paxx db upgrade
```

That's it. You now have a fully functional auth system that you own and can customize.

## Available Plugins

### `auth` - Authentication & Users

Complete authentication system:

```bash
paxx feature add auth
```

**What you get:**

```
features/auth/
├── __init__.py
├── config.py           # Feature configuration
├── models.py           # User model
├── schemas.py          # UserCreate, UserPublic, LoginRequest, etc.
├── services.py         # Password hashing, JWT tokens
├── routes.py           # /register, /login, /logout, /me
└── dependencies.py     # get_current_user, require_auth
```

**Endpoints:**
- `POST /auth/register` - create new user
- `POST /auth/login` - authenticate and get token
- `POST /auth/logout` - invalidate session
- `GET /auth/me` - get current user profile
- `PATCH /auth/me` - update current user profile

**Dependencies for your routes:**
```python
from features.auth.dependencies import get_current_user, require_auth

@router.get("/protected")
async def protected_route(user: User = Depends(require_auth)):
    return {"message": f"Hello {user.email}"}
```

### `admin` - Admin Panel (Future)

Auto-generated admin interface for managing models.

### `permissions` - RBAC (Future)

Role-based access control system.

## Architecture

### Plugin Source Structure

Plugins live in the paxx package as templates:

```
src/paxx/
├── contrib/
│   ├── __init__.py
│   ├── auth/              # Auth plugin template
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── admin/             # Admin plugin template (future)
│   └── permissions/       # Permissions plugin template (future)
```

### How `paxx feature add` Works

1. Locates the plugin in `paxx.contrib`
2. Copies files to `features/<plugin_name>/`
3. Adjusts imports for your project structure
4. Plugin is now a regular feature—discovered automatically

### Existing Foundation

paxx's feature system already supports plugins:

- **Model auto-discovery** - Alembic finds models across all features
- **Standardized structure** - consistent file organization

## Customization Examples

Once scaffolded, you can customize anything:

### Add Fields to User Model

```python
# features/auth/models.py
class User(BaseModel):
    __tablename__ = "users"

    email: Mfeatureed[str] = mfeatureed_column(String(255), unique=True, index=True)
    hashed_password: Mfeatureed[str] = mfeatureed_column(String(255))
    is_active: Mfeatureed[bool] = mfeatureed_column(default=True)
    is_superuser: Mfeatureed[bool] = mfeatureed_column(default=False)

    # Add your own fields
    first_name: Mfeatureed[str | None] = mfeatureed_column(String(100))
    last_name: Mfeatureed[str | None] = mfeatureed_column(String(100))
    avatar_url: Mfeatureed[str | None] = mfeatureed_column(String(500))
```

### Change Token Strategy

```python
# features/auth/services.py
# Switch from JWT to session-based, or change token expiry, etc.
```

### Add OAuth Providers

```python
# features/auth/routes.py
@router.get("/oauth/google")
async def google_oauth():
    # Add your OAuth flow
    pass
```

## CLI Commands

```bash
paxx feature add <plugin>      # Scaffold a plugin into features/
paxx feature add auth          # Add authentication
paxx feature add admin         # Add admin panel (future)
```

## Implementation Checklist

### Phase 1: Auth Plugin Template

- [ ] `contrib/auth/models.py` - User model
- [ ] `contrib/auth/schemas.py` - request/response schemas
- [ ] `contrib/auth/services.py` - password hashing, JWT tokens
- [ ] `contrib/auth/routes.py` - API endpoints
- [ ] `contrib/auth/dependencies.py` - get_current_user, require_auth
- [ ] `contrib/auth/config.py` - feature configuration

### Phase 2: CLI Command

- [ ] `paxx feature add <plugin>` - scaffold plugin to features/
- [ ] List available plugins on invalid name
- [ ] Prevent overwriting existing feature

### Phase 3: Additional Plugins

- [ ] `contrib/admin` - admin interface
- [ ] `contrib/permissions` - RBAC system

## Design Decisions

### Why Scaffold Instead of Import?

**Transparency** - You can read and understand every line of your auth code.

**Flexibility** - Modify the User model, change password hashing, add OAuth—no "ejecting" needed because you already own the code.

**Stability** - Your auth won't break when paxx updates. You control when to adopt changes.

**Simplicity** - No plugin discovery system, no dependency resolution, no magic. It's just an feature.

### Why Not pip Packages?

Contrib plugins are:

- Tightly integrated with paxx conventions
- Simple files, not complex packages
- Designed to be modified, not used as-is

Third-party plugins can still be distributed via pip if they prefer the import featureroach.
