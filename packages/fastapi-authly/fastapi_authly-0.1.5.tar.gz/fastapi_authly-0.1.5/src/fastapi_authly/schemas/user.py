"""Data models for FastAPI Auth Module."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import EmailStr
from pydantic import ConfigDict, Field
from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False



class UserCreate(UserBase):
    """用户创建模型"""
    password: str


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserPublic(UserBase):
    """用户公开模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """ 用户登录传参模型 """
    username: str
    password: str
    meta: Optional[Dict[str, Any]] = Field(default=None)

class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """令牌数据模型"""
    sub: str
    exp: Optional[datetime] = None


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr


class PasswordReset(BaseModel):
    """密码重置模型"""
    token: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    """邮件验证请求模型"""
    email: EmailStr


class EmailVerification(BaseModel):
    """邮件验证模型"""
    token: str
