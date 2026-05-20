from .openai_provider import OpenAIProvider


class MoonshotProvider(OpenAIProvider):
    """月之暗面 Kimi — OpenAI 兼容 API"""
    provider_name = "moonshot"
    display_name = "月之暗面 Kimi"
    supports_chat = True
    supports_embedding = False

    def __init__(self, config: dict):
        config.setdefault("api_base", "https://api.moonshot.cn/v1")
        config.setdefault("model", "moonshot-v1-128k")
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "type": "chat"},
            {"id": "moonshot-v1-32k", "name": "Moonshot V1 32K", "type": "chat"},
            {"id": "moonshot-v1-8k", "name": "Moonshot V1 8K", "type": "chat"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-128k",
        }
