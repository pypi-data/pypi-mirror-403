# -*- coding: utf-8 -*-
"""评估任务相关的 Pydantic Schemas"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, validator
from decimal import Decimal


class EvaluationTaskCreate(BaseModel):
    """创建评估任务 Schema"""

    name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    config: Dict[str, Any] = Field(..., description="评估配置")
    dataset_uri: Optional[str] = Field(None, description="数据集存储URI")
    auto_execute: bool = Field(True, description="是否自动执行任务")


class EvaluationTaskUpdate(BaseModel):
    """更新评估任务 Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: Optional[str] = Field(None, description="任务状态")


class EvaluationTaskResponse(BaseModel):
    """评估任务响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    user_id: int
    name: str
    description: Optional[str]
    status: str
    config: Dict[str, Any]
    dataset_uri: Optional[str]
    dataset_size: int
    progress: Decimal
    result_uri: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class EvaluationResultResponse(BaseModel):
    """评估结果响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    sample_index: int
    grader_name: str
    result_type: str
    score: Optional[Decimal]
    rank: Optional[List[int]]
    reason: Optional[str]
    meta_data: Optional[Dict[str, Any]]
    created_at: datetime


class TaskStatistics(BaseModel):
    """任务统计 Schema"""

    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int


class ScenarioEvaluationRequest(BaseModel):
    """场景评估请求 Schema"""

    grader: str = Field(..., description="评估器名称 (如: relevance, correctness, instruction_following)")
    query: str = Field(..., min_length=1, description="用户查询或需求描述")
    response: str = Field(..., min_length=1, description="系统响应内容")
    context: Optional[str] = Field(None, description="额外上下文信息")
    reference: Optional[str] = Field(None, description="期望响应或参考答案")
    grader_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="评估器配置")


class ScenarioEvaluationResponse(BaseModel):
    """场景评估响应 Schema"""

    grader_name: str = Field(..., description="使用的评估器名称")
    result_type: str = Field(..., description="结果类型 (score/rank)")
    score: Optional[Decimal] = Field(None, description="评估分数")
    rank: Optional[List[int]] = Field(None, description="排序结果")
    reason: Optional[str] = Field(None, description="评估原因或说明")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="元数据")


class BatchScenarioEvaluationRequest(BaseModel):
    """批量场景评估请求 Schema"""

    grader: str = Field(..., description="评估器名称 (如: relevance, correctness)")
    scenarios: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="待评估的场景列表，每个场景包含 query, response 等字段"
    )
    grader_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="评估器配置")

    @validator('scenarios')
    def validate_scenarios(cls, v):
        """验证场景数据"""
        for idx, scenario in enumerate(v):
            if 'query' not in scenario or 'response' not in scenario:
                raise ValueError(f"Scenario at index {idx} must have 'query' and 'response' fields")
        return v


class BatchScenarioEvaluationResponse(BaseModel):
    """批量场景评估响应 Schema"""

    total_count: int = Field(..., description="总场景数")
    success_count: int = Field(..., description="成功评估数")
    failed_count: int = Field(..., description="失败评估数")
    results: List[ScenarioEvaluationResponse] = Field(..., description="评估结果列表")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误信息列表")
