"""
Simple Agent Example

This example demonstrates how to create a basic conversational agent using the Agent Framework.
The agent uses LlamaIndex with OpenAI's GPT models and includes automatic memory management.

Features demonstrated:
- Basic agent setup with LlamaIndex
- Automatic conversation memory (remembers previous messages)
- Automatic model configuration from environment
- Session-based memory persistence
- Web server integration with memory support
- Basic skills usage (list_skills, load_skill)
- Agent tags and image URL for visual metadata

Usage:
    python simple_agent.py

The agent will start a web server on http://localhost:8100
Try having a conversation, then reload the page - the agent will remember your previous messages!

Skills Integration:
    This agent demonstrates basic skills usage. Try:
    - "What skills are available?" → Lists all registered skills
    - "Load the chart skill" → Loads chart generation capability

Requirements: pip install agent-framework-lib[llamaindex]
"""

import os
from typing import Any

from agent_framework.core.models import Tag
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.skills import get_skills_discovery_prompt


class CalculatorAgent(LlamaIndexAgent):
    """
    A simple calculator agent with basic math operations and skills support.

    This agent demonstrates:
    - Basic tool usage (add, multiply)
    - Skills System integration for on-demand capabilities
    - Automatic memory management
    - Agent tags and image URL for visual metadata
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="calculator_agent_v1",
            name="Calculator Agent",
            description="A helpful calculator assistant that can perform basic math operations.",
            # Tags for categorization - can be Tag objects, dicts, or strings
            tags=[
                Tag(name="example", color="#6C757D"),
                {"name": "calculator"},  # Random color will be generated
                "math",  # Random color will be generated
            ],
            image_url="https://api.dicebear.com/7.x/bottts/svg?seed=calculator",
        )
        self.current_user_id = "default_user"
        self.current_session_id: str | None = None

        # Register built-in skills for on-demand loading
        # Skills are available but not loaded until needed
        self.register_builtin_skills()

    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """Capture session context."""
        self.current_user_id = session_configuration.get("user_id", "default_user")
        self.current_session_id = session_configuration.get("session_id")
        await super().configure_session(session_configuration)

    def get_agent_prompt(self) -> str:
        """
        Define the agent's base system prompt.

        This prompt includes:
        - Core calculator behavior
        - Skills discovery instructions for on-demand capabilities

        Note: Rich content capabilities (Mermaid diagrams, Chart.js charts, forms,
        option blocks, tables) are available through the Skills System.
        Use list_skills() to see available skills and load_skill() to load them.
        """
        base_prompt = """You are a helpful calculator assistant. Use the provided tools to perform calculations.
Always be helpful and explain your calculations clearly.

You also have access to a Skills System for additional capabilities like charts, diagrams, and PDFs.
Use list_skills() to see what's available and load_skill("skill_name") to load a capability."""

        # Add skills discovery prompt for on-demand capabilities
        skills_prompt = get_skills_discovery_prompt()

        return f"{base_prompt}\n\n{skills_prompt}"

    def get_agent_tools(self) -> list[callable]:
        """
        Define the tools available to the agent.

        Returns:
            List of tools including:
            - Calculator tools (add, multiply)
            - Skill management tools (list_skills, load_skill, unload_skill)
        """

        def add(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b

        def multiply(a: int, b: int) -> int:
            """Multiply two numbers together."""
            return a * b

        # Start with calculator tools
        tools = [add, multiply]

        # Add skill management tools for on-demand capability loading
        tools.extend(self.get_skill_tools())

        return tools


def main() -> None:
    """Start the calculator agent server with UI."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key-here")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8100"))

    print("=" * 60)
    print("🚀 Starting Simple Calculator Agent Server")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print(f"🔧 Tools: add, multiply")
    print(f"🎯 Skills: Available on-demand (use list_skills)")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)

    create_basic_agent_server(
        agent_class=CalculatorAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
