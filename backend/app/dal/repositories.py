from typing import Any, List, Optional, Type

import uuid
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.base import Repository
from app.dal.postgres import PostgreSQLAdapter


class ModelRepository(Repository):
    def __init__(self, adapter: PostgreSQLAdapter, model_class: Type):
        super().__init__(adapter)
        self.model_class = model_class
        self.table_name = model_class.__tablename__

    async def _get_session(self) -> AsyncSession:
        return await self.adapter.get_session()

    async def get_by_id(self, id: Any) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.model_class))
            return result.scalars().all()

    async def create(self, entity: Any) -> Any:
        async with await self._get_session() as session:
            session.add(entity)
            await session.flush()
            await session.commit()
            return entity

    async def update(self, entity: Any) -> Any:
        async with await self._get_session() as session:
            session.add(entity)
            await session.flush()
            await session.commit()
            return entity

    async def delete(self, id: Any) -> bool:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            entity = result.scalar_one_or_none()
            if entity:
                await session.delete(entity)
                await session.commit()
                return True
            return False


class EmployeeRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.employee import Employee
        super().__init__(adapter, Employee)
        self.Employee = Employee

    async def get_by_id(self, employee_id: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.Employee).where(self.Employee.employee_id == employee_id)
            )
            return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.Employee).where(self.Employee.employee_id == employee_id)
            )
            return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.Employee).where(self.Employee.employee_id == username)
            )
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.Employee).where(self.Employee.name == name)
            )
            return result.scalar_one_or_none()

    async def list_by_department(self, department: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.Employee).where(self.Employee.department == department)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def count_by_department(self, department: str) -> int:
        async with await self._get_session() as session:
            query = select(func.count()).select_from(self.Employee).where(self.Employee.department == department)
            result = await session.execute(query)
            return result.scalar() or 0

    async def get_by_dept_id(self, dept_id: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.Employee).where(self.Employee.dept_id == dept_id)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def list_active_users(self, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.Employee).where(self.Employee.is_active == True)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()


class ConversationRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.conversation import Conversation
        super().__init__(adapter, Conversation)
        self.Conversation = Conversation

    async def list_by_user_id(self, user_id: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.Conversation).where(self.Conversation.user_id == user_id)
            query = query.order_by(self.Conversation.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def list_by_dept_id(self, dept_id: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.Conversation).where(self.Conversation.dept_id == dept_id)
            query = query.order_by(self.Conversation.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()


class AuditLogRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.audit import AuditLog
        super().__init__(adapter, AuditLog)
        self.AuditLog = AuditLog

    async def list_by_user_id(self, user_id: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.AuditLog).where(self.AuditLog.user_id == user_id)
            query = query.order_by(self.AuditLog.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def list_by_action(self, action: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.AuditLog).where(self.AuditLog.action == action)
            query = query.order_by(self.AuditLog.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.AuditLog)
            
            conditions = []
            if start_time:
                conditions.append(self.AuditLog.created_at >= start_time)
            if end_time:
                conditions.append(self.AuditLog.created_at <= end_time)
            if user_id:
                conditions.append(self.AuditLog.user_id == user_id)
            if action:
                conditions.append(self.AuditLog.action == action)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(self.AuditLog.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await session.execute(query)
            return result.scalars().all()

    async def count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> int:
        async with await self._get_session() as session:
            query = select(func.count(self.AuditLog.id))
            
            conditions = []
            if start_time:
                conditions.append(self.AuditLog.created_at >= start_time)
            if end_time:
                conditions.append(self.AuditLog.created_at <= end_time)
            if user_id:
                conditions.append(self.AuditLog.user_id == user_id)
            if action:
                conditions.append(self.AuditLog.action == action)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0

    async def export(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 10000
    ) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.AuditLog)
            
            conditions = []
            if start_time:
                conditions.append(self.AuditLog.created_at >= start_time)
            if end_time:
                conditions.append(self.AuditLog.created_at <= end_time)
            if user_id:
                conditions.append(self.AuditLog.user_id == user_id)
            if action:
                conditions.append(self.AuditLog.action == action)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(self.AuditLog.created_at.desc())
            query = query.limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()


class CasbinRuleRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.casbin import CasbinRule
        super().__init__(adapter, CasbinRule)
        self.CasbinRule = CasbinRule

    async def get_by_ptype(self, ptype: str) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.CasbinRule).where(self.CasbinRule.ptype == ptype))
            return result.scalars().all()


class SystemConfigRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.system_config import SystemConfig
        super().__init__(adapter, SystemConfig)
        self.SystemConfig = SystemConfig

    async def get_by_category(self, category: str) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.SystemConfig).where(self.SystemConfig.category == category))
            return result.scalars().all()

    async def get_by_key(self, category: str, key: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.SystemConfig).where(
                    self.SystemConfig.category == category,
                    self.SystemConfig.key == key
                )
            )
            return result.scalar_one_or_none()


class SearchEventRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.heatmap import SearchEvent
        super().__init__(adapter, SearchEvent)
        self.SearchEvent = SearchEvent

    async def list_by_user_id(self, user_id: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.SearchEvent).where(self.SearchEvent.user_id == user_id)
            query = query.order_by(self.SearchEvent.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()


class HeatmapStatsRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.heatmap import HeatmapStats
        super().__init__(adapter, HeatmapStats)
        self.HeatmapStats = HeatmapStats

    async def get_by_type(self, stat_type: str) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.HeatmapStats).where(self.HeatmapStats.stat_type == stat_type)
            )
            return result.scalars().all()

    async def get_by_type_and_date(self, stat_type: str, stat_date: datetime.date) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.HeatmapStats).where(
                    self.HeatmapStats.stat_type == stat_type,
                    self.HeatmapStats.stat_date == stat_date
                )
            )
            return result.scalars().all()

    async def get_by_type_key_date(self, stat_type: str, stat_key: str, stat_date: datetime.date) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.HeatmapStats).where(
                    self.HeatmapStats.stat_type == stat_type,
                    self.HeatmapStats.stat_key == stat_key,
                    self.HeatmapStats.stat_date == stat_date
                )
            )
            return result.scalar_one_or_none()
