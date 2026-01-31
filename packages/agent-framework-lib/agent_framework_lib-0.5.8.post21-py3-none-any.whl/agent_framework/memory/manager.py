"""
Memory Manager for Agent Framework.

Orchestrates memory providers (Memori, Graphiti) with support for:
- Single provider operation
- Dual provider (hybrid) operation
- Automatic context retrieval and injection
- Interaction storage
- Async fire-and-forget storage

The manager is designed to be used internally by agents, following the
framework's philosophy of encapsulation.

Example:
    ```python
    class MyAgent(LlamaIndexAgent):
        def get_memory_config(self) -> Optional[MemoryConfig]:
            return MemoryConfig.hybrid()  # Both Memori and Graphiti
    ```

Version: 0.2.0
"""

import asyncio
import logging
import time
from typing import Any

from .base import MemoryContext, MemoryProviderInterface
from .config import MemoryConfig
from .providers.graphiti_provider import GRAPHITI_AVAILABLE, GraphitiProvider
from .providers.memori_provider import MEMORI_AVAILABLE, MemoriProvider


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages memory providers for an agent.
    
    Supports single or dual provider operation:
    - Single: Only primary provider is used
    - Dual: Both providers are used, results merged
    
    The manager handles:
    - Provider initialization
    - Context retrieval (with optional merging)
    - Interaction storage (to both providers in hybrid mode)
    - Provider lifecycle
    
    Attributes:
        config: MemoryConfig with provider settings
        primary: Primary memory provider (or None)
        secondary: Secondary memory provider (or None)
    """

    def __init__(self, config: MemoryConfig):
        """
        Initialize memory manager.
        
        Args:
            config: Memory configuration
        """
        self.config = config
        self._primary: MemoryProviderInterface | None = None
        self._secondary: MemoryProviderInterface | None = None
        self._initialized = False

        # Background task management for async storage
        self._pending_tasks: set[asyncio.Task] = set()
        self._task_semaphore: asyncio.Semaphore | None = None

    async def initialize(self) -> bool:
        """
        Initialize configured memory providers.
        
        Creates and initializes primary and optionally secondary providers.
        
        Returns:
            True if at least one provider initialized successfully
        """
        if self._initialized:
            return True

        if not self.config.is_enabled:
            logger.info("Memory disabled (primary_provider='none')")
            return True

        success = False

        # Initialize primary provider
        self._primary = await self._create_provider(self.config.primary_provider)
        if self._primary:
            success = True
            logger.info(
                f"✅ Primary memory provider initialized: {self.config.primary_provider}"
            )

        # Initialize secondary provider (hybrid mode)
        if self.config.secondary_provider:
            self._secondary = await self._create_provider(self.config.secondary_provider)
            if self._secondary:
                logger.info(
                    f"✅ Secondary memory provider initialized: {self.config.secondary_provider}"
                )

        self._initialized = success
        return success

    async def _create_provider(
        self,
        provider_type: str
    ) -> MemoryProviderInterface | None:
        """
        Create and initialize a memory provider.
        
        Args:
            provider_type: "memori" or "graphiti"
            
        Returns:
            Initialized provider or None
        """
        provider: MemoryProviderInterface | None = None

        try:
            if provider_type == "memori":
                if not MEMORI_AVAILABLE:
                    logger.error(
                        "Memori requested but not installed. "
                        "Install with: pip install memori"
                    )
                    return None
                provider = MemoriProvider(self.config.memori)

            elif provider_type == "graphiti":
                if not GRAPHITI_AVAILABLE:
                    logger.error(
                        "Graphiti requested but not installed. "
                        "Install with: pip install graphiti-core"
                    )
                    return None
                provider = GraphitiProvider(self.config.graphiti)

            if provider:
                success = await provider.initialize()
                if success:
                    return provider
                else:
                    logger.error(f"Failed to initialize {provider_type} provider")
                    return None

        except Exception as e:
            logger.error(f"Error creating {provider_type} provider: {e}")
            return None

        return None

    async def store_interaction(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Store interaction in all active memory providers.
        
        In hybrid mode, stores to both providers for comprehensive memory.
        When async_store is True, spawns background task and returns immediately.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_id: Agent identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional metadata
            
        Returns:
            True if stored in at least one provider (or if async task was scheduled)
        """
        if not self.config.auto_store_interactions:
            return True

        if self.config.async_store:
            # Fire-and-forget: spawn background task and return immediately
            self._schedule_background_store(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                user_message=user_message,
                agent_response=agent_response,
                metadata=metadata
            )
            return True  # Return immediately
        else:
            # Synchronous: wait for completion
            return await self._store_interaction_sync(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                user_message=user_message,
                agent_response=agent_response,
                metadata=metadata
            )

    async def _store_interaction_sync(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Synchronously store interaction in all active memory providers.
        
        This is the actual storage logic, extracted for use by both
        sync and async code paths.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_id: Agent identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional metadata
            
        Returns:
            True if stored in at least one provider
        """
        success = False

        # Store in primary
        if self._primary:
            try:
                result = await self._primary.store_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    metadata=metadata
                )
                if result:
                    success = True
            except Exception as e:
                logger.error(f"Error storing in primary provider: {e}")

        # Store in secondary (hybrid mode)
        if self._secondary:
            try:
                result = await self._secondary.store_interaction(
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    metadata=metadata
                )
                if result:
                    success = True
            except Exception as e:
                logger.error(f"Error storing in secondary provider: {e}")

        return success

    def _schedule_background_store(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Schedule a background store task.
        
        Creates an asyncio task for background storage and tracks it
        in the pending tasks set.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_id: Agent identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional metadata
        """
        task = asyncio.create_task(
            self._background_store_task(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                user_message=user_message,
                agent_response=agent_response,
                metadata=metadata
            )
        )

        # Track task
        self._pending_tasks.add(task)
        task.add_done_callback(self._on_task_done)

    async def _background_store_task(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Background task for storing interaction.
        
        Respects concurrency limit via semaphore and logs duration.
        Catches and logs exceptions without re-raising.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_id: Agent identifier
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional metadata
            
        Returns:
            True if stored successfully, False otherwise
        """
        # Initialize semaphore lazily to respect concurrency limit
        if self._task_semaphore is None:
            self._task_semaphore = asyncio.Semaphore(
                self.config.async_store_max_concurrent
            )

        async with self._task_semaphore:
            start_time = time.perf_counter()

            try:
                result = await self._store_interaction_sync(
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    user_message=user_message,
                    agent_response=agent_response,
                    metadata=metadata
                )

                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Background store completed in {duration_ms:.1f}ms")

                return result
            except Exception as e:
                logger.error(f"Background store failed: {e}")
                return False

    def _on_task_done(self, task: asyncio.Task) -> None:
        """
        Callback when a background task completes.
        
        Removes the task from the pending set and logs any unhandled exception.
        
        Args:
            task: The completed asyncio task
        """
        self._pending_tasks.discard(task)

        # Log any exception that wasn't handled
        if not task.cancelled():
            try:
                exc = task.exception()
                if exc:
                    logger.error(f"Background task exception: {exc}")
            except asyncio.InvalidStateError:
                # Task is not done yet (shouldn't happen in done callback)
                pass

    async def recall(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int | None = None
    ) -> MemoryContext:
        """
        Recall relevant memories from all active providers.
        
        In hybrid mode, merges results from both providers,
        sorted by confidence score.
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier
            query: Search query
            limit: Max facts (uses config default if None)
            
        Returns:
            MemoryContext with merged facts
        """
        limit = limit or self.config.max_context_facts

        # Collect from primary
        primary_context = MemoryContext(facts=[])
        if self._primary:
            try:
                primary_context = await self._primary.recall(
                    user_id=user_id,
                    agent_id=agent_id,
                    query=query,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Error recalling from primary provider: {e}")

        # Collect from secondary (hybrid mode)
        if self._secondary:
            try:
                secondary_context = await self._secondary.recall(
                    user_id=user_id,
                    agent_id=agent_id,
                    query=query,
                    limit=limit
                )
                # Merge contexts
                primary_context = primary_context.merge_with(secondary_context)
            except Exception as e:
                logger.error(f"Error recalling from secondary provider: {e}")

        # Limit total facts
        if len(primary_context.facts) > limit:
            primary_context.facts = primary_context.facts[:limit]

        return primary_context

    async def _recall_from_primary_only(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int
    ) -> MemoryContext:
        """
        Recall from primary provider only (optimized for passive injection).
        
        This method is faster than recall() as it only queries the primary
        provider, skipping the secondary provider entirely. Used when
        passive_injection_primary_only is enabled.
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier
            query: Search query
            limit: Max facts to return
            
        Returns:
            MemoryContext with facts from primary provider only
        """
        start_time = time.perf_counter()

        if not self._primary:
            return MemoryContext(facts=[])

        try:
            context = await self._primary.recall(
                user_id=user_id,
                agent_id=agent_id,
                query=query,
                limit=limit
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Primary-only recall completed in {duration_ms:.1f}ms")

            return context
        except Exception as e:
            logger.error(f"Error in primary-only recall: {e}")
            return MemoryContext(facts=[])

    async def get_context_for_prompt(
        self,
        user_id: str,
        agent_id: str,
        query: str
    ) -> str | None:
        """
        Get formatted memory context for injection into prompt.
        
        Convenience method that recalls and formats in one call.
        Applies confidence filtering based on passive_injection_min_confidence.
        
        When passive_injection_primary_only is True, only queries primary provider.
        This is faster but may miss complex relationships from secondary.
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier
            query: The user's current query
            
        Returns:
            Formatted string for prompt injection, or None if no context
        """
        # Use passive_injection_max_facts for limit when getting context for prompt
        limit = self.config.passive_injection_max_facts

        # Optimization: query only primary for passive injection when configured
        if self.config.passive_injection_primary_only and self._primary:
            context = await self._recall_from_primary_only(
                user_id=user_id,
                agent_id=agent_id,
                query=query,
                limit=limit
            )
        else:
            # Default: query both providers
            context = await self.recall(
                user_id=user_id,
                agent_id=agent_id,
                query=query,
                limit=limit
            )

        if not context.facts:
            return None

        # Apply confidence filtering based on passive_injection_min_confidence
        min_confidence = self.config.passive_injection_min_confidence
        filtered_facts = [
            fact for fact in context.facts
            if fact.confidence >= min_confidence
        ]

        if not filtered_facts:
            logger.debug(
                f"No facts passed confidence filter (min={min_confidence}). "
                f"Original count: {len(context.facts)}"
            )
            return None

        # Update context with filtered facts
        context.facts = filtered_facts

        # Use passive_injection_max_facts for formatting
        return context.to_prompt_string(max_facts=self.config.passive_injection_max_facts)

    async def clear_user_memory(
        self,
        user_id: str,
        agent_id: str | None = None
    ) -> bool:
        """
        Clear memories for a user from all providers.
        
        Args:
            user_id: User identifier
            agent_id: Optional agent filter
            
        Returns:
            True if cleared from at least one provider
        """
        success = False

        if self._primary:
            try:
                result = await self._primary.clear_user_memory(user_id, agent_id)
                if result:
                    success = True
            except Exception as e:
                logger.error(f"Error clearing primary provider: {e}")

        if self._secondary:
            try:
                result = await self._secondary.clear_user_memory(user_id, agent_id)
                if result:
                    success = True
            except Exception as e:
                logger.error(f"Error clearing secondary provider: {e}")

        return success

    async def close(self) -> None:
        """
        Close memory manager and wait for pending tasks.
        
        Implements graceful shutdown by:
        1. Waiting for pending background tasks with a timeout
        2. Cancelling remaining tasks if timeout is exceeded
        3. Closing all memory providers regardless of task status
        """
        # Wait for pending tasks with timeout
        if self._pending_tasks:
            pending_count = len(self._pending_tasks)
            logger.info(f"Waiting for {pending_count} pending memory tasks...")

            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._pending_tasks, return_exceptions=True),
                    timeout=self.config.async_store_timeout
                )
                logger.debug("All pending memory tasks completed successfully")
            except asyncio.TimeoutError:
                remaining_count = len(self._pending_tasks)
                logger.warning(
                    f"Timeout waiting for pending tasks after {self.config.async_store_timeout}s. "
                    f"{remaining_count} tasks may be incomplete."
                )
                # Cancel remaining tasks
                for task in list(self._pending_tasks):
                    if not task.done():
                        task.cancel()

        # Close providers regardless of task status
        if self._primary:
            await self._primary.close()
        if self._secondary:
            await self._secondary.close()
        self._initialized = False

    @property
    def is_enabled(self) -> bool:
        """Whether memory is enabled."""
        return self.config.is_enabled

    @property
    def is_initialized(self) -> bool:
        """Whether manager is initialized."""
        return self._initialized

    @property
    def is_hybrid(self) -> bool:
        """Whether using dual provider mode."""
        return self._secondary is not None

    @property
    def primary(self) -> MemoryProviderInterface | None:
        """Get primary provider."""
        return self._primary

    @property
    def secondary(self) -> MemoryProviderInterface | None:
        """Get secondary provider."""
        return self._secondary

    def get_provider_status(self) -> dict[str, Any]:
        """
        Get status of memory providers.
        
        Returns:
            Dictionary with provider status information including:
            - Provider initialization status
            - Async storage configuration
            - Passive injection configuration
            - Pending background task count
        """
        return {
            "enabled": self.config.is_enabled,
            "initialized": self._initialized,
            "hybrid_mode": self.is_hybrid,
            "primary": {
                "type": self.config.primary_provider,
                "initialized": self._primary.is_initialized if self._primary else False,
                "supports_temporal": self._primary.supports_temporal_queries if self._primary else False,
            } if self.config.primary_provider != "none" else None,
            "secondary": {
                "type": self.config.secondary_provider,
                "initialized": self._secondary.is_initialized if self._secondary else False,
                "supports_temporal": self._secondary.supports_temporal_queries if self._secondary else False,
            } if self.config.secondary_provider else None,
            "available_providers": {
                "memori": MEMORI_AVAILABLE,
                "graphiti": GRAPHITI_AVAILABLE,
            },
            # Async storage status
            "async_store_enabled": self.config.async_store,
            "passive_primary_only": self.config.passive_injection_primary_only,
            "pending_tasks": len(self._pending_tasks),
        }


# Factory function for convenience
async def create_memory_manager(config: MemoryConfig) -> MemoryManager:
    """
    Create and initialize a memory manager.
    
    Convenience function that creates and initializes in one call.
    
    Args:
        config: Memory configuration
        
    Returns:
        Initialized MemoryManager
        
    Example:
        ```python
        manager = await create_memory_manager(MemoryConfig.hybrid())
        ```
    """
    manager = MemoryManager(config)
    await manager.initialize()
    return manager
