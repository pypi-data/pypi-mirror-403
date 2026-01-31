"""
Example: Agent with Long-Term Memory

Demonstrates how to create an agent with memory capabilities using:
- Memori (SQL-native, simple setup)
- Graphiti (Knowledge graph, temporal)
- Hybrid mode (both providers)

Requirements:
    pip install agent-framework-lib[llamaindex,memory]
    
    # For Graphiti with FalkorDB:
    docker run -d -p 6379:6379 falkordb/falkordb:latest

Environment:
    export OPENAI_API_KEY=sk-...
    
    # Optional: Configure memory via environment
    export MEMORY_PRIMARY_PROVIDER=memori
    export MEMORI_DATABASE_URL=sqlite:///agent_memory.db
"""

import asyncio
import logging
from agent_framework import LlamaIndexAgent
from agent_framework.memory import MemoryConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Simple Memori Memory (SQLite)
# ============================================================================

class SimpleMemoryAgent(LlamaIndexAgent):
    """Agent with simple Memori memory using SQLite."""
    
    def __init__(self):
        super().__init__(
            agent_id="simple-memory-agent",
            name="Simple Memory Agent",
            description="An agent with SQLite-based memory"
        )
    
    def get_memory_config(self):
        """Enable Memori with SQLite (simplest setup)."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///simple_agent_memory.db",
            passive_injection=True  # Auto-inject context
        )
    
    def get_agent_prompt(self):
        return """You are a helpful assistant with long-term memory.
        
You can remember information about users across conversations using your memory tools:
- Use recall_memory() to search for relevant information
- Use store_memory() to save important facts
- Use forget_memory() to remove outdated information

Be proactive in using your memory to provide personalized assistance."""


# ============================================================================
# Example 2: Graphiti Memory (Knowledge Graph)
# ============================================================================

class GraphMemoryAgent(LlamaIndexAgent):
    """Agent with Graphiti knowledge graph memory."""
    
    def __init__(self):
        super().__init__(
            agent_id="graph-memory-agent",
            name="Graph Memory Agent",
            description="An agent with temporal knowledge graph memory"
        )
    
    def get_memory_config(self):
        """Enable Graphiti with FalkorDB."""
        return MemoryConfig.graphiti_simple(
            use_falkordb=True,
            falkordb_host="localhost",
            falkordb_port=6379,
            passive_injection=True
        )
    
    def get_agent_prompt(self):
        return """You are an intelligent assistant with advanced memory capabilities.

Your memory system understands:
- Temporal relationships (when things happened)
- Entity relationships (how things are connected)
- Contradictions (when information changes)

Use your memory tools to provide context-aware, personalized responses."""


# ============================================================================
# Example 3: Hybrid Memory (Both Memori + Graphiti)
# ============================================================================

class HybridMemoryAgent(LlamaIndexAgent):
    """Agent with both Memori and Graphiti for best of both worlds."""
    
    def __init__(self):
        super().__init__(
            agent_id="hybrid-memory-agent",
            name="Hybrid Memory Agent",
            description="An agent with dual memory providers"
        )
    
    def get_memory_config(self):
        """Enable both Memori (fast) and Graphiti (advanced)."""
        return MemoryConfig.hybrid(
            memori_database_url="sqlite:///hybrid_agent_memory.db",
            graphiti_use_falkordb=True,
            passive_injection=True
        )
    
    def get_agent_prompt(self):
        return """You are an advanced AI assistant with hybrid memory.

Your memory combines:
- Fast SQL-based fact retrieval (Memori)
- Complex relationship understanding (Graphiti)

This gives you both speed and depth in understanding user context."""


# ============================================================================
# Example 4: Memory Without Passive Injection (Tools Only)
# ============================================================================

class ActiveMemoryAgent(LlamaIndexAgent):
    """Agent that only uses memory tools (no passive injection)."""
    
    def __init__(self):
        super().__init__(
            agent_id="active-memory-agent",
            name="Active Memory Agent",
            description="An agent that actively manages its memory"
        )
    
    def get_memory_config(self):
        """Enable memory tools but disable passive injection."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///active_agent_memory.db",
            passive_injection=False  # Agent decides when to use memory
        )
    
    def get_agent_prompt(self):
        return """You are a helpful assistant with memory tools.

You have access to memory tools but context is NOT automatically injected.
You must actively decide when to:
- recall_memory() to search for relevant information
- store_memory() to save important facts
- forget_memory() to remove outdated information

This gives you full control over memory usage and token efficiency."""


