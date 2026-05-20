import httpx
from typing import AsyncGenerator

from .base import BaseLLMProvider


class WenxinProvider(BaseLLMProvider):
    """文心一言 — 百度自有 API"""
    provider_name = "wenxin"
    display_name = "文心一言"
    supports_chat = True
    supports_embedding = False
    supports_streaming = True

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.secret_key = config.get("secret_key", "")
        self.default_model = config.get("model", "ernie-4.0-8k")
        self._access_token = None

    async def _get_access_token(self) -> str:
        """获取百度 API access_token"""
        if self._access_token:
            return self._access_token
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params)
            data = resp.json()
            self._access_token = data.get("access_token", "")
        return self._access_token

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=2000) -> str:
        token = await self._get_access_token()
        model_name = model or self.default_model
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model_name}?access_token={token}"

        # 转换消息格式
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            return data.get("result", "")

    async def stream_chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        token = await self._get_access_token()
        model_name = model or self.default_model
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model_name}?access_token={token}"

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            if "result" in chunk:
                                yield chunk["result"]
                        except json.JSONDecodeError:
                            pass

    def get_available_models(self):
        return [
            {"id": "ernie-4.0-8k", "name": "ERNIE 4.0", "type": "chat"},
            {"id": "ernie-3.5-8k", "name": "ERNIE 3.5", "type": "chat"},
            {"id": "ernie-speed-8k", "name": "ERNIE Speed", "type": "chat"},
        ]

    def get_default_config(self):
        return {
            "model": "ernie-4.0-8k",
        }

    def validate_config(self, config):
        if not config.get("api_key"):
            return False, "API Key (client_id) is required"
        if not config.get("secret_key"):
            return False, "Secret Key is required for Wenxin"
        return True, ""
