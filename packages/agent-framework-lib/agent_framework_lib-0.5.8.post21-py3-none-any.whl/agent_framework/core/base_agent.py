"""
Framework-Agnostic Base Agent Class

This base class provides a generic foundation for AI agents across different frameworks
(LlamaIndex, Microsoft Agent Framework, etc.):
- Session/config handling
- State management via subclass-provided context (serialize/deserialize)
- Non-streaming and streaming message processing
- Streaming event formatting aligned with modern UI expectations
- Special output parsing (charts, forms, structured data)

Note: This base does NOT construct any concrete agent.
Subclasses must implement all abstract methods to provide framework-specific functionality.
"""

from __future__ import annotations

import json
import logging
import os
from abc import abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from ..utils.special_blocks import parse_special_blocks_from_text
from .agent_interface import (
    ActivityOutputPart,
    AgentInterface,
    StructuredAgentInput,
    StructuredAgentOutput,
    TextInputPart,
    TextOutputPart,
    TextOutputStreamPart,
)
from .model_config import model_config
from .models import Tag
from .activity_formatter import ActivityFormatter


# Memory integration (optional)
try:
    from ..memory import MemoryMixin

    MEMORY_AVAILABLE = True
except ImportError:
    # Memory module not installed - create a no-op mixin
    MEMORY_AVAILABLE = False

    class MemoryMixin:
        """No-op mixin when memory module is not available."""

        pass


# Skills integration (optional)
try:
    from ..skills import SkillsMixin

    SKILLS_AVAILABLE = True
except ImportError:
    # Skills module not installed - create a no-op mixin
    SKILLS_AVAILABLE = False

    class SkillsMixin:
        """No-op mixin when skills module is not available."""

        pass


logger = logging.getLogger(__name__)


