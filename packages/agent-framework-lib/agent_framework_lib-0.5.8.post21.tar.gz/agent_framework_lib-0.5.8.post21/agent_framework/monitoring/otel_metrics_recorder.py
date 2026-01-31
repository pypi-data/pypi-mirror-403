"""OpenTelemetry Metrics Recorder.

Records LLM and API timing metrics using OpenTelemetry instruments.
Supports counters for token usage and histograms for timing measurements.

The recorder integrates with OTelSetup to use the configured MeterProvider
and handles graceful degradation when OTel is not available.

Example:
    ```python
    from agent_framework.monitoring.otel_setup import get_otel_setup
    from agent_framework.monitoring.otel_metrics_recorder import OTelMetricsRecorder

    setup = get_otel_setup()
    setup.initialize()

    recorder = OTelMetricsRecorder(setup)

    # Record LLM metrics
    recorder.record_llm_metrics(llm_metrics)

    # Record API timing
    recorder.record_api_timing(api_timing_data)
    ```
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from agent_framework.monitoring.api_timing_tracker import APITimingData
    from agent_framework.monitoring.llm_metrics import LLMMetrics
    from agent_framework.monitoring.otel_setup import OTelSetup

logger = logging.getLogger(__name__)


class OTelMetricsRecorder:
    """Records metrics using OpenTelemetry instruments.

    Provides counters for token usage and histograms for timing measurements.
    All metrics include resource attributes (service.name, service.version,
    deployment.environment) from the OTelSetup configuration.

    Attributes:
        METRIC_LLM_INPUT_TOKENS: Counter name for input tokens
        METRIC_LLM_OUTPUT_TOKENS: Counter name for output tokens
        METRIC_LLM_DURATION: Histogram name for LLM request duration
        METRIC_LLM_TTFT: Histogram name for time to first token
        METRIC_HTTP_DURATION: Histogram name for HTTP request duration
        METRIC_HTTP_PREPROCESSING: Histogram name for preprocessing duration
        METRIC_HTTP_POSTPROCESSING: Histogram name for postprocessing duration
    """

    METRIC_LLM_INPUT_TOKENS = "llm.tokens.input"
    METRIC_LLM_OUTPUT_TOKENS = "llm.tokens.output"
    METRIC_LLM_THINKING_TOKENS = "llm.tokens.thinking"
    METRIC_LLM_DURATION = "llm.request.duration"
    METRIC_LLM_TTFT = "llm.request.time_to_first_token"

    METRIC_HTTP_DURATION = "http.request.duration"
    METRIC_HTTP_PREPROCESSING = "http.request.preprocessing_duration"
    METRIC_HTTP_POSTPROCESSING = "http.request.postprocessing_duration"

    LLM_DURATION_BUCKETS = (
        100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 150000, 200000, 300000
    )

    def __init__(self, otel_setup: OTelSetup) -> None:
        """Initialize the metrics recorder.

        Args:
            otel_setup: OTelSetup instance for getting the meter
        """
        self._setup = otel_setup
        self._meter = otel_setup.get_meter("agent_framework.metrics")
        self._initialized = False

        self._input_tokens_counter: Any = None
        self._output_tokens_counter: Any = None
        self._thinking_tokens_counter: Any = None
        self._llm_duration_histogram: Any = None
        self._llm_ttft_histogram: Any = None
        self._http_duration_histogram: Any = None
        self._http_preprocessing_histogram: Any = None
        self._http_postprocessing_histogram: Any = None

        self._setup_instruments()

    def _setup_instruments(self) -> None:
        """Create all metric instruments.

        Sets up counters for token usage and histograms for timing.
        Handles graceful degradation if OTel is not available.
        """
        if not self._meter:
            logger.warning("No meter available, metrics recording will be disabled")
            return

        try:
            self._input_tokens_counter = self._meter.create_counter(
                name=self.METRIC_LLM_INPUT_TOKENS,
                description="Input tokens sent to LLM",
                unit="tokens",
            )

            self._output_tokens_counter = self._meter.create_counter(
                name=self.METRIC_LLM_OUTPUT_TOKENS,
                description="Output tokens received from LLM",
                unit="tokens",
            )

            self._thinking_tokens_counter = self._meter.create_counter(
                name=self.METRIC_LLM_THINKING_TOKENS,
                description="Thinking/reasoning tokens from LLM",
                unit="tokens",
            )

            self._llm_duration_histogram = self._meter.create_histogram(
                name=self.METRIC_LLM_DURATION,
                description="LLM request duration",
                unit="ms",
            )

            self._llm_ttft_histogram = self._meter.create_histogram(
                name=self.METRIC_LLM_TTFT,
                description="Time to first token from LLM",
                unit="ms",
            )

            self._http_duration_histogram = self._meter.create_histogram(
                name=self.METRIC_HTTP_DURATION,
                description="Total HTTP request duration",
                unit="ms",
            )

            self._http_preprocessing_histogram = self._meter.create_histogram(
                name=self.METRIC_HTTP_PREPROCESSING,
                description="HTTP request preprocessing duration before LLM",
                unit="ms",
            )

            self._http_postprocessing_histogram = self._meter.create_histogram(
                name=self.METRIC_HTTP_POSTPROCESSING,
                description="HTTP request postprocessing duration after LLM",
                unit="ms",
            )

            self._initialized = True
            logger.debug("OTel metrics instruments initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize OTel metrics instruments: {e}")
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if metrics instruments are initialized.

        Returns:
            True if instruments are ready for recording
        """
        return self._initialized

    def record_llm_metrics(
        self,
        metrics: LLMMetrics,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record LLM call metrics.

        Records token counts to counters and duration to histogram.
        Includes model name and session ID as attributes.

        Args:
            metrics: LLMMetrics from a completed LLM call
            attributes: Optional additional attributes to include

        Example:
            ```python
            recorder.record_llm_metrics(
                metrics,
                attributes={"custom_tag": "value"}
            )
            ```
        """
        if not self._initialized:
            logger.debug("Metrics recorder not initialized, skipping LLM metrics")
            return

        try:
            attrs = {
                "model": metrics.model_name or "unknown",
                "session_id": metrics.session_id or "unknown",
            }
            if attributes:
                attrs.update(attributes)

            if self._input_tokens_counter and metrics.input_tokens > 0:
                self._input_tokens_counter.add(metrics.input_tokens, attrs)

            if self._output_tokens_counter and metrics.output_tokens > 0:
                self._output_tokens_counter.add(metrics.output_tokens, attrs)

            if self._thinking_tokens_counter and metrics.thinking_tokens > 0:
                self._thinking_tokens_counter.add(metrics.thinking_tokens, attrs)

            if self._llm_duration_histogram and metrics.duration_ms is not None:
                self._llm_duration_histogram.record(metrics.duration_ms, attrs)

            if self._llm_ttft_histogram and metrics.time_to_first_token_ms is not None:
                self._llm_ttft_histogram.record(metrics.time_to_first_token_ms, attrs)

            logger.debug(
                f"Recorded LLM metrics: model={metrics.model_name}, "
                f"input_tokens={metrics.input_tokens}, "
                f"thinking_tokens={metrics.thinking_tokens}, "
                f"output_tokens={metrics.output_tokens}, "
                f"duration_ms={metrics.duration_ms}"
            )

        except Exception as e:
            logger.warning(f"Failed to record LLM metrics: {e}")

    def record_api_timing(
        self,
        timing: APITimingData,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record API request timing metrics.

        Records total duration, preprocessing, and postprocessing times
        to histograms. Includes endpoint and method as attributes.

        Args:
            timing: APITimingData from a completed API request
            attributes: Optional additional attributes to include

        Example:
            ```python
            recorder.record_api_timing(
                timing_data,
                attributes={"custom_tag": "value"}
            )
            ```
        """
        if not self._initialized:
            logger.debug("Metrics recorder not initialized, skipping API timing")
            return

        try:
            attrs = {
                "endpoint": timing.endpoint or "unknown",
                "method": timing.method or "unknown",
            }
            if timing.session_id:
                attrs["session_id"] = timing.session_id
            if attributes:
                attrs.update(attributes)

            if self._http_duration_histogram and timing.total_api_duration_ms is not None:
                self._http_duration_histogram.record(timing.total_api_duration_ms, attrs)

            if self._http_preprocessing_histogram and timing.preprocessing_duration_ms is not None:
                self._http_preprocessing_histogram.record(timing.preprocessing_duration_ms, attrs)

            if (
                self._http_postprocessing_histogram
                and timing.postprocessing_duration_ms is not None
            ):
                self._http_postprocessing_histogram.record(timing.postprocessing_duration_ms, attrs)

            logger.debug(
                f"Recorded API timing: endpoint={timing.endpoint}, "
                f"method={timing.method}, "
                f"total_ms={timing.total_api_duration_ms}"
            )

        except Exception as e:
            logger.warning(f"Failed to record API timing: {e}")


_default_metrics_recorder: OTelMetricsRecorder | None = None


def get_otel_metrics_recorder(
    otel_setup: OTelSetup | None = None,
) -> OTelMetricsRecorder:
    """Get or create the default OTel metrics recorder.

    Returns a singleton instance of OTelMetricsRecorder. If no OTelSetup
    is provided, uses the default from get_otel_setup().

    Args:
        otel_setup: Optional OTelSetup instance

    Returns:
        OTelMetricsRecorder instance
    """
    global _default_metrics_recorder
    if _default_metrics_recorder is None:
        if otel_setup is None:
            from agent_framework.monitoring.otel_setup import get_otel_setup

            otel_setup = get_otel_setup()
        _default_metrics_recorder = OTelMetricsRecorder(otel_setup)
    return _default_metrics_recorder


def reset_otel_metrics_recorder() -> None:
    """Reset the default OTel metrics recorder.

    Useful for testing or reconfiguration.
    """
    global _default_metrics_recorder
    _default_metrics_recorder = None
