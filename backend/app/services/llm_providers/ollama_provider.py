from .openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """本地 Ollama — OpenAI 兼容 API"""
    provider_name = "ollama"
    display_name = "Ollama (本地)"
    supports_chat = True
    supports_embedding = True

    def __init__(self, config: dict):
        config.setdefault("api_base", "http://localhost:11434/v1")
        config.setdefault("model", "llama3")
        config.setdefault("embedding_model", "nomic-embed-text")
        config.setdefault("embedding_dim", "768")
        config.setdefault("api_key", "ollama")  # Ollama 不需要真实 key
        super().__init__(config)

    def get_available_models(self):
        return [
            {"id": "llama3", "name": "Llama 3", "type": "chat"},
            {"id": "qwen2", "name": "Qwen 2", "type": "chat"},
            {"id": "deepseek-v2", "name": "DeepSeek V2", "type": "chat"},
            {"id": "mistral", "name": "Mistral", "type": "chat"},
            {"id": "nomic-embed-text", "name": "Nomic Embed Text", "type": "embedding"},
        ]

    def get_default_config(self):
        return {
            "api_base": "http://localhost:11434/v1",
            "model": "llama3",
            "embedding_model": "nomic-embed-text",
            "embedding_dim": "768",
        }

    def validate_config(self, config):
        # Ollama 不需要 API Key
        return True, ""
