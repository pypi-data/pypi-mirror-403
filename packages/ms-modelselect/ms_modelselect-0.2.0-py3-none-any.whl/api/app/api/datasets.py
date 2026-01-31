# -*- coding: utf-8 -*-
"""数据集管理 API 路由"""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.services.storage import StorageService
from app.utils.deps import get_current_user, get_current_tenant
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/datasets/upload", summary="上传数据集文件")
async def upload_dataset(
    file: UploadFile = File(..., description="数据集文件(JSON或JSONL格式)"),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    上传评估数据集文件

    支持的格式:
    - JSON: [{"question": "...", "answer": "...", "reference": "..."}, ...]
    - JSONL: 每行一个JSON对象

    Args:
        file: 上传的文件
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        上传结果
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 验证文件大小 (限制10MB)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large (max 10MB)"
            )

        # 解析数据集
        try:
            # 尝试JSON格式
            if file.filename.endswith('.json'):
                dataset = json.loads(content.decode('utf-8'))
            # 尝试JSONL格式
            elif file.filename.endswith('.jsonl'):
                dataset = []
                for line in content.decode('utf-8').strip().split('\n'):
                    if line:
                        dataset.append(json.loads(line))
            else:
                # 默认尝试JSON
                dataset = json.loads(content.decode('utf-8'))

            if not isinstance(dataset, list):
                raise ValueError("Dataset must be a list")

            # 验证数据格式
            for idx, sample in enumerate(dataset):
                if not isinstance(sample, dict):
                    raise ValueError(f"Sample {idx} is not a dict")
                if "question" not in sample and "answer" not in sample:
                    raise ValueError(f"Sample {idx} missing required fields")

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dataset format: {str(e)}"
            )

        # 上传到MinIO
        object_name = StorageService.generate_object_name(
            current_tenant.id,
            current_user.id,
            file.filename
        )

        uri = StorageService.upload_file(
            bucket_name="datasets",
            object_name=object_name,
            data=content,
            content_type="application/json"
        )

        if not uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

        logger.info(
            f"Dataset uploaded: {len(dataset)} samples, "
            f"user={current_user.id}, tenant={current_tenant.id}"
        )

        return {
            "uri": uri,
            "bucket": "datasets",
            "object_name": object_name,
            "filename": file.filename,
            "size": len(content),
            "sample_count": len(dataset),
            "dataset": dataset  # 返回数据集供任务创建使用
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload dataset: {str(e)}"
        )


@router.post("/datasets/validate", summary="验证数据集格式")
async def validate_dataset(
    dataset: List[dict],
    current_user: UserResponse = Depends(get_current_user),
):
    """
    验证数据集格式

    Args:
        dataset: 数据集
        current_user: 当前用户

    Returns:
        验证结果
    """
    try:
        errors = []
        warnings = []

        for idx, sample in enumerate(dataset):
            # 基本格式检查
            if not isinstance(sample, dict):
                errors.append(f"Sample {idx}: Not a dictionary")
                continue

            # 必需字段检查
            if "question" not in sample:
                warnings.append(f"Sample {idx}: Missing 'question' field")
            if "answer" not in sample:
                errors.append(f"Sample {idx}: Missing 'answer' field")

            # 字段类型检查
            for key in ["question", "answer", "reference"]:
                if key in sample and not isinstance(sample[key], str):
                    errors.append(f"Sample {idx}: '{key}' must be a string")

        return {
            "valid": len(errors) == 0,
            "total_samples": len(dataset),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:10],  # 只返回前10个错误
            "warnings": warnings[:10]
        }

    except Exception as e:
        logger.error(f"Failed to validate dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate dataset: {str(e)}"
        )
