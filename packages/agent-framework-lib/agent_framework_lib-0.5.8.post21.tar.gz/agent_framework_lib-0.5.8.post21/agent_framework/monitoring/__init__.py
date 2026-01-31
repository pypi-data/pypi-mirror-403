"""Monitoring module for performance, progress tracking, and error handling.

This module provides observability components for the Agent Framework:

New (Recommended):
    - ObservabilityManager: Unified facade for tracing, metrics, and logging
    - OTelSetup: OpenTelemetry initialization and configuration
    - TracingContextManager: API-first trace hierarchy management
    - OTelMetricsRecorder: OpenTelemetry metrics recording
    - OTelLoggingHandler: OpenTelemetry log handler with trace correlation

Deprecated (for backward compatibility):
    - LLMMetricsLogger: Use ObservabilityManager.record_llm_call() instead
    - setup_llm_metrics_logger: Use get_observability_manager() instead

Migration Guide:
    Old way (deprecated)::

        from agent_framework.monitoring import LLMMetricsLogger
        metrics_logger = LLMMetricsLogger(es_client=es_client)
        metrics_logger.log_metrics(llm_metrics)

    New way (recommended)::

        from agent_framework.monitoring import get_observability_manager
        manager = get_observability_manager()
        manager.record_llm_call(llm_metrics)
"""

from agent_framework.monitoring.api_timing_tracker import APITimingData, APITimingTracker
from agent_framework.monitoring.llm_metrics import LLMMetrics, SessionLLMStats
from agent_framework.monitoring.llm_metrics_collector import LLMMetricsCollector
from agent_framework.monitoring.llm_metrics_logger import (
    LLMMetricsLogger,  # Deprecated: use ObservabilityManager instead
    setup_llm_metrics_logger,  # Deprecated: use get_observability_manager instead
)
from agent_framework.monitoring.metrics_config import (
    MetricsConfig,
    get_metrics_config,
    reset_metrics_config,
)
from agent_framework.monitoring.otel_instrumentor import (
    OTELInstrumentor,
    get_meter,
    get_otel_instrumentor,
    get_tracer,
)
from agent_framework.monitoring.otel_setup import (
    OTelConfig,
    OTelSetup,
    get_otel_setup,
    reset_otel_setup,
)
from agent_framework.monitoring.timing_tracker import TimingData, TimingTracker
from agent_framework.monitoring.token_counter import TokenCount, TokenCounter
from agent_framework.monitoring.tracing_context import (
    APISpanContext,
    LLMCallMetrics,
    LLMSpanContext,
    TracingContextManager,
    get_tracing_context_manager,
    reset_tracing_context_manager,
)
from agent_framework.monitoring.otel_metrics_recorder import (
    OTelMetricsRecorder,
    get_otel_metrics_recorder,
    reset_otel_metrics_recorder,
)
from agent_framework.monitoring.otel_logging_handler import (
    OTelLoggingHandler,
    get_otel_logging_handler,
    setup_otel_logging,
)
from agent_framework.monitoring.observability_manager import (
    ObservabilityManager,
    get_observability_manager,
    reset_observability_manager,
)

__all__ = [
    # Module references (for submodule access)
    "performance_monitor",
    "progress_tracker",
    "resource_manager",
    "error_handling",
    "error_logging",
    "elasticsearch_logging",
    "elasticsearch_circuit_breaker",
    # ===========================================
    # NEW: OpenTelemetry Observability (Recommended)
    # ===========================================
    # ObservabilityManager Facade (primary entry point)
    "ObservabilityManager",
    "get_observability_manager",
    "reset_observability_manager",
    # OTel Setup (unified initialization)
    "OTelConfig",
    "OTelSetup",
    "get_otel_setup",
    "reset_otel_setup",
    # Tracing Context (API-first hierarchy)
    "TracingContextManager",
    "APISpanContext",
    "LLMSpanContext",
    "LLMCallMetrics",
    "get_tracing_context_manager",
    "reset_tracing_context_manager",
    # OTel Metrics Recorder
    "OTelMetricsRecorder",
    "get_otel_metrics_recorder",
    "reset_otel_metrics_recorder",
    # OTel Logging Handler
    "OTelLoggingHandler",
    "get_otel_logging_handler",
    "setup_otel_logging",
    # OpenTelemetry Instrumentor
    "OTELInstrumentor",
    "get_tracer",
    "get_meter",
    "get_otel_instrumentor",
    # ===========================================
    # Metrics Configuration
    # ===========================================
    "MetricsConfig",
    "get_metrics_config",
    "reset_metrics_config",
    # ===========================================
    # Data Models (still current)
    # ===========================================
    "LLMMetrics",
    "SessionLLMStats",
    "LLMMetricsCollector",
    "TokenCounter",
    "TokenCount",
    "TimingTracker",
    "TimingData",
    "APITimingTracker",
    "APITimingData",
    # ===========================================
    # DEPRECATED: Legacy exports (for backward compatibility)
    # Use ObservabilityManager instead
    # ===========================================
    "LLMMetricsLogger",  # Deprecated: use ObservabilityManager.record_llm_call()
    "setup_llm_metrics_logger",  # Deprecated: use get_observability_manager()
]
