# -*- coding: utf-8 -*-
"""应用配置模块"""

from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    APP_NAME: str = "ModelSelect"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = Field(default="your-secret-key-change-this-in-production")

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS 配置"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "modelselect"
    DB_USER: str = "modelselect"
    DB_PASSWORD: str = "modelselect_2025"

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接 URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        """构建 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_2025"
    MINIO_BUCKET: str = "modelselect"
    MINIO_SECURE: bool = False

    # JWT 配置
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key-change-this")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 评估配置
    GRADER_MAX_CONCURRENT: int = 10
    GRADER_TIMEOUT: int = 300
    TASK_MAX_RETRIES: int = 3

    # LLM 模型配置 (用于 RelevanceGrader, CorrectnessGrader 等)
    LLM_PROVIDER: str = "openai"  # openai, azure_openai, etc.
    LLM_MODEL: str = "gpt-5.2"  # 模型名称
    LLM_API_KEY: str = "sk-BTBOBhThYM6wnyyEgrSmsdvXVMa7D4eRNRw4PhZS7ocAaadw"  # API 密钥
    LLM_BASE_URL: str = "https://api.302.ai/v1"  # 自定义 API endpoint (可选)
    LLM_TEMPERATURE: float = 0.1  # 默认温度
    LLM_MAX_TOKENS: int = 100000  # 默认最大 tokens

    # 文件存储配置
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(default=["json", "csv", "txt"])

    class Config:
        """配置类"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
