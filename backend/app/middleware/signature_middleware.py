import logging
import json
from typing import Callable
from urllib.parse import parse_qs

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.core.sign_utils import verify_signature, is_timestamp_valid, compute_body_hash

logger = logging.getLogger(__name__)


class SignatureMiddleware(BaseHTTPMiddleware):
    """签名验证中间件"""

    async def dispatch(self, request: Request, call_next: Callable):
        settings = get_settings()
        
        if not settings.SIGNATURE_ENABLED:
            return await call_next(request)
        
        path = str(request.url.path)
        
        excluded_paths = [p.strip() for p in settings.SIGNATURE_EXCLUDED_PATHS.split(',')]
        if path in excluded_paths:
            return await call_next(request)
        
        timestamp_str = request.headers.get('X-Sign-Timestamp')
        nonce = request.headers.get('X-Sign-Nonce')
        signature = request.headers.get('X-Sign-Signature')
        
        if not all([timestamp_str, nonce, signature]):
            logger.warning(f"Missing signature headers: {path}")
            return JSONResponse(
                status_code=403,
                content={"error_code": "99006", "message": "Missing signature headers", "detail": "Missing signature headers"}
            )
        
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp_str}")
            return JSONResponse(
                status_code=403,
                content={"error_code": "99004", "message": "Request expired", "detail": "Invalid timestamp format"}
            )
        
        if not is_timestamp_valid(timestamp, settings.SIGNATURE_TIMESTAMP_TOLERANCE):
            logger.warning(f"Request expired: {path}, timestamp={timestamp}")
            return JSONResponse(
                status_code=403,
                content={"error_code": "99004", "message": "Request expired", "detail": "Request timestamp expired"}
            )
        
        body_bytes = b''
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
            except Exception as e:
                logger.debug(f"Failed to read request body: {e}")
        
        body_hash = compute_body_hash(body_bytes)
        logger.debug(f"Request body hash: {body_hash}")
        
        params = {
            'timestamp': timestamp_str,
            'nonce': nonce,
            'body_hash': body_hash
        }
        
        if not verify_signature(params, signature, settings.SIGNATURE_SECRET_KEY):
            logger.warning(f"Signature verification failed: {path}")
            return JSONResponse(
                status_code=403,
                content={"error_code": "99005", "message": "Signature verification failed", "detail": "Signature verification failed"}
            )
        
        return await call_next(request)
