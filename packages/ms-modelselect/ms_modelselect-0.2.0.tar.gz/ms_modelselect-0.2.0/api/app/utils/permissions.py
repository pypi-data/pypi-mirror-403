# -*- coding: utf-8 -*-
"""RBAC 权限管理工具"""

from datetime import datetime
from typing import List, Optional, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import User, Permission, RolePermission, UserRole
from app.utils.deps import get_current_user
from loguru import logger


class PermissionChecker:
    """权限检查器类"""

    def __init__(self):
        self._permission_cache = {}  # 权限缓存 {user_id: set(permission_codes)}

    async def get_user_permissions(
        self,
        db: AsyncSession,
        user_id: int,
        use_cache: bool = True,
    ) -> Set[str]:
        """
        获取用户的所有权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            use_cache: 是否使用缓存

        Returns:
            Set[str]: 用户权限代码集合
        """
        # 检查缓存
        if use_cache and user_id in self._permission_cache:
            return self._permission_cache[user_id]

        # 查询用户的所有角色
        user_roles_result = await db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        user_roles = user_roles_result.scalars().all()

        # 如果用户没有角色，返回空权限
        if not user_roles:
            return set()

        # 获取角色列表
        roles = [ur.role for ur in user_roles]

        # 查询这些角色的所有权限
        permissions_result = await db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role.in_(roles))
        )
        permissions = permissions_result.scalars().all()

        # 提取权限代码
        permission_codes = {p.code for p in permissions}

        # 缓存权限
        if use_cache:
            self._permission_cache[user_id] = permission_codes

        return permission_codes

    async def clear_user_cache(self, user_id: int):
        """清除用户权限缓存"""
        if user_id in self._permission_cache:
            del self._permission_cache[user_id]

    async def has_permission(
        self,
        db: AsyncSession,
        user: User,
        permission_code: str,
    ) -> bool:
        """
        检查用户是否拥有指定权限

        Args:
            db: 数据库会话
            user: 用户对象
            permission_code: 权限代码（如 "tenant.create"）

        Returns:
            bool: 是否有权限
        """
        # admin 角色拥有所有权限（通配符）
        # 兼容旧的 users.role 字段
        if user.role == "admin":
            return True

        # 检查 user_roles 表中的角色
        permissions = await self.get_user_permissions(db, user.id)

        # 检查是否有通配符权限（system.manage）
        if "system.manage" in permissions or "*" in permissions:
            return True

        # 检查具体权限
        return permission_code in permissions

    async def has_any_permission(
        self,
        db: AsyncSession,
        user: User,
        permission_codes: List[str],
    ) -> bool:
        """
        检查用户是否拥有任一指定权限

        Args:
            db: 数据库会话
            user: 用户对象
            permission_codes: 权限代码列表

        Returns:
            bool: 是否有任一权限
        """
        for perm in permission_codes:
            if await self.has_permission(db, user, perm):
                return True
        return False

    async def has_all_permissions(
        self,
        db: AsyncSession,
        user: User,
        permission_codes: List[str],
    ) -> bool:
        """
        检查用户是否拥有所有指定权限

        Args:
            db: 数据库会话
            user: 用户对象
            permission_codes: 权限代码列表

        Returns:
            bool: 是否有所有权限
        """
        for perm in permission_codes:
            if not await self.has_permission(db, user, perm):
                return False
        return True


# 全局权限检查器实例
permission_checker = PermissionChecker()


def require_permission(permission_code: str):
    """
    要求特定权限的依赖注入装饰器

    Args:
        permission_code: 权限代码（如 "tenant.create"）

    Returns:
        依赖注入函数

    Example:
        @router.post("/tenants")
        async def create_tenant(
            current_user: User = Depends(require_permission("tenant.create"))
        ):
            ...
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 检查权限
        has_perm = await permission_checker.has_permission(db, current_user, permission_code)

        if not has_perm:
            logger.warning(
                f"User {current_user.id} (role: {current_user.role}) "
                f"denied access to permission: {permission_code}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code} required",
            )

        return current_user


def require_any_permission(*permission_codes: str):
    """
    要求任一权限的依赖注入装饰器

    Args:
        *permission_codes: 权限代码列表

    Returns:
        依赖注入函数

    Example:
        @router.put("/users/{id}")
        async def update_user(
            current_user: User = Depends(
                require_any_permission("user.update", "user.update.self")
            )
        ):
            ...
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 检查是否拥有任一权限
        has_perm = await permission_checker.has_any_permission(
            db, current_user, list(permission_codes)
        )

        if not has_perm:
            logger.warning(
                f"User {current_user.id} (role: {current_user.role}) "
                f"denied access to permissions: {permission_codes}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: one of {permission_codes} required",
            )

        return current_user


def require_resource_ownership(resource_type: str, resource_id_param: str = "id"):
    """
    要求资源所有权或管理权限的装饰器

    Args:
        resource_type: 资源类型（如 "task", "user"）
        resource_id_param: 资源ID参数名

    Returns:
        依赖注入函数

    Example:
        @router.delete("/tasks/{task_id}")
        async def delete_task(
            task_id: int,
            current_user: User = Depends(
                require_resource_ownership("task", "task_id")
            )
        ):
            ...
    """
    async def check_ownership(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # admin 绕过所有权检查
        if current_user.role == "admin":
            return current_user

        # TODO: 实现资源所有权检查
        # 需要根据 resource_type 和 resource_id_param 查询资源
        # 并检查 resource.user_id == current_user.id

        return current_user


async def grant_role_to_user(
    db: AsyncSession,
    user_id: int,
    role: str,
    granted_by: int,
    expires_at: Optional[datetime] = None,
):
    """
    为用户授予角色

    Args:
        db: 数据库会话
        user_id: 用户ID
        role: 角色名称
        granted_by: 授权人ID
        expires_at: 过期时间（可选）
    """
    # 检查角色是否已存在
    existing = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role == role,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has role: {role}",
        )

    # 创建用户角色
    user_role = UserRole(
        user_id=user_id,
        role=role,
        granted_by=granted_by,
        expires_at=expires_at,
    )
    db.add(user_role)

    # 清除权限缓存
    await permission_checker.clear_user_cache(user_id)

    logger.info(f"Granted role {role} to user {user_id} by user {granted_by}")


async def revoke_role_from_user(
    db: AsyncSession,
    user_id: int,
    role: str,
):
    """
    撤销用户的角色

    Args:
        db: 数据库会话
        user_id: 用户ID
        role: 角色名称
    """
    # 删除用户角色
    result = await db.execute(
        select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.role == role,
            )
        )
    )
    user_role = result.scalar_one_or_none()

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role: {role}",
        )

    await db.delete(user_role)

    # 清除权限缓存
    await permission_checker.clear_user_cache(user_id)

    logger.info(f"Revoked role {role} from user {user_id}")


async def get_user_roles(
    db: AsyncSession,
    user_id: int,
) -> List[str]:
    """
    获取用户的所有角色

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        List[str]: 角色列表
    """
    result = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id)
    )
    user_roles = result.scalars().all()

    return [ur.role for ur in user_roles]
