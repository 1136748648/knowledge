import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserContext
from app.services.wiki_service import WikiService

logger = logging.getLogger(__name__)


class WikiAgent:
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.wiki_service = WikiService(db, user)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索 Wiki 文档"""
        pages = await self.wiki_service.search(query, page_size=top_k)
        return [
            {
                "id": str(page.id),
                "title": page.title,
                "content": page.content[:500],  # 截取摘要
                "slug": page.slug,
                "sensitivity": page.sensitivity,
            }
            for page in pages
        ]

    async def get_page_content(self, page_id: str) -> dict | None:
        """获取页面内容"""
        from uuid import UUID
        page = await self.wiki_service.get_page(UUID(page_id))
        if not page:
            return None
        return {
            "id": str(page.id),
            "title": page.title,
            "content": page.content,
            "slug": page.slug,
        }
