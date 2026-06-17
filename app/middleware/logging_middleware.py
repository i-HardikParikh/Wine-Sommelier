import time
import uuid
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        response = await call_next(request)

        elapsed_ms = round((time.time() - start) * 1000, 1)
        logger.info(
            "request_end",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response
