"""
Skills Demo Agent - Comprehensive Skills System Demonstration

This example provides a comprehensive demonstration of the Skills System,
showing all skill management operations and best practices. Skill tools are
automatically available at initialization - no need to override get_agent_tools()
for skill tools.

Features demonstrated:
- Automatic skill tools loading (no manual tool registration needed)
- All skill management operations:
  - register_skill(): Register custom skills
  - register_builtin_skills(): Register all built-in skills
  - load_skill(): Load skill instructions on-demand
  - unload_skill(): Unload skill instructions to free context
  - list_skills(): List all available skills
  - search skills by query
- Custom skill creation
- Skill categories and metadata
- Token optimization: tools are cheap (~50 tokens), instructions loaded on-demand
- File storage integration for file-related skills

Skills Categories:
    Visualization: chart, mermaid, table
    Document: file, pdf, pdf_with_images, file_access
    Web: web_search
    Multimodal: multimodal
    UI: form, optionsblock, image_display

Usage:
    python skills_demo_agent.py

The agent will start a web server on http://localhost:8204

Example Interactions:
    - "Show me all available skills" → Lists all registered skills
    - "What visualization skills do you have?" → Searches for visualization skills
    - "Load the chart skill" → Gets detailed chart instructions
    - "Create a pie chart of expenses" → Uses chart skill tools (always available)
    - "Unload the chart skill" → Frees up the chart instructions
    - "What skills are currently loaded?" → Shows loaded skill instructions

Token Optimization:
    - System prompt: ~700 tokens (base + skills discovery)
    - Skill tools: ~50-100 tokens each (auto-loaded at init)
    - Skill instructions: ~500 tokens each (loaded on-demand via load_skill())

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

from agent_framework.core.step_display_config import StepDisplayInfo
from agent_framework.implementations import LlamaIndexAgent
from agent_framework.skills import (
    Skill,
    SkillMetadata,
    get_skills_discovery_prompt,
)
from agent_framework.storage.file_system_management import FileStorageFactory


logger = logging.getLogger(__name__)


# Example of a custom skill definition
GREETING_INSTRUCTIONS = """
## Greeting Skill Instructions

This skill provides personalized greeting capabilities.

**How to use:**
1. When a user asks for a greeting, use the greet() tool
2. Customize the greeting based on the time of day
3. Include the user's name if provided

**Greeting Guidelines:**
- Morning (5am-12pm): "Good morning!"
- Afternoon (12pm-5pm): "Good afternoon!"
- Evening (5pm-9pm): "Good evening!"
- Night (9pm-5am): "Hello!"

