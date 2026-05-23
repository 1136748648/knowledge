import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import (
    create_local_token,
    get_current_active_user,
    verify_keycloak_token,
)
from app.models.schemas import UserContext
from app.services import get_auth_service, AuthService

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
async def login(data: LoginRequest):
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
        from app.dal import get_adapter
        from app.dal.repositories import LocalUserRepository
        service = AuthService(LocalUserRepository(get_adapter()))
        
        result = await service.authenticate(data.username, data.password)
        
        if not result["success"]:
            raise HTTPException(status_code=401, detail=result["error"])

        return TokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login DB error: {e}")
        raise HTTPException(status_code=503, detail="数据库不可用，请先完成系统初始化")


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(
    service: AuthService = Depends(get_auth_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    result = await service.get_user_info(current_user)
    return UserInfoResponse(**result)


@router.post("/logout")
async def logout(current_user: UserContext = Depends(get_current_active_user)):
    return {"message": "Logged out successfully"}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    service: AuthService = Depends(get_auth_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    result = await service.change_password(current_user.user_id, data.old_password, data.new_password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}


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
async def keycloak_callback(data: KeycloakCallbackRequest):
    """
    Keycloak OAuth2 回调接口
    用授权码换取 Keycloak token，然后生成本地 token 返回
    """
    from app.config import get_settings
    from app.dal import get_adapter
    from app.dal.repositories import LocalUserRepository
    settings = get_settings()

    if not settings.KEYCLOAK_SERVER_URL:
        raise HTTPException(status_code=503, detail="Keycloak 未配置")

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

            service = AuthService(LocalUserRepository(get_adapter()))
            result = await service.keycloak_callback(user_context.username)

            logger.info(f"Keycloak login success for user: {user_context.username}")
            return create_local_token(
                user_id=result["user_id"],
                username=user_context.username,
                roles=result["roles"],
                dept_id=result["dept_id"],
            )

    except httpx.HTTPError as e:
        logger.error(f"Keycloak HTTP error: {e}")
        raise HTTPException(status_code=503, detail="无法连接 Keycloak 服务器")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keycloak callback error: {e}")
        raise HTTPException(status_code=500, detail="Keycloak 登录处理失败")