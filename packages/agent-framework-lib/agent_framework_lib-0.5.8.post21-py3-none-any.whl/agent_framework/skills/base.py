"""
Base classes for the Skills System.

This module provides the core data models and registry for managing skills:
- SkillMetadata: Lightweight metadata for skill discovery
- Skill: Complete skill definition with instructions and tools
- LoadedSkillContext: Runtime context for a loaded skill
- SkillRegistry: Central registry for skill management
- SkillCategory: Standard skill categories
"""

import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr

from agent_framework.core.step_display_config import StepDisplayInfo


logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Standard skill categories."""

    DOCUMENT = "document"  # PDF, DOCX, file operations
    VISUALIZATION = "visualization"  # Charts, diagrams, tables
    WEB = "web"  # Web search, scraping
    DATA = "data"  # Data processing, analysis
    MULTIMODAL = "multimodal"  # Image, audio processing
    UI = "ui"  # Forms, options blocks
    GENERAL = "general"  # General purpose


class SkillMetadata(BaseModel):
    """
    Lightweight skill metadata for discovery (~50 tokens per skill).

    This class contains only the essential information needed to discover
    and select skills without loading their full instructions.
    """

    name: str = Field(..., description="Unique skill identifier")
    description: str = Field(..., description="Short description (~1 line)")
    trigger_patterns: list[str] = Field(
        default_factory=list, description="Keywords/patterns for automatic discovery"
    )
    category: str = Field(
        default="general", description="Category: document, data, web, visualization, etc."
    )
    version: str = Field(default="1.0.0", description="Skill version")

    def matches_query(self, query: str) -> bool:
        """
        Check if skill matches a search query.

        Matches against name, description, and trigger patterns.

        Args:
            query: Search query string

        Returns:
            True if the skill matches the query
        """
        query_lower = query.lower()
        if query_lower in self.name.lower():
            return True
        if query_lower in self.description.lower():
            return True
        return any(pattern.lower() in query_lower for pattern in self.trigger_patterns)


class Skill(BaseModel):
    """
    Complete skill definition with metadata, instructions, and tools.

    A skill packages together:
    - Metadata for discovery
    - Detailed instructions for the agent
    - Associated tools that become available when loaded
    - Dependencies on other skills
    - Configuration options
    - Optional display information for the skill's tools
    """

    metadata: SkillMetadata
    instructions: str | Path = Field(
        ..., description="Full instructions or path to instructions file"
    )
    tools: list[Any] = Field(
        default_factory=list, description="AgentTool instances associated with this skill"
    )
    dependencies: list[str] = Field(default_factory=list, description="Names of required skills")
    config: dict[str, Any] = Field(default_factory=dict, description="Skill-specific configuration")
    display_info: StepDisplayInfo | None = Field(
        None,
        description="Optional display information for this skill's tools. "
        "If not provided, tools use their own display info or defaults.",
    )

    _cached_instructions: str | None = PrivateAttr(default=None)
    _display_name: str | None = PrivateAttr(default=None)
    _display_icon: str | None = PrivateAttr(default=None)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def display_name(self) -> str:
        """User-friendly display name for the skill.

        Returns the custom display name if set, otherwise falls back to
        the skill's metadata name.
        """
        if self._display_name:
            return self._display_name
        return self.metadata.name

    @display_name.setter
    def display_name(self, value: str) -> None:
        """Set the display name."""
        self._display_name = value

    @property
    def display_icon(self) -> str:
        """Emoji icon for the skill.

        Returns the custom icon if set, otherwise returns the default "📥".
        """
        if self._display_icon:
            return self._display_icon
        return "📥"

    @display_icon.setter
    def display_icon(self, value: str) -> None:
        """Set the display icon."""
        self._display_icon = value

    def get_instructions(self) -> str:
        """
        Get full instructions, loading from file if needed.

        Supports lazy loading: if instructions is a Path, the file
        content is loaded and cached on first access.

        Returns:
            The full instruction text as a string

        Raises:
            FileNotFoundError: If instructions is a Path and file doesn't exist
        """
        if self._cached_instructions is not None:
            return self._cached_instructions

        if isinstance(self.instructions, Path):
            self._cached_instructions = self.instructions.read_text(encoding="utf-8")
        else:
            self._cached_instructions = self.instructions

        return self._cached_instructions

    def get_tools(self) -> list[Any]:
        """
        Get the list of tools for this skill.

        Returns:
            List of AgentTool instances
        """
        return self.tools

    def validate_skill(self) -> bool:
        """
        Validate skill integrity.

        Checks that all required fields are present and valid.

        Returns:
            True if the skill is valid, False otherwise
        """
        if not self.metadata.name:
            return False
        return bool(self.instructions)


class LoadedSkillContext(BaseModel):
    """
    Runtime context for a loaded skill.

    Contains the resolved instructions and activated tools
    for a skill that has been loaded into an agent's context.
    """

    skill: Skill
    instructions: str = Field(..., description="Resolved instructions")
    tools: list[Any] = Field(default_factory=list, description="Activated tools")
    loaded_at: datetime = Field(default_factory=datetime.now)
    dependencies_loaded: list[str] = Field(
        default_factory=list, description="Names of loaded dependency skills"
    )

    model_config = {"arbitrary_types_allowed": True}


class SkillRegistry:
    """
    Central registry for skill management.

    Handles skill registration, discovery, loading, and unloading.
    Supports dependency resolution when loading skills.
    """

    def __init__(self) -> None:
        """Initialize an empty skill registry."""
        self._skills: dict[str, Skill] = {}
        self._loaded: set[str] = set()
        self._loaded_contexts: dict[str, LoadedSkillContext] = {}

    def register(self, skill: Skill) -> None:
        """
        Register a skill in the registry.

        Args:
            skill: The skill to register

        Raises:
            ValueError: If the skill is invalid
        """
        if not skill.validate_skill():
            raise ValueError(f"Invalid skill: {skill.metadata.name}")
        self._skills[skill.metadata.name] = skill

    def unregister(self, name: str) -> None:
        """
        Remove a skill from the registry.

        If the skill is currently loaded, it will be unloaded first.

        Args:
            name: Name of the skill to unregister
        """
        if name in self._loaded:
            self.unload(name)
        if name in self._skills:
            del self._skills[name]

    def get(self, name: str) -> Skill | None:
        """
        Get a skill by name.

        Args:
            name: Name of the skill

        Returns:
            The skill if found, None otherwise
        """
        return self._skills.get(name)

    def list_all(self) -> list[SkillMetadata]:
        """
        List metadata for all registered skills.

        Returns:
            List of SkillMetadata for all registered skills
        """
        return [skill.metadata for skill in self._skills.values()]

    def list_loaded(self) -> list[str]:
        """
        List names of currently loaded skills.

        Returns:
            List of skill names that are currently loaded
        """
        return list(self._loaded)

    def is_loaded(self, name: str) -> bool:
        """
        Check if a skill is loaded.

        Args:
            name: Name of the skill

        Returns:
            True if the skill is loaded
        """
        return name in self._loaded

    def search(self, query: str) -> list[SkillMetadata]:
        """
        Search skills by query.

        Matches against skill name, description, and trigger patterns.

        Args:
            query: Search query string

        Returns:
            List of matching skill metadata
        """
        return [
            skill.metadata for skill in self._skills.values() if skill.metadata.matches_query(query)
        ]

    def load(self, name: str) -> LoadedSkillContext:
        """
        Load a skill and its dependencies.

        Dependencies are loaded recursively before the main skill.
        Circular dependencies are detected and raise an error.

        Args:
            name: Name of the skill to load

        Returns:
            LoadedSkillContext with resolved instructions and tools

        Raises:
            ValueError: If skill not found or circular dependency detected
        """
        return self._load_with_chain(name, set())

    def _load_with_chain(self, name: str, loading_chain: set[str]) -> LoadedSkillContext:
        """
        Internal method to load a skill with circular dependency detection.

        Args:
            name: Name of the skill to load
            loading_chain: Set of skills currently being loaded (for cycle detection)

        Returns:
            LoadedSkillContext with resolved instructions and tools

        Raises:
            ValueError: If skill not found or circular dependency detected
        """
        if name not in self._skills:
            raise ValueError(f"Skill not found: {name}")

        # Check for circular dependency
        if name in loading_chain:
            raise ValueError(f"Circular dependency detected: {name}")

        # If already loaded, return existing context
        if name in self._loaded:
            return self._loaded_contexts[name]

        skill = self._skills[name]
        dependencies_loaded: list[str] = []

        # Add to loading chain for cycle detection
        loading_chain.add(name)

        # Load dependencies first
        for dep_name in skill.dependencies:
            if dep_name not in self._loaded:
                self._load_with_chain(dep_name, loading_chain)
                dependencies_loaded.append(dep_name)

        # Remove from loading chain
        loading_chain.remove(name)

        # Create loaded context
        context = LoadedSkillContext(
            skill=skill,
            instructions=skill.get_instructions(),
            tools=skill.get_tools(),
            dependencies_loaded=dependencies_loaded,
        )

        self._loaded.add(name)
        self._loaded_contexts[name] = context
        return context

    def unload(self, name: str) -> None:
        """
        Unload a skill.

        Args:
            name: Name of the skill to unload
        """
        if name in self._loaded:
            self._loaded.remove(name)
            if name in self._loaded_contexts:
                del self._loaded_contexts[name]

    def get_loaded_context(self, name: str) -> LoadedSkillContext | None:
        """
        Get the loaded context for a skill.

        Args:
            name: Name of the skill

        Returns:
            LoadedSkillContext if skill is loaded, None otherwise
        """
        return self._loaded_contexts.get(name)


__all__ = [
    "SkillCategory",
    "SkillMetadata",
    "Skill",
    "LoadedSkillContext",
    "SkillRegistry",
]
