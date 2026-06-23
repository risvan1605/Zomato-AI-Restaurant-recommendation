"""
FastAPI middleware.
"""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log basic request details and latency."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.monotonic()
        try:
            response = await call_next(request)
            process_time = time.monotonic() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Latency: {process_time:.3f}s"
            )
            return response
        except Exception as exc:
            process_time = time.monotonic() - start_time
            logger.error(
                f"{request.method} {request.url.path} "
                f"- Failed with {type(exc).__name__} "
                f"- Latency: {process_time:.3f}s"
            )
            raise
