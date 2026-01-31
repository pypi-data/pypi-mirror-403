# -*- coding: utf-8 -*-
"""认证相关 API 路由"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models import User, Tenant
from app.schemas.user import UserLogin, Token, UserResponse, UserCreate
from app.utils.security import verify_password, create_access_token, create_refresh_token
from loguru import logger

router = APIRouter()


@router.post("/auth/login", response_model=Token, summary="用户登录")
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    Args:
        user_data: 登录数据（邮箱、密码、租户代码）
        db: 数据库会话

    Returns:
        Token: 访问令牌和刷新令牌

    Raises:
        HTTPException: 登录失败
    """
    # 查找租户
    if user_data.tenant_code:
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.code == user_data.tenant_code)
        )
        tenant = tenant_result.scalar_one_or_none()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        if tenant.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant account is suspended",
            )

        tenant_id = tenant.id
    else:
        # 如果没有提供租户代码，使用默认租户
        tenant_result = await db.execute(select(Tenant).where(Tenant.code == "default"))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default tenant not found",
            )
        tenant_id = tenant.id

    # 查找用户
    result = await db.execute(
        select(User).where(
            User.tenant_id == tenant_id,
            User.email == user_data.email,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or banned",
        )

    # 生成令牌
    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
    )

    refresh_token = create_refresh_token(
        subject=user.id,
        tenant_id=user.tenant_id,
    )

    # 更新最后登录时间
    from datetime import datetime

    user.last_login_at = datetime.now()
    await db.commit()

    logger.info(f"User {user.email} logged in successfully")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/auth/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册（仅用于演示，生产环境需要邮箱验证）

    Args:
        user_data: 用户注册数据
        db: 数据库会话

    Returns:
        UserResponse: 创建的用户

    Raises:
        HTTPException: 注册失败
    """
    from app.utils.security import get_password_hash
    from sqlalchemy import select, func

    # 查找默认租户
    tenant_result = await db.execute(select(Tenant).where(Tenant.code == "default"))
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Default tenant not found",
        )

    # 检查用户是否已存在
    existing_user = await db.execute(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == user_data.email,
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 安全检查：禁止通过注册 API 创建管理员角色
    if user_data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot register as admin. Admin role must be assigned by existing admin.",
        )

    # 创建用户（强制设置为普通用户）
    user = User(
        tenant_id=tenant.id,
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role="user",  # 强制设置为普通用户
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user {user.email} registered with role: user")

    return user
