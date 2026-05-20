import casbin
import casbin_sqlalchemy_adapter
from functools import lru_cache

from app.config import get_settings

settings = get_settings()

# Casbin RBAC 模型定义
RBAC_MODEL = """
[request_definition]
r = sub, obj, act, scope

[policy_definition]
p = sub, obj, act, scope

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act && r.scope == p.scope
"""


@lru_cache()
def get_enforcer() -> casbin.Enforcer:
    """获取 Casbin enforcer 实例（缓存）"""
    # 使用内存适配器，后续可替换为数据库适配器
    adapter = casbin_sqlalchemy_adapter.Adapter(settings.DATABASE_URL)
    model = casbin.model.Model()
    model.load_model_from_text(RBAC_MODEL)
    enforcer = casbin.Enforcer(model, adapter)
    return enforcer


async def check_permission(user_roles: list[str], resource: str, action: str, scope: str) -> bool:
    """检查用户是否有权限执行操作"""
    enforcer = get_enforcer()
    for role in user_roles:
        if enforcer.enforce(role, resource, action, scope):
            return True
    return False


async def get_user_permissions(user_roles: list[str]) -> list[dict]:
    """获取用户所有权限"""
    enforcer = get_enforcer()
    permissions = []
    for role in user_roles:
        perms = enforcer.get_permissions_for_user(role)
        for perm in perms:
            permissions.append({
                "sub": perm[0],
                "obj": perm[1],
                "act": perm[2],
                "scope": perm[3] if len(perm) > 3 else None,
            })
    return permissions
