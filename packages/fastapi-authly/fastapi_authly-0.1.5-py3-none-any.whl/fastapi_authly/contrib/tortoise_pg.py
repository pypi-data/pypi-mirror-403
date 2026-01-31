# fastapi_authly.contrib.tortoise_pg
from typing import Any, Optional

from tortoise.exceptions import DoesNotExist
from ..interfaces import UserRepository
from ..schemas.user import UserCreate, UserPublic
from ..models.user import User


class TortoiseUserRepository(UserRepository):
    async def get_by_name(self, username: str) -> Optional[User]:
        try:
            return await User.get(username=username)
        except DoesNotExist:
            return None

    async def get_by_id(self, user_id: str | int) -> Optional[User]:
        try:
            return await User.get(id=int(user_id))
        except DoesNotExist:
            return None

    async def create_user(self, user: UserCreate) -> User:
        obj = await User.create(
            username=user.username,
            email=user.email,
            hashed_password=user.password,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        )
        return obj

    async def to_public(self, user: User) -> UserPublic:
        return UserPublic.model_validate(user)