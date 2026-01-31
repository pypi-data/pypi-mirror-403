# -*- coding: utf-8 -*-
"""API密钥模型"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIKey(Base):
    """API密钥模型"""

    __tablename__ = "api_keys"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="API密钥ID")
    tenant_id = Column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户ID",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="用户ID",
    )
    name = Column(String(100), nullable=False, comment="密钥名称")
    key_prefix = Column(String(10), nullable=False, comment="密钥前缀")
    key_hash = Column(String(255), nullable=False, unique=True, comment="密钥哈希")
    scopes = Column(JSON, nullable=True, comment="权限范围")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关系
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")
