"""
Memory Provider Interface for Agent Framework.

Provides a unified interface for different memory backends:
- Memori (SQL-based, simple, fast setup)
- Graphiti (Knowledge Graph, temporal, complex queries)

Memory can be configured directly within agent classes, following the
framework's philosophy of encapsulation.

Example:
    ```python
    class MyAgent(LlamaIndexAgent):
        def get_memory_config(self) -> Optional[MemoryConfig]:
            return MemoryConfig(
                primary_provider="memori",
                memori=MemoriConfig(database_url="sqlite:///memory.db")
            )
    ```

Version: 0.1.0
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory providers supported."""
    MEMORI = "memori"
    GRAPHITI = "graphiti"


@dataclass
class MemoryFact:
    """
    Represents a fact/memory retrieved from storage.
    
    Unified format across all memory providers, with optional
    provider-specific fields.
    
    Attributes:
        content: The actual fact content
        fact_type: Type of fact ("fact", "preference", "event", "relationship", etc.)
        confidence: Confidence/similarity score (0.0 - 1.0)
        timestamp: When the fact was created/extracted
        source_session_id: Session where fact originated
        source_provider: Which provider returned this fact
        metadata: Additional provider-specific metadata
        
        # Graphiti-specific (temporal)
        valid_from: When the fact became true in the real world
        valid_until: When the fact stopped being true
        entity_names: Entities involved in this fact
    """
    content: str
    fact_type: str = "fact"
    confidence: float = 1.0
    timestamp: datetime | None = None
    source_session_id: str | None = None
    source_provider: MemoryType | None = None
    metadata: dict[str, Any] | None = None

    # Graphiti-specific temporal fields
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    entity_names: list[str] | None = None

    def is_currently_valid(self) -> bool:
        """Check if this fact is currently valid (for temporal facts)."""
        if self.valid_until is None:
            return True
        return datetime.now() < self.valid_until

    def to_prompt_string(self) -> str:
        """Format fact for injection into prompt."""
        prefix = f"[{self.fact_type}]" if self.fact_type != "fact" else ""
        return f"{prefix} {self.content}".strip()


@dataclass
class MemoryContext:
    """
    Context package containing retrieved memories.
    
    Used to inject relevant context into agent prompts.
    
    Attributes:
        facts: List of retrieved facts
        summary: Optional AI-generated summary of facts
        total_facts_available: Total matching facts (may be more than returned)
        retrieval_time_ms: Time taken for retrieval
        providers_used: Which providers contributed facts
    """
    facts: list[MemoryFact] = field(default_factory=list)
    summary: str | None = None
    total_facts_available: int = 0
    retrieval_time_ms: int | None = None
    providers_used: list[MemoryType] = field(default_factory=list)

    def to_prompt_string(self, max_facts: int = 20) -> str:
        """
        Format memory context for injection into prompt.
        
        Args:
            max_facts: Maximum number of facts to include
            
        Returns:
            Formatted string ready for prompt injection
        """
        if not self.facts:
            return ""

        facts_to_use = self.facts[:max_facts]
        facts_text = "\n".join([
            f"- {fact.to_prompt_string()}"
            for fact in facts_to_use
        ])

        header = "## Relevant Memory Context\n"
        header += "The following is known about this user from previous interactions:\n"

        footer = "\nUse this context to provide personalized, consistent responses."

        if len(self.facts) > max_facts:
            footer = f"\n({len(self.facts) - max_facts} additional facts available)\n" + footer

        return f"{header}{facts_text}{footer}"

    def merge_with(self, other: "MemoryContext") -> "MemoryContext":
        """
        Merge another MemoryContext into this one.
        
        Useful for combining results from multiple providers.
        """
        merged_facts = self.facts + other.facts
        # Sort by confidence
        merged_facts.sort(key=lambda f: f.confidence, reverse=True)

        merged_providers = list(set(self.providers_used + other.providers_used))

        return MemoryContext(
            facts=merged_facts,
            total_facts_available=self.total_facts_available + other.total_facts_available,
            retrieval_time_ms=(self.retrieval_time_ms or 0) + (other.retrieval_time_ms or 0),
            providers_used=merged_providers
        )


class MemoryProviderInterface(ABC):
    """
    Abstract interface for memory providers.
    
    All memory backends (Memori, Graphiti) must implement this interface
    to be usable within the Agent Framework.
    
    Implementations handle:
    - Storing conversation interactions for fact extraction
    - Semantic recall of relevant facts
    - User context management
    - Memory cleanup
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the memory provider.
        
        Should be called once before using the provider.
        Handles database connections, schema creation, etc.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
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
        Store a conversation interaction for memory extraction.
        
        The memory provider will extract facts, preferences, entities, etc.
        from the interaction. Extraction may happen synchronously or
        asynchronously depending on the provider.
        
        Args:
            user_id: Unique user identifier (entity_id for Memori, group_id for Graphiti)
            session_id: Current session ID
            agent_id: Agent identifier (process_id for Memori)
            user_message: The user's message
            agent_response: The agent's response
            metadata: Optional additional metadata (timestamps, etc.)
            
        Returns:
            True if stored successfully
        """
        pass

    @abstractmethod
    async def recall(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int = 10,
        include_session: str | None = None
    ) -> MemoryContext:
        """
        Recall relevant memories for a given query.
        
        Uses semantic search to find facts related to the query.
        
        Args:
            user_id: User to recall memories for
            agent_id: Agent context (for process-specific memories)
            query: Search query (will be embedded for semantic search)
            limit: Maximum number of facts to return
            include_session: Optionally filter to specific session
            
        Returns:
            MemoryContext with relevant facts
        """
        pass

    @abstractmethod
    async def get_user_context(
        self,
        user_id: str,
        agent_id: str,
        context_types: list[str] | None = None
    ) -> MemoryContext:
        """
        Get all known context about a user.
        
        Retrieves general user information without a specific query.
        
        Args:
            user_id: User identifier
            agent_id: Agent context
            context_types: Filter by type ("fact", "preference", "relationship", etc.)
            
        Returns:
            MemoryContext with user's known facts
        """
        pass

    @abstractmethod
    async def clear_user_memory(
        self,
        user_id: str,
        agent_id: str | None = None
    ) -> bool:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier
            agent_id: Optional - clear only for specific agent context
            
        Returns:
            True if cleared successfully
        """
        pass

    async def close(self) -> None:
        """
        Close connections and cleanup resources.
        
        Called when the provider is no longer needed.
        """
        pass

    @property
    @abstractmethod
    def provider_type(self) -> MemoryType:
        """Return the type of memory provider."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether the provider has been initialized."""
        pass

    @property
    def supports_temporal_queries(self) -> bool:
        """
        Whether this provider supports point-in-time queries.
        
        Only Graphiti supports this via bi-temporal model.
        """
        return False

    @property
    def supports_relationships(self) -> bool:
        """
        Whether this provider supports entity relationships.
        
        Both providers support this, but Graphiti has richer support.
        """
        return False

    @property
    def supports_auto_extraction(self) -> bool:
        """
        Whether this provider automatically extracts facts.
        
        Both Memori and Graphiti do this automatically.
        """
        return True
