from .openai_provider import OpenAIProvider


class DeepseekProvider(OpenAIProvider):
    """DeepSeek — OpenAI 兼容 API"""
    provider_name = "deepseek"
    display_name = "DeepSeek"
    supports_chat = True
    supports_embedding = False

    def __init__(self, config: dict):
        config.setdefault("api_base", "https://api.deepseek.com/v1")
        config.setdefault("model", "deepseek-chat")
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat"},
            {"id": "deepseek-coder", "name": "DeepSeek Coder", "type": "chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
        }
