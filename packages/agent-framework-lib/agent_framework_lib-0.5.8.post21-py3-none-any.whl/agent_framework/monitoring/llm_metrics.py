"""LLM Metrics Data Models.

Provides structured data models for LLM observability metrics including:
- LLMMetrics: Complete metrics for a single LLM call
- SessionLLMStats: Cumulative statistics for a session

These models support:
- Token counting (input, thinking, output)
- Timing measurements
- Elasticsearch document serialization
- OpenTelemetry trace correlation
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field


class LLMMetrics(BaseModel):
    """Complete metrics for a single LLM call.

    This model captures all observability data for an LLM interaction including
    token counts, timing measurements, and context information for correlation.

    Attributes:
        input_tokens: Tokens from user message and system prompt
        thinking_tokens: Tokens from intermediate reasoning/tool calls
        output_tokens: Tokens from the final response
        start_time: When the LLM call started
        end_time: When the LLM call completed
        duration_ms: Total duration in milliseconds
        time_to_first_token_ms: Time until first token received (streaming)
        tool_call_durations_ms: List of tool call execution times
        model_name: Name of the LLM model used
        encoding_name: Tiktoken encoding used for counting
        session_id: Session identifier for correlation
        user_id: User identifier for correlation
        agent_id: Agent identifier for correlation
        trace_id: OpenTelemetry trace ID
        span_id: OpenTelemetry span ID

    Example:
        ```python
        metrics = LLMMetrics(
            input_tokens=150,
            thinking_tokens=50,
            output_tokens=200,
            start_time=datetime.now(timezone.utc),
            model_name="gpt-5-mini",
            session_id="session-123"
        )
        print(f"Total tokens: {metrics.total_tokens}")
        print(f"Throughput: {metrics.tokens_per_second} tokens/sec")
        ```
    """

    # Token counts
    input_tokens: int = 0
    thinking_tokens: int = 0
    output_tokens: int = 0

    # Timing
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    time_to_first_token_ms: float | None = None
    tool_call_durations_ms: list[float] = Field(default_factory=list)

    # Context
    model_name: str | None = None
    encoding_name: str = "cl100k_base"
    session_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None

    # Trace correlation
    trace_id: str | None = None
    span_id: str | None = None

    # API timing correlation
    api_request_id: str | None = None

    @computed_field
    @property
    def total_tokens(self) -> int:
        """Total tokens across all categories.

        Returns:
            Sum of input_tokens + thinking_tokens + output_tokens
        """
        return self.input_tokens + self.thinking_tokens + self.output_tokens

    @computed_field
    @property
    def tokens_per_second(self) -> float | None:
        """Output tokens per second throughput.

        Returns:
            Throughput in tokens/second, or None if duration or output_tokens is zero
        """
        if self.duration_ms and self.duration_ms > 0 and self.output_tokens > 0:
            duration_seconds = self.duration_ms / 1000
            if duration_seconds > 0:
                return self.output_tokens / duration_seconds
        return None

    def to_elasticsearch_doc(self) -> dict[str, Any]:
        """Convert to Elasticsearch document format.

        Returns:
            Dictionary suitable for Elasticsearch indexing with @timestamp field

        Example:
            ```python
            doc = metrics.to_elasticsearch_doc()
            await es_client.index(index="agent-llm-metrics-2024-01-15", body=doc)
            ```
        """
        return {
            "@timestamp": self.start_time.isoformat(),
            "input_tokens": self.input_tokens,
            "thinking_tokens": self.thinking_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "tokens_per_second": self.tokens_per_second,
            "model_name": self.model_name,
            "encoding_name": self.encoding_name,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "api_request_id": self.api_request_id,
            "tool_call_count": len(self.tool_call_durations_ms),
            "tool_call_total_ms": (
                sum(self.tool_call_durations_ms) if self.tool_call_durations_ms else 0.0
            ),
        }


class SessionLLMStats(BaseModel):
    """Cumulative LLM statistics for a session.

    Tracks aggregate metrics across multiple LLM calls within a session,
    useful for usage tracking and cost estimation.

    Attributes:
        total_input_tokens: Cumulative input tokens
        total_thinking_tokens: Cumulative thinking tokens
        total_output_tokens: Cumulative output tokens
        total_llm_calls: Number of LLM calls made
        total_duration_ms: Cumulative duration in milliseconds

    Example:
        ```python
        stats = SessionLLMStats()

        # Update with each LLM call
        stats.update(metrics1)
        stats.update(metrics2)

        print(f"Total calls: {stats.total_llm_calls}")
        print(f"Average response time: {stats.average_response_time_ms}ms")
        ```
    """

    total_input_tokens: int = 0
    total_thinking_tokens: int = 0
    total_output_tokens: int = 0
    total_llm_calls: int = 0
    total_duration_ms: float = 0.0

    @computed_field
    @property
    def total_tokens(self) -> int:
        """Total tokens across all categories.

        Returns:
            Sum of total_input_tokens + total_thinking_tokens + total_output_tokens
        """
        return self.total_input_tokens + self.total_thinking_tokens + self.total_output_tokens

    @computed_field
    @property
    def average_response_time_ms(self) -> float:
        """Average response time per LLM call.

        Returns:
            Average duration in milliseconds, or 0.0 if no calls made
        """
        if self.total_llm_calls > 0:
            return self.total_duration_ms / self.total_llm_calls
        return 0.0

    def update(self, metrics: LLMMetrics) -> None:
        """Update cumulative stats with new metrics.

        Args:
            metrics: LLMMetrics from a completed LLM call

        Example:
            ```python
            stats = SessionLLMStats()
            stats.update(metrics)
            ```
        """
        self.total_input_tokens += metrics.input_tokens
        self.total_thinking_tokens += metrics.thinking_tokens
        self.total_output_tokens += metrics.output_tokens
        self.total_llm_calls += 1
        if metrics.duration_ms:
            self.total_duration_ms += metrics.duration_ms
