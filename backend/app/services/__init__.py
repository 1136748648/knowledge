from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
    AuditLogRepository,
)
from .wiki_service import WikiService
from .auth_service import AuthService
from .knowledge_service import KnowledgeService
from .heatmap_service import HeatmapService
from .admin_service import AdminService
from .qa_service import QAService


@lru_cache()
def get_wiki_page_repo() -> WikiPageRepository:
    adapter = get_adapter()
    return WikiPageRepository(adapter)


@lru_cache()
def get_wiki_version_repo() -> WikiPageVersionRepository:
    adapter = get_adapter()
    return WikiPageVersionRepository(adapter)


def get_wiki_service(
    page_repo: WikiPageRepository = Depends(get_wiki_page_repo),
    version_repo: WikiPageVersionRepository = Depends(get_wiki_version_repo),
) -> WikiService:
    return WikiService(page_repo, version_repo)


@lru_cache()
def get_local_user_repo() -> LocalUserRepository:
    adapter = get_adapter()
    return LocalUserRepository(adapter)


def get_auth_service(
    user_repo: LocalUserRepository = Depends(get_local_user_repo),
) -> AuthService:
    return AuthService(user_repo)


@lru_cache()
def get_knowledge_nav_repo() -> KnowledgeNavRepository:
    adapter = get_adapter()
    return KnowledgeNavRepository(adapter)


@lru_cache()
def get_nav_content_link_repo() -> NavContentLinkRepository:
    adapter = get_adapter()
    return NavContentLinkRepository(adapter)


def get_knowledge_service(
    nav_repo: KnowledgeNavRepository = Depends(get_knowledge_nav_repo),
    link_repo: NavContentLinkRepository = Depends(get_nav_content_link_repo),
) -> KnowledgeService:
    return KnowledgeService(nav_repo, link_repo)


@lru_cache()
def get_search_event_repo() -> SearchEventRepository:
    adapter = get_adapter()
    return SearchEventRepository(adapter)


@lru_cache()
def get_heatmap_stats_repo() -> HeatmapStatsRepository:
    adapter = get_adapter()
    return HeatmapStatsRepository(adapter)


def get_heatmap_service(
    search_event_repo: SearchEventRepository = Depends(get_search_event_repo),
    stats_repo: HeatmapStatsRepository = Depends(get_heatmap_stats_repo),
) -> HeatmapService:
    return HeatmapService(search_event_repo, stats_repo)


@lru_cache()
def get_audit_log_repo() -> AuditLogRepository:
    adapter = get_adapter()
    return AuditLogRepository(adapter)


def get_admin_service(
    audit_log_repo: AuditLogRepository = Depends(get_audit_log_repo),
) -> AdminService:
    return AdminService(audit_log_repo)


def get_qa_service() -> QAService:
    return QAService()


__all__ = [
    "WikiService",
    "get_wiki_service",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthService",
    "get_auth_service",
    "get_local_user_repo",
    "KnowledgeService",
    "get_knowledge_service",
    "get_knowledge_nav_repo",
    "get_nav_content_link_repo",
    "HeatmapService",
    "get_heatmap_service",
    "get_search_event_repo",
    "get_heatmap_stats_repo",
    "AdminService",
    "get_admin_service",
    "get_audit_log_repo",
    "QAService",
    "get_qa_service",
]