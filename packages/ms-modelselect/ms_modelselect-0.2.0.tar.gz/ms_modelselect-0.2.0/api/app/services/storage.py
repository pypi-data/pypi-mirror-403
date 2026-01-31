# -*- coding: utf-8 -*-
"""MinIO 存储服务"""

import io
from typing import Optional, BinaryIO
from loguru import logger
from datetime import datetime

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    logger.warning("MinIO not available")
    MINIO_AVAILABLE = False

from app.core.config import settings


class StorageService:
    """MinIO 存储服务"""

    _client: Optional[Minio] = None

    @classmethod
    def get_client(cls) -> Optional[Minio]:
        """获取 MinIO 客户端"""
        if not MINIO_AVAILABLE:
            return None

        if cls._client is None:
            try:
                cls._client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                logger.info(f"MinIO client initialized: {settings.MINIO_ENDPOINT}")
            except Exception as e:
                logger.error(f"Failed to initialize MinIO client: {e}")
                return None

        return cls._client

    @classmethod
    def ensure_bucket(cls, bucket_name: str) -> bool:
        """确保存储桶存在

        Args:
            bucket_name: 存储桶名称

        Returns:
            是否成功
        """
        client = cls.get_client()
        if not client:
            return False

        try:
            # 检查存储桶是否存在
            if not client.bucket_exists(bucket_name):
                # 创建存储桶
                client.make_bucket(bucket_name)
                logger.info(f"Bucket created: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
            return False

    @classmethod
    def upload_file(
        cls,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """上传文件

        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称
            data: 文件数据
            content_type: 内容类型

        Returns:
            文件URI或None
        """
        client = cls.get_client()
        if not client:
            return None

        try:
            # 确保存储桶存在
            if not cls.ensure_bucket(bucket_name):
                return None

            # 上传文件
            client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )

            # 生成URI
            uri = f"minio://{bucket_name}/{object_name}"
            logger.info(f"File uploaded: {uri}")

            return uri

        except S3Error as e:
            logger.error(f"Failed to upload file {object_name}: {e}")
            return None

    @classmethod
    def download_file(cls, bucket_name: str, object_name: str) -> Optional[bytes]:
        """下载文件

        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称

        Returns:
            文件数据或None
        """
        client = cls.get_client()
        if not client:
            return None

        try:
            response = client.get_object(bucket_name, object_name)
            data = response.read()
            return data
        except S3Error as e:
            logger.error(f"Failed to download file {object_name}: {e}")
            return None

    @classmethod
    def delete_file(cls, bucket_name: str, object_name: str) -> bool:
        """删除文件

        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称

        Returns:
            是否成功
        """
        client = cls.get_client()
        if not client:
            return False

        try:
            client.remove_object(bucket_name, object_name)
            logger.info(f"File deleted: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file {object_name}: {e}")
            return False

    @classmethod
    def generate_object_name(cls, tenant_id: int, user_id: int, filename: str) -> str:
        """生成对象名称

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            filename: 文件名

        Returns:
            对象名称
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tenants/{tenant_id}/users/{user_id}/{timestamp}_{filename}"
