# -*- coding: utf-8 -*-
"""评估任务管理 API 路由"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from app.core.database import get_db
from app.models import EvaluationTask, EvaluationResult
from app.schemas.task import (
    EvaluationTaskCreate,
    EvaluationTaskUpdate,
    EvaluationTaskResponse,
    EvaluationResultResponse,
    TaskStatistics,
)
from app.utils.deps import get_current_user, get_current_tenant
from app.schemas.user import UserResponse
from app.services.task_executor import TaskExecutor
from loguru import logger

router = APIRouter()


@router.post("/tasks", response_model=EvaluationTaskResponse, summary="创建评估任务")
async def create_task(
    task_data: EvaluationTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    创建评估任务

    Args:
        task_data: 任务创建数据
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        EvaluationTaskResponse: 创建的任务
    """
    # 创建任务
    task = EvaluationTask(
        tenant_id=current_tenant.id,
        user_id=current_user.id,
        name=task_data.name,
        description=task_data.description,
        config=task_data.config,
        dataset_uri=task_data.dataset_uri,
        dataset_size=0,  # 将在上传数据集后更新
        status="pending",
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 添加后台任务执行评估
    if task_data.auto_execute:
        background_tasks.add_task(
            TaskExecutor.execute_task,
            task.id,
            current_tenant.id,
            db
        )
        logger.info(f"Task {task.id} scheduled for execution")
    else:
        logger.info(f"Task {task.id} created (manual execution)")

    return task


@router.get("/tasks", response_model=List[EvaluationTaskResponse], summary="获取任务列表")
async def list_tasks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回记录数"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取当前租户的评估任务列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        status: 状态筛选
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        List[EvaluationTaskResponse]: 任务列表
    """
    query = select(EvaluationTask).where(
        EvaluationTask.tenant_id == current_tenant.id
    )

    if status:
        query = query.where(EvaluationTask.status == status)

    # 非管理员只能看到自己的任务
    if current_user.role != "admin":
        query = query.where(EvaluationTask.user_id == current_user.id)

    query = query.order_by(EvaluationTask.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return tasks


@router.get("/tasks/statistics", response_model=TaskStatistics, summary="获取任务统计")
async def get_task_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取任务统计信息

    Args:
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        TaskStatistics: 统计信息
    """
    query = select(EvaluationTask).where(
        EvaluationTask.tenant_id == current_tenant.id
    )

    # 非管理员只能统计自己的任务
    if current_user.role != "admin":
        query = query.where(EvaluationTask.user_id == current_user.id)

    result = await db.execute(query)
    tasks = result.scalars().all()

    total = len(tasks)
    pending = sum(1 for t in tasks if t.status == "pending")
    running = sum(1 for t in tasks if t.status == "running")
    completed = sum(1 for t in tasks if t.status == "completed")
    failed = sum(1 for t in tasks if t.status == "failed")

    return TaskStatistics(
        total_tasks=total,
        pending_tasks=pending,
        running_tasks=running,
        completed_tasks=completed,
        failed_tasks=failed,
    )


@router.get("/tasks/{task_id}", response_model=EvaluationTaskResponse, summary="获取任务详情")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取任务详情

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        EvaluationTaskResponse: 任务详情

    Raises:
        HTTPException: 任务不存在或无权访问
    """
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return task


@router.put("/tasks/{task_id}", response_model=EvaluationTaskResponse, summary="更新任务")
async def update_task(
    task_id: int,
    task_data: EvaluationTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    更新任务信息

    Args:
        task_id: 任务ID
        task_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        EvaluationTaskResponse: 更新后的任务

    Raises:
        HTTPException: 任务不存在或无权访问
    """
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 更新字段
    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task


@router.post("/tasks/{task_id}/cancel", response_model=EvaluationTaskResponse, summary="取消任务")
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    取消正在运行的任务

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        EvaluationTaskResponse: 取消后的任务

    Raises:
        HTTPException: 任务不存在或无法取消
    """
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 只能取消 pending 或 running 状态的任务
    if task.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled",
        )

    task.status = "cancelled"
    task.completed_at = datetime.now()

    await db.commit()
    await db.refresh(task)

    logger.info(f"Task {task_id} cancelled by user {current_user.id}")

    return task


@router.get("/tasks/{task_id}/results", response_model=List[EvaluationResultResponse], summary="获取任务结果")
async def get_task_results(
    task_id: int,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    获取任务的评估结果

    Args:
        task_id: 任务ID
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        List[EvaluationResultResponse]: 评估结果列表

    Raises:
        HTTPException: 任务不存在或无权访问
    """
    # 检查任务权限
    task_result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 获取结果
    result = await db.execute(
        select(EvaluationResult)
        .where(EvaluationResult.task_id == task_id)
        .order_by(EvaluationResult.sample_index)
        .offset(skip)
        .limit(limit)
    )
    results = result.scalars().all()

    return results


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除任务")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    删除任务及其结果

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Raises:
        HTTPException: 任务不存在或无权删除
    """
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 不能删除正在运行的任务
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running task",
        )

    await db.delete(task)
    await db.commit()

    logger.info(f"Task {task_id} deleted by user {current_user.id}")


@router.post("/tasks/{task_id}/execute", response_model=EvaluationTaskResponse, summary="手动执行任务")
async def execute_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant),
):
    """
    手动执行评估任务

    Args:
        task_id: 任务ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        current_tenant: 当前租户

    Returns:
        EvaluationTaskResponse: 任务信息

    Raises:
        HTTPException: 任务不存在或无法执行
    """
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.tenant_id == current_tenant.id,
            )
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 权限检查
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 只能执行 pending 或 failed 状态的任务
    if task.status not in ["pending", "failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be executed (current status: {task.status})",
        )

    # 添加后台任务
    background_tasks.add_task(
        TaskExecutor.execute_task,
        task.id,
        current_tenant.id,
        db
    )

    logger.info(f"Task {task_id} manually triggered by user {current_user.id}")

    return task

