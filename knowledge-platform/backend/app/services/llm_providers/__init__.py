from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .zhipu_provider import ZhipuProvider
from .qwen_provider import QwenProvider
from .wenxin_provider import WenxinProvider
from .moonshot_provider import MoonshotProvider
from .deepseek_provider import DeepseekProvider
from .ollama_provider import OllamaProvider


class ProviderRegistry:
    """LLM 提供商注册表"""
    _providers: dict[str, BaseLLMProvider] = {}

    @classmethod
    def register(cls, provider_class: type[BaseLLMProvider]):
        """注册提供商类"""
        instance = provider_class.__new__(provider_class)
        cls._providers[provider_class.provider_name] = instance

    @classmethod
    def get(cls, provider_name: str) -> type[BaseLLMProvider]:
        """获取提供商类"""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls._providers.keys())}")
        return cls._providers[provider_name]

    @classmethod
    def create(cls, provider_name: str, config: dict) -> BaseLLMProvider:
        """创建提供商实例"""
        provider_cls = type(cls.get(provider_name))
        return provider_cls(config)

    @classmethod
    def list_providers(cls) -> list[dict]:
        """列出所有提供商"""
        return [
            {
                "name": p.provider_name,
                "display_name": p.display_name,
                "supports_chat": p.supports_chat,
                "supports_embedding": p.supports_embedding,
                "supports_streaming": p.supports_streaming,
            }
            for p in cls._providers.values()
        ]

    @classmethod
    def list_provider_models(cls, provider_name: str) -> list[dict]:
        """列出某提供商的可用模型"""
        provider = cls.get(provider_name)
        return provider.get_available_models()

    @classmethod
    def get_provider_default_config(cls, provider_name: str) -> dict:
        """获取提供商默认配置"""
        provider = cls.get(provider_name)
        return provider.get_default_config()


# 注册所有内置提供商
for provider_cls in [
    OpenAIProvider,
    AnthropicProvider,
    ZhipuProvider,
    QwenProvider,
    WenxinProvider,
    MoonshotProvider,
    DeepseekProvider,
    OllamaProvider,
]:
    ProviderRegistry.register(provider_cls)

__all__ = [
    "BaseLLMProvider",
    "ProviderRegistry",
    "OpenAIProvider",
    "AnthropicProvider",
    "ZhipuProvider",
    "QwenProvider",
    "WenxinProvider",
    "MoonshotProvider",
    "DeepseekProvider",
    "OllamaProvider",
]
