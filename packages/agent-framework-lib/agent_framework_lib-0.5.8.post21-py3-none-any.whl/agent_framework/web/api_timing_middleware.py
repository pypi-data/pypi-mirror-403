"""FastAPI middleware for automatic API request timing.

This middleware tracks the complete request lifecycle and injects
an APITimingTracker into the request state for use by handlers.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp

from agent_framework.monitoring.api_timing_tracker import (
    APITimingData,
    APITimingTracker,
    normalize_endpoint_path,
)


logger = logging.getLogger(__name__)


class APITimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API request timing.

    This middleware:
    - Creates an APITimingTracker for each request
    - Stores it in request.state.api_timing for handler access
    - Handles both streaming and non-streaming responses
    - Records time-to-first-chunk for SSE responses
    - Logs timing data to the configured metrics logger
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool | None = None,
        metrics_logger: Any | None = None,
    ):
        super().__init__(app)
        if enabled is None:
            enabled = os.getenv("API_TIMING_ENABLED", "true").lower() == "true"
        self.enabled = enabled
        self.metrics_logger = metrics_logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        is_streaming = "text/event-stream" in request.headers.get("accept", "")

        # Normalize the endpoint path for consistent metric labeling
        raw_path = str(request.url.path)
        normalized_path = normalize_endpoint_path(raw_path)

        tracker = APITimingTracker(
            endpoint=normalized_path,
            method=request.method,
            is_streaming=is_streaming,
        )

        tracker.start_request()
        request.state.api_timing = tracker

        response = await call_next(request)

        if isinstance(response, StreamingResponse):
            original_body_iterator = response.body_iterator

            async def timed_body_iterator():
                first_chunk = True
                async for chunk in original_body_iterator:
                    if first_chunk:
                        tracker.record_first_chunk()
                        first_chunk = False
                    yield chunk

                timing_data = tracker.finish_request()
                self._log_timing(timing_data)

            response.body_iterator = timed_body_iterator()
            return response

        timing_data = tracker.finish_request()
        self._log_timing(timing_data)

        return response

    def _log_timing(self, timing_data: APITimingData) -> None:
        """Log timing data to metrics logger and standard logging."""
        if self.metrics_logger:
            try:
                self.metrics_logger.log_api_timing(timing_data)
            except Exception as e:
                logger.warning(f"Failed to log API timing to metrics logger: {e}")

        logger.debug(
            f"API timing: {timing_data.endpoint} "
            f"total={timing_data.total_api_duration_ms:.2f}ms "
            f"llm={timing_data.total_llm_duration_ms:.2f}ms "
            f"({timing_data.llm_percentage:.1f}% LLM)"
            if timing_data.total_api_duration_ms and timing_data.llm_percentage
            else f"API timing: {timing_data.endpoint} total={timing_data.total_api_duration_ms}ms"
        )


def get_api_timing_tracker(request: Request) -> APITimingTracker | None:
    """Get the API timing tracker from request state.

    Use this helper in route handlers to access the timing tracker.

    Example:
        @app.post("/chat")
        async def chat(request: Request, ...):
            tracker = get_api_timing_tracker(request)
            if tracker:
                tracker.start_llm_call()
            # ... LLM call ...
            if tracker:
                tracker.end_llm_call()
    """
    return getattr(request.state, "api_timing", None)
