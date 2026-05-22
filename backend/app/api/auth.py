import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, get_current_active_user, create_local_token, verify_password
from app.db.session import get_db
from app.models.schemas import UserContext

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfoResponse(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]
    dept_id: str | None = None


@router.post("/token", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    登录接口：
    - 系统未初始化时 → 内置管理员直接登录（无需数据库）
    - 系统已初始化后 → 内置管理员失效，走数据库验证
    """
    from app.main import SYSTEM_INITIALIZED, BUILTIN_ADMIN_USER, BUILTIN_ADMIN_PASS

    # 内置管理员（仅系统未初始化时可用）
    if data.username == BUILTIN_ADMIN_USER and data.password == BUILTIN_ADMIN_PASS:
        if not SYSTEM_INITIALIZED:
            logger.info("Built-in admin login (system not initialized)")
            return create_local_token(
                user_id="builtin-admin",
                username=BUILTIN_ADMIN_USER,
                roles=["admin"],
            )
        else:
            raise HTTPException(status_code=403, detail="内置管理员已停用，请使用您创建的管理员账号登录")

    # 数据库验证
    try:
        from app.models.local_user import LocalUser
        result = await db.execute(
            select(LocalUser).where(LocalUser.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        return create_local_token(
            user_id=str(user.id),
            username=user.username,
            roles=user.roles or ["employee"],
            dept_id=user.dept_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login DB error: {e}")
        raise HTTPException(status_code=503, detail="数据库不可用，请先完成系统初始化")


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(current_user: UserContext = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserInfoResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        roles=current_user.roles,
        dept_id=current_user.dept_id,
    )


@router.post("/logout")
async def logout(current_user: UserContext = Depends(get_current_active_user)):
    return {"message": "Logged out successfully"}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户密码"""
    from app.core.security import hash_password
    from app.models.local_user import LocalUser

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")

    # 内置管理员不允许修改密码（它没有数据库记录）
    if current_user.user_id == "builtin-admin":
        raise HTTPException(status_code=400, detail="内置管理员不支持修改密码，请先完成系统初始化")

    result = await db.execute(
        select(LocalUser).where(LocalUser.id == int(current_user.user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    user.password_hash = hash_password(data.new_password)
    await db.commit()
    logger.info(f"User {user.username} changed password")
    return {"message": "密码修改成功"}
