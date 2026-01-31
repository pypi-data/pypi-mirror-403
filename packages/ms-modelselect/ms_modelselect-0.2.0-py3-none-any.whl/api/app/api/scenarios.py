# -*- coding: utf-8 -*-
"""场景评估 API 路由"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from app.services.evaluation import EvaluationService
from app.utils.deps import get_current_user
from app.schemas.user import UserResponse
from app.schemas.task import ScenarioEvaluationRequest, ScenarioEvaluationResponse, BatchScenarioEvaluationRequest, BatchScenarioEvaluationResponse

router = APIRouter()


@router.post(
    "/scenarios/evaluate",
    response_model=ScenarioEvaluationResponse,
    summary="评估单个场景",
    description="无需上传数据集,直接评估单个 query-response 对。适用于快速评估和测试。"
)
async def evaluate_scenario(
    request: ScenarioEvaluationRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    评估单个场景 (无需创建任务)

    支持的评估器:
    - **relevance**: 相关性评估 (1-5分) - 评估响应与查询的相关性
    - **correctness**: 正确性评估 (1-5分) - 评估响应的正确性
    - **similarity**: 相似度评估 (0-1分) - 计算响应与参考答案的相似度
    - **json_match**: JSON 格式匹配 - 验证 JSON 格式和字段

    使用场景:
    - 客服对话质量评估
    - 业务需求理解评估
    - 代码实现质量评估
    - 文档生成质量评估
    - 快速原型测试

    Args:
        request: 场景评估请求

    Returns:
        ScenarioEvaluationResponse: 评估结果
    """
    try:
        # 检查 ModelSelect 是否可用
        if not EvaluationService.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ModelSelect service is not available"
            )

        # 执行场景评估
        result = await EvaluationService.evaluate_scenario(
            grader_name=request.grader,
            query=request.query,
            response=request.response,
            context=request.context,
            reference=request.reference,
            grader_config=request.grader_config
        )

        logger.info(
            f"Scenario evaluation completed for user {current_user.id}, "
            f"grader: {request.grader}, score: {result.get('score')}"
        )

        return ScenarioEvaluationResponse(**result)

    except ValueError as e:
        # 参数验证错误
        logger.warning(f"Invalid scenario evaluation request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        # ModelSelect 不可用
        logger.error(f"ModelSelect runtime error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        # 其他错误
        logger.error(f"Failed to evaluate scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get(
    "/scenarios/graders",
    summary="获取场景评估支持的 Grader",
    description="获取适用于场景评估的 Grader 列表及其说明"
)
async def list_scenario_graders(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    获取场景评估支持的 Grader 列表

    场景评估主要使用 LLM-based Graders,支持对 query-response 对的
    多维度评估。

    Returns:
        Dict: Grader 列表和使用说明
    """
    try:
        all_graders = EvaluationService.get_supported_graders()

        # 场景评估特别适合的 Graders
        scenario_graders = [
            {
                "code": "relevance",
                "name": "RelevanceGrader",
                "description": "评估响应与查询的相关性 (1-5分)",
                "use_cases": [
                    "客服对话质量评估",
                    "搜索结果相关性评估",
                    "问答系统评估"
                ],
                "required_fields": ["query", "response"],
                "optional_fields": ["context", "reference"],
                "example": {
                    "grader": "relevance",
                    "query": "如何申请退款?",
                    "response": "您可以在订单详情页面点击退款按钮...",
                    "context": "客户购买的是数字商品",
                    "reference": "应该说明退款政策并提供操作指引"
                }
            },
            {
                "code": "correctness",
                "name": "CorrectnessGrader",
                "description": "评估响应的正确性和准确性 (1-5分)",
                "use_cases": [
                    "知识问答正确性评估",
                    "代码实现正确性评估",
                    "事实核查"
                ],
                "required_fields": ["query", "response"],
                "optional_fields": ["reference"],
                "example": {
                    "grader": "correctness",
                    "query": "法国的首都是哪里?",
                    "response": "法国的首都是巴黎",
                    "reference": "正确答案: 巴黎"
                }
            },
            {
                "code": "similarity",
                "name": "SimilarityGrader",
                "description": "计算响应与参考答案的相似度 (0-1分,使用BLEU等指标)",
                "use_cases": [
                    "翻译质量评估",
                    "文本生成评估",
                    "摘要质量评估"
                ],
                "required_fields": ["response", "reference"],
                "optional_fields": ["query"],
                "example": {
                    "grader": "similarity",
                    "query": "翻译这段文本",
                    "response": "这是一个翻译结果",
                    "reference": "这是标准翻译答案"
                }
            },
            {
                "code": "json_match",
                "name": "JsonMatchGrader",
                "description": "验证 JSON 格式和字段匹配",
                "use_cases": [
                    "API 响应格式验证",
                    "结构化数据生成评估",
                    "配置文件格式检查"
                ],
                "required_fields": ["response", "reference"],
                "optional_fields": [],
                "example": {
                    "grader": "json_match",
                    "response": '{"name": "test", "value": 123}',
                    "reference": '{"name": "test", "value": 123}'
                }
            }
        ]

        return {
            "total": len(scenario_graders),
            "graders": scenario_graders,
            "modelselect_available": EvaluationService.is_available()
        }

    except Exception as e:
        logger.error(f"Failed to list scenario graders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenario graders: {str(e)}"
        )


@router.post(
    "/scenarios/batch-evaluate",
    response_model=BatchScenarioEvaluationResponse,
    summary="批量评估多个场景",
    description="无需上传数据集,一次性批量评估多个 query-response 对。"
)
async def batch_evaluate_scenarios(
    request: BatchScenarioEvaluationRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    批量评估多个场景 (无需创建任务)

    支持的评估器:
    - **relevance**: 相关性评估 (1-5分)
    - **correctness**: 正确性评估 (1-5分)
    - **similarity**: 相似度评估 (0-1分)
    - **json_match**: JSON 格式匹配

    使用场景:
    - 批量客服对话质量评估
    - 多个知识问答的批量验证
    - 批量翻译质量评估
    - 批量 API 响应验证

    Args:
        request: 批量场景评估请求

    Returns:
        BatchScenarioEvaluationResponse: 批量评估结果
    """
    try:
        # 检查 ModelSelect 是否可用
        if not EvaluationService.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ModelSelect service is not available"
            )

        # 执行批量场景评估
        result = await EvaluationService.batch_evaluate_scenarios(
            grader_name=request.grader,
            scenarios=request.scenarios,
            grader_config=request.grader_config
        )

        logger.info(
            f"Batch scenario evaluation completed for user {current_user.id}, "
            f"grader: {request.grader}, "
            f"success: {result['success_count']}/{result['total_count']}"
        )

        return BatchScenarioEvaluationResponse(**result)

    except ValueError as e:
        # 参数验证错误
        logger.warning(f"Invalid batch scenario evaluation request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        # ModelSelect 不可用
        logger.error(f"ModelSelect runtime error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        # 其他错误
        logger.error(f"Failed to batch evaluate scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch evaluation failed: {str(e)}"
        )
