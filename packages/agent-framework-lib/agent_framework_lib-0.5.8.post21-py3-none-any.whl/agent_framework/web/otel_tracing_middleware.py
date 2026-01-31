"""FastAPI middleware for OpenTelemetry tracing integration.

This middleware creates OTel spans for API requests and injects
tracing context into the request state for use by handlers.

The middleware integrates with ObservabilityManager to provide:
- Automatic API span creation for all requests
- Request ID generation and propagation
- Trace context injection into request state
- Integration with existing API timing middleware
"""

import logging
import os
import uuid
from typing import Any, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp


logger = logging.getLogger(__name__)


class OTelTracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add OpenTelemetry tracing to API requests.

    This middleware:
    - Creates a parent API span for each request
    - Generates and propagates request_id
    - Stores tracing context in request.state.otel_context
    - Integrates with ObservabilityManager for unified observability
    - Works alongside APITimingMiddleware for comprehensive metrics
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: Optional[bool] = None,
        excluded_paths: Optional[list[str]] = None,
    ):
        """Initialize the OTel tracing middleware.

        Args:
            app: The ASGI application
            enabled: Whether tracing is enabled (default: from OTEL_ENABLED env var)
            excluded_paths: List of path prefixes to exclude from tracing
        """
        super().__init__(app)
        if enabled is None:
            enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
        self.enabled = enabled
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json", "/stream"]
        self._observability_manager: Any = None

    def _get_observability_manager(self) -> Any:
        """Get or create the ObservabilityManager instance."""
        if self._observability_manager is None:
            try:
                from ..monitoring.observability_manager import get_observability_manager
                self._observability_manager = get_observability_manager()
            except ImportError:
                logger.warning("ObservabilityManager not available, tracing disabled")
                self.enabled = False
        return self._observability_manager

    def _should_trace(self, path: str) -> bool:
        """Check if the request path should be traced."""
        if not self.enabled:
            return False
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        return True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with OTel tracing."""
        path = str(request.url.path)
        
        if not self._should_trace(path):
            return await call_next(request)

        obs_manager = self._get_observability_manager()
        if not obs_manager:
            return await call_next(request)

        # Generate request ID (use existing if provided in header)
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Extract session_id from query params or headers if available
        session_id = (
            request.query_params.get("session_id")
            or request.headers.get("X-Session-ID")
        )

        # Create API span context
        async with obs_manager.api_request(
            endpoint=path,
            method=request.method,
            session_id=session_id,
            request_id=request_id,
        ) as api_ctx:
            # Store context in request state for handlers
            request.state.otel_context = api_ctx
            request.state.request_id = request_id
            
            # Get trace context for response headers
            trace_id, span_id = obs_manager.get_trace_context()
            
            try:
                response = await call_next(request)
                
                # Set HTTP status code on span
                if hasattr(obs_manager, 'tracing') and hasattr(obs_manager.tracing, 'set_api_status_code'):
                    obs_manager.tracing.set_api_status_code(api_ctx, response.status_code)
                
                # Add trace context to response headers
                if trace_id:
                    response.headers["X-Trace-ID"] = trace_id
                if span_id:
                    response.headers["X-Span-ID"] = span_id
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                # Record exception in span
                logger.error(f"Request failed: {e}")
                raise


def get_otel_context(request: Request) -> Optional[Any]:
    """Get the OTel API span context from request state.

    Use this helper in route handlers to access the tracing context.

    Example:
        @app.post("/chat")
        async def chat(request: Request, ...):
            api_ctx = get_otel_context(request)
            if api_ctx:
                # Record LLM metrics to the API context
                obs_manager.record_llm_call(metrics, api_context=api_ctx)
    """
    return getattr(request.state, "otel_context", None)


def get_request_id(request: Request) -> Optional[str]:
    """Get the request ID from request state.

    Use this helper in route handlers to access the request ID.

    Example:
        @app.post("/chat")
        async def chat(request: Request, ...):
            request_id = get_request_id(request)
            logger.info(f"Processing request {request_id}")
    """
    return getattr(request.state, "request_id", None)
