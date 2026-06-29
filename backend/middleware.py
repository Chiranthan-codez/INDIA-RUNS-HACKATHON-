"""
Cross-cutting middleware for the RecruitIQ API.

- RequestIdMiddleware: attaches a unique UUID to every request/response.
- RequestTimingMiddleware: measures wall-clock time and adds X-Process-Time header.
"""
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("backend.middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Assigns a UUID-4 request ID to every incoming request.

    The ID is:
      - Stored in request.state.request_id (available to route handlers)
      - Returned in the X-Request-Id response header
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    Measures request processing time and returns it in the X-Process-Time
    header (in seconds, 4 decimal places).

    Also logs slow requests (>2s) as warnings.
    """
    SLOW_THRESHOLD_S = 2.0

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"

        if elapsed > self.SLOW_THRESHOLD_S:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {elapsed:.2f}s"
            )

        return response
