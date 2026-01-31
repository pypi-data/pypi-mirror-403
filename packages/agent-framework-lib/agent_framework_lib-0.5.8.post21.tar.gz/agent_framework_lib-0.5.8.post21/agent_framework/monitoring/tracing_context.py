"""API-First Tracing Context Manager.

Provides OpenTelemetry tracing with API-first hierarchy where:
- API requests are parent spans
- LLM calls are child spans nested under API spans

This module implements the trace hierarchy required for request-centric
performance analysis, enabling operators to see the full request lifecycle
with LLM calls as children of the API span.

Example:
    ```python
    from agent_framework.monitoring.tracing_context import (
        TracingContextManager,
        get_tracing_context_manager,
    )
    from agent_framework.monitoring.otel_setup import get_otel_setup

    setup = get_otel_setup()
    setup.initialize()

    tracing = TracingContextManager(setup)

    with tracing.api_request_span(
        endpoint="/chat",
        method="POST",
        session_id="sess-123"
    ) as api_ctx:
        # LLM calls automatically become children
        with tracing.llm_call_span(model_name="gpt-4") as llm_ctx:
            # Perform LLM call
            response = await llm.chat(messages)
            llm_ctx.record_tokens(input_tokens=100, output_tokens=50)

        # API span gets aggregated metrics
        print(f"Total LLM calls: {api_ctx.llm_call_count}")
    ```
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Generator

    from agent_framework.monitoring.otel_setup import OTelSetup

logger = logging.getLogger(__name__)


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM call within an API request.

    Captures per-call token counts and timing for aggregation
    at the API span level.

    Attributes:
        model_name: Name of the LLM model used
        input_tokens: Number of input tokens sent to the model
        output_tokens: Number of output tokens received
        thinking_tokens: Number of thinking/reasoning tokens (if applicable)
        duration_ms: Total duration of the LLM call in milliseconds
        time_to_first_token_ms: Time until first token received (streaming)
        operation: Type of operation (e.g., "chat", "completion")
    """

    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    duration_ms: float = 0.0
    time_to_first_token_ms: float | None = None
    operation: str = "chat"

    @property
    def total_tokens(self) -> int:
        """Total tokens for this LLM call."""
        return self.input_tokens + self.output_tokens + self.thinking_tokens


@dataclass
class LLMSpanContext:
    """Context for an LLM call span.

    Provides methods to record metrics during the LLM call execution.
    The span is automatically a child of the current API span.

    Attributes:
        span: OpenTelemetry Span instance (or None if OTel unavailable)
        model_name: Name of the LLM model
        operation: Type of operation
        start_time: When the LLM call started (perf_counter)
    """

    span: Any
    model_name: str
    operation: str = "chat"
    start_time: float = field(default_factory=time.perf_counter)
    _input_tokens: int = field(default=0, repr=False)
    _output_tokens: int = field(default=0, repr=False)
    _thinking_tokens: int = field(default=0, repr=False)
    _time_to_first_token_ms: float | None = field(default=None, repr=False)

    def record_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
    ) -> None:
        """Record token counts for this LLM call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            thinking_tokens: Number of thinking/reasoning tokens
        """
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._thinking_tokens = thinking_tokens

    def record_time_to_first_token(self, ttft_ms: float) -> None:
        """Record time to first token for streaming responses.

        Args:
            ttft_ms: Time to first token in milliseconds
        """
        self._time_to_first_token_ms = ttft_ms

    def get_metrics(self) -> LLMCallMetrics:
        """Get the collected metrics for this LLM call.

        Returns:
            LLMCallMetrics with all recorded data
        """
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        return LLMCallMetrics(
            model_name=self.model_name,
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
            thinking_tokens=self._thinking_tokens,
            duration_ms=duration_ms,
            time_to_first_token_ms=self._time_to_first_token_ms,
            operation=self.operation,
        )


@dataclass
class APISpanContext:
    """Context for an API request span with LLM call tracking.

    Tracks the parent API span and aggregates metrics from all
    child LLM calls made during the request.

    Attributes:
        span: OpenTelemetry Span instance (or None if OTel unavailable)
        request_id: Unique identifier for this request
        endpoint: HTTP endpoint path
        method: HTTP method
        session_id: Session identifier for correlation
        llm_calls: List of LLM call metrics collected during the request
        start_time: When the API request started (perf_counter)
    """

    span: Any
    request_id: str
    endpoint: str
    method: str
    session_id: str | None = None
    llm_calls: list[LLMCallMetrics] = field(default_factory=list)
    start_time: float = field(default_factory=time.perf_counter)

    def add_llm_call(self, metrics: LLMCallMetrics) -> None:
        """Add LLM call metrics to this API request.

        Args:
            metrics: LLMCallMetrics from a completed LLM call
        """
        self.llm_calls.append(metrics)

    @property
    def llm_call_count(self) -> int:
        """Number of LLM calls made during this request."""
        return len(self.llm_calls)

    @property
    def total_llm_duration_ms(self) -> float:
        """Total duration of all LLM calls in milliseconds."""
        return sum(call.duration_ms for call in self.llm_calls)

    @property
    def total_input_tokens(self) -> int:
        """Total input tokens across all LLM calls."""
        return sum(call.input_tokens for call in self.llm_calls)

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens across all LLM calls."""
        return sum(call.output_tokens for call in self.llm_calls)

    @property
    def total_tokens(self) -> int:
        """Total tokens across all LLM calls."""
        return sum(call.total_tokens for call in self.llm_calls)

    @property
    def api_duration_ms(self) -> float:
        """Total API request duration in milliseconds."""
        return (time.perf_counter() - self.start_time) * 1000

    @property
    def llm_percentage(self) -> float:
        """Percentage of API time spent in LLM calls."""
        api_duration = self.api_duration_ms
        if api_duration > 0:
            return (self.total_llm_duration_ms / api_duration) * 100
        return 0.0

    def finalize(self) -> None:
        """Add aggregated metrics to span before closing.

        Sets span attributes with aggregated LLM metrics:
        - llm.call_count: Number of LLM calls
        - llm.total_duration_ms: Total LLM time
        - llm.percentage: Percentage of API time in LLM
        - llm.total_input_tokens: Total input tokens
        - llm.total_output_tokens: Total output tokens
        """
        if not self.span:
            return

        try:
            self.span.set_attribute("llm.call_count", self.llm_call_count)
            self.span.set_attribute("llm.total_duration_ms", self.total_llm_duration_ms)
            self.span.set_attribute("llm.percentage", self.llm_percentage)
            self.span.set_attribute("llm.total_input_tokens", self.total_input_tokens)
            self.span.set_attribute("llm.total_output_tokens", self.total_output_tokens)
            self.span.set_attribute("llm.total_tokens", self.total_tokens)
        except Exception as e:
            logger.warning(f"Failed to finalize API span attributes: {e}")


class TracingContextManager:
    """Manages trace context with API-first hierarchy.

    Creates parent spans for API requests and child spans for LLM calls,
    ensuring proper parent-child relationships in distributed traces.

    The manager uses the OTelSetup instance to get tracers and handles
    graceful degradation when OTel is not available.

    Attributes:
        ATTR_HTTP_METHOD: Semantic convention for HTTP method
        ATTR_HTTP_ROUTE: Semantic convention for HTTP route
        ATTR_HTTP_STATUS_CODE: Semantic convention for HTTP status
        ATTR_SESSION_ID: Custom attribute for session correlation
        ATTR_REQUEST_ID: Custom attribute for request correlation
        ATTR_MODEL: Semantic convention for LLM model
        ATTR_INPUT_TOKENS: Semantic convention for input tokens
        ATTR_OUTPUT_TOKENS: Semantic convention for output tokens
        ATTR_DURATION_MS: Custom attribute for duration
    """

    ATTR_HTTP_METHOD = "http.method"
    ATTR_HTTP_ROUTE = "http.route"
    ATTR_HTTP_STATUS_CODE = "http.status_code"
    ATTR_SESSION_ID = "session.id"
    ATTR_REQUEST_ID = "request.id"

    ATTR_MODEL = "gen_ai.request.model"
    ATTR_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    ATTR_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
    ATTR_THINKING_TOKENS = "gen_ai.usage.thinking_tokens"
    ATTR_DURATION_MS = "gen_ai.response.duration_ms"
    ATTR_TTFT_MS = "gen_ai.response.time_to_first_token_ms"
    ATTR_OPERATION = "gen_ai.operation.name"

    def __init__(self, otel_setup: OTelSetup) -> None:
        """Initialize the tracing context manager.

        Args:
            otel_setup: OTelSetup instance for getting tracers
        """
        self._setup = otel_setup
        self._tracer = otel_setup.get_tracer("agent_framework.api")

    @contextmanager
    def api_request_span(
        self,
        endpoint: str,
        method: str,
        request_id: str | None = None,
        session_id: str | None = None,
    ) -> Generator[APISpanContext, None, None]:
        """Create parent span for API request.

        Creates a span that serves as the parent for all LLM calls
        made during this request. The span follows OTel semantic
        conventions for HTTP requests.

        Args:
            endpoint: HTTP endpoint path (e.g., "/chat", "/api/v1/messages")
            method: HTTP method (e.g., "POST", "GET")
            request_id: Unique request identifier (auto-generated if not provided)
            session_id: Session identifier for correlation

        Yields:
            APISpanContext for tracking LLM calls and aggregating metrics

        Example:
            ```python
            with tracing.api_request_span(
                endpoint="/chat",
                method="POST",
                session_id="sess-123"
            ) as ctx:
                # Process request with LLM calls
                pass
            ```
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        if not self._tracer or not self._setup.is_initialized:
            ctx = APISpanContext(
                span=None,
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                session_id=session_id,
            )
            yield ctx
            return

        try:
            from opentelemetry.trace import Status, StatusCode
        except ImportError:
            ctx = APISpanContext(
                span=None,
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                session_id=session_id,
            )
            yield ctx
            return

        operation_name = f"{method} {endpoint}"

        with self._tracer.start_as_current_span(operation_name) as span:
            span.set_attribute(self.ATTR_HTTP_METHOD, method)
            span.set_attribute(self.ATTR_HTTP_ROUTE, endpoint)
            span.set_attribute(self.ATTR_REQUEST_ID, request_id)
            if session_id:
                span.set_attribute(self.ATTR_SESSION_ID, session_id)

            ctx = APISpanContext(
                span=span,
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                session_id=session_id,
            )

            try:
                yield ctx
                ctx.finalize()
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                ctx.finalize()
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @contextmanager
    def llm_call_span(
        self,
        model_name: str,
        operation: str = "chat",
        api_context: APISpanContext | None = None,
    ) -> Generator[LLMSpanContext, None, None]:
        """Create child span for LLM call within current API context.

        Creates a span that is automatically a child of the current
        active span (typically the API request span). The span follows
        OTel semantic conventions for generative AI.

        Args:
            model_name: Name of the LLM model being called
            operation: Type of operation (default: "chat")
            api_context: Optional APISpanContext to add metrics to

        Yields:
            LLMSpanContext for recording token counts and timing

        Example:
            ```python
            with tracing.api_request_span(...) as api_ctx:
                with tracing.llm_call_span(
                    model_name="gpt-4",
                    api_context=api_ctx
                ) as llm_ctx:
                    response = await llm.chat(messages)
                    llm_ctx.record_tokens(input_tokens=100, output_tokens=50)
            ```
        """
        if not self._tracer or not self._setup.is_initialized:
            ctx = LLMSpanContext(
                span=None,
                model_name=model_name,
                operation=operation,
            )
            try:
                yield ctx
            finally:
                if api_context is not None:
                    api_context.add_llm_call(ctx.get_metrics())
            return

        try:
            from opentelemetry.trace import Status, StatusCode
        except ImportError:
            ctx = LLMSpanContext(
                span=None,
                model_name=model_name,
                operation=operation,
            )
            try:
                yield ctx
            finally:
                if api_context is not None:
                    api_context.add_llm_call(ctx.get_metrics())
            return

        span_name = f"llm.{operation}"

        with self._tracer.start_as_current_span(span_name) as span:
            span.set_attribute(self.ATTR_MODEL, model_name)
            span.set_attribute(self.ATTR_OPERATION, operation)

            ctx = LLMSpanContext(
                span=span,
                model_name=model_name,
                operation=operation,
            )

            try:
                yield ctx
                metrics = ctx.get_metrics()
                self._add_llm_metrics_to_span(span, metrics)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                metrics = ctx.get_metrics()
                self._add_llm_metrics_to_span(span, metrics)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            finally:
                if api_context is not None:
                    api_context.add_llm_call(ctx.get_metrics())

    def _add_llm_metrics_to_span(self, span: Any, metrics: LLMCallMetrics) -> None:
        """Add LLM metrics as span attributes.

        Args:
            span: OpenTelemetry Span instance
            metrics: LLMCallMetrics with collected data
        """
        if not span:
            return

        try:
            span.set_attribute(self.ATTR_INPUT_TOKENS, metrics.input_tokens)
            span.set_attribute(self.ATTR_OUTPUT_TOKENS, metrics.output_tokens)
            span.set_attribute(self.ATTR_THINKING_TOKENS, metrics.thinking_tokens)
            span.set_attribute(self.ATTR_DURATION_MS, metrics.duration_ms)
            if metrics.time_to_first_token_ms is not None:
                span.set_attribute(self.ATTR_TTFT_MS, metrics.time_to_first_token_ms)
        except Exception as e:
            logger.warning(f"Failed to add LLM metrics to span: {e}")

    def set_api_status_code(self, ctx: APISpanContext, status_code: int) -> None:
        """Set HTTP status code on API span.

        Args:
            ctx: APISpanContext from api_request_span
            status_code: HTTP status code (e.g., 200, 404, 500)
        """
        if ctx.span:
            try:
                ctx.span.set_attribute(self.ATTR_HTTP_STATUS_CODE, status_code)
            except Exception as e:
                logger.warning(f"Failed to set status code on span: {e}")

    def get_current_trace_context(self) -> tuple[str | None, str | None]:
        """Get current trace_id and span_id for correlation.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None)
            if no active span or OTel unavailable
        """
        if not self._setup.is_initialized:
            return None, None

        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")
        except Exception as e:
            logger.warning(f"Failed to get trace context: {e}")

        return None, None


_default_tracing_manager: TracingContextManager | None = None


def get_tracing_context_manager(otel_setup: OTelSetup | None = None) -> TracingContextManager:
    """Get or create the default tracing context manager.

    Returns a singleton instance of TracingContextManager. If no OTelSetup
    is provided, uses the default from get_otel_setup().

    Args:
        otel_setup: Optional OTelSetup instance

    Returns:
        TracingContextManager instance
    """
    global _default_tracing_manager
    if _default_tracing_manager is None:
        if otel_setup is None:
            from agent_framework.monitoring.otel_setup import get_otel_setup

            otel_setup = get_otel_setup()
        _default_tracing_manager = TracingContextManager(otel_setup)
    return _default_tracing_manager


def reset_tracing_context_manager() -> None:
    """Reset the default tracing context manager.

    Useful for testing or reconfiguration.
    """
    global _default_tracing_manager
    _default_tracing_manager = None
