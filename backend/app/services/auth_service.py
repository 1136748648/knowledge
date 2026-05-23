import logging
from app.dal.repositories import LocalUserRepository
from app.core.security import hash_password, verify_password, create_local_token
from app.models.schemas import UserContext

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: LocalUserRepository):
        self.user_repo = user_repo

    async def authenticate(self, username: str, password: str) -> dict:
        user = await self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.password_hash):
            return {"success": False, "error": "用户名或密码错误"}

        if not user.is_active:
            return {"success": False, "error": "账号已被禁用"}

        token = create_local_token(
            user_id=str(user.id),
            username=user.username,
            roles=user.roles or ["employee"],
            dept_id=user.dept_id,
        )

        return {
            "success": True,
            "access_token": token["access_token"],
            "token_type": token["token_type"],
            "expires_in": token["expires_in"],
        }

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        if len(new_password) < 6:
            return {"success": False, "error": "新密码至少 6 位"}

        if user_id == "builtin-admin":
            return {"success": False, "error": "内置管理员不支持修改密码"}

        user = await self.user_repo.get_by_id(int(user_id))
        if not user:
            return {"success": False, "error": "用户不存在"}

        if not verify_password(old_password, user.password_hash):
            return {"success": False, "error": "原密码错误"}

        user.password_hash = hash_password(new_password)
        await self.user_repo.update(user)
        logger.info(f"User {user.username} changed password")

        return {"success": True, "message": "密码修改成功"}

    async def get_user_info(self, current_user: UserContext) -> dict:
        return {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "roles": current_user.roles,
            "dept_id": current_user.dept_id,
        }

    async def keycloak_callback(self, keycloak_username: str) -> dict:
        local_user = await self.user_repo.get_by_username(keycloak_username)

        if local_user:
            return {
                "user_id": str(local_user.id),
                "roles": local_user.roles or ["employee"],
                "dept_id": local_user.dept_id,
            }
        else:
            return {
                "user_id": keycloak_username,
                "roles": ["employee"],
                "dept_id": None,
            }