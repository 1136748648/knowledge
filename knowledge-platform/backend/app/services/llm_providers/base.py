from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseLLMProvider(ABC):
    """LLM 提供商抽象基类"""

    provider_name: str = ""         # 唯一标识，如 "openai", "zhipu"
    display_name: str = ""          # 显示名称，如 "OpenAI", "智谱 GLM"
    supports_chat: bool = True
    supports_embedding: bool = False
    supports_streaming: bool = True

    @abstractmethod
    def __init__(self, config: dict):
        """初始化提供商，config 包含 api_key, api_base, model 等"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """发送聊天请求，返回文本内容"""
        pass

    async def stream_chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """流式聊天，逐块返回文本"""
        # 默认实现：调用 chat 然后一次性 yield
        result = await self.chat(messages, model, temperature, max_tokens)
        yield result

    async def embed(self, text: str, model: str = None) -> list[float]:
        """获取文本嵌入向量"""
        raise NotImplementedError(f"{self.display_name} does not support embeddings")

    async def embed_batch(self, texts: list[str], model: str = None) -> list[list[float]]:
        """批量获取嵌入向量"""
        raise NotImplementedError(f"{self.display_name} does not support embeddings")

    @abstractmethod
    def get_available_models(self) -> list[dict]:
        """返回可用模型列表 [{"id": "gpt-4", "name": "GPT-4", "type": "chat"}]"""
        pass

    @abstractmethod
    def get_default_config(self) -> dict:
        """返回该提供商的默认配置项"""
        pass

    def validate_config(self, config: dict) -> tuple[bool, str]:
        """校验配置是否完整，返回 (是否有效, 错误信息)"""
        if not config.get("api_key"):
            return False, "API Key is required"
        return True, ""
