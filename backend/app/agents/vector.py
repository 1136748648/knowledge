import logging

from app.models.schemas import UserContext
from app.services.vector_service import VectorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class VectorAgent:
    def __init__(self, user: UserContext):
        self.user = user
        self.vector_service = VectorService()
        self.llm = LLMService()

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """语义搜索会话记录"""
        # 获取查询向量
        query_embedding = await self.llm.embed(query)

        # 构建权限过滤
        allowed_sensitivities = self._get_allowed_sensitivities()
        visible_dept_ids = self._get_visible_dept_ids()

        results = await self.vector_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            user_id=self.user.user_id,
            visible_dept_ids=visible_dept_ids,
            allowed_sensitivities=allowed_sensitivities,
        )

        return results

    async def store(self, text: str, metadata: dict) -> str:
        """存储文本到向量库"""
        embedding = await self.llm.embed(text)
        ids = await self.vector_service.insert(
            texts=[text],
            embeddings=[embedding],
            user_ids=[metadata.get("user_id", self.user.user_id)],
            dept_ids=[metadata.get("dept_id", self.user.dept_id)],
            sensitivities=[metadata.get("sensitivity", "public")],
        )
        return ids[0]

    def _get_allowed_sensitivities(self) -> list[str]:
        allowed = ["public"]
        if "manager" in self.user.roles or "hr" in self.user.roles:
            allowed.append("internal")
        if "hr" in self.user.roles or "admin" in self.user.roles:
            allowed.append("confidential")
        if "admin" in self.user.roles:
            allowed.append("secret")
        return allowed

    def _get_visible_dept_ids(self) -> list[str] | None:
        if "admin" in self.user.roles or "hr" in self.user.roles:
            return None  # 可见所有部门
        if self.user.dept_id:
            return [self.user.dept_id]
        return []
