import uuid
import logging
import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Milvus REST API (available on port 19531 by default)
MILVUS_REST_PORT = 19531


class VectorService:
    def __init__(self):
        self._base_url: str | None = None
        self._collection_created = False

    @property
    def base_url(self) -> str:
        if not self._base_url:
            self._base_url = f"http://{settings.MILVUS_HOST}:{MILVUS_REST_PORT}"
        return self._base_url

    async def _request(self, method: str, path: str, data: dict = None) -> dict:
        """发送 REST 请求到 Milvus"""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                resp = await client.get(url, params=data)
            else:
                resp = await client.post(url, json=data or {})
            resp.raise_for_status()
            return resp.json()

    async def ensure_collection(self):
        """确保 Collection 存在"""
        if self._collection_created:
            return

        collection_name = settings.MILVUS_COLLECTION

        # 检查 collection 是否存在
        try:
            result = await self._request("POST", "/v1/vector/collections/describe", {
                "collectionName": collection_name,
            })
            if result.get("data"):
                self._collection_created = True
                return
        except Exception:
            pass

        # 创建 collection
        try:
            await self._request("POST", "/v1/vector/collections/create", {
                "collectionName": collection_name,
                "dimension": settings.LLM_EMBEDDING_DIM,
                "metricType": "COSINE",
                "fields": [
                    {"name": "id", "dataType": "VarChar", "isPrimary": True, "maxLength": 64},
                    {"name": "user_id", "dataType": "VarChar", "maxLength": 128},
                    {"name": "dept_id", "dataType": "VarChar", "maxLength": 64},
                    {"name": "sensitivity", "dataType": "VarChar", "maxLength": 32},
                    {"name": "text", "dataType": "VarChar", "maxLength": 65535},
                    {"name": "embedding", "dataType": "FloatVector", "dim": settings.LLM_EMBEDDING_DIM},
                ],
            })
            self._collection_created = True
            logger.info(f"Created Milvus collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to create collection (may already exist): {e}")
            self._collection_created = True

    async def insert(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        user_ids: list[str],
        dept_ids: list[str | None],
        sensitivities: list[str],
        ids: list[str] | None = None,
    ) -> list[str]:
        """插入向量"""
        await self.ensure_collection()

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        data = [
            {
                "id": ids[i],
                "user_id": user_ids[i],
                "dept_id": dept_ids[i] or "",
                "sensitivity": sensitivities[i],
                "text": texts[i],
                "embedding": embeddings[i],
            }
            for i in range(len(texts))
        ]

        await self._request("POST", "/v1/vector/insert", {
            "collectionName": settings.MILVUS_COLLECTION,
            "data": data,
        })

        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        user_id: str | None = None,
        visible_dept_ids: list[str] | None = None,
        allowed_sensitivities: list[str] | None = None,
    ) -> list[dict]:
        """搜索相似向量"""
        await self.ensure_collection()

        # 构建过滤表达式
        filters = []
        if user_id:
            filters.append(f'user_id == "{user_id}"')
        if visible_dept_ids:
            dept_list = ", ".join(f'"{d}"' for d in visible_dept_ids)
            filters.append(f"dept_id in [{dept_list}]")
        if allowed_sensitivities:
            sens_list = ", ".join(f'"{s}"' for s in allowed_sensitivities)
            filters.append(f"sensitivity in [{sens_list}]")

        filter_expr = " and ".join(filters) if filters else ""

        result = await self._request("POST", "/v1/vector/search", {
            "collectionName": settings.MILVUS_COLLECTION,
            "vector": query_embedding,
            "limit": top_k,
            "outputFields": ["id", "user_id", "dept_id", "sensitivity", "text"],
            "filter": filter_expr,
            "metricType": "COSINE",
        })

        hits = result.get("data", [])
        return [
            {
                "id": hit.get("id", ""),
                "score": hit.get("distance", 0),
                "text": hit.get("text", ""),
                "user_id": hit.get("user_id", ""),
                "dept_id": hit.get("dept_id", ""),
                "sensitivity": hit.get("sensitivity", ""),
            }
            for hit in hits
        ]

    async def delete(self, ids: list[str]):
        """删除向量"""
        await self.ensure_collection()

        await self._request("POST", "/v1/vector/delete", {
            "collectionName": settings.MILVUS_COLLECTION,
            "ids": ids,
        })

    async def close(self):
        """关闭连接（REST 无状态，无需操作）"""
        pass
