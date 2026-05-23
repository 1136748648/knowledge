from typing import Any, Dict, List, Optional, Type

import uuid
from datetime import datetime

from sqlalchemy import select, func
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


class WikiPageRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.wiki import WikiPage
        super().__init__(adapter, WikiPage)
        self.WikiPage = WikiPage

    async def get_by_slug(self, slug: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.WikiPage).where(self.WikiPage.slug == slug)
            )
            return result.scalar_one_or_none()

    async def list_by_parent(self, parent_id: Optional[uuid.UUID], page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.WikiPage)
            if parent_id:
                query = query.where(self.WikiPage.parent_id == parent_id)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def list_by_sensitivity(self, sensitivity: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.WikiPage).where(self.WikiPage.sensitivity == sensitivity)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()

    async def search(self, query: str, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            search_query = (
                select(self.WikiPage)
                .where(
                    func.to_tsvector("simple", self.WikiPage.title + " " + self.WikiPage.content)
                    .match(query, postgresql_regconfig="simple")
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await session.execute(search_query)
            return result.scalars().all()


class WikiPageVersionRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.wiki import WikiPageVersion
        super().__init__(adapter, WikiPageVersion)
        self.WikiPageVersion = WikiPageVersion

    async def get_by_page_id(self, page_id: uuid.UUID) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.WikiPageVersion)
                .where(self.WikiPageVersion.page_id == page_id)
                .order_by(self.WikiPageVersion.version.desc())
            )
            return result.scalars().all()

    async def get_max_version(self, page_id: uuid.UUID) -> int:
        async with await self._get_session() as session:
            result = await session.execute(
                select(func.max(self.WikiPageVersion.version)).where(self.WikiPageVersion.page_id == page_id)
            )
            return result.scalar() or 0


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


class KnowledgeNavRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.navigation import KnowledgeNav
        super().__init__(adapter, KnowledgeNav)
        self.KnowledgeNav = KnowledgeNav

    async def get_root_nodes(self) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.KnowledgeNav).where(self.KnowledgeNav.parent_id.is_(None)).order_by(self.KnowledgeNav.sort_order)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_parent_id(self, parent_id: uuid.UUID) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.KnowledgeNav).where(self.KnowledgeNav.parent_id == parent_id).order_by(self.KnowledgeNav.sort_order)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_path(self, path: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.KnowledgeNav).where(self.KnowledgeNav.path == path))
            return result.scalar_one_or_none()


class NavContentLinkRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.navigation import NavContentLink
        super().__init__(adapter, NavContentLink)
        self.NavContentLink = NavContentLink

    async def get_by_nav_id(self, nav_id: uuid.UUID) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.NavContentLink).where(self.NavContentLink.nav_id == nav_id))
            return result.scalars().all()

    async def get_by_content(self, content_type: str, content_id: str) -> List[Any]:
        async with await self._get_session() as session:
            result = await session.execute(
                select(self.NavContentLink).where(
                    self.NavContentLink.content_type == content_type,
                    self.NavContentLink.content_id == content_id
                )
            )
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


class LocalUserRepository(ModelRepository):
    def __init__(self, adapter: PostgreSQLAdapter):
        from app.models.local_user import LocalUser
        super().__init__(adapter, LocalUser)
        self.LocalUser = LocalUser

    async def get_by_username(self, username: str) -> Optional[Any]:
        async with await self._get_session() as session:
            result = await session.execute(select(self.LocalUser).where(self.LocalUser.username == username))
            return result.scalar_one_or_none()

    async def list_active_users(self, page: int = 1, page_size: int = 20) -> List[Any]:
        async with await self._get_session() as session:
            query = select(self.LocalUser).where(self.LocalUser.is_active == True)
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            return result.scalars().all()


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
