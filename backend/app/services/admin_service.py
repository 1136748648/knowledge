from app.core.casbin_policy import (
    check_permission,
    get_user_permissions,
    add_policy,
    remove_policy,
    add_role_for_user,
    remove_role_for_user,
    get_user_roles,
)
from app.dal.repositories import AuditLogRepository
from app.models.schemas import UserContext


class AdminService:
    def __init__(self, audit_log_repo: AuditLogRepository):
        self.audit_log_repo = audit_log_repo

    async def check_admin_access(self, user: UserContext) -> bool:
        return "admin" in user.roles

    async def check_policy_manage(self, user: UserContext) -> bool:
        return await check_permission(user.roles, "casbin_policy", "manage")

    async def get_audit_logs(
        self,
        user: UserContext,
        target_user_id: str | None = None,
        action: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        return await self.audit_log_repo.get_logs(target_user_id, action, page, page_size)

    async def list_users(self, user: UserContext):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        return []

    async def get_permissions(self, user: UserContext):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        if not await self.check_policy_manage(user):
            raise PermissionError("Permission denied")
        return await get_user_permissions(user.roles)

    async def create_policy(self, user: UserContext, sub: str, obj: str, act: str):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        if not await self.check_policy_manage(user):
            raise PermissionError("Permission denied")
        return await add_policy(sub, obj, act)

    async def delete_policy(self, user: UserContext, sub: str, obj: str, act: str):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        if not await self.check_policy_manage(user):
            raise PermissionError("Permission denied")
        return await remove_policy(sub, obj, act)

    async def assign_role(self, user: UserContext, target_user: str, role: str):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        if not await self.check_policy_manage(user):
            raise PermissionError("Permission denied")
        return await add_role_for_user(target_user, role)

    async def unassign_role(self, user: UserContext, target_user: str, role: str):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        if not await self.check_policy_manage(user):
            raise PermissionError("Permission denied")
        return await remove_role_for_user(target_user, role)

    async def get_user_roles(self, user: UserContext, target_user: str):
        if not await self.check_admin_access(user):
            raise PermissionError("Admin access required")
        roles = await get_user_roles(target_user)
        return {"user": target_user, "roles": roles}