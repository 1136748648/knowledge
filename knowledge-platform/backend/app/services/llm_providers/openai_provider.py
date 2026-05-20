from typing import AsyncGenerator
from openai import AsyncOpenAI

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"
    display_name = "OpenAI"
    supports_chat = True
    supports_embedding = True
    supports_streaming = True

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        self.default_model = config.get("model", "gpt-4o")
        self.default_embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_base)

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=2000) -> str:
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def stream_chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        stream = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text, model=None) -> list[float]:
        response = await self.client.embeddings.create(
            model=model or self.default_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts, model=None) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=model or self.default_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def get_available_models(self):
        return [
            {"id": "gpt-4o", "name": "GPT-4o", "type": "chat"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "chat"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat"},
            {"id": "text-embedding-3-small", "name": "Embedding 3 Small", "type": "embedding"},
            {"id": "text-embedding-3-large", "name": "Embedding 3 Large", "type": "embedding"},
        ]

    def get_default_config(self):
        return {
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "embedding_model": "text-embedding-3-small",
            "embedding_dim": "1536",
        }
