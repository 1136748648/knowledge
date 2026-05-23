from .base import DatabaseAdapter, Repository, Transactional
from .postgres import PostgreSQLAdapter, get_base
from .registry import get_adapter, get_repository, register_repository
from .repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    EmployeeRepository,
    ConversationRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
    AuditLogRepository,
    CasbinRuleRepository,
    SystemConfigRepository,
    LocalUserRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
)

Base = get_base()


async def get_db():
    """FastAPI dependency for getting a database session"""
    adapter = get_adapter()
    async with await adapter.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "DatabaseAdapter",
    "Repository",
    "Transactional",
    "PostgreSQLAdapter",
    "Base",
    "get_db",
    "get_adapter",
    "get_repository",
    "register_repository",
    "WikiPageRepository",
    "WikiPageVersionRepository",
    "EmployeeRepository",
    "ConversationRepository",
    "KnowledgeNavRepository",
    "NavContentLinkRepository",
    "AuditLogRepository",
    "CasbinRuleRepository",
    "SystemConfigRepository",
    "LocalUserRepository",
    "SearchEventRepository",
    "HeatmapStatsRepository",
]
