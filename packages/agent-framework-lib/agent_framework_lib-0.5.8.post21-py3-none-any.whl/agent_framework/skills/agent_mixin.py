"""
Skills Mixin for BaseAgent.

Provides skills capabilities to agents via mixin pattern.
This allows clean integration without modifying the core BaseAgent class.

Usage:
    ```python
    from agent_framework.core.base_agent import BaseAgent
    from agent_framework.skills.agent_mixin import SkillsMixin

    class MyAgent(SkillsMixin, BaseAgent):
        pass

    # Skills are automatically available
    agent = MyAgent(agent_id="my-agent", name="My Agent", description="...")
    agent.register_builtin_skills()
    context = agent.load_skill("chart")
    ```

The mixin provides:
- Skill registry management
- Skill registration, loading, and unloading
- Access to skill tools for agent use
- Combined instructions from loaded skills
- Combined tools from loaded skills
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .base import LoadedSkillContext, Skill, SkillRegistry


logger = logging.getLogger(__name__)


class SkillsMixin:
    """
    Mixin that adds skills capabilities to agents.

    Agents that inherit this mixin gain:
    - A skill registry for managing skills
    - Methods to register, load, and unload skills
    - Access to skill management tools
    - Combined instructions and tools from loaded skills

    Attributes:
        _skill_registry: SkillRegistry instance for managing skills
        _skill_tools: Cached skill management tools
        _skill_tool_instances: List of AgentTool instances that need context configuration
    """

    # These will be set by the agent class
    agent_id: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize skills mixin."""
        # Import here to avoid circular imports
        from .base import SkillRegistry

        # Initialize skills attributes before super().__init__
        self._skill_registry: SkillRegistry = SkillRegistry()
        self._skill_tools: list[Callable[..., str]] = []
        self._skill_tool_instances: list[Any] = []

        # Call parent __init__
        super().__init__(*args, **kwargs)

    @property
    def skill_registry(self) -> "SkillRegistry":
        """
        Access the skill registry.

        Returns:
            The SkillRegistry instance for this agent
        """
        return self._skill_registry

    def register_skill(self, skill: "Skill") -> None:
        """
        Register a skill with this agent.

        Args:
            skill: The Skill instance to register

        Raises:
            ValueError: If the skill is invalid
        """
        self._skill_registry.register(skill)
        logger.debug(f"Registered skill '{skill.metadata.name}' with agent")

    def load_skill(self, name: str) -> "LoadedSkillContext":
        """
        Load a skill by name.

        Loading a skill resolves its instructions and activates its tools.
        Dependencies are automatically loaded first.

        Args:
            name: Name of the skill to load

        Returns:
            LoadedSkillContext with resolved instructions and tools

        Raises:
            ValueError: If skill not found or circular dependency detected
        """
        context = self._skill_registry.load(name)
        logger.info(f"Loaded skill '{name}' for agent '{getattr(self, 'agent_id', 'unknown')}'")
        return context

    def unload_skill(self, name: str) -> None:
        """
        Unload a skill by name.

        Unloading a skill deactivates its tools and removes it from
        the loaded set.

        Args:
            name: Name of the skill to unload
        """
        self._skill_registry.unload(name)
        logger.info(f"Unloaded skill '{name}' for agent '{getattr(self, 'agent_id', 'unknown')}'")

    def register_builtin_skills(self) -> None:
        """
        Register all built-in skills with this agent.

        This method registers all pre-built skills from the builtin module,
        making them available for discovery and loading.
        
        Note: Skills that are already registered will be skipped to avoid
        duplicate registration.
        """
        from .builtin import get_all_builtin_skills

        builtin_skills = get_all_builtin_skills()
        registered_count = 0
        
        for skill in builtin_skills:
            # Skip if already registered
            if self._skill_registry.get(skill.metadata.name) is not None:
                continue
            self.register_skill(skill)
            registered_count += 1

        if registered_count > 0:
            logger.info(
                f"Registered {registered_count} built-in skills "
                f"for agent '{getattr(self, 'agent_id', 'unknown')}'"
            )
        elif builtin_skills:
            logger.debug(
                f"All {len(builtin_skills)} built-in skills already registered "
                f"for agent '{getattr(self, 'agent_id', 'unknown')}'"
            )

    def get_skill_tools(self) -> list[Callable[..., str]]:
        """
        Get skill management tools for the agent.

        Returns tools that allow the agent to discover, load, and unload
        skills at runtime. These tools are bound to this agent's registry.

        Returns:
            List of callable tools: [list_skills, load_skill, unload_skill]
        """
        if not self._skill_tools:
            from .tools import create_skill_tools

            self._skill_tools = create_skill_tools(self._skill_registry)
        return self._skill_tools

    def get_loaded_skill_instructions(self) -> str:
        """
        Get combined instructions from all loaded skills.

        Returns a formatted string containing the instructions from
        all currently loaded skills, suitable for injection into
        the agent's context.

        Returns:
            Combined instructions string, or empty string if no skills loaded
        """
        instructions: list[str] = []
        for name in self._skill_registry.list_loaded():
            context = self._skill_registry.get_loaded_context(name)
            if context:
                instructions.append(f"## {name} Skill\n{context.instructions}")

        return "\n\n".join(instructions)

    def get_loaded_skill_tools(self) -> list[Any]:
        """
        Get all tools from loaded skills.

        Returns a list of all tool instances from all currently
        loaded skills.

        Returns:
            List of tool instances from loaded skills
        """
        tools: list[Any] = []
        for name in self._skill_registry.list_loaded():
            context = self._skill_registry.get_loaded_context(name)
            if context:
                tools.extend(context.tools)
        return tools

    def get_skills_summary(self) -> dict[str, Any]:
        """
        Get a summary of skills status for metadata.

        Returns:
            Dictionary with total_skills and loaded_skills counts
        """
        all_skills = self._skill_registry.list_all()
        loaded_skills = self._skill_registry.list_loaded()
        return {
            "total_skills": len(all_skills),
            "loaded_skills": len(loaded_skills),
            "loaded_skill_names": loaded_skills,
        }

    def get_all_registered_skill_tools(self) -> list[Any]:
        """
        Get tools from ALL registered skills (not just loaded ones).

        This is necessary because LlamaIndex and similar frameworks have
        fixed tool sets at initialization time. Tools must be available
        before load_skill() is called.

        The load_skill() function still returns instructions for context
        injection, but tools are already available from initialization.

        Handles different tool types:
        - AgentTool: Calls get_tool_function() to get the callable
        - FunctionTool: Used directly (LlamaIndex tool wrapper)
        - Callable: Used directly (plain functions)

        Note: AgentTool instances are stored in _skill_tool_instances for
        later context configuration via configure_skill_tools_context().

        Returns:
            List of tool instances from all registered skills
        """
        tools: list[Any] = []
        self._skill_tool_instances = []
        all_skills = self._skill_registry.list_all()
        
        logger.debug(f"Getting tools from {len(all_skills)} registered skills")
        
        for skill_meta in all_skills:
            skill = self._skill_registry.get(skill_meta.name)
            if skill:
                skill_tools = skill.get_tools()
                logger.debug(
                    f"Skill '{skill_meta.name}' has {len(skill_tools)} tools"
                )
                
                for tool in skill_tools:
                    # Handle different tool types
                    if hasattr(tool, "get_tool_function"):
                        # AgentTool with get_tool_function method
                        # Store the instance for later context configuration
                        self._skill_tool_instances.append(tool)
                        tool_func = tool.get_tool_function()
                        tools.append(tool_func)
                        tool_name = getattr(tool_func, "__name__", type(tool).__name__)
                        logger.debug(
                            f"  Added AgentTool '{tool_name}' from skill '{skill_meta.name}'"
                        )
                    elif callable(tool):
                        # Direct callable or FunctionTool
                        tools.append(tool)
                        tool_name = getattr(tool, "__name__", type(tool).__name__)
                        logger.debug(
                            f"  Added callable '{tool_name}' from skill '{skill_meta.name}'"
                        )
                    else:
                        logger.warning(
                            f"  Skipping non-callable tool from skill '{skill_meta.name}': "
                            f"{type(tool).__name__}"
                        )
        
        logger.debug(f"Total skill tools collected: {len(tools)}")
        logger.debug(f"AgentTool instances stored for context: {len(self._skill_tool_instances)}")
        return tools

    def configure_skill_tools_context(
        self,
        file_storage: Any = None,
        user_id: str | None = None,
        session_id: str | None = None
    ) -> None:
        """
        Configure context for all AgentTool instances from registered skills.

        This method should be called after file_storage is initialized and
        before the agent processes messages. It sets the context (file_storage,
        user_id, session_id) on all AgentTool instances collected by
        get_all_registered_skill_tools().

        Args:
            file_storage: FileStorageManager instance for file operations
            user_id: Current user identifier
            session_id: Current session identifier
        """
        if not self._skill_tool_instances:
            logger.debug("No skill tool instances to configure")
            return

        configured_count = 0
        for tool in self._skill_tool_instances:
            if hasattr(tool, "set_context"):
                tool.set_context(
                    file_storage=file_storage,
                    user_id=user_id,
                    session_id=session_id
                )
                configured_count += 1
                logger.debug(f"Configured context for {type(tool).__name__}")

        logger.info(f"🔧 Configured context for {configured_count} skill tools")


__all__ = [
    "SkillsMixin",
]
