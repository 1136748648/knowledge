from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class PresignedUrl:
    url: str
    expires_in: int


@dataclass
class StorageConfig:
    provider: str
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str = ""
    use_ssl: bool = True


class BaseStorageProvider(ABC):
    """存储提供商抽象基类"""

    provider_name: str = ""
    display_name: str = ""

    @abstractmethod
    def __init__(self, config: StorageConfig):
        pass

    @abstractmethod
    async def upload(self, file_path: str, content: bytes | BinaryIO) -> bool:
        pass

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def get_presigned_upload_url(self, file_path: str, expires_in: int = 900) -> PresignedUrl:
        pass

    @abstractmethod
    async def get_presigned_download_url(self, file_path: str, expires_in: int = 300) -> PresignedUrl:
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        pass
