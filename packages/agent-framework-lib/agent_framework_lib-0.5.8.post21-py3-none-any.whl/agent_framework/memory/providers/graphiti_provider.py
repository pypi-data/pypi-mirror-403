"""
Graphiti Memory Provider for Agent Framework.

Temporal Knowledge Graph with bi-temporal model for advanced memory.
Best for: Complex reasoning, temporal queries, entity relationships.

Features:
- Bi-temporal model (when fact was true + when we learned it)
- Automatic contradiction detection and resolution
- Complex entity relationships with graph traversal
- Hybrid search (semantic + keyword + graph)
- Point-in-time queries

Requires Neo4j or FalkorDB as graph database backend.

Example:
    ```python
    from agent_framework.memory.providers.graphiti_provider import GraphitiProvider
    from agent_framework.memory.config import GraphitiConfig

    # Simple setup with FalkorDB
    config = GraphitiConfig(use_falkordb=True)
    provider = GraphitiProvider(config)
    await provider.initialize()

    # Store interaction
    await provider.store_interaction(
        user_id="user-123",
        session_id="session-456",
        agent_id="my-agent",
        user_message="I moved from Paris to London last month",
        agent_response="I'll update your location."
    )

    # Recall with temporal awareness
    context = await provider.recall(
        user_id="user-123",
        agent_id="my-agent",
        query="Where does the user live?"
    )
    # Returns: "User lives in London" (with valid_from timestamp)
    ```

Version: 0.1.0
"""

import logging
import re
from datetime import datetime
from typing import Any

from ..base import MemoryContext, MemoryFact, MemoryProviderInterface, MemoryType
from ..config import GraphitiConfig


logger = logging.getLogger(__name__)


def _sanitize_for_redisearch(text: str) -> str:
    """
    Sanitize text to avoid RediSearch syntax errors.

    RediSearch has special characters that need escaping or removal:
    - | (OR operator)
    - / (path separator, causes issues)
    - @ (field prefix)
    - : (field separator)
    - ( ) (grouping)
    - [ ] (range)
    - { } (tag)
    - " (phrase)
    - ~ (fuzzy)
    - * (wildcard)
    - - (negation)
    - ' (escape)

    We replace problematic characters with spaces to preserve word boundaries.
    """
    # Characters that cause RediSearch syntax errors
    special_chars = r'[|/@:(){}\[\]"~*\-\'\\/]'
    # Replace with space to preserve word boundaries
    sanitized = re.sub(special_chars, " ", text)
    # Collapse multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized.strip()


# Lazy import to avoid dependency issues if Graphiti not installed
GRAPHITI_AVAILABLE = False
_graphiti_import_error: str | None = None

try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    GRAPHITI_AVAILABLE = True
except ImportError as e:
    Graphiti = None
    EpisodeType = None
    _graphiti_import_error = str(e)


