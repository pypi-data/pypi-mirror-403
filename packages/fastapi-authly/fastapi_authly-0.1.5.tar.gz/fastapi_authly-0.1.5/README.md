# fastapi-authly

[![PyPI version](https://badge.fury.io/py/fastapi-authly.svg)](https://pypi.org/project/fastapi-authly/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-authly.svg)](https://pypi.org/project/fastapi-authly/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A modular authentication system for FastAPI applications. Provides complete user authentication with OAuth2, JWT tokens, password recovery, and more.

## ✨ Features

- 🔐 **OAuth2 Password Flow** - Standard OAuth2 authentication
- 🎫 **JWT Token Management** - Secure token creation and validation
- 🔑 **Password Recovery** - Email-based password reset
- 👤 **User Management** - Registration, profile management
- 📧 **Email Verification** - User email verification system
- 🔄 **Token Refresh** - Refresh token functionality
- 🧩 **Modular Design** - Easy to integrate and configure
- 🛡️ **Security First** - Built with security best practices
- 📚 **Type Hints** - Full type annotation support

## 🚀 Quick Start (Tortoise + Postgres 默认实现)

### Installation

```bash
uv pip install fastapi-authly
# or
pip install fastapi-authly
```

### Minimal FastAPI App (uses default TortoiseUserRepository)

```python
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi_authly import (
    AuthConfig,
    AuthDependencyConfig,
    create_auth_router,
)
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository

app = FastAPI()

# 1) init Tortoise (Postgres)
register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/mydb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# 2) assemble auth router with default repo (can override via dependencies)
config = AuthConfig(token_url="login")  # keep token_url aligned with /login route
deps = AuthDependencyConfig(user_repository=TortoiseUserRepository())

auth_router = create_auth_router(config=config, dependencies=deps)
app.include_router(auth_router)

# Optional: Setup Scalar API documentation (static resources included, no manual setup needed)
from fastapi_authly import setup_scalar_docs
setup_scalar_docs(app, docs_url="/docs", static_url="/static")
```

### Advanced Usage (custom implementations)

```python
from fastapi_authly import AuthConfig, AuthDependencyConfig, create_auth_router
from fastapi_authly.interfaces import UserRepository, Mailer

class MyRepo(UserRepository):
    async def get_by_name(self, username: str): ...
    async def get_by_id(self, user_id: str | int): ...
    async def create_user(self, user): ...
    async def to_public(self, user): ...

class MyMailer(Mailer):
    async def send_password_reset(self, request, token): ...
    async def send_verification(self, email, token): ...

config = AuthConfig(router_prefix="/api/auth", token_url="login")
deps = AuthDependencyConfig(
    user_repository=MyRepo(),
    mailer=MyMailer(),
)
auth_router = create_auth_router(config=config, dependencies=deps)
```

## 📚 API Documentation

`fastapi-authly` includes built-in Scalar API documentation support with all necessary static resources:

```python
from fastapi import FastAPI
from fastapi_authly import setup_scalar_docs

app = FastAPI(title="My API")

# One line to enable Scalar documentation
# Automatically mounts static files to /static and creates docs page at /docs
setup_scalar_docs(app)

# Custom configuration
setup_scalar_docs(
    app,
    docs_url="/api-docs",      # Custom docs URL
    static_url="/assets",      # Custom static files prefix
    title="Custom API Docs",   # Custom title
    openapi_url="/openapi.json" # Custom OpenAPI schema URL
)
```

## 📋 API Endpoints

### Authentication
- `POST /auth/login` - Login and get access token (+optional refresh)
- `POST /auth/token/verify` - Verify token validity
- `POST /auth/token/refresh` - Refresh access token

### User Management
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user info

### Password Management
- `POST /auth/password/reset-request` - Request password reset
- `POST /auth/password/reset` - Reset password with token

## 🔧 Configuration

### AuthConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `secret_key` | `str` | `"your-secret-key-change-in-production"` | JWT secret key |
| `algorithm` | `str` | `"HS256"` | JWT algorithm |
| `access_token_expire_minutes` | `int` | `30` | Access token expiration |
| `refresh_token_expire_days` | `int` | `7` | Refresh token expiration |
| `router_prefix` | `str` | `"/auth"` | API route prefix |
| `router_tags` | `List[str]` | `["authentication"]` | API tags |
| `token_url` | `str` | `"token"` | OAuth2 token path (set to `"login"` to match default route) |
| `enable_password_recovery` | `bool` | `True` | Enable password recovery |
| `enable_user_registration` | `bool` | `True` | Enable user registration |
| `enable_token_refresh` | `bool` | `True` | Enable token refresh |
| `enable_html_content` | `bool` | `True` | Allow HTML in responses |
| `email_from` | `str` | `"noreply@example.com"` | Email sender |
| `email_from_name` | `str` | `"Auth System"` | Email sender name |
| `password_reset_url_template` | `str` | Template URL | Password reset URL |
| `verification_url_template` | `str` | Template URL | Email verification URL |

## 🏗️ Architecture

```
fastapi_authly/
├── auth.py                    # Main authentication module (routes)
├── schemas/                   # Pydantic schemas (request/response models)
│   └── user.py
├── models/                    # DB models (e.g., Tortoise ORM)
│   └── user.py
├── contrib/
│   └── tortoise_pg.py         # Default Tortoise Postgres repository
├── core/                      # Core functionality
│   ├── config.py              # Settings & dependency container
│   ├── security.py            # Token + password utilities
│   └── __init__.py
├── interfaces.py              # Protocols (UserRepository, Mailer, etc.)
├── __init__.py                # Package exports
└── __about__.py               # Version info
```

## 🔌 Integration Examples

```python
# FastAPI + Tortoise + Postgres (default repo)
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi_authly import AuthConfig, AuthDependencyConfig, create_auth_router
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository

app = FastAPI()

register_tortoise(
    app,
    db_url="postgres://user:password@localhost:5432/mydb",
    modules={"models": ["fastapi_authly.models.user"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

config = AuthConfig(token_url="login")
deps = AuthDependencyConfig(user_repository=TortoiseUserRepository())
app.include_router(create_auth_router(config=config, dependencies=deps))
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [python-jose](https://python-jose.readthedocs.io/) - JWT implementation
- [passlib](https://passlib.readthedocs.io/) - Password hashing

## 📞 Support

If you have any questions or need help:

- 💬 GitHub Issues: [Create an issue](https://github.com/yourusername/fastapi-authly/issues)
- 📖 Documentation: [Read the docs](https://yourusername.github.io/fastapi-authly/)
