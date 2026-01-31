"""LLM Metrics Logger for Elasticsearch.

.. deprecated::
    This module is deprecated. Use :class:`ObservabilityManager` from
    :mod:`agent_framework.monitoring.observability_manager` instead.
    Metrics now flow through OpenTelemetry Collector to Elasticsearch
    in OTel data model format.

    Migration example::

        # Old way (deprecated)
        from agent_framework.monitoring.llm_metrics_logger import LLMMetricsLogger
        metrics_logger = LLMMetricsLogger(es_client=es_client)
        metrics_logger.log_metrics(llm_metrics)

        # New way (recommended)
        from agent_framework.monitoring import get_observability_manager
        manager = get_observability_manager()
        manager.record_llm_call(llm_metrics)

This module provides a dedicated logger for LLM and API metrics that sends them to
Elasticsearch with batching, time-based flushing, and automatic fallback
to standard logging.

Key Features:
- Circular buffer with configurable max size
- Batch processing with configurable batch size
- Time-based flushing with configurable interval
- Automatic fallback to standard logging on ES failure
- Daily index rotation via {date} pattern
- Circuit breaker integration for resilience
- Non-blocking async operations
- Unified configuration via MetricsConfig

Environment Variables:
- METRICS_ENABLED: Master switch for all metrics (default: true)
- METRICS_INDEX_PREFIX: Base prefix for indices (default: agent-metrics)
- METRICS_BATCH_SIZE: Batch size for ES operations (default: 50)
- METRICS_FLUSH_INTERVAL: Flush interval in seconds (default: 5.0)

Example:
    ```python
    from agent_framework.monitoring.llm_metrics_logger import LLMMetricsLogger
    from agent_framework.session.session_storage import get_shared_elasticsearch_client

    # Get shared ES client
    es_client = await get_shared_elasticsearch_client()

    # Create logger (uses unified MetricsConfig)
    metrics_logger = LLMMetricsLogger(es_client=es_client)

    # Log metrics
    metrics_logger.log_metrics(llm_metrics)
    metrics_logger.log_api_timing(api_timing_data)

    # Flush on shutdown
    await metrics_logger.flush()
    metrics_logger.close()
    ```
"""

import asyncio
import logging
import warnings
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import TYPE_CHECKING, Any, Optional

from agent_framework.monitoring.llm_metrics import LLMMetrics
from agent_framework.monitoring.api_timing_tracker import APITimingData
from agent_framework.monitoring.metrics_config import MetricsConfig, get_metrics_config


if TYPE_CHECKING:
    from agent_framework.monitoring.elasticsearch_circuit_breaker import (
        ElasticsearchCircuitBreaker,
    )


logger = logging.getLogger(__name__)


def _get_circuit_breaker() -> "ElasticsearchCircuitBreaker":
    """Get the circuit breaker instance lazily to avoid circular imports."""
    from agent_framework.monitoring.elasticsearch_circuit_breaker import (
        get_elasticsearch_circuit_breaker,
    )

    return get_elasticsearch_circuit_breaker()


