# -*- coding: utf-8 -*-
"""租户模型"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, JSON, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tenant(Base):
    """租户模型"""

    __tablename__ = "tenants"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="租户ID")
    name = Column(String(100), nullable=False, comment="租户名称")
    code = Column(String(50), nullable=False, unique=True, comment="租户代码")
    status = Column(
        Enum("active", "suspended", "deleted", name="tenant_status"),
        nullable=False,
        default="active",
        comment="租户状态",
    )
    plan = Column(
        Enum("free", "basic", "pro", "enterprise", name="tenant_plan"),
        nullable=False,
        default="free",
        comment="订阅计划",
    )
    max_users = Column(BigInteger, nullable=False, default=5, comment="最大用户数")
    max_api_calls_per_day = Column(BigInteger, nullable=False, default=1000, comment="每日最大API调用次数")
    max_storage_gb = Column(Numeric(10, 2), nullable=False, default=10.00, comment="最大存储空间(GB)")
    expired_at = Column(DateTime, nullable=True, comment="订阅过期时间")
    settings = Column(JSON, nullable=True, comment="租户配置")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关系
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    evaluation_tasks = relationship("EvaluationTask", back_populates="tenant", cascade="all, delete-orphan")
    usage_statistics = relationship("UsageStatistic", back_populates="tenant", cascade="all, delete-orphan")
