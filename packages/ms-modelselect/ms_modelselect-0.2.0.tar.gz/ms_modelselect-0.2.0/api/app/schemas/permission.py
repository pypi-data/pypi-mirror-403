# -*- coding: utf-8 -*-
"""权限相关的 Pydantic Schemas"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PermissionResponse(BaseModel):
    """权限响应 Schema"""

    id: int
    code: str
    name: str
    description: Optional[str]
    resource: str
    action: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RolePermissionResponse(BaseModel):
    """角色权限响应 Schema"""

    role: str
    permissions: List[PermissionResponse]


class UserRoleResponse(BaseModel):
    """用户角色响应 Schema"""

    id: int
    user_id: int
    role: str
    granted_by: Optional[int]
    granted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class GrantRoleRequest(BaseModel):
    """授予角色请求 Schema"""

    role: str = Field(..., description="角色名称（admin/user/viewer）")
    expires_at: Optional[datetime] = Field(None, description="过期时间（可选）")


class UserPermissionsResponse(BaseModel):
    """用户权限响应 Schema"""

    user_id: int
    roles: List[str]
    permissions: List[str]
