# -*- coding: utf-8 -*-
"""异步任务执行引擎"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import EvaluationTask, EvaluationResult
from app.services.evaluation import EvaluationService


class TaskExecutor:
    """任务执行器 - 负责异步执行评估任务"""

    @staticmethod
    async def execute_task(
        task_id: int,
        tenant_id: int,
        db: AsyncSession,
        dataset: Optional[list] = None
    ):
        """
        执行评估任务

        Args:
            task_id: 任务ID
            tenant_id: 租户ID
            db: 数据库会话
            dataset: 数据集(如果已提供)
        """
        logger.info(f"Starting task execution: task_id={task_id}, tenant_id={tenant_id}")

        try:
            # 1. 查询任务
            result = await db.execute(
                select(EvaluationTask).where(
                    and_(
                        EvaluationTask.id == task_id,
                        EvaluationTask.tenant_id == tenant_id
                    )
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task {task_id} not found")
                return

            # 2. 更新任务状态为运行中
            task.status = "running"
            task.started_at = datetime.now()
            await db.commit()

            # 3. 加载数据集
            if dataset is None:
                # 从task.config中获取数据集
                config = task.config
                dataset = config.get("dataset", [])

            if not dataset:
                raise ValueError("Dataset is empty")

            task.dataset_size = len(dataset)
            await db.commit()

            # 4. 执行评估
            logger.info(f"Executing evaluation for task {task_id} with {len(dataset)} samples")

            results = await EvaluationService.evaluate(
                config=task.config,
                dataset=dataset,
                task_id=task_id,
                tenant_id=tenant_id
            )

            # 5. 保存结果
            logger.info(f"Saving {len(results)} results for task {task_id}")

            for result_data in results:
                result = EvaluationResult(**result_data)
                db.add(result)

            # 6. 更新任务状态
            completed_count = len([r for r in results if r.get("result_type") != "error"])
            error_count = len(results) - completed_count

            if error_count == len(results):
                # 全部失败
                task.status = "failed"
                task.error_message = "All samples failed to evaluate"
            elif error_count > 0:
                # 部分失败
                task.status = "completed"
                task.error_message = f"{error_count} samples failed"
            else:
                # 全部成功
                task.status = "completed"

            task.progress = 100.0
            task.completed_at = datetime.now()

            # 计算平均分
            scores = [r["score"] for r in results if r.get("score") is not None]
            if scores:
                avg_score = sum(scores) / len(scores)
                task.config["average_score"] = avg_score
                task.config["completed_count"] = completed_count
                task.config["error_count"] = error_count

            await db.commit()

            logger.info(
                f"Task {task_id} completed: "
                f"{completed_count} successful, {error_count} failed"
            )

        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}", exc_info=True)

            # 尝试更新任务状态为失败
            try:
                result = await db.execute(
                    select(EvaluationTask).where(EvaluationTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    task.completed_at = datetime.now()
                    await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update task status: {db_error}")

    @staticmethod
    def get_task_progress(task: EvaluationTask) -> Dict[str, Any]:
        """
        获取任务进度

        Args:
            task: 任务对象

        Returns:
            进度信息
        """
        return {
            "task_id": task.id,
            "status": task.status,
            "progress": float(task.progress) if task.progress else 0.0,
            "dataset_size": task.dataset_size,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
        }
