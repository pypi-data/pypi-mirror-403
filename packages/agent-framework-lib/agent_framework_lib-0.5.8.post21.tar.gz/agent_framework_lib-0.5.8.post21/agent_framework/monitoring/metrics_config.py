"""Unified metrics configuration for LLM and API observability.

This module provides a centralized configuration for all metrics-related
settings, simplifying environment variable management and providing
sensible defaults.

Environment Variables:
- METRICS_ENABLED: Master switch for all metrics (default: true)
- METRICS_INDEX_PREFIX: Base prefix for all metrics indices (default: agent-metrics)
- METRICS_BATCH_SIZE: Batch size for ES bulk operations (default: 50)
- METRICS_FLUSH_INTERVAL: Flush interval in seconds (default: 5.0)

The module creates the following Elasticsearch indices:
- {prefix}-llm-{date}: LLM call metrics (tokens, timing, model info)
- {prefix}-api-{date}: API request metrics (end-to-end timing)
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class MetricsConfig:
    """Unified configuration for metrics collection and logging.

    This class centralizes all metrics-related configuration, providing
    a single source of truth for metrics settings across the framework.

    Attributes:
        enabled: Master switch for all metrics collection
        index_prefix: Base prefix for Elasticsearch indices
        batch_size: Number of metrics to batch before sending to ES
        flush_interval: Seconds between automatic flushes
        max_buffer_size: Maximum buffer size (circular buffer)

    Example:
        ```python
        config = MetricsConfig.from_env()
        print(config.llm_index_pattern)  # agent-metrics-llm-{date}
        print(config.api_index_pattern)  # agent-metrics-api-{date}
        ```
    """

    enabled: bool = True
    index_prefix: str = "agent-metrics"
    batch_size: int = 50
    flush_interval: float = 5.0
    max_buffer_size: int = 1000

    @classmethod
    def from_env(cls) -> "MetricsConfig":
        """Create configuration from environment variables.

        Environment Variables:
            METRICS_ENABLED: Enable/disable all metrics (default: true)
            METRICS_INDEX_PREFIX: Base index prefix (default: agent-metrics)
            METRICS_BATCH_SIZE: Batch size for ES operations (default: 50)
            METRICS_FLUSH_INTERVAL: Flush interval in seconds (default: 5.0)
            METRICS_MAX_BUFFER_SIZE: Max buffer size (default: 1000)

        Returns:
            MetricsConfig instance with values from environment
        """
        enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        index_prefix = os.getenv("METRICS_INDEX_PREFIX", "agent-metrics")
        batch_size = int(os.getenv("METRICS_BATCH_SIZE", "50"))
        flush_interval = float(os.getenv("METRICS_FLUSH_INTERVAL", "5.0"))
        max_buffer_size = int(os.getenv("METRICS_MAX_BUFFER_SIZE", "1000"))

        return cls(
            enabled=enabled,
            index_prefix=index_prefix,
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer_size=max_buffer_size,
        )

    @property
    def llm_index_pattern(self) -> str:
        """Get the index pattern for LLM metrics.

        Returns:
            Index pattern with {date} placeholder, e.g., 'agent-metrics-llm-{date}'
        """
        return f"{self.index_prefix}-llm-{{date}}"

    @property
    def api_index_pattern(self) -> str:
        """Get the index pattern for API timing metrics.

        Returns:
            Index pattern with {date} placeholder, e.g., 'agent-metrics-api-{date}'
        """
        return f"{self.index_prefix}-api-{{date}}"

    def get_llm_index_name(self) -> str:
        """Get the current LLM metrics index name with date substitution.

        Returns:
            Index name with current date, e.g., 'agent-metrics-llm-2024-01-15'
        """
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.index_prefix}-llm-{current_date}"

    def get_api_index_name(self) -> str:
        """Get the current API metrics index name with date substitution.

        Returns:
            Index name with current date, e.g., 'agent-metrics-api-2024-01-15'
        """
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.index_prefix}-api-{current_date}"


# Global singleton for easy access
_metrics_config: MetricsConfig | None = None


def get_metrics_config() -> MetricsConfig:
    """Get the global metrics configuration singleton.

    Returns:
        MetricsConfig instance loaded from environment variables

    Example:
        ```python
        from agent_framework.monitoring.metrics_config import get_metrics_config

        config = get_metrics_config()
        if config.enabled:
            # Initialize metrics collection
            pass
        ```
    """
    global _metrics_config
    if _metrics_config is None:
        _metrics_config = MetricsConfig.from_env()
    return _metrics_config


def reset_metrics_config() -> None:
    """Reset the global metrics configuration.

    Useful for testing or when environment variables change.
    """
    global _metrics_config
    _metrics_config = None
