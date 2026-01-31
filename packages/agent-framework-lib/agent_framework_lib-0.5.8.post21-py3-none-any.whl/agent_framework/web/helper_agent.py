"""
Framework Helper Agent

An intelligent assistant that helps developers create agents using the Agent Framework library.
Uses Memori for per-user facts/preferences and accesses shared Graphiti knowledge via tools.

Features:
- Deep knowledge of framework documentation, examples, and source code
- Model selection with Claude preference, GPT fallback
- Tools for searching documentation and examples
- Memory for user preferences and conversation context
"""

import ast
import inspect
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.model_config import model_config
from ..implementations.llamaindex_agent import LlamaIndexAgent
from ..memory.config import MemoryConfig


logger = logging.getLogger(__name__)


@dataclass
class CodeRelationship:
    """Relationship between code entities for Graphiti."""

    source_entity: str
    target_entity: str
    relationship_type: str  # "imports", "extends", "implements", "uses"
    source_file: str


@dataclass
class KnowledgeChunk:
    """A chunk of indexed knowledge."""

    content: str
    source_file: str
    chunk_type: str  # "documentation", "example", "source"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStatus:
    """Status of memory providers for framework knowledge."""

    graphiti_connected: bool
    memori_connected: bool
    indexed_files_count: int = 0

    def get_warnings(self) -> list[str]:
        """Generate user-facing warnings for degraded state."""
        warnings = []
        if not self.graphiti_connected:
            warnings.append(
                "⚠️ Graphiti not connected - limited code relationship understanding. "
                "Configure FalkorDB or Neo4j for full capabilities."
            )
        if not self.memori_connected:
            warnings.append(
                "⚠️ Memori not connected - no semantic memory across sessions. "
                "Configure a database URL."
            )
        if self.indexed_files_count == 0:
            warnings.append("⚠️ Knowledge base initializing...")
        return warnings


