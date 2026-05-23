import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from .base import BaseStorageProvider, PresignedUrl, StorageConfig


class MinIOProvider(BaseStorageProvider):
    provider_name = "minio"
    display_name = "MinIO"

    def __init__(self, config: StorageConfig):
        self.config = config
        self.client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if config.use_ssl else 'http'}://{config.endpoint}",
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region or "us-east-1",
            config=BotoConfig(signature_version="s3v4"),
        )

    async def upload(self, file_path: str, content: bytes) -> bool:
        try:
            self.client.put_object(Bucket=self.config.bucket, Key=file_path, Body=content)
            return True
        except Exception:
            return False

    async def download(self, file_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.config.bucket, Key=file_path)
        return response["Body"].read()

    async def delete(self, file_path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.config.bucket, Key=file_path)
            return True
        except Exception:
            return False

    async def get_presigned_upload_url(self, file_path: str, expires_in: int = 900) -> PresignedUrl:
        url = self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.config.bucket, "Key": file_path},
            ExpiresIn=expires_in,
        )
        return PresignedUrl(url=url, expires_in=expires_in)

    async def get_presigned_download_url(self, file_path: str, expires_in: int = 300) -> PresignedUrl:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.bucket, "Key": file_path},
            ExpiresIn=expires_in,
        )
        return PresignedUrl(url=url, expires_in=expires_in)

    async def exists(self, file_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.config.bucket, Key=file_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def test_connection(self) -> tuple[bool, str]:
        try:
            self.client.head_bucket(Bucket=self.config.bucket)
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
