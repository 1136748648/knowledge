from .openai_provider import OpenAIProvider


class DeepseekProvider(OpenAIProvider):
    """DeepSeek — OpenAI 兼容 API"""
    provider_name = "deepseek"
    display_name = "DeepSeek"
    supports_chat = True
    supports_embedding = True

    def __init__(self, config: dict):
        config.setdefault("api_base", "https://api.deepseek.com/v1")
        config.setdefault("model", "deepseek-chat")
        config.setdefault("embedding_model", "deepseek-embedding")
        config.setdefault("embedding_dim", "4096")
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat"},
            {"id": "deepseek-embedding", "name": "DeepSeek Embedding", "type": "embedding"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "embedding_model": "deepseek-embedding",
            "embedding_dim": "4096",
        }
