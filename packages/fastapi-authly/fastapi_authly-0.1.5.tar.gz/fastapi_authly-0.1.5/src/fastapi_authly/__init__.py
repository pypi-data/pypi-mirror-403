"""
FastAPI Auth Module - A modular authentication system for FastAPI

This package provides a complete authentication solution with:
- OAuth2 password flow
- JWT token management
- Password recovery
- User management
- Modular and configurable design
- Built-in Scalar API documentation
"""

from .auth import AuthModule, create_auth_router
from .core import AuthConfig, AuthDependencyConfig, JwtConfig, BcryptPasswordHasher, JWTTokenService
from .docs import setup_scalar_docs
from .interfaces import Mailer, PasswordHasher, TokenService, UserRepository
from .schemas.user import UserBase, UserCreate, UserUpdate, UserPublic, Token, TokenData

# ECharts 截图（需安装 fastapi-authly[charts] 以使用）
from .charts import (
    build_option,
    echarts_option_to_html,
    engine_make_snapshot,
    get_driver,
    render_chart_to_png,
    render_option_to_png,
)

__version__ = "0.1.1"

__all__ = [
    # Main classes
    "AuthModule",
    "AuthConfig",
    "AuthDependencyConfig",
    "JwtConfig",

    # Core functions
    "create_auth_router",
    "setup_scalar_docs",

    # Security utilities
    "BcryptPasswordHasher",
    "JWTTokenService",

    # Interfaces
    "PasswordHasher",
    "TokenService",
    "Mailer",
    "UserRepository",

    # Models
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
    "Token",
    "TokenData",

    # ECharts 图表截图
    "build_option",
    "echarts_option_to_html",
    "engine_make_snapshot",
    "get_driver",
    "render_chart_to_png",
    "render_option_to_png",
]
