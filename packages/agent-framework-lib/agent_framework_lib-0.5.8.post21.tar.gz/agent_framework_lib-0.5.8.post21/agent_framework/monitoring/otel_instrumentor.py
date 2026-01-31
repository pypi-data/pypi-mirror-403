"""OpenTelemetry Instrumentation for LLM Calls.

Provides OpenTelemetry integration for LLM observability including:
- Distributed tracing with spans for each LLM call
- Metrics export (counters, histograms)
- Semantic conventions for LLM attributes (gen_ai.*)
- Graceful degradation when OTEL is not configured

The module uses lazy imports to avoid requiring OpenTelemetry as a hard dependency.
When OTEL packages are not installed or not configured, all operations become no-ops.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP exporter endpoint (e.g., http://localhost:4317)
    OTEL_SERVICE_NAME: Service name for traces (default: agent_framework)
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Generator

    from agent_framework.monitoring.api_timing_tracker import APITimingData
    from agent_framework.monitoring.llm_metrics import LLMMetrics

logger = logging.getLogger(__name__)

# Module-level cache for OTEL components
_tracer: Any = None
_meter: Any = None
_otel_available: bool | None = None


def _check_otel_available() -> bool:
    """Check if OpenTelemetry is available and configured.

    Performs a lazy check for OTEL package availability. The result is cached
    to avoid repeated import attempts.

    Returns:
        True if OpenTelemetry packages are installed, False otherwise
    """
    global _otel_available
    if _otel_available is not None:
        return _otel_available

    try:
        from opentelemetry import metrics, trace  # noqa: F401
        from opentelemetry.sdk.metrics import MeterProvider  # noqa: F401
        from opentelemetry.sdk.trace import TracerProvider  # noqa: F401

        _otel_available = True
        logger.debug("OpenTelemetry packages available")
    except ImportError:
        _otel_available = False
        logger.debug("OpenTelemetry packages not installed, OTEL features disabled")

    return _otel_available


def get_tracer() -> Any:
    """Get or create OpenTelemetry tracer for LLM operations.

    Returns a tracer instance for creating spans. If OTEL is not available,
    returns None and all tracing operations become no-ops.

    Returns:
        OpenTelemetry Tracer instance or None if OTEL unavailable

    Example:
        ```python
        tracer = get_tracer()
        if tracer:
            with tracer.start_as_current_span("llm.chat") as span:
                span.set_attribute("model", "gpt-5")
        ```
    """
    global _tracer
    if not _check_otel_available():
        return None

    if _tracer is None:
        from opentelemetry import trace

        _tracer = trace.get_tracer("agent_framework.llm", "1.0.0")

    return _tracer


def get_meter() -> Any:
    """Get or create OpenTelemetry meter for LLM metrics.

    Returns a meter instance for recording metrics (counters, histograms).
    If OTEL is not available, returns None and all metrics operations become no-ops.

    Returns:
        OpenTelemetry Meter instance or None if OTEL unavailable

    Example:
        ```python
        meter = get_meter()
        if meter:
            counter = meter.create_counter("llm.tokens.total")
            counter.add(100, {"model": "gpt-5"})
        ```
    """
    global _meter
    if not _check_otel_available():
        return None

    if _meter is None:
        from opentelemetry import metrics

        _meter = metrics.get_meter("agent_framework.llm", "1.0.0")

    return _meter


class OTELInstrumentor:
    """OpenTelemetry instrumentation for LLM calls.

    Provides tracing and metrics instrumentation following OpenTelemetry
    semantic conventions for generative AI (gen_ai.* attributes).

    The instrumentor gracefully degrades when OTEL is not configured,
    making all operations no-ops without raising errors.

    Attributes:
        ATTR_MODEL: Semantic convention attribute for model name
        ATTR_INPUT_TOKENS: Attribute for input token count
        ATTR_OUTPUT_TOKENS: Attribute for output token count
        ATTR_TOTAL_TOKENS: Attribute for total token count
        ATTR_THINKING_TOKENS: Attribute for thinking/reasoning tokens
        ATTR_DURATION_MS: Attribute for request duration
        ATTR_TTFT_MS: Attribute for time to first token
        ATTR_SESSION_ID: Attribute for session correlation
        ATTR_USER_ID: Attribute for user correlation

    Example:
        ```python
        instrumentor = OTELInstrumentor()

        with instrumentor.trace_llm_call(
            operation_name="llm.chat",
            model_name="gpt-5-mini",
            session_id="session-123"
        ) as span:
            # Perform LLM call
            response = await llm.chat(messages)

        # Record metrics after call completes
        instrumentor.record_metrics(metrics)
        instrumentor.add_metrics_to_span(span, metrics)
        ```
    """

    # Semantic convention attributes for LLM (gen_ai.* namespace)
    ATTR_MODEL = "gen_ai.request.model"
    ATTR_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    ATTR_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
    ATTR_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
    ATTR_THINKING_TOKENS = "gen_ai.usage.thinking_tokens"
    ATTR_DURATION_MS = "gen_ai.response.duration_ms"
    ATTR_TTFT_MS = "gen_ai.response.time_to_first_token_ms"
    ATTR_SESSION_ID = "session.id"
    ATTR_USER_ID = "user.id"

    # API timing attributes
    ATTR_API_DURATION_MS = "http.request.duration_ms"
    ATTR_API_PREPROCESSING_MS = "http.request.preprocessing_ms"
    ATTR_API_POSTPROCESSING_MS = "http.request.postprocessing_ms"
    ATTR_API_LLM_PERCENTAGE = "http.request.llm_percentage"
    ATTR_API_TTFC_MS = "http.request.time_to_first_chunk_ms"
    ATTR_API_ENDPOINT = "http.route"
    ATTR_API_METHOD = "http.method"
    ATTR_API_REQUEST_ID = "http.request.id"

    def __init__(self) -> None:
        """Initialize the OTEL instrumentor.

        Sets up tracer and meter instances, and creates metric instruments
        if OTEL is available.
        """
        self._tracer = get_tracer()
        self._meter = get_meter()
        self._token_counter: Any = None
        self._latency_histogram: Any = None
        self._ttft_histogram: Any = None
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up OTEL metrics instruments.

        Creates counter and histogram instruments for tracking:
        - Total tokens processed (counter)
        - Request duration (histogram)
        - Time to first token (histogram)
        """
        if not self._meter:
            return

        try:
            self._token_counter = self._meter.create_counter(
                "llm.tokens.total",
                description="Total tokens processed by LLM calls",
                unit="tokens",
            )

            self._latency_histogram = self._meter.create_histogram(
                "llm.request.duration",
                description="LLM request duration in milliseconds",
                unit="ms",
            )

            self._ttft_histogram = self._meter.create_histogram(
                "llm.request.time_to_first_token",
                description="Time to first token in milliseconds",
                unit="ms",
            )
            logger.debug("OTEL metrics instruments created successfully")
        except Exception as e:
            logger.warning(f"Failed to create OTEL metrics instruments: {e}")

    @contextmanager
    def trace_llm_call(
        self,
        operation_name: str = "llm.chat",
        model_name: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> Generator[Any, None, None]:
        """Context manager for tracing an LLM call.

        Creates a span for the LLM operation with initial attributes.
        Additional attributes can be added to the span during execution.

        Args:
            operation_name: Name for the span (default: "llm.chat")
            model_name: LLM model being used
            session_id: Session identifier for correlation
            user_id: User identifier for correlation

        Yields:
            OpenTelemetry Span instance or None if OTEL unavailable

        Example:
            ```python
            with instrumentor.trace_llm_call(
                model_name="gpt-5",
                session_id="sess-123"
            ) as span:
                response = await llm.chat(messages)
                if span:
                    span.set_attribute("custom.attr", "value")
            ```
        """
        if not self._tracer:
            yield None
            return

        from opentelemetry.trace import Status, StatusCode

        with self._tracer.start_as_current_span(operation_name) as span:
            try:
                if model_name:
                    span.set_attribute(self.ATTR_MODEL, model_name)
                if session_id:
                    span.set_attribute(self.ATTR_SESSION_ID, session_id)
                if user_id:
                    span.set_attribute(self.ATTR_USER_ID, user_id)

                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def record_metrics(self, metrics: LLMMetrics) -> None:
        """Record metrics to OTEL metrics backend.

        Exports token counts and timing measurements to the configured
        OTEL metrics backend (e.g., Prometheus, OTLP collector).

        Args:
            metrics: LLMMetrics instance with collected data

        Example:
            ```python
            metrics = collector.finish()
            instrumentor.record_metrics(metrics)
            ```
        """
        if not self._meter:
            return

        attributes = {
            "model": metrics.model_name or "unknown",
            "session_id": metrics.session_id or "unknown",
        }

        try:
            # Record token counts
            if self._token_counter:
                self._token_counter.add(metrics.total_tokens, attributes=attributes)

            # Record latency
            if metrics.duration_ms and self._latency_histogram:
                self._latency_histogram.record(metrics.duration_ms, attributes=attributes)

            # Record TTFT
            if metrics.time_to_first_token_ms and self._ttft_histogram:
                self._ttft_histogram.record(
                    metrics.time_to_first_token_ms, attributes=attributes
                )
        except Exception as e:
            logger.warning(f"Failed to record OTEL metrics: {e}")

    def add_metrics_to_span(self, span: Any, metrics: LLMMetrics) -> None:
        """Add metrics as span attributes.

        Enriches an existing span with token counts and timing measurements
        following gen_ai.* semantic conventions.

        Args:
            span: OpenTelemetry Span instance (can be None)
            metrics: LLMMetrics instance with collected data

        Example:
            ```python
            with instrumentor.trace_llm_call() as span:
                # ... perform LLM call ...
                metrics = collector.finish()
                instrumentor.add_metrics_to_span(span, metrics)
            ```
        """
        if not span:
            return

        try:
            span.set_attribute(self.ATTR_INPUT_TOKENS, metrics.input_tokens)
            span.set_attribute(self.ATTR_THINKING_TOKENS, metrics.thinking_tokens)
            span.set_attribute(self.ATTR_OUTPUT_TOKENS, metrics.output_tokens)
            span.set_attribute(self.ATTR_TOTAL_TOKENS, metrics.total_tokens)

            if metrics.duration_ms is not None:
                span.set_attribute(self.ATTR_DURATION_MS, metrics.duration_ms)
            if metrics.time_to_first_token_ms is not None:
                span.set_attribute(self.ATTR_TTFT_MS, metrics.time_to_first_token_ms)
        except Exception as e:
            logger.warning(f"Failed to add metrics to span: {e}")

    def get_current_trace_context(self) -> tuple[str | None, str | None]:
        """Get current trace_id and span_id for correlation.

        Retrieves the current trace context from the active span, useful
        for correlating logs and metrics with distributed traces.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None)
            if no active span or OTEL unavailable

        Example:
            ```python
            trace_id, span_id = instrumentor.get_current_trace_context()
            if trace_id:
                log.info("Processing request", extra={
                    "trace_id": trace_id,
                    "span_id": span_id
                })
            ```
        """
        if not _check_otel_available():
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

    @contextmanager
    def trace_api_request(
        self,
        endpoint: str | None = None,
        method: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
    ) -> Generator[Any, None, None]:
        """Context manager for tracing an API request.

        Creates a parent span for the full API request lifecycle.
        Child spans for LLM calls will be nested under this span.

        Args:
            endpoint: HTTP endpoint path
            method: HTTP method (GET, POST, etc.)
            request_id: Unique request identifier
            session_id: Session identifier for correlation

        Yields:
            OpenTelemetry Span instance or None if OTEL unavailable
        """
        if not self._tracer:
            yield None
            return

        from opentelemetry.trace import Status, StatusCode

        operation_name = f"http.request {method or 'UNKNOWN'} {endpoint or '/'}"

        with self._tracer.start_as_current_span(operation_name) as span:
            try:
                if endpoint:
                    span.set_attribute(self.ATTR_API_ENDPOINT, endpoint)
                if method:
                    span.set_attribute(self.ATTR_API_METHOD, method)
                if request_id:
                    span.set_attribute(self.ATTR_API_REQUEST_ID, request_id)
                if session_id:
                    span.set_attribute(self.ATTR_SESSION_ID, session_id)

                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def add_api_timing_to_span(self, span: Any, timing_data: APITimingData) -> None:
        """Add API timing data as span attributes.

        Enriches an existing span with API timing measurements.

        Args:
            span: OpenTelemetry Span instance (can be None)
            timing_data: APITimingData instance with collected data
        """
        if not span:
            return

        try:
            if timing_data.total_api_duration_ms is not None:
                span.set_attribute(self.ATTR_API_DURATION_MS, timing_data.total_api_duration_ms)
            if timing_data.preprocessing_duration_ms is not None:
                span.set_attribute(
                    self.ATTR_API_PREPROCESSING_MS, timing_data.preprocessing_duration_ms
                )
            if timing_data.postprocessing_duration_ms is not None:
                span.set_attribute(
                    self.ATTR_API_POSTPROCESSING_MS, timing_data.postprocessing_duration_ms
                )
            if timing_data.llm_percentage is not None:
                span.set_attribute(self.ATTR_API_LLM_PERCENTAGE, timing_data.llm_percentage)
            if timing_data.time_to_first_chunk_ms is not None:
                span.set_attribute(self.ATTR_API_TTFC_MS, timing_data.time_to_first_chunk_ms)
            if timing_data.endpoint:
                span.set_attribute(self.ATTR_API_ENDPOINT, timing_data.endpoint)
            if timing_data.method:
                span.set_attribute(self.ATTR_API_METHOD, timing_data.method)
            span.set_attribute(self.ATTR_API_REQUEST_ID, timing_data.request_id)
        except Exception as e:
            logger.warning(f"Failed to add API timing to span: {e}")

    def record_api_timing_metrics(self, timing_data: APITimingData) -> None:
        """Record API timing metrics to OTEL metrics backend.

        Args:
            timing_data: APITimingData instance with collected data
        """
        if not self._meter:
            return

        attributes = {
            "endpoint": timing_data.endpoint or "unknown",
            "method": timing_data.method or "unknown",
            "is_streaming": str(timing_data.is_streaming).lower(),
        }

        try:
            if timing_data.total_api_duration_ms and self._latency_histogram:
                self._latency_histogram.record(
                    timing_data.total_api_duration_ms,
                    attributes={**attributes, "phase": "total"},
                )
        except Exception as e:
            logger.warning(f"Failed to record API timing metrics: {e}")


# Module-level convenience instance
_default_instrumentor: OTELInstrumentor | None = None


def get_otel_instrumentor() -> OTELInstrumentor:
    """Get or create the default OTEL instrumentor instance.

    Returns a singleton instance of OTELInstrumentor for convenience.
    The instrumentor gracefully handles missing OTEL packages.

    Returns:
        OTELInstrumentor instance

    Example:
        ```python
        instrumentor = get_otel_instrumentor()
        with instrumentor.trace_llm_call(model_name="gpt-5") as span:
            # ... perform LLM call ...
        ```
    """
    global _default_instrumentor
    if _default_instrumentor is None:
        _default_instrumentor = OTELInstrumentor()
    return _default_instrumentor
