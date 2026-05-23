from fastapi import APIRouter, Depends, Query, HTTPException

from app.dal import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.schemas import UserContext, AuditLogResponse, PolicyCreate, RoleAssign
from app.core.casbin_policy import (
    check_permission,
    get_user_permissions,
    add_policy,
    remove_policy,
    add_role_for_user,
    remove_role_for_user,
    get_user_roles,
)

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return []


@router.get("/users")
async def list_users(
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return []


@router.get("/permissions")
async def get_permissions(
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not await check_permission(current_user.roles, "casbin_policy", "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    permissions = await get_user_permissions(current_user.roles)
    return permissions


@router.post("/policies")
async def create_policy(
    policy: PolicyCreate,
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not await check_permission(current_user.roles, "casbin_policy", "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    result = await add_policy(policy.sub, policy.obj, policy.act)
    return {"success": result}


@router.delete("/policies")
async def delete_policy(
    sub: str,
    obj: str,
    act: str,
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not await check_permission(current_user.roles, "casbin_policy", "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    result = await remove_policy(sub, obj, act)
    return {"success": result}


@router.post("/roles/assign")
async def assign_role(
    role_data: RoleAssign,
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not await check_permission(current_user.roles, "casbin_policy", "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    result = await add_role_for_user(role_data.user, role_data.role)
    return {"success": result}


@router.delete("/roles/assign")
async def unassign_role(
    user: str,
    role: str,
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not await check_permission(current_user.roles, "casbin_policy", "manage"):
        raise HTTPException(status_code=403, detail="Permission denied")
    result = await remove_role_for_user(user, role)
    return {"success": result}


@router.get("/roles/{user}")
async def get_user_role_list(
    user: str,
    current_user: UserContext = Depends(get_current_active_user),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    roles = await get_user_roles(user)
    return {"user": user, "roles": roles}
