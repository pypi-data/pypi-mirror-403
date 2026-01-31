# -*- coding: utf-8 -*-
"""API Key 相关的 Pydantic Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class APIKeyCreate(BaseModel):
    """创建 API Key Schema"""

    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    scopes: Optional[List[str]] = Field(None, description="权限范围")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class APIKeyUpdate(BaseModel):
    """更新 API Key Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="密钥名称")
    scopes: Optional[List[str]] = Field(None, description="权限范围")
    is_active: Optional[bool] = Field(None, description="是否激活")


class APIKeyResponse(BaseModel):
    """API Key 响应 Schema（不包含敏感信息）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    user_id: Optional[int]
    name: str
    key_prefix: str
    scopes: Optional[List[str]]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


class APIKeyCreateResponse(BaseModel):
    """创建 API Key 响应 Schema（包含完整密钥，仅返回一次）"""

    id: int
    tenant_id: int
    user_id: Optional[int]
    name: str
    api_key: str = Field(..., description="完整 API Key（仅显示一次，请妥善保存）")
    key_prefix: str
    scopes: Optional[List[str]]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime


class APIKeyListResponse(BaseModel):
    """API Key 列表响应 Schema"""

    total: int
    api_keys: List[APIKeyResponse]


class APIKeyVerifyRequest(BaseModel):
    """验证 API Key 请求 Schema"""

    api_key: str = Field(..., description="要验证的 API Key")


class APIKeyVerifyResponse(BaseModel):
    """验证 API Key 响应 Schema"""

    valid: bool = Field(..., description="是否有效")
    api_key: Optional[Dict[str, Any]] = Field(None, description="API Key 信息（如果有效）")
    error: Optional[str] = Field(None, description="错误信息（如果无效）")
