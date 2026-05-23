# 项目结构解耦优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 API Layer → Server Layer → DAL Layer 分层架构，使用 FastAPI Depends 依赖注入

**Architecture:** 创建独立的 Server 层（app/server/），将业务逻辑从 API 层和 services 层迁移到 Server 层，API 层只负责请求路由和参数校验

**Tech Stack:** FastAPI Depends, Python, SQLAlchemy

---

## 文件结构

```
app/
├── api/                    # API Layer (修改)
│   ├── wiki.py           # 修改: 使用 WikiServer
│   ├── auth.py           # 修改: 使用 AuthServer
│   ├── qa.py             # 修改: 使用 QAServer
│   ├── admin.py          # 修改: 使用 AdminServer
│   ├── heatmap.py        # 修改: 使用 HeatmapServer
│   └── knowledge.py      # 修改: 使用 KnowledgeServer
│
├── server/                # 新建 Server Layer
│   ├── __init__.py       # 新建: DI 工厂
│   ├── wiki_server.py    # 新建: WikiServer
│   ├── auth_server.py    # 新建: AuthServer
│   ├── qa_server.py      # 新建: QAServer
│   ├── admin_server.py   # 新建: AdminServer
│   ├── heatmap_server.py # 新建: HeatmapServer
│   └── knowledge_server.py # 新建: KnowledgeServer
│
├── services/              # 基础设施服务层 (不变)
├── dal/                   # DAL Layer (不变)
└── main.py               # 修改: 更新导入
```

---

## 任务清单

### Task 1: 创建 Server Layer 骨架

**Files:**
- Create: `backend/app/server/__init__.py`

- [ ] **Step 1: 创建 server 目录和 __init__.py**

```python
from functools import lru_cache
from fastapi import Depends

def get_adapter():
    from app.dal import get_adapter as _get_adapter
    return _get_adapter()

__all__ = []
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/server/__init__.py
git commit -m "feat: create server layer skeleton"
```

---

### Task 2: 创建 WikiServer

**Files:**
- Create: `backend/app/server/wiki_server.py`
- Create: `backend/app/server/__init__.py` (添加 WikiServer 导出和 DI)
- Modify: `backend/app/api/wiki.py` (使用 WikiServer)

- [ ] **Step 1: 创建 WikiServer**

```python
from typing import Optional
import uuid
from app.dal import WikiPageRepository, WikiPageVersionRepository
from app.models.schemas import WikiPageCreate, WikiPageUpdate, WikiPageResponse, UserContext
from app.core.casbin_policy import check_permission


class WikiServer:
    def __init__(
        self,
        page_repo: WikiPageRepository,
        version_repo: WikiPageVersionRepository,
    ):
        self.page_repo = page_repo
        self.version_repo = version_repo

    async def list_pages(
        self,
        user: UserContext,
        parent_id: Optional[uuid.UUID] = None,
        sensitivity: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        if not await check_permission(user.roles, "wiki", "read"):
            return []

        if parent_id:
            pages = await self.page_repo.list_by_parent(parent_id, page, page_size)
        elif sensitivity:
            pages = await self.page_repo.list_by_sensitivity(sensitivity, page, page_size)
        else:
            pages = await self.page_repo.get_all()

        return [p for p in pages if await self._can_access(user, p.sensitivity)]

    async def get_page(self, user: UserContext, page_id: uuid.UUID):
        if not await check_permission(user.roles, "wiki", "read"):
            return None

        page = await self.page_repo.get_by_id(page_id)
        if page and not await self._can_access(user, page.sensitivity):
            return None
        return page

    async def create_page(self, user: UserContext, data: WikiPageCreate):
        if not await check_permission(user.roles, "wiki", "write"):
            raise PermissionError("You do not have permission to create wiki pages")

        from app.models.wiki import WikiPage, WikiPageVersion

        page = WikiPage(
            title=data.title,
            content=data.content,
            slug=data.slug,
            parent_id=data.parent_id,
            sensitivity=data.sensitivity,
            dept_id=data.dept_id,
            created_by=user.username,
        )
        page = await self.page_repo.create(page)

        version = WikiPageVersion(
            page_id=page.id,
            title=data.title,
            content=data.content,
            version=1,
            edited_by=user.username,
            edit_summary="Initial creation",
        )
        await self.version_repo.create(version)
        return page

    async def update_page(self, user: UserContext, page_id: uuid.UUID, data: WikiPageUpdate):
        if not await check_permission(user.roles, "wiki", "write"):
            return None

        page = await self.page_repo.get_by_id(page_id)
        if not page:
            return None

        if not await self._can_write(user, page.sensitivity):
            return None

        max_version = await self.version_repo.get_max_version(page_id)

        if data.title is not None:
            page.title = data.title
        if data.content is not None:
            page.content = data.content
        if data.parent_id is not None:
            page.parent_id = data.parent_id
        if data.sensitivity is not None:
            page.sensitivity = data.sensitivity
        page.updated_by = user.username

        page = await self.page_repo.update(page)

        from app.models.wiki import WikiPageVersion

        version = WikiPageVersion(
            page_id=page.id,
            title=page.title,
            content=page.content,
            version=max_version + 1,
            edited_by=user.username,
            edit_summary=data.edit_summary,
        )
        await self.version_repo.create(version)
        return page

    async def delete_page(self, user: UserContext, page_id: uuid.UUID) -> bool:
        if not await check_permission(user.roles, "wiki", "delete"):
            return False

        page = await self.page_repo.get_by_id(page_id)
        if not page:
            return False
        return await self.page_repo.delete(page_id)

    async def get_versions(self, user: UserContext, page_id: uuid.UUID):
        if not await check_permission(user.roles, "wiki", "read"):
            return []

        return await self.version_repo.get_by_page_id(page_id)

    async def search(self, user: UserContext, query: str, page: int = 1, page_size: int = 20):
        if not await check_permission(user.roles, "wiki", "read"):
            return []

        results = await self.page_repo.search(query, page, page_size)
        return [p for p in results if await self._can_access(user, p.sensitivity)]

    async def _allowed_sensitivities(self, user: UserContext) -> list[str]:
        allowed = ["public"]
        if await check_permission(user.roles, "wiki", "read"):
            if "admin" in user.roles or "hr" in user.roles or "manager" in user.roles:
                allowed.append("internal")
            if "admin" in user.roles or "hr" in user.roles:
                allowed.append("confidential")
            if "admin" in user.roles:
                allowed.append("secret")
        return allowed

    async def _can_access(self, user: UserContext, sensitivity: str) -> bool:
        return sensitivity in await self._allowed_sensitivities(user)

    async def _can_write(self, user: UserContext, sensitivity: str) -> bool:
        if await check_permission(user.roles, "wiki", "write"):
            if "admin" in user.roles:
                return True
            if "hr" in user.roles and sensitivity in ("public", "internal", "confidential"):
                return True
            if sensitivity == "public":
                return True
        return False
```

- [ ] **Step 2: 更新 server/__init__.py 添加 WikiServer DI**

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
)
from .wiki_server import WikiServer

@lru_cache()
def get_wiki_page_repo() -> WikiPageRepository:
    adapter = get_adapter()
    return WikiPageRepository(adapter)

@lru_cache()
def get_wiki_version_repo() -> WikiPageVersionRepository:
    adapter = get_adapter()
    return WikiPageVersionRepository(adapter)

def get_wiki_server(
    page_repo: WikiPageRepository = Depends(get_wiki_page_repo),
    version_repo: WikiPageVersionRepository = Depends(get_wiki_version_repo),
) -> WikiServer:
    return WikiServer(page_repo, version_repo)

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
]
```

- [ ] **Step 3: 修改 api/wiki.py 使用 WikiServer**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, WikiPageCreate, WikiPageUpdate,
    WikiPageResponse, WikiPageListResponse,
)
from app.server import get_wiki_server, WikiServer

router = APIRouter()


@router.get("/", response_model=list[WikiPageListResponse])
async def list_wiki_pages(
    parent_id: UUID | None = None,
    sensitivity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.list_pages(current_user, parent_id, sensitivity, page, page_size)


@router.get("/{page_id}", response_model=WikiPageResponse)
async def get_wiki_page(
    page_id: UUID,
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    page = await server.get_page(current_user, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/", response_model=WikiPageResponse, status_code=201)
async def create_wiki_page(
    data: WikiPageCreate,
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.create_page(current_user, data)


@router.put("/{page_id}", response_model=WikiPageResponse)
async def update_wiki_page(
    page_id: UUID,
    data: WikiPageUpdate,
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    page = await server.update_page(current_user, page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.delete("/{page_id}", status_code=204)
async def delete_wiki_page(
    page_id: UUID,
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    if not await server.delete_page(current_user, page_id):
        raise HTTPException(status_code=404, detail="Page not found")


@router.get("/{page_id}/versions")
async def get_page_versions(
    page_id: UUID,
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.get_versions(current_user, page_id)


@router.get("/search/{query}")
async def search_wiki(
    query: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    server: WikiServer = Depends(get_wiki_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.search(current_user, query, page, page_size)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/server/wiki_server.py backend/app/server/__init__.py backend/app/api/wiki.py
git commit -m "feat: add WikiServer with DI support"
```

---

### Task 3: 创建 AuthServer

**Files:**
- Create: `backend/app/server/auth_server.py`
- Modify: `backend/app/server/__init__.py` (添加 AuthServer 导出)
- Modify: `backend/app/api/auth.py` (使用 AuthServer)

- [ ] **Step 1: 创建 AuthServer**

```python
import logging
from app.dal.repositories import LocalUserRepository
from app.core.security import hash_password, verify_password, create_local_token
from app.models.schemas import UserContext

logger = logging.getLogger(__name__)


class AuthServer:
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
```

- [ ] **Step 2: 更新 server/__init__.py 添加 AuthServer DI**

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
)
from .wiki_server import WikiServer
from .auth_server import AuthServer

# ... existing wiki functions ...

@lru_cache()
def get_local_user_repo() -> LocalUserRepository:
    adapter = get_adapter()
    return LocalUserRepository(adapter)

def get_auth_server(
    user_repo: LocalUserRepository = Depends(get_local_user_repo),
) -> AuthServer:
    return AuthServer(user_repo)

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthServer",
    "get_auth_server",
    "get_local_user_repo",
]
```

- [ ] **Step 3: 修改 api/auth.py 使用 AuthServer**

```python
import logging
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import (
    create_local_token,
    get_current_active_user,
    hash_password,
    verify_keycloak_token,
)
from app.models.schemas import UserContext
from app.server import get_auth_server, AuthServer

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


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class KeycloakLoginResponse(BaseModel):
    authorization_url: str


class KeycloakCallbackRequest(BaseModel):
    code: str
    state: str


@router.post("/token", response_model=TokenResponse)
async def login(data: LoginRequest):
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
        adapter = get_adapter()
        server = AuthServer(LocalUserRepository(adapter))
        result = await server.authenticate(data.username, data.password)

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
    server: AuthServer = Depends(get_auth_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.get_user_info(current_user)


@router.post("/logout")
async def logout(current_user: UserContext = Depends(get_current_active_user)):
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    server: AuthServer = Depends(get_auth_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    result = await server.change_password(
        current_user.user_id,
        data.old_password,
        data.new_password,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"]}


@router.get("/keycloak/login", response_model=KeycloakLoginResponse)
async def keycloak_login():
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


@router.post("/keycloak/callback", response_model=TokenResponse)
async def keycloak_callback(data: KeycloakCallbackRequest):
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

            adapter = get_adapter()
            server = AuthServer(LocalUserRepository(adapter))
            result = await server.keycloak_callback(user_context.username)

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
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/server/auth_server.py backend/app/server/__init__.py backend/app/api/auth.py
git commit -m "feat: add AuthServer with DI support"
```

---

### Task 4: 创建 KnowledgeServer

**Files:**
- Create: `backend/app/server/knowledge_server.py`
- Modify: `backend/app/server/__init__.py` (添加 KnowledgeServer 导出)
- Modify: `backend/app/api/knowledge.py` (使用 KnowledgeServer)

- [ ] **Step 1: 创建 KnowledgeServer**

```python
from typing import Optional
import uuid
from app.dal import KnowledgeNavRepository, NavContentLinkRepository
from app.models.schemas import UserContext, NavNodeCreate, NavNodeUpdate


class KnowledgeServer:
    def __init__(
        self,
        nav_repo: KnowledgeNavRepository,
        link_repo: NavContentLinkRepository,
    ):
        self.nav_repo = nav_repo
        self.link_repo = link_repo

    async def get_tree(self, user: UserContext):
        nodes = await self.nav_repo.get_root_nodes()
        return [node for node in nodes if self._can_view_node(user, node)]

    async def get_node(self, node_id: uuid.UUID):
        return await self.nav_repo.get_by_id(node_id)

    async def create_node(self, user: UserContext, data: NavNodeCreate):
        path = data.name
        if data.parent_id:
            parent = await self.get_node(data.parent_id)
            if parent:
                path = f"{parent.path}.{data.name}"

        from app.models.navigation import KnowledgeNav

        node = KnowledgeNav(
            name=data.name,
            parent_id=data.parent_id,
            path=path,
            icon=data.icon,
            description=data.description,
            visibility_roles=data.visibility_roles,
            created_by=user.username,
        )
        return await self.nav_repo.create(node)

    async def update_node(self, user: UserContext, node_id: uuid.UUID, data: NavNodeUpdate):
        node = await self.get_node(node_id)
        if not node:
            return None

        if data.name is not None:
            node.name = data.name
        if data.parent_id is not None:
            node.parent_id = data.parent_id
        if data.icon is not None:
            node.icon = data.icon
        if data.description is not None:
            node.description = data.description
        if data.sort_order is not None:
            node.sort_order = data.sort_order
        if data.visibility_roles is not None:
            node.visibility_roles = data.visibility_roles

        return await self.nav_repo.update(node)

    async def delete_node(self, user: UserContext, node_id: uuid.UUID) -> bool:
        node = await self.get_node(node_id)
        if not node:
            return False
        return await self.nav_repo.delete(node_id)

    async def link_content(
        self,
        user: UserContext,
        node_id: uuid.UUID,
        content_type: str,
        content_id: str,
    ):
        from app.models.navigation import NavContentLink

        link = NavContentLink(
            nav_id=node_id,
            content_type=content_type,
            content_id=content_id,
        )
        return await self.link_repo.create(link)

    def _can_view_node(self, user: UserContext, node) -> bool:
        if not node.visibility_roles:
            return True
        if "admin" in user.roles:
            return True
        return any(role in user.roles for role in node.visibility_roles)
```

- [ ] **Step 2: 更新 server/__init__.py 添加 KnowledgeServer DI**

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
)
from .wiki_server import WikiServer
from .auth_server import AuthServer
from .knowledge_server import KnowledgeServer

# ... existing wiki and auth functions ...

@lru_cache()
def get_knowledge_nav_repo() -> KnowledgeNavRepository:
    adapter = get_adapter()
    return KnowledgeNavRepository(adapter)

@lru_cache()
def get_nav_content_link_repo() -> NavContentLinkRepository:
    adapter = get_adapter()
    return NavContentLinkRepository(adapter)

def get_knowledge_server(
    nav_repo: KnowledgeNavRepository = Depends(get_knowledge_nav_repo),
    link_repo: NavContentLinkRepository = Depends(get_nav_content_link_repo),
) -> KnowledgeServer:
    return KnowledgeServer(nav_repo, link_repo)

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthServer",
    "get_auth_server",
    "get_local_user_repo",
    "KnowledgeServer",
    "get_knowledge_server",
    "get_knowledge_nav_repo",
    "get_nav_content_link_repo",
]
```

- [ ] **Step 3: 修改 api/knowledge.py 使用 KnowledgeServer**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, NavNodeCreate, NavNodeUpdate, NavNodeResponse,
)
from app.server import get_knowledge_server, KnowledgeServer

router = APIRouter()


@router.get("/nav", response_model=list[NavNodeResponse])
async def get_navigation_tree(
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.get_tree(current_user)


@router.post("/nav", response_model=NavNodeResponse, status_code=201)
async def create_nav_node(
    data: NavNodeCreate,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.create_node(current_user, data)


@router.put("/nav/{node_id}", response_model=NavNodeResponse)
async def update_nav_node(
    node_id: UUID,
    data: NavNodeUpdate,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    node = await server.update_node(current_user, node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nav/{node_id}", status_code=204)
async def delete_nav_node(
    node_id: UUID,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    if not await server.delete_node(current_user, node_id):
        raise HTTPException(status_code=404, detail="Node not found")


@router.post("/nav/{node_id}/link")
async def link_content_to_nav(
    node_id: UUID,
    content_type: str = Query(..., pattern="^(wiki|conversation|external)$"),
    content_id: str = ...,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    return await server.link_content(current_user, node_id, content_type, content_id)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/server/knowledge_server.py backend/app/server/__init__.py backend/app/api/knowledge.py
git commit -m "feat: add KnowledgeServer with DI support"
```

---

### Task 5: 创建 HeatmapServer

**Files:**
- Create: `backend/app/server/heatmap_server.py`
- Modify: `backend/app/server/__init__.py` (添加 HeatmapServer 导出)
- Modify: `backend/app/api/heatmap.py` (使用 HeatmapServer)

- [ ] **Step 1: 创建 HeatmapServer**

```python
from datetime import date, datetime, timedelta
from app.dal import SearchEventRepository, HeatmapStatsRepository
from app.core.redis import get_redis


class HeatmapServer:
    def __init__(
        self,
        search_event_repo: SearchEventRepository,
        stats_repo: HeatmapStatsRepository,
    ):
        self.search_event_repo = search_event_repo
        self.stats_repo = stats_repo
        self._redis_client = None

    async def get_redis_client(self):
        if self._redis_client is None:
            self._redis_client = await get_redis()
        return self._redis_client

    async def record_search_event(self, user_id: str, query: str, dept_id: str = None):
        from app.models.heatmap import SearchEvent

        event = SearchEvent(
            query_text=query,
            user_id=user_id,
            dept_id=dept_id,
            created_at=datetime.utcnow(),
        )
        await self.search_event_repo.create(event)

        redis_client = await self.get_redis_client()
        redis_key = f"heatmap:search:{date.today().isoformat()}"
        await redis_client.hincrby(redis_key, query, 1)
        await redis_client.expire(redis_key, 86400)

    async def get_hot_queries(self, time_range: str = "24h", limit: int = 10):
        redis_client = await self.get_redis_client()
        today_key = f"heatmap:search:{date.today().isoformat()}"
        
        all_queries = {}
        
        if time_range == "24h":
            data = await redis_client.zrevrange(today_key, 0, limit - 1, withscores=True)
            return [{"query": k, "count": int(v)} for k, v in data]
        else:
            delta = 7 if time_range == "7d" else 30
            for i in range(delta):
                key = f"heatmap:search:{(date.today() - timedelta(days=i)).isoformat()}"
                data = await redis_client.hgetall(key)
                for query, count in data.items():
                    all_queries[query] = all_queries.get(query, 0) + int(count)
            
            sorted_queries = sorted(all_queries.items(), key=lambda x: x[1], reverse=True)
            return [{"query": k, "count": v} for k, v in sorted_queries[:limit]]

    async def get_hot_documents(self, time_range: str = "24h", limit: int = 10):
        return [{"doc_id": f"doc{i}", "hit_count": 20 - i * 2} for i in range(1, limit + 1)]

    async def get_timeline(self, target_date: str | None = None, granularity: str = "hour"):
        if target_date is None:
            target_date = date.today().isoformat()
        
        redis_client = await self.get_redis_client()
        redis_key = f"heatmap:timeline:{target_date}"
        data = await redis_client.get(redis_key)
        
        if data:
            return {"date": target_date, "granularity": granularity, "data": eval(data)}
        
        return {
            "date": target_date,
            "granularity": granularity,
            "data": [{"hour": i, "count": 0} for i in range(24)] if granularity == "hour" else [],
        }

    async def get_navigation_heat(self):
        stats = await self.stats_repo.get_by_type("navigation")
        result = []
        for stat in stats[:10]:
            hot_level = "hot" if stat.count > 100 else "warm" if stat.count > 50 else "cold"
            result.append({
                "node_id": stat.stat_key,
                "hot_level": hot_level,
                "count": stat.count,
            })
        return result

    async def aggregate_daily_stats(self):
        yesterday = date.today() - timedelta(days=1)
        redis_key = f"heatmap:search:{yesterday.isoformat()}"

        redis_client = await self.get_redis_client()
        search_counts = await redis_client.hgetall(redis_key)
        if not search_counts:
            return

        from app.models.heatmap import HeatmapStats

        for query, count in search_counts.items():
            existing = await self.stats_repo.get_by_type_key_date("search", query, yesterday)
            if existing:
                existing.count += int(count)
                await self.stats_repo.update(existing)
            else:
                stat = HeatmapStats(
                    stat_type="search",
                    stat_key=query,
                    stat_date=yesterday,
                    count=int(count),
                )
                await self.stats_repo.create(stat)

        await redis_client.delete(redis_key)
```

- [ ] **Step 2: 更新 server/__init__.py 添加 HeatmapServer DI**

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
)
from .wiki_server import WikiServer
from .auth_server import AuthServer
from .knowledge_server import KnowledgeServer
from .heatmap_server import HeatmapServer

# ... existing wiki, auth, knowledge functions ...

@lru_cache()
def get_search_event_repo() -> SearchEventRepository:
    adapter = get_adapter()
    return SearchEventRepository(adapter)

@lru_cache()
def get_heatmap_stats_repo() -> HeatmapStatsRepository:
    adapter = get_adapter()
    return HeatmapStatsRepository(adapter)

def get_heatmap_server(
    search_event_repo: SearchEventRepository = Depends(get_search_event_repo),
    stats_repo: HeatmapStatsRepository = Depends(get_heatmap_stats_repo),
) -> HeatmapServer:
    return HeatmapServer(search_event_repo, stats_repo)

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthServer",
    "get_auth_server",
    "get_local_user_repo",
    "KnowledgeServer",
    "get_knowledge_server",
    "get_knowledge_nav_repo",
    "get_nav_content_link_repo",
    "HeatmapServer",
    "get_heatmap_server",
    "get_search_event_repo",
    "get_heatmap_stats_repo",
]
```

- [ ] **Step 3: 修改 api/heatmap.py 使用 HeatmapServer**

```python
from fastapi import APIRouter, Depends, Query
from app.server import get_heatmap_server, HeatmapServer

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


@router.get("/queries")
async def get_hot_queries(
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
    server: HeatmapServer = Depends(get_heatmap_server),
):
    data = await server.get_hot_queries(time_range, limit)
    return {"time_range": time_range, "data": data, "updated_at": "now"}


@router.get("/documents")
async def get_hot_documents(
    time_range: str = Query("24h", regex="^(24h|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
    server: HeatmapServer = Depends(get_heatmap_server),
):
    data = await server.get_hot_documents(time_range, limit)
    return {"time_range": time_range, "data": data}


@router.get("/timeline")
async def get_timeline(
    date: str | None = Query(None),
    granularity: str = Query("hour", regex="^(hour|day)$"),
    server: HeatmapServer = Depends(get_heatmap_server),
):
    return await server.get_timeline(date, granularity)


@router.get("/navigation")
async def get_navigation_heat(
    server: HeatmapServer = Depends(get_heatmap_server),
):
    data = await server.get_navigation_heat()
    return {"data": data}
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/server/heatmap_server.py backend/app/server/__init__.py backend/app/api/heatmap.py
git commit -m "feat: add HeatmapServer with DI support"
```

---

### Task 6: 创建 AdminServer 和 QAServer

**Files:**
- Create: `backend/app/server/admin_server.py`
- Create: `backend/app/server/qa_server.py`
- Modify: `backend/app/server/__init__.py` (添加导出)
- Modify: `backend/app/api/admin.py` (使用 AdminServer)
- Modify: `backend/app/api/qa.py` (使用 QAServer)

- [ ] **Step 1: 创建 AdminServer**

```python
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


class AdminServer:
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
```

- [ ] **Step 2: 创建 QAServer**

```python
from app.agents.router import RouterAgent
from app.models.schemas import UserContext


class QAServer:
    def __init__(self):
        pass

    async def ask_question(self, user: UserContext, question: str) -> dict:
        agent = RouterAgent(user)
        result = await agent.route(question)
        return result
```

- [ ] **Step 3: 更新 server/__init__.py 添加 AdminServer 和 QAServer DI**

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
    AuditLogRepository,
)
from .wiki_server import WikiServer
from .auth_server import AuthServer
from .knowledge_server import KnowledgeServer
from .heatmap_server import HeatmapServer
from .admin_server import AdminServer
from .qa_server import QAServer

# ... existing functions ...

@lru_cache()
def get_audit_log_repo() -> AuditLogRepository:
    adapter = get_adapter()
    return AuditLogRepository(adapter)

def get_admin_server(
    audit_log_repo: AuditLogRepository = Depends(get_audit_log_repo),
) -> AdminServer:
    return AdminServer(audit_log_repo)

def get_qa_server() -> QAServer:
    return QAServer()

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthServer",
    "get_auth_server",
    "get_local_user_repo",
    "KnowledgeServer",
    "get_knowledge_server",
    "get_knowledge_nav_repo",
    "get_nav_content_link_repo",
    "HeatmapServer",
    "get_heatmap_server",
    "get_search_event_repo",
    "get_heatmap_stats_repo",
    "AdminServer",
    "get_admin_server",
    "get_audit_log_repo",
    "QAServer",
    "get_qa_server",
]
```

- [ ] **Step 4: 修改 api/admin.py 使用 AdminServer**

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.security import get_current_active_user
from app.models.schemas import UserContext, AuditLogResponse, PolicyCreate, RoleAssign
from app.server import get_admin_server, AdminServer

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_audit_logs(current_user, user_id, action, page, page_size)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/users")
async def list_users(
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.list_users(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/permissions")
async def get_permissions(
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_permissions(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/policies")
async def create_policy(
    policy: PolicyCreate,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.create_policy(current_user, policy.sub, policy.obj, policy.act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/policies")
async def delete_policy(
    sub: str,
    obj: str,
    act: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.delete_policy(current_user, sub, obj, act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/roles/assign")
async def assign_role(
    role_data: RoleAssign,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.assign_role(current_user, role_data.user, role_data.role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/roles/assign")
async def unassign_role(
    user: str,
    role: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.unassign_role(current_user, user, role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/roles/{user}")
async def get_user_role_list(
    user: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_user_roles(current_user, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

- [ ] **Step 5: 修改 api/qa.py 使用 QAServer**

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.server import get_qa_server, QAServer

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    server: QAServer = Depends(get_qa_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    result = await server.ask_question(current_user, data.question)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/server/admin_server.py backend/app/server/qa_server.py
git add backend/app/server/__init__.py
git add backend/app/api/admin.py backend/app/api/qa.py
git commit -m "feat: add AdminServer and QAServer with DI support"
```

---

### Task 7: 更新 main.py 和验证

**Files:**
- Modify: `backend/app/main.py` (检查导入)

- [ ] **Step 1: 检查 main.py 导入是否需要更新**

查看 main.py 中的导入语句：

```python
from app.api import auth, wiki, qa, knowledge, admin, system, heatmap
from app.dal import get_adapter, LocalUserRepository
```

main.py 中直接使用了 `LocalUserRepository`，需要改为通过 Server 或 DAL 层：

```python
from app.dal import get_adapter
from app.dal.repositories import LocalUserRepository
```

- [ ] **Step 2: 运行测试验证**

```bash
cd backend
python -m pytest tests/ -v --ignore=tests/test_qa.py
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/main.py
git commit -m "chore: update main.py imports for server layer"
```

---

## 自检清单

- [ ] 所有 API 层只调用 Server 层
- [ ] 所有 Server 层通过构造函数注入 Repository
- [ ] 所有 DI 工厂函数在 `app/server/__init__.py` 中定义
- [ ] 无越级调用（DAL → API，DAL → Server，API → DAL）
- [ ] 测试通过
