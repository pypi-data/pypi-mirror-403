# -*- coding: utf-8 -*-
"""API Key 管理 API 路由"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger
import secrets
import string

from app.core.database import get_db
from app.models import APIKey
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyListResponse,
)
from app.utils.deps import get_current_user, get_current_tenant
from app.utils.security import get_password_hash, verify_password
from app.schemas.user import UserResponse

router = APIRouter()

# API Key 前缀
API_KEY_PREFIX = "oj_"


def generate_api_key() -> str:
    """生成新的 API Key
    
    Returns:
        str: 格式为 oj_<随机字符串> 的 API Key
    """
    # 生成 32 字节的随机字符串
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"{API_KEY_PREFIX}{random_part}"


@router.post("/api-keys", response_model=APIKeyCreateResponse, summary="创建 API Key")
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """创建新的 API Key

    创建后会返回完整的 API Key，**请妥善保存**，之后无法再次查看完整密钥。

    Args:
        key_data: API Key 创建数据
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        APIKeyCreateResponse: 包含完整 API Key 的响应
    """
    # 生成 API Key
    api_key_value = generate_api_key()
    
    # 提取前缀（用于查询）
    key_prefix = api_key_value[:10]  # oj_ + 7个字符
    
    # 哈希存储
    key_hash = get_password_hash(api_key_value)
    
    # 创建记录
    api_key = APIKey(
        tenant_id=current_tenant.id,
        user_id=current_user.id,
        name=key_data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=key_data.scopes or ["read", "write"],  # 默认权限
        is_active=True,
        expires_at=key_data.expires_at,
        created_at=datetime.now(),
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    logger.info(f"API Key created: {key_prefix}... by user {current_user.id}")
    
    return APIKeyCreateResponse(
        id=api_key.id,
        tenant_id=api_key.tenant_id,
        user_id=api_key.user_id,
        name=api_key.name,
        api_key=api_key_value,  # 仅返回这一次
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=APIKeyListResponse, summary="获取 API Key 列表")
async def list_api_keys(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    include_inactive: bool = Query(False, description="是否包含已禁用的密钥"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """获取当前用户的 API Key 列表

    管理员可以查看租户下所有密钥，普通用户只能查看自己的密钥。

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        include_inactive: 是否包含已禁用的密钥
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        APIKeyListResponse: API Key 列表
    """
    query = select(APIKey).where(APIKey.tenant_id == current_tenant.id)
    
    # 非管理员只能看到自己的密钥
    if current_user.role != "admin":
        query = query.where(APIKey.user_id == current_user.id)
    
    # 是否包含已禁用的密钥
    if not include_inactive:
        query = query.where(APIKey.is_active == True)
    
    query = query.order_by(APIKey.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    # 获取总数
    count_query = select(APIKey).where(APIKey.tenant_id == current_tenant.id)
    if current_user.role != "admin":
        count_query = count_query.where(APIKey.user_id == current_user.id)
    if not include_inactive:
        count_query = count_query.where(APIKey.is_active == True)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return APIKeyListResponse(
        total=total,
        api_keys=list(api_keys),
    )


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse, summary="获取 API Key 详情")
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """获取 API Key 详情

    Args:
        key_id: API Key ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        APIKeyResponse: API Key 详情

    Raises:
        HTTPException: API Key 不存在或无权访问
    """
    result = await db.execute(
        select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == current_tenant.id,
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    
    # 权限检查：非管理员只能查看自己的密钥
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return api_key


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse, summary="更新 API Key")
async def update_api_key(
    key_id: int,
    key_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """更新 API Key 信息

    可以更新密钥名称、权限范围和激活状态。

    Args:
        key_id: API Key ID
        key_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        APIKeyResponse: 更新后的 API Key

    Raises:
        HTTPException: API Key 不存在或无权访问
    """
    result = await db.execute(
        select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == current_tenant.id,
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    
    # 权限检查：非管理员只能更新自己的密钥
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # 更新字段
    update_data = key_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)
    
    await db.commit()
    await db.refresh(api_key)
    
    logger.info(f"API Key {key_id} updated by user {current_user.id}")
    
    return api_key


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 API Key")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """删除 API Key

    Args:
        key_id: API Key ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Raises:
        HTTPException: API Key 不存在或无权删除
    """
    result = await db.execute(
        select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == current_tenant.id,
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    
    # 权限检查：非管理员只能删除自己的密钥
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    await db.delete(api_key)
    await db.commit()
    
    logger.info(f"API Key {key_id} deleted by user {current_user.id}")


@router.post("/api-keys/{key_id}/revoke", response_model=APIKeyResponse, summary="撤销 API Key")
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """撤销（禁用）API Key

    与删除不同，撤销只是将密钥标记为失效，记录仍然保留。

    Args:
        key_id: API Key ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        APIKeyResponse: 撤销后的 API Key
    """
    result = await db.execute(
        select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.tenant_id == current_tenant.id,
            )
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    
    # 权限检查：非管理员只能撤销自己的密钥
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)
    
    logger.info(f"API Key {key_id} revoked by user {current_user.id}")
    
    return api_key
