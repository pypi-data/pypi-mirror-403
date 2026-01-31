# AWS Cognito Auth Feature Setup

AWS Cognito authentication feature providing user registration, login, password reset, and JWT validation.

## Environment Variables

Add to your `.env` file:

```env
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret
COGNITO_REGION=us-east-1
```

## AWS Cognito Setup

1. Create a User Pool in AWS Cognito
2. Create an App Client with:
   - Generate client secret: **Yes**
   - Authentication flows: `ALLOW_USER_PASSWORD_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`
3. Configure email verification (recommended)

## API Endpoints

| Endpoint                        | Method | Description                      |
| ------------------------------- | ------ | -------------------------------- |
| `/auth/register`                | POST   | Register new user                |
| `/auth/confirm`                 | POST   | Confirm email with code          |
| `/auth/resend-confirmation`     | POST   | Resend verification code         |
| `/auth/login`                   | POST   | Login, get tokens                |
| `/auth/refresh`                 | POST   | Refresh access token             |
| `/auth/logout`                  | POST   | Global sign out                  |
| `/auth/me`                      | GET    | Get current user (requires auth) |
| `/auth/forgot-password`         | POST   | Initiate password reset          |
| `/auth/confirm-forgot-password` | POST   | Complete password reset          |
| `/auth/change-password`         | POST   | Change password                  |
| `/auth/delete-account`          | DELETE | Delete user account              |

## Protecting Routes

Use the `get_current_user` dependency to protect routes:

```python
from fastapi import Depends
from features.auth_aws_cognito.dependencies import get_current_user

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user_id": user["sub"], "email": user["email"]}
```

The user dict contains:

- `sub`: Cognito user ID (UUID)
- `email`: User's email
- `email_verified`: Boolean
- `token_use`: "access" or "id"

## Automatic Setup (already done)

The following script was already run when adding the feature. No further actions are required. The following section is for reference.

### The setup script

This script was run when adding "auth_aws_cognito" feature:

```bash
python features/auth_aws_cognito/setup.py
```

### Added Dependencies

Added in `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "boto3>=1.35.0",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.27.0",
    "email-validator>=2.3.0",
]
```

Then installed with:

```bash
uv sync
```

### Required Settings

Added settings in `settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Cognito settings
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_client_secret: str
    cognito_region: str = "us-east-1"
```
