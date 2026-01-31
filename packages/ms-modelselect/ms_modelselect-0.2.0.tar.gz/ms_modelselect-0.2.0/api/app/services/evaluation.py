# -*- coding: utf-8 -*-
"""ModelSelect 评估服务层"""

import json
from typing import Dict, Any, List, Optional
from loguru import logger
from pathlib import Path

# ModelSelect 核心导入
try:
    from modelselect.graders.common.relevance import RelevanceGrader
    from modelselect.graders.text.similarity import SimilarityGrader
    from modelselect.graders.common.correctness import CorrectnessGrader
    from modelselect.graders.format.json.json_match import JsonMatchGrader as JSONMatchGrader
    from modelselect.runner import GradingRunner
    MODELSELECT_AVAILABLE = True
    # F1ScoreGrader 不存在，使用 None
    F1ScoreGrader = None
except ImportError as e:
    logger.warning(f"ModelSelect not fully available: {e}")
    MODELSELECT_AVAILABLE = False
    # 创建占位符
    RelevanceGrader = None
    SimilarityGrader = None
    CorrectnessGrader = None
    JSONMatchGrader = None
    F1ScoreGrader = None
    GradingRunner = None


class EvaluationService:
    """ModelSelect 评估服务"""

    # 支持的 Grader 映射 (动态初始化)
    GRADER_MAPPING = {}

    @classmethod
    def _init_grader_mapping(cls):
        """初始化 Grader 映射"""
        if cls.GRADER_MAPPING:
            return

        if MODELSELECT_AVAILABLE:
            cls.GRADER_MAPPING = {
                "relevance": RelevanceGrader,
                "similarity": SimilarityGrader,
                "correctness": CorrectnessGrader,
                "json_match": JSONMatchGrader,
            }
        else:
            # ModelSelect 不可用时的占位映射
            cls.GRADER_MAPPING = {
                "relevance": None,
                "similarity": None,
                "correctness": None,
                "json_match": None,
            }

    @classmethod
    def is_available(cls) -> bool:
        """检查 ModelSelect 是否可用"""
        return MODELSELECT_AVAILABLE

    @classmethod
    def get_supported_graders(cls) -> List[Dict[str, str]]:
        """获取支持的 Grader 列表"""
        cls._init_grader_mapping()
        graders = []
        for key, grader_class in cls.GRADER_MAPPING.items():
            if MODELSELECT_AVAILABLE:
                try:
                    grader = grader_class()
                    graders.append({
                        "code": key,
                        "name": grader.__class__.__name__,
                        "description": getattr(grader, "__doc__", "No description")
                    })
                except Exception as e:
                    logger.warning(f"Failed to load {key}: {e}")
            else:
                graders.append({
                    "code": key,
                    "name": grader_class.__name__,
                    "description": "ModelSelect not available"
                })
        return graders

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证评估配置

        Args:
            config: 评估配置

        Returns:
            (is_valid, error_message)
        """
        cls._init_grader_mapping()
        required_fields = ["grader", "dataset"]

        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"

        grader_name = config.get("grader")
        if grader_name not in cls.GRADER_MAPPING:
            return False, f"Unsupported grader: {grader_name}"

        return True, None

    @classmethod
    async def evaluate(
        cls,
        config: Dict[str, Any],
        dataset: List[Dict[str, Any]],
        task_id: int,
        tenant_id: int
    ) -> List[Dict[str, Any]]:
        """执行评估

        Args:
            config: 评估配置
            dataset: 评估数据集
            task_id: 任务ID
            tenant_id: 租户ID

        Returns:
            评估结果列表
        """
        if not OPENJUDGE_AVAILABLE:
            logger.error("ModelSelect is not available")
            raise RuntimeError("ModelSelect is not installed or not available")

        # 验证配置
        is_valid, error_msg = cls.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid config: {error_msg}")

        grader_name = config.get("grader")
        grader_config = config.get("grader_config", {})

        logger.info(f"Starting evaluation for task {task_id}, grader: {grader_name}")

        try:
            # 加载 Grader
            grader_class = cls.GRADER_MAPPING[grader_name]
            grader = grader_class(**grader_config)

            logger.info(f"Grader initialized: {grader.__class__.__name__}")

            # 执行评估 (使用 grader.aevaluate 方法)
            results = []
            for idx, sample in enumerate(dataset):
                try:
                    # 提取字段 - 根据 SimilarityGrader 的签名
                    # aevaluate(reference_response: str, response: str, **kwargs)
                    reference_response = sample.get("reference", "")
                    response = sample.get("answer", "")

                    # 执行评分
                    result = await grader.aevaluate(
                        reference_response=reference_response,
                        response=response
                    )

                    # 格式化结果
                    results.append({
                        "task_id": task_id,
                        "sample_index": idx,
                        "grader_name": grader_name,
                        "result_type": "score" if hasattr(result, "score") else "rank",
                        "score": float(result.score) if hasattr(result, "score") else None,
                        "rank": result.rank if hasattr(result, "rank") else None,
                        "reason": result.reason if hasattr(result, "reason") else None,
                        "meta_data": {
                            "reference": reference_response[:100],
                            "response": response[:100],
                        }
                    })

                    logger.debug(f"Sample {idx} evaluated: {result}")

                except Exception as e:
                    logger.error(f"Error evaluating sample {idx}: {e}")
                    results.append({
                        "task_id": task_id,
                        "sample_index": idx,
                        "grader_name": grader_name,
                        "result_type": "error",
                        "score": None,
                        "rank": None,
                        "reason": str(e),
                        "meta_data": {}
                    })

            logger.info(f"Evaluation completed for task {task_id}, {len(results)} samples processed")
            return results

        except Exception as e:
            logger.error(f"Evaluation failed for task {task_id}: {e}")
            raise

    @classmethod
    def get_grader_info(cls, grader_name: str) -> Optional[Dict[str, Any]]:
        """获取 Grader 详细信息

        Args:
            grader_name: Grader 名称

        Returns:
            Grader 信息
        """
        cls._init_grader_mapping()
        if grader_name not in cls.GRADER_MAPPING:
            return None

        grader_class = cls.GRADER_MAPPING[grader_name]

        if grader_class is None:
            return {
                "code": grader_name,
                "class_name": "NotAvailable",
                "module": "N/A",
                "description": "ModelSelect is not available",
            }

        return {
            "code": grader_name,
            "class_name": grader_class.__name__,
            "module": grader_class.__module__,
            "description": grader_class.__doc__,
        }


    @classmethod
    async def evaluate_scenario(
        cls,
        grader_name: str,
        query: str,
        response: str,
        context: Optional[str] = None,
        reference: Optional[str] = None,
        grader_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """评估单个场景 (无需创建任务)

        适用于快速评估 query-response 对,无需上传完整数据集。
        支持 LLM-based Graders (如 RelevanceGrader, CorrectnessGrader)。

        Args:
            grader_name: 评估器名称 (如: relevance, correctness)
            query: 用户查询或需求描述
            response: 系统响应内容
            context: 额外上下文信息 (可选)
            reference: 期望响应或参考答案 (可选)
            grader_config: 评估器配置 (可选)

        Returns:
            评估结果字典
        """
        if not OPENJUDGE_AVAILABLE:
            logger.error("ModelSelect is not available")
            raise RuntimeError("ModelSelect is not installed or not available")

        cls._init_grader_mapping()

        # 验证 grader_name
        if grader_name not in cls.GRADER_MAPPING:
            raise ValueError(f"Unsupported grader: {grader_name}")

        if grader_config is None:
            grader_config = {}

        logger.info(f"Starting scenario evaluation with grader: {grader_name}")

        try:
            # 加载 Grader
            grader_class = cls.GRADER_MAPPING[grader_name]
            
            # 对于 LLM-based Graders (relevance, correctness),提供默认模型配置
            llm_graders = ["relevance", "correctness"]
            if grader_name in llm_graders:
                # 如果用户没有提供 model,使用默认配置
                if "model" not in grader_config:
                    from app.core.config import settings
                    if settings.LLM_API_KEY:
                        # 使用配置的 API Key 创建模型
                        grader_config["model"] = settings.LLM_MODEL
                        logger.info(f"Using configured LLM model: {settings.LLM_MODEL}")
                    else:
                        # 使用模拟模型 (如果用户没有配置 API Key)
                        logger.warning("No LLM API key configured, using default model config")
                        grader_config["model"] = {"model": "gpt-4o-mini"}
            
            grader = grader_class(**grader_config)

            logger.info(f"Grader initialized: {grader.__class__.__name__}")

            # 准备评估参数
            # 不同 Grader 有不同的参数要求:
            # - RelevanceGrader: aevaluate(query, response, context, reference_response)
            # - SimilarityGrader: aevaluate(reference_response, response)
            # - CorrectnessGrader: aevaluate(query, response, reference_response)
            
            kwargs = {}
            
            # 根据 Grader 类型准备参数
            if grader_name == "relevance":
                kwargs["query"] = query
                kwargs["response"] = response
                if context:
                    kwargs["context"] = context
                if reference:
                    kwargs["reference_response"] = reference
            elif grader_name == "correctness":
                kwargs["query"] = query
                kwargs["response"] = response
                if reference:
                    kwargs["reference_response"] = reference
            elif grader_name == "similarity":
                # SimilarityGrader 只需要 reference_response 和 response
                kwargs["reference_response"] = reference if reference else query
                kwargs["response"] = response
            elif grader_name == "json_match":
                kwargs["reference_response"] = reference if reference else query
                kwargs["response"] = response
            else:
                # 默认参数
                kwargs["query"] = query
                kwargs["response"] = response
                if reference:
                    kwargs["reference_response"] = reference

            # 执行评分
            result = await grader.aevaluate(**kwargs)

            # 格式化结果
            evaluation_result = {
                "grader_name": grader_name,
                "result_type": "score" if hasattr(result, "score") else "rank",
                "score": float(result.score) if hasattr(result, "score") else None,
                "rank": result.rank if hasattr(result, "rank") else None,
                "reason": result.reason if hasattr(result, "reason") else None,
                "meta_data": {
                    "query": query[:200] if query else None,
                    "response": response[:200] if response else None,
                    "context": context[:200] if context else None,
                    "reference": reference[:200] if reference else None,
                }
            }

            logger.info(f"Scenario evaluation completed: {evaluation_result.get('score')}")
            return evaluation_result

        except Exception as e:
            logger.error(f"Scenario evaluation failed: {e}")
            raise


    @classmethod
    async def batch_evaluate_scenarios(
        cls,
        grader_name: str,
        scenarios: List[Dict[str, Any]],
        grader_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """批量评估多个场景 (无需创建任务)

        适用于一次性评估多个 query-response 对，无需上传完整数据集。
        支持 LLM-based Graders (如 RelevanceGrader, CorrectnessGrader)。

        Args:
            grader_name: 评估器名称 (如: relevance, correctness)
            scenarios: 场景列表，每个场景包含 query, response 等字段
            grader_config: 评估器配置 (可选)

        Returns:
            批量评估结果字典
        """
        if not OPENJUDGE_AVAILABLE:
            logger.error("ModelSelect is not available")
            raise RuntimeError("ModelSelect is not installed or not available")

        cls._init_grader_mapping()

        # 验证 grader_name
        if grader_name not in cls.GRADER_MAPPING:
            raise ValueError(f"Unsupported grader: {grader_name}")

        if grader_config is None:
            grader_config = {}

        total_count = len(scenarios)
        logger.info(f"Starting batch scenario evaluation for {total_count} scenarios, grader: {grader_name}")

        results = []
        errors = []

        # 批量评估每个场景
        for idx, scenario in enumerate(scenarios):
            try:
                # 提取场景参数
                query = scenario.get("query", "")
                response = scenario.get("response", "")
                context = scenario.get("context")
                reference = scenario.get("reference")

                # 使用单个场景评估方法
                result = await cls.evaluate_scenario(
                    grader_name=grader_name,
                    query=query,
                    response=response,
                    context=context,
                    reference=reference,
                    grader_config=grader_config
                )

                results.append(result)
                logger.debug(f"Scenario {idx} evaluation completed")

            except Exception as e:
                logger.error(f"Failed to evaluate scenario {idx}: {e}")
                errors.append({
                    "index": idx,
                    "scenario": scenario,
                    "error": str(e)
                })

        success_count = len(results)
        failed_count = len(errors)

        logger.info(
            f"Batch scenario evaluation completed: "
            f"{success_count}/{total_count} succeeded, {failed_count}/{total_count} failed"
        )

        return {
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "errors": errors
        }