class LLMMetricsLogger:
    """Log LLM and API metrics to Elasticsearch with batching and fallback.

    This logger accumulates metrics in circular buffers and sends them
    to Elasticsearch in batches. It supports time-based flushing and automatic
    fallback to standard logging when Elasticsearch is unavailable.

    The logger is designed to be non-blocking - log_metrics() returns immediately
    and the actual ES indexing happens asynchronously.

    Attributes:
        es_client: Elasticsearch client instance
        config: MetricsConfig instance with all settings
        llm_index_pattern: Index pattern for LLM metrics
        api_index_pattern: Index pattern for API metrics

    Example:
        ```python
        # Create logger with unified config
        metrics_logger = LLMMetricsLogger(es_client=es_client)

        # Or with custom config
        config = MetricsConfig(
            enabled=True,
            index_prefix="my-app-metrics",
            batch_size=100,
            flush_interval=10.0
        )
        metrics_logger = LLMMetricsLogger(es_client=es_client, config=config)

        # Log metrics (non-blocking)
        metrics_logger.log_metrics(llm_metrics)
        metrics_logger.log_api_timing(api_timing)

        # Force flush before shutdown
        await metrics_logger.flush()
        ```
    """

    def __init__(
        self,
        es_client: Any | None = None,
        config: Optional[MetricsConfig] = None,
    ):
        """Initialize the LLM metrics logger.

        .. deprecated::
            LLMMetricsLogger is deprecated. Use ObservabilityManager instead.
            See module docstring for migration guide.

        Args:
            es_client: Elasticsearch client instance (async client)
            config: MetricsConfig instance (if None, uses global config from env)
        """
        warnings.warn(
            "LLMMetricsLogger is deprecated and will be removed in a future version. "
            "Use ObservabilityManager from agent_framework.monitoring.observability_manager instead. "
            "Metrics now flow through OpenTelemetry Collector to Elasticsearch in OTel data model format. "
            "Migration: Replace LLMMetricsLogger.log_metrics() with ObservabilityManager.record_llm_call()",
            DeprecationWarning,
            stacklevel=2,
        )

        self.es_client = es_client

        # Use provided config or get from environment
        if config is None:
            config = get_metrics_config()
        self._config = config

        self._llm_index_pattern = config.llm_index_pattern
        self._api_index_pattern = config.api_index_pattern
        self.batch_size = config.batch_size
        self.flush_interval = config.flush_interval
        self.max_buffer_size = config.max_buffer_size

        # Circular buffer for LLM metrics documents
        self._buffer: deque[dict[str, Any]] = deque(maxlen=self.max_buffer_size)
        self._buffer_lock = Lock()

        # Separate buffer for API timing metrics
        self._api_timing_buffer: deque[dict[str, Any]] = deque(maxlen=self.max_buffer_size)

        # Flush timing
        self._last_flush = datetime.now(timezone.utc)
        self._closed = False

        # Track pending flush tasks
        self._pending_flush: asyncio.Task | None = None

        logger.debug(
            f"Initialized LLMMetricsLogger: "
            f"llm_index={self._llm_index_pattern}, api_index={self._api_index_pattern}, "
            f"batch_size={self.batch_size}, flush_interval={self.flush_interval}s"
        )

    @property
    def index_pattern(self) -> str:
        """Get the LLM index pattern."""
        return self._llm_index_pattern

    @property
    def config(self) -> MetricsConfig:
        """Get the metrics configuration."""
        return self._config

    def _get_index_name(self) -> str:
        """Get the LLM index name with date substitution.

        Returns:
            Index name with {date} replaced by current date in YYYY-MM-DD format

        Example:
            >>> logger = LLMMetricsLogger()
            >>> logger._get_index_name()
            'agent-metrics-llm-2024-01-15'
        """
        if "{date}" in self._llm_index_pattern:
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return self._llm_index_pattern.replace("{date}", current_date)
        return self._llm_index_pattern

    def _get_api_timing_index_name(self) -> str:
        """Get the API timing index name with date substitution."""
        if "{date}" in self._api_index_pattern:
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            return self._api_index_pattern.replace("{date}", current_date)
        return self._api_index_pattern

    def log_metrics(self, metrics: LLMMetrics) -> None:
        """Add metrics to buffer for async logging.

        This method is non-blocking and returns immediately. The metrics are
        added to an internal buffer and will be sent to Elasticsearch
        asynchronously when the batch size is reached or the flush interval
        elapses.

        If the logger is closed or the buffer is full (circular buffer),
        oldest metrics will be dropped.

        Args:
            metrics: LLMMetrics instance to log

        Example:
            ```python
            metrics = LLMMetrics(
                input_tokens=100,
                output_tokens=200,
                start_time=datetime.now(timezone.utc),
                model_name="gpt-5-mini"
            )
            metrics_logger.log_metrics(metrics)
            ```
        """
        if self._closed:
            logger.debug("LLMMetricsLogger is closed, ignoring metrics")
            return

        # Convert metrics to ES document
        doc = metrics.to_elasticsearch_doc()

        with self._buffer_lock:
            self._buffer.append(doc)
            buffer_size = len(self._buffer)

        # Check if we should flush
        should_flush = False
        if buffer_size >= self.batch_size:
            should_flush = True
        else:
            time_since_flush = (datetime.now(timezone.utc) - self._last_flush).total_seconds()
            if time_since_flush >= self.flush_interval:
                should_flush = True

        if should_flush:
            self._schedule_flush()

    def log_api_timing(self, timing_data: APITimingData) -> None:
        """Add API timing data to buffer for async logging.

        This method is non-blocking and returns immediately. The timing data
        is added to a separate buffer and will be sent to Elasticsearch
        asynchronously.

        Args:
            timing_data: APITimingData instance to log

        Example:
            ```python
            timing_data = tracker.finish_request()
            metrics_logger.log_api_timing(timing_data)
            ```
        """
        if self._closed:
            logger.debug("LLMMetricsLogger is closed, ignoring API timing")
            return

        doc = timing_data.to_elasticsearch_doc()

        with self._buffer_lock:
            self._api_timing_buffer.append(doc)
            buffer_size = len(self._api_timing_buffer)

        if buffer_size >= self.batch_size:
            self._schedule_flush()

    def _schedule_flush(self) -> None:
        """Schedule an async flush operation.

        This method attempts to schedule a flush task on the current event loop.
        If no event loop is running, the flush will be deferred until the next
        call or explicit flush() call.
        """
        try:
            loop = asyncio.get_running_loop()
            # Only schedule if no pending flush
            if self._pending_flush is None or self._pending_flush.done():
                self._pending_flush = loop.create_task(self._flush_buffer())
        except RuntimeError:
            # No running event loop - flush will happen on next opportunity
            logger.debug("No running event loop, deferring flush")

    async def _flush_buffer(self) -> None:
        """Flush buffered metrics to Elasticsearch using bulk API.

        This method handles the actual sending of metrics to Elasticsearch.
        It uses the circuit breaker pattern to avoid overwhelming a failing
        ES cluster and falls back to standard logging when ES is unavailable.
        """
        if self._closed:
            return

        # Get documents from both buffers
        with self._buffer_lock:
            llm_documents = list(self._buffer) if self._buffer else []
            api_documents = list(self._api_timing_buffer) if self._api_timing_buffer else []
            self._buffer.clear()
            self._api_timing_buffer.clear()

        if not llm_documents and not api_documents:
            return

        # Update last flush time
        self._last_flush = datetime.now(timezone.utc)

        # Check circuit breaker before attempting ES operation
        circuit_breaker = _get_circuit_breaker()

        # Try to send to Elasticsearch
        if self.es_client and circuit_breaker.is_available():
            try:
                # Prepare bulk operations for LLM metrics
                operations = []
                if llm_documents:
                    index_name = self._get_index_name()
                    for doc in llm_documents:
                        operations.append({"index": {"_index": index_name}})
                        operations.append(doc)

                # Prepare bulk operations for API timing metrics
                if api_documents:
                    api_index_name = self._get_api_timing_index_name()
                    for doc in api_documents:
                        operations.append({"index": {"_index": api_index_name}})
                        operations.append(doc)

                if operations:
                    # Send bulk request
                    response = await self.es_client.bulk(operations=operations)

                    # Record success with circuit breaker
                    circuit_breaker.record_success()

                    # Check for errors
                    if response.get("errors"):
                        error_count = sum(
                            1 for item in response["items"] if "error" in item.get("index", {})
                        )
                        logger.warning(
                            f"Elasticsearch bulk operation had {error_count} errors for metrics"
                        )
                        self._log_to_fallback(llm_documents)
                        self._log_api_timing_to_fallback(api_documents)
                    else:
                        logger.debug(
                            f"Successfully sent {len(llm_documents)} LLM metrics and "
                            f"{len(api_documents)} API timing metrics to Elasticsearch"
                        )

            except Exception as e:
                logger.error(f"Failed to send metrics to Elasticsearch: {e}")

                # Record failure with circuit breaker
                circuit_breaker.record_failure()

                # Fallback to standard logging
                logger.warning(
                    f"Activating fallback logging for metrics due to ES failure: {e} "
                    f"(circuit_breaker_state={circuit_breaker.get_state().value})"
                )
                self._log_to_fallback(llm_documents)
                self._log_api_timing_to_fallback(api_documents)
        else:
            # Circuit breaker is open or no ES client, use fallback immediately
            if self.es_client and not circuit_breaker.is_available():
                logger.warning(
                    f"Circuit breaker is open, using fallback logging for metrics "
                    f"(state={circuit_breaker.get_state().value})"
                )
            self._log_to_fallback(llm_documents)
            self._log_api_timing_to_fallback(api_documents)

    def _log_to_fallback(self, documents: list[dict[str, Any]]) -> None:
        """Log metrics to standard Python logging as fallback.

        This method is called when Elasticsearch is unavailable. It logs
        the metrics using the standard logging module so they are not lost.

        Args:
            documents: List of metric documents to log
        """
        for doc in documents:
            # Create a structured log message
            log_data = {
                "type": "llm_metrics",
                "model": doc.get("model_name"),
                "session_id": doc.get("session_id"),
                "total_tokens": doc.get("total_tokens"),
                "input_tokens": doc.get("input_tokens"),
                "output_tokens": doc.get("output_tokens"),
                "duration_ms": doc.get("duration_ms"),
                "tokens_per_second": doc.get("tokens_per_second"),
            }
            logger.info(f"LLM_METRICS: {log_data}")

    def _log_api_timing_to_fallback(self, documents: list[dict[str, Any]]) -> None:
        """Log API timing to standard Python logging as fallback.

        Args:
            documents: List of API timing documents to log
        """
        for doc in documents:
            log_data = {
                "type": "api_timing",
                "request_id": doc.get("request_id"),
                "endpoint": doc.get("endpoint"),
                "method": doc.get("method"),
                "total_api_duration_ms": doc.get("total_api_duration_ms"),
                "preprocessing_duration_ms": doc.get("preprocessing_duration_ms"),
                "llm_duration_ms": doc.get("llm_duration_ms"),
                "postprocessing_duration_ms": doc.get("postprocessing_duration_ms"),
                "llm_percentage": doc.get("llm_percentage"),
            }
            logger.info(f"API_TIMING: {log_data}")

    async def flush(self) -> None:
        """Force flush all buffered metrics.

        This method should be called before shutdown to ensure all
        buffered metrics are sent to Elasticsearch.

        Example:
            ```python
            # Before application shutdown
            await metrics_logger.flush()
            metrics_logger.close()
            ```
        """
        await self._flush_buffer()

    def close(self) -> None:
        """Close the logger.

        Marks the logger as closed. After calling close(), no new metrics
        will be accepted. Call flush() before close() to ensure all
        buffered metrics are sent.

        Example:
            ```python
            await metrics_logger.flush()
            metrics_logger.close()
            ```
        """
        self._closed = True
        logger.debug("LLMMetricsLogger closed")


async def setup_llm_metrics_logger(
    es_client: Any | None = None,
    config: Optional[MetricsConfig] = None,
) -> LLMMetricsLogger | None:
    """Set up an LLM metrics logger with the shared Elasticsearch client.

    .. deprecated::
        This function is deprecated. Use get_observability_manager() instead.
        See module docstring for migration guide.

    This is a convenience function that creates an LLMMetricsLogger
    using the shared Elasticsearch client from the framework.

    Args:
        es_client: Elasticsearch client (if None, will use shared client)
        config: MetricsConfig instance (if None, uses global config from env)

    Returns:
        LLMMetricsLogger instance if ES is available, None otherwise

    Example:
        ```python
        from agent_framework.monitoring.llm_metrics_logger import setup_llm_metrics_logger

        # Set up logger with defaults
        metrics_logger = await setup_llm_metrics_logger()

        if metrics_logger:
            metrics_logger.log_metrics(metrics)
        ```
    """
    warnings.warn(
        "setup_llm_metrics_logger is deprecated and will be removed in a future version. "
        "Use get_observability_manager() from agent_framework.monitoring instead. "
        "Example: manager = get_observability_manager(); manager.record_llm_call(metrics)",
        DeprecationWarning,
        stacklevel=2,
    )

    try:
        # Get ES client if not provided
        if es_client is None:
            from agent_framework.session.session_storage import get_shared_elasticsearch_client

            es_client = await get_shared_elasticsearch_client()

        # Check if ES is available
        if es_client is None:
            logger.info("LLM metrics logging not enabled (Elasticsearch client not available)")
            return None

        # Create logger
        metrics_logger = LLMMetricsLogger(es_client=es_client, config=config)

        logger.info("LLM metrics logger configured successfully")
        return metrics_logger

    except Exception as e:
        logger.error(f"Failed to setup LLM metrics logger: {e}")
        return None