**Example:**
User: "Greet me, my name is Alice"
→ Use greet(name="Alice", time_of_day="morning")
→ Returns: "Good morning, Alice! How can I help you today?"
"""


def create_greeting_skill() -> Skill:
    """
    Create a custom greeting skill.

    This demonstrates how to create custom skills with:
    - Custom metadata (name, description, trigger patterns)
    - Custom instructions
    - Custom tools (defined as functions)
    """

    def greet(name: str = "friend", time_of_day: str = "day") -> str:
        """
        Generate a personalized greeting.

        Args:
            name: The name of the person to greet
            time_of_day: morning, afternoon, evening, or night

        Returns:
            A personalized greeting message
        """
        greetings = {
            "morning": f"Good morning, {name}! How can I help you today?",
            "afternoon": f"Good afternoon, {name}! What can I do for you?",
            "evening": f"Good evening, {name}! How may I assist you?",
            "night": f"Hello, {name}! Working late? How can I help?",
        }
        return greetings.get(time_of_day, f"Hello, {name}! How can I help you?")

    return Skill(
        metadata=SkillMetadata(
            name="greeting",
            description="Generate personalized greetings based on time of day",
            trigger_patterns=["greet", "hello", "hi", "good morning", "good evening"],
            category="general",
            version="1.0.0",
        ),
        instructions=GREETING_INSTRUCTIONS,
        tools=[greet],
        dependencies=[],
        config={},
        display_info=StepDisplayInfo(
            id="greet",
            friendly_name="👋 Salutation personnalisée",
            description="Génère une salutation personnalisée selon l'heure",
            icon="👋",
            category="general",
        ),
    )


class SkillsDemoAgent(LlamaIndexAgent):
    """
    Comprehensive demonstration agent for the Skills System.

    This agent showcases all skill management operations:
    - Registering built-in and custom skills
    - Loading and unloading skill instructions on-demand
    - Searching for skills by query
    - Using skill tools (always available after init)
    - Token optimization through lazy instruction loading

    Key insight: Tools are cheap (~50 tokens), instructions are expensive (~500 tokens).
    - Skill tools are auto-loaded at init (always available)
    - Skill instructions are loaded on-demand via load_skill() (token efficient)

    No need to override get_agent_tools() for skill tools - they're added automatically
    by BaseAgent._get_all_tools(). This class only adds demo-specific tools.
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="skills-demo-agent-v1",
            name="Skills Demo Agent",
            description=(
                "A demonstration agent showcasing the complete Skills System "
                "with all management operations and custom skill creation."
            ),
        )
        self.current_user_id = "default_user"
        self.current_session_id: str | None = None
        self.file_storage = None

        # Register all built-in skills
        self.register_builtin_skills()

        # Register a custom skill to demonstrate custom skill creation
        custom_skill = create_greeting_skill()
        self.register_skill(custom_skill)

        logger.info(
            f"Registered {len(self.skill_registry.list_all())} skills "
            f"({len(self.skill_registry.list_all()) - 1} built-in + 1 custom)"
        )

    async def _ensure_file_storage(self) -> None:
        """Ensure file storage is initialized for file-related skills."""
        if self.file_storage is None:
            self.file_storage = await FileStorageFactory.create_storage_manager()

    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """Configure session and initialize file storage for skills."""
        self.current_user_id = session_configuration.get("user_id", "default_user")
        self.current_session_id = session_configuration.get("session_id")

        await self._ensure_file_storage()
        self._configure_skill_tools_context()

        await super().configure_session(session_configuration)

    def _configure_skill_tools_context(self) -> None:
        """Configure file storage context for skill tools that need it."""
        for tool in self.get_loaded_skill_tools():
            if hasattr(tool, "set_context"):
                tool.set_context(
                    file_storage=self.file_storage,
                    user_id=self.current_user_id,
                    session_id=self.current_session_id,
                )

    def get_agent_prompt(self) -> str:
        """
        Define the agent's system prompt with comprehensive skills guidance.

        This prompt teaches the agent:
        - How to discover available skills
        - How to load and unload skills
        - How to search for skills by category or keyword
        - Best practices for skill management
        """
        base_prompt = """You are a demonstration agent showcasing the Skills System.

Your primary purpose is to demonstrate all skill management operations:

**Skill Discovery:**
- Use list_skills() to show all available skills
- Use search_skills(query) to find skills by keyword or category

**Skill Loading:**
- Use load_skill("skill_name") to load a skill and get its instructions
- Loading a skill makes its tools available for use
- Skills are loaded on-demand to optimize token usage

**Skill Unloading:**
- Use unload_skill("skill_name") to unload a skill when done
- This frees up context space for other skills

**Skill Status:**
- Use get_loaded_skills() to see currently loaded skills
- Use get_skills_summary() to see overall skills status

**Best Practices:**
1. Only load skills when needed for a task
2. Unload skills when done to free context
3. Search for skills before loading to find the right one
4. Follow skill instructions carefully after loading

When users ask about skills, demonstrate the relevant operations.
When users request a capability, load the appropriate skill first."""

        skills_prompt = get_skills_discovery_prompt()

        return f"{base_prompt}\n\n{skills_prompt}"

    async def get_welcome_message(self) -> str:
        """Return a comprehensive welcome message about skills."""
        all_skills = self.skill_registry.list_all()
        loaded_skills = self.skill_registry.list_loaded()

        # Group skills by category
        categories: dict[str, list[str]] = {}
        for skill in all_skills:
            cat = skill.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill.name)

        categories_text = "\n".join(
            f"  • {cat.title()}: {', '.join(sorted(names))}"
            for cat, names in sorted(categories.items())
        )

        return f"""Welcome to the Skills Demo Agent! 🎯

I'm here to demonstrate the complete Skills System.

**Available Skills ({len(all_skills)} total):**
{categories_text}

**Currently Loaded:** {len(loaded_skills)} skills
{', '.join(loaded_skills) if loaded_skills else 'None (skills are loaded on-demand)'}

**Try these commands:**
• "List all skills" - See all available skills
• "Search for visualization skills" - Find skills by category
• "Load the chart skill" - Load a specific skill
• "What skills are loaded?" - Check loaded skills
• "Unload the chart skill" - Free up a loaded skill
• "Create a bar chart" - Use a loaded skill

What would you like to explore?"""

    def get_agent_tools(self) -> list[callable]:
        """
        Return agent-specific tools for this demo.

        Note: Skill tools are automatically added by BaseAgent._get_all_tools().
        No need to manually add them here. This method only returns the
        additional demo tools (search_skills, get_loaded_skills, get_skills_summary)
        that are specific to this demonstration agent.
        """
        return self._get_demo_tools()

    def _get_demo_tools(self) -> list[callable]:
        """
        Get additional demonstration tools for skills management.

        These tools provide extra functionality for demonstrating
        the Skills System capabilities.
        """

        def search_skills(query: str) -> str:
            """
            Search for skills by keyword or category.

            Args:
                query: Search term (e.g., "chart", "visualization", "pdf")

            Returns:
                List of matching skills with descriptions
            """
            results = self.skill_registry.search(query)
            if not results:
                return f"No skills found matching '{query}'."

            lines = [f"Skills matching '{query}':"]
            for meta in results:
                status = "✓ loaded" if self.skill_registry.is_loaded(meta.name) else ""
                lines.append(f"  • {meta.name}: {meta.description} {status}")
                if meta.trigger_patterns:
                    lines.append(f"    Triggers: {', '.join(meta.trigger_patterns[:3])}")

            return "\n".join(lines)

        def get_loaded_skills() -> str:
            """
            Get the list of currently loaded skills.

            Returns:
                List of loaded skill names or message if none loaded
            """
            loaded = self.skill_registry.list_loaded()
            if not loaded:
                return "No skills are currently loaded. Use load_skill() to load one."

            lines = ["Currently loaded skills:"]
            for name in loaded:
                context = self.skill_registry.get_loaded_context(name)
                if context:
                    tool_count = len(context.tools)
                    lines.append(f"  • {name}: {tool_count} tool(s) available")

            return "\n".join(lines)

        def get_skills_summary() -> str:
            """
            Get a summary of the skills system status.

            Returns:
                Summary including total skills, loaded count, and categories
            """
            summary = self.get_skills_summary()
            all_skills = self.skill_registry.list_all()

            # Count by category
            categories: dict[str, int] = {}
            for skill in all_skills:
                cat = skill.category
                categories[cat] = categories.get(cat, 0) + 1

            lines = [
                "Skills System Summary:",
                f"  Total skills: {summary['total_skills']}",
                f"  Loaded skills: {summary['loaded_skills']}",
                "",
                "Skills by category:",
            ]
            for cat, count in sorted(categories.items()):
                lines.append(f"  • {cat}: {count}")

            if summary["loaded_skill_names"]:
                lines.append("")
                lines.append(f"Loaded: {', '.join(summary['loaded_skill_names'])}")

            return "\n".join(lines)

        return [search_skills, get_loaded_skills, get_skills_summary]


