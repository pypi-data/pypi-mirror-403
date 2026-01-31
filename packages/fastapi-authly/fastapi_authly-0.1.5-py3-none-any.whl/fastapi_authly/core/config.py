"""Configuration settings for fastapi-authly."""

from typing import List, Optional, Any, Union
from datetime import timedelta
from pydantic import BaseModel, Field, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class JwtConfig(BaseModel):
    secret_key: str = "xxx"
    algorithm: str = "HS256"
    scheme: str = "JWT"
    token_expires_time: str = "1200"  # seconds, legacy name
    access_token_expires_minutes: int | None = None
    refresh_token_expires_days: int = 7

    @property
    def access_expires(self) -> timedelta:
        """Preferred access token expiry."""
        if self.access_token_expires_minutes is not None:
            return timedelta(minutes=self.access_token_expires_minutes)
        # fallback to legacy seconds-based setting
        return timedelta(seconds=int(self.token_expires_time))

    @property
    def refresh_expires(self) -> timedelta:
        return timedelta(days=self.refresh_token_expires_days)


class AuthConfig(BaseSettings):
    """
    Runtime configuration loaded from environment variables with ``AUTH_`` prefix.

    Host applications can still pass an ``AuthConfig`` instance directly;
    in that case, the passed values override the environment values.
    """
    jwt: Union[JwtConfig, dict] = Field(default_factory=JwtConfig)

    router_prefix: str = "/auth"
    router_tags: List[str] = Field(default_factory=lambda: ["authentication"])
    token_url: str = "login"  # OAuth2 token URL path

    enable_password_recovery: bool = True
    enable_user_registration: bool = True
    enable_token_refresh: bool = True
    enable_html_content: bool = True

    email_from: str = "noreply@example.com"
    email_from_name: str = "Auth System"
    password_reset_url_template: str = (
        "https://yourapp.com/reset-password?token={token}"
    )
    verification_url_template: str = (
        "https://yourapp.com/verify-email?token={token}"
    )

    model_config = SettingsConfigDict(
        env_prefix="AUTH_",
        extra="ignore",
    )
    
    @model_validator(mode='after')
    def _ensure_jwt_is_config(self):
        """确保 jwt 字段始终是 JwtConfig 实例"""
        if isinstance(self.jwt, dict):
            self.jwt = JwtConfig(**self.jwt)
        elif not isinstance(self.jwt, JwtConfig):
            self.jwt = JwtConfig()
        return self
    
    def _ensure_jwt_config(self) -> JwtConfig:
        """确保 jwt 是 JwtConfig 实例，如果不是则转换"""
        if isinstance(self.jwt, dict):
            self.jwt = JwtConfig(**self.jwt)
        elif not isinstance(self.jwt, JwtConfig):
            self.jwt = JwtConfig()
        return self.jwt
    
    # 属性访问器：直接访问 jwt 中的属性，兼容现有代码
    @property
    def secret_key(self) -> str:
        """JWT secret key"""
        jwt_config = self._ensure_jwt_config()
        return jwt_config.secret_key
    
    @property
    def algorithm(self) -> str:
        """JWT algorithm"""
        jwt_config = self._ensure_jwt_config()
        return jwt_config.algorithm
    
    @property
    def access_token_expire_minutes(self) -> Optional[int]:
        """Access token expiration in minutes (compatible with auth.py)"""
        jwt_config = self._ensure_jwt_config()
        return jwt_config.access_token_expires_minutes
    
    @property
    def refresh_token_expire_days(self) -> int:
        """Refresh token expiration in days"""
        jwt_config = self._ensure_jwt_config()
        return jwt_config.refresh_token_expires_days

_config = AuthConfig()

class AuthDependencyConfig(BaseModel):
    """
    Optional dependency injection container.

    Host projects can supply custom implementations for the overridable hooks.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_repository: Optional[Any] = None
    password_hasher: Optional[Any] = None
    token_service: Optional[Any] = None
    mailer: Optional[Any] = None
    # 可选：自定义 token 提取依赖（例如自定义 Bearer/JWT 解析）
    # token_dependency: Optional[Any] = Noneptional[Any] = None
    # 可选：自定义 token 提取依赖（例如自定义 Bearer/JWT 解析）
    token_dependency: Optional[Any] = None