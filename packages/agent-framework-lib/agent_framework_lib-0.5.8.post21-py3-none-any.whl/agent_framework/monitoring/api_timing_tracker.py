"""API timing tracker for end-to-end HTTP request timing.

This module provides timing measurement for the complete API request lifecycle,
from FastAPI endpoint to response, enabling performance analysis across the
entire stack (network, preprocessing, LLM, postprocessing).
"""

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, computed_field


# Patterns for path parameter normalization
# These patterns match common path parameter formats
PATH_PARAM_PATTERNS = [
    # UUID pattern (e.g., /sessions/550e8400-e29b-41d4-a716-446655440000)
    (
        re.compile(r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
        "/{id}",
    ),
    # Numeric ID pattern (e.g., /users/123)
    (re.compile(r"/\d+(?=/|$)"), "/{id}"),
    # MongoDB ObjectId pattern (e.g., /items/507f1f77bcf86cd799439011)
    (re.compile(r"/[0-9a-fA-F]{24}(?=/|$)"), "/{id}"),
]


def normalize_endpoint_path(path: str) -> str:
    """Normalize an endpoint path for consistent metric labeling.

    This function:
    - Removes trailing slashes (except for root path)
    - Normalizes path parameters to consistent labels (e.g., /users/123 -> /users/{id})
    - Preserves the path structure for meaningful grouping

    Args:
        path: The raw endpoint path (e.g., "/message/", "/sessions/abc-123/messages")

    Returns:
        Normalized path string (e.g., "/message", "/sessions/{id}/messages")

    Examples:
        >>> normalize_endpoint_path("/message/")
        '/message'
        >>> normalize_endpoint_path("/sessions/550e8400-e29b-41d4-a716-446655440000/messages")
        '/sessions/{id}/messages'
        >>> normalize_endpoint_path("/users/123")
        '/users/{id}'
        >>> normalize_endpoint_path("/")
        '/'
    """
    if not path:
        return "/"

    # Remove trailing slashes (but keep root path as "/")
    normalized = path.rstrip("/") if path != "/" else path
    if not normalized:
        normalized = "/"

    # Normalize path parameters
    for pattern, replacement in PATH_PARAM_PATTERNS:
        normalized = pattern.sub(replacement, normalized)

    return normalized


class APITimingData(BaseModel):
    """Complete timing data for an API request lifecycle."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    request_start: datetime
    request_end: datetime | None = None
    llm_start: datetime | None = None
    llm_end: datetime | None = None
    first_chunk_sent: datetime | None = None

    total_api_duration_ms: float | None = None
    preprocessing_duration_ms: float | None = None
    llm_duration_ms: float | None = None
    postprocessing_duration_ms: float | None = None
    time_to_first_chunk_ms: float | None = None

    llm_call_count: int = 0
    total_llm_duration_ms: float = 0.0

    endpoint: str | None = None
    method: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    is_streaming: bool = False

    @computed_field
    @property
    def llm_percentage(self) -> float | None:
        """Percentage of total time spent in LLM calls."""
        if self.total_api_duration_ms and self.total_api_duration_ms > 0:
            return (self.total_llm_duration_ms / self.total_api_duration_ms) * 100
        return None

    @computed_field
    @property
    def overhead_ms(self) -> float | None:
        """Non-LLM overhead (preprocessing + postprocessing)."""
        if self.total_api_duration_ms is not None:
            return self.total_api_duration_ms - self.total_llm_duration_ms
        return None

    def to_elasticsearch_doc(self) -> dict[str, Any]:
        """Convert to Elasticsearch document format."""
        return {
            "@timestamp": self.request_start.isoformat(),
            "request_id": self.request_id,
            "total_api_duration_ms": self.total_api_duration_ms,
            "preprocessing_duration_ms": self.preprocessing_duration_ms,
            "llm_duration_ms": self.llm_duration_ms,
            "postprocessing_duration_ms": self.postprocessing_duration_ms,
            "time_to_first_chunk_ms": self.time_to_first_chunk_ms,
            "llm_call_count": self.llm_call_count,
            "total_llm_duration_ms": self.total_llm_duration_ms,
            "llm_percentage": self.llm_percentage,
            "overhead_ms": self.overhead_ms,
            "endpoint": self.endpoint,
            "method": self.method,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "is_streaming": self.is_streaming,
        }


class APITimingTracker:
    """Track timing for complete API request lifecycle.

    This tracker measures:
    - Total API duration (request arrival to response sent)
    - Preprocessing duration (request arrival to first LLM call)
    - LLM duration (time spent in LLM calls)
    - Postprocessing duration (last LLM response to HTTP response)
    - Time to first chunk (for streaming responses)
    """

    def __init__(
        self,
        endpoint: str | None = None,
        method: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        is_streaming: bool = False,
    ):
        self.endpoint = endpoint
        self.method = method
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.is_streaming = is_streaming

        self._request_id = str(uuid.uuid4())
        self._request_start: float | None = None
        self._request_start_dt: datetime | None = None
        self._llm_start: float | None = None
        self._llm_start_dt: datetime | None = None
        self._first_chunk_time: float | None = None
        self._first_chunk_dt: datetime | None = None

        self._llm_call_count = 0
        self._total_llm_duration = 0.0
        self._current_llm_start: float | None = None

    @property
    def request_id(self) -> str:
        """Get the request ID for correlation."""
        return self._request_id

    def set_context(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Update context information after tracker creation.

        This method allows setting session_id, user_id, and agent_id after
        the tracker is created, which is useful when this information is
        only available after request routing/processing.

        Args:
            session_id: Session identifier for correlation
            user_id: User identifier for correlation
            agent_id: Agent identifier for correlation
        """
        if session_id is not None:
            self.session_id = session_id
        if user_id is not None:
            self.user_id = user_id
        if agent_id is not None:
            self.agent_id = agent_id

    def start_request(self) -> None:
        """Record start of API request."""
        self._request_start = time.perf_counter()
        self._request_start_dt = datetime.now(timezone.utc)

    def start_llm_call(self) -> None:
        """Record start of an LLM call within the request."""
        now = time.perf_counter()
        if self._llm_start is None:
            self._llm_start = now
            self._llm_start_dt = datetime.now(timezone.utc)
        self._current_llm_start = now

    def end_llm_call(self) -> None:
        """Record end of an LLM call."""
        if self._current_llm_start is not None:
            duration = (time.perf_counter() - self._current_llm_start) * 1000
            self._total_llm_duration += duration
            self._llm_call_count += 1
            self._current_llm_start = None

    def record_first_chunk(self) -> None:
        """Record when first chunk is sent (streaming responses)."""
        if self._first_chunk_time is None and self._request_start is not None:
            self._first_chunk_time = time.perf_counter()
            self._first_chunk_dt = datetime.now(timezone.utc)

    def finish_request(self) -> APITimingData:
        """Finish timing and return complete timing data."""
        request_end = time.perf_counter()
        request_end_dt = datetime.now(timezone.utc)

        total_api_duration_ms = None
        preprocessing_duration_ms = None
        postprocessing_duration_ms = None
        time_to_first_chunk_ms = None

        if self._request_start is not None:
            total_api_duration_ms = (request_end - self._request_start) * 1000

            if self._llm_start is not None:
                preprocessing_duration_ms = (self._llm_start - self._request_start) * 1000

            if self._first_chunk_time is not None:
                time_to_first_chunk_ms = (self._first_chunk_time - self._request_start) * 1000

        if total_api_duration_ms is not None and preprocessing_duration_ms is not None:
            postprocessing_duration_ms = (
                total_api_duration_ms - preprocessing_duration_ms - self._total_llm_duration
            )
            if postprocessing_duration_ms < 0:
                postprocessing_duration_ms = 0

        return APITimingData(
            request_id=self._request_id,
            request_start=self._request_start_dt or datetime.now(timezone.utc),
            request_end=request_end_dt,
            llm_start=self._llm_start_dt,
            llm_end=datetime.now(timezone.utc) if self._llm_call_count > 0 else None,
            first_chunk_sent=self._first_chunk_dt,
            total_api_duration_ms=total_api_duration_ms,
            preprocessing_duration_ms=preprocessing_duration_ms,
            llm_duration_ms=self._total_llm_duration if self._llm_call_count > 0 else None,
            postprocessing_duration_ms=postprocessing_duration_ms,
            time_to_first_chunk_ms=time_to_first_chunk_ms,
            llm_call_count=self._llm_call_count,
            total_llm_duration_ms=self._total_llm_duration,
            endpoint=self.endpoint,
            method=self.method,
            session_id=self.session_id,
            user_id=self.user_id,
            agent_id=self.agent_id,
            is_streaming=self.is_streaming,
        )

    def reset(self) -> None:
        """Reset tracker for reuse."""
        self._request_id = str(uuid.uuid4())
        self._request_start = None
        self._request_start_dt = None
        self._llm_start = None
        self._llm_start_dt = None
        self._first_chunk_time = None
        self._first_chunk_dt = None
        self._llm_call_count = 0
        self._total_llm_duration = 0.0
        self._current_llm_start = None
