"""OpenTelemetry Unified Setup Module.

Provides a single initialization point for all OpenTelemetry components:
- TracerProvider for distributed tracing
- MeterProvider for metrics
- LoggerProvider for structured logging

The module supports graceful degradation when OTel packages are not installed
or not configured, making all operations no-ops without raising errors.

Environment Variables:
    OTEL_ENABLED: Master switch for OTel (default: true)
    OTEL_SERVICE_NAME: Service name for all signals (default: agent_framework)
    OTEL_SERVICE_VERSION: Service version (default: 1.0.0)
    OTEL_ENVIRONMENT: Deployment environment (default: development)
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint
    OTEL_EXPORTER_OTLP_PROTOCOL: Protocol: grpc or http (default: grpc)
    OTEL_METRICS_EXPORTER: Metrics exporter: otlp, prometheus, none (default: otlp)
    OTEL_LOGS_EXPORTER: Logs exporter: otlp, none (default: otlp)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class OTelConfig:
    """Configuration for OpenTelemetry setup.

    This dataclass holds all configuration options for initializing
    OpenTelemetry providers. It can be created manually or loaded
    from environment variables using the from_env() class method.

    Attributes:
        enabled: Master switch for OTel (default: True)
        service_name: Service name for all signals (default: agent_framework)
        service_version: Service version (default: 1.0.0)
        environment: Deployment environment (default: development)
        otlp_endpoint: OTLP collector endpoint (optional)
        otlp_protocol: Protocol: grpc or http (default: grpc)
        metrics_exporter: Metrics exporter type: otlp, prometheus, none (default: otlp)
        logs_exporter: Logs exporter type: otlp, none (default: otlp)

    Example:
        ```python
        # Create from environment variables
        config = OTelConfig.from_env()

        # Create manually
        config = OTelConfig(
            enabled=True,
            service_name="my-agent",
            otlp_endpoint="http://localhost:4317",
        )
        ```
    """

    enabled: bool = True
    service_name: str = "agent_framework"
    service_version: str = "1.0.0"
    environment: str = "development"
    otlp_endpoint: str | None = None
    otlp_protocol: str = "grpc"
    metrics_exporter: str = "otlp"
    logs_exporter: str = "otlp"

    @classmethod
    def from_env(cls) -> OTelConfig:
        """Create configuration from environment variables.

        Reads all OTel configuration from environment variables with
        sensible defaults. This is the recommended way to configure
        OTel in production environments.

        Returns:
            OTelConfig instance populated from environment

        Environment Variables:
            OTEL_ENABLED: "true" or "false" (default: "true")
            OTEL_SERVICE_NAME: Service name (default: "agent_framework")
            OTEL_SERVICE_VERSION: Version string (default: "1.0.0")
            OTEL_ENVIRONMENT: Environment name (default: "development")
            OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL
            OTEL_EXPORTER_OTLP_PROTOCOL: "grpc" or "http" (default: "grpc")
            OTEL_METRICS_EXPORTER: "otlp", "prometheus", or "none" (default: "otlp")
            OTEL_LOGS_EXPORTER: "otlp" or "none" (default: "otlp")

        Example:
            ```python
            # Set environment variables
            os.environ["OTEL_SERVICE_NAME"] = "my-agent"
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://collector:4317"

            # Load configuration
            config = OTelConfig.from_env()
            print(config.service_name)  # "my-agent"
            ```
        """
        return cls(
            enabled=os.getenv("OTEL_ENABLED", "true").lower() == "true",
            service_name=os.getenv("OTEL_SERVICE_NAME", "agent_framework"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("OTEL_ENVIRONMENT", "development"),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            otlp_protocol=os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"),
            metrics_exporter=os.getenv("OTEL_METRICS_EXPORTER", "otlp"),
            logs_exporter=os.getenv("OTEL_LOGS_EXPORTER", "otlp"),
        )


class OTelSetup:
    """Unified OpenTelemetry setup for traces, metrics, and logs.

    This class provides a single initialization point for all OTel providers,
    ensuring consistent configuration across traces, metrics, and logs.
    It supports graceful degradation when OTel packages are not installed.

    Attributes:
        config: OTelConfig instance with configuration options

    Example:
        ```python
        # Initialize with default config from environment
        setup = OTelSetup()
        if setup.initialize():
            tracer = setup.get_tracer()
            meter = setup.get_meter()
            logger_provider = setup.get_logger_provider()

        # Cleanup on shutdown
        setup.shutdown()
        ```
    """

    def __init__(self, config: OTelConfig | None = None) -> None:
        """Initialize the OTel setup.

        Args:
            config: Optional OTelConfig instance. If not provided,
                   configuration is loaded from environment variables.
        """
        self.config = config or OTelConfig.from_env()
        self._tracer_provider: Any = None
        self._meter_provider: Any = None
        self._logger_provider: Any = None
        self._initialized = False
        self._otel_available: bool | None = None

    def _check_otel_available(self) -> bool:
        """Check if OpenTelemetry packages are available.

        Performs a lazy check for OTel package availability. The result
        is cached to avoid repeated import attempts.

        Returns:
            True if OpenTelemetry packages are installed, False otherwise
        """
        if self._otel_available is not None:
            return self._otel_available

        try:
            from opentelemetry import metrics, trace  # noqa: F401
            from opentelemetry.sdk.metrics import MeterProvider  # noqa: F401
            from opentelemetry.sdk.trace import TracerProvider  # noqa: F401
            from opentelemetry.sdk._logs import LoggerProvider  # noqa: F401

            self._otel_available = True
            logger.debug("OpenTelemetry packages available")
        except ImportError:
            self._otel_available = False
            logger.warning(
                "OpenTelemetry packages not installed. "
                "Install with: pip install opentelemetry-sdk opentelemetry-api"
            )

        return self._otel_available

    def initialize(self) -> bool:
        """Initialize all OTel providers.

        Sets up TracerProvider, MeterProvider, and LoggerProvider with
        the configured exporters. Supports both gRPC and HTTP OTLP exporters.

        Returns:
            True if initialization was successful, False otherwise.
            Returns False if:
            - OTel is disabled via config
            - OTel packages are not installed
            - Provider initialization fails

        Example:
            ```python
            setup = OTelSetup()
            if setup.initialize():
                print("OTel initialized successfully")
            else:
                print("OTel initialization failed or disabled")
            ```
        """
        if not self.config.enabled:
            logger.info("OpenTelemetry is disabled via configuration")
            return False

        if not self._check_otel_available():
            logger.warning(
                "OpenTelemetry packages not installed. "
                "OTel features will be disabled."
            )
            return False

        try:
            self._setup_tracer_provider()
            self._setup_meter_provider()
            self._setup_logger_provider()
            self._initialized = True
            logger.info(
                f"OpenTelemetry initialized for service '{self.config.service_name}' "
                f"(version: {self.config.service_version}, env: {self.config.environment})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            return False

    def _get_resource(self) -> Any:
        """Create OTel Resource with service attributes.

        Returns:
            OpenTelemetry Resource instance with service.name,
            service.version, and deployment.environment attributes
        """
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

        return Resource.create({
            SERVICE_NAME: self.config.service_name,
            SERVICE_VERSION: self.config.service_version,
            "deployment.environment": self.config.environment,
        })

    def _create_otlp_span_exporter(self) -> Any:
        """Create OTLP span exporter based on protocol configuration.

        Returns:
            OTLP span exporter (gRPC or HTTP) or None if no endpoint configured
        """
        if not self.config.otlp_endpoint:
            return None

        if self.config.otlp_protocol == "http":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            return OTLPSpanExporter(endpoint=f"{self.config.otlp_endpoint}/v1/traces")
        else:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            return OTLPSpanExporter(endpoint=self.config.otlp_endpoint)

    def _create_otlp_metric_exporter(self) -> Any:
        """Create OTLP metric exporter based on protocol configuration.

        Returns:
            OTLP metric exporter (gRPC or HTTP) or None if not configured
        """
        if self.config.metrics_exporter != "otlp" or not self.config.otlp_endpoint:
            return None

        if self.config.otlp_protocol == "http":
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            return OTLPMetricExporter(endpoint=f"{self.config.otlp_endpoint}/v1/metrics")
        else:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            return OTLPMetricExporter(endpoint=self.config.otlp_endpoint)

    def _create_otlp_log_exporter(self) -> Any:
        """Create OTLP log exporter based on protocol configuration.

        Returns:
            OTLP log exporter (gRPC or HTTP) or None if not configured
        """
        if self.config.logs_exporter != "otlp" or not self.config.otlp_endpoint:
            return None

        if self.config.otlp_protocol == "http":
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
            return OTLPLogExporter(endpoint=f"{self.config.otlp_endpoint}/v1/logs")
        else:
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
            return OTLPLogExporter(endpoint=self.config.otlp_endpoint)

    def _setup_tracer_provider(self) -> None:
        """Set up the TracerProvider with configured exporters."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        resource = self._get_resource()
        self._tracer_provider = TracerProvider(resource=resource)

        otlp_exporter = self._create_otlp_span_exporter()
        if otlp_exporter:
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.debug(f"Added OTLP span exporter to {self.config.otlp_endpoint}")
        else:
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            logger.debug("No OTLP endpoint configured, using console span exporter")

        trace.set_tracer_provider(self._tracer_provider)

    def _setup_meter_provider(self) -> None:
        """Set up the MeterProvider with configured exporters and custom histogram buckets."""
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
            PeriodicExportingMetricReader,
        )
        from opentelemetry.sdk.metrics.view import View, ExplicitBucketHistogramAggregation

        resource = self._get_resource()
        readers = []

        if self.config.metrics_exporter == "otlp":
            otlp_exporter = self._create_otlp_metric_exporter()
            if otlp_exporter:
                readers.append(PeriodicExportingMetricReader(otlp_exporter))
                logger.debug(f"Added OTLP metric exporter to {self.config.otlp_endpoint}")

        if self.config.metrics_exporter == "prometheus":
            try:
                from opentelemetry.exporter.prometheus import PrometheusMetricReader
                readers.append(PrometheusMetricReader())
                logger.debug("Added Prometheus metric reader")
            except ImportError:
                logger.warning(
                    "Prometheus exporter not installed. "
                    "Install with: pip install opentelemetry-exporter-prometheus"
                )

        if not readers and self.config.metrics_exporter != "none":
            readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))
            logger.debug("No metric exporter configured, using console exporter")

        llm_duration_buckets = (
            100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000,
            100000, 150000, 200000, 300000, 600000
        )

        views = [
            View(
                instrument_name="llm.request.duration",
                aggregation=ExplicitBucketHistogramAggregation(boundaries=llm_duration_buckets),
            ),
            View(
                instrument_name="http.request.duration",
                aggregation=ExplicitBucketHistogramAggregation(boundaries=llm_duration_buckets),
            ),
        ]

        self._meter_provider = MeterProvider(
            resource=resource, metric_readers=readers, views=views
        )
        metrics.set_meter_provider(self._meter_provider)
        logger.debug("Configured custom histogram buckets for LLM duration metrics (up to 10min)")

    def _setup_logger_provider(self) -> None:
        """Set up the LoggerProvider with configured exporters."""
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import (
            BatchLogRecordProcessor,
            ConsoleLogExporter,
        )
        from opentelemetry._logs import set_logger_provider

        resource = self._get_resource()
        self._logger_provider = LoggerProvider(resource=resource)

        otlp_exporter = self._create_otlp_log_exporter()
        if otlp_exporter:
            self._logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(otlp_exporter)
            )
            logger.debug(f"Added OTLP log exporter to {self.config.otlp_endpoint}")
        elif self.config.logs_exporter != "none":
            self._logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(ConsoleLogExporter())
            )
            logger.debug("No OTLP endpoint configured, using console log exporter")

        set_logger_provider(self._logger_provider)

    def get_tracer(self, name: str = "agent_framework") -> Any:
        """Get a tracer instance.

        Args:
            name: Tracer name (default: agent_framework)

        Returns:
            OpenTelemetry Tracer instance, or a no-op tracer if
            OTel is not initialized

        Example:
            ```python
            tracer = setup.get_tracer("my-component")
            with tracer.start_as_current_span("operation") as span:
                span.set_attribute("key", "value")
            ```
        """
        if not self._initialized or not self._tracer_provider:
            from opentelemetry import trace
            return trace.get_tracer(name)

        return self._tracer_provider.get_tracer(name, self.config.service_version)

    def get_meter(self, name: str = "agent_framework") -> Any:
        """Get a meter instance.

        Args:
            name: Meter name (default: agent_framework)

        Returns:
            OpenTelemetry Meter instance, or a no-op meter if
            OTel is not initialized

        Example:
            ```python
            meter = setup.get_meter("my-component")
            counter = meter.create_counter("requests")
            counter.add(1, {"endpoint": "/api"})
            ```
        """
        if not self._initialized or not self._meter_provider:
            from opentelemetry import metrics
            return metrics.get_meter(name)

        return self._meter_provider.get_meter(name, self.config.service_version)

    def get_logger_provider(self) -> Any:
        """Get the logger provider for log emission.

        Returns:
            OpenTelemetry LoggerProvider instance, or None if
            OTel is not initialized

        Example:
            ```python
            provider = setup.get_logger_provider()
            if provider:
                otel_logger = provider.get_logger("my-component")
            ```
        """
        return self._logger_provider

    @property
    def is_initialized(self) -> bool:
        """Check if OTel has been successfully initialized.

        Returns:
            True if initialize() completed successfully, False otherwise
        """
        return self._initialized

    def shutdown(self) -> None:
        """Gracefully shutdown all providers.

        Flushes any pending telemetry data and releases resources.
        Should be called during application shutdown.

        Example:
            ```python
            import atexit

            setup = OTelSetup()
            setup.initialize()
            atexit.register(setup.shutdown)
            ```
        """
        if not self._initialized:
            return

        try:
            if self._tracer_provider:
                self._tracer_provider.shutdown()
                logger.debug("TracerProvider shutdown complete")

            if self._meter_provider:
                self._meter_provider.shutdown()
                logger.debug("MeterProvider shutdown complete")

            if self._logger_provider:
                self._logger_provider.shutdown()
                logger.debug("LoggerProvider shutdown complete")

            self._initialized = False
            logger.info("OpenTelemetry shutdown complete")
        except Exception as e:
            logger.error(f"Error during OpenTelemetry shutdown: {e}")


_default_otel_setup: OTelSetup | None = None


def get_otel_setup() -> OTelSetup:
    """Get or create the default OTel setup instance.

    Returns a singleton instance of OTelSetup for convenience.
    The setup is not automatically initialized; call initialize()
    to start OTel.

    Returns:
        OTelSetup instance

    Example:
        ```python
        setup = get_otel_setup()
        if setup.initialize():
            tracer = setup.get_tracer()
        ```
    """
    global _default_otel_setup
    if _default_otel_setup is None:
        _default_otel_setup = OTelSetup()
    return _default_otel_setup


def reset_otel_setup() -> None:
    """Reset the default OTel setup instance.

    Useful for testing or reconfiguration. Shuts down the existing
    setup if initialized.
    """
    global _default_otel_setup
    if _default_otel_setup is not None:
        _default_otel_setup.shutdown()
        _default_otel_setup = None
