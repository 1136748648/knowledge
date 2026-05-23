import uuid
import logging
from app.services.storage_providers import (
    BaseStorageProvider,
    StorageConfig,
    PROVIDER_MAP,
)
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class StorageService:
    """对象存储服务，支持多种存储提供商"""

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self._provider: BaseStorageProvider | None = None

    async def get_provider(self) -> BaseStorageProvider:
        if self._provider:
            return self._provider

        provider_name = await self.config_service.get("storage", "provider", "minio")
        config = StorageConfig(
            provider=provider_name,
            endpoint=await self.config_service.get("storage", "endpoint", ""),
            access_key=await self.config_service.get("storage", "access_key", ""),
            secret_key=await self.config_service.get("storage", "secret_key", ""),
            bucket=await self.config_service.get("storage", "bucket", "wiki"),
            region=await self.config_service.get("storage", "region", ""),
            use_ssl=(await self.config_service.get("storage", "use_ssl", "true")).lower() == "true",
        )

        provider_class = PROVIDER_MAP.get(provider_name, PROVIDER_MAP["minio"])
        self._provider = provider_class(config)
        return self._provider

    def generate_file_path(self, page_id: uuid.UUID, file_id: uuid.UUID, version: int) -> str:
        return f"/wiki/{page_id}/{file_id}/v{version}.md"

    async def upload(self, file_path: str, content: bytes) -> bool:
        provider = await self.get_provider()
        return await provider.upload(file_path, content)

    async def download(self, file_path: str) -> bytes:
        provider = await self.get_provider()
        return await provider.download(file_path)

    async def delete(self, file_path: str) -> bool:
        provider = await self.get_provider()
        return await provider.delete(file_path)

    async def get_upload_url(self, file_path: str, expires_in: int = 900):
        provider = await self.get_provider()
        return await provider.get_presigned_upload_url(file_path, expires_in)

    async def get_download_url(self, file_path: str, expires_in: int = 300):
        provider = await self.get_provider()
        return await provider.get_presigned_download_url(file_path, expires_in)

    async def exists(self, file_path: str) -> bool:
        provider = await self.get_provider()
        return await provider.exists(file_path)

    async def test_connection(self) -> tuple[bool, str]:
        try:
            provider = await self.get_provider()
            return await provider.test_connection()
        except Exception as e:
            return False, str(e)

    async def is_configured(self) -> bool:
        endpoint = await self.config_service.get("storage", "endpoint")
        return endpoint is not None and endpoint != ""
