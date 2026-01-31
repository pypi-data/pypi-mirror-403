# -*- coding: utf-8 -*-
"""用户相关的 Pydantic Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    """用户基础 Schema"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """创建用户 Schema"""

    password: str = Field(..., min_length=6, max_length=100, description="密码")
    role: Optional[str] = Field(default="user", description="用户角色")


class UserUpdate(BaseModel):
    """更新用户 Schema"""

    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="密码")
    role: Optional[str] = Field(None, description="用户角色")
    status: Optional[str] = Field(None, description="用户状态")
    avatar: Optional[str] = Field(None, description="头像URL")


class UserResponse(UserBase):
    """用户响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    role: str
    status: str
    avatar: Optional[str]
    last_login_at: Optional[datetime]
    created_at: datetime


class UserLogin(BaseModel):
    """用户登录 Schema"""

    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")
    tenant_code: Optional[str] = Field(None, description="租户代码")


class UserInDB(UserResponse):
    """数据库中的用户 Schema"""

    password_hash: str


class Token(BaseModel):
    """JWT Token 响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT Token 载荷"""

    sub: str  # 用户ID (字符串类型,JWT要求)
    tenant_id: int  # 租户ID
    exp: Optional[int] = None
    type: Optional[str] = None  # Token类型 (access/refresh)
