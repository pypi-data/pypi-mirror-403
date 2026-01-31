"""
Skill management tools for agents.

This module provides tools that agents can use to discover, load, and unload skills
at runtime. These tools enable dynamic capability acquisition based on task needs.

Key Functions:
    - list_skills: List all available skills with descriptions
    - load_skill: Load a skill to gain its capabilities and tools
    - unload_skill: Unload a skill to free up context space
    - create_skill_tools: Factory function to create skill tools for a registry
"""

from typing import TYPE_CHECKING, Callable


if TYPE_CHECKING:
    from .base import SkillRegistry


def list_skills(registry: "SkillRegistry") -> str:
    """
    List all available skills with their descriptions.

    Returns a lightweight summary of available skills that can be loaded
    to gain specific capabilities. Each skill shows its name, description,
    and whether it's currently loaded.

    Args:
        registry: The SkillRegistry to query

    Returns:
        Formatted list of available skills with names and descriptions
    """
    skills = registry.list_all()
    if not skills:
        return "No skills available."

    lines = ["Available Skills:"]
    for meta in skills:
        status = "✓ loaded" if registry.is_loaded(meta.name) else ""
        lines.append(f"- {meta.name}: {meta.description} {status}")

    return "\n".join(lines)


def load_skill(registry: "SkillRegistry", skill_name: str) -> str:
    """
    Load a skill to gain its capabilities and tools.

    Loading a skill injects detailed instructions into the context
    and activates the skill's associated tools. Dependencies are
    automatically loaded first.

    Args:
        registry: The SkillRegistry to use
        skill_name: Name of the skill to load

    Returns:
        Success message with loaded instructions, or error message
    """
    try:
        context = registry.load(skill_name)

        tool_names = [_get_tool_name(t) for t in context.tools]

        return (
            f"Skill '{skill_name}' loaded successfully.\n\n"
            f"Tools available: {', '.join(tool_names) if tool_names else 'None'}\n\n"
            f"Instructions:\n{context.instructions}"
        )
    except ValueError as e:
        return f"Error loading skill: {str(e)}"


def unload_skill(registry: "SkillRegistry", skill_name: str) -> str:
    """
    Unload a skill to free up context space.

    Unloading a skill deactivates its tools and removes it from
    the loaded set. This can be useful in long conversations to
    free up tool slots.

    Args:
        registry: The SkillRegistry to use
        skill_name: Name of the skill to unload

    Returns:
        Success or informative message
    """
    if not registry.is_loaded(skill_name):
        return f"Skill '{skill_name}' is not loaded."

    registry.unload(skill_name)
    return f"Skill '{skill_name}' unloaded successfully."


def _get_tool_name(tool: object) -> str:
    """
    Extract a display name from a tool object.

    Tries various attributes to find a suitable name.

    Args:
        tool: The tool object

    Returns:
        A string name for the tool
    """
    # Try common name attributes
    if hasattr(tool, "name"):
        return str(tool.name)
    if hasattr(tool, "__name__"):
        return str(tool.__name__)
    # Fall back to class name or string representation
    if hasattr(tool, "__class__"):
        return tool.__class__.__name__
    return str(tool)


def create_skill_tools(registry: "SkillRegistry") -> list[Callable[..., str]]:
    """
    Create skill management tools bound to a specific registry.

    This factory function creates closures that capture the registry,
    allowing the tools to be used by agents without needing to pass
    the registry explicitly.

    Args:
        registry: The SkillRegistry to bind to the tools

    Returns:
        List of callable tools: [list_skills, load_skill, unload_skill]

    Example:
        registry = SkillRegistry()
        tools = create_skill_tools(registry)
        list_skills_tool, load_skill_tool, unload_skill_tool = tools

        # Agent can now call these directly
        print(list_skills_tool())
        print(load_skill_tool("chart"))
    """

    def list_skills_tool() -> str:
        """
        List all available skills with their descriptions.

        Returns a lightweight summary of available skills that can be loaded
        to gain specific capabilities.

        Returns:
            Formatted list of available skills with names and descriptions
        """
        return list_skills(registry)

    def load_skill_tool(skill_name: str) -> str:
        """
        Load a skill to gain its capabilities and tools.

        Loading a skill injects detailed instructions into the context
        and activates the skill's associated tools.

        Args:
            skill_name: Name of the skill to load

        Returns:
            Success message with loaded instructions summary, or error message
        """
        return load_skill(registry, skill_name)

    def unload_skill_tool(skill_name: str) -> str:
        """
        Unload a skill to free up context space.

        Args:
            skill_name: Name of the skill to unload

        Returns:
            Success or error message
        """
        return unload_skill(registry, skill_name)

    return [list_skills_tool, load_skill_tool, unload_skill_tool]


__all__ = [
    "list_skills",
    "load_skill",
    "unload_skill",
    "create_skill_tools",
]
