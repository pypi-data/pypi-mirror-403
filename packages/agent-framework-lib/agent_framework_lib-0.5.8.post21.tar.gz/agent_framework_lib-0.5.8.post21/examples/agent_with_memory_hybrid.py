"""
Agent with Hybrid Memory (Memori + Graphiti)

Demonstrates an agent with both Memori and Graphiti memory providers.
This hybrid approach combines the best of both worlds:
- Memori: Fast SQL-based fact retrieval
- Graphiti: Complex relationship and temporal understanding

Features:
- Dual provider setup (Memori primary, Graphiti secondary)
- Merged results from both providers
- Fast simple queries via Memori
- Complex relationship queries via Graphiti

Performance Optimizations (enabled by default):
- async_store=True: Fire-and-forget storage - agent responses are not delayed
  by memory updates. Storage happens in the background.
- passive_injection_primary_only=True: Passive context injection only queries
  the fast primary provider (Memori), reducing latency from ~200-500ms to ~50-100ms.
  Active recall tools still query both providers for comprehensive results.

Requirements:
    pip install agent-framework-lib[llamaindex,memory]

    # Start FalkorDB (required for Graphiti):
    docker run -d -p 6379:6379 --name falkordb falkordb/falkordb:latest

Usage:
    python agent_with_memory_hybrid.py

The agent will start a web server on http://localhost:8103

Environment Variables for Optimization:
    MEMORY_ASYNC_STORE=true          # Enable async storage (default: true)
    MEMORY_PASSIVE_PRIMARY_ONLY=true # Primary-only passive injection (default: true)
    MEMORY_ASYNC_MAX_CONCURRENT=10   # Max concurrent background tasks
    MEMORY_ASYNC_TIMEOUT=30.0        # Shutdown timeout for pending tasks
"""

import os
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.memory import MemoryConfig




class HybridMemoryAgent(LlamaIndexAgent):
    """Agent with hybrid memory using both Memori and Graphiti."""

    def __init__(self):
        super().__init__(
            agent_id="hybrid-memory-agent",
            name="Hybrid Memory Agent",
            description="An agent with dual memory providers for comprehensive recall",
        )

    def get_memory_config(self):
        """
        Enable both Memori and Graphiti with performance optimizations.
        
        Optimization settings (enabled by default in hybrid mode):
        - async_store=True: Memory storage runs in background, doesn't block responses
        - passive_injection_primary_only=True: Only queries fast Memori for auto-context
        
        These defaults provide the best balance of speed and functionality.
        Set to False if you need synchronous storage or want passive injection
        to include Graphiti's complex relationships.
        """
        return MemoryConfig.hybrid(
            memori_database_url="sqlite:///hybrid_agent_memory.db",
            graphiti_use_falkordb=True,
            passive_injection=True,
            # Performance optimizations (these are the defaults, shown explicitly)
            async_store=True,  # Fire-and-forget storage for faster responses
            passive_injection_primary_only=True,  # Fast primary-only passive recall
        )

    def get_agent_prompt(self):
        return """You are an advanced AI assistant with hybrid memory.

Your memory system combines two complementary approaches:

1. MEMORI (SQL-based):
   - Fast retrieval of simple facts
   - Efficient for direct queries
   - Great for preferences, names, basic information

2. GRAPHITI (Knowledge Graph):
   - Complex relationship understanding
   - Temporal awareness (when things changed)
   - Entity connections and context

Memory Tools Available:
- recall_memory(query): Search both providers, get merged results
- store_memory(fact, fact_type): Save to both providers
- forget_memory(query): Mark as outdated in both providers"""

    def get_agent_tools(self):
        """Return base tools. Memory tools are added automatically by the framework."""
        return []


def main():
    """Start the hybrid memory agent server with UI."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8103"))

    print("=" * 60)
    print("🧠 Starting Hybrid Memory Agent Server (Memori + Graphiti)")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print(f"💾 Memory: Memori (SQLite) + Graphiti (FalkorDB)")
    print(f"⚡ Optimizations: async_store=True, passive_primary_only=True")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)
    print("\n⚠️  Make sure FalkorDB is running for full hybrid mode:")
    print("   docker run -d -p 6379:6379 --name falkordb falkordb/falkordb:latest")
    print("\n💡 Performance tips:")
    print("   - Async storage: responses return immediately, storage runs in background")
    print("   - Primary-only passive: fast context injection (~50-100ms vs ~200-500ms)")
    print("   - Active recall tools still query both providers for full results\n")

    create_basic_agent_server(
        agent_class=HybridMemoryAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
