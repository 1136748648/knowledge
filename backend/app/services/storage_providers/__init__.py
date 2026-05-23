from .base import BaseStorageProvider, PresignedUrl, StorageConfig
from .minio_provider import MinIOProvider
from .s3_provider import S3Provider
from .oss_provider import OSSProvider

PROVIDER_MAP = {
    "minio": MinIOProvider,
    "s3": S3Provider,
    "oss": OSSProvider,
}

__all__ = [
    "BaseStorageProvider",
    "PresignedUrl",
    "StorageConfig",
    "MinIOProvider",
    "S3Provider",
    "OSSProvider",
    "PROVIDER_MAP",
]
