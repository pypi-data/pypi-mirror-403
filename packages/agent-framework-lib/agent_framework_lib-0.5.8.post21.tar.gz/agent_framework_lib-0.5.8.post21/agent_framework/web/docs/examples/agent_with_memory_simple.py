"""
Agent with Simple Memori Memory (SQLite)

Demonstrates an agent with Memori memory using SQLite database.
This is the simplest memory setup - no external services required.

Features:
- SQLite-based persistent memory (no external database needed)
- Automatic fact extraction from conversations
- Passive context injection (memory auto-injected into prompts)
- Active memory tools (recall, store, forget)

Requirements:
    pip install agent-framework-lib[llamaindex,memory]

Usage:
    python agent_with_memory_simple.py

The agent will start a web server on http://localhost:8101
"""

import os
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.memory import MemoryConfig


class SimpleMemoryAgent(LlamaIndexAgent):
    """Agent with simple Memori memory using SQLite."""

    def __init__(self):
        super().__init__(
            agent_id="simple-memory-agent",
            name="Simple Memory Agent",
            description="An agent with SQLite-based memory for remembering user information",
        )

    def get_memory_config(self):
        """Enable Memori with SQLite (simplest setup)."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///simple_agent_memory.db",
            passive_injection=True,
        )

    def get_agent_prompt(self):
        return """You are a helpful assistant with long-term memory.

You can remember information about users across conversations using your memory tools:
- Use recall_memory() to search for relevant information
- Use store_memory() to save important facts
- Use forget_memory() to remove outdated information

Be proactive in using your memory to provide personalized assistance."""

    def get_agent_tools(self):
        """Return base tools. Memory tools are added automatically by the framework."""
        return []


def main():
    """Start the memory agent server with UI."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8101"))

    print("=" * 60)
    print("🧠 Starting Simple Memory Agent Server (Memori/SQLite)")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print(f"💾 Memory: Memori (SQLite)")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)

    create_basic_agent_server(
        agent_class=SimpleMemoryAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
