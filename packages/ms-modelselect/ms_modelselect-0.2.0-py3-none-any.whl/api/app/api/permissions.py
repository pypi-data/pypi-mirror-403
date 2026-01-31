# -*- coding: utf-8 -*-
"""权限管理 API 路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.database import get_db
from app.models import Permission, RolePermission, UserRole
from app.schemas.user import UserResponse
from app.schemas.permission import (
    PermissionResponse,
    RolePermissionResponse,
    UserRoleResponse,
    GrantRoleRequest,
    UserPermissionsResponse,
)
from app.utils.deps import get_current_user, get_current_tenant, require_admin
from app.utils.permissions import (
    permission_checker,
    grant_role_to_user,
    revoke_role_from_user,
    get_user_roles,
)

router = APIRouter()


@router.get("/permissions", response_model=List[PermissionResponse], summary="获取所有权限")
async def list_permissions(
    category: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取所有权限列表

    Args:
        category: 权限分类筛选（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        List[PermissionResponse]: 权限列表
    """
    query = select(Permission)

    if category:
        query = query.where(Permission.category == category)

    result = await db.execute(query)
    permissions = result.scalars().all()

    return permissions


@router.get("/roles/permissions", response_model=List[RolePermissionResponse], summary="获取角色权限映射")
async def get_role_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取所有角色的权限映射

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        List[RolePermissionResponse]: 角色权限映射列表
    """
    # 获取所有角色
    roles = ["admin", "user", "viewer"]
    result_data = []

    for role in roles:
        # 查询角色的权限
        result = await db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role == role)
        )
        permissions = result.scalars().all()

        result_data.append({
            "role": role,
            "permissions": list(permissions)
        })

    return result_data


@router.get("/users/me/permissions", response_model=UserPermissionsResponse, summary="获取当前用户权限")
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取当前用户的角色和权限

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        UserPermissionsResponse: 用户权限信息
    """
    # 获取用户角色
    roles = await get_user_roles(db, current_user.id)

    # 获取用户权限
    permissions = await permission_checker.get_user_permissions(db, current_user.id)

    return UserPermissionsResponse(
        user_id=current_user.id,
        roles=roles,
        permissions=list(permissions),
    )


@router.get("/users/{user_id}/roles", response_model=List[UserRoleResponse], summary="获取用户角色")
async def get_user_roles_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取指定用户的角色列表（仅管理员）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户（需管理员权限）
        current_tenant: 当前租户

    Returns:
        List[UserRoleResponse]: 用户角色列表
    """
    # 查询用户角色
    result = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id)
    )
    user_roles = result.scalars().all()

    return user_roles


@router.post("/users/{user_id}/roles", response_model=UserRoleResponse, summary="授予用户角色")
async def grant_role(
    user_id: int,
    role_data: GrantRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    为用户授予角色（仅管理员）

    Args:
        user_id: 用户ID
        role_data: 角色数据
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Returns:
        UserRoleResponse: 创建的用户角色

    Raises:
        HTTPException: 授权失败
    """
    # 验证角色名称
    valid_roles = ["admin", "user", "viewer"]
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    # 授予角色
    await grant_role_to_user(
        db=db,
        user_id=user_id,
        role=role_data.role,
        granted_by=current_user.id,
        expires_at=role_data.expires_at,
    )

    await db.commit()

    # 查询并返回创建的用户角色
    result = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role == role_data.role,
            )
        )
    )
    user_role = result.scalar_one()

    return user_role


@router.delete("/users/{user_id}/roles/{role}", status_code=status.HTTP_204_NO_CONTENT, summary="撤销用户角色")
async def revoke_role(
    user_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    撤销用户的角色（仅管理员）

    Args:
        user_id: 用户ID
        role: 角色名称
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Raises:
        HTTPException: 撤销失败
    """
    # 验证角色名称
    valid_roles = ["admin", "user", "viewer"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    # 撤销角色
    await revoke_role_from_user(
        db=db,
        user_id=user_id,
        role=role,
    )

    await db.commit()
