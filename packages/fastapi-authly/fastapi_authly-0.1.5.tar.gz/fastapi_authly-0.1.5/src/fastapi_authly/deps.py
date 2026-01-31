from typing import Annotated, Optional, List
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, ValidationError
from .core.config import _config
from .models.user import User


class FlexibleHTTPBearer(HTTPBearer):
    """支持自定义 scheme 的 HTTP Bearer"""

    def __init__(
            self,
            *,
            accepted_schemes: Optional[List[str]] = None,
            scheme_name: Optional[str] = None,
            auto_error: bool = True,
    ):
        self.accepted_schemes_lower = [
            s.lower() for s in (accepted_schemes or ["bearer", "jwt"])
        ]
        super().__init__(
            scheme_name=scheme_name or "Bearer/JWT",
            auto_error=auto_error,
        )

    async def __call__(
            self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)

        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            return None

        if scheme.lower() not in self.accepted_schemes_lower:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid auth scheme. Accepted: {', '.join(self.accepted_schemes_lower)}",
                )
            return None

        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


jwt_scheme = FlexibleHTTPBearer(
    accepted_schemes=["bearer", "jwt"],  # 可以改成 ["bearer"] 或 ["jwt"]
    auto_error=True
)

class TokenPayload(BaseModel):
    """
    JWT 载荷模型
    - sub: 用户 ID
    - type: 令牌类型（access/refresh），旧 token 可能缺少
    - exp/nbf 等字段由 jwt 库自行校验
    """

    sub: int
    type: str | None = None

async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    scheme = credentials.scheme  # "Bearer" / "JWT"
    token = credentials.credentials

    if scheme.lower() not in ("bearer", "jwt"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid auth scheme. Expected 'Bearer' or 'JWT', got '{scheme}'",
        )
    return token

TokenDep = Annotated[str, Depends(get_token)]

async def get_current_user(token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token,
            _config.jwt.secret_key,
            algorithms=[_config.jwt.algorithm],
        )
        token_data = TokenPayload(**payload)
        if token_data.type and token_data.type != "access":
            raise InvalidTokenError("Invalid token type")
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = await User.get_or_none(id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user