"""
FastAPI Auth Module - A modular authentication system for FastAPI

This package provides a complete authentication solution with:
- OAuth2 password flow
- JWT token management
- Password recovery
- User management
- Modular and configurable design
"""

from .auth import AuthModule, create_auth_router
from .core import AuthConfig, AuthDependencyConfig, BcryptPasswordHasher, JWTTokenService
from .docs import setup_scalar_docs
from .interfaces import Mailer, PasswordHasher, TokenService, UserRepository
from .schemas.user import UserBase, UserCreate, UserUpdate, UserPublic, Token, TokenData

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "AuthModule",
    "AuthConfig",
    "AuthDependencyConfig",

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
]
