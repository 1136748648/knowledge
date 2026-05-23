import oss2

from .base import BaseStorageProvider, PresignedUrl, StorageConfig


class OSSProvider(BaseStorageProvider):
    provider_name = "oss"
    display_name = "阿里云 OSS"

    def __init__(self, config: StorageConfig):
        self.config = config
        auth = oss2.Auth(config.access_key, config.secret_key)
        bucket_endpoint = config.endpoint
        if config.region:
            bucket_endpoint = f"oss-{config.region}.{config.endpoint}"
        self.bucket = oss2.Bucket(auth, f"https://{bucket_endpoint}", config.bucket)

    async def upload(self, file_path: str, content: bytes) -> bool:
        try:
            self.bucket.put_object(file_path, content)
            return True
        except Exception:
            return False

    async def download(self, file_path: str) -> bytes:
        result = self.bucket.get_object(file_path)
        return result.read()

    async def delete(self, file_path: str) -> bool:
        try:
            self.bucket.delete_object(file_path)
            return True
        except Exception:
            return False

    async def get_presigned_upload_url(self, file_path: str, expires_in: int = 900) -> PresignedUrl:
        url = self.bucket.sign_url("PUT", file_path, expires_in)
        return PresignedUrl(url=url, expires_in=expires_in)

    async def get_presigned_download_url(self, file_path: str, expires_in: int = 300) -> PresignedUrl:
        url = self.bucket.sign_url("GET", file_path, expires_in)
        return PresignedUrl(url=url, expires_in=expires_in)

    async def exists(self, file_path: str) -> bool:
        return self.bucket.object_exists(file_path)

    async def test_connection(self) -> tuple[bool, str]:
        try:
            self.bucket.get_bucket_info()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
