from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from ..interfaces import PasswordHasher, TokenService


class BcryptPasswordHasher(PasswordHasher):
    """Default bcrypt-based password hasher."""

    def __init__(self) -> None:
        # pbkdf2_sha256 avoids platform-specific bcrypt backend issues
        self._ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        if not hashed:
            return False
        try:
            return self._ctx.verify(password, hashed)
        except UnknownHashError:
            # 如果哈希格式无法识别，返回 False
            return False


class JWTTokenService(TokenService):
    """Default JWT token service using python-jose."""

    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str,
        access_token_expire_minutes: int,
        refresh_token_expire_days: int,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)

    def _create_token(self, subject: str | Any, expires_delta: timedelta, token_type: str) -> str:
        expire = datetime.now() + expires_delta
        to_encode: Dict[str, Any] = {
            "exp": expire,
            "sub": str(subject),
            "type": token_type,
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, subject: str | Any) -> str:
        return self._create_token(subject, self.access_token_expire, token_type="access")

    def create_refresh_token(self, subject: str | Any) -> str:
        return self._create_token(subject, self.refresh_token_expire, token_type="refresh")

    def decode_token(self, token: str, verify_type: Optional[str] = None) -> Dict[str, Any]:
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        if verify_type and payload.get("type") != verify_type:
            raise JWTError("Invalid token type")
        return payload
