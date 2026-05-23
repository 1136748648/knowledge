import uuid

from app.dal import WikiPageRepository, WikiPageVersionRepository, get_adapter
from app.models.schemas import UserContext, WikiPageCreate, WikiPageUpdate
from app.core.casbin_policy import check_permission


class WikiService:
    def __init__(self, user: UserContext):
        adapter = get_adapter()
        self.page_repo = WikiPageRepository(adapter)
        self.version_repo = WikiPageVersionRepository(adapter)
        self.user = user

    async def list_pages(
        self,
        parent_id: uuid.UUID | None = None,
        sensitivity: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        if not await check_permission(self.user.roles, "wiki", "read"):
            return []

        if parent_id:
            pages = await self.page_repo.list_by_parent(parent_id, page, page_size)
        elif sensitivity:
            pages = await self.page_repo.list_by_sensitivity(sensitivity, page, page_size)
        else:
            pages = await self.page_repo.get_all()

        return [p for p in pages if await self._can_access(p.sensitivity)]

    async def get_page(self, page_id: uuid.UUID):
        if not await check_permission(self.user.roles, "wiki", "read"):
            return None

        page = await self.page_repo.get_by_id(page_id)
        if page and not await self._can_access(page.sensitivity):
            return None
        return page

    async def create_page(self, data: WikiPageCreate):
        if not await check_permission(self.user.roles, "wiki", "write"):
            raise PermissionError("You do not have permission to create wiki pages")

        from app.models.wiki import WikiPage, WikiPageVersion

        page = WikiPage(
            title=data.title,
            content=data.content,
            slug=data.slug,
            parent_id=data.parent_id,
            sensitivity=data.sensitivity,
            dept_id=data.dept_id,
            created_by=self.user.username,
        )
        page = await self.page_repo.create(page)

        version = WikiPageVersion(
            page_id=page.id,
            title=data.title,
            content=data.content,
            version=1,
            edited_by=self.user.username,
            edit_summary="Initial creation",
        )
        await self.version_repo.create(version)
        return page

    async def update_page(self, page_id: uuid.UUID, data: WikiPageUpdate):
        if not await check_permission(self.user.roles, "wiki", "write"):
            return None

        page = await self.page_repo.get_by_id(page_id)
        if not page:
            return None

        if not await self._can_write(page.sensitivity):
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
        page.updated_by = self.user.username

        page = await self.page_repo.update(page)

        from app.models.wiki import WikiPageVersion

        version = WikiPageVersion(
            page_id=page.id,
            title=page.title,
            content=page.content,
            version=max_version + 1,
            edited_by=self.user.username,
            edit_summary=data.edit_summary,
        )
        await self.version_repo.create(version)
        return page

    async def delete_page(self, page_id: uuid.UUID) -> bool:
        if not await check_permission(self.user.roles, "wiki", "delete"):
            return False

        page = await self.page_repo.get_by_id(page_id)
        if not page:
            return False
        return await self.page_repo.delete(page_id)

    async def get_versions(self, page_id: uuid.UUID):
        if not await check_permission(self.user.roles, "wiki", "read"):
            return []

        return await self.version_repo.get_by_page_id(page_id)

    async def search(self, query: str, page: int = 1, page_size: int = 20):
        if not await check_permission(self.user.roles, "wiki", "read"):
            return []

        results = await self.page_repo.search(query, page, page_size)
        return [p for p in results if await self._can_access(p.sensitivity)]

    async def _allowed_sensitivities(self) -> list[str]:
        allowed = ["public"]
        if await check_permission(self.user.roles, "wiki", "read"):
            if "admin" in self.user.roles or "hr" in self.user.roles or "manager" in self.user.roles:
                allowed.append("internal")
            if "admin" in self.user.roles or "hr" in self.user.roles:
                allowed.append("confidential")
            if "admin" in self.user.roles:
                allowed.append("secret")
        return allowed

    async def _can_access(self, sensitivity: str) -> bool:
        return sensitivity in await self._allowed_sensitivities()

    async def _can_write(self, sensitivity: str) -> bool:
        if await check_permission(self.user.roles, "wiki", "write"):
            if "admin" in self.user.roles:
                return True
            if "hr" in self.user.roles and sensitivity in ("public", "internal", "confidential"):
                return True
            if sensitivity == "public":
                return True
        return False
