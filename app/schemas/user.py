from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr, Field


# 注册请求 Schema
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str = Field(..., min_length=6, max_length=128)


# 注册成功返回 Schema
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    is_active: bool

    class Config:
        from_attributes = True


# 登录请求 Schema
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserDetail(BaseModel):
    id: int
    username: str
    email: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True  # SQLAlchemy ORM 转 Pydantic（非常关键）
