import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wiki import WikiPage, WikiPageVersion
from app.models.schemas import UserContext, WikiPageCreate, WikiPageUpdate
from app.core.casbin_policy import check_permission


class WikiService:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user

    async def list_pages(
        self,
        parent_id: uuid.UUID | None = None,
        sensitivity: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[WikiPage]:
        query = select(WikiPage)
        if parent_id:
            query = query.where(WikiPage.parent_id == parent_id)
        if sensitivity:
            query = query.where(WikiPage.sensitivity == sensitivity)
        # 权限过滤：只返回用户有权访问的文档
        query = query.where(WikiPage.sensitivity.in_(self._allowed_sensitivities()))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_page(self, page_id: uuid.UUID) -> WikiPage | None:
        result = await self.db.execute(
            select(WikiPage).where(WikiPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        if page and not await self._can_access(page.sensitivity):
            return None
        return page

    async def create_page(self, data: WikiPageCreate) -> WikiPage:
        page = WikiPage(
            title=data.title,
            content=data.content,
            slug=data.slug,
            parent_id=data.parent_id,
            sensitivity=data.sensitivity,
            dept_id=data.dept_id,
            created_by=self.user.username,
        )
        self.db.add(page)
        await self.db.flush()

        # 创建初始版本
        version = WikiPageVersion(
            page_id=page.id,
            title=data.title,
            content=data.content,
            version=1,
            edited_by=self.user.username,
            edit_summary="Initial creation",
        )
        self.db.add(version)
        await self.db.flush()
        return page

    async def update_page(self, page_id: uuid.UUID, data: WikiPageUpdate) -> WikiPage | None:
        result = await self.db.execute(
            select(WikiPage).where(WikiPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        if not page:
            return None

        if not await self._can_write(page.sensitivity):
            return None

        # 获取最新版本号
        version_result = await self.db.execute(
            select(func.max(WikiPageVersion.version)).where(WikiPageVersion.page_id == page_id)
        )
        max_version = version_result.scalar() or 0

        # 更新字段
        if data.title is not None:
            page.title = data.title
        if data.content is not None:
            page.content = data.content
        if data.parent_id is not None:
            page.parent_id = data.parent_id
        if data.sensitivity is not None:
            page.sensitivity = data.sensitivity
        page.updated_by = self.user.username

        # 创建新版本
        version = WikiPageVersion(
            page_id=page.id,
            title=page.title,
            content=page.content,
            version=max_version + 1,
            edited_by=self.user.username,
            edit_summary=data.edit_summary,
        )
        self.db.add(version)
        await self.db.flush()
        return page

    async def delete_page(self, page_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(WikiPage).where(WikiPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        if not page:
            return False
        await self.db.delete(page)
        await self.db.flush()
        return True

    async def get_versions(self, page_id: uuid.UUID) -> list[WikiPageVersion]:
        result = await self.db.execute(
            select(WikiPageVersion)
            .where(WikiPageVersion.page_id == page_id)
            .order_by(WikiPageVersion.version.desc())
        )
        return result.scalars().all()

    async def search(self, query: str, page: int = 1, page_size: int = 20) -> list[WikiPage]:
        # PostgreSQL 全文搜索
        search_query = (
            select(WikiPage)
            .where(
                func.to_tsvector("simple", WikiPage.title + " " + WikiPage.content)
                .match(query, postgresql_regconfig="simple")
            )
            .where(WikiPage.sensitivity.in_(self._allowed_sensitivities()))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(search_query)
        return result.scalars().all()

    def _allowed_sensitivities(self) -> list[str]:
        """根据用户角色返回可访问的敏感度级别"""
        allowed = ["public"]
        if "manager" in self.user.roles or "hr" in self.user.roles or "admin" in self.user.roles:
            allowed.append("internal")
        if "hr" in self.user.roles or "admin" in self.user.roles:
            allowed.append("confidential")
        if "admin" in self.user.roles:
            allowed.append("secret")
        return allowed

    async def _can_access(self, sensitivity: str) -> bool:
        return sensitivity in self._allowed_sensitivities()

    async def _can_write(self, sensitivity: str) -> bool:
        if "admin" in self.user.roles:
            return True
        if "hr" in self.user.roles and sensitivity in ("public", "internal", "confidential"):
            return True
        if sensitivity == "public":
            return True
        return False