class BaseAgent(SkillsMixin, MemoryMixin, AgentInterface):
    """
    Abstract base class for framework-agnostic agents.

    Automatically injects skills discovery capabilities into the system prompt,
    allowing agents to dynamically load specialized capabilities (charts, PDFs,
    diagrams, etc.) on-demand. This replaces the previous rich content prompt
    approach with a more token-efficient skills-based system.

    For a complete guide on creating agents with BaseAgent, see:
    - docs/CREATING_AGENTS.md - Comprehensive agent creation guide
    - examples/custom_framework_agent.py - Complete working example
    - docs/TOOLS_AND_MCP_GUIDE.md - Adding tools and MCP servers

    SKILLS SYSTEM
    =============

    The skills system provides on-demand capabilities:
    - Skills are loaded only when needed (token-efficient)
    - Each skill bundles instructions + tools together
    - Agents can discover skills via list_skills() tool
    - Agents can load skills via load_skill() tool

    Token Optimization:
    - Old approach: ~3000 tokens in every system prompt
    - New approach: ~200 tokens in system prompt + ~500 tokens per skill (one-time)

    STREAMING ARCHITECTURE
    ======================

    This class implements a clear separation of concerns for streaming:

    ┌─────────────────────────────────────────────────────────────┐
    │  Custom Framework Agent (Your Implementation)               │
    │                                                             │
    │  run_agent(stream=True)                                     │
    │    └─> Yields RAW framework-specific events                │
    │         (e.g., LlamaIndex events, custom events, etc.)     │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  BaseAgent.handle_message_stream() [FINAL - DO NOT OVERRIDE]│
    │                                                             │
    │  Orchestrates the streaming flow:                           │
    │    1. Calls run_agent(stream=True)                          │
    │    2. For each event, calls process_streaming_event()       │
    │    3. Converts to StructuredAgentOutput                     │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  Custom Framework Agent (Your Implementation)               │
    │                                                             │
    │  process_streaming_event(event)                             │
    │    └─> Converts framework event to unified format          │
    │         Returns: {"type": "chunk", "content": "...", ...}   │
    └─────────────────────────────────────────────────────────────┘

    KEY PRINCIPLE:
    - run_agent() = Framework-specific logic, yields RAW events
    - process_streaming_event() = Conversion layer, framework-specific
    - handle_message_stream() = Orchestration, framework-agnostic (DO NOT OVERRIDE)

    REQUIRED METHODS (must implement in subclass):
    - get_agent_prompt() -> str
    - get_agent_tools() -> List[callable]
    - async initialize_agent(model_name: str, system_prompt: str, tools: List[callable], **kwargs) -> None
    - create_fresh_context() -> Any
    - serialize_context(ctx: Any) -> Dict[str, Any]
    - deserialize_context(state: Dict[str, Any]) -> Any
    - async run_agent(query: str, ctx: Any, stream: bool = False) -> Union[str, AsyncGenerator]

    OPTIONAL METHODS (can be overridden):
    - get_mcp_server_params() -> Optional[Dict[str, Any]]
    - async process_streaming_event(event: Any) -> Optional[Dict[str, Any]]
    - get_model_config() -> Dict[str, Any]

    EXAMPLES AND GUIDES:
    - See examples/custom_framework_agent.py for a complete implementation
    - See docs/CREATING_AGENTS.md for step-by-step guide
    - See docs/TOOLS_AND_MCP_GUIDE.md for tool integration patterns
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        tags: list[Tag] | list[dict[str, str]] | None = None,
        image_url: str | None = None,
    ):
        """
        Initialize the base agent with required identity information.

        Args:
            agent_id: Unique identifier for the agent (used for session isolation)
            name: Human-readable name of the agent
            description: Description of the agent's purpose and capabilities
            tags: Optional list of tags for categorizing the agent. Can be Tag objects,
                  dicts with 'name' and optional 'color' keys, or strings (name only).
                  Tags without colors will have random colors generated.
            image_url: Optional URL to an image representing the agent

        Raises:
            ValueError: If agent_id, name, or description is empty
        """
        # Validate required parameters
        if not agent_id:
            raise ValueError("agent_id is required and cannot be empty")
        if not name:
            raise ValueError("name is required and cannot be empty")
        if not description:
            raise ValueError("description is required and cannot be empty")

        # Agent identity (required)
        self.agent_id: str = agent_id
        self.name: str = name
        self.description: str = description

        # Process tags - convert dicts/strings to Tag objects, generate colors if needed
        self.tags: list[Tag] = []
        if tags:
            for tag in tags:
                if isinstance(tag, Tag):
                    self.tags.append(tag)
                elif isinstance(tag, dict):
                    if "color" in tag:
                        self.tags.append(Tag(name=tag["name"], color=tag["color"]))
                    else:
                        self.tags.append(Tag.from_name(tag["name"]))
                elif isinstance(tag, str):
                    self.tags.append(Tag.from_name(tag))

        # Agent image URL (optional)
        self.image_url: str | None = image_url

        # Session-configurable settings
        self._session_system_prompt: str = self.get_agent_prompt()
        self._session_model_config: dict[str, Any] = {}
        self._session_model_name: str | None = None

        # Skills configuration (enabled by default, respects ENABLE_SKILLS env var)
        env_enable_skills = os.getenv("ENABLE_SKILLS", "true").lower()
        self._enable_skills: bool = env_enable_skills in ("true", "1", "yes")

        # Subclass-managed runtime
        self._agent_built: bool = False
        self._state_ctx: Any | None = None

        # Initialize parent classes (including SkillsMixin and MemoryMixin if available)
        super().__init__()

        # Register built-in skills if skills are enabled
        if SKILLS_AVAILABLE and self._enable_skills:
            try:
                self.register_builtin_skills()
            except Exception as e:
                logger.warning(f"Failed to register built-in skills: {e}")

        # Build the agent via subclass hook
        self._ensure_agent_built()

    # ----- Abstract hooks to implement in subclass -----
    @abstractmethod
    def get_agent_prompt(self) -> str:
        """Return the default system prompt for the agent."""
        raise NotImplementedError

    @abstractmethod
    def get_agent_tools(self) -> list[callable]:
        """Return the list of tools available to the agent."""
        raise NotImplementedError

    @abstractmethod
    async def initialize_agent(
        self, model_name: str, system_prompt: str, tools: list[callable], **kwargs
    ) -> None:
        """Initialize the agent with the underlying framework."""
        raise NotImplementedError

    @abstractmethod
    def create_fresh_context(self) -> Any:
        """Create a new empty context for the agent."""
        raise NotImplementedError

    @abstractmethod
    def serialize_context(self, ctx: Any) -> dict[str, Any]:
        """Serialize context to dictionary for persistence."""
        raise NotImplementedError

    @abstractmethod
    def deserialize_context(self, state: dict[str, Any]) -> Any:
        """Deserialize dictionary to context object."""
        raise NotImplementedError

    @abstractmethod
    async def run_agent(self, query: str, ctx: Any, stream: bool = False) -> str | AsyncGenerator:
        """
        Execute the agent with a query.

        IMPORTANT: This method should yield RAW framework-specific events when streaming.
        The events will be converted to unified format via process_streaming_event().

        Args:
            query: The user query to process
            ctx: The context object for conversation history
            stream: Whether to return streaming results

        Returns:
            If stream=False:
                - MUST return the final response as a string
                - Example: return "The answer is 42"

            If stream=True:
                - MUST return an AsyncGenerator that yields RAW framework events
                - DO NOT convert events to unified format here
                - Events will be converted via process_streaming_event()

        Examples:
            # Non-streaming mode
            async def run_agent(self, query, ctx, stream=False):
                if not stream:
                    response = await my_framework.chat(query, ctx)
                    return response.text

            # Streaming mode - yield RAW framework events
            async def run_agent(self, query, ctx, stream=False):
                if stream:
                    async def event_generator():
                        async for event in my_framework.stream_chat(query, ctx):
                            # Yield the RAW event from your framework
                            # DO NOT convert it here - that happens in process_streaming_event()
                            yield event
                    return event_generator()

        Note:
            - The framework events you yield can be in ANY format your framework uses
            - They will be converted to unified format by process_streaming_event()
            - This separation keeps framework-specific logic isolated
        """
        raise NotImplementedError

    # ----- Optional hooks (can be overridden) -----
    def get_mcp_server_params(self) -> dict[str, Any] | None:
        """
        Return MCP server configuration if MCP tools are needed.

        Returns:
            Dictionary with MCP server parameters, or None if MCP is not used.
        """
        return None

    async def process_streaming_event(self, event: Any) -> dict[str, Any] | None:
        """
        Convert framework-specific streaming events to unified format.

        This method is called by handle_message_stream() for each event yielded
        by run_agent(stream=True). It converts your framework's event format
        into the standard unified format used by the framework.

        Args:
            event: RAW framework-specific streaming event (any type your framework uses)

        Returns:
            Dictionary in unified format, or None to skip this event.

            Unified format structure:
            {
                "type": "chunk" | "tool_call" | "tool_result" | "activity" | "error",
                "content": str,
                "metadata": {...}  # Optional additional data
            }

        Event Types:
            - "chunk": Text content being streamed to the user
            - "tool_call": Agent is calling a tool
            - "tool_result": Result from a tool execution
            - "activity": General activity message (e.g., "thinking", "processing")
            - "error": Error occurred during processing

        Examples:
            # Example 1: LlamaIndex text chunk
            async def process_streaming_event(self, event):
                if hasattr(event, 'delta') and event.delta:
                    return {
                        "type": "chunk",
                        "content": event.delta,
                        "metadata": {"source": "llamaindex"}
                    }
                return None

            # Example 2: Custom framework tool call
            async def process_streaming_event(self, event):
                if event.type == "tool_request":
                    return {
                        "type": "tool_call",
                        "content": "",
                        "metadata": {
                            "tool_name": event.tool_name,
                            "tool_arguments": event.arguments,
                            "call_id": event.id
                        }
                    }
                return None

            # Example 3: OpenAI-style streaming chunk
            async def process_streaming_event(self, event):
                if event.choices and event.choices[0].delta.content:
                    return {
                        "type": "chunk",
                        "content": event.choices[0].delta.content,
                        "metadata": {"model": event.model}
                    }
                return None

            # Example 4: Tool result
            async def process_streaming_event(self, event):
                if event.type == "tool_response":
                    return {
                        "type": "tool_result",
                        "content": str(event.result),
                        "metadata": {
                            "tool_name": event.tool_name,
                            "call_id": event.call_id,
                            "is_error": event.is_error
                        }
                    }
                return None

            # Example 5: Multiple event types
            async def process_streaming_event(self, event):
                # Handle different event types from your framework
                if isinstance(event, MyFrameworkTextChunk):
                    return {
                        "type": "chunk",
                        "content": event.text,
                        "metadata": {}
                    }
                elif isinstance(event, MyFrameworkToolCall):
                    return {
                        "type": "tool_call",
                        "content": "",
                        "metadata": {
                            "tool_name": event.name,
                            "tool_arguments": event.args,
                            "call_id": event.id
                        }
                    }
                # Skip unknown events
                return None

        Note:
            - Return None to skip events you don't want to process
            - The default implementation returns None (skips all events)
            - Override this method to handle your framework's specific event types
            - This method is called automatically by handle_message_stream()
        """
        return None

    def get_model_config(self) -> dict[str, Any]:
        """
        Return default model configuration.

        Returns:
            Dictionary with model configuration parameters (temperature, max_tokens, etc.)
        """
        return {}

    # ----- Internal helpers -----
    def _resolve_model_name(self) -> str:
        """Resolve the model name from session config, environment, or default."""
        # Priority: session model > OPENAI_API_MODEL env var > DEFAULT_MODEL from config
        candidate = (
            self._session_model_name or os.getenv("OPENAI_API_MODEL") or model_config.default_model
        )
        if not candidate:
            # Final fallback if nothing is configured
            return "gpt-4o-mini"
        return candidate

    def _ensure_agent_built(self):
        """Ensure agent is built (synchronous check)."""
        if not self._agent_built:
            # Synchronous wrapper calling async build in a lazy fashion is not ideal;
            # but AgentManager invokes configure_session before first use. We'll rely on build being awaited there.
            # For safety, we expose an async ensure in configure_session.
            pass

    def _get_memory_tools(self) -> list[callable]:
        """
        Get memory tools for this agent.

        Returns:
            List of memory tool instances (FunctionTool for LlamaIndex)
        """
        if not MEMORY_AVAILABLE:
            return []

        if not hasattr(self, "_memory_manager") or not self._memory_manager:
            return []

        try:
            from ..memory import create_memory_tools

            # Create getters for user_id and session_id
            def get_user_id() -> str | None:
                return getattr(self, "_current_user_id", None)

            def get_session_id() -> str | None:
                return getattr(self, "_current_session_id", None)

            # Create memory tools bound to this agent's memory manager
            tools = create_memory_tools(
                memory_manager=self._memory_manager,
                user_id_getter=get_user_id,
                session_id_getter=get_session_id,
                agent_id=self.agent_id,
            )

            return tools

        except Exception as e:
            logger.error(f"Error creating memory tools: {e}")
            return []

    def _get_skill_management_tools(self) -> list[callable]:
        """
        Get skill management tools for this agent.

        Returns:
            List of skill management tools (list_skills, load_skill, unload_skill)
        """
        if not SKILLS_AVAILABLE:
            return []

        if not self._enable_skills:
            return []

        try:
            return self.get_skill_tools()
        except Exception as e:
            logger.error(f"Error creating skill management tools: {e}")
            return []

    async def _get_all_tools(self) -> list[callable]:
        """
        Get all tools including agent-defined tools, skill tools, and memory tools.

        When skills are enabled, ALL registered skill tools are included automatically.
        This ensures tools are available immediately without requiring load_skill() first.

        Tool Loading Order:
        1. Agent's custom tools (from get_agent_tools())
        2. Skill management tools (list_skills, load_skill, unload_skill)
        3. ALL registered skill tools (chart, mermaid, pdf, etc.)
        4. Memory tools (if memory is configured)

        This order ensures no conflicts and proper tool availability.

        Returns:
            Combined list of agent tools, skill management tools, skill tools, and memory tools
        """
        # 1. Get base tools from agent implementation
        tools = self.get_agent_tools()
        logger.debug(f"📦 Agent {self.agent_id} has {len(tools)} custom tools")

        # 2. Add skill management tools if skills are enabled
        if SKILLS_AVAILABLE and self._enable_skills:
            skill_mgmt_tools = self._get_skill_management_tools()
            if skill_mgmt_tools:
                tools = tools + skill_mgmt_tools
                logger.info(
                    f"🎯 Added {len(skill_mgmt_tools)} skill management tools to agent {self.agent_id}"
                )

            # 3. Add tools from ALL registered skills (not just loaded ones)
            # This is the key fix: tools must be available before load_skill() is called
            all_skill_tools = self.get_all_registered_skill_tools()
            if all_skill_tools:
                tools = tools + all_skill_tools
                logger.info(f"🔧 Added {len(all_skill_tools)} skill tools to agent {self.agent_id}")

        # 4. Add memory tools if memory is configured (AFTER skill tools)
        if MEMORY_AVAILABLE and hasattr(self, "_ensure_memory_initialized"):
            try:
                # Initialize memory if configured (this is async)
                memory_available = await self._ensure_memory_initialized()
                if memory_available and self.memory_enabled:
                    memory_tools = self._get_memory_tools()
                    if memory_tools:
                        tools = tools + memory_tools
                        logger.info(
                            f"🧠 Added {len(memory_tools)} memory tools to agent {self.agent_id}"
                        )
            except Exception as e:
                logger.warning(f"Failed to add memory tools: {e}")

        logger.debug(f"📊 Total tools for agent {self.agent_id}: {len(tools)}")
        return tools

    async def _async_ensure_agent_built(self):
        """Ensure agent is built (asynchronous)."""
        if not self._agent_built:
            tools = await self._get_all_tools()
            # Get the combined system prompt (with rich content if enabled)
            system_prompt = await self.get_system_prompt()
            await self.initialize_agent(self._resolve_model_name(), system_prompt, tools)
            self._agent_built = True

    # ----- AgentInterface -----
    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """Configure the agent with session-level settings."""
        logger.info(f"BaseAgent: Configuring session: {session_configuration}")

        # Handle skills configuration (replaces rich content configuration)
        if "enable_skills" in session_configuration:
            value = session_configuration["enable_skills"]
            if not isinstance(value, bool):
                logger.warning(f"Invalid enable_skills value: {value}, defaulting to True")
                self._enable_skills = True
            else:
                self._enable_skills = value
            logger.info(f"Skills capabilities: {'enabled' if self._enable_skills else 'disabled'}")

        if "system_prompt" in session_configuration:
            # Only override the agent's custom prompt if the incoming prompt is NOT the generic default.
            # This preserves the agent's get_agent_prompt() when no custom config is provided.
            incoming_prompt = session_configuration["system_prompt"]
            default_prompt = "You are a helpful AI assistant."

            if incoming_prompt != default_prompt:
                # Incoming is a custom prompt (from ES, session config, etc.) - use it
                self._session_system_prompt = incoming_prompt
                logger.info("Session system_prompt override applied (custom prompt from config)")
            else:
                # Incoming is the generic default - keep the agent's own prompt
                logger.debug(
                    f"Keeping agent's custom prompt (incoming was generic default). "
                    f"Agent prompt length: {len(self._session_system_prompt or '')} chars"
                )
        if "model_config" in session_configuration:
            self._session_model_config = session_configuration["model_config"]
        if "model_name" in session_configuration:
            self._session_model_name = session_configuration["model_name"]

        # Rebuild agent with new params
        self._agent_built = False
        await self._async_ensure_agent_built()

    async def get_system_prompt(self) -> str | None:
        """
        Return the current system prompt with skills discovery capabilities.

        If skills are enabled (default), automatically combines the agent's
        custom prompt with skills discovery instructions that teach the agent
        how to discover and load skills on-demand.

        Returns:
            Combined system prompt with skills discovery capabilities, or base prompt if disabled
        """
        base_prompt = self._session_system_prompt or ""

        if not base_prompt:
            logger.warning("Agent has no base prompt defined")
            if self._enable_skills and SKILLS_AVAILABLE:
                # Import here to avoid circular dependencies
                try:
                    from ..skills.discovery_prompt import get_skills_discovery_prompt

                    return get_skills_discovery_prompt()
                except ImportError as e:
                    logger.error(f"Failed to import skills discovery prompt: {e}")
                    logger.warning("Skills discovery capabilities unavailable, using empty prompt")
                    return ""
            return ""

        if not self._enable_skills or not SKILLS_AVAILABLE:
            logger.debug("Skills disabled, returning base prompt only")
            return base_prompt

        # Import here to avoid circular dependencies
        try:
            from ..skills.discovery_prompt import get_skills_discovery_prompt

            skills_prompt = get_skills_discovery_prompt()
            combined = f"{base_prompt}\n\n{skills_prompt}"
            logger.debug(
                f"Combined prompt length: {len(combined)} chars (base: {len(base_prompt)}, skills: {len(skills_prompt)})"
            )
            return combined
        except ImportError as e:
            logger.error(f"Failed to import skills discovery prompt: {e}")
            logger.warning("Skills discovery capabilities unavailable, using base prompt only")
            return base_prompt

    async def get_current_model(self, session_id: str) -> str | None:
        """Return the current model name."""
        return self._resolve_model_name()

    async def get_metadata(self) -> dict[str, Any]:
        """Return agent metadata including id, name, description, and skills summary."""
        tools = await self._get_all_tools()
        tool_list = [
            {
                "name": getattr(t, "__name__", str(t)),
                "description": getattr(t, "__doc__", "Agent tool"),
                "type": "static",
            }
            for t in tools
        ]

        # Build skills summary if skills are available
        skills_summary = None
        if SKILLS_AVAILABLE and self._enable_skills:
            try:
                skills_summary = self.get_skills_summary()
            except Exception as e:
                logger.warning(f"Failed to get skills summary: {e}")
                skills_summary = {"total_skills": 0, "loaded_skills": 0, "loaded_skill_names": []}

        metadata = {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "tags": [{"name": t.name, "color": t.color} for t in self.tags],
            "image_url": self.image_url,
            "capabilities": {
                "streaming": True,
                "tool_use": True,
                "reasoning": True,
                "multimodal": False,
                "skills": SKILLS_AVAILABLE and self._enable_skills,
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text", "structured"],
            "tools": tool_list,
            "tool_summary": {
                "total_tools": len(tools),
                "static_tools": len(tools),
            },
            "framework": "Generic",
        }

        # Add skills summary if available
        if skills_summary:
            metadata["skills_summary"] = skills_summary

        return metadata

    def _build_full_query(self, agent_input: StructuredAgentInput) -> str:
        """Build full query with clear separation between user query and file content."""
        from datetime import datetime

        parts_text = []

        # Add text from all TextInputPart (file content)
        for part in agent_input.parts:
            if isinstance(part, TextInputPart):
                parts_text.append(part.text)

        # Debug logging
        logger.info(
            f"[_build_full_query] Found {len(parts_text)} TextInputPart(s) in agent_input with {len(agent_input.parts)} total parts"
        )
        if parts_text:
            for i, text in enumerate(parts_text):
                logger.info(
                    f"[_build_full_query] Part {i+1} length: {len(text)} chars, preview: {text[:200]}..."
                )

        # Add timestamp for temporal awareness
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build message with clear structure
        if parts_text:
            # Timestamp, user query, then file content clearly separated
            full_message = f"[{timestamp}] User Query: {agent_input.query}\n\n"
            full_message += "Attached Files Content:\n"
            full_message += "\n\n".join(parts_text)
            logger.info(f"[_build_full_query] Final message length: {len(full_message)} chars")
            return full_message

        return f"[{timestamp}] {agent_input.query}"

    async def handle_message(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> StructuredAgentOutput:
        """Handle a user message in non-streaming mode."""
        if not agent_input.query:
            return StructuredAgentOutput(response_text="Input query cannot be empty.", parts=[])

        await self._async_ensure_agent_built()

        # Context reuse
        ctx = self._state_ctx or self.create_fresh_context()

        # Build full query including file content from parts
        full_query = self._build_full_query(agent_input)

        # === PASSIVE MEMORY INJECTION ===
        # Inject memory context if memory is enabled and passive injection is configured
        if MEMORY_AVAILABLE and hasattr(self, "memory_enabled") and self.memory_enabled:
            try:
                memory_config = self.get_memory_config()
                if memory_config and memory_config.passive_injection:
                    # Get user_id from agent input or session
                    user_id = (
                        getattr(agent_input, "user_id", None)
                        or getattr(self, "_current_user_id", None)
                        or "default_user"
                    )

                    # Retrieve memory context for the query
                    memory_context = await self.get_memory_context(user_id, agent_input.query)

                    if memory_context:
                        # Import helper to inject memory into prompt
                        from ..memory.agent_mixin import inject_memory_into_prompt

                        # Get current system prompt and inject memory context
                        current_prompt = await self.get_system_prompt()
                        enhanced_prompt = inject_memory_into_prompt(
                            current_prompt or "", memory_context
                        )

                        # Temporarily update the session prompt for this message
                        self._session_system_prompt = enhanced_prompt

                        # Rebuild agent with enhanced prompt
                        self._agent_built = False
                        await self._async_ensure_agent_built()

                        logger.debug(f"Injected memory context for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to inject memory context: {e}")
                # Continue without memory context - don't fail the message

        # Use run_agent in non-streaming mode
        final_response = await self.run_agent(full_query, ctx, stream=False)
        response_text = str(final_response)

        # Save context for future
        self._state_ctx = ctx

        # === AUTO-STORE INTERACTION ===
        # Store interaction for memory extraction if auto_store_interactions is enabled
        if MEMORY_AVAILABLE and hasattr(self, "memory_enabled") and self.memory_enabled:
            try:
                memory_config = self.get_memory_config()
                if memory_config and memory_config.auto_store_interactions:
                    # Get user_id and session_id
                    user_id = (
                        getattr(agent_input, "user_id", None)
                        or getattr(self, "_current_user_id", None)
                        or "default_user"
                    )
                    current_session_id = getattr(self, "_current_session_id", None) or session_id

                    # Store the interaction (don't await to avoid blocking)
                    success = await self.store_memory_interaction(
                        user_id=user_id,
                        session_id=current_session_id,
                        user_message=agent_input.query,
                        agent_response=response_text,
                        metadata={"source": "handle_message"},
                    )

                    if success:
                        logger.debug(f"Auto-stored interaction for user {user_id}")
                    else:
                        logger.warning(f"Failed to auto-store interaction for user {user_id}")
            except Exception as e:
                # Log warning but don't fail the message
                logger.warning(f"Error auto-storing interaction: {e}")

        cleaned, parts = parse_special_blocks_from_text(response_text)

        # === RICH CONTENT VALIDATION ===
        # Validate and repair rich content blocks (mermaid, chart, tabledata)
        # This also corrects wrong language identifiers (e.g., ```json -> ```chart)
        try:
            from ..processing.rich_content_validation import validate_rich_content

            cleaned = validate_rich_content(cleaned)
            logger.debug("Rich content validation completed")
        except ImportError:
            logger.debug("Rich content validation module not available, skipping")
        except Exception as e:
            logger.warning(f"Rich content validation failed: {e}, using original content")

        return StructuredAgentOutput(
            response_text=cleaned, parts=[TextOutputPart(text=cleaned), *parts]
        )

    async def handle_message_stream(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> AsyncGenerator[StructuredAgentOutput, None]:
        """
        Handle a user message in streaming mode.

        ⚠️  FINAL METHOD - DO NOT OVERRIDE IN SUBCLASSES ⚠️

        This method orchestrates the streaming flow and should NOT be overridden.
        Instead, implement run_agent() and process_streaming_event() in your subclass.

        ORCHESTRATION FLOW:
        ===================

        1. Calls run_agent(stream=True) to get framework-specific events
        2. For each event from run_agent():
           - Calls process_streaming_event() to convert to unified format
           - Converts unified format to StructuredAgentOutput
           - Yields the output to the client
        3. Handles final response assembly and special block parsing

        EVENT FLOW DIAGRAM:

        Your Framework          BaseAgent (This Method)         Client
        ───────────────         ───────────────────────         ──────
              │                          │                         │
              │  run_agent(stream=True)  │                         │
              │◄─────────────────────────│                         │
              │                          │                         │
              │  yield raw_event_1       │                         │
              ├─────────────────────────►│                         │
              │                          │                         │
              │                          │ process_streaming_event()│
              │                          │ (converts to unified)   │
              │                          │                         │
              │                          │  StructuredAgentOutput  │
              │                          ├────────────────────────►│
              │                          │                         │
              │  yield raw_event_2       │                         │
              ├─────────────────────────►│                         │
              │                          │                         │
              │                          │ process_streaming_event()│
              │                          │                         │
              │                          │  StructuredAgentOutput  │
              │                          ├────────────────────────►│
              │                          │                         │

        WHY THIS IS FINAL:
        ==================

        This method contains framework-agnostic orchestration logic that:
        - Manages the streaming lifecycle
        - Handles event conversion consistently
        - Ensures proper output formatting
        - Manages context state
        - Parses special blocks (charts, forms, etc.)

        By keeping this final, we ensure:
        - Consistent behavior across all agent implementations
        - Separation of concerns (framework logic vs orchestration)
        - Easier maintenance and debugging
        - Clear extension points (run_agent and process_streaming_event)

        WHAT TO IMPLEMENT INSTEAD:
        ===========================

        1. run_agent(stream=True) - Yield RAW framework events
           Example:
           async def run_agent(self, query, ctx, stream=True):
               async for event in my_framework.stream(query):
                   yield event  # Yield RAW events

        2. process_streaming_event() - Convert events to unified format
           Example:
           async def process_streaming_event(self, event):
               if event.type == "text":
                   return {"type": "chunk", "content": event.text, "metadata": {}}
               return None

        Args:
            session_id: The session identifier
            agent_input: Structured input containing query and optional file content

        Yields:
            StructuredAgentOutput: Streaming outputs with text chunks, activities, and final response

        Note:
            This method is marked as FINAL to maintain consistent streaming behavior.
            Do not override this method. Implement run_agent() and process_streaming_event() instead.
        """
        if not agent_input.query:
            yield StructuredAgentOutput(response_text="Input query cannot be empty.", parts=[])
            return

        await self._async_ensure_agent_built()

        ctx = self._state_ctx or self.create_fresh_context()

        # Build full query including file content from parts
        full_query = self._build_full_query(agent_input)

        # === PASSIVE MEMORY INJECTION ===
        # Inject memory context if memory is enabled and passive injection is configured
        if MEMORY_AVAILABLE and hasattr(self, "memory_enabled") and self.memory_enabled:
            try:
                memory_config = self.get_memory_config()
                if memory_config and memory_config.passive_injection:
                    # Get user_id from agent input or session
                    user_id = (
                        getattr(agent_input, "user_id", None)
                        or getattr(self, "_current_user_id", None)
                        or "default_user"
                    )

                    # Retrieve memory context for the query
                    memory_context = await self.get_memory_context(user_id, agent_input.query)

                    if memory_context:
                        # Import helper to inject memory into prompt
                        from ..memory.agent_mixin import inject_memory_into_prompt

                        # Get current system prompt and inject memory context
                        current_prompt = await self.get_system_prompt()
                        enhanced_prompt = inject_memory_into_prompt(
                            current_prompt or "", memory_context
                        )

                        # Temporarily update the session prompt for this message
                        self._session_system_prompt = enhanced_prompt

                        # Rebuild agent with enhanced prompt
                        self._agent_built = False
                        await self._async_ensure_agent_built()

                        logger.debug(f"Injected memory context for user {user_id} (streaming)")
            except Exception as e:
                logger.warning(f"Failed to inject memory context (streaming): {e}")
                # Continue without memory context - don't fail the message

        # Use run_agent in streaming mode
        stream_generator = await self.run_agent(full_query, ctx, stream=True)

        agent_loop_started_emitted = False
        final_text_parts: list[str] = []

        # === RICH CONTENT STREAMING BUFFER ===
        # Accumulate all chunks, then send validated content when rich blocks complete
        # This handles cases where markers are split across chunks
        import re

        pending_buffer = ""  # Buffer for text not yet sent
        RICH_CONTENT_PATTERN = re.compile(
            r"```(mermaid|chart|chartjs|tabledata)\s*\n.*?```", re.DOTALL
        )

        # === TOOL CONSOLIDATION TRACKING ===
        # Track pending tool calls to consolidate with results
        pending_tool_calls: dict[str, dict] = {}  # call_id -> tool call data
        activity_formatter = ActivityFormatter(source=self.name or "base_agent")

        async for event in stream_generator:
            # Process event through subclass-specific handler
            processed_event = await self.process_streaming_event(event)

            if processed_event is None:
                continue

            event_type = processed_event.get("type")

            # Handle different event types
            if event_type == "chunk":
                chunk = processed_event.get("content", "")
                if chunk:
                    final_text_parts.append(chunk)
                    pending_buffer += chunk

                    # Try to extract and send complete content
                    while True:
                        # Check for complete rich content block
                        match = RICH_CONTENT_PATTERN.search(pending_buffer)
                        if match:
                            # Send text before the block
                            before = pending_buffer[: match.start()]
                            if before:
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
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[
                                        TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")
                                    ],
                                )
                            except Exception as e:
                                logger.warning(f"Rich content streaming validation: {e}")
                                yield StructuredAgentOutput(
                                    response_text="",
                                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{block}")],
                                )

                            # Keep the rest in buffer
                            pending_buffer = pending_buffer[match.end() :]
                        else:
                            # No complete block found
                            # Check if we might be in the middle of a block
                            has_open_block = False
                            for marker in ("```mermaid", "```chart", "```chartjs", "```tabledata"):
                                if marker in pending_buffer:
                                    # Found opening, check if closed
                                    marker_pos = pending_buffer.find(marker)
                                    after_marker = pending_buffer[marker_pos + len(marker) :]
                                    if "\n" in after_marker:
                                        # Has newline after marker, look for closing
                                        newline_pos = after_marker.find("\n")
                                        rest = after_marker[newline_pos:]
                                        if "```" not in rest:
                                            # Block not closed yet, keep buffering
                                            has_open_block = True
                                            break
                                    else:
                                        # No newline yet, keep buffering
                                        has_open_block = True
                                        break

                            if not has_open_block:
                                # Safe to send everything except potential partial markers
                                # Keep last 15 chars in case of split marker like "```mer" + "maid"
                                if len(pending_buffer) > 15:
                                    to_send = pending_buffer[:-15]
                                    pending_buffer = pending_buffer[-15:]
                                    yield StructuredAgentOutput(
                                        response_text="",
                                        parts=[
                                            TextOutputStreamPart(text=f"__STREAM_CHUNK__{to_send}")
                                        ],
                                    )
                            break

            elif event_type == "tool_call":
                # FLUSH pending_buffer BEFORE storing tool call
                # This ensures text is fully emitted before the activity part
                if pending_buffer:
                    try:
                        from ..processing.rich_content_validation import validate_rich_content

                        validated = validate_rich_content(pending_buffer)
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")],
                        )
                    except Exception as e:
                        logger.warning(f"Rich content flush before tool call: {e}")
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")],
                        )
                    pending_buffer = ""

                # Store tool call as pending for consolidation with result
                call_id = processed_event.get("metadata", {}).get("call_id", "unknown")
                tool_name = processed_event.get("metadata", {}).get("tool_name", "unknown")
                tool_arguments = processed_event.get("metadata", {}).get("tool_arguments", {})

                pending_tool_calls[call_id] = {
                    "tool_name": tool_name,
                    "arguments": tool_arguments,
                    "call_id": call_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "display_info": processed_event.get("metadata", {}).get("display_info"),
                }
                # Don't emit yet - wait for tool_result to consolidate
                agent_loop_started_emitted = False

            elif event_type == "tool_result":
                # FLUSH pending_buffer BEFORE emitting consolidated tool activity
                # This ensures text is fully emitted before the activity part
                if pending_buffer:
                    try:
                        from ..processing.rich_content_validation import validate_rich_content

                        validated = validate_rich_content(pending_buffer)
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")],
                        )
                    except Exception as e:
                        logger.warning(f"Rich content flush before tool result: {e}")
                        yield StructuredAgentOutput(
                            response_text="",
                            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")],
                        )
                    pending_buffer = ""

                # Get tool result data
                call_id = processed_event.get("metadata", {}).get("call_id", "unknown")
                tool_name = processed_event.get("metadata", {}).get("tool_name", "unknown")
                result_content = processed_event.get("content", "")
                is_error = processed_event.get("metadata", {}).get("is_error", False)

                # Look up pending tool call for consolidation
                pending_call = pending_tool_calls.pop(call_id, None)
                if pending_call:
                    tool_name = pending_call["tool_name"]
                    tool_arguments = pending_call["arguments"]
                else:
                    tool_arguments = {}

                # Use ActivityFormatter to create consolidated activity with specific friendly_name
                activity_part = activity_formatter.format_tool_execution(
                    tool_name=tool_name,
                    arguments=tool_arguments,
                    result=result_content,
                    execution_time_ms=0,  # We don't have exact timing here
                    is_error=is_error,
                )
                # Override source with agent name
                activity_part.source = self.name or "base_agent"

                # Create backward-compatible __STREAM_ACTIVITY__ event
                tool_call_event = {
                    "type": "tool_call",
                    "source": self.name or "base_agent",
                    "tools": [{"name": tool_name, "arguments": tool_arguments, "id": call_id}],
                    "results": [
                        {
                            "name": tool_name,
                            "content": result_content,
                            "is_error": is_error,
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

            elif event_type == "activity":
                if not agent_loop_started_emitted:
                    loop_activity = {
                        "type": "activity",
                        "source": "base_agent",
                        "content": processed_event.get("content", "Agent loop started"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    # Create ActivityOutputPart for order preservation
                    activity_part = ActivityOutputPart(
                        activity_type="activity",
                        source="base_agent",
                        content=loop_activity["content"],
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        display_info=processed_event.get("metadata", {}).get("display_info"),
                    )

                    yield StructuredAgentOutput(
                        response_text="",
                        parts=[
                            activity_part,  # NEW: ActivityOutputPart for order preservation
                            TextOutputStreamPart(
                                text=f"__STREAM_ACTIVITY__{json.dumps(loop_activity)}"
                            ),  # KEEP: backward compatibility
                        ],
                    )
                    agent_loop_started_emitted = True

            elif event_type == "error":
                error_activity = {
                    "type": "error",
                    "source": "base_agent",
                    "content": processed_event.get("content", "Unknown error"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Create ActivityOutputPart for order preservation
                activity_part = ActivityOutputPart(
                    activity_type="error",
                    source="base_agent",
                    content=error_activity["content"],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    display_info=processed_event.get("metadata", {}).get("display_info"),
                )

                yield StructuredAgentOutput(
                    response_text="",
                    parts=[
                        activity_part,  # NEW: ActivityOutputPart for order preservation
                        TextOutputStreamPart(
                            text=f"__STREAM_ACTIVITY__{json.dumps(error_activity)}"
                        ),  # KEEP: backward compatibility
                    ],
                )

        # Flush any remaining pending buffer
        if pending_buffer:
            try:
                from ..processing.rich_content_validation import validate_rich_content

                validated = validate_rich_content(pending_buffer)
                yield StructuredAgentOutput(
                    response_text="",
                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")],
                )
            except Exception as e:
                logger.warning(f"Rich content final flush validation: {e}")
                yield StructuredAgentOutput(
                    response_text="",
                    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")],
                )

        # Final result
        self._state_ctx = ctx
        final_text = "".join(final_text_parts)

        # === AUTO-STORE INTERACTION ===
        # Store interaction for memory extraction if auto_store_interactions is enabled
        if MEMORY_AVAILABLE and hasattr(self, "memory_enabled") and self.memory_enabled:
            try:
                memory_config = self.get_memory_config()
                if memory_config and memory_config.auto_store_interactions:
                    # Get user_id and session_id
                    user_id = (
                        getattr(agent_input, "user_id", None)
                        or getattr(self, "_current_user_id", None)
                        or "default_user"
                    )
                    current_session_id = getattr(self, "_current_session_id", None) or session_id

                    # Store the interaction with collected response
                    success = await self.store_memory_interaction(
                        user_id=user_id,
                        session_id=current_session_id,
                        user_message=agent_input.query,
                        agent_response=final_text,
                        metadata={"source": "handle_message_stream"},
                    )

                    if success:
                        logger.debug(f"Auto-stored streaming interaction for user {user_id}")
                    else:
                        logger.warning(
                            f"Failed to auto-store streaming interaction for user {user_id}"
                        )
            except Exception as e:
                # Log warning but don't fail the message
                logger.warning(f"Error auto-storing streaming interaction: {e}")

        cleaned, parts = parse_special_blocks_from_text(final_text)

        # === RICH CONTENT VALIDATION ===
        # Validate and repair rich content blocks (mermaid, chart, tabledata)
        # This also corrects wrong language identifiers (e.g., ```json -> ```chart)
        try:
            from ..processing.rich_content_validation import validate_rich_content

            cleaned = validate_rich_content(cleaned)
            logger.debug("Rich content validation completed")
        except ImportError:
            logger.debug("Rich content validation module not available, skipping")
        except Exception as e:
            logger.warning(f"Rich content validation failed: {e}, using original content")

        yield StructuredAgentOutput(
            response_text=cleaned,
            parts=[TextOutputPart(text=cleaned), *parts],
        )

    async def get_state(self) -> dict[str, Any]:
        """Get the current agent state."""
        if self._state_ctx is None:
            return {}
        try:
            return self.serialize_context(self._state_ctx)
        finally:
            # One-time retrieval pattern to keep consistent with existing examples
            self._state_ctx = None

    async def load_state(self, state: dict[str, Any]):
        """Load agent state from a dictionary."""
        # Ensure the concrete agent exists before creating or deserializing context
        await self._async_ensure_agent_built()
        if state:
            try:
                self._state_ctx = self.deserialize_context(state)
            except Exception as e:
                logger.error(f"Failed to load context state: {e}. Starting fresh.")
                self._state_ctx = self.create_fresh_context()
        else:
            self._state_ctx = self.create_fresh_context()
