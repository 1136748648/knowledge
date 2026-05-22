from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.schemas import UserContext, AuditLogResponse

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取审计日志（仅管理员）"""
    if "admin" not in current_user.roles:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    # TODO: 实现审计日志查询
    return []


@router.get("/users")
async def list_users(
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取用户列表（仅管理员）"""
    if "admin" not in current_user.roles:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    # TODO: 从 Keycloak 获取用户列表
    return []


@router.get("/permissions")
async def get_permissions(
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取权限策略列表（仅管理员）"""
    if "admin" not in current_user.roles:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    # TODO: 从 Casbin 获取策略
    return []