async def ensure_metrics_index_templates(es_client: Any | None = None) -> bool:
    """Ensure index templates exist for metrics indices.

    Creates index templates that define proper mappings for LLM and API metrics.
    This ensures that string fields like model_name and endpoint are indexed
    as 'keyword' type for aggregations, not 'text'.

    Should be called once at application startup before logging metrics.

    Args:
        es_client: Elasticsearch client (if None, will use shared client)

    Returns:
        True if templates were created/verified successfully, False otherwise

    Example:
        ```python
        from agent_framework.monitoring.llm_metrics_logger import ensure_metrics_index_templates

        # At application startup
        await ensure_metrics_index_templates()
        ```
    """
    try:
        if es_client is None:
            from agent_framework.session.session_storage import get_shared_elasticsearch_client

            es_client = await get_shared_elasticsearch_client()

        if es_client is None:
            logger.warning("Cannot create index templates: Elasticsearch client not available")
            return False

        config = get_metrics_config()

        # LLM metrics index template
        llm_template = {
            "index_patterns": [f"{config.index_prefix}-llm-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "input_tokens": {"type": "integer"},
                        "output_tokens": {"type": "integer"},
                        "thinking_tokens": {"type": "integer"},
                        "total_tokens": {"type": "integer"},
                        "duration_ms": {"type": "float"},
                        "time_to_first_token_ms": {"type": "float"},
                        "tokens_per_second": {"type": "float"},
                        "model_name": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "agent_id": {"type": "keyword"},
                        "api_request_id": {"type": "keyword"},
                        "tool_call_count": {"type": "integer"},
                        "tool_call_duration_ms": {"type": "float"},
                    }
                },
            },
        }

        # API metrics index template
        api_template = {
            "index_patterns": [f"{config.index_prefix}-api-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "request_id": {"type": "keyword"},
                        "endpoint": {"type": "keyword"},
                        "method": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "agent_id": {"type": "keyword"},
                        "total_api_duration_ms": {"type": "float"},
                        "preprocessing_duration_ms": {"type": "float"},
                        "llm_duration_ms": {"type": "float"},
                        "total_llm_duration_ms": {"type": "float"},
                        "postprocessing_duration_ms": {"type": "float"},
                        "overhead_ms": {"type": "float"},
                        "llm_percentage": {"type": "float"},
                        "llm_call_count": {"type": "integer"},
                        "time_to_first_chunk_ms": {"type": "float"},
                        "is_streaming": {"type": "boolean"},
                        "status_code": {"type": "integer"},
                    }
                },
            },
        }

        # Create LLM metrics template
        await es_client.indices.put_index_template(
            name=f"{config.index_prefix}-llm-template",
            body=llm_template,
        )
        logger.info(f"Created/updated index template: {config.index_prefix}-llm-template")

        # Create API metrics template
        await es_client.indices.put_index_template(
            name=f"{config.index_prefix}-api-template",
            body=api_template,
        )
        logger.info(f"Created/updated index template: {config.index_prefix}-api-template")

        return True

    except Exception as e:
        logger.error(f"Failed to create metrics index templates: {e}")
        return False