# ============================================================================
# Demo Functions
# ============================================================================

async def demo_simple_memory():
    """Demo simple Memori memory."""
    print("\n" + "="*70)
    print("DEMO 1: Simple Memori Memory (SQLite)")
    print("="*70 + "\n")
    
    agent = SimpleMemoryAgent()
    
    # First conversation
    print("👤 User: My name is Alice and I love Python programming.")
    response = await agent.handle_message(
        user_id="alice",
        session_id="session-1",
        message="My name is Alice and I love Python programming."
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Second conversation (new session)
    print("👤 User: What's my name and what do I like?")
    response = await agent.handle_message(
        user_id="alice",
        session_id="session-2",
        message="What's my name and what do I like?"
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Check memory status
    status = agent.get_memory_status()
    print(f"📊 Memory Status: {status}\n")


async def demo_graph_memory():
    """Demo Graphiti knowledge graph memory."""
    print("\n" + "="*70)
    print("DEMO 2: Graphiti Knowledge Graph Memory")
    print("="*70 + "\n")
    
    agent = GraphMemoryAgent()
    
    # Store temporal information
    print("👤 User: I moved from Paris to London last month.")
    response = await agent.handle_message(
        user_id="bob",
        session_id="session-1",
        message="I moved from Paris to London last month."
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Query with temporal awareness
    print("👤 User: Where do I live now?")
    response = await agent.handle_message(
        user_id="bob",
        session_id="session-2",
        message="Where do I live now?"
    )
    print(f"🤖 Agent: {response.text}\n")


async def demo_hybrid_memory():
    """Demo hybrid memory (both providers)."""
    print("\n" + "="*70)
    print("DEMO 3: Hybrid Memory (Memori + Graphiti)")
    print("="*70 + "\n")
    
    agent = HybridMemoryAgent()
    
    # Store complex information
    print("👤 User: I work at Acme Corp as a Software Engineer. My colleague Bob is on my team.")
    response = await agent.handle_message(
        user_id="charlie",
        session_id="session-1",
        message="I work at Acme Corp as a Software Engineer. My colleague Bob is on my team."
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Query relationships
    print("👤 User: Tell me about my work situation.")
    response = await agent.handle_message(
        user_id="charlie",
        session_id="session-2",
        message="Tell me about my work situation."
    )
    print(f"🤖 Agent: {response.text}\n")


async def demo_active_memory():
    """Demo active memory (tools only, no passive injection)."""
    print("\n" + "="*70)
    print("DEMO 4: Active Memory (Tools Only)")
    print("="*70 + "\n")
    
    agent = ActiveMemoryAgent()
    
    # Agent must actively use tools
    print("👤 User: Please remember that I prefer dark mode.")
    response = await agent.handle_message(
        user_id="dave",
        session_id="session-1",
        message="Please remember that I prefer dark mode."
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Agent must actively recall
    print("👤 User: What are my preferences?")
    response = await agent.handle_message(
        user_id="dave",
        session_id="session-2",
        message="What are my preferences?"
    )
    print(f"🤖 Agent: {response.text}\n")


async def demo_memory_tools():
    """Demo explicit memory tool usage."""
    print("\n" + "="*70)
    print("DEMO 5: Explicit Memory Tool Usage")
    print("="*70 + "\n")
    
    agent = SimpleMemoryAgent()
    
    # Explicit store
    print("👤 User: Remember that my favorite color is blue.")
    response = await agent.handle_message(
        user_id="eve",
        session_id="session-1",
        message="Remember that my favorite color is blue."
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Explicit recall
    print("👤 User: What's my favorite color?")
    response = await agent.handle_message(
        user_id="eve",
        session_id="session-2",
        message="What's my favorite color?"
    )
    print(f"🤖 Agent: {response.text}\n")
    
    # Explicit forget
    print("👤 User: Forget my favorite color.")
    response = await agent.handle_message(
        user_id="eve",
        session_id="session-3",
        message="Forget my favorite color."
    )
    print(f"🤖 Agent: {response.text}\n")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all demos."""
    print("\n🧠 Agent Framework - Memory Module Examples")
    print("=" * 70)
    
    try:
        # Run demos
        await demo_simple_memory()
        
        # Uncomment to run other demos:
        # await demo_graph_memory()  # Requires FalkorDB
        # await demo_hybrid_memory()  # Requires FalkorDB
        # await demo_active_memory()
        # await demo_memory_tools()
        
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
    
    print("\n✅ Demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