class FrameworkHelperAgent(LlamaIndexAgent):
    """
    Agent specialized in helping users create agents with the Agent Framework.

    This agent:
    - Uses Memori for per-user facts and preferences
    - Accesses shared Graphiti knowledge via tools (not per-user memory)
    - Prefers Claude 4.5 Sonnet, falls back to GPT-5
    - Provides tools for searching documentation and examples
    """

    _shared_knowledge_indexed: bool = False
    _shared_graphiti_client: Any | None = None
    _indexed_docs: list[str] = []
    _indexed_examples: list[str] = []
    _indexed_source: list[str] = []
    _graphiti_episode_count: int = 0  # Count from FalkorDB when reusing existing graph

    AGENT_ID = "framework_helper_v2"

    def __init__(self) -> None:
        super().__init__(
            agent_id=self.AGENT_ID,
            name="Framework Helper",
            description="Expert assistant for Agent Framework development",
        )
        self._knowledge_indexed = False
        self._memory_status: MemoryStatus | None = None

    def get_memory_config(self) -> MemoryConfig | None:
        """
        Configure hybrid memory with Memori + Graphiti (FalkorDB).

        Uses the same memory setup as other agents for consistency.
        """
        return MemoryConfig.hybrid(
            memori_database_url=os.getenv(
                "HELPER_AGENT_MEMORY_DB", "sqlite:///helper_agent_memory.db"
            ),
            graphiti_use_falkordb=True,
            passive_injection=True,
            async_store=True,
            passive_injection_primary_only=True,
        )

    def _load_llamaindex_agent_source(self) -> str:
        """
        Load the source code of LlamaIndexAgent for inclusion in the prompt.

        Uses inspect.getsource() for PyPI compatibility, with fallback to
        file reading for development mode.

        Returns:
            Source code of LlamaIndexAgent class, or placeholder if unavailable.
        """
        try:
            return inspect.getsource(LlamaIndexAgent)
        except (OSError, TypeError) as e:
            logger.debug(f"[FrameworkHelperAgent] inspect.getsource failed: {e}, trying file read")

        try:
            source_path = (
                Path(__file__).parent.parent / "implementations" / "llamaindex_agent.py"
            )
            if source_path.exists():
                return source_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"[FrameworkHelperAgent] Failed to read source file: {e}")

        return "# LlamaIndexAgent source not available"

    def _load_doc_examples(self) -> str:
        """
        Load example Python files from the examples directory.

        Loads up to 5 example files and formats them as markdown code blocks
        for inclusion in the agent prompt.

        Returns:
            Formatted markdown string with example code blocks.
        """
        examples: list[str] = []
        examples_path = self._get_examples_path()

        if not examples_path.exists():
            logger.debug(f"[FrameworkHelperAgent] Examples path not found: {examples_path}")
            return "# No examples available"

        example_files = [
            "simple_agent.py",
            "agent_with_file_storage.py",
            "agent_with_mcp.py",
            "agent_with_memory_simple.py",
            "agent_with_custom_tools_file_storage.py",
        ]

        for filename in example_files:
            file_path = examples_path / filename
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    examples.append(f"### {filename}\n```python\n{content}\n```")
                except Exception as e:
                    logger.warning(f"[FrameworkHelperAgent] Failed to read example {filename}: {e}")

            if len(examples) >= 5:
                break

        if not examples:
            return "# No examples available"

        return "\n\n".join(examples)

    def _load_tools_and_mcp_guide(self) -> str:
        """
        Load the TOOLS_AND_MCP_GUIDE.md documentation.

        Returns:
            Content of the tools guide, or empty string if not available.
        """
        docs_path = self._get_docs_path()
        guide_path = docs_path / "TOOLS_AND_MCP_GUIDE.md"

        if not guide_path.exists():
            logger.debug(f"[FrameworkHelperAgent] Tools guide not found: {guide_path}")
            return ""

        try:
            content = guide_path.read_text(encoding="utf-8", errors="ignore")
            # Truncate if too long (keep first ~15000 chars to stay within context limits)
            if len(content) > 15000:
                content = content[:15000] + "\n\n... (truncated for brevity)"
            return content
        except Exception as e:
            logger.warning(f"[FrameworkHelperAgent] Failed to read tools guide: {e}")
            return ""

    def _get_base_prompt(self) -> str:
        """
        Return the base system prompt for framework assistance.

        Returns:
            Base prompt string with framework guidance.
        """
        return """You are an expert assistant for the Agent Framework library - a Python framework for building conversational AI agents.

## Your Expertise
You have deep knowledge of:
- Framework architecture and design patterns
- Agent creation using LlamaIndexAgent base class
- Memory systems (Memori for SQL-native storage, Graphiti for knowledge graphs)
- Tool creation and MCP server integration
- Session management and state persistence
- File storage and multimodal processing
- Server to serve the agent

## How to Help Users Create Agents

When helping users create agents, guide them through these key methods:

### 1. `get_agent_prompt()` - Define the agent's personality
```python
def get_agent_prompt(self) -> str:
    return \"\"\"You are a helpful assistant that...\"\"\"
```

### 2. `get_agent_tools()` - Add capabilities
```python
def get_agent_tools(self) -> List[callable]:
    def my_tool(param: str) -> str:
        \"\"\"Tool description for the LLM.\"\"\"
        return f"Result: {param}"
    return [my_tool]
```

### 3. `initialize_agent()` - (Optional) Customize agent initialization
The default implementation uses FunctionAgent. Override only if you need custom behavior.

### 4. `get_memory_config()` - (Optional) Enable memory
```python
def get_memory_config(self) -> Optional[MemoryConfig]:
    return MemoryConfig.memori_simple(database_url="sqlite:///memory.db")
```

## Using Your Tools
Use your search tools to find relevant documentation and examples:
- `search_knowledge(query)` - Search framework for knowledge
- `list_indexed_files(type)` - List all file indexed
- `get_code_relationships(class_name)` - Query class relationships and dependencies
- `web_search(query)` - Search the web for current information (Python libs, best practices, etc.)

## Best Practices to Recommend
1. Always extend `LlamaIndexAgent` for new agents
2. Use type hints on all tool parameters
3. Write clear docstrings for tools (LLM uses them)
4. Use `MemoryConfig` for persistent memory
5. Use `create_basic_agent_server()` for quick deployment

Be helpful, provide working code examples, and explain framework concepts clearly."""

    def get_agent_prompt(self) -> str:
        """
        System prompt for framework assistance with dynamic content.

        Combines the base prompt with:
        - LlamaIndexAgent source code (for accurate reference)
        - Example agent implementations from the docs
        - Tools and MCP integration guide

        This ensures the agent has accurate, up-to-date information about
        the framework regardless of whether it's running from source or PyPI.
        """
        base_prompt = self._get_base_prompt()
        source_code = self._load_llamaindex_agent_source()
        examples = self._load_doc_examples()
        tools_guide = self._load_tools_and_mcp_guide()

        prompt = f"""{base_prompt}

## LlamaIndexAgent Source Code (Reference)
Use this as the authoritative reference for how agents should be implemented.
When documentation conflicts with source code, prioritize source code accuracy.

```python
{source_code}
```

## Example Agents from Documentation
These are complete, runnable examples showing different agent patterns:

{examples}
"""

        if tools_guide:
            prompt += f"""

## Tools and MCP Integration Guide
Complete reference for creating tools and integrating MCP servers:

{tools_guide}
"""

        return prompt

    def get_agent_tools(self) -> list[Callable[..., Any]]:
        """
        Tools for searching the knowledge base.

        These tools access the shared Graphiti knowledge graph.
        Returns FunctionTool instances with async functions to work properly
        with the event loop (same pattern as memory tools).
        """
        from llama_index.core.tools import FunctionTool

        async def search_knowledge(query: str) -> str:
            """
            Search the framework knowledge base for relevant information.

            Use this to find documentation, examples, and source code about
            the Agent Framework. This searches across ALL indexed content.

            Args:
                query: What you're looking for (e.g., "memory configuration",
                       "file storage", "MCP integration", "tools")

            Returns:
                Relevant excerpts from documentation, examples, and source code
            """
            try:
                return await self._search_graphiti(query, num_results=8)
            except Exception as e:
                logger.warning(f"Graphiti search failed: {e}")
                return self._search_indexed_content(query, "documentation")

        async def list_indexed_files(file_type: str = "all") -> str:
            """
            List all files indexed in the knowledge base.

            Use this to see what documentation, examples, and source files
            are available for searching.

            Args:
                file_type: Filter by type - "docs", "examples", "source", or "all"

            Returns:
                List of indexed files by category
            """
            # Use class-level attributes (populated during indexing)
            cls = FrameworkHelperAgent

            # Check if we're using a reused FalkorDB graph (lists are empty but episodes exist)
            has_local_lists = any([cls._indexed_docs, cls._indexed_examples, cls._indexed_source])

            if not has_local_lists:
                # Try to get episode names from FalkorDB
                if cls._shared_graphiti_client is not None:
                    try:
                        episodes = await self._get_episode_names_from_graphiti(file_type)
                        if episodes:
                            return episodes
                    except Exception as e:
                        logger.warning(f"Failed to get episode names from FalkorDB: {e}")

                if cls._graphiti_episode_count > 0:
                    return (
                        f"Knowledge base contains {cls._graphiti_episode_count} episodes "
                        "in FalkorDB (reusing existing graph).\n\n"
                        "**Indexed content includes:**\n"
                        "- Documentation files (docs/*.md)\n"
                        "- Example agents (examples/*.py)\n"
                        "- Core source files (agent_framework/core/, implementations/, etc.)\n\n"
                        "Use `search_knowledge(query)` to search across all indexed content."
                    )
                if cls._shared_knowledge_indexed:
                    return "Knowledge base is indexed but file lists are not available."
                return "No files indexed yet. Knowledge base may still be initializing."

            result = []

            if file_type in ("all", "docs"):
                docs = cls._indexed_docs or []
                if docs:
                    result.append(f"**Documentation ({len(docs)} files):**")
                    for f in docs:
                        result.append(f"  - {f}")

            if file_type in ("all", "examples"):
                examples = cls._indexed_examples or []
                if examples:
                    result.append(f"\n**Examples ({len(examples)} files):**")
                    for f in examples:
                        result.append(f"  - {f}")

            if file_type in ("all", "source"):
                source = cls._indexed_source or []
                if source:
                    result.append(f"\n**Source ({len(source)} files):**")
                    for f in source:
                        result.append(f"  - {f}")

            return "\n".join(result) if result else "No files found for the specified type."

        async def get_code_relationships(class_name: str) -> str:
            """
            Query class relationships and dependencies.

            Use this to understand how framework components relate to each other.

            Args:
                class_name: Name of the class (e.g., "LlamaIndexAgent", "BaseAgent")

            Returns:
                Information about inheritance, imports, and usage patterns
            """
            try:
                return await self._query_graphiti_relationships(class_name)
            except Exception as e:
                logger.warning(f"Graphiti relationship query failed: {e}")
                return self._query_code_relationships(class_name)

        async def web_search(query: str) -> str:
            """
            Search the web for current information using DuckDuckGo.

            Use this to find up-to-date information about Python libraries,
            best practices, or any topic not covered in the framework documentation.

            Args:
                query: Search query to look up on the web

            Returns:
                Relevant web search results with titles, snippets, and URLs
            """
            try:
                from ddgs import DDGS
            except ImportError:
                return (
                    "Web search is not available. "
                    "Install with: uv add ddgs"
                )

            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))

                if not results:
                    return f"No results found for: {query}"

                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    body = result.get("body", "No description")
                    href = result.get("href", "")
                    formatted_results.append(
                        f"{i}. **{title}**\n   {body}\n   URL: {href}"
                    )

                return f"Web search results for '{query}':\n\n" + "\n\n".join(formatted_results)

            except Exception as e:
                logger.error(f"Web search error: {e}")
                return f"Search failed: {e}"

        # Create FunctionTool instances with async_fn (same pattern as memory tools)
        return [
            FunctionTool.from_defaults(
                async_fn=search_knowledge,
                name="search_knowledge",
                description=(
                    "Search the framework knowledge base for documentation, examples, "
                    "and source code. Use for questions about Agent Framework features."
                )
            ),
            FunctionTool.from_defaults(
                async_fn=list_indexed_files,
                name="list_indexed_files",
                description=(
                    "List all files indexed in the knowledge base. "
                    "Filter by type: 'docs', 'examples', 'source', or 'all'."
                )
            ),
            FunctionTool.from_defaults(
                async_fn=get_code_relationships,
                name="get_code_relationships",
                description=(
                    "Query class relationships and dependencies. "
                    "Use to understand how framework components relate to each other."
                )
            ),
            FunctionTool.from_defaults(
                async_fn=web_search,
                name="web_search",
                description=(
                    "Search the web for current information using DuckDuckGo. "
                    "Use for Python libraries, best practices, or topics not in framework docs."
                )
            ),
        ]

    async def initialize_agent(
        self,
        model_name: str,  # noqa: ARG002 - ignored, we use _get_preferred_model()
        system_prompt: str,
        tools: list[Callable[..., Any]],
        **kwargs: Any,
    ) -> None:
        """
        Initialize with preferred model (Claude 4.5 Sonnet or GPT-5 fallback).

        Overrides the default to use model selection logic.
        The model_name parameter is ignored in favor of _get_preferred_model().
        """
        preferred_model = self._get_preferred_model()
        logger.info(f"[FrameworkHelperAgent] Using model: {preferred_model}")

        # Call parent initialize_agent with our preferred model
        # This handles FunctionAgent creation and _run_agent_stream_internal_impl assignment
        await super().initialize_agent(preferred_model, system_prompt, tools, **kwargs)

        logger.info(f"[FrameworkHelperAgent] Initialized with {len(tools)} tools")

    def _get_preferred_model(self) -> str:
        """
        Return preferred model based on environment configuration.

        Priority:
        1. HELPER_AGENT_MODEL env var (explicit override)
        2. Claude 4.5 Sonnet if ANTHROPIC_API_KEY available
        3. GPT-5 if OPENAI_API_KEY available
        4. Default model from config
        """
        # Allow explicit model override via env var
        explicit_model = os.getenv("HELPER_AGENT_MODEL")
        if explicit_model:
            logger.info(f"[FrameworkHelperAgent] Using explicit model: {explicit_model}")
            return explicit_model

        if os.getenv("ANTHROPIC_API_KEY"):
            logger.debug("[FrameworkHelperAgent] Using Claude (Anthropic key available)")
            return "claude-sonnet-4-5-20250929"
        elif os.getenv("OPENAI_API_KEY"):
            logger.debug("[FrameworkHelperAgent] Using GPT-5 (OpenAI key available)")
            return "gpt-5"
        logger.warning("[FrameworkHelperAgent] No API keys found, defaulting to gpt-4o-mini")
        return model_config.default_model

    def _search_indexed_content(self, query: str, content_type: str) -> str:
        """
        Search indexed content by type.

        Args:
            query: Search query
            content_type: Type of content ("documentation" or "example")

        Returns:
            Matching content or message if not found
        """
        if not self._shared_knowledge_indexed:
            return "Knowledge base not yet indexed. " "Please wait for initialization to complete."

        query_lower = query.lower()

        if content_type == "documentation":
            matches = self._search_docs_content(query_lower)
        else:
            matches = self._search_examples_content(query_lower)

        if not matches:
            return f"No {content_type} found matching '{query}'. Try a different search term."

        return "\n\n---\n\n".join(matches[:3])

    def _search_docs_content(self, query: str) -> list[str]:
        """Search documentation content."""
        matches: list[str] = []
        docs_path = self._get_docs_path()

        if not docs_path.exists():
            return matches

        for doc_file in self._indexed_docs:
            file_path = docs_path / doc_file
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if query in content.lower():
                    excerpt = self._extract_relevant_excerpt(content, query)
                    matches.append(f"**{doc_file}**:\n{excerpt}")

        return matches

    def _search_examples_content(self, query: str) -> list[str]:
        """Search example content."""
        matches: list[str] = []
        examples_path = self._get_examples_path()

        if not examples_path.exists():
            return matches

        for example_file in self._indexed_examples:
            file_path = examples_path / example_file
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if query in content.lower():
                    excerpt = self._extract_relevant_excerpt(content, query)
                    matches.append(f"**{example_file}**:\n```python\n{excerpt}\n```")

        return matches

    def _extract_relevant_excerpt(self, content: str, query: str, context_lines: int = 10) -> str:
        """Extract relevant excerpt around query match."""
        lines = content.split("\n")
        query_lower = query.lower()

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                return "\n".join(lines[start:end])

        return content[:500] + "..." if len(content) > 500 else content

    def _query_code_relationships(self, class_name: str) -> str:
        """
        Query code relationships for a class.

        Args:
            class_name: Name of the class to query

        Returns:
            Information about class relationships
        """
        if not self._shared_knowledge_indexed:
            return "Knowledge base not yet indexed. Please wait for initialization."

        relationships = []

        if class_name in ["LlamaIndexAgent", "BaseAgent", "AgentInterface"]:
            relationships.append(
                f"**{class_name}** is a core framework class:\n"
                "- Located in `agent_framework/implementations/` or `agent_framework/core/`\n"
                "- Implements the AgentInterface protocol\n"
                "- Provides base functionality for all agents"
            )

        if class_name == "LlamaIndexAgent":
            relationships.append(
                "**Inheritance**: LlamaIndexAgent extends BaseAgent\n"
                "**Key methods to override**:\n"
                "- `get_agent_prompt()` - Define system prompt\n"
                "- `get_agent_tools()` - Define available tools\n"
                "- `get_memory_config()` - Configure memory (optional)\n"
                "- `initialize_agent()` - Custom initialization (optional)"
            )

        if not relationships:
            return (
                f"No specific relationship information found for '{class_name}'. "
                "Try searching for 'LlamaIndexAgent', 'BaseAgent', or 'AgentInterface'."
            )

        return "\n\n".join(relationships)

    async def _get_episode_names_from_graphiti(self, file_type: str = "all") -> str | None:
        """
        Get episode names from FalkorDB directly.

        Args:
            file_type: Filter by type - "docs", "examples", "source", or "all"

        Returns:
            Formatted list of episode names, or None if failed
        """
        if self._shared_graphiti_client is None:
            return None

        try:
            from falkordb import FalkorDB

            falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
            falkordb_port = int(os.getenv("FALKORDB_PORT", "6379"))

            db = FalkorDB(host=falkordb_host, port=falkordb_port)
            graph = db.select_graph("framework_knowledge")

            # Query episode names
            result = graph.query(
                "MATCH (e:Episodic) RETURN e.name as name ORDER BY e.name"
            )

            if not result.result_set:
                return None

            # Categorize by prefix
            docs = []
            examples = []
            source = []
            other = []

            for row in result.result_set:
                name = row[0] if row[0] else "unknown"
                if name.startswith("doc:"):
                    docs.append(name.replace("doc:", ""))
                elif name.startswith("example:"):
                    examples.append(name.replace("example:", ""))
                elif name.startswith("source:"):
                    source.append(name.replace("source:", ""))
                elif name.startswith("rel:"):
                    pass  # Skip relationship episodes
                else:
                    other.append(name)

            # Build result based on filter
            result_lines = []

            if file_type in ("all", "docs") and docs:
                result_lines.append(f"**Documentation ({len(docs)} files):**")
                for f in docs:
                    result_lines.append(f"  - {f}")

            if file_type in ("all", "examples") and examples:
                if result_lines:
                    result_lines.append("")
                result_lines.append(f"**Examples ({len(examples)} files):**")
                for f in examples:
                    result_lines.append(f"  - {f}")

            if file_type in ("all", "source") and source:
                if result_lines:
                    result_lines.append("")
                result_lines.append(f"**Source ({len(source)} files):**")
                for f in source:
                    result_lines.append(f"  - {f}")

            if file_type == "all" and other:
                if result_lines:
                    result_lines.append("")
                result_lines.append(f"**Other ({len(other)} items):**")
                for f in other[:10]:  # Limit other items
                    result_lines.append(f"  - {f}")
                if len(other) > 10:
                    result_lines.append(f"  ... and {len(other) - 10} more")

            return "\n".join(result_lines) if result_lines else None

        except Exception as e:
            logger.warning(f"[FrameworkHelperAgent] Failed to query FalkorDB episodes: {e}")
            return None

    async def _search_graphiti(self, query: str, num_results: int = 10) -> str:
        """
        Search the knowledge graph using Graphiti semantic search.

        Returns ALL results without filtering - let the LLM decide what's relevant.

        Args:
            query: Search query
            num_results: Max results to return

        Returns:
            Formatted search results
        """
        if self._shared_graphiti_client is None:
            logger.debug("[FrameworkHelperAgent] Graphiti not available")
            return f"Knowledge base not connected. Query was: {query}"

        try:
            results = await self._shared_graphiti_client.search(
                query=query,
                num_results=num_results,
            )

            if not results:
                return f"No results found for: {query}"

            formatted = []
            for i, result in enumerate(results, 1):
                fact = getattr(result, "fact", None) or str(result)
                name = getattr(result, "name", "") or ""
                source = getattr(result, "source_description", "") or ""

                header = f"**[{i}] {name}**" if name else f"**[{i}]**"
                if source:
                    header += f" ({source})"
                formatted.append(f"{header}\n{fact}")

            return "\n\n---\n\n".join(formatted)

        except Exception as e:
            logger.error(f"[FrameworkHelperAgent] Graphiti search error: {e}")
            return f"Search failed: {e}"

    async def _search_graphiti_docs(self, query: str) -> str:
        """Search documentation - delegates to unified search."""
        return await self._search_graphiti(f"documentation {query}", num_results=5)

    async def _search_graphiti_examples(self, query: str) -> str:
        """
        Search example code using Graphiti semantic search.

        Uses the shared Graphiti client to perform semantic search on indexed
        example files with group_id="framework_knowledge".

        Args:
            query: Search query describing the pattern or feature

        Returns:
            Formatted search results with file names and code snippets
        """
        if self._shared_graphiti_client is None:
            logger.debug("[FrameworkHelperAgent] Graphiti not available, using fallback search")
            return self._search_indexed_content(query, "example")

        try:
            results = await self._shared_graphiti_client.search(
                query=query,
                num_results=5,
                group_ids=["framework_knowledge"],
            )

            if not results:
                return self._search_indexed_content(query, "example")

            formatted_results = []
            for result in results:
                fact = getattr(result, "fact", None) or str(result)
                source_desc = getattr(result, "source_description", "") or ""
                episode_name = getattr(result, "name", "") or ""

                # Match examples: "example:" prefix OR "Example agent" in source OR .py file
                is_example = (
                    "example:" in episode_name
                    or "example" in source_desc.lower()
                    or episode_name.endswith(".py")
                )
                if is_example:
                    source_file = (
                        episode_name.replace("example:", "") if episode_name else "unknown"
                    )
                    formatted_results.append(f"**{source_file}**:\n```python\n{fact}\n```")

            if not formatted_results:
                # No filtered results, return all results
                for result in results:
                    fact = getattr(result, "fact", None) or str(result)
                    episode_name = getattr(result, "name", "") or "unknown"
                    formatted_results.append(f"**{episode_name}**:\n```python\n{fact}\n```")

            if not formatted_results:
                return self._search_indexed_content(query, "example")

            return "\n\n---\n\n".join(formatted_results[:3])

        except Exception as e:
            logger.warning(f"[FrameworkHelperAgent] Graphiti example search failed: {e}")
            return self._search_indexed_content(query, "example")

    async def _query_graphiti_relationships(self, class_name: str) -> str:
        """
        Query Graphiti for actual class relationships and dependencies.

        Uses the shared Graphiti client to search for relationship facts
        about the specified class.

        Args:
            class_name: Name of the class to query relationships for

        Returns:
            Structured information about class dependencies
        """
        if self._shared_graphiti_client is None:
            logger.debug("[FrameworkHelperAgent] Graphiti not available, using fallback")
            return self._query_code_relationships(class_name)

        try:
            results = await self._shared_graphiti_client.search(
                query=f"{class_name} extends imports implements uses",
                num_results=10,
                group_ids=["framework_knowledge"],
            )

            if not results:
                return self._query_code_relationships(class_name)

            relationships = []
            extends_list = []
            imports_list = []
            uses_list = []

            for result in results:
                fact = getattr(result, "fact", None) or str(result)
                episode_name = getattr(result, "name", "")

                if "rel:" in episode_name and class_name.lower() in fact.lower():
                    if "extends" in fact.lower():
                        extends_list.append(fact)
                    elif "imports" in fact.lower():
                        imports_list.append(fact)
                    elif "uses" in fact.lower():
                        uses_list.append(fact)
                    else:
                        relationships.append(fact)

            formatted_output = [f"**Relationships for {class_name}**:\n"]

            if extends_list:
                formatted_output.append("**Inheritance:**")
                for ext in extends_list[:3]:
                    formatted_output.append(f"  - {ext}")

            if imports_list:
                formatted_output.append("\n**Imports:**")
                for imp in imports_list[:5]:
                    formatted_output.append(f"  - {imp}")

            if uses_list:
                formatted_output.append("\n**Uses:**")
                for use in uses_list[:3]:
                    formatted_output.append(f"  - {use}")

            if relationships:
                formatted_output.append("\n**Other relationships:**")
                for rel in relationships[:3]:
                    formatted_output.append(f"  - {rel}")

            if len(formatted_output) == 1:
                return self._query_code_relationships(class_name)

            return "\n".join(formatted_output)

        except Exception as e:
            logger.warning(f"[FrameworkHelperAgent] Graphiti relationship query failed: {e}")
            return self._query_code_relationships(class_name)

    @classmethod
    def _get_docs_path(cls) -> Path:
        """Get path to docs directory."""
        return Path(__file__).parent.parent.parent / "docs"

    @classmethod
    def _get_examples_path(cls) -> Path:
        """Get path to examples directory."""
        return Path(__file__).parent.parent.parent / "examples"

    @classmethod
    def _get_source_path(cls) -> Path:
        """Get path to agent_framework source directory."""
        return Path(__file__).parent.parent

    @classmethod
    async def index_shared_knowledge(cls, graphiti_client: Any | None = None) -> None:
        """
        Index framework knowledge ONCE into shared Graphiti instance (not per-user).

        This is called at server startup, not per-user session.
        All users access this shared knowledge via tools.

        Args:
            graphiti_client: Optional Graphiti client for knowledge graph storage.
                            If provided, content will be indexed into Graphiti using add_episode.
        """
        if cls._shared_knowledge_indexed:
            logger.info("[FrameworkHelperAgent] Knowledge already indexed, skipping")
            return

        logger.info("[FrameworkHelperAgent] Starting knowledge indexing...")
        cls._shared_graphiti_client = graphiti_client

        indexing_errors: list[str] = []

        # Index documentation files
        doc_errors = await cls._index_documentation_async()
        indexing_errors.extend(doc_errors)

        # Index example files
        example_errors = await cls._index_examples_async()
        indexing_errors.extend(example_errors)

        # Index source files with relationship extraction
        source_errors = await cls._index_source_files_async()
        indexing_errors.extend(source_errors)

        cls._shared_knowledge_indexed = True
        total = len(cls._indexed_docs) + len(cls._indexed_examples) + len(cls._indexed_source)
        logger.info(f"[FrameworkHelperAgent] Indexed {total} files successfully")

        if indexing_errors:
            logger.warning(
                f"[FrameworkHelperAgent] {len(indexing_errors)} indexing errors occurred"
            )
            for error in indexing_errors[:5]:  # Log first 5 errors
                logger.warning(f"  - {error}")

    @classmethod
    async def _index_documentation_async(cls) -> list[str]:
        """
        Index documentation files from docs directory into Graphiti.

        Returns:
            List of error messages for files that failed to index
        """
        errors: list[str] = []
        docs_path = cls._get_docs_path()

        if not docs_path.exists():
            logger.warning(f"[FrameworkHelperAgent] Docs path not found: {docs_path}")
            return errors

        for md_file in docs_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                cls._indexed_docs.append(md_file.name)

                # Index into Graphiti if client is available
                if cls._shared_graphiti_client is not None:
                    await cls._add_episode_to_graphiti(
                        name=f"doc:{md_file.name}",
                        content=content,
                        source_description=f"Framework documentation: {md_file.name}",
                        chunk_type="documentation",
                    )
                    # Rate limit protection: wait between indexing operations
                    await asyncio.sleep(2.0)

                logger.debug(f"[FrameworkHelperAgent] Indexed doc: {md_file.name}")

            except Exception as e:
                error_msg = f"Error indexing doc {md_file.name}: {e}"
                logger.error(f"[FrameworkHelperAgent] {error_msg}")
                errors.append(error_msg)

        logger.info(f"[FrameworkHelperAgent] Indexed {len(cls._indexed_docs)} documentation files")
        return errors

    @classmethod
    async def _index_examples_async(cls) -> list[str]:
        """
        Index example agent files from examples directory into Graphiti.

        Returns:
            List of error messages for files that failed to index
        """
        errors: list[str] = []
        examples_path = cls._get_examples_path()

        if not examples_path.exists():
            logger.warning(f"[FrameworkHelperAgent] Examples path not found: {examples_path}")
            return errors

        for py_file in examples_path.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                cls._indexed_examples.append(py_file.name)

                # Index into Graphiti if client is available
                if cls._shared_graphiti_client is not None:
                    await cls._add_episode_to_graphiti(
                        name=f"example:{py_file.name}",
                        content=content,
                        source_description=f"Example agent code: {py_file.name}",
                        chunk_type="example",
                    )
                    # Rate limit protection: wait between indexing operations
                    await asyncio.sleep(2.0)

                logger.debug(f"[FrameworkHelperAgent] Indexed example: {py_file.name}")

            except Exception as e:
                error_msg = f"Error indexing example {py_file.name}: {e}"
                logger.error(f"[FrameworkHelperAgent] {error_msg}")
                errors.append(error_msg)

        logger.info(f"[FrameworkHelperAgent] Indexed {len(cls._indexed_examples)} example files")
        return errors

    @classmethod
    async def _index_source_files_async(cls) -> list[str]:
        """
        Index key source code files from agent_framework directory into Graphiti.

        Also extracts class relationships using AST parsing.

        Returns:
            List of error messages for files that failed to index
        """
        errors: list[str] = []
        source_path = cls._get_source_path()

        if not source_path.exists():
            logger.warning(f"[FrameworkHelperAgent] Source path not found: {source_path}")
            return errors

        key_files = [
            # Core framework
            "core/agent_interface.py",
            "core/base_agent.py",
            "core/model_clients.py",
            "core/model_config.py",
            # Implementations
            "implementations/llamaindex_agent.py",
            # Memory system
            "memory/__init__.py",
            "memory/config.py",
            "memory/manager.py",
            "memory/agent_mixin.py",
            "memory/base.py",
            "memory/tools.py",
            "memory/providers/__init__.py",
            "memory/providers/graphiti_provider.py",
            "memory/providers/memori_provider.py",
            # Session storage
            "session/session_storage.py",
            "session/elasticsearch_session_storage.py",
            # File storage
            "storage/file_storages.py",
            "storage/file_system_management.py",
            "storage/storage_optimizer.py",
            # Tools
            "tools/__init__.py",
            "tools/base.py",
            "tools/file_tools.py",
            "tools/file_access_tools.py",
            "tools/pdf_tools.py",
            "tools/pdf_with_images_tool.py",
            "tools/chart_tools.py",
            "tools/mermaid_tools.py",
            "tools/tabledata_tools.py",
            "tools/multimodal_tools.py",
            "tools/web_search_tools.py",
            "tools/adaptive_pdf_css.py",
            "tools/html_content_analyzer.py",
            "tools/pdf_image_scaler.py",
            "tools/sizing_config.py",
            # Web server
            "web/server.py",
        ]

        for rel_path in key_files:
            file_path = source_path / rel_path
            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                cls._indexed_source.append(rel_path)

                # Index into Graphiti if client is available
                if cls._shared_graphiti_client is not None:
                    await cls._add_episode_to_graphiti(
                        name=f"source:{rel_path}",
                        content=content,
                        source_description=f"Framework source code: {rel_path}",
                        chunk_type="source",
                    )

                    # Extract and index relationships
                    relationships = cls._extract_code_relationships(content, rel_path)
                    for rel in relationships:
                        await cls._add_relationship_to_graphiti(rel)

                logger.debug(f"[FrameworkHelperAgent] Indexed source: {rel_path}")

            except Exception as e:
                error_msg = f"Error indexing source {rel_path}: {e}"
                logger.error(f"[FrameworkHelperAgent] {error_msg}")
                errors.append(error_msg)

        logger.info(f"[FrameworkHelperAgent] Indexed {len(cls._indexed_source)} source files")
        return errors

    @classmethod
    async def _add_episode_to_graphiti(
        cls,
        name: str,
        content: str,
        source_description: str,
        chunk_type: str,
        max_retries: int = 3,
    ) -> bool:
        """
        Add an episode to the shared Graphiti knowledge graph with retry logic.

        Args:
            name: Unique name for the episode
            content: The content to index
            source_description: Description of the content source
            chunk_type: Type of content (documentation, example, source)
            max_retries: Maximum number of retry attempts for rate limit errors

        Returns:
            True if successfully added, False otherwise
        """
        if cls._shared_graphiti_client is None:
            return False

        try:
            from graphiti_core.nodes import EpisodeType
        except ImportError:
            logger.debug(
                "[FrameworkHelperAgent] graphiti_core not available, skipping Graphiti indexing"
            )
            return False

        group_id = "framework_knowledge"
        full_description = f"[{chunk_type}] {source_description}"

        for attempt in range(max_retries):
            try:
                await cls._shared_graphiti_client.add_episode(
                    name=name,
                    episode_body=content,
                    source_description=full_description,
                    source=EpisodeType.text,
                    reference_time=datetime.now(),
                    group_id=group_id,
                )

                logger.debug(
                    f"[FrameworkHelperAgent] Added {chunk_type} episode to Graphiti: {name}"
                )
                return True

            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = "rate limit" in error_str or "429" in error_str

                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(
                        f"[FrameworkHelperAgent] Rate limit hit for {name}, "
                        f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.warning(
                        f"[FrameworkHelperAgent] Failed to add episode to Graphiti: {e}"
                    )
                    return False

        return False

    @classmethod
    def _extract_code_relationships(cls, content: str, source_file: str) -> list[CodeRelationship]:
        """
        Extract class relationships from Python source code using AST.

        Extracts:
        - Class inheritance (extends)
        - Import statements (imports)

        Args:
            content: Python source code content
            source_file: Path to the source file

        Returns:
            List of CodeRelationship objects
        """
        relationships: list[CodeRelationship] = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"[FrameworkHelperAgent] Syntax error parsing {source_file}: {e}")
            return relationships

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    relationships.append(
                        CodeRelationship(
                            source_entity=source_file,
                            target_entity=alias.name,
                            relationship_type="imports",
                            source_file=source_file,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    target = f"{module}.{alias.name}" if module else alias.name
                    relationships.append(
                        CodeRelationship(
                            source_entity=source_file,
                            target_entity=target,
                            relationship_type="imports",
                            source_file=source_file,
                        )
                    )

        # Extract class definitions and inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for base in node.bases:
                    base_name = cls._get_ast_name(base)
                    if base_name:
                        relationships.append(
                            CodeRelationship(
                                source_entity=class_name,
                                target_entity=base_name,
                                relationship_type="extends",
                                source_file=source_file,
                            )
                        )

        return relationships

    @classmethod
    def _get_ast_name(cls, node: ast.expr) -> str | None:
        """Extract name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = cls._get_ast_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        return None

    @classmethod
    async def _add_relationship_to_graphiti(cls, relationship: CodeRelationship) -> bool:
        """
        Add a code relationship to Graphiti as structured data.

        Args:
            relationship: The CodeRelationship to add

        Returns:
            True if successfully added, False otherwise
        """
        if cls._shared_graphiti_client is None:
            return False

        try:
            # Import EpisodeType for Graphiti
            try:
                from graphiti_core.nodes import EpisodeType
            except ImportError:
                return False

            # Format relationship as a fact statement
            fact_statement = (
                f"{relationship.source_entity} {relationship.relationship_type} "
                f"{relationship.target_entity} (in {relationship.source_file})"
            )

            group_id = "framework_knowledge"

            await cls._shared_graphiti_client.add_episode(
                name=f"rel:{relationship.source_entity}:{relationship.target_entity}",
                episode_body=fact_statement,
                source_description=f"Code relationship from {relationship.source_file}",
                source=EpisodeType.text,
                reference_time=datetime.now(),
                group_id=group_id,
            )

            return True

        except Exception as e:
            logger.debug(f"[FrameworkHelperAgent] Failed to add relationship: {e}")
            return False

    def _check_graphiti_connection(self) -> bool:
        """
        Check if Graphiti knowledge graph is connected via memory system.

        Returns:
            True if Graphiti is configured and available
        """
        # Check if memory manager has Graphiti configured
        if hasattr(self, "_memory_manager") and self._memory_manager is not None:
            if hasattr(self._memory_manager, "_secondary_provider"):
                return self._memory_manager._secondary_provider is not None

        # Fallback: check memory config
        memory_config = self.get_memory_config()
        if memory_config and memory_config.graphiti:
            return True

        return False

    def _check_memori_connection(self) -> bool:
        """
        Check if Memori SQL memory is connected.

        Returns:
            True if Memori database is accessible
        """
        memory_config = self.get_memory_config()
        if memory_config is None:
            return False

        db_url = os.getenv("HELPER_AGENT_MEMORY_DB", "sqlite:///helper_agent_memory.db")

        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if db_path.startswith("/"):
                return Path(db_path).parent.exists()
            return True

        return True

    def get_memory_status_warnings(self) -> list[str]:
        """
        Check memory providers and return warnings for UI.

        Checks:
        - Graphiti connection status (for code relationships)
        - Memori connection status (for user facts/preferences)
        - Number of indexed files

        Returns:
            List of warning messages for degraded state
        """
        graphiti_connected = self._check_graphiti_connection()
        memori_connected = self._check_memori_connection()

        # Use get_indexed_files_count which handles both local lists and FalkorDB count
        indexed_count = self.get_indexed_files_count()

        self._memory_status = MemoryStatus(
            graphiti_connected=graphiti_connected,
            memori_connected=memori_connected,
            indexed_files_count=indexed_count,
        )

        return self._memory_status.get_warnings()

    @classmethod
    def get_indexed_files_count(cls) -> int:
        """Get total count of indexed files."""
        local_count = len(cls._indexed_docs) + len(cls._indexed_examples) + len(cls._indexed_source)
        # If we have a count from FalkorDB (reused graph), use that if local is empty
        if local_count == 0 and cls._graphiti_episode_count > 0:
            return cls._graphiti_episode_count
        return local_count

    @classmethod
    def is_knowledge_indexed(cls) -> bool:
        """Check if knowledge has been indexed."""
        return cls._shared_knowledge_indexed
