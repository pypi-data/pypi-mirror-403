from typing import Optional, Any
from datetime import datetime
from uuid import uuid4
from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from ..db.models.feedback import FeedbackBase
from ..db.database import DatabaseManager


class FeedbackStorage:
    """反馈存储管理器 - 使用 PostgreSQL 数据库存储"""

    def __init__(self, database_manager: DatabaseManager = None):
        self.database_manager = database_manager
        self._db = None
        # 内存存储后备(用于数据库未配置时)
        self._storage: dict[str, dict[str, Any]] = {}
        self._task_index: dict[str, list[str]] = {}
        self._workflow_index: dict[str, list[str]] = {}

    @property
    def db(self):
        """延迟获取数据库连接"""
        if self._db is None and self.database_manager is not None:
            self._db = self.database_manager.get_default_postgres_database()
        return self._db

    async def create_feedback(
        self,
        trace_id: str,
        workflow_name: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        service_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """创建新的反馈记录"""
        if self.db is None:
            logger.warning("数据库未初始化,使用内存存储(数据将在重启后丢失)")
            return self._create_feedback_in_memory(trace_id, workflow_name, rating, comment, metadata, service_name)

        try:
            feedback_id = uuid4()
            created_at = datetime.now()

            feedback = FeedbackBase(
                feedback_id=feedback_id,
                trace_id=trace_id,
                service_name=service_name,
                workflow_name=workflow_name,
                rating=rating,
                comment=comment,
                extra_metadata=metadata or {},
                created_at=created_at,
            )

            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                session.add(feedback)
                await session.commit()
                await session.refresh(feedback)

                logger.info(f"创建反馈: feedback_id={feedback_id}, trace_id={trace_id}, workflow={workflow_name}")
                return feedback.to_dict()

        except SQLAlchemyError as e:
            logger.error(f"数据库创建反馈失败: {e}")
            raise
        except Exception as e:
            logger.error(f"创建反馈失败: {e}")
            raise

    async def get_feedback(self, feedback_id: str) -> Optional[dict[str, Any]]:
        """根据反馈ID获取反馈"""
        if self.db is None:
            return self._get_feedback_from_memory(feedback_id)

        try:
            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                result = await session.execute(
                    select(FeedbackBase).where(FeedbackBase.feedback_id == feedback_id)
                )
                feedback = result.scalar_one_or_none()
                return feedback.to_dict() if feedback else None

        except SQLAlchemyError as e:
            logger.error(f"查询反馈失败: {e}")
            return None

    async def get_feedbacks_by_trace(self, trace_id: str) -> list[dict[str, Any]]:
        """根据trace_id获取所有反馈"""
        if self.db is None:
            return self._get_feedbacks_by_trace_from_memory(trace_id)

        try:
            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                result = await session.execute(
                    select(FeedbackBase)
                    .where(FeedbackBase.trace_id == trace_id)
                    .order_by(FeedbackBase.created_at.desc())
                )
                feedbacks = result.scalars().all()
                return [f.to_dict() for f in feedbacks]

        except SQLAlchemyError as e:
            logger.error(f"查询任务反馈失败: {e}")
            return []

    async def get_feedbacks_by_workflow(self, workflow_name: str) -> list[dict[str, Any]]:
        """根据工作流名称获取所有反馈"""
        if self.db is None:
            return self._get_feedbacks_by_workflow_from_memory(workflow_name)

        try:
            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                result = await session.execute(
                    select(FeedbackBase)
                    .where(FeedbackBase.workflow_name == workflow_name)
                    .order_by(FeedbackBase.created_at.desc())
                )
                feedbacks = result.scalars().all()
                return [f.to_dict() for f in feedbacks]

        except SQLAlchemyError as e:
            logger.error(f"查询工作流反馈失败: {e}")
            return []

    async def get_all_feedbacks(self) -> list[dict[str, Any]]:
        """获取所有反馈"""
        if self.db is None:
            return self._get_all_feedbacks_from_memory()

        try:
            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                result = await session.execute(
                    select(FeedbackBase).order_by(FeedbackBase.created_at.desc())
                )
                feedbacks = result.scalars().all()
                return [f.to_dict() for f in feedbacks]

        except SQLAlchemyError as e:
            logger.error(f"查询所有反馈失败: {e}")
            return []

    async def delete_feedback(self, feedback_id: str) -> bool:
        """删除反馈"""
        if self.db is None:
            return self._delete_feedback_from_memory(feedback_id)

        try:
            session_factory = await self.db.get_session_factory()
            async with session_factory() as session:
                result = await session.execute(
                    select(FeedbackBase).where(FeedbackBase.feedback_id == feedback_id)
                )
                feedback = result.scalar_one_or_none()

                if not feedback:
                    return False

                await session.delete(feedback)
                await session.commit()

                logger.info(f"删除反馈: feedback_id={feedback_id}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"删除反馈失败: {e}")
            return False

    # ========== 内存存储后备方法(用于数据库未配置时) ==========

    def _create_feedback_in_memory(
        self,
        trace_id: str,
        workflow_name: str,
        rating: Optional[int],
        comment: Optional[str],
        metadata: Optional[dict[str, Any]],
        service_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """内存存储版本"""
        feedback_id = str(uuid4())
        created_at = datetime.now()

        feedback_data = {
            "feedback_id": feedback_id,
            "service_name": service_name,
            "trace_id": trace_id,
            "workflow_name": workflow_name,
            "rating": rating,
            "comment": comment,
            "metadata": metadata or {},
            "created_at": created_at,
        }

        self._storage[feedback_id] = feedback_data

        if trace_id not in self._task_index:
            self._task_index[trace_id] = []
        self._task_index[trace_id].append(feedback_id)

        if workflow_name not in self._workflow_index:
            self._workflow_index[workflow_name] = []
        self._workflow_index[workflow_name].append(feedback_id)

        logger.info(f"[内存存储]创建反馈: feedback_id={feedback_id}")
        return feedback_data

    def _get_feedback_from_memory(self, feedback_id: str) -> Optional[dict[str, Any]]:
        return self._storage.get(feedback_id)

    def _get_feedbacks_by_trace_from_memory(self, trace_id: str) -> list[dict[str, Any]]:
        feedback_ids = self._task_index.get(trace_id, [])
        return [self._storage[fid] for fid in feedback_ids if fid in self._storage]

    def _get_feedbacks_by_workflow_from_memory(self, workflow_name: str) -> list[dict[str, Any]]:
        feedback_ids = self._workflow_index.get(workflow_name, [])
        return [self._storage[fid] for fid in feedback_ids if fid in self._storage]

    def _get_all_feedbacks_from_memory(self) -> list[dict[str, Any]]:
        return list(self._storage.values())

    def _delete_feedback_from_memory(self, feedback_id: str) -> bool:
        if feedback_id not in self._storage:
            return False

        feedback = self._storage[feedback_id]
        trace_id = feedback["trace_id"]
        workflow_name = feedback["workflow_name"]

        if trace_id in self._task_index:
            self._task_index[trace_id].remove(feedback_id)
        if workflow_name in self._workflow_index:
            self._workflow_index[workflow_name].remove(feedback_id)

        del self._storage[feedback_id]
        logger.info(f"[内存存储]删除反馈: feedback_id={feedback_id}")
        return True


# 全局单例实例
feedback_storage = FeedbackStorage()
