"""
Memory Mixin for BaseAgent.

Provides memory capabilities to agents via mixin pattern.
This allows clean integration without modifying the core BaseAgent class.

Usage:
    ```python
    from agent_framework.core.base_agent import BaseAgent
    from agent_framework.memory.agent_mixin import MemoryMixin
    
    class MyAgent(MemoryMixin, BaseAgent):
        def get_memory_config(self):
            return MemoryConfig.memori_simple()
    ```

Or directly in LlamaIndexAgent by overriding get_memory_config().

Version: 0.1.0
"""

import logging
from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    from .config import MemoryConfig
    from .manager import MemoryManager

logger = logging.getLogger(__name__)


class MemoryMixin:
    """
    Mixin that adds memory capabilities to agents.
    
    Agents that inherit this mixin gain:
    - Automatic memory initialization
    - Context injection before messages
    - Interaction storage after responses
    
    Override get_memory_config() to configure memory.
    
    Attributes:
        _memory_manager: MemoryManager instance (or None if disabled)
        _memory_initialized: Whether memory has been initialized
    """

    # These will be set by the agent class
    agent_id: str
    _current_user_id: str | None
    _current_session_id: str | None

    def __init__(self, *args, **kwargs):
        """Initialize memory mixin."""
        # Initialize memory attributes before super().__init__
        self._memory_manager: MemoryManager | None = None
        self._memory_initialized: bool = False
        self._memory_init_attempted: bool = False

        # Call parent __init__
        super().__init__(*args, **kwargs)

    def get_memory_config(self) -> Optional["MemoryConfig"]:
        """
        Return memory configuration for this agent.
        
        Override this method in your agent class to enable memory.
        
        Returns:
            MemoryConfig instance, or None to disable memory
            
        Examples:
            ```python
            # Simple Memori (SQLite)
            def get_memory_config(self):
                return MemoryConfig.memori_simple()
            
            # Graphiti with FalkorDB
            def get_memory_config(self):
                return MemoryConfig.graphiti_simple()
            
            # Hybrid (both providers)
            def get_memory_config(self):
                return MemoryConfig.hybrid()
            
            # Custom configuration
            def get_memory_config(self):
                return MemoryConfig(
                    primary_provider="memori",
                    secondary_provider="graphiti",
                    memori=MemoriConfig(
                        database_url="postgresql://localhost/memory"
                    ),
                    graphiti=GraphitiConfig(
                        use_falkordb=True,
                        falkordb_host="redis-server"
                    ),
                    max_context_facts=30
                )
            
            # Disabled
            def get_memory_config(self):
                return None
            ```
        """
        return None  # Disabled by default

    async def _ensure_memory_initialized(self) -> bool:
        """
        Ensure memory manager is initialized.
        
        Called lazily before first memory operation.
        
        Returns:
            True if memory is available
        """
        if self._memory_initialized:
            return self._memory_manager is not None

        if self._memory_init_attempted:
            # Already tried and failed
            return False

        self._memory_init_attempted = True

        config = self.get_memory_config()
        if config is None or not config.is_enabled:
            logger.debug(f"Memory disabled for agent {getattr(self, 'agent_id', 'unknown')}")
            return False

        try:
            from .manager import MemoryManager
            from .providers import GRAPHITI_AVAILABLE, MEMORI_AVAILABLE

            # Log helpful messages about provider availability
            agent_id = getattr(self, 'agent_id', 'unknown')
            providers = config.get_enabled_providers()

            for provider in providers:
                if provider == "memori" and not MEMORI_AVAILABLE:
                    logger.warning(
                        f"⚠️ Agent '{agent_id}' requested Memori memory but it's not installed.\n"
                        f"   Install with: pip install memori\n"
                        f"   Or: uv add agent-framework-lib[memory]"
                    )
                elif provider == "graphiti" and not GRAPHITI_AVAILABLE:
                    logger.warning(
                        f"⚠️ Agent '{agent_id}' requested Graphiti memory but it's not installed.\n"
                        f"   Install with: pip install graphiti-core\n"
                        f"   Or: uv add agent-framework-lib[memory]"
                    )

            self._memory_manager = MemoryManager(config)
            success = await self._memory_manager.initialize()

            if success:
                self._memory_initialized = True
                status = self._memory_manager.get_provider_status()
                primary_init = status.get('primary', {}).get('initialized', False) if status.get('primary') else False
                secondary_init = status.get('secondary', {}).get('initialized', False) if status.get('secondary') else False

                if primary_init or secondary_init:
                    logger.info(
                        f"✅ Memory initialized for agent '{agent_id}': "
                        f"providers={providers}, "
                        f"primary_ok={primary_init}, secondary_ok={secondary_init}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Memory configured for agent '{agent_id}' but no providers initialized.\n"
                        f"   Requested providers: {providers}\n"
                        f"   Available: memori={MEMORI_AVAILABLE}, graphiti={GRAPHITI_AVAILABLE}"
                    )
                return True
            else:
                logger.warning(
                    f"⚠️ Memory initialization failed for agent '{agent_id}'.\n"
                    f"   Requested providers: {providers}\n"
                    f"   The agent will continue without memory features."
                )
                self._memory_manager = None
                return False

        except ImportError as e:
            logger.warning(
                f"⚠️ Memory module import error: {e}\n"
                f"   Install memory dependencies with: uv add agent-framework-lib[memory]"
            )
            self._memory_manager = None
            return False
        except Exception as e:
            logger.error(f"Error initializing memory: {e}")
            self._memory_manager = None
            return False

    async def get_memory_context(
        self,
        user_id: str,
        query: str
    ) -> str | None:
        """
        Get memory context formatted for prompt injection.
        
        Call this before generating a response to inject relevant memories.
        
        Args:
            user_id: User identifier
            query: The user's current message/query
            
        Returns:
            Formatted memory context string, or None if no relevant memories
        """
        if not await self._ensure_memory_initialized():
            return None

        if not self._memory_manager:
            return None

        try:
            return await self._memory_manager.get_context_for_prompt(
                user_id=user_id,
                agent_id=getattr(self, 'agent_id', 'agent'),
                query=query
            )
        except Exception as e:
            logger.error(f"Error getting memory context: {e}")
            return None

    async def store_memory_interaction(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Store an interaction for memory extraction.
        
        Call this after generating a response to store the interaction.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_message: The user's message
            agent_response: The agent's response
            metadata: Optional additional metadata
            
        Returns:
            True if stored successfully
        """
        if not await self._ensure_memory_initialized():
            return False

        if not self._memory_manager:
            return False

        try:
            return await self._memory_manager.store_interaction(
                user_id=user_id,
                session_id=session_id,
                agent_id=getattr(self, 'agent_id', 'agent'),
                user_message=user_message,
                agent_response=agent_response,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error storing memory interaction: {e}")
            return False

    async def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if cleared successfully
        """
        if not await self._ensure_memory_initialized():
            return False

        if not self._memory_manager:
            return False

        try:
            return await self._memory_manager.clear_user_memory(
                user_id=user_id,
                agent_id=getattr(self, 'agent_id', None)
            )
        except Exception as e:
            logger.error(f"Error clearing user memory: {e}")
            return False

    def get_memory_status(self) -> dict[str, Any]:
        """
        Get status of memory system.
        
        Returns:
            Dictionary with memory status information
        """
        if not self._memory_manager:
            config = self.get_memory_config()
            return {
                "enabled": config is not None and config.is_enabled if config else False,
                "initialized": False,
                "reason": "Memory not configured" if config is None else "Not yet initialized"
            }

        return self._memory_manager.get_provider_status()

    @property
    def memory_enabled(self) -> bool:
        """Whether memory is enabled and initialized."""
        return self._memory_initialized and self._memory_manager is not None

    @property
    def memory_manager(self) -> Optional["MemoryManager"]:
        """Get the memory manager (may be None if not initialized)."""
        return self._memory_manager


# Helper to add memory context to system prompt
def inject_memory_into_prompt(
    base_prompt: str,
    memory_context: str | None
) -> str:
    """
    Inject memory context into a system prompt.
    
    Args:
        base_prompt: The original system prompt
        memory_context: Memory context to inject (or None)
        
    Returns:
        Modified prompt with memory context
    """
    if not memory_context:
        return base_prompt

    # Add memory context before the main prompt
    return f"{memory_context}\n\n{base_prompt}"
