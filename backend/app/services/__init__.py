from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dal import get_adapter, get_db
from app.dal.repositories import (
    EmployeeRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
    AuditLogRepository,
)
from .auth_service import AuthService
from .heatmap_service import HeatmapService
from .admin_service import AdminService
from .qa_service import QAService
from .storage_service import StorageService
from .config_service import ConfigService


@lru_cache()
def get_employee_repo() -> EmployeeRepository:
    adapter = get_adapter()
    return EmployeeRepository(adapter)


def get_auth_service(
    user_repo: EmployeeRepository = Depends(get_employee_repo),
) -> AuthService:
    return AuthService(user_repo)


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


def get_admin_service() -> AdminService:
    return AdminService()


def get_qa_service() -> QAService:
    return QAService()


def get_config_service(db: AsyncSession = Depends(get_db)) -> ConfigService:
    return ConfigService(db)


def get_storage_service(
    config_service: ConfigService = Depends(get_config_service),
) -> StorageService:
    return StorageService(config_service)


__all__ = [
    "AuthService",
    "get_auth_service",
    "get_employee_repo",
    "HeatmapService",
    "get_heatmap_service",
    "get_search_event_repo",
    "get_heatmap_stats_repo",
    "AdminService",
    "get_admin_service",
    "get_audit_log_repo",
    "QAService",
    "get_qa_service",
    "StorageService",
    "get_storage_service",
    "ConfigService",
    "get_config_service",
]
