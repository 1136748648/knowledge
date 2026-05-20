import logging

from app.models.schemas import UserContext
from app.core.casbin_policy import check_permission

logger = logging.getLogger(__name__)


class PermissionAgent:
    def __init__(self, user: UserContext):
        self.user = user

    async def check_access(self, resource: str, action: str, scope: str) -> bool:
        """检查用户是否有权限访问资源"""
        return await check_permission(self.user.roles, resource, action, scope)

    async def get_accessible_scopes(self, resource: str, action: str) -> list[str]:
        """获取用户可访问的范围列表"""
        scopes = []
        for scope in ["own", "department", "all"]:
            if await check_permission(self.user.roles, resource, action, scope):
                scopes.append(scope)
        return scopes

    async def filter_sensitive_fields(self, data: dict, resource_type: str) -> dict:
        """根据权限过滤敏感字段"""
        sensitive_fields = {
            "employees": ["salary", "phone", "clearance_level"],
            "conversations": ["embedding_id"],
        }

        fields_to_mask = sensitive_fields.get(resource_type, [])

        # HR 和管理员可以看到所有字段
        if "hr" in self.user.roles or "admin" in self.user.roles:
            return data

        # 其他角色脱敏
        filtered = data.copy()
        for field in fields_to_mask:
            if field in filtered:
                filtered[field] = "***"
        return filtered
