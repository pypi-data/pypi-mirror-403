# -*- coding: utf-8 -*-
"""Grader 管理 API 路由"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from app.services.evaluation import EvaluationService
from app.utils.deps import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/graders", summary="获取支持的 Grader 列表")
async def list_graders(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取所有支持的 Grader 列表

    Returns:
        List[Dict]: Grader 列表
    """
    try:
        graders = EvaluationService.get_supported_graders()
        return {
            "total": len(graders),
            "graders": graders,
            "modelselect_available": EvaluationService.is_available()
        }
    except Exception as e:
        logger.error(f"Failed to list graders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list graders: {str(e)}"
        )


@router.get("/graders/{grader_name}", summary="获取 Grader 详细信息")
async def get_grader_info(
    grader_name: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取指定 Grader 的详细信息

    Args:
        grader_name: Grader 名称

    Returns:
        Dict: Grader 详细信息
    """
    try:
        info = EvaluationService.get_grader_info(grader_name)

        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grader '{grader_name}' not found"
            )

        return info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get grader info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get grader info: {str(e)}"
        )


@router.get("/graders/{grader_name}/schema", summary="获取 Grader 配置 Schema")
async def get_grader_schema(
    grader_name: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取 Grader 的配置 Schema

    Args:
        grader_name: Grader 名称

    Returns:
        Dict: 配置 Schema
    """
    try:
        info = EvaluationService.get_grader_info(grader_name)

        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grader '{grader_name}' not found"
            )

        # 返回示例配置
        return {
            "grader": grader_name,
            "schema": {
                "type": "object",
                "properties": {
                    "grader": {
                        "type": "string",
                        "const": grader_name,
                        "description": f"Use {grader_name} grader"
                    },
                    "grader_config": {
                        "type": "object",
                        "description": "Grader-specific configuration",
                        "properties": {}
                    },
                    "dataset": {
                        "type": "array",
                        "description": "Evaluation dataset",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "answer": {"type": "string"},
                                "reference": {"type": "string"}
                            },
                            "required": ["question", "answer"]
                        }
                    }
                },
                "required": ["grader", "dataset"]
            },
            "example": {
                "grader": grader_name,
                "grader_config": {},
                "dataset": [
                    {
                        "question": "What is the capital of France?",
                        "answer": "Paris",
                        "reference": "Paris is the capital of France."
                    }
                ]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get grader schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get grader schema: {str(e)}"
        )
