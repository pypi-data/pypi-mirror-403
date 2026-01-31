"""认证模块 - 提供可重写的 FastAPI 路由集合。"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import EmailStr

from .core.config import AuthConfig, AuthDependencyConfig, _config
from .core.security import BcryptPasswordHasher, JWTTokenService
from .interfaces import Mailer, PasswordHasher, TokenService, UserRepository
from .schemas.user import (
    PasswordReset,
    PasswordResetRequest,
    Token,
    TokenData,
    UserCreate,
    UserPublic,
    UserLogin
)
from fastapi_authly.contrib.tortoise_pg import TortoiseUserRepository


def _merge_config(config: Optional[AuthConfig]) -> AuthConfig:
    """Environment-driven config, overridden by user-supplied config when provided."""
    if config is None:
        return _config
    return _config.model_copy(update=config.model_dump(exclude_none=True))


class AuthModule:
    """认证模块：默认实现最小逻辑，所有外部依赖均可替换。"""

    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        dependencies: Optional[AuthDependencyConfig] = None,
    ):
        self.config = _merge_config(config)
        self.dependencies = dependencies or AuthDependencyConfig()

        self.password_hasher: PasswordHasher = (
            self.dependencies.password_hasher or BcryptPasswordHasher()
        )
        self.token_service: TokenService = (
            self.dependencies.token_service
            or JWTTokenService(
                secret_key=self.config.secret_key,
                algorithm=self.config.algorithm,
                access_token_expire_minutes=self.config.access_token_expire_minutes,
                refresh_token_expire_days=self.config.refresh_token_expire_days,
            )
        )
        self.user_repository = (
                self.dependencies.user_repository
                or TortoiseUserRepository()
        )

        self.mailer: Optional[Mailer] = self.dependencies.mailer

        self.router = APIRouter(
            prefix=self.config.router_prefix, tags=self.config.router_tags
        )
        # token 提取依赖：默认使用 OAuth2PasswordBearer，可通过 AuthDependencyConfig.token_dependency 覆盖
        self.token_dependency = (
            self.dependencies.token_dependency
            or OAuth2PasswordBearer(
                tokenUrl=f"{self.config.router_prefix.rstrip('/')}/{self.config.token_url}".strip(
                    "/"
                )
            )
        )

        self._setup_routes()

    def _setup_routes(self) -> None:
        self._add_token_routes()
        if self.config.enable_user_registration:
            self._add_user_routes()
        if self.config.enable_password_recovery:
            self._add_password_routes()
        if self.config.enable_token_refresh:
            self._add_refresh_routes()

    def _ensure_user_repo(self) -> UserRepository:
        if not self.user_repository:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="User repository not provided. Supply a UserRepository implementation.",
            )
        return self.user_repository

    def _add_token_routes(self) -> None:
        @self.router.post("/login", response_model=Token)
        async def login_for_access_token(
            body: UserLogin,
        ) -> Token:
            repo = self._ensure_user_repo()
            user = await repo.get_by_name(body.username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect username or password",
                )

            hashed_password = getattr(user, "hashed_password", None) or ""
            if not hashed_password or not self.password_hasher.verify(body.password, hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect username or password",
                )
                
            if not user.is_active:
                raise HTTPException(status_code=400, detail="Inactive user")

            user_id = str(getattr(user, "id", ""))
            access_token = self.token_service.create_access_token(user_id)
            refresh_token = (
                self.token_service.create_refresh_token(user_id)
                if self.config.enable_token_refresh
                else None
            )
            return Token(access_token=access_token, refresh_token=refresh_token)

        @self.router.post("/token/verify")
        async def verify_token(token: str = Depends(self.token_dependency)) -> Dict[str, Any]:
            try:
                payload = self.token_service.decode_token(token)
                token_data = TokenData(**payload)
                return {"valid": True, "user_id": token_data.sub, "exp": token_data.exp}
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    def _add_user_routes(self) -> None:
        @self.router.post("/register", response_model=UserPublic)
        async def register_user(user: UserCreate) -> UserPublic:
            repo = self._ensure_user_repo()
            hashed_pw = self.password_hasher.hash(user.password)
            user_to_create = user.model_copy(update={"password": hashed_pw})
            created = await repo.create_user(user_to_create)
            return await repo.to_public(created)

        @self.router.get("/me", response_model=UserPublic)
        async def get_current_user(token: str = Depends(self.token_dependency)) -> UserPublic:
            repo = self._ensure_user_repo()
            try:
                payload = self.token_service.decode_token(token, verify_type="access")
                token_data = TokenData(**payload)
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user = await repo.get_by_id(token_data.sub)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return await repo.to_public(user)

    def _add_password_routes(self) -> None:
        @self.router.post("/password/reset-request")
        async def request_password_reset(request: PasswordResetRequest) -> Dict[str, str]:
            repo = self._ensure_user_repo()
            if not self.mailer:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Mailer not provided. Supply a Mailer implementation.",
                )

            user = await repo.get_by_email(request.email)
            if not user:
                # Intentionally return generic message
                return {"detail": "If the account exists, a reset email will be sent."}

            token = self.token_service.create_refresh_token(str(getattr(user, "id", "")))
            await self.mailer.send_password_reset(request, token)
            return {"detail": "If the account exists, a reset email will be sent."}

        @self.router.post("/password/reset")
        async def reset_password(payload: PasswordReset) -> Dict[str, str]:
            repo = self._ensure_user_repo()
            try:
                data = self.token_service.decode_token(payload.token)
                user_id = data.get("sub")
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired token",
                )

            user = await repo.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            hashed = self.password_hasher.hash(payload.new_password)

            if hasattr(repo, "update_password"):
                await getattr(repo, "update_password")(user_id, hashed)  # type: ignore[attr-defined]
                return {"detail": "Password updated"}

            if hasattr(user, "set_password"):
                user.set_password(hashed)
                return {"detail": "Password updated"}

            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Provide `update_password` on UserRepository or `set_password` on user model.",
            )

    def _add_refresh_routes(self) -> None:
        @self.router.post("/token/refresh", response_model=Token)
        async def refresh_access_token(refresh_token: str) -> Token:
            try:
                payload = self.token_service.decode_token(refresh_token, verify_type="refresh")
                user_id = payload.get("sub")
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token = self.token_service.create_access_token(user_id)
            return Token(access_token=access_token, token_type="bearer")

    def get_router(self) -> APIRouter:
        return self.router


def create_auth_router(
    *,
    config: Optional[AuthConfig] = None,
    dependencies: Optional[AuthDependencyConfig] = None,
) -> APIRouter:
    """便捷函数：构建可配置的认证路由器。"""
    module = AuthModule(config=config, dependencies=dependencies)
    return module.get_router()
