"""Timing tracker for LLM operations.

Provides precise timing measurements for LLM calls including:
- Total duration
- Time to first token (streaming)
- Tool call execution times
"""

import time
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TimingData(BaseModel):
    """Timing measurements for an LLM call."""

    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    time_to_first_token_ms: float | None = None
    tool_call_durations_ms: list[float] = Field(default_factory=list)

    def calculate_duration(self) -> float:
        """Calculate duration from start/end times."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return 0.0


class TimingTracker:
    """Track timing for LLM operations.

    Usage:
        tracker = TimingTracker()
        tracker.start()

        # For streaming responses
        tracker.record_first_token()

        # For tool calls
        tracker.start_tool_call("tool_1")
        # ... tool execution ...
        tracker.end_tool_call("tool_1")

        timing_data = tracker.finish()
    """

    def __init__(self) -> None:
        self._start_time: float | None = None
        self._first_token_time: float | None = None
        self._tool_call_starts: dict[str, float] = {}
        self._tool_call_durations: list[float] = []
        self._start_datetime: datetime | None = None

    def start(self) -> None:
        """Record start of LLM call."""
        self._start_time = time.perf_counter()
        self._start_datetime = datetime.now(timezone.utc)

    def record_first_token(self) -> None:
        """Record when first token is received (streaming)."""
        if self._first_token_time is None and self._start_time is not None:
            self._first_token_time = time.perf_counter()

    def start_tool_call(self, tool_id: str) -> None:
        """Record start of a tool call.

        Args:
            tool_id: Unique identifier for the tool call
        """
        self._tool_call_starts[tool_id] = time.perf_counter()

    def end_tool_call(self, tool_id: str) -> None:
        """Record end of a tool call.

        Args:
            tool_id: Unique identifier for the tool call (must match start_tool_call)
        """
        if tool_id in self._tool_call_starts:
            duration = (time.perf_counter() - self._tool_call_starts[tool_id]) * 1000
            self._tool_call_durations.append(duration)
            del self._tool_call_starts[tool_id]

    def finish(self) -> TimingData:
        """Finish timing and return results.

        Returns:
            TimingData with all collected timing measurements
        """
        end_time = time.perf_counter()
        end_datetime = datetime.now(timezone.utc)

        duration_ms = None
        ttft_ms = None

        if self._start_time is not None:
            duration_ms = (end_time - self._start_time) * 1000

            if self._first_token_time is not None:
                ttft_ms = (self._first_token_time - self._start_time) * 1000

        return TimingData(
            start_time=self._start_datetime or datetime.now(timezone.utc),
            end_time=end_datetime,
            duration_ms=duration_ms,
            time_to_first_token_ms=ttft_ms,
            tool_call_durations_ms=self._tool_call_durations.copy(),
        )

    def reset(self) -> None:
        """Reset tracker for reuse."""
        self._start_time = None
        self._first_token_time = None
        self._tool_call_starts.clear()
        self._tool_call_durations.clear()
        self._start_datetime = None
