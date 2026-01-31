# -*- coding: utf-8 -*-
"""用户模型"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    tenant_id = Column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户ID",
    )
    username = Column(String(50), nullable=False, comment="用户名")
    email = Column(String(100), nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(
        Enum("admin", "user", "viewer", name="user_role"),
        nullable=False,
        default="user",
        comment="用户角色",
    )
    status = Column(
        Enum("active", "inactive", "banned", name="user_status"),
        nullable=False,
        default="active",
        comment="用户状态",
    )
    avatar = Column(String(255), nullable=True, comment="头像URL")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关系
    tenant = relationship("Tenant", back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    evaluation_tasks = relationship("EvaluationTask", back_populates="user")
