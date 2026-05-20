from .openai_provider import OpenAIProvider


class QwenProvider(OpenAIProvider):
    """通义千问 — OpenAI 兼容 API"""
    provider_name = "qwen"
    display_name = "通义千问"
    supports_chat = True
    supports_embedding = True

    def __init__(self, config: dict):
        config.setdefault("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        config.setdefault("model", "qwen-max")
        config.setdefault("embedding_model", "text-embedding-v3")
        config.setdefault("embedding_dim", "1024")
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "qwen-max", "name": "通义千问 Max", "type": "chat"},
            {"id": "qwen-plus", "name": "通义千问 Plus", "type": "chat"},
            {"id": "qwen-turbo", "name": "通义千问 Turbo", "type": "chat"},
            {"id": "qwen-long", "name": "通义千问 Long", "type": "chat"},
            {"id": "text-embedding-v3", "name": "Embedding V3", "type": "embedding"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-max",
            "embedding_model": "text-embedding-v3",
            "embedding_dim": "1024",
        }
