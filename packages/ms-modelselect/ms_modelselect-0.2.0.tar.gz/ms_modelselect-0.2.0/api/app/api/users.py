# -*- coding: utf-8 -*-
"""用户管理 API 路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.deps import get_current_user, get_current_tenant, require_admin
from app.utils.security import get_password_hash

router = APIRouter()


@router.post("/users", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
    current_tenant = Depends(get_current_tenant),
):
    """
    创建新用户（需要管理员权限）

    Args:
        user_data: 用户创建数据
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        UserResponse: 创建的用户

    Raises:
        HTTPException: 用户已存在
    """
    # 检查用户名是否已存在
    existing = await db.execute(
        select(User).where(
            User.tenant_id == current_tenant.id,
            User.username == user_data.username,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # 检查邮箱是否已存在
    existing = await db.execute(
        select(User).where(
            User.tenant_id == current_tenant.id,
            User.email == user_data.email,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # 创建用户
    user = User(
        tenant_id=current_tenant.id,
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def list_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取当前租户的用户列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        List[UserResponse]: 用户列表
    """
    result = await db.execute(
        select(User)
        .where(User.tenant_id == current_tenant.id)
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()

    return users


@router.get("/users/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取当前登录用户的信息

    Args:
        current_user: 当前用户

    Returns:
        UserResponse: 当前用户信息
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取用户详情

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        UserResponse: 用户详情

    Raises:
        HTTPException: 用户不存在或无权访问
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_tenant.id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    更新用户信息

    Args:
        user_id: 用户ID
        user_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        UserResponse: 更新后的用户

    Raises:
        HTTPException: 用户不存在或无权访问
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_tenant.id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 权限检查：只有管理员或用户本人可以更新
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)

    # 如果更新密码，需要哈希处理
    if "password" in update_data:
        from app.utils.security import get_password_hash
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
    current_tenant = Depends(get_current_tenant),
):
    """
    删除用户（仅管理员）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户（需管理员权限）
        current_tenant: 当前租户

    Raises:
        HTTPException: 用户不存在
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_tenant.id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    await db.delete(user)
    await db.commit()
