"""
Multi-Skills Agent Example

This example demonstrates how to create an agent that uses the Skills System
for on-demand capability loading. Skill tools are automatically available
at initialization - no need to override get_agent_tools().

Features demonstrated:
- Automatic skill tools loading (no manual tool registration needed)
- On-demand skill instruction loading via load_skill()
- Skill management tools (list_skills, load_skill, unload_skill)
- Token optimization: tools are cheap (~50 tokens), instructions loaded on-demand

Skills Available:
    Visualization: chart, mermaid, table
    Document: file, pdf, pdf_with_images, file_access
    Web: web_search
    Multimodal: multimodal
    UI: form, optionsblock, image_display

Usage:
    python agent_example_multi_skills.py

The agent will start a web server on http://localhost:8203
Try asking the agent to:
- "List available skills" → Shows all registered skills
- "Create a bar chart" → Agent uses chart skill tools directly
- "Generate a flowchart diagram" → Agent uses mermaid skill tools
- "Create a PDF report" → Agent uses pdf skill tools

Token Optimization:
    - System prompt: ~700 tokens (base + skills discovery)
    - Skill tools: ~50-100 tokens each (auto-loaded at init)
    - Skill instructions: ~500 tokens each (loaded on-demand via load_skill())
    - vs. Old approach: ~3500 tokens in every system prompt

Requirements:
    uv add agent-framework-lib[llamaindex]
"""

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from agent_framework.core.models import Tag
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.storage.file_system_management import FileStorageFactory
from agent_framework.memory import MemoryConfig


logger = logging.getLogger(__name__)


class MultiSkillsAgent(LlamaIndexAgent):
    """
    An agent that demonstrates the Skills System with automatic tool loading.

    This agent uses the SkillsMixin (inherited via LlamaIndexAgent) to gain:
    - Automatic registration of built-in skills
    - Automatic loading of ALL skill tools at initialization
    - Skill management tools (list_skills, load_skill, unload_skill)

    Key insight: Tools are cheap (~50 tokens), instructions are expensive (~500 tokens).
    - Skill tools are auto-loaded at init (always available)
    - Skill instructions are loaded on-demand via load_skill() (token efficient)

    No need to override get_agent_tools() - skill tools are added automatically
    by BaseAgent._get_all_tools().
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="multi-skills-agent-v1",
            name="Multi-Skills Agent",
            description=(
                "A versatile assistant that can dynamically load specialized skills "
                "for charts, diagrams, PDFs, file operations, web search, and more."
            ),
            tags=[
                Tag(name="files", color="#17A2B8"),
                {"name": "storage"},
                "pdf",
            ],
            image_url="https://api.dicebear.com/7.x/bottts/svg?seed=filestorage",
        )
        self.current_user_id = "default_user"
        self.current_session_id: str | None = None
        self.file_storage = None

        # Note: Built-in skills are automatically registered by BaseAgent.__init__
        # No need to call register_builtin_skills() manually
        logger.info(f"Registered {len(self.skill_registry.list_all())} built-in skills")
    def get_memory_config(self) -> MemoryConfig:
        """Configure Graphiti memory with FalkorDB backend."""
        return MemoryConfig.graphiti_simple(
            use_falkordb=True,
            falkordb_host=os.getenv("FALKORDB_HOST", "localhost"),
            falkordb_port=int(os.getenv("FALKORDB_PORT", "6379")),
            environment=os.getenv("ENVIRONMENT", "dev"),
            passive_injection=False,
            skip_index_creation=True,
        )

    async def _ensure_file_storage(self) -> None:
        """Ensure file storage is initialized for file-related skills."""
        if self.file_storage is None:
            self.file_storage = await FileStorageFactory.create_storage_manager()

    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """Configure session and initialize file storage for skills."""
        self.current_user_id = session_configuration.get("user_id", "default_user")
        self.current_session_id = session_configuration.get("session_id")

        # Initialize file storage for file-related skills
        await self._ensure_file_storage()

        # Call parent to build the agent (this collects skill tool instances)
        await super().configure_session(session_configuration)

        # Configure context for ALL registered skill tools
        # This must be called AFTER super().configure_session()
        self.configure_skill_tools_context(
            file_storage=self.file_storage,
            user_id=self.current_user_id,
            session_id=self.current_session_id,
        )

    def get_agent_prompt(self) -> str:
        """
        Define the agent's system prompt with skills discovery.

        The skills discovery prompt is automatically appended by BaseAgent.get_system_prompt()
        when skills are enabled. This teaches the agent to:
        - Use list_skills() to see available skills
        - Use load_skill("name") to get detailed instructions
        - Use skill tools directly (they're already available)
        """
        return """You are a versatile assistant with access to a Skills System.

Your capabilities are organized into skills. Skill tools are always available to you.
Use list_skills() to see all available skills and their descriptions.
Use load_skill("skill_name") to get detailed instructions for using a skill.

When a user asks for something:
1. Use the appropriate skill tools directly (they're already available)
2. If you need guidance, load the skill to get detailed instructions
3. Follow the skill's instructions to complete the task

Be proactive about using your capabilities to help users."""

    def get_agent_tools(self) -> list[callable]:
        """
        Return agent-specific tools.

        Note: Skill tools are automatically added by BaseAgent._get_all_tools().
        No need to manually add them here. This method only needs to return
        any custom tools specific to this agent (none in this case).
        """
        return []

    async def get_welcome_message(self) -> str:
        """Return a welcome message showing available skills."""
        skills = self.skill_registry.list_all()
        skill_categories: dict[str, list[str]] = {}

        for skill in skills:
            category = skill.category
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill.name)

        categories_text = "\n".join(
            f"  - {cat.title()}: {', '.join(names)}" for cat, names in skill_categories.items()
        )

        return f"""Hello! I'm the {self.name}.

I have access to {len(skills)} skills organized by category:
{categories_text}

Skill tools are already available - just ask me to:
- Create charts, diagrams, or tables
- Generate PDF documents
- Search the web
- Analyze images
- And more!

What would you like me to help you with?"""


def main() -> None:
    """Start the multi-skills agent server."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: No API key found")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8204"))

    print("=" * 60)
    print("🚀 Starting Multi-Skills Agent Server")
    print("=" * 60)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print("🎯 Skills: 12 built-in skills (tools auto-loaded)")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 60)
    print("\nTry asking:")
    print("  - 'List available skills'")
    print("  - 'Create a bar chart of monthly sales'")
    print("  - 'Generate a flowchart diagram'")
    print("  - 'Create a PDF report'")
    print("=" * 60)

    create_basic_agent_server(
        agent_class=MultiSkillsAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
