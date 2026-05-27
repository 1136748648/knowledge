from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging
from app.services.storage_service import StorageService
from app.services import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadUrlRequest(BaseModel):
    file_path: str
    expires_in: int = 900


@router.post("/upload-url")
async def get_upload_url(
    request: UploadUrlRequest,
    service: StorageService = Depends(get_storage_service),
):
    if not await service.is_configured():
        raise HTTPException(status_code=503, detail="Storage is not configured. Please set STORAGE_ENDPOINT and other storage configuration.")
    
    try:
        url = await service.get_upload_url(request.file_path, request.expires_in)
        return {"url": url.url, "expires_in": url.expires_in}
    except Exception as e:
        logger.error(f"Failed to get upload URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@router.post("/test")
async def test_connection(
    service: StorageService = Depends(get_storage_service),
):
    success, message = await service.test_connection()
    return {"success": success, "message": message}
