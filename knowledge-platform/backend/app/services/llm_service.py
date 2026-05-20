import json
import logging
from typing import AsyncGenerator

from app.config import get_settings
from app.services.llm_providers import ProviderRegistry, BaseLLMProvider

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务 — 基于 ProviderRegistry 的多提供商架构

    用法：
        # 使用当前激活的提供商（从配置读取）
        service = LLMService()

        # 指定提供商
        service = LLMService(provider_name="zhipu", config={"api_key": "...", "model": "glm-4"})
    """

    def __init__(self, provider_name: str = None, config: dict = None):
        if provider_name and config:
            # 直接使用指定的提供商和配置
            self.provider = ProviderRegistry.create(provider_name, config)
        else:
            # 从环境变量/默认配置加载（兼容旧模式）
            self.provider = self._create_default_provider()

    def _create_default_provider(self) -> BaseLLMProvider:
        """从默认配置创建提供商（兼容旧的 .env 模式）"""
        # 默认使用 OpenAI 兼容模式
        return ProviderRegistry.create("openai", {
            "api_key": settings.LLM_API_KEY,
            "api_base": settings.LLM_API_BASE,
            "model": settings.LLM_MODEL,
            "embedding_model": settings.LLM_EMBEDDING_MODEL,
            "embedding_dim": str(settings.LLM_EMBEDDING_DIM),
        })

    @staticmethod
    def from_config_service(configs: dict[str, str]) -> "LLMService":
        """从配置服务的配置创建 LLMService"""
        provider_name = configs.get("provider", "openai")
        config = {
            "api_key": configs.get("api_key", ""),
            "api_base": configs.get("api_base", ""),
            "model": configs.get("model", ""),
            "embedding_model": configs.get("embedding_model", ""),
            "embedding_dim": configs.get("embedding_dim", "1536"),
            "secret_key": configs.get("secret_key", ""),
        }
        return LLMService(provider_name=provider_name, config=config)

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """发送聊天请求"""
        return await self.provider.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        async for chunk in self.provider.stream_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens):
            yield chunk

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        """获取文本嵌入向量"""
        return await self.provider.embed(text, model=model)

    async def embed_batch(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """批量获取嵌入向量"""
        return await self.provider.embed_batch(texts, model=model)

    async def classify_intent(self, question: str) -> dict:
        """意图分类"""
        system_prompt = """你是一个意图分类器。根据用户问题，判断查询意图类型和涉及的数据源。

意图类型：
- PURE_DB: 只需要查询数据库（员工信息、项目、考勤、绩效等）
- PURE_KB: 只需要查询知识库（制度、规范、FAQ等）
- HYBRID: 需要同时查询数据库和知识库
- BOUNDARY: 无法确定或超出范围

请返回JSON格式：
{"intent": "PURE_DB|PURE_KB|HYBRID|BOUNDARY", "confidence": 0.0-1.0, "entities": {"employee_names": [], "departments": []}, "keywords": []}"""

        response = await self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"intent": "BOUNDARY", "confidence": 0.5, "entities": {}, "keywords": []}

    @property
    def provider_name(self) -> str:
        return self.provider.provider_name

    @property
    def display_name(self) -> str:
        return self.provider.display_name
