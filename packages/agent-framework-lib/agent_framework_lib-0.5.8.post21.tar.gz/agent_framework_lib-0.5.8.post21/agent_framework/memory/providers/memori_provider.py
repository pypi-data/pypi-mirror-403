"""
Memori Memory Provider for Agent Framework.

SQL-native memory storage with automatic fact extraction.
Best for: Quick integration, simple memory needs, SQL infrastructure.

Features:
- One-line setup with SQLite, PostgreSQL, MySQL, etc.
- Automatic fact, preference, rule extraction (background, zero-latency)
- Vectorized semantic search
- Entity/Process/Session attribution
- No graph database required

Example:
    ```python
    from agent_framework.memory.providers.memori_provider import MemoriProvider
    from agent_framework.memory.config import MemoriConfig
    
    config = MemoriConfig(database_url="sqlite:///memory.db")
    provider = MemoriProvider(config)
    await provider.initialize()
    
    # Store interaction
    await provider.store_interaction(
        user_id="user-123",
        session_id="session-456",
        agent_id="my-agent",
        user_message="My favorite color is blue",
        agent_response="I'll remember that!"
    )
    
    # Recall
    context = await provider.recall(
        user_id="user-123",
        agent_id="my-agent",
        query="What is the user's favorite color?"
    )
    ```

Version: 0.1.0
"""

import logging
from datetime import datetime
from typing import Any

from ..base import MemoryContext, MemoryFact, MemoryProviderInterface, MemoryType
from ..config import MemoriConfig


logger = logging.getLogger(__name__)

# Lazy import to avoid dependency issues if Memori not installed
MEMORI_AVAILABLE = False
_memori_import_error: str | None = None

try:
    from memori import Memori
    MEMORI_AVAILABLE = True
except ImportError as e:
    Memori = None
    _memori_import_error = str(e)


class MemoriProvider(MemoryProviderInterface):
    """
    Memori-based memory provider.
    
    Uses Memori's SQL-native storage with automatic fact extraction.
    Extraction happens in background with zero added latency.
    
    Attributes:
        config: MemoriConfig with connection settings
        
    Features:
        - SQL-native: SQLite, PostgreSQL, MySQL, MongoDB, Oracle
        - Auto-extraction: Facts, preferences, rules, relationships
        - Semantic search: Vectorized memories with similarity scoring
        - Attribution: Entity (user) → Process (agent) → Session
    """

    def __init__(self, config: MemoriConfig):
        """
        Initialize Memori provider.
        
        Args:
            config: MemoriConfig with database connection settings
            
        Raises:
            ImportError: If Memori package is not installed
        """
        if not MEMORI_AVAILABLE:
            raise ImportError(
                f"Memori is not installed. Install with: pip install memori\n"
                f"Import error: {_memori_import_error}"
            )

        self.config = config
        self._memori: Any | None = None  # Memori instance
        self._session_factory: Any | None = None
        self._openai_client: Any | None = None  # OpenAI client for fact extraction
        self._initialized = False
        self._current_attribution: dict[str, str] | None = None

    async def initialize(self) -> bool:
        """
        Initialize Memori with database connection.
        
        Creates SQLAlchemy engine and session factory, then initializes
        Memori with automatic schema creation.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            logger.debug("Memori already initialized")
            return True

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            # Create SQLAlchemy engine and session factory
            engine = create_engine(
                self.config.database_url,
                pool_pre_ping=True,  # Verify connections before use
                echo=False  # Set to True for SQL debugging
            )
            self._session_factory = sessionmaker(bind=engine)

            # Initialize Memori with session factory
            self._memori = Memori(conn=self._session_factory)

            # Build/migrate schema
            self._memori.config.storage.build()

            # Register OpenAI client with Memori for automatic fact extraction
            self._setup_openai_client()

            self._initialized = True
            logger.info(
                f"✅ Memori initialized with database: "
                f"{self._mask_connection_string(self.config.database_url)}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Memori: {e}")
            self._initialized = False
            return False

    def _mask_connection_string(self, url: str) -> str:
        """Mask password in connection string for logging."""
        if "@" in url and ":" in url:
            # Try to mask password portion
            try:
                parts = url.split("@")
                credentials = parts[0].split(":")
                if len(credentials) >= 3:
                    credentials[-1] = "****"
                    parts[0] = ":".join(credentials)
                return "@".join(parts)
            except:
                pass
        return url

    def _setup_openai_client(self) -> None:
        """
        Set up AsyncOpenAI client and register with Memori for fact extraction.
        
        Memori extracts facts by intercepting OpenAI API calls.
        We use AsyncOpenAI because we're in an async context (initialize is async).
        Memori detects the running event loop and wraps with InvokeAsync.
        """
        import os

        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning(
                "⚠️ OPENAI_API_KEY not set - Memori fact extraction will be limited. "
                "Set OPENAI_API_KEY for automatic fact extraction."
            )
            return

        try:
            from openai import AsyncOpenAI

            # Create AsyncOpenAI client (required for async context)
            self._openai_client = AsyncOpenAI(api_key=api_key)

            # Register with Memori for automatic interception
            # Memori will wrap with InvokeAsync since we're in async context
            self._memori.openai.register(self._openai_client)

            logger.debug("✅ AsyncOpenAI client registered with Memori for fact extraction")

        except ImportError:
            logger.warning(
                "⚠️ OpenAI package not installed - Memori fact extraction disabled. "
                "Install with: pip install openai"
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup OpenAI client for Memori: {e}")

    def _set_attribution(self, user_id: str, agent_id: str) -> None:
        """
        Set attribution context for Memori operations.
        
        Memori uses attribution to organize memories:
        - entity_id: The user (person, account, etc.)
        - process_id: The agent (your bot, assistant, etc.)
        """
        if not self._memori:
            return

        new_attribution = {"entity_id": user_id, "process_id": agent_id}

        # Only set if changed (optimization)
        if self._current_attribution != new_attribution:
            self._memori.attribution(
                entity_id=user_id,
                process_id=agent_id
            )
            self._current_attribution = new_attribution

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
        Store a conversation interaction for fact extraction.
        
        This method triggers fact extraction by making an LLM call through
        the Memori-registered OpenAI client. Memori intercepts this call
        and extracts facts in the background.
        
        Args:
            user_id: Unique user identifier (maps to entity_id)
            session_id: Current session ID
            agent_id: Agent identifier (maps to process_id)
            user_message: The user's message
            agent_response: The agent's response
            metadata: Optional additional metadata
            
        Returns:
            True if stored successfully
        """
        if not self._initialized or not self._memori:
            logger.warning("Memori not initialized, cannot store interaction")
            return False

        try:
            # Set attribution context
            self._set_attribution(user_id, agent_id)

            # Set session for this interaction
            self._memori.set_session(session_id)

            # Trigger fact extraction by making an LLM call through Memori
            # Memori intercepts this and extracts facts in background
            await self._trigger_fact_extraction(user_message, agent_response)

            logger.debug(
                f"📝 Memori: Stored interaction for user={user_id}, "
                f"session={session_id}, agent={agent_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store interaction in Memori: {e}")
            return False

    async def _trigger_fact_extraction(
        self,
        user_message: str,
        agent_response: str
    ) -> None:
        """
        Trigger Memori's fact extraction by making an async LLM call.
        
        Memori extracts facts by intercepting OpenAI/Anthropic calls.
        We make a minimal call with the conversation to trigger extraction.
        
        We use AsyncOpenAI client which Memori wraps with InvokeAsync,
        so we await the call directly.
        """
        if not self._openai_client:
            logger.debug("No OpenAI client registered, skipping fact extraction trigger")
            return

        try:
            # Make a minimal async LLM call that Memori will intercept
            # The actual response doesn't matter - we just need Memori to see the conversation
            await self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": agent_response}
                ],
                max_tokens=1  # Minimal tokens since we don't need the response
            )
            logger.debug("✅ Fact extraction triggered via AsyncOpenAI call")
        except Exception as e:
            # Don't fail the store operation if extraction trigger fails
            logger.debug(f"Fact extraction trigger call failed (non-critical): {e}")

    async def recall(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int = 10,
        include_session: str | None = None
    ) -> MemoryContext:
        """
        Recall relevant facts using semantic search.
        
        Uses Memori's vectorized memory search to find facts
        semantically related to the query.
        
        Args:
            user_id: User to recall memories for
            agent_id: Agent context
            query: Search query (embedded for semantic similarity)
            limit: Maximum number of facts to return
            include_session: Optional session filter (not fully supported)
            
        Returns:
            MemoryContext with relevant facts
        """
        if not self._initialized or not self._memori:
            return MemoryContext(
                facts=[],
                total_facts_available=0,
                providers_used=[MemoryType.MEMORI]
            )

        try:
            # Set attribution context
            self._set_attribution(user_id, agent_id)

            # Perform semantic search
            start_time = datetime.now()
            results = self._memori.recall(query, limit=limit)
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Convert Memori results to MemoryFact
            facts = []
            for result in results:
                # Handle both dict and object results
                if isinstance(result, dict):
                    content = result.get("content", "")
                    fact_type = result.get("type", "fact")
                    confidence = result.get("similarity", 1.0)
                    timestamp_str = result.get("created_at")
                    session_id = result.get("session_id")
                    entity_id = result.get("entity_id")
                    process_id = result.get("process_id")
                else:
                    content = getattr(result, "content", str(result))
                    fact_type = getattr(result, "type", "fact")
                    confidence = getattr(result, "similarity", 1.0)
                    timestamp_str = getattr(result, "created_at", None)
                    session_id = getattr(result, "session_id", None)
                    entity_id = getattr(result, "entity_id", None)
                    process_id = getattr(result, "process_id", None)

                # Parse timestamp if string
                timestamp = None
                if timestamp_str:
                    try:
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        elif isinstance(timestamp_str, datetime):
                            timestamp = timestamp_str
                    except:
                        pass

                fact = MemoryFact(
                    content=content,
                    fact_type=fact_type,
                    confidence=confidence,
                    timestamp=timestamp,
                    source_session_id=session_id,
                    source_provider=MemoryType.MEMORI,
                    metadata={
                        "entity_id": entity_id,
                        "process_id": process_id,
                    }
                )
                facts.append(fact)

            logger.debug(
                f"🔍 Memori recall: query='{query[:50]}...' "
                f"found {len(facts)} facts in {elapsed_ms}ms"
            )

            return MemoryContext(
                facts=facts,
                total_facts_available=len(facts),
                retrieval_time_ms=elapsed_ms,
                providers_used=[MemoryType.MEMORI]
            )

        except Exception as e:
            logger.error(f"Failed to recall from Memori: {e}")
            return MemoryContext(
                facts=[],
                total_facts_available=0,
                providers_used=[MemoryType.MEMORI]
            )

    async def get_user_context(
        self,
        user_id: str,
        agent_id: str,
        context_types: list[str] | None = None
    ) -> MemoryContext:
        """
        Get all known facts about a user.
        
        Uses a generic query to retrieve user-related facts.
        
        Args:
            user_id: User identifier
            agent_id: Agent context
            context_types: Optional filter by fact types
            
        Returns:
            MemoryContext with user's known facts
        """
        # Use a broad query to get user context
        query = "information about user"
        return await self.recall(
            user_id=user_id,
            agent_id=agent_id,
            query=query,
            limit=50  # Get more for general context
        )

    async def clear_user_memory(
        self,
        user_id: str,
        agent_id: str | None = None
    ) -> bool:
        """
        Clear memories for a user.
        
        Note: Full implementation requires direct database access.
        Current implementation logs warning.
        
        Args:
            user_id: User identifier
            agent_id: Optional agent filter
            
        Returns:
            True if cleared successfully
        """
        logger.warning(
            f"clear_user_memory for Memori requires direct DB access. "
            f"user_id={user_id}, agent_id={agent_id}"
        )
        # TODO: Implement direct SQL deletion
        return False

    async def close(self) -> None:
        """Close database connections."""
        if self._session_factory:
            # SQLAlchemy session factory doesn't need explicit close
            pass
        self._initialized = False
        self._memori = None
        logger.debug("Memori provider closed")

    @property
    def provider_type(self) -> MemoryType:
        """Return provider type."""
        return MemoryType.MEMORI

    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized

    @property
    def supports_temporal_queries(self) -> bool:
        """Memori doesn't have bi-temporal model."""
        return False

    @property
    def supports_relationships(self) -> bool:
        """Memori supports basic relationships via semantic triples."""
        return True

    # -------------------------------------------------------------------------
    # Memori-specific methods (not in base interface)
    # -------------------------------------------------------------------------

    def register_openai_client(self, client: Any) -> None:
        """
        Register OpenAI client for automatic interception.
        
        When registered, Memori automatically captures all LLM
        interactions and extracts facts in background.
        
        Args:
            client: OpenAI client instance
        """
        if not self._memori:
            logger.warning("Memori not initialized, cannot register OpenAI client")
            return

        self._memori.openai.register(client)
        logger.info("✅ OpenAI client registered with Memori for auto-extraction")

    def register_anthropic_client(self, client: Any) -> None:
        """
        Register Anthropic client for automatic interception.
        
        Args:
            client: Anthropic client instance
        """
        if not self._memori:
            logger.warning("Memori not initialized, cannot register Anthropic client")
            return

        self._memori.anthropic.register(client)
        logger.info("✅ Anthropic client registered with Memori for auto-extraction")

    def new_session(self) -> str:
        """
        Start a new Memori session.
        
        Returns:
            New session ID
        """
        if self._memori:
            self._memori.new_session()
            return self._memori.config.session_id
        return ""

    def get_current_session_id(self) -> str | None:
        """Get the current Memori session ID."""
        if self._memori:
            return self._memori.config.session_id
        return None
