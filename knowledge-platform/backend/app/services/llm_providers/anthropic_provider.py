from typing import AsyncGenerator
from anthropic import AsyncAnthropic

from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"
    display_name = "Anthropic Claude"
    supports_chat = True
    supports_embedding = False
    supports_streaming = True

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.anthropic.com")
        self.default_model = config.get("model", "claude-sonnet-4-20250514")
        self.client = AsyncAnthropic(api_key=self.api_key, base_url=self.api_base)

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=2000) -> str:
        # Anthropic 需要分离 system 消息
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        kwargs = {
            "model": model or self.default_model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_msg:
            kwargs["system"] = system_msg

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def stream_chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        kwargs = {
            "model": model or self.default_model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_msg:
            kwargs["system"] = system_msg

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    def get_available_models(self):
        return [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "type": "chat"},
            {"id": "claude-haiku-4-20250506", "name": "Claude Haiku 4", "type": "chat"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://api.anthropic.com",
            "model": "claude-sonnet-4-20250514",
        }
