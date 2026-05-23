import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage_providers.base import PresignedUrl


class TestPresignedUrl:
    def test_presigned_url_creation(self):
        url = PresignedUrl(url="http://example.com/upload", expires_in=900)
        
        assert url.url == "http://example.com/upload"
        assert url.expires_in == 900


class TestStorageProviderBase:
    @pytest.mark.asyncio
    async def test_base_class_is_abstract(self):
        from app.services.storage_providers.base import BaseStorageProvider
        
        with pytest.raises(TypeError):
            BaseStorageProvider()