class GraphitiProvider(MemoryProviderInterface):
    """
    Graphiti-based memory provider.

    Uses temporal knowledge graph for advanced memory capabilities.

    Architecture:
        - Episodic Subgraph: Raw events/messages with timestamps
        - Semantic Subgraph: Extracted entities and relationships
        - Community Subgraph: Entity clusters for navigation

    Bi-temporal Model:
        - t_valid / t_invalid: When fact was true in real world
        - t_created / t_expired: When fact was added/removed in system

    Environment Isolation:
        Set GRAPHITI_ENVIRONMENT to prefix group_ids (e.g., dev_user123, prod_user123).
        This allows multiple environments to share the same Neo4j/FalkorDB instance.

    Attributes:
        config: GraphitiConfig with connection settings
    """

    def __init__(self, config: GraphitiConfig):
        """
        Initialize Graphiti provider.

        Args:
            config: GraphitiConfig with database connection settings

        Raises:
            ImportError: If Graphiti package is not installed
        """
        if not GRAPHITI_AVAILABLE:
            raise ImportError(
                f"Graphiti is not installed. Install with: pip install graphiti-core\n"
                f"For FalkorDB support: pip install graphiti-core[falkordb]\n"
                f"Import error: {_graphiti_import_error}"
            )

        self.config = config
        self._graphiti: Any | None = None
        self._initialized = False
        # Cache of Graphiti instances per user_id (for FalkorDB multi-tenant support)
        self._user_graphiti_cache: dict[str, Any] = {}

    def _sanitize_group_id(self, value: str) -> str:
        """
        Sanitize a string to be valid as a Graphiti group_id.
        
        Graphiti requires group_id to contain only alphanumeric characters,
        dashes, or underscores. This method replaces invalid characters.
        
        Args:
            value: The raw string (e.g., email address)
            
        Returns:
            Sanitized string safe for use as group_id
            
        Examples:
            - "elliott.girard@icloud.com" → "elliott_girard_at_icloud_com"
            - "user+test@example.org" → "user_test_at_example_org"
            - "simple_user" → "simple_user" (unchanged)
        """
        # Replace @ with _at_ for readability
        sanitized = value.replace("@", "_at_")
        # Replace dots with underscores
        sanitized = sanitized.replace(".", "_")
        # Replace any other invalid characters with underscores
        # Valid: alphanumeric, dash, underscore
        sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "_", sanitized)
        # Collapse multiple underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        return sanitized

    def _build_group_id(self, user_id: str) -> str:
        """
        Build group_id with optional environment prefix.

        Allows isolation of data by environment (dev, prod, preprod, etc.)
        while sharing the same Neo4j/FalkorDB instance.
        
        The user_id is sanitized to ensure it only contains valid characters
        (alphanumeric, dashes, underscores) as required by Graphiti.

        Args:
            user_id: The user identifier (can be email or any string)

        Returns:
            group_id with environment prefix if configured, sanitized for Graphiti

        Examples:
            - user_id="user@example.com", env="dev" → "dev_user_at_example_com"
            - user_id="simple_user", env="prod" → "prod_simple_user"
            - user_id="user123", env="" → "user123"
        """
        # Sanitize user_id to remove invalid characters (e.g., @ and . in emails)
        sanitized_user_id = self._sanitize_group_id(user_id)
        
        env = self.config.environment
        group_id = f"{env}_{sanitized_user_id}" if env else sanitized_user_id
        
        # Debug logging to trace user_id → group_id mapping
        logger.info(f"🔑 Graphiti group_id: user_id='{user_id}' → group_id='{group_id}'")
        
        return group_id

    async def initialize(self) -> bool:
        """
        Initialize Graphiti with graph database connection.

        Supports Neo4j or FalkorDB as backend.
        Creates necessary indices for efficient search (unless skip_index_creation is True).

        Returns:
            True if initialization successful
        """
        if self._initialized:
            logger.debug("Graphiti already initialized")
            return True

        try:
            if self.config.use_falkordb:
                await self._initialize_falkordb()
            else:
                await self._initialize_neo4j()

            # Build indices for efficient search (skip if configured)
            if not self.config.skip_index_creation:
                # Note: graphiti-core >= 0.24 uses build_indices_and_constraints
                if hasattr(self._graphiti, "build_indices_and_constraints"):
                    await self._graphiti.build_indices_and_constraints()
                elif hasattr(self._graphiti, "build_indices"):
                    await self._graphiti.build_indices()
            else:
                logger.info("⏭️ Skipping index creation (skip_index_creation=True)")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Graphiti: {e}")
            self._initialized = False
            return False

    async def _initialize_falkordb(self) -> None:
        """Initialize with FalkorDB backend."""
        try:
            from graphiti_core.driver.falkordb_driver import FalkorDriver
        except ImportError:
            raise ImportError(
                "FalkorDB driver not available. Install with: "
                "pip install graphiti-core[falkordb]"
            )

        # Create default driver (will be used for initialization)
        driver = FalkorDriver(
            host=self.config.falkordb_host,
            port=self.config.falkordb_port,
            password=self.config.falkordb_password,
        )

        self._graphiti = Graphiti(graph_driver=driver)

        logger.info(
            f"✅ Graphiti initialized with FalkorDB: "
            f"{self.config.falkordb_host}:{self.config.falkordb_port}"
        )

    async def _get_user_graphiti(self, user_id: str) -> Any:
        """
        Get or create a Graphiti instance for a specific user.

        FalkorDB uses the group_id as a separate database name, so we need
        to create a driver with the group_id (with env prefix) as the database name
        for searches to work correctly.

        Args:
            user_id: User identifier

        Returns:
            Graphiti instance configured for the user's database
        """
        if not self.config.use_falkordb:
            # Neo4j uses group_id as a filter, not separate databases
            return self._graphiti

        # Build group_id with environment prefix
        group_id = self._build_group_id(user_id)

        if group_id in self._user_graphiti_cache:
            return self._user_graphiti_cache[group_id]

        try:
            from graphiti_core.driver.falkordb_driver import FalkorDriver

            driver = FalkorDriver(
                host=self.config.falkordb_host,
                port=self.config.falkordb_port,
                password=self.config.falkordb_password,
                database=group_id,  # Use group_id (with env prefix) as database name
            )

            user_graphiti = Graphiti(graph_driver=driver)
            await user_graphiti.build_indices_and_constraints()

            self._user_graphiti_cache[group_id] = user_graphiti
            logger.debug(f"Created Graphiti instance for database: {group_id}")

            return user_graphiti

        except Exception as e:
            logger.warning(f"Failed to create user-specific Graphiti: {e}, using default")
            return self._graphiti

    async def _initialize_neo4j(self) -> None:
        """Initialize with Neo4j backend."""
        self._graphiti = Graphiti(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
        )

        logger.info(f"✅ Graphiti initialized with Neo4j: {self.config.neo4j_uri}")

    async def store_interaction(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: str,
        agent_response: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Store interaction as Graphiti episodes.

        Creates episodes for both user message and agent response.
        Graphiti automatically extracts entities, facts, and relationships.

        The group_id parameter isolates data per user (multi-tenant).

        Args:
            user_id: User identifier (maps to group_id for isolation)
            session_id: Current session ID
            agent_id: Agent identifier
            user_message: The user's message
            agent_response: The agent's response
            metadata: Optional additional metadata

        Returns:
            True if stored successfully
        """
        if not self._initialized or not self._graphiti:
            logger.warning("Graphiti not initialized, cannot store interaction")
            return False

        async def _try_add_episode(name: str, body: str, description: str) -> bool:
            """Try to add episode, with fallback to sanitized version on RediSearch errors."""
            try:
                await self._graphiti.add_episode(
                    name=name,
                    episode_body=body,
                    source_description=description,
                    source=EpisodeType.message,
                    reference_time=datetime.now(),
                    group_id=self._build_group_id(user_id),
                )
                return True
            except Exception as e:
                error_str = str(e)
                # Check if it's a RediSearch syntax error
                if "RediSearch" in error_str and "Syntax error" in error_str:
                    logger.warning(
                        f"RediSearch syntax error, retrying with sanitized content: {error_str[:100]}"
                    )
                    # Retry with sanitized content
                    sanitized_body = _sanitize_for_redisearch(body)
                    try:
                        await self._graphiti.add_episode(
                            name=name,
                            episode_body=sanitized_body,
                            source_description=description,
                            source=EpisodeType.message,
                            reference_time=datetime.now(),
                            group_id=self._build_group_id(user_id),
                        )
                        logger.debug("Successfully stored episode with sanitized content")
                        return True
                    except Exception as retry_error:
                        logger.error(f"Failed to store even with sanitized content: {retry_error}")
                        return False
                else:
                    raise

        try:
            timestamp = datetime.now()

            # Store only user message as episode
            # Agent responses are NOT stored to avoid extracting facts from agent's own output
            # Facts should come from what the user says, not what the agent proposes
            user_success = await _try_add_episode(
                name=f"user_{session_id}_{timestamp.timestamp()}",
                body=user_message,
                description="User message",
            )

            if user_success:
                logger.debug(
                    f"📝 Graphiti: Stored user message for user={user_id}, " f"session={session_id}"
                )
            return user_success

        except Exception as e:
            logger.error(f"Failed to store interaction in Graphiti: {e}")
            return False

    async def recall(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        limit: int = 10,
        include_session: str | None = None,
    ) -> MemoryContext:
        """
        Recall relevant facts using hybrid search.

        Combines:
        - Semantic similarity (embeddings)
        - Keyword search (BM25)
        - Graph traversal

        Args:
            user_id: User to recall memories for (group_id filter)
            agent_id: Agent context
            query: Search query
            limit: Maximum facts to return
            include_session: Optional session filter

        Returns:
            MemoryContext with relevant facts (including temporal metadata)
        """
        if not self._initialized or not self._graphiti:
            return MemoryContext(
                facts=[], total_facts_available=0, providers_used=[MemoryType.GRAPHITI]
            )

        try:
            start_time = datetime.now()

            # Sanitize query to avoid RediSearch syntax errors
            # Characters like /, |, @, etc. can cause parsing issues
            sanitized_query = _sanitize_for_redisearch(query)

            if not sanitized_query:
                logger.debug("Query was empty after sanitization, returning empty context")
                return MemoryContext(
                    facts=[], total_facts_available=0, providers_used=[MemoryType.GRAPHITI]
                )

            # Get user-specific Graphiti instance for FalkorDB
            # FalkorDB uses group_id as database name, so we need a separate driver
            user_graphiti = await self._get_user_graphiti(user_id)

            # Search for relevant edges (facts/relationships)
            # Note: graphiti-core >= 0.24 uses 'num_results' instead of 'limit'
            results = await user_graphiti.search(
                query=sanitized_query,
                num_results=limit,
                # Don't pass group_ids for FalkorDB as it uses separate databases
            )

            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Convert Graphiti results to MemoryFact
            facts = []
            for result in results:
                fact = self._convert_edge_to_fact(result)
                if fact:
                    facts.append(fact)

            logger.debug(
                f"🔍 Graphiti recall: query='{query[:50]}...' "
                f"found {len(facts)} facts in {elapsed_ms}ms"
            )

            return MemoryContext(
                facts=facts,
                total_facts_available=len(facts),
                retrieval_time_ms=elapsed_ms,
                providers_used=[MemoryType.GRAPHITI],
            )

        except Exception as e:
            logger.error(f"Failed to recall from Graphiti: {e}")
            return MemoryContext(
                facts=[], total_facts_available=0, providers_used=[MemoryType.GRAPHITI]
            )

    def _convert_edge_to_fact(self, edge: Any) -> MemoryFact | None:
        """Convert a Graphiti edge to MemoryFact."""
        try:
            # Extract fact content
            content = getattr(edge, "fact", None) or str(edge)

            # Extract temporal information (Graphiti's bi-temporal model)
            valid_from = getattr(edge, "valid_at", None)
            valid_until = getattr(edge, "invalid_at", None)
            created_at = getattr(edge, "created_at", None)

            # Extract entity names
            source_name = getattr(edge, "source_node_name", None)
            target_name = getattr(edge, "target_node_name", None)
            entity_names = [n for n in [source_name, target_name] if n]

            # Extract score if available
            confidence = getattr(edge, "score", 1.0)
            if confidence is None:
                confidence = 1.0

            return MemoryFact(
                content=content,
                fact_type="relationship" if entity_names else "fact",
                confidence=confidence,
                timestamp=created_at,
                source_provider=MemoryType.GRAPHITI,
                valid_from=valid_from,
                valid_until=valid_until,
                entity_names=entity_names if entity_names else None,
                metadata={
                    "edge_uuid": getattr(edge, "uuid", None),
                    "episode_uuid": getattr(edge, "episode_uuid", None),
                    "edge_name": getattr(edge, "name", None),
                },
            )

        except Exception as e:
            logger.warning(f"Failed to convert Graphiti edge to fact: {e}")
            return None

    async def get_user_context(
        self, user_id: str, agent_id: str, context_types: list[str] | None = None
    ) -> MemoryContext:
        """
        Get entity summaries and relationships for user.

        Uses search to retrieve relevant facts about the user.
        Note: graphiti-core >= 0.24 removed get_nodes_by_query,
        so we use search() instead.

        Args:
            user_id: User identifier
            agent_id: Agent context
            context_types: Optional filter (not used currently)

        Returns:
            MemoryContext with entity summaries
        """
        if not self._initialized or not self._graphiti:
            return MemoryContext(
                facts=[], total_facts_available=0, providers_used=[MemoryType.GRAPHITI]
            )

        try:
            start_time = datetime.now()

            # Get user-specific Graphiti instance for FalkorDB
            user_graphiti = await self._get_user_graphiti(user_id)

            # Use search to get relevant facts about user
            # Note: get_nodes_by_query was removed in graphiti-core >= 0.24
            results = await user_graphiti.search(
                query="user information preferences",
                num_results=20,
            )

            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            facts = []
            for result in results:
                fact = self._convert_edge_to_fact(result)
                if fact:
                    facts.append(fact)

            return MemoryContext(
                facts=facts,
                total_facts_available=len(facts),
                retrieval_time_ms=elapsed_ms,
                providers_used=[MemoryType.GRAPHITI],
            )

        except Exception as e:
            logger.error(f"Failed to get user context from Graphiti: {e}")
            return MemoryContext(
                facts=[], total_facts_available=0, providers_used=[MemoryType.GRAPHITI]
            )

    async def clear_user_memory(self, user_id: str, agent_id: str | None = None) -> bool:
        """
        Clear all memories for a user.

        Removes all graph data associated with the user's group_id.

        Args:
            user_id: User identifier (group_id)
            agent_id: Not used (Graphiti doesn't partition by agent)

        Returns:
            True if cleared successfully
        """
        if not self._initialized or not self._graphiti:
            return False

        try:
            group_id = self._build_group_id(user_id)
            await self._graphiti.clear_graph(group_ids=[group_id])
            logger.info(f"🗑️ Cleared Graphiti memory for group_id {group_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear Graphiti memory: {e}")
            return False

    async def close(self) -> None:
        """Close graph database connections."""
        if self._graphiti:
            # Graphiti handles connection cleanup internally
            pass
        self._initialized = False
        self._graphiti = None
        logger.debug("Graphiti provider closed")

    @property
    def provider_type(self) -> MemoryType:
        """Return provider type."""
        return MemoryType.GRAPHITI

    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized

    @property
    def supports_temporal_queries(self) -> bool:
        """Graphiti has full bi-temporal model."""
        return True

    @property
    def supports_relationships(self) -> bool:
        """Graphiti is a full knowledge graph."""
        return True

    # -------------------------------------------------------------------------
    # Graphiti-specific methods (not in base interface)
    # -------------------------------------------------------------------------

    async def query_at_time(
        self, user_id: str, query: str, point_in_time: datetime, limit: int = 10
    ) -> MemoryContext:
        """
        Query facts as they were known at a specific point in time.

        Graphiti's bi-temporal model allows reconstructing the state
        of knowledge at any historical moment.

        Args:
            user_id: User identifier
            query: Search query
            point_in_time: The moment to query knowledge state
            limit: Maximum facts to return

        Returns:
            MemoryContext with facts valid at that time
        """
        # Get all facts first
        context = await self.recall(
            user_id=user_id, agent_id="", query=query, limit=limit * 2  # Get more to filter
        )

        # Filter to facts valid at point_in_time
        valid_facts = []
        for fact in context.facts:
            # Check if fact was valid at that time
            if fact.valid_from and fact.valid_from > point_in_time:
                continue  # Fact wasn't true yet
            if fact.valid_until and fact.valid_until <= point_in_time:
                continue  # Fact had already become invalid
            valid_facts.append(fact)

        return MemoryContext(
            facts=valid_facts[:limit],
            total_facts_available=len(valid_facts),
            retrieval_time_ms=context.retrieval_time_ms,
            providers_used=[MemoryType.GRAPHITI],
        )

    async def add_structured_data(
        self, user_id: str, data: dict[str, Any], source_description: str = "Structured data"
    ) -> bool:
        """
        Add structured JSON data to the knowledge graph.

        Graphiti can ingest JSON data and extract entities/relationships.

        Args:
            user_id: User identifier (group_id)
            data: JSON-serializable data
            source_description: Description of the data source

        Returns:
            True if added successfully
        """
        if not self._initialized or not self._graphiti:
            return False

        try:
            import json

            await self._graphiti.add_episode(
                name=f"data_{datetime.now().timestamp()}",
                episode_body=json.dumps(data),
                source_description=source_description,
                source=EpisodeType.json,
                reference_time=datetime.now(),
                group_id=self._build_group_id(user_id),
            )

            logger.debug(f"📊 Added structured data for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add structured data to Graphiti: {e}")
            return False

    async def get_entity_relationships(
        self, user_id: str, entity_name: str, limit: int = 20
    ) -> MemoryContext:
        """
        Get all relationships for a specific entity.

        Uses graph traversal to find connected facts.

        Args:
            user_id: User identifier
            entity_name: Name of the entity to query
            limit: Maximum relationships to return

        Returns:
            MemoryContext with entity's relationships
        """
        return await self.recall(user_id=user_id, agent_id="", query=entity_name, limit=limit)
