# -*- coding: utf-8 -*-
"""租户相关的 Pydantic Schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class TenantBase(BaseModel):
    """租户基础 Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    code: str = Field(..., min_length=1, max_length=50, description="租户代码")
    plan: str = Field(default="free", description="订阅计划")


class TenantCreate(TenantBase):
    """创建租户 Schema"""

    max_users: Optional[int] = Field(None, description="最大用户数")
    max_api_calls_per_day: Optional[int] = Field(None, description="每日最大API调用次数")
    max_storage_gb: Optional[Decimal] = Field(None, description="最大存储空间(GB)")
    expired_at: Optional[datetime] = Field(None, description="订阅过期时间")
    settings: Optional[Dict[str, Any]] = Field(None, description="租户配置")


class TenantUpdate(BaseModel):
    """更新租户 Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="租户名称")
    status: Optional[str] = Field(None, description="租户状态")
    plan: Optional[str] = Field(None, description="订阅计划")
    max_users: Optional[int] = Field(None, description="最大用户数")
    max_api_calls_per_day: Optional[int] = Field(None, description="每日最大API调用次数")
    max_storage_gb: Optional[Decimal] = Field(None, description="最大存储空间(GB)")
    expired_at: Optional[datetime] = Field(None, description="订阅过期时间")
    settings: Optional[Dict[str, Any]] = Field(None, description="租户配置")


class TenantResponse(TenantBase):
    """租户响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    max_users: int
    max_api_calls_per_day: int
    max_storage_gb: Decimal
    expired_at: Optional[datetime]
    settings: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class TenantInDB(TenantResponse):
    """数据库中的租户 Schema"""

    pass
