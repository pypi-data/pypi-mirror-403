# -*- coding: utf-8 -*-
"""租户管理 API 路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.utils.deps import get_current_user, require_admin
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/tenants", response_model=TenantResponse, summary="创建租户")
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    创建新租户（仅管理员）

    Args:
        tenant_data: 租户创建数据
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Returns:
        TenantResponse: 创建的租户

    Raises:
        HTTPException: 租户代码已存在
    """
    # 检查租户代码是否已存在
    existing = await db.execute(
        select(Tenant).where(Tenant.code == tenant_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant code already exists",
        )

    # 创建租户
    tenant = Tenant(**tenant_data.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return tenant


@router.get("/tenants", response_model=List[TenantResponse], summary="获取租户列表")
async def list_tenants(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    获取租户列表（仅管理员）

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Returns:
        List[TenantResponse]: 租户列表
    """
    result = await db.execute(
        select(Tenant)
        .offset(skip)
        .limit(limit)
    )
    tenants = result.scalars().all()

    return tenants


@router.get("/tenants/{tenant_id}", response_model=TenantResponse, summary="获取租户详情")
async def get_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    获取租户详情（仅管理员）

    Args:
        tenant_id: 租户ID
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Returns:
        TenantResponse: 租户详情

    Raises:
        HTTPException: 租户不存在
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse, summary="更新租户")
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    更新租户信息（仅管理员）

    Args:
        tenant_id: 租户ID
        tenant_data: 更新数据
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Returns:
        TenantResponse: 更新后的租户

    Raises:
        HTTPException: 租户不存在
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # 更新字段
    for field, value in tenant_data.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)

    await db.commit()
    await db.refresh(tenant)

    return tenant


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除租户")
async def delete_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_admin),
):
    """
    删除租户（仅管理员）

    Args:
        tenant_id: 租户ID
        db: 数据库会话
        current_user: 当前用户（需管理员权限）

    Raises:
        HTTPException: 租户不存在
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    await db.delete(tenant)
    await db.commit()
