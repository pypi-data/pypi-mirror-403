# -*- coding: utf-8 -*-
"""安全工具函数"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: int,
    tenant_id: int,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    创建访问令牌

    Args:
        subject: 令牌主题（用户ID）
        tenant_id: 租户ID
        expires_delta: 过期时间增量
        additional_claims: 额外的声明

    Returns:
        str: JWT 访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),  # JWT sub 必须是字符串
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: int,
    tenant_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建刷新令牌

    Args:
        subject: 令牌主题（用户ID）
        tenant_id: 租户ID
        expires_delta: 过期时间增量

    Returns:
        str: JWT 刷新令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),  # JWT sub 必须是字符串
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码令牌

    Args:
        token: JWT 令牌

    Returns:
        Dict[str, Any]: 解码后的令牌数据

    Raises:
        JWTError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Could not validate credentials: {str(e)}")


def generate_api_key() -> str:
    """
    生成 API 密钥

    Returns:
        str: API 密钥（格式: oj_XXXXXXXXXXXX）
    """
    import secrets

    return f"oj_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    对 API 密钥进行哈希

    Args:
        api_key: API 密钥

    Returns:
        str: 哈希后的 API 密钥
    """
    return get_password_hash(api_key)
