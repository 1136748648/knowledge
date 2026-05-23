import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_local_token,
    get_current_active_user,
    hash_password,
    verify_password,
    verify_keycloak_token,
)
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
    - 系统未初始化时 -> 内置管理员直接登录（无需数据库）
    - 系统已初始化后 -> 内置管理员失效，走数据库验证
    """
    from app.main import BUILTIN_ADMIN_PASS, BUILTIN_ADMIN_USER, SYSTEM_INITIALIZED

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
    from app.models.local_user import LocalUser

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")

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


class KeycloakLoginResponse(BaseModel):
    authorization_url: str


@router.get("/keycloak/login", response_model=KeycloakLoginResponse)
async def keycloak_login():
    """
    Keycloak OAuth2 登录入口
    返回 Keycloak 授权页面 URL，前端需重定向到该 URL
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.KEYCLOAK_SERVER_URL:
        raise HTTPException(status_code=503, detail="Keycloak 未配置")

    import secrets
    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth"

    params = {
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }

    auth_url = f"{redirect_uri}?{urlencode(params)}"
    logger.info(f"Keycloak login initiated, state={state}")
    return KeycloakLoginResponse(authorization_url=auth_url)


class KeycloakCallbackRequest(BaseModel):
    code: str
    state: str


@router.post("/keycloak/callback", response_model=TokenResponse)
async def keycloak_callback(data: KeycloakCallbackRequest, db: AsyncSession = Depends(get_db)):
    """
    Keycloak OAuth2 回调接口
    用授权码换取 Keycloak token，然后生成本地 token 返回
    """
    from app.config import get_settings
    from app.models.local_user import LocalUser
    settings = get_settings()

    if not settings.KEYCLOAK_SERVER_URL:
        raise HTTPException(status_code=503, detail="Keycloak 未配置")

    import httpx

    token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
    redirect_uri = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth"

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.KEYCLOAK_CLIENT_ID,
                    "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
                    "code": data.code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )

            if token_response.status_code != 200:
                logger.error(f"Keycloak token exchange failed: {token_response.text}")
                raise HTTPException(status_code=401, detail="Keycloak 认证失败")

            token_data = token_response.json()
            keycloak_access_token = token_data.get("access_token")

            if not keycloak_access_token:
                raise HTTPException(status_code=401, detail="Keycloak 未返回 access_token")

            user_context = verify_keycloak_token(keycloak_access_token)
            if not user_context:
                raise HTTPException(status_code=401, detail="Keycloak token 验证失败")

            result = await db.execute(
                select(LocalUser).where(LocalUser.username == user_context.username)
            )
            local_user = result.scalar_one_or_none()

            if local_user:
                user_id = str(local_user.id)
                roles = local_user.roles or user_context.roles
                dept_id = local_user.dept_id or user_context.dept_id
            else:
                user_id = user_context.user_id
                roles = user_context.roles or ["employee"]
                dept_id = user_context.dept_id

            logger.info(f"Keycloak login success for user: {user_context.username}")
            return create_local_token(
                user_id=user_id,
                username=user_context.username,
                roles=roles,
                dept_id=dept_id,
            )

    except httpx.HTTPError as e:
        logger.error(f"Keycloak HTTP error: {e}")
        raise HTTPException(status_code=503, detail="无法连接 Keycloak 服务器")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keycloak callback error: {e}")
        raise HTTPException(status_code=500, detail="Keycloak 登录处理失败")
