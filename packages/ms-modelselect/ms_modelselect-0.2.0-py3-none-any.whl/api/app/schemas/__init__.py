# -*- coding: utf-8 -*-
"""Pydantic Schemas"""

from .tenant import TenantCreate, TenantUpdate, TenantResponse, TenantInDB
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserLogin,
    Token,
    TokenPayload,
)
from .task import (
    EvaluationTaskCreate,
    EvaluationTaskUpdate,
    EvaluationTaskResponse,
    EvaluationResultResponse,
    TaskStatistics,
)
from .permission import (
    PermissionResponse,
    RolePermissionResponse,
    UserRoleResponse,
    GrantRoleRequest,
    UserPermissionsResponse,
)

__all__ = [
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantInDB",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserLogin",
    "Token",
    "TokenPayload",
    "EvaluationTaskCreate",
    "EvaluationTaskUpdate",
    "EvaluationTaskResponse",
    "EvaluationResultResponse",
    "TaskStatistics",
    "PermissionResponse",
    "RolePermissionResponse",
    "UserRoleResponse",
    "GrantRoleRequest",
    "UserPermissionsResponse",
]
