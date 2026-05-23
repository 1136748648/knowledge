from fastapi import APIRouter, Depends, Query, HTTPException

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, AuditLogResponse, PolicyCreate, RoleAssign
from app.services import get_admin_service, AdminService

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.get_audit_logs(current_user, user_id, action, page, page_size)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/users")
async def list_users(
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.list_users(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/permissions")
async def get_permissions(
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.get_permissions(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/policies")
async def create_policy(
    policy: PolicyCreate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.create_policy(current_user, policy.sub, policy.obj, policy.act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/policies")
async def delete_policy(
    sub: str,
    obj: str,
    act: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.delete_policy(current_user, sub, obj, act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/roles/assign")
async def assign_role(
    role_data: RoleAssign,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.assign_role(current_user, role_data.user, role_data.role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/roles/assign")
async def unassign_role(
    user: str,
    role: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.unassign_role(current_user, user, role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/roles/{user}")
async def get_user_role_list(
    user: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.get_user_roles(current_user, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))