"""
LlamaIndex-Based Agent Implementation

This implementation provides LlamaIndex-specific functionality:
- Session/config handling
- State management via LlamaIndex Context (serialize/deserialize)
- Non-streaming and streaming message processing
- Streaming event formatting aligned with modern UI expectations
- LLM observability with token counting and timing metrics

Note: This implementation constructs a concrete LlamaIndex agent.
Subclasses must implement get_agent_prompt(), get_agent_tools(), and initialize_agent().
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from ..core.activity_formatter import ActivityFormatter
from ..core.agent_interface import (
    ActivityOutputPart,
    AgentConfig,
    StructuredAgentInput,
    StructuredAgentOutput,
    TextOutputPart,
    TextOutputStreamPart,
)
from ..core.base_agent import SKILLS_AVAILABLE, BaseAgent
from ..core.model_clients import client_factory
from ..core.step_display_config import DisplayConfigManager, enrich_event_with_display_info
from ..core.streaming_parts_accumulator import StreamingPartsAccumulator
from ..utils.special_blocks import parse_special_blocks_from_text


# LLM Metrics integration (optional - graceful degradation)
try:
    from ..monitoring import LLMMetrics, LLMMetricsCollector

    LLM_METRICS_AVAILABLE = True
except ImportError:
    LLM_METRICS_AVAILABLE = False
    LLMMetrics = None
    LLMMetricsCollector = None

logger = logging.getLogger(__name__)


class _StreamingActivityAccumulator:
    """Accumulates streaming activities during agent execution.

    Stores the raw JSON dictionaries in the same format as __STREAM_ACTIVITY__ events,
    so they can be replayed by the frontend when loading history from ES.
    """

    def __init__(self) -> None:
        self._activities: list[dict[str, Any]] = []

    def add_activity(self, activity: dict[str, Any]) -> None:
        """Add a raw activity dictionary to the accumulator.

        Args:
            activity: The activity dictionary (same format as __STREAM_ACTIVITY__ events).
        """
        self._activities.append(activity)

    def add_tool_request(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        call_id: str,
        timestamp: str,
        display_info: dict[str, Any] | None = None,
    ) -> None:
        """Add a tool request activity (legacy method for compatibility).

        Creates a raw dict in the same format as __STREAM_ACTIVITY__ tool_request events.
        """
        activity = {
            "type": "tool_request",
            "source": "llamaindex_agent",
            "tools": [{"name": tool_name, "arguments": arguments, "id": call_id}],
            "timestamp": timestamp,
        }
        if display_info:
            activity["display_info"] = display_info
        self._activities.append(activity)

    def add_tool_result(
        self,
        tool_name: str,
        result_content: str,
        is_error: bool,
        call_id: str,
        timestamp: str,
        display_info: dict[str, Any] | None = None,
    ) -> None:
        """Add a tool result activity (legacy method for compatibility).

        Creates a raw dict in the same format as __STREAM_ACTIVITY__ tool_result events.
        """
        activity = {
            "type": "tool_result",
            "source": "llamaindex_agent",
            "results": [
                {
                    "name": tool_name,
                    "content": result_content,
                    "is_error": is_error,
                    "call_id": call_id,
                }
            ],
            "timestamp": timestamp,
        }
        if display_info:
            activity["display_info"] = display_info
        self._activities.append(activity)

    def get_activities(self) -> list[dict[str, Any]]:
        """Return a copy of the accumulated activities.

        Returns:
            A copy of the list of accumulated activity dictionaries.
        """
        return self._activities.copy()

    def get_parts(self) -> list[dict[str, Any]]:
        """Alias for get_activities() for backward compatibility."""
        return self.get_activities()

    def clear(self) -> None:
        """Clear all accumulated activities."""
        self._activities.clear()


class LlamaIndexAgent(BaseAgent):
    """
    Concrete implementation of BaseAgent for LlamaIndex framework.

    For a complete guide on creating LlamaIndex agents, see:
    - docs/CREATING_AGENTS.md - Comprehensive agent creation guide
    - examples/simple_agent.py - Basic LlamaIndex agent example
    - examples/agent_with_file_storage.py - Agent with file upload/download
    - examples/agent_with_mcp.py - Agent with MCP server integration
    - docs/TOOLS_AND_MCP_GUIDE.md - Adding tools and MCP servers

    Subclasses must provide:
    - get_agent_prompt() -> str
    - get_agent_tools() -> list[callable]
    - async initialize_agent(model_name: str, system_prompt: str, tools: list[callable], **kwargs) -> None
    - create_fresh_context() -> Any
    - serialize_context(ctx: Any) -> dict[str, Any]
    - deserialize_context(state: dict[str, Any]) -> Any
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        default_model: str | None = None,
        metrics_enabled: bool | None = None,
        tags: list | None = None,
        image_url: str | None = None,
    ):
        """
        Initialize the LlamaIndex agent with required identity information.

        Args:
            agent_id: Unique identifier for the agent (used for session isolation)
            name: Human-readable name of the agent
            description: Description of the agent's purpose and capabilities
            default_model: Optional default model for backward compatibility.
                          When set, this model will be used if no model_preference
                          is provided in the request, bypassing the ModelRouter.
            metrics_enabled: Optional flag to enable/disable LLM metrics collection.
                            Defaults to True if LLM_METRICS_AVAILABLE, can be overridden
                            via ENABLE_LLM_METRICS environment variable.
            tags: Optional list of tags for categorizing the agent. Can be Tag objects,
                  dicts with 'name' and optional 'color' keys, or strings (name only).
            image_url: Optional URL to an image representing the agent

        Raises:
            ValueError: If agent_id, name, or description is empty
        """
        # LlamaIndex-specific runtime
        self._agent_instance: Any | None = None
        # Memory management
        self._session_storage: Any | None = None
        self._memory_adapter: Any | None = None
        self._current_memory: Any | None = None
        self._current_session_id: str | None = None
        self._current_user_id: str | None = None
        # Model tracking for change detection and backward compatibility
        self._current_model: str | None = None
        self._default_model: str | None = default_model

        # LLM Metrics configuration
        # Priority: constructor arg > env var > default (True if available)
        if metrics_enabled is not None:
            self._metrics_enabled = metrics_enabled
        else:
            env_metrics = os.getenv("ENABLE_LLM_METRICS", "true").lower()
            self._metrics_enabled = env_metrics in ("true", "1", "yes") and LLM_METRICS_AVAILABLE

        # Metrics collector instance (created per-call)
        self._metrics_collector: LLMMetricsCollector | None = None
        # Store last completed metrics for retrieval
        self._last_llm_metrics: LLMMetrics | None = None
        # API timing tracker reference (set by middleware via set_api_timing_tracker)
        self._api_timing_tracker: Any | None = None
        # Display config manager for event enrichment (optional)
        self._display_config_manager: DisplayConfigManager | None = None

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            tags=tags,
            image_url=image_url,
        )

    def create_llm(
        self, model_name: str = None, agent_config: AgentConfig = None, **override_params
    ) -> Any:
        """
        Helper method to create a LlamaIndex LLM using the ModelClientFactory.

        This method simplifies LLM creation in initialize_agent() by handling
        provider-specific imports and parameter compatibility automatically.

        Example usage in initialize_agent():
            llm = self.create_llm(model_name, agent_config)
            self._agent_instance = ReActAgent.from_tools(
                tools=tools,
                llm=llm,
                system_prompt=system_prompt
            )

        Args:
            model_name: Name of the model (e.g., "gpt-4", "claude-3-opus")
            agent_config: Optional agent configuration with overrides
            **override_params: Additional parameters to override defaults

        Returns:
            Configured LlamaIndex LLM instance (OpenAI, Anthropic, or Gemini)
        """
        return client_factory.create_llamaindex_llm(
            model_name=model_name, agent_config=agent_config, **override_params
        )

    def set_session_storage(self, session_storage: Any) -> None:
        """
        Set the session storage backend for memory management.

        This should be called by the server/framework to provide access
        to conversation history for memory loading.

        Args:
            session_storage: SessionStorageInterface instance
        """
        self._session_storage = session_storage
        if session_storage:
            from .llamaindex_memory_adapter import LlamaIndexMemoryAdapter

            self._memory_adapter = LlamaIndexMemoryAdapter(session_storage)

    async def _load_memory_for_session(
        self, session_id: str, user_id: str, model_name: str | None = None
    ) -> Any | None:
        """
        Load memory for a specific session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            model_name: Optional model name for model-specific caching.
                       When provided, ensures proper tokenization for the model.

        Returns:
            Memory object or None if not available
        """
        if not self._memory_adapter:
            logger.debug("No memory adapter available, memory disabled")
            return None

        try:
            memory = await self._memory_adapter.get_memory_for_session(
                session_id=session_id, user_id=user_id, model_name=model_name
            )
            logger.info(
                f"Loaded memory for session {session_id} (model: {model_name or 'default'})"
            )
            return memory
        except Exception as e:
            logger.error(f"Failed to load memory for session {session_id}: {e}")
            return None

    # ----- Abstract hooks to implement in subclass -----
    def get_agent_prompt(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def get_agent_tools(self) -> list[callable]:  # pragma: no cover - abstract
        raise NotImplementedError

    def _convert_to_function_tools(self, tools: list[callable]) -> list[Any]:
        """
        Convert callable tools to LlamaIndex FunctionTool instances.

        This ensures proper tool registration with:
        - Function name as tool name
        - Function docstring as tool description
        - Proper parameter schema inference

        Args:
            tools: List of callable functions to convert

        Returns:
            List of FunctionTool instances
        """
        from llama_index.core.tools import FunctionTool

        function_tools = []
        for tool in tools:
            if isinstance(tool, FunctionTool):
                # Already a FunctionTool, use as-is
                function_tools.append(tool)
            elif callable(tool):
                # Convert callable to FunctionTool
                tool_name = getattr(tool, "__name__", "unknown_tool")
                tool_description = getattr(tool, "__doc__", None) or f"Tool: {tool_name}"

                function_tool = FunctionTool.from_defaults(
                    fn=tool, name=tool_name, description=tool_description.strip()
                )
                function_tools.append(function_tool)
                logger.debug(
                    f"Converted tool '{tool_name}' to FunctionTool with description: {tool_description[:100]}..."
                )
            else:
                logger.warning(f"Skipping non-callable tool: {tool}")

        logger.info(f"Converted {len(function_tools)} tools to FunctionTool instances")
        return function_tools

    async def initialize_agent(
        self, model_name: str, system_prompt: str, tools: list[callable], **kwargs
    ) -> None:
        """
        Initialize the LlamaIndex agent with FunctionAgent (default implementation).

        This default implementation creates a FunctionAgent with the provided tools.
        Tools are automatically converted to FunctionTool instances with proper
        names and descriptions extracted from the function metadata.

        Subclasses can override this method to use different agent types or configurations.

        Default implementation:
            - Creates LLM using self.create_llm()
            - Converts tools to FunctionTool instances
            - Creates FunctionAgent with tools and system prompt
            - Stores agent in self._agent_instance

        To customize, override this method in your subclass:
            async def initialize_agent(self, model_name, system_prompt, tools, **kwargs):
                llm = self.create_llm(model_name)
                # Create your custom agent type
                self._agent_instance = YourCustomAgent(...)

        Args:
            model_name: Name of the model to use
            system_prompt: System prompt for the agent
            tools: List of callable tools for the agent (will be converted to FunctionTool)
            **kwargs: Additional configuration options
        """
        from llama_index.core.agent.workflow import FunctionAgent

        # Use the helper method to create LLM with automatic provider detection
        llm = self.create_llm(model_name)

        # Convert callable tools to FunctionTool instances
        function_tools = self._convert_to_function_tools(tools)

        # Create FunctionAgent with the FunctionTool instances
        self._agent_instance = FunctionAgent(
            tools=function_tools,
            llm=llm,
            system_prompt=system_prompt,
            verbose=kwargs.get("verbose", True),
        )

        logger.info(f"Initialized FunctionAgent with {len(function_tools)} FunctionTool(s)")

        # Provide default implementation of _run_agent_stream_internal for FunctionAgent
        # Subclasses can override if they use a different agent type
        if not hasattr(self, "_run_agent_stream_internal_impl"):
            self._run_agent_stream_internal_impl = self._default_run_agent_stream

    def _default_run_agent_stream(self, query: str, ctx: Any, **kwargs) -> Any:
        """
        Default implementation for running FunctionAgent with memory support.

        Args:
            query: User query
            ctx: Context object
            **kwargs: Additional arguments including optional 'memory'
        """
        # Extract memory if provided
        memory = kwargs.get("memory")

        # Run agent with or without memory
        if memory:
            return self._agent_instance.run(
                user_msg=query, ctx=ctx, memory=memory, max_iterations=50
            )
        else:
            return self._agent_instance.run(user_msg=query, ctx=ctx, max_iterations=50)

    def create_fresh_context(self) -> Any:
        """
        Create a fresh LlamaIndex Context.

        Default implementation works for standard LlamaIndex agents.
        Override only if you need custom context initialization.

        Returns:
            Fresh Context instance for the agent
        """
        from llama_index.core.workflow import Context

        return Context(self._agent_instance)

    def serialize_context(self, ctx: Any) -> dict[str, Any]:
        """
        Serialize the context for state persistence.

        Default implementation uses JsonSerializer for standard LlamaIndex contexts.
        Override only if you need custom serialization logic.

        Args:
            ctx: Context object to serialize

        Returns:
            Dictionary representation of the context
        """
        from llama_index.core.workflow import JsonSerializer

        return ctx.to_dict(serializer=JsonSerializer())

    def deserialize_context(self, state: dict[str, Any]) -> Any:
        """
        Deserialize the context from saved state.

        Default implementation uses JsonSerializer for standard LlamaIndex contexts.
        Override only if you need custom deserialization logic.

        Args:
            state: Dictionary representation of the context

        Returns:
            Restored Context instance
        """
        from llama_index.core.workflow import Context, JsonSerializer

        return Context.from_dict(self._agent_instance, state, serializer=JsonSerializer())

    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """
        Configure session and load memory for the session.

        This override loads conversation history from SessionStorage
        when the session changes.

        Args:
            session_configuration: Configuration dict with user_id, session_id, etc.
        """
        # Extract session info
        user_id = session_configuration.get("user_id")
        session_id = session_configuration.get("session_id")

        # Check if session changed (before updating current values)
        session_changed = session_id != self._current_session_id or user_id != self._current_user_id

        # ALWAYS update user_id and session_id when provided
        # This fixes the bug where user_id was only updated when session_changed was True,
        # causing Graphiti to use 'default_user' for group_id isolation
        if user_id:
            self._current_user_id = user_id
            logger.debug(f"📝 Updated _current_user_id to: {user_id}")
        if session_id:
            self._current_session_id = session_id

        if session_changed and session_id and user_id:
            logger.info(f"🔄 Session changed to {session_id} for user {user_id}, loading memory")

            # Load memory for this session (with model if available)
            self._current_memory = await self._load_memory_for_session(
                session_id, user_id, self._current_model
            )
            if self._current_memory:
                logger.info(f"✅ Memory loaded successfully for session {session_id}")
            else:
                logger.warning(f"⚠️ No memory loaded for session {session_id}")

        # Call parent configure_session
        await super().configure_session(session_configuration)

    async def configure_session_with_model(
        self,
        session_configuration: dict[str, Any],
        model_name: str,
    ) -> None:
        """
        Configure session with a specific model, handling model changes.

        This method extends configure_session to handle model changes mid-session.
        When the model changes, it invalidates the memory cache, rebuilds the agent
        with the new model, and reloads conversation history from SessionStorage.

        Args:
            session_configuration: Configuration dict with user_id, session_id, etc.
            model_name: The model to use for this session
        """
        user_id = session_configuration.get("user_id")
        session_id = session_configuration.get("session_id")

        # Detect model change
        model_changed = self._current_model != model_name

        if model_changed:
            logger.info(
                f"🔄 Model change: {self._current_model} → {model_name} for session {session_id}"
            )
            # Clear current memory to force reload with new model
            self._current_memory = None

        # Update current model
        self._current_model = model_name

        # Add model_name to session_configuration so configure_session rebuilds the agent
        config_with_model = {**session_configuration, "model_name": model_name}

        # Call the standard configure_session which handles:
        # - Session changes and memory loading
        # - Agent rebuild when model_name is in config (sets _agent_built = False)
        await self.configure_session(config_with_model)

        # If model changed, ensure memory is reloaded with fresh tokenization
        if model_changed and session_id and user_id:
            self._current_memory = await self._load_memory_for_session(
                session_id, user_id, model_name
            )
            if self._current_memory:
                logger.info(f"✅ Memory reloaded for session {session_id} with model {model_name}")

    async def set_model_for_session(self, session_id: str, model_name: str) -> None:
        """
        Set the model for a session (called by server before streaming).

        This is a simplified version that just updates _current_model without
        full session reconfiguration. Used by the streaming endpoint to ensure
        get_current_model() returns the correct value.

        Args:
            session_id: The session ID
            model_name: The model name to set
        """
        if model_name and model_name != self._current_model:
            logger.info(f"🔄 Setting model to {model_name} for session {session_id}")
            self._current_model = model_name

    async def get_current_model(self, session_id: str = None) -> str | None:
        """
        Get the current model being used by this agent.

        Args:
            session_id: Optional session ID (for interface compatibility)

        Returns:
            The current model name, or None if not set
        """
        return self._current_model

    def get_default_model(self) -> str | None:
        """
        Get the default model configured for this agent (backward compatibility).

        Returns:
            The default model name, or None if not configured
        """
        return self._default_model

    def get_llm_metrics(self) -> LLMMetrics | None:
        """
        Get the most recent LLM metrics from the last completed call.

        Returns:
            LLMMetrics from the last handle_message or handle_message_stream call,
            or None if metrics collection is disabled or no call has been made.

        Example:
            ```python
            response = await agent.handle_message(session_id, input)
            metrics = agent.get_llm_metrics()
            if metrics:
                print(f"Total tokens: {metrics.total_tokens}")
                print(f"Duration: {metrics.duration_ms}ms")
            ```
        """
        return self._last_llm_metrics

    def set_api_timing_tracker(self, tracker: Any) -> None:
        """
        Set the API timing tracker for correlation with LLM metrics.

        This method is called by the API layer to pass the request's timing
        tracker to the agent, enabling correlation between API-level timing
        and LLM-level metrics.

        Args:
            tracker: APITimingTracker instance from the request middleware
        """
        self._api_timing_tracker = tracker

    def set_display_config_manager(self, manager: DisplayConfigManager | None) -> None:
        """Set the display config manager for event enrichment.

        This method is called by the server/framework to provide access
        to display configuration for enriching streaming events with
        friendly names and icons.

        Args:
            manager: DisplayConfigManager instance, or None to disable enrichment.
        """
        self._display_config_manager = manager

    def _enrich_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Enrich an event with display info if manager is available.

        This method adds display metadata to streaming events, enabling
        frontends to render user-friendly names and icons. The enrichment
        is optional and gracefully degrades if no manager is configured.

        Args:
            event: The streaming event dictionary to enrich.

        Returns:
            The enriched event dictionary with display_info added,
            or the original event if no manager is available.
        """
        if self._display_config_manager is not None:
            return enrich_event_with_display_info(
                event, self._display_config_manager, agent_id=self.agent_id
            )
        return event

    def _create_metrics_collector(self) -> LLMMetricsCollector | None:
        """
        Create a new metrics collector for an LLM call.

        Returns:
            LLMMetricsCollector instance if metrics are enabled, None otherwise.
        """
        if not self._metrics_enabled or not LLM_METRICS_AVAILABLE:
            return None

        # Get API request ID for correlation if available
        api_request_id = None
        if self._api_timing_tracker:
            api_request_id = getattr(self._api_timing_tracker, "request_id", None)
            # Notify API timing tracker that LLM call is starting
            if hasattr(self._api_timing_tracker, "start_llm_call"):
                self._api_timing_tracker.start_llm_call()

        return LLMMetricsCollector(
            model_name=self._current_model,
            session_id=self._current_session_id,
            user_id=self._current_user_id,
            agent_id=self.agent_id,
            enabled=True,
            api_request_id=api_request_id,
        )

    def _finish_metrics_collection(self) -> LLMMetrics | None:
        """
        Finish metrics collection, notify API timing tracker, and record to OTel.

        Returns:
            LLMMetrics from the completed collection, or None if not collecting.
        """
        if not self._metrics_collector:
            return None

        metrics = self._metrics_collector.finish()

        # Notify API timing tracker that LLM call ended
        if self._api_timing_tracker and hasattr(self._api_timing_tracker, "end_llm_call"):
            self._api_timing_tracker.end_llm_call()

        # Note: Metrics are recorded through ObservabilityManager in agent_provider.py
        # via get_llm_metrics() with the proper api_context for accurate aggregation.
        # We don't call _record_metrics_to_otel here to avoid double recording
        # and to ensure metrics are properly associated with the API request context.

        return metrics

    def _record_metrics_to_otel(self, metrics: LLMMetrics) -> None:
        """
        Record LLM metrics through ObservabilityManager for OTel pipeline.

        This ensures metrics flow through the unified OTel observability stack,
        enabling export to Prometheus, Elasticsearch, and other backends.

        Args:
            metrics: LLMMetrics from a completed LLM call
        """
        try:
            from ..monitoring.observability_manager import get_observability_manager

            obs_manager = get_observability_manager()
            obs_manager.record_llm_call(metrics)
            logger.debug(
                f"📊 Recorded LLM metrics to OTel: "
                f"model={metrics.model_name}, "
                f"tokens={metrics.total_tokens}"
            )
        except ImportError:
            logger.debug("ObservabilityManager not available, skipping OTel metrics recording")
        except Exception as e:
            logger.warning(f"Failed to record LLM metrics to OTel: {e}")

    async def _update_session_llm_stats(self, metrics: LLMMetrics) -> None:
        """
        Update session LLM statistics with metrics from a completed LLM call.

        This method updates the cumulative LLM stats in the session storage
        for tracking usage per session.

        Args:
            metrics: LLMMetrics from a completed LLM call
        """
        if not self._session_storage or not metrics:
            return

        if not self._current_user_id or not self._current_session_id:
            logger.debug("Cannot update session LLM stats: missing user_id or session_id")
            return

        try:
            metrics_dict = {
                "input_tokens": metrics.input_tokens,
                "thinking_tokens": metrics.thinking_tokens,
                "output_tokens": metrics.output_tokens,
                "duration_ms": metrics.duration_ms or 0.0,
            }

            success = await self._session_storage.update_session_llm_stats(
                user_id=self._current_user_id,
                session_id=self._current_session_id,
                metrics=metrics_dict,
            )

            if success:
                logger.debug(
                    f"📊 Updated session LLM stats for {self._current_session_id}: "
                    f"+{metrics.total_tokens} tokens"
                )
            else:
                logger.warning(f"Failed to update session LLM stats for {self._current_session_id}")
        except Exception as e:
            logger.error(f"Error updating session LLM stats: {e}")

    async def run_agent(self, query: str, ctx: Any, stream: bool = False) -> str | AsyncGenerator:
        """
        Execute the LlamaIndex agent with a query.

        Args:
            query: The user query to process
            ctx: The LlamaIndex Context object for conversation history
            stream: Whether to return streaming results

        Returns:
            If stream=False: Returns the final response as a string
            If stream=True: Returns an AsyncGenerator that yields LlamaIndex streaming events
        """
        if not self._agent_instance:
            raise RuntimeError("Agent not initialized. Call initialize_agent first.")

        # Pass memory to the agent run if available
        run_kwargs = {}
        if self._current_memory:
            # Sanitize memory before use for cross-provider compatibility
            # This handles Anthropic → OpenAI and vice versa transitions
            if self._memory_adapter:
                # Detect target provider from current model
                target_provider = self._get_provider_for_model(self._current_model)
                self._memory_adapter.sanitize_memory_buffer(
                    self._current_memory, target_provider=target_provider
                )
            run_kwargs["memory"] = self._current_memory

        # Get the streaming handler from subclass
        handler = self._run_agent_stream_internal(query, ctx, **run_kwargs)

        if stream:
            # Return an async generator that yields events from the handler
            return self._stream_events_wrapper(handler)
        else:
            # Use streaming runner but await the final result
            final_response = await handler
            return str(final_response)

    def _get_provider_for_model(self, model_name: str | None) -> str | None:
        """
        Detect the provider for a given model name.

        Args:
            model_name: The model name (e.g., 'gpt-4o', 'claude-3-opus')

        Returns:
            Provider name ('openai', 'anthropic', 'gemini') or None if unknown
        """
        if not model_name:
            return None

        model_lower = model_name.lower()

        # OpenAI patterns
        if any(p in model_lower for p in ["gpt", "o1-", "o3-"]):
            return "openai"

        # Anthropic patterns
        if "claude" in model_lower:
            return "anthropic"

        # Gemini patterns
        if any(p in model_lower for p in ["gemini", "bison", "gecko"]):
            return "gemini"

        return None

    def _run_agent_stream_internal(self, query: str, ctx: Any, **kwargs) -> Any:
        """
        Internal method to run the agent in streaming mode.

        This method should be implemented by subclasses to return a handler
        that has both stream_events() method and is awaitable for the final result.

        Args:
            query: The user query
            ctx: The context object
            **kwargs: Additional arguments (e.g., memory=Memory object)

        Returns:
            A handler object with stream_events() method and awaitable for final response.
        """
        # Use default implementation if available (set by initialize_agent)
        if hasattr(self, "_run_agent_stream_internal_impl"):
            return self._run_agent_stream_internal_impl(query, ctx, **kwargs)

        raise NotImplementedError("Subclasses must implement _run_agent_stream_internal")

    async def _stream_events_wrapper(self, handler: Any) -> AsyncGenerator:
        """
        Wrapper to yield events from the LlamaIndex handler's stream_events() method.

        Args:
            handler: The LlamaIndex streaming handler

        Yields:
            LlamaIndex streaming events
        """
        async for event in handler.stream_events():
            yield event

    async def process_streaming_event(self, event: Any) -> dict[str, Any] | None:
        """
        Convert LlamaIndex streaming events to unified format.

        Args:
            event: LlamaIndex streaming event (AgentStream, ToolCallResult, etc.)

        Returns:
            Dictionary in unified format, or None if event should be skipped.
        """
        try:
            event_type = type(event).__name__

            # Token deltas
            if event_type == "AgentStream":
                chunk = getattr(event, "delta", "")
                if chunk:
                    return {
                        "type": "chunk",
                        "content": chunk,
                        "metadata": {
                            "source": "llamaindex_agent",
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                return None

            # Tool results (emit request first so UI shows arguments)
            if event_type == "ToolCallResult":
                tool_name = getattr(event, "tool_name", "unknown_tool")
                tool_kwargs = getattr(event, "tool_kwargs", {})
                call_id = getattr(event, "call_id", "unknown")
                tool_output = str(getattr(event, "tool_output", ""))

                # First emit tool call
                tool_call_event = {
                    "type": "tool_call",
                    "content": "",
                    "metadata": {
                        "source": "llamaindex_agent",
                        "tool_name": tool_name,
                        "tool_arguments": tool_kwargs,
                        "call_id": call_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                }

                # Then emit tool result
                tool_result_event = {
                    "type": "tool_result",
                    "content": tool_output,
                    "metadata": {
                        "source": "llamaindex_agent",
                        "tool_name": tool_name,
                        "call_id": call_id,
                        "is_error": False,
                        "timestamp": datetime.now().isoformat(),
                    },
                }

                # Return tool call first (result will be handled separately)
                # Note: This is a simplification - in practice, we'd need to yield both
                return tool_call_event

            # AgentOutput or lifecycle noise suppression
            if event_type in {"AgentOutput"}:
                return None

            # Agent loop started marker
            if event_type in {"AgentInput", "InputEvent"}:
                return {
                    "type": "activity",
                    "content": "Agent loop started",
                    "metadata": {
                        "source": "llamaindex_agent",
                        "timestamp": datetime.now().isoformat(),
                    },
                }

            # Suppress lifecycle events
            if event_type in {"StopEvent", "StartEvent"}:
                return None

            # Fallback: concise other event
            event_str = str(event)
            if len(event_str) > 800 or "ChatMessage(" in event_str or "tool_kwargs=" in event_str:
                content = event_type
            else:
                content = event_str

            return {
                "type": "activity",
                "content": content,
                "metadata": {
                    "source": "llamaindex_agent",
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Failed to process streaming event: {e}")
            return {
                "type": "error",
                "content": f"Failed to serialize event: {e}",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                },
            }

    async def handle_message(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> StructuredAgentOutput:
        """
        Handle a user message in non-streaming mode with LLM metrics collection.

        This override adds metrics collection around the parent's handle_message implementation.

        Metrics collected:
        - Input tokens (from query and system prompt)
        - Output tokens (from response)
        - Total duration
        """
        if not agent_input.query:
            return StructuredAgentOutput(response_text="Input query cannot be empty.", parts=[])

        # Initialize metrics collector for this call
        self._metrics_collector = self._create_metrics_collector()
        if self._metrics_collector:
            self._metrics_collector.start()
            # Count input tokens (query + file content)
            full_query = self._build_full_query(agent_input)
            self._metrics_collector.count_input(full_query)
            logger.debug("📊 Started metrics collection for non-streaming call")

        try:
            # Call parent's handle_message
            result = await super().handle_message(session_id, agent_input)

            # Finalize metrics collection
            if self._metrics_collector:
                # Count output tokens from response
                if result.response_text:
                    self._metrics_collector.count_output(result.response_text)

                # Finish and store metrics (also notifies API timing tracker)
                self._last_llm_metrics = self._finish_metrics_collection()
                if self._last_llm_metrics:
                    # Update session LLM stats
                    await self._update_session_llm_stats(self._last_llm_metrics)

            return result

        finally:
            # Ensure collector is cleaned up
            self._metrics_collector = None

    async def handle_message_stream(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> AsyncGenerator[StructuredAgentOutput, None]:
        """
        Handle a user message in streaming mode with LlamaIndex-specific event handling.

        This override preserves the original LlamaIndex streaming behavior from LlamaIndexBasedAgent
        and adds LLM metrics collection for observability.

        Metrics collected:
        - Input tokens (from query and system prompt)
        - Output tokens (from streamed response)
        - Thinking tokens (from tool calls and intermediate reasoning)
        - Time to first token
        - Total duration
        - Tool call execution times
        """
        if not agent_input.query:
            yield StructuredAgentOutput(response_text="Input query cannot be empty.", parts=[])
            return

        await self._async_ensure_agent_built()

        ctx = self._state_ctx or self.create_fresh_context()

        # Build full query including file content from parts (same as non-streaming)
        full_query = self._build_full_query(agent_input)

        # Initialize metrics collector for this call
        self._metrics_collector = self._create_metrics_collector()
        if self._metrics_collector:
            self._metrics_collector.start()
            # Count input tokens (query + system prompt approximation)
            self._metrics_collector.count_input(full_query)
            logger.debug("📊 Started metrics collection for streaming call")

        # Initialize activity accumulator for persistence with consolidation support
        activity_accumulator = StreamingPartsAccumulator(source=self.name or "llamaindex_agent")
        activity_formatter = ActivityFormatter(
            source=self.name or "llamaindex_agent",
            display_config_manager=self._display_config_manager,
            agent_id=self.agent_id,
        )

        # Pass memory to the agent run if available
        run_kwargs = {}
        if self._current_memory:
            # Sanitize memory before use for cross-provider compatibility
            # This handles Anthropic → OpenAI and vice versa transitions
            if self._memory_adapter:
                # Detect target provider from current model
                target_provider = self._get_provider_for_model(self._current_model)
                self._memory_adapter.sanitize_memory_buffer(
                    self._current_memory, target_provider=target_provider
                )
            run_kwargs["memory"] = self._current_memory

        handler = self._run_agent_stream_internal(full_query, ctx, **run_kwargs)

        agent_loop_started_emitted = False
        first_token_recorded = False
        output_chunks: list[str] = []

        # === RICH CONTENT STREAMING BUFFER ===
        # Accumulate chunks to validate rich content blocks before sending
        import re

        pending_buffer = ""
        validated_output_parts: list[str] = []  # Track validated content for final response
        # Pattern matches opening marker, then content until closing ``` on its own line
        RICH_CONTENT_PATTERN = re.compile(
            r"^[ \t]*```(mermaid|chart|chartjs|tabledata)\s*\n(.*?)^[ \t]*```",
            re.DOTALL | re.MULTILINE,
        )

        async for event in handler.stream_events():
            # Token deltas
            if getattr(event, "__class__", type("", (), {})).__name__ == "AgentStream":
                chunk = getattr(event, "delta", "")
                if chunk:
                    # Record time to first token on first chunk
                    if not first_token_recorded and self._metrics_collector:
                        self._metrics_collector.record_first_token()
                        first_token_recorded = True

                    # Collect output chunks for token counting
                    output_chunks.append(chunk)
                    pending_buffer += chunk

                    # Process buffer for rich content blocks
                    while True:
                        match = RICH_CONTENT_PATTERN.search(pending_buffer)
                        if match:
                            # Send text before the block
                            before = pending_buffer[: match.start()]
                            if before:
                                validated_output_parts.append(before)
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{before}")],
                                )
                            # Validate and send the block
                            block = match.group(0)
                            try:
                                from ..processing.rich_content_validation import (
                                    validate_rich_content,
                                )

                                validated = validate_rich_content(block)
                                validated_output_parts.append(validated)
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[
                                        TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")
                                    ],
                                )
                            except Exception as e:
                                logger.warning(f"Rich content streaming validation: {e}")
                                validated_output_parts.append(block)
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{block}")],
                                )
                            pending_buffer = pending_buffer[match.end() :]
                        else:
                            # Check if inside an open block (marker found but not closed)
                            has_open_block = False
                            for marker in ("```mermaid", "```chart", "```chartjs", "```tabledata"):
                                marker_pos = pending_buffer.find(marker)
                                if marker_pos >= 0:
                                    after_marker = pending_buffer[marker_pos:]
                                    # Check if there's a closing ``` on its own line after the opening
                                    lines_after = after_marker.split("\n")[1:]  # Skip opening line
                                    has_closing = any(line.strip() == "```" for line in lines_after)
                                    if not has_closing:
                                        has_open_block = True
                                        break

                            if not has_open_block and len(pending_buffer) > 20:
                                # Safe to send - keep last 20 chars for partial markers
                                to_send = pending_buffer[:-20]
                                pending_buffer = pending_buffer[-20:]
                                validated_output_parts.append(to_send)
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{to_send}")],
                                )
                            break
                continue

            # Tool results - CONSOLIDATED: emit single tool_call activity instead of separate request/result
            if getattr(event, "__class__", type("", (), {})).__name__ == "ToolCallResult":
                # FLUSH pending_buffer BEFORE emitting tool activity
                # This ensures text is fully emitted before the activity part
                if pending_buffer:
                    try:
                        from ..processing.rich_content_validation import validate_rich_content

                        validated = validate_rich_content(pending_buffer)
                        validated_output_parts.append(validated)
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")],
                        )
                    except Exception as e:
                        logger.warning(f"Rich content flush before tool call: {e}")
                        validated_output_parts.append(pending_buffer)
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")],
                        )
                    pending_buffer = ""

                tool_name = getattr(event, "tool_name", "unknown_tool")
                tool_kwargs = getattr(event, "tool_kwargs", {})
                call_id = getattr(event, "call_id", "unknown")
                tool_output = str(getattr(event, "tool_output", ""))

                # Track tool call timing
                if self._metrics_collector:
                    # End the tool call timing (started when tool_request was emitted)
                    self._metrics_collector.end_tool_call(call_id)

                    # Count tool call tokens (function name + arguments) as thinking tokens
                    tool_call_data = [
                        {
                            "function": {
                                "name": tool_name,
                                "arguments": (
                                    json.dumps(tool_kwargs)
                                    if isinstance(tool_kwargs, dict)
                                    else str(tool_kwargs)
                                ),
                            }
                        }
                    ]
                    self._metrics_collector.count_tool_call_tokens(tool_call_data)

                # Count tool output as thinking tokens
                if self._metrics_collector and tool_output:
                    self._metrics_collector.count_thinking(tool_output)

                # Calculate execution time (approximate - we don't have exact timing here)
                execution_time_ms = 0

                # Use ActivityFormatter to create consolidated activity with specific friendly_name
                # Special handling for skill loading tools to use format_skill_loading()
                if tool_name in ("load_skill", "load_skill_tool"):
                    skill_name = tool_kwargs.get("skill_name", "unknown")

                    # Get skill from registry to access display metadata
                    skill = (
                        self._skill_registry.get(skill_name)
                        if hasattr(self, "_skill_registry")
                        else None
                    )

                    display_name = skill.display_name if skill else skill_name
                    display_icon = skill.display_icon if skill else "📥"
                    skill_description = skill.metadata.description if skill else ""

                    activity_part = activity_formatter.format_skill_loading(
                        skill_name=skill_name,
                        skill_description=skill_description,
                        loaded_prompt=tool_output,
                        execution_time_ms=execution_time_ms,
                        display_name=display_name,
                        display_icon=display_icon,
                    )
                # Special handling for diagram generation to use format_diagram_generation()
                elif tool_name == "save_mermaid_as_image":
                    mermaid_code = tool_kwargs.get("mermaid_code", "")
                    file_name = tool_kwargs.get("file_name", "diagram.png")

                    # Extract diagram type from mermaid code (first line usually indicates type)
                    # e.g., "gantt", "flowchart", "sequenceDiagram", etc.
                    diagram_type = "unknown"
                    if mermaid_code:
                        first_line = mermaid_code.strip().split("\n")[0].lower()
                        for dtype in [
                            "gantt",
                            "mindmap",
                            "flowchart",
                            "sequence",
                            "class",
                            "state",
                            "er",
                            "pie",
                            "journey",
                            "quadrant",
                            "architecture",
                        ]:
                            if dtype in first_line:
                                diagram_type = dtype
                                break

                    activity_part = activity_formatter.format_diagram_generation(
                        diagram_type=diagram_type,
                        file_name=file_name,
                        content=mermaid_code,
                        execution_time_ms=execution_time_ms,
                    )
                # Special handling for chart generation to use format_chart_generation()
                elif tool_name == "save_chart_as_image":
                    chart_config = tool_kwargs.get("chart_config", {})
                    file_name = tool_kwargs.get("file_name", "chart.png")

                    # Extract chart type from config
                    chart_type = "unknown"
                    if isinstance(chart_config, dict):
                        chart_type = chart_config.get("type", "unknown")
                    elif isinstance(chart_config, str):
                        # Try to parse JSON string
                        try:
                            config = json.loads(chart_config)
                            chart_type = config.get("type", "unknown")
                        except (json.JSONDecodeError, TypeError):
                            pass

                    # Convert chart_config to string for content if it's a dict
                    content = (
                        json.dumps(chart_config, indent=2)
                        if isinstance(chart_config, dict)
                        else str(chart_config)
                    )

                    activity_part = activity_formatter.format_chart_generation(
                        chart_type=chart_type,
                        file_name=file_name,
                        content=content,
                        execution_time_ms=execution_time_ms,
                    )
                else:
                    activity_part = activity_formatter.format_tool_execution(
                        tool_name=tool_name,
                        arguments=tool_kwargs,
                        result=tool_output,
                        execution_time_ms=execution_time_ms,
                        is_error=False,
                    )
                # Override source with agent name
                activity_part.source = self.name or "llamaindex_agent"

                # Add to accumulator for persistence
                activity_accumulator.add_activity(activity_part)

                # Create backward-compatible __STREAM_ACTIVITY__ event
                # Use tool_call type for consolidated activity
                tool_call_event = {
                    "type": "tool_call",
                    "source": self.name or "llamaindex_agent",
                    "tools": [{"name": tool_name, "arguments": tool_kwargs, "id": call_id}],
                    "results": [
                        {
                            "name": tool_name,
                            "content": tool_output,
                            "is_error": False,
                            "call_id": call_id,
                        }
                    ],
                    "timestamp": activity_part.timestamp,
                    "display_info": activity_part.display_info,
                }

                yield StructuredAgentOutput(
                    response_text="",
                    parts=[
                        activity_part,  # ActivityOutputPart for order preservation
                        TextOutputStreamPart(
                            text=f"__STREAM_ACTIVITY__{json.dumps(tool_call_event)}"
                        ),  # backward compatibility
                    ],
                )
                agent_loop_started_emitted = False
                continue

            # AgentOutput or lifecycle noise suppression and loop marker
            event_type = type(event).__name__
            if event_type in {"AgentOutput"}:
                continue
            if event_type in {"AgentInput", "InputEvent"}:
                if not agent_loop_started_emitted:
                    loop_activity = {
                        "type": "activity",
                        "source": "agent",
                        "content": "Agent loop started",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    # Enrich with display info
                    loop_activity = self._enrich_event(loop_activity)

                    # Create ActivityOutputPart for order preservation
                    activity_part = ActivityOutputPart(
                        activity_type="activity",
                        source="agent",
                        content="Agent loop started",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        display_info=loop_activity.get("display_info"),
                    )
                    # Accumulate for persistence
                    activity_accumulator.add_activity(activity_part)

                    yield StructuredAgentOutput(
                        response_text="",
                        parts=[
                            activity_part,  # ActivityOutputPart for order preservation
                            TextOutputStreamPart(
                                text=f"__STREAM_ACTIVITY__{json.dumps(loop_activity)}"
                            ),  # backward compatibility
                        ],
                    )
                    agent_loop_started_emitted = True
                continue
            if event_type in {"StopEvent", "StartEvent"}:
                continue

            # Check for tool call start events to track timing
            if event_type == "ToolCall":
                if self._metrics_collector:
                    tool_call_id = getattr(event, "call_id", None) or getattr(
                        event, "id", "unknown"
                    )
                    self._metrics_collector.start_tool_call(tool_call_id)
                # Skip emitting ToolCall as "thought" - it's handled via ToolCallResult
                # which provides the consolidated tool_call activity with both request and result
                continue

            # Map LlamaIndex event types to friendly names
            event_type_friendly_names = {
                "ToolCall": "🔧 Utilisation de l'outil",
                "AgentRunStep": "🤖 Étape de l'agent",
                "LLMChatStart": "💬 Début de conversation LLM",
                "LLMChatEnd": "💬 Fin de conversation LLM",
                "FunctionCall": "📞 Appel de fonction",
                "StreamChatDelta": "📝 Réponse en cours",
            }
            friendly_name = event_type_friendly_names.get(event_type, f"⚙️ {event_type}")

            # Fallback: concise other event
            try:
                event_str = str(event)
                if (
                    len(event_str) > 800
                    or "ChatMessage(" in event_str
                    or "tool_kwargs=" in event_str
                ):
                    other = {
                        "type": "other",
                        "source": "llamaindex_agent",
                        "content": event_type,
                        "event_type": event_type,
                        "friendly_name": friendly_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    other = {
                        "type": "other",
                        "source": "llamaindex_agent",
                        "content": event_str,
                        "event_type": event_type,
                        "friendly_name": friendly_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                # Enrich with display info
                other = self._enrich_event(other)

                # Create ActivityOutputPart for order preservation
                # Use "thought" as activity_type for "other" events (internal agent activity)
                activity_part = ActivityOutputPart(
                    activity_type="thought",
                    source="llamaindex_agent",
                    content=other.get("content"),
                    timestamp=other.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    display_info=other.get("display_info"),
                )
                # Accumulate for persistence
                activity_accumulator.add_activity(activity_part)

                yield StructuredAgentOutput(
                    response_text="",
                    parts=[
                        activity_part,  # ActivityOutputPart for order preservation
                        TextOutputStreamPart(
                            text=f"__STREAM_ACTIVITY__{json.dumps(other)}"
                        ),  # backward compatibility
                    ],
                )
            except Exception as e:
                err = {
                    "type": "error",
                    "content": f"Failed to serialize event: {e}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                # Enrich with display info
                err = self._enrich_event(err)

                # Create ActivityOutputPart for order preservation
                activity_part = ActivityOutputPart(
                    activity_type="error",
                    source="llamaindex_agent",
                    content=f"Failed to serialize event: {e}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    display_info=err.get("display_info"),
                )
                # Accumulate for persistence
                activity_accumulator.add_activity(activity_part)

                yield StructuredAgentOutput(
                    response_text="",
                    parts=[
                        activity_part,  # ActivityOutputPart for order preservation
                        TextOutputStreamPart(
                            text=f"__STREAM_ACTIVITY__{json.dumps(err)}"
                        ),  # backward compatibility
                    ],
                )

        # Flush remaining pending buffer
        if pending_buffer:
            try:
                from ..processing.rich_content_validation import validate_rich_content

                validated = validate_rich_content(pending_buffer)
                validated_output_parts.append(validated)
                yield StructuredAgentOutput(
                    response_text="",
                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")],
                )
            except Exception as e:
                logger.warning(f"Rich content final flush: {e}")
                validated_output_parts.append(pending_buffer)
                yield StructuredAgentOutput(
                    response_text="",
                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")],
                )

        # Final result - use validated content instead of raw LlamaIndex response
        final_response = await handler
        self._state_ctx = ctx
        # Use the validated output that was actually streamed to the client
        final_text = (
            "".join(validated_output_parts) if validated_output_parts else str(final_response)
        )

        # Finalize metrics collection
        if self._metrics_collector:
            # Count output tokens from collected chunks
            full_output = "".join(output_chunks)
            if full_output:
                self._metrics_collector.count_output(full_output)

            # Finish and store metrics (also notifies API timing tracker)
            self._last_llm_metrics = self._finish_metrics_collection()
            if self._last_llm_metrics:
                # Update session LLM stats
                await self._update_session_llm_stats(self._last_llm_metrics)

            self._metrics_collector = None

        # Note: Special blocks (optionsblock, formDefinition, image) are now extracted
        # by consolidate_text_parts() in the server, so we don't parse them here anymore.
        # This avoids duplication when the server consolidates all streamed parts.
        # We still use parse_special_blocks_from_text to get the cleaned text for response_text.
        cleaned, _special_parts = parse_special_blocks_from_text(final_text)

        # Get accumulated activities for persistence
        # Convert ActivityOutputPart objects to dicts for ES storage
        accumulated_parts = activity_accumulator.get_parts()
        accumulated_activities = []
        for part in accumulated_parts:
            if isinstance(part, ActivityOutputPart):
                # Convert to dict format for ES storage
                activity_dict = {
                    "type": part.activity_type,
                    "source": part.source,
                    "timestamp": part.timestamp,
                }
                if part.content:
                    activity_dict["content"] = part.content
                if part.tools:
                    activity_dict["tools"] = part.tools
                if part.results:
                    activity_dict["results"] = part.results
                if part.display_info:
                    activity_dict["display_info"] = part.display_info
                if part.technical_details:
                    activity_dict["technical_details"] = part.technical_details.model_dump()
                accumulated_activities.append(activity_dict)

        # Final result - streaming_activities stored for ES persistence and frontend replay
        # Note: We don't include special blocks in parts here because they are extracted
        # by consolidate_text_parts() in the server from the streamed text chunks.
        # This avoids duplication.
        yield StructuredAgentOutput(
            response_text=cleaned,
            parts=[],  # Empty - special blocks extracted by server's consolidate_text_parts
            streaming_activities=accumulated_activities,
        )

    async def get_metadata(self) -> dict[str, Any]:
        """Return LlamaIndex-specific agent metadata including id, name, and description."""
        tools = self.get_agent_tools()
        tool_list = [
            {
                "name": getattr(t, "__name__", str(t)),
                "description": getattr(t, "__doc__", "Agent tool"),
                "type": "static",
            }
            for t in tools
        ]
        # Check if agent declares file_storage capability:
        # 1. Via has_file_storage attribute/property (explicit declaration)
        # 2. Via file_storage attribute being defined (even if None at init time)
        # 3. Via AgentTool instances requiring file storage
        has_file_storage = getattr(self, "has_file_storage", False)
        if not has_file_storage:
            # Check if agent has file_storage attribute defined (indicates it will use it)
            has_file_storage = "file_storage" in self.__dict__
        if not has_file_storage:
            # Scan agent attributes for AgentTool instances requiring file storage
            for attr_name in dir(self):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(self, attr_name, None)
                if isinstance(attr, (list, tuple)):
                    for item in attr:
                        if hasattr(item, "get_tool_info"):
                            info = item.get_tool_info()
                            if info.get("requires_file_storage", False):
                                has_file_storage = True
                                break
                if has_file_storage:
                    break
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "tags": [{"name": t.name, "color": t.color} for t in self.tags],
            "image_url": self.image_url,
            "capabilities": {
                "streaming": True,
                "tool_use": True,
                "reasoning": True,
                "model_choice": True,
                "multimodal": False,
                "file_storage": has_file_storage,
                "skills": SKILLS_AVAILABLE and self._enable_skills,
                "rich_content": SKILLS_AVAILABLE and self._enable_skills,
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text", "structured"],
            "tools": tool_list,
            "tool_summary": {
                "total_tools": len(tools),
                "static_tools": len(tools),
            },
            "framework": "LlamaIndex",
        }
