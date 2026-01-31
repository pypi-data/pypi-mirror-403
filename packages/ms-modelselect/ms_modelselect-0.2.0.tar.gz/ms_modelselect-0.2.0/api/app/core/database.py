# -*- coding: utf-8 -*-
"""数据库连接和会话管理"""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from contextlib import contextmanager

from app.core.config import settings

# 同步引擎（用于 Alembic 迁移）
# 确保 URL 使用 mysql+pymysql 驱动
sync_url = settings.DATABASE_URL
if "mysql+aiomysql" in sync_url:
    sync_url = sync_url.replace("mysql+aiomysql", "mysql+pymysql")
elif "mysql+pymysql" not in sync_url:
    sync_url = sync_url.replace("mysql://", "mysql+pymysql://")

sync_engine = create_engine(
    sync_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False
    }
)

# 异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("mysql+pymysql", "mysql+aiomysql"),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base 类用于模型继承
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_db() -> Session:
    """
    获取同步数据库会话的上下文管理器

    Usage:
        with get_sync_db() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """初始化数据库（创建所有表）"""
    async with async_engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        # noqa 表示忽略未使用导入的警告
        from app.models import (  # noqa
            tenant,      # Tenant 模型
            user,        # User 模型
            api_key,     # APIKey 模型
            task,        # EvaluationTask, EvaluationResult, UsageStatistic 模型
            permission,  # Permission, RolePermission, UserRole 模型
        )

        await conn.run_sync(Base.metadata.create_all)
