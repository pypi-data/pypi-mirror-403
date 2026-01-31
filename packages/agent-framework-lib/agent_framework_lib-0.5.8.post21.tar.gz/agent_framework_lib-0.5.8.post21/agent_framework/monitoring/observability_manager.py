"""ObservabilityManager Facade.

Provides a unified interface for all observability concerns:
- Tracing (via TracingContextManager)
- Metrics (via OTelMetricsRecorder)
- Logging (via OTelLoggingHandler or ElasticsearchLoggingHandler fallback)
- Direct Elasticsearch metrics logging (optional, for Kibana dashboards)

The ObservabilityManager simplifies observability integration by providing
a single entry point that handles OTel initialization, fallback to Elasticsearch
when OTel is unavailable, and consistent API for recording telemetry.

Environment Variables:
    METRICS_ES_LOGGING_ENABLED: Enable direct ES logging for Kibana dashboards (default: false)
        When enabled, metrics are logged to both OTel and Elasticsearch indices.

Example:
    ```python
    from agent_framework.monitoring.observability_manager import (
        ObservabilityManager,
        get_observability_manager,
    )

    # Get the singleton manager
    manager = get_observability_manager()

    # Use unified API request context
    async with manager.api_request(
        endpoint="/chat",
        method="POST",
        session_id="sess-123"
    ) as ctx:
        # Record LLM calls within the request
        manager.record_llm_call(llm_metrics)

        # Access tracing context
        print(f"Request ID: {ctx.request_id}")
        print(f"LLM calls: {ctx.llm_call_count}")
    ```
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from agent_framework.monitoring.api_timing_tracker import APITimingData
    from agent_framework.monitoring.llm_metrics import LLMMetrics
    from agent_framework.monitoring.otel_setup import OTelSetup
    from agent_framework.monitoring.tracing_context import APISpanContext

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """Unified facade for observability: tracing, metrics, and logging.

    Combines TracingContextManager and OTelMetricsRecorder into a single
    interface, with automatic fallback to Elasticsearch when OTel is
    unavailable.

    Optionally supports direct Elasticsearch logging for Kibana dashboards
    when METRICS_ES_LOGGING_ENABLED=true. This logs metrics to both OTel
    and Elasticsearch indices (agent-metrics-llm-* and agent-metrics-api-*).

    Attributes:
        otel_setup: OTelSetup instance for OTel configuration
        tracing: TracingContextManager for distributed tracing
        metrics: OTelMetricsRecorder for metrics recording
        es_fallback_enabled: Whether ES fallback is active
        es_metrics_logging_enabled: Whether direct ES metrics logging is enabled
    """

    def __init__(
        self,
        otel_setup: OTelSetup | None = None,
        enable_es_fallback: bool = True,
        enable_es_metrics_logging: bool | None = None,
    ) -> None:
        """Initialize the ObservabilityManager.

        Args:
            otel_setup: Optional OTelSetup instance. If not provided,
                       uses the default from get_otel_setup().
            enable_es_fallback: Whether to enable Elasticsearch fallback
                               when OTel is unavailable (default: True)
            enable_es_metrics_logging: Whether to enable direct ES metrics logging
                                      for Kibana dashboards. If None, reads from
                                      METRICS_ES_LOGGING_ENABLED env var (default: false)
        """
        from agent_framework.monitoring.otel_setup import get_otel_setup

        self._otel_setup = otel_setup or get_otel_setup()
        self._enable_es_fallback = enable_es_fallback

        # Determine ES metrics logging setting
        if enable_es_metrics_logging is None:
            enable_es_metrics_logging = (
                os.getenv("METRICS_ES_LOGGING_ENABLED", "false").lower() == "true"
            )
        self._enable_es_metrics_logging = enable_es_metrics_logging

        self._tracing: Any = None
        self._metrics: Any = None
        self._es_logging_handler: Any = None
        self._es_fallback_active = False

        # Direct ES metrics logger (for Kibana dashboards)
        self._es_metrics_logger: Any = None
        self._es_metrics_logger_initialized = False

        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize tracing and metrics components."""
        from agent_framework.monitoring.otel_metrics_recorder import OTelMetricsRecorder
        from agent_framework.monitoring.tracing_context import TracingContextManager

        self._tracing = TracingContextManager(self._otel_setup)
        self._metrics = OTelMetricsRecorder(self._otel_setup)

        if not self._otel_setup.is_initialized and self._enable_es_fallback:
            self._activate_es_fallback()

        if self._enable_es_metrics_logging:
            logger.info(
                "Direct ES metrics logging enabled (METRICS_ES_LOGGING_ENABLED=true). "
                "Metrics will be logged to agent-metrics-llm-* and agent-metrics-api-* indices."
            )

    def _activate_es_fallback(self) -> None:
        """Activate Elasticsearch fallback when OTel is unavailable."""
        if self._es_fallback_active:
            return

        logger.warning(
            "OpenTelemetry is not initialized. "
            "Activating Elasticsearch fallback for logging. "
            "Metrics and tracing will be disabled."
        )

        try:
            from agent_framework.monitoring.elasticsearch_logging import (
                ElasticsearchLoggingHandler,
            )

            self._es_logging_handler = ElasticsearchLoggingHandler
            self._es_fallback_active = True
            logger.info("Elasticsearch fallback activated for logging")
        except ImportError:
            logger.warning(
                "ElasticsearchLoggingHandler not available. "
                "Logging fallback disabled."
            )
            self._es_fallback_active = False

    @property
    def is_otel_initialized(self) -> bool:
        """Check if OTel is initialized and available.

        Returns:
            True if OTel is initialized, False otherwise
        """
        return self._otel_setup.is_initialized

    @property
    def is_es_fallback_active(self) -> bool:
        """Check if Elasticsearch fallback is active.

        Returns:
            True if ES fallback is being used, False otherwise
        """
        return self._es_fallback_active

    @property
    def is_es_metrics_logging_enabled(self) -> bool:
        """Check if direct ES metrics logging is enabled.

        Returns:
            True if ES metrics logging is enabled, False otherwise
        """
        return self._enable_es_metrics_logging

    @property
    def tracing(self) -> Any:
        """Get the TracingContextManager instance.

        Returns:
            TracingContextManager for creating spans
        """
        return self._tracing

    @property
    def metrics(self) -> Any:
        """Get the OTelMetricsRecorder instance.

        Returns:
            OTelMetricsRecorder for recording metrics
        """
        return self._metrics

    @asynccontextmanager
    async def api_request(
        self,
        endpoint: str,
        method: str,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> AsyncGenerator[APISpanContext, None]:
        """Track an API request with automatic LLM call aggregation.

        Creates a parent span for the API request and provides context
        for tracking LLM calls made during the request. Automatically
        records API timing metrics when the context exits.

        Args:
            endpoint: HTTP endpoint path (e.g., "/chat")
            method: HTTP method (e.g., "POST")
            session_id: Optional session identifier for correlation
            request_id: Optional request ID (auto-generated if not provided)

        Yields:
            APISpanContext for tracking LLM calls and accessing request info

        Example:
            ```python
            async with manager.api_request(
                endpoint="/chat",
                method="POST",
                session_id="sess-123"
            ) as ctx:
                # Make LLM calls
                response = await llm.chat(messages)
                manager.record_llm_call(metrics)

                # Access aggregated data
                print(f"Total LLM calls: {ctx.llm_call_count}")
            ```
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        with self._tracing.api_request_span(
            endpoint=endpoint,
            method=method,
            request_id=request_id,
            session_id=session_id,
        ) as ctx:
            try:
                yield ctx
            finally:
                self._record_api_timing_from_context(ctx)

    def _record_api_timing_from_context(self, ctx: APISpanContext) -> None:
        """Record API timing metrics from the span context.

        Args:
            ctx: APISpanContext with timing and LLM call data
        """
        from datetime import datetime, timezone

        from agent_framework.monitoring.api_timing_tracker import APITimingData

        timing = APITimingData(
            request_id=ctx.request_id,
            request_start=datetime.now(timezone.utc),
            total_api_duration_ms=ctx.api_duration_ms,
            llm_call_count=ctx.llm_call_count,
            total_llm_duration_ms=ctx.total_llm_duration_ms,
            endpoint=ctx.endpoint,
            method=ctx.method,
            session_id=ctx.session_id,
        )

        # Use self.record_api_timing to include ES logging
        self.record_api_timing(timing)

    def record_llm_call(
        self,
        metrics: LLMMetrics,
        api_context: APISpanContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record LLM call metrics via OTel and optionally to Elasticsearch.

        Records token counts and timing to OTel metrics instruments.
        If an API context is provided, also adds the metrics to the
        context for aggregation.

        When ES metrics logging is enabled (METRICS_ES_LOGGING_ENABLED=true),
        also logs metrics to Elasticsearch for Kibana dashboards.

        Args:
            metrics: LLMMetrics from a completed LLM call
            api_context: Optional APISpanContext to add metrics to
            attributes: Optional additional attributes for metrics

        Example:
            ```python
            async with manager.api_request(...) as ctx:
                # After LLM call completes
                manager.record_llm_call(metrics, api_context=ctx)
            ```
        """
        # Record to OTel
        self._metrics.record_llm_metrics(metrics, attributes)

        # Record to ES if enabled
        if self._enable_es_metrics_logging and self._es_metrics_logger is not None:
            self._es_metrics_logger.log_metrics(metrics)

        if api_context is not None:
            from agent_framework.monitoring.tracing_context import LLMCallMetrics

            llm_call_metrics = LLMCallMetrics(
                model_name=metrics.model_name or "unknown",
                input_tokens=metrics.input_tokens,
                output_tokens=metrics.output_tokens,
                thinking_tokens=metrics.thinking_tokens,
                duration_ms=metrics.duration_ms or 0.0,
                time_to_first_token_ms=metrics.time_to_first_token_ms,
            )
            api_context.add_llm_call(llm_call_metrics)

    def record_api_timing(
        self,
        timing: APITimingData,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record API request timing metrics.

        Records total duration, preprocessing, and postprocessing times
        to OTel metrics instruments.

        When ES metrics logging is enabled (METRICS_ES_LOGGING_ENABLED=true),
        also logs timing to Elasticsearch for Kibana dashboards.

        Args:
            timing: APITimingData from a completed API request
            attributes: Optional additional attributes for metrics

        Example:
            ```python
            timing_data = tracker.finish_request()
            manager.record_api_timing(timing_data)
            ```
        """
        # Record to OTel
        self._metrics.record_api_timing(timing, attributes)

        # Record to ES if enabled
        if self._enable_es_metrics_logging and self._es_metrics_logger is not None:
            self._es_metrics_logger.log_api_timing(timing)

    def get_trace_context(self) -> tuple[str | None, str | None]:
        """Get current trace_id and span_id for correlation.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None)
            if no active span or OTel unavailable
        """
        result: tuple[str | None, str | None] = self._tracing.get_current_trace_context()
        return result

    async def setup_es_logging_handler(
        self,
        logger_instance: logging.Logger | None = None,
        log_level: str = "INFO",
    ) -> Any | None:
        """Set up Elasticsearch logging handler as fallback.

        Creates and attaches an ElasticsearchLoggingHandler to the
        specified logger when OTel is not available.

        Args:
            logger_instance: Logger to add handler to (default: agent_framework)
            log_level: Logging level as string (default: INFO)

        Returns:
            ElasticsearchLoggingHandler if successful, None otherwise
        """
        if self.is_otel_initialized:
            logger.debug("OTel is initialized, ES logging fallback not needed")
            return None

        if not self._es_fallback_active:
            logger.debug("ES fallback not active, cannot setup handler")
            return None

        try:
            from agent_framework.monitoring.elasticsearch_logging import (
                setup_elasticsearch_logging,
            )

            handler = await setup_elasticsearch_logging(
                logger_instance=logger_instance,
                log_level=log_level,
            )
            return handler
        except Exception as e:
            logger.warning(f"Failed to setup ES logging handler: {e}")
            return None

    def shutdown(self) -> None:
        """Shutdown the observability manager.

        Cleans up resources and flushes any pending telemetry.
        """
        if self._otel_setup.is_initialized:
            self._otel_setup.shutdown()

        if self._es_metrics_logger is not None:
            self._es_metrics_logger.close()
            self._es_metrics_logger = None

        logger.debug("ObservabilityManager shutdown complete")

    async def initialize_es_metrics_logger(self) -> bool:
        """Initialize the Elasticsearch metrics logger for Kibana dashboards.

        This method should be called during application startup if
        METRICS_ES_LOGGING_ENABLED=true. It sets up direct logging to
        Elasticsearch indices (agent-metrics-llm-* and agent-metrics-api-*).

        Also creates index templates to ensure proper field mappings
        (keyword types for aggregations instead of text).

        Returns:
            True if initialization was successful, False otherwise

        Example:
            ```python
            manager = get_observability_manager()
            if manager.is_es_metrics_logging_enabled:
                await manager.initialize_es_metrics_logger()
            ```
        """
        if not self._enable_es_metrics_logging:
            logger.debug("ES metrics logging not enabled, skipping initialization")
            return False

        if self._es_metrics_logger_initialized:
            logger.debug("ES metrics logger already initialized")
            return True

        try:
            import warnings

            from agent_framework.session.session_storage import get_shared_elasticsearch_client

            es_client = await get_shared_elasticsearch_client()
            if es_client is None:
                logger.warning(
                    "ES metrics logging enabled but Elasticsearch client not available. "
                    "Metrics will only be sent to OTel."
                )
                return False

            # Create index templates for proper field mappings
            from agent_framework.monitoring.llm_metrics_logger import (
                ensure_metrics_index_templates,
            )

            await ensure_metrics_index_templates(es_client)

            # Import with warning suppression since we're using it intentionally
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                from agent_framework.monitoring.llm_metrics_logger import LLMMetricsLogger

                self._es_metrics_logger = LLMMetricsLogger(es_client=es_client)

            self._es_metrics_logger_initialized = True
            logger.info(
                "ES metrics logger initialized. Metrics will be logged to "
                "agent-metrics-llm-* and agent-metrics-api-* indices for Kibana dashboards."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ES metrics logger: {e}")
            return False

    async def flush_es_metrics(self) -> None:
        """Flush any buffered ES metrics.

        Should be called before application shutdown to ensure all
        metrics are sent to Elasticsearch.
        """
        if self._es_metrics_logger is not None:
            await self._es_metrics_logger.flush()


_default_observability_manager: ObservabilityManager | None = None


def get_observability_manager(
    otel_setup: OTelSetup | None = None,
    enable_es_fallback: bool = True,
    enable_es_metrics_logging: bool | None = None,
) -> ObservabilityManager:
    """Get or create the default ObservabilityManager instance.

    Returns a singleton instance of ObservabilityManager for convenience.
    The manager automatically initializes OTel if not already done.

    Args:
        otel_setup: Optional OTelSetup instance
        enable_es_fallback: Whether to enable ES fallback (default: True)
        enable_es_metrics_logging: Whether to enable direct ES metrics logging
                                  for Kibana dashboards. If None, reads from
                                  METRICS_ES_LOGGING_ENABLED env var.

    Returns:
        ObservabilityManager instance

    Example:
        ```python
        manager = get_observability_manager()

        async with manager.api_request(endpoint="/chat", method="POST") as ctx:
            # Process request
            pass
        ```
    """
    global _default_observability_manager
    if _default_observability_manager is None:
        _default_observability_manager = ObservabilityManager(
            otel_setup=otel_setup,
            enable_es_fallback=enable_es_fallback,
            enable_es_metrics_logging=enable_es_metrics_logging,
        )
    return _default_observability_manager


def reset_observability_manager() -> None:
    """Reset the default ObservabilityManager instance.

    Useful for testing or reconfiguration. Shuts down the existing
    manager if initialized.
    """
    global _default_observability_manager
    if _default_observability_manager is not None:
        _default_observability_manager.shutdown()
        _default_observability_manager = None
