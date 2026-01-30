"""Configuration settings for fastapi-authly."""

from typing import List, Optional, Any
from datetime import timedelta
from pydantic import BaseModel, Field, ConfigDict
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
    jwt: JwtConfig = JwtConfig()

    router_prefix: str = "/auth"
    router_tags: List[str] = Field(default_factory=lambda: ["authentication"])

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
    token_dependency: Optional[Any] = None