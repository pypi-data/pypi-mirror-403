"""Overridable interfaces for fastapi-authly."""

from __future__ import annotations

from typing import Any, Awaitable, Protocol

from .schemas.user import PasswordReset, PasswordResetRequest, UserBase, UserCreate, UserPublic


class PasswordHasher(Protocol):
    """Interface for password hashing and verification."""

    def hash(self, password: str) -> str:
        ...

    def verify(self, password: str, hashed: str) -> bool:
        ...


class TokenService(Protocol):
    """Interface for issuing and validating tokens."""

    def create_access_token(self, subject: str) -> str:
        ...

    def create_refresh_token(self, subject: str) -> str:
        ...

    def decode_token(self, token: str, verify_type: str | None = None) -> dict[str, Any]:
        ...


class Mailer(Protocol):
    """Interface for delivering email notifications."""

    async def send_password_reset(self, request: PasswordResetRequest, token: str) -> Any:
        ...

    async def send_verification(self, email: str, token: str) -> Any:
        ...


class UserRepository(Protocol):
    """Interface for user persistence operations."""

    async def get_by_name(self, email: str) -> Any:
        ...

    async def get_by_id(self, user_id: str | int) -> Any:
        ...

    async def create_user(self, user: UserCreate) -> Any:
        ...

    async def to_public(self, user: Any) -> UserPublic:
        ...