def main() -> None:
    """Start the skills demo agent server."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: No API key found")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        return

    from agent_framework import create_basic_agent_server

    port = int(os.getenv("AGENT_PORT", "8204"))

    print("=" * 70)
    print("🎯 Starting Skills Demo Agent Server")
    print("=" * 70)
    print(f"📊 Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print(f"🎯 Skills: 13 total (12 built-in + 1 custom)")
    print(f"🌐 Server: http://localhost:{port}")
    print(f"🎨 UI: http://localhost:{port}/ui")
    print("=" * 70)
    print("\n📚 This agent demonstrates all Skills System operations:")
    print("   • list_skills() - List all available skills")
    print("   • load_skill(name) - Load a skill on-demand")
    print("   • unload_skill(name) - Unload a skill")
    print("   • search_skills(query) - Search skills by keyword")
    print("   • get_loaded_skills() - Show loaded skills")
    print("   • get_skills_summary() - Get system summary")
    print("=" * 70)
    print("\n💡 Try these interactions:")
    print('   "List all skills"')
    print('   "Search for chart skills"')
    print('   "Load the mermaid skill"')
    print('   "Create a flowchart diagram"')
    print('   "What skills are loaded?"')
    print("=" * 70)

    create_basic_agent_server(
        agent_class=SkillsDemoAgent,
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
