# -*- coding: utf-8 -*-
"""评估任务模型"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, ForeignKey, Text, Integer, JSON, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class EvaluationTask(Base):
    """评估任务模型"""

    __tablename__ = "evaluation_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    tenant_id = Column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户ID",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="创建用户ID",
    )
    name = Column(String(255), nullable=False, comment="任务名称")
    description = Column(Text, nullable=True, comment="任务描述")
    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled", name="task_status"),
        nullable=False,
        default="pending",
        comment="任务状态",
    )
    config = Column(JSON, nullable=False, comment="评估配置")
    dataset_uri = Column(String(500), nullable=True, comment="数据集存储URI")
    dataset_size = Column(Integer, nullable=False, default=0, comment="数据集大小")
    progress = Column(Numeric(5, 2), nullable=False, default=0.00, comment="进度百分比")
    result_uri = Column(String(500), nullable=True, comment="结果存储URI")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关系
    tenant = relationship("Tenant", back_populates="evaluation_tasks")
    user = relationship("User", back_populates="evaluation_tasks")
    results = relationship("EvaluationResult", back_populates="task", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """评估结果模型"""

    __tablename__ = "evaluation_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="结果ID")
    task_id = Column(
        BigInteger,
        ForeignKey("evaluation_tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )
    sample_index = Column(Integer, nullable=False, comment="样本索引")
    grader_name = Column(String(100), nullable=False, comment="评分器名称")
    result_type = Column(
        Enum("score", "rank", "error", name="result_type"),
        nullable=False,
        comment="结果类型",
    )
    score = Column(Numeric(10, 4), nullable=True, comment="分数")
    rank = Column(JSON, nullable=True, comment="排序结果")
    reason = Column(Text, nullable=True, comment="评估原因")
    meta_data = Column(JSON, nullable=True, comment="元数据")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关系
    task = relationship("EvaluationTask", back_populates="results")


class UsageStatistic(Base):
    """使用统计模型"""

    __tablename__ = "usage_statistics"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="统计ID")
    tenant_id = Column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户ID",
    )
    date = Column(DateTime, nullable=False, comment="统计日期")
    api_calls = Column(Integer, nullable=False, default=0, comment="API调用次数")
    evaluations_count = Column(Integer, nullable=False, default=0, comment="评估任务数")
    samples_count = Column(Integer, nullable=False, default=0, comment="评估样本数")
    storage_used_mb = Column(Numeric(10, 2), nullable=False, default=0.00, comment="存储使用量(MB)")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )

    # 关系
    tenant = relationship("Tenant", back_populates="usage_statistics")
