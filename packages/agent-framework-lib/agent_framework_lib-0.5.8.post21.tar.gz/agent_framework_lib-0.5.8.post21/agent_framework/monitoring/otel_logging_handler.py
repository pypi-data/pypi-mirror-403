"""OpenTelemetry Logging Handler.

Provides a Python logging handler that emits logs via OpenTelemetry LoggerProvider,
enabling trace context correlation and structured log export to OTel backends.

This handler integrates with the standard Python logging module and automatically:
- Injects trace_id and span_id from active spans
- Maps Python log levels to OTel severity numbers
- Emits structured log records with all attributes

Example:
    ```python
    from agent_framework.monitoring.otel_logging_handler import OTelLoggingHandler
    from agent_framework.monitoring.otel_setup import get_otel_setup

    setup = get_otel_setup()
    setup.initialize()

    handler = OTelLoggingHandler(setup)
    logger = logging.getLogger("my_app")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("This log will be exported via OTel")
    ```
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from agent_framework.monitoring.otel_setup import OTelSetup


# Python log level to OTel severity number mapping
# Based on OpenTelemetry Log Data Model specification
# https://opentelemetry.io/docs/specs/otel/logs/data-model/#severity-fields
SEVERITY_NUMBER_MAP = {
    logging.NOTSET: 0,      # UNSPECIFIED
    logging.DEBUG: 5,       # DEBUG
    logging.INFO: 9,        # INFO
    logging.WARNING: 13,    # WARN
    logging.ERROR: 17,      # ERROR
    logging.CRITICAL: 21,   # FATAL
}

# OTel severity text mapping
SEVERITY_TEXT_MAP = {
    logging.NOTSET: "UNSPECIFIED",
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "FATAL",
}


class OTelLoggingHandler(logging.Handler):
    """Logging handler that emits logs via OpenTelemetry.

    This handler extends Python's logging.Handler to emit log records
    through the OpenTelemetry LoggerProvider. It automatically injects
    trace context (trace_id, span_id) when a span is active.

    Attributes:
        otel_setup: OTelSetup instance for getting LoggerProvider
        logger_name: Name for the OTel logger (default: agent_framework)
    """

    def __init__(
        self,
        otel_setup: OTelSetup,
        logger_name: str = "agent_framework",
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize the OTel logging handler.

        Args:
            otel_setup: OTelSetup instance that provides the LoggerProvider
            logger_name: Name for the OTel logger (default: agent_framework)
            level: Logging level threshold (default: NOTSET, accepts all)
        """
        super().__init__(level)
        self._otel_setup = otel_setup
        self._logger_name = logger_name
        self._otel_logger: Any = None
        self._initialized = False
        self._initialize_logger()

    def _initialize_logger(self) -> None:
        """Initialize the OTel logger from the LoggerProvider."""
        if not self._otel_setup.is_initialized:
            return

        logger_provider = self._otel_setup.get_logger_provider()
        if logger_provider is None:
            return

        try:
            self._otel_logger = logger_provider.get_logger(
                self._logger_name,
                version=self._otel_setup.config.service_version,
            )
            self._initialized = True
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to initialize OTel logger: {e}"
            )

    def _get_trace_context(self) -> tuple[str | None, str | None]:
        """Get current trace_id and span_id from active span.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None)
            if no active span or OTel unavailable
        """
        if not self._otel_setup.is_initialized:
            return None, None

        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                return trace_id, span_id
        except ImportError:
            pass
        except Exception as e:
            logging.getLogger(__name__).debug(
                f"Failed to get trace context: {e}"
            )

        return None, None

    def _map_level_to_severity(self, levelno: int) -> tuple[int, str]:
        """Map Python log level to OTel severity number and text.

        Args:
            levelno: Python logging level number

        Returns:
            Tuple of (severity_number, severity_text)
        """
        severity_number = SEVERITY_NUMBER_MAP.get(levelno, 0)
        severity_text = SEVERITY_TEXT_MAP.get(levelno, "UNSPECIFIED")

        if levelno not in SEVERITY_NUMBER_MAP:
            if levelno < logging.DEBUG:
                severity_number = 1  # TRACE
                severity_text = "TRACE"
            elif levelno < logging.INFO:
                severity_number = 5  # DEBUG
                severity_text = "DEBUG"
            elif levelno < logging.WARNING:
                severity_number = 9  # INFO
                severity_text = "INFO"
            elif levelno < logging.ERROR:
                severity_number = 13  # WARN
                severity_text = "WARN"
            elif levelno < logging.CRITICAL:
                severity_number = 17  # ERROR
                severity_text = "ERROR"
            else:
                severity_number = 21  # FATAL
                severity_text = "FATAL"

        return severity_number, severity_text

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record via OpenTelemetry.

        This method is called by the logging framework for each log record
        that passes the level filter. It formats the record and emits it
        through the OTel LoggerProvider.

        Args:
            record: The log record to emit
        """
        if not self._initialized:
            self._initialize_logger()
            if not self._initialized:
                return

        try:
            self._emit_otel_log(record)
        except Exception:
            self.handleError(record)

    def _emit_otel_log(self, record: logging.LogRecord) -> None:
        """Internal method to emit log via OTel.

        Args:
            record: The log record to emit
        """
        if self._otel_logger is None:
            return

        trace_id, span_id = self._get_trace_context()
        severity_number, severity_text = self._map_level_to_severity(record.levelno)

        attributes: dict[str, Any] = {
            "level": record.levelname,
            "logger_name": record.name,
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
            "pathname": record.pathname,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if trace_id:
            attributes["trace_id"] = trace_id
        if span_id:
            attributes["span_id"] = span_id

        if hasattr(record, "session_id") and record.session_id:
            attributes["session_id"] = record.session_id

        if hasattr(record, "request_id") and record.request_id:
            attributes["request_id"] = record.request_id

        if hasattr(record, "context") and record.context:
            attributes["context"] = str(record.context)

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            if exc_type:
                attributes["exception.type"] = exc_type.__name__
            if exc_value:
                attributes["exception.message"] = str(exc_value)

        try:
            from opentelemetry._logs import SeverityNumber

            self._otel_logger.emit(
                self._otel_logger.create_log_record(
                    body=self.format(record) if self.formatter else record.getMessage(),
                    severity_number=SeverityNumber(severity_number),
                    severity_text=severity_text,
                    attributes=attributes,
                )
            )
        except ImportError:
            pass
        except AttributeError:
            self._emit_otel_log_legacy(record, attributes, severity_number)

    def _emit_otel_log_legacy(
        self,
        record: logging.LogRecord,
        attributes: dict[str, Any],
        severity_number: int,
    ) -> None:
        """Fallback emission for older OTel SDK versions.

        Args:
            record: The log record to emit
            attributes: Prepared attributes dictionary
            severity_number: OTel severity number
        """
        try:
            from opentelemetry.sdk._logs import LogRecord as OTelLogRecord
            from opentelemetry._logs import SeverityNumber
            import time

            log_record = OTelLogRecord(
                timestamp=int(record.created * 1e9),
                observed_timestamp=int(time.time_ns()),
                body=self.format(record) if self.formatter else record.getMessage(),
                severity_number=SeverityNumber(severity_number),
                attributes=attributes,
            )

            if hasattr(self._otel_logger, "_multi_log_record_processor"):
                self._otel_logger._multi_log_record_processor.emit(log_record)
        except Exception as e:
            logging.getLogger(__name__).debug(
                f"Failed to emit log via legacy method: {e}"
            )

    def close(self) -> None:
        """Close the handler.

        Releases any resources held by the handler.
        """
        self._otel_logger = None
        self._initialized = False
        super().close()


def get_otel_logging_handler(
    otel_setup: OTelSetup | None = None,
    logger_name: str = "agent_framework",
    level: int = logging.NOTSET,
) -> OTelLoggingHandler | None:
    """Create an OTel logging handler if OTel is available.

    Convenience function that creates an OTelLoggingHandler using
    the default or provided OTelSetup instance.

    Args:
        otel_setup: Optional OTelSetup instance (uses default if None)
        logger_name: Name for the OTel logger
        level: Logging level threshold

    Returns:
        OTelLoggingHandler if OTel is initialized, None otherwise

    Example:
        ```python
        handler = get_otel_logging_handler()
        if handler:
            logging.getLogger("my_app").addHandler(handler)
        ```
    """
    if otel_setup is None:
        from agent_framework.monitoring.otel_setup import get_otel_setup
        otel_setup = get_otel_setup()

    if not otel_setup.is_initialized:
        return None

    return OTelLoggingHandler(otel_setup, logger_name, level)


def setup_otel_logging(
    logger_instance: logging.Logger | None = None,
    otel_setup: OTelSetup | None = None,
    log_level: str = "INFO",
) -> OTelLoggingHandler | None:
    """Set up OTel logging for a logger instance.

    Convenience function that creates and attaches an OTelLoggingHandler
    to the specified logger.

    Args:
        logger_instance: Logger to add handler to (default: agent_framework)
        otel_setup: Optional OTelSetup instance
        log_level: Logging level as string (default: INFO)

    Returns:
        OTelLoggingHandler if successful, None otherwise

    Example:
        ```python
        from agent_framework.monitoring.otel_logging_handler import setup_otel_logging
        from agent_framework.monitoring.otel_setup import get_otel_setup

        setup = get_otel_setup()
        setup.initialize()

        handler = setup_otel_logging(log_level="DEBUG")
        ```
    """
    handler = get_otel_logging_handler(otel_setup, level=getattr(logging, log_level.upper()))
    if handler is None:
        return None

    if logger_instance is None:
        logger_instance = logging.getLogger("agent_framework")

    logger_instance.addHandler(handler)
    return handler
