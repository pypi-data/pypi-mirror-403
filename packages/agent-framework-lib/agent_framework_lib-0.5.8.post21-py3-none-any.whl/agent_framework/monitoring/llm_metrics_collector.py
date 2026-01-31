"""LLM Metrics Collector Module.

Orchestrates token counting and timing tracking for LLM interactions.
Combines TokenCounter and TimingTracker into a single interface for
collecting comprehensive observability metrics.

This module provides:
- Unified metrics collection interface
- Token counting for input, thinking, and output phases
- Timing measurements including time-to-first-token
- Tool call tracking with token counting
- Enable/disable toggle for minimal overhead when not needed
"""

from datetime import datetime, timezone
from typing import Any, Optional

from agent_framework.monitoring.llm_metrics import LLMMetrics
from agent_framework.monitoring.timing_tracker import TimingTracker
from agent_framework.monitoring.token_counter import TokenCounter


class LLMMetricsCollector:
    """Collect and aggregate LLM metrics.

    This class orchestrates token counting and timing tracking for LLM calls,
    providing a unified interface for metrics collection. It can be enabled
    or disabled at runtime to minimize overhead when metrics are not needed.

    Attributes:
        enabled: Whether metrics collection is active
        model_name: Name of the LLM model for encoding selection
        session_id: Session identifier for correlation
        user_id: User identifier for correlation
        agent_id: Agent identifier for correlation

    Example:
        ```python
        collector = LLMMetricsCollector(
            model_name="gpt-5-mini",
            session_id="session-123",
            enabled=True
        )

        # Start collection
        collector.start()

        # Count tokens at different phases
        collector.count_input("System prompt and user message")
        collector.record_first_token()  # For streaming
        collector.count_output("LLM response text")

        # Track tool calls
        collector.start_tool_call("tool_1")
        # ... tool execution ...
        collector.end_tool_call("tool_1")

        # Finish and get metrics
        metrics = collector.finish()
        print(f"Total tokens: {metrics.total_tokens}")
        ```
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        enabled: bool = True,
        api_request_id: Optional[str] = None,
    ) -> None:
        """Initialize the metrics collector.

        Args:
            model_name: Optional model name for encoding selection
            session_id: Optional session ID for correlation
            user_id: Optional user ID for correlation
            agent_id: Optional agent ID for correlation
            enabled: Whether to collect metrics (default: True)
            api_request_id: Optional API request ID for correlation with API timing
        """
        self.enabled = enabled
        self.model_name = model_name
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.api_request_id = api_request_id

        self._token_counter: Optional[TokenCounter] = None
        self._timing_tracker: Optional[TimingTracker] = None
        self._input_tokens = 0
        self._thinking_tokens = 0
        self._output_tokens = 0

        if enabled:
            self._token_counter = TokenCounter(model_name)
            self._timing_tracker = TimingTracker()

    def start(self) -> None:
        """Start metrics collection for an LLM call.

        Records the start timestamp for timing measurements.
        Has no effect if collector is disabled.
        """
        if self._timing_tracker:
            self._timing_tracker.start()

    def count_input(self, text: str) -> int:
        """Count and record input tokens.

        Args:
            text: Input text (system prompt + user message)

        Returns:
            Number of tokens counted, or 0 if disabled
        """
        if not self._token_counter:
            return 0
        result = self._token_counter.count_tokens(text)
        self._input_tokens += result.count
        return result.count

    def count_thinking(self, text: str) -> int:
        """Count and record thinking/intermediate tokens.

        Args:
            text: Intermediate reasoning or tool call text

        Returns:
            Number of tokens counted, or 0 if disabled
        """
        if not self._token_counter:
            return 0
        result = self._token_counter.count_tokens(text)
        self._thinking_tokens += result.count
        return result.count

    def count_tool_call_tokens(self, tool_calls: list[dict[str, Any]]) -> int:
        """Count and record tool call tokens as thinking tokens.

        Extracts function names and arguments from tool calls and counts
        them as thinking tokens, since tool calls represent LLM reasoning
        about which tools to use and how to use them.

        Args:
            tool_calls: List of tool call dictionaries, typically in the format:
                [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Seattle"}'
                        }
                    }
                ]

        Returns:
            Total number of tokens counted across all tool calls, or 0 if disabled
        """
        if not self._token_counter or not tool_calls:
            return 0

        total_tokens = 0
        for tool_call in tool_calls:
            # Extract function information from the tool call
            function_info = tool_call.get("function", {})
            if not function_info and "name" in tool_call:
                # Handle alternative format where name/arguments are at top level
                function_info = tool_call

            function_name = function_info.get("name", "")
            arguments = function_info.get("arguments", "")

            # Count tokens for function name
            if function_name:
                result = self._token_counter.count_tokens(function_name)
                total_tokens += result.count
                self._thinking_tokens += result.count

            # Count tokens for arguments (may be JSON string or dict)
            if arguments:
                if isinstance(arguments, dict):
                    import json

                    arguments = json.dumps(arguments)
                result = self._token_counter.count_tokens(arguments)
                total_tokens += result.count
                self._thinking_tokens += result.count

        return total_tokens

    def count_output(self, text: str) -> int:
        """Count and record output tokens.

        Args:
            text: Final response text from the LLM

        Returns:
            Number of tokens counted, or 0 if disabled
        """
        if not self._token_counter:
            return 0
        result = self._token_counter.count_tokens(text)
        self._output_tokens += result.count
        return result.count

    def record_first_token(self) -> None:
        """Record time to first token for streaming responses.

        Should be called when the first token is received during streaming.
        Has no effect if collector is disabled or already recorded.
        """
        if self._timing_tracker:
            self._timing_tracker.record_first_token()

    def start_tool_call(self, tool_id: str) -> None:
        """Start timing a tool call.

        Args:
            tool_id: Unique identifier for the tool call
        """
        if self._timing_tracker:
            self._timing_tracker.start_tool_call(tool_id)

    def end_tool_call(self, tool_id: str) -> None:
        """End timing a tool call.

        Args:
            tool_id: Unique identifier for the tool call (must match start_tool_call)
        """
        if self._timing_tracker:
            self._timing_tracker.end_tool_call(tool_id)

    def finish(self) -> Optional[LLMMetrics]:
        """Finish collection and return metrics.

        Returns:
            LLMMetrics with all collected data, or None if disabled

        Note:
            After calling finish(), the collector should be reset() before reuse.
        """
        if not self.enabled:
            return None

        timing = self._timing_tracker.finish() if self._timing_tracker else None
        encoding_name = "cl100k_base"
        if self._token_counter:
            _, encoding_name = self._token_counter._get_encoding()

        return LLMMetrics(
            input_tokens=self._input_tokens,
            thinking_tokens=self._thinking_tokens,
            output_tokens=self._output_tokens,
            start_time=timing.start_time if timing else datetime.now(timezone.utc),
            end_time=timing.end_time if timing else None,
            duration_ms=timing.duration_ms if timing else None,
            time_to_first_token_ms=timing.time_to_first_token_ms if timing else None,
            tool_call_durations_ms=timing.tool_call_durations_ms if timing else [],
            model_name=self.model_name,
            encoding_name=encoding_name,
            session_id=self.session_id,
            user_id=self.user_id,
            agent_id=self.agent_id,
            api_request_id=self.api_request_id,
        )

    def reset(self) -> None:
        """Reset collector for reuse.

        Clears all accumulated token counts and timing data while
        preserving the enabled state and configuration.
        """
        self._input_tokens = 0
        self._thinking_tokens = 0
        self._output_tokens = 0
        if self._timing_tracker:
            self._timing_tracker.reset()
