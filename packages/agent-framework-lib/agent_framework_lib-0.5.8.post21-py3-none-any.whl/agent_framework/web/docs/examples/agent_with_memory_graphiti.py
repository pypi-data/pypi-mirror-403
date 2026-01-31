"""
Agent with Graphiti Knowledge Graph Memory (FalkorDB)

Demonstrates an agent with Graphiti temporal knowledge graph memory.
Graphiti excels at understanding relationships and temporal changes.

Features:
- Temporal knowledge graph (understands when facts change over time)
- Entity relationship extraction (people, places, organizations)
- Bi-temporal model (valid_at, invalid_at for fact validity)

Requirements:
    pip install agent-framework-lib[llamaindex,memory]

    # Start FalkorDB (required):
    docker run -d -p 6379:6379 --name falkordb falkordb/falkordb:latest

Usage:
    python agent_with_memory_graphiti.py

The agent will start a web server on http://localhost:8102
"""

import os
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.memory import MemoryConfig


class GraphMemoryAgent(LlamaIndexAgent):
    """Agent with Graphiti knowledge graph memory."""

    def __init__(self):
        super().__init__(
            agent_id="graph-memory-agent",
            name="Graph Memory Agent",
            description="An agent with temporal knowledge graph memory",
        )

    def get_memory_config(self):
        """Enable Graphiti with FalkorDB."""
        return MemoryConfig.graphiti_simple(
            use_falkordb=True,
            falkordb_host=os.getenv("FALKORDB_HOST", "localhost"),
            falkordb_port=int(os.getenv("FALKORDB_PORT", "6379")),
            passive_injection=True,
        )

    def get_agent_prompt(self):
        return """You are an intelligent assistant with advanced temporal memory.

Your memory system understands:
- TEMPORAL RELATIONSHIPS: When things happened and how they changed over time
- ENTITY RELATIONSHIPS: How people, places, and organizations are connected
- CONTRADICTIONS: When information changes or conflicts

Memory Tools Available:
- recall_memory(query): Search for relevant information with temporal context
- store_memory(fact, fact_type): Save facts with automatic entity extraction
- forget_memory(query): Mark information as outdated"""

    def get_agent_tools(self):
        """Return base tools. Memory tools are added automatically by the framework."""
        return []


def main():
    """Start the graph memory agent server with UI."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8102"))

    print("=" * 60)
    print("🧠 Starting Graph Memory Agent Server (Graphiti/FalkorDB)")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-5-mini')}")
    print(f"💾 Memory: Graphiti (FalkorDB)")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)
    print("\n⚠️  Make sure FalkorDB is running:")
    print("   docker run -d -p 6379:6379 --name falkordb falkordb/falkordb:latest\n")

    create_basic_agent_server(
        agent_class=GraphMemoryAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
