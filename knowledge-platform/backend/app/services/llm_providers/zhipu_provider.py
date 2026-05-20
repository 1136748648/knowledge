from .openai_provider import OpenAIProvider


class ZhipuProvider(OpenAIProvider):
    """智谱 GLM — OpenAI 兼容 API"""
    provider_name = "zhipu"
    display_name = "智谱 GLM"
    supports_chat = True
    supports_embedding = True

    def __init__(self, config: dict):
        config.setdefault("api_base", "https://open.bigmodel.cn/api/paas/v4")
        config.setdefault("model", "glm-4-flash")
        config.setdefault("embedding_model", "embedding-3")
        config.setdefault("embedding_dim", "2048")
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "type": "chat"},
            {"id": "glm-4-air", "name": "GLM-4 Air", "type": "chat"},
            {"id": "glm-4-airx", "name": "GLM-4 AirX", "type": "chat"},
            {"id": "glm-4", "name": "GLM-4", "type": "chat"},
            {"id": "embedding-3", "name": "Embedding-3", "type": "embedding"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4-flash",
            "embedding_model": "embedding-3",
            "embedding_dim": "2048",
        }
