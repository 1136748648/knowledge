import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.models.schemas import UserContext
from app.dal import AuditLogRepository, get_adapter

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        user_context: UserContext | None = None
        if hasattr(request.state, "user"):
            user_context = request.state.user

        response = await call_next(request)

        if user_context and request.url.path.startswith("/api/"):
            try:
                adapter = get_adapter()
                repo = AuditLogRepository(adapter)
                
                from app.models.audit import AuditLog
                
                audit_log = AuditLog(
                    user_id=user_context.user_id,
                    user_roles=user_context.roles,
                    action=request.method,
                    resource_type=request.url.path.split("/")[2] if len(request.url.path.split("/")) > 2 else None,
                    details={
                        "path": str(request.url.path),
                        "query": str(request.url.query),
                        "duration_ms": round((time.time() - start_time) * 1000),
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    status_code=response.status_code,
                )
                await repo.create(audit_log)
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")

        return response
