"""StreamingPartsAccumulator for consolidating streaming parts.

This module provides the StreamingPartsAccumulator class that accumulates
streaming parts in chronological order and consolidates tool_request + tool_result
into single ActivityOutputPart instances.

The accumulator is designed to be used in both llamaindex_agent.py and base_agent.py
to provide consistent activity consolidation across agent implementations.
"""

from datetime import datetime, timezone
from typing import Any

from agent_framework.core.agent_interface import (
    ActivityOutputPart,
    AgentOutputPartUnion,
    TechnicalDetails,
    TextOutputPart,
)


class StreamingPartsAccumulator:
    """Accumulates streaming parts in chronological order.

    This class tracks pending tool requests and consolidates them with their
    corresponding results into single ActivityOutputPart instances. It maintains
    chronological order of all parts (text and activities) as they are added.

    Key features:
    - Track pending tool requests by call_id
    - Consolidate tool_request + tool_result into single ActivityOutputPart
    - Include TechnicalDetails in consolidated activities
    - Maintain chronological order of all parts
    - Handle edge cases (result without request, multiple requests, etc.)

    Example usage:
        accumulator = StreamingPartsAccumulator()

        # Add text part
        accumulator.add_text("I will search for information...")

        # Add tool request (stored as pending)
        accumulator.add_tool_request(
            call_id="call_123",
            tool_name="search",
            arguments={"query": "python"}
        )

        # Add tool result (consolidates with pending request)
        activity = accumulator.add_tool_result(
            call_id="call_123",
            result="Found 10 results...",
            is_error=False,
            execution_time_ms=150
        )

        # Get all parts in chronological order
        parts = accumulator.get_parts()
    """

    def __init__(self, source: str = "agent") -> None:
        """Initialize the accumulator.

        Args:
            source: The source identifier for activities (e.g., "socrate", "james",
                   "llamaindex_agent"). Defaults to "agent".
        """
        self._parts: list[AgentOutputPartUnion] = []
        self._pending_tool_requests: dict[str, dict[str, Any]] = {}  # call_id -> request data
        self._source = source

    def add_text(self, text: str) -> TextOutputPart:
        """Add text part, preserving order.

        Creates a TextOutputPart and appends it to the parts list in chronological
        order. This ensures text parts maintain their position relative to activities.

        Args:
            text: The text content to add.

        Returns:
            The created TextOutputPart instance.
        """
        part = TextOutputPart(text=text)
        self._parts.append(part)
        return part

    def add_tool_request(
        self,
        call_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        display_info: dict[str, Any] | None = None,
    ) -> None:
        """Store tool request for later consolidation with result.

        The request is stored as pending and will be consolidated with its
        corresponding result when add_tool_result is called with the same call_id.

        Args:
            call_id: Unique identifier for this tool call.
            tool_name: Name of the tool being called.
            arguments: Arguments passed to the tool.
            display_info: Optional display metadata (friendly_name, description, icon).
        """
        self._pending_tool_requests[call_id] = {
            "call_id": call_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "display_info": display_info,
            "request_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def add_tool_result(
        self,
        call_id: str,
        result: str,
        is_error: bool,
        execution_time_ms: int,
        display_info: dict[str, Any] | None = None,
    ) -> ActivityOutputPart:
        """Consolidate with pending request and emit single activity.

        This method looks up the pending request by call_id, consolidates it with
        the result, and creates a single ActivityOutputPart with TechnicalDetails.
        The consolidated activity is appended to the parts list.

        If no pending request is found for the call_id, a standalone activity is
        created with the available result information.

        Args:
            call_id: Unique identifier matching the original tool request.
            result: The result content from the tool execution.
            is_error: Whether the tool execution resulted in an error.
            execution_time_ms: Execution time in milliseconds.
            display_info: Optional display metadata to override request's display_info.

        Returns:
            The created ActivityOutputPart instance.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Look up pending request
        pending_request = self._pending_tool_requests.pop(call_id, None)

        if pending_request:
            tool_name = pending_request["tool_name"]
            arguments = pending_request["arguments"]
            request_display_info = pending_request.get("display_info")
            # Use result's display_info if provided, otherwise fall back to request's
            final_display_info = display_info or request_display_info
        else:
            # No pending request found - create activity with available info
            tool_name = "unknown_tool"
            arguments = {}
            final_display_info = display_info

        # Create TechnicalDetails for Elasticsearch storage
        technical_details = TechnicalDetails(
            function_name=tool_name,
            arguments=arguments,
            raw_result=result,
            execution_time_ms=execution_time_ms,
            timestamp=timestamp,
            status="error" if is_error else "success",
            error_message=result if is_error else None,
        )

        # Create user-friendly content
        if is_error:
            content = f"Erreur lors de l'exécution: {result}"
        else:
            # Truncate long results for display
            if len(result) > 500:
                content = f"{result[:500]}..."
            else:
                content = result

        # Build display_info with defaults if not provided
        if final_display_info is None:
            final_display_info = {
                "id": f"tool_{tool_name}",
                "friendly_name": f"Exécution de {tool_name}",
                "description": f"Appel de l'outil {tool_name}",
                "icon": "🔧",
                "category": "tool",
            }

        # Create consolidated ActivityOutputPart
        activity = ActivityOutputPart(
            activity_type="tool_call",
            source=self._source,
            content=content,
            timestamp=timestamp,
            tools=[{"name": tool_name, "arguments": arguments, "id": call_id}],
            results=[
                {
                    "name": tool_name,
                    "content": result,
                    "is_error": is_error,
                    "call_id": call_id,
                }
            ],
            display_info=final_display_info,
            technical_details=technical_details,
        )

        self._parts.append(activity)
        return activity

    def add_activity(self, activity: ActivityOutputPart) -> None:
        """Add a pre-built ActivityOutputPart directly.

        This method allows adding activities that were created externally,
        such as skill loading or diagram generation activities.

        Args:
            activity: The ActivityOutputPart to add.
        """
        self._parts.append(activity)

    def add_raw_activity(self, activity_dict: dict[str, Any]) -> ActivityOutputPart:
        """Add a raw activity dictionary, converting it to ActivityOutputPart.

        This method provides backward compatibility with code that works with
        raw activity dictionaries.

        Args:
            activity_dict: Raw activity dictionary with keys like 'type', 'source', etc.

        Returns:
            The created ActivityOutputPart instance.
        """
        from agent_framework.core.agent_interface import activity_dict_to_output_part

        activity = activity_dict_to_output_part(activity_dict)
        self._parts.append(activity)
        return activity

    def get_parts(self) -> list[AgentOutputPartUnion]:
        """Get all parts in chronological order.

        Returns a copy of the parts list to prevent external modification.

        Returns:
            A copy of the list of all accumulated parts in chronological order.
        """
        return self._parts.copy()

    def get_pending_requests(self) -> dict[str, dict[str, Any]]:
        """Get pending tool requests that haven't been consolidated yet.

        Returns a copy of the pending requests dictionary.

        Returns:
            A copy of the dictionary mapping call_id to request data.
        """
        return self._pending_tool_requests.copy()

    def has_pending_requests(self) -> bool:
        """Check if there are any pending tool requests.

        Returns:
            True if there are pending requests, False otherwise.
        """
        return len(self._pending_tool_requests) > 0

    def clear(self) -> None:
        """Clear all accumulated parts and pending requests."""
        self._parts.clear()
        self._pending_tool_requests.clear()

    def clear_pending_requests(self) -> None:
        """Clear only pending requests, keeping accumulated parts."""
        self._pending_tool_requests.clear()
