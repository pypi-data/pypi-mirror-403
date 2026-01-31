# -*- coding: utf-8 -*-
"""ModelSelect SaaS API 主应用"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, tenants, users, tasks, permissions, graders, datasets, scenarios, api_keys


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")

    yield

    # 关闭时的清理工作
    logger.info("Shutting down application...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="ModelSelect - AI 应用评估框架 SaaS 服务",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# 注册路由
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["认证"])
app.include_router(tenants.router, prefix=settings.API_PREFIX, tags=["租户管理"])
app.include_router(users.router, prefix=settings.API_PREFIX, tags=["用户管理"])
app.include_router(api_keys.router, prefix=settings.API_PREFIX, tags=["API Key管理"])
app.include_router(datasets.router, prefix=settings.API_PREFIX, tags=["数据集管理"])
app.include_router(tasks.router, prefix=settings.API_PREFIX, tags=["评估任务"])
app.include_router(graders.router, prefix=settings.API_PREFIX, tags=["Grader管理"])
app.include_router(permissions.router, prefix=settings.API_PREFIX, tags=["权限管理"])
app.include_router(scenarios.router, prefix=settings.API_PREFIX, tags=["场景评估"])


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
