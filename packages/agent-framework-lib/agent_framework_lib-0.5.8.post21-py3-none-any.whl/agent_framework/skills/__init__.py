"""
Agent Framework Skills System

A modular system for organizing agent capabilities into on-demand packages called "Skills".
Each skill bundles together metadata, detailed instructions, and associated tools.

This design reduces token consumption by loading detailed instructions only when needed,
while providing agents with lightweight metadata for capability discovery.

Key Components:
    - Skill: Complete skill definition with metadata, instructions, and tools
    - SkillMetadata: Lightweight metadata for skill discovery (~50 tokens per skill)
    - SkillRegistry: Central registry for skill management
    - LoadedSkillContext: Runtime context for a loaded skill
    - SkillsMixin: Mixin class for integrating skills into agents

Token Optimization:
    Instead of injecting ~3000 tokens of instructions into every system prompt,
    the skills system delivers instructions on-demand via tool responses.

    - System prompt: ~700 tokens (base + skills discovery)
    - Skill loading: ~500 tokens per skill (one-time, in conversation context)

Built-in Skills:
    Visualization:
        - chart: Chart.js chart generation
        - mermaid: Mermaid diagram generation
        - table: Table image generation

    Document:
        - file: File operations (create, list, read)
        - pdf: PDF generation from Markdown/HTML
        - pdf_with_images: PDF with embedded images
        - file_access: File path and data URI access

    Web:
        - web_search: Web and news search

    Multimodal:
        - multimodal: Image analysis

    UI:
        - form: Form generation
        - optionsblock: Options block generation
        - image_display: Image display

Example:
    from agent_framework.skills import Skill, SkillMetadata, SkillRegistry

    # Create a skill
    skill = Skill(
        metadata=SkillMetadata(
            name="chart",
            description="Generate Chart.js charts as PNG images",
            trigger_patterns=["chart", "graph", "plot"],
            category="visualization"
        ),
        instructions="## Chart Generation Instructions\\n...",
        tools=[ChartToImageTool()]
    )

    # Register and load
    registry = SkillRegistry()
    registry.register(skill)
    context = registry.load("chart")

    # Access loaded instructions and tools
    print(context.instructions)
    print(context.tools)

    # Or use built-in skills
    from agent_framework.skills import get_all_builtin_skills
    for skill in get_all_builtin_skills():
        registry.register(skill)
"""

from .agent_mixin import SkillsMixin
from .base import (
    LoadedSkillContext,
    Skill,
    SkillCategory,
    SkillMetadata,
    SkillRegistry,
)
from .builtin import (
    CHART_INSTRUCTIONS,
    FILE_ACCESS_INSTRUCTIONS,
    FILE_INSTRUCTIONS,
    FORM_INSTRUCTIONS,
    IMAGE_DISPLAY_INSTRUCTIONS,
    MERMAID_INSTRUCTIONS,
    MULTIMODAL_INSTRUCTIONS,
    OPTIONSBLOCK_INSTRUCTIONS,
    PDF_INSTRUCTIONS,
    PDF_WITH_IMAGES_INSTRUCTIONS,
    TABLE_INSTRUCTIONS,
    WEB_SEARCH_INSTRUCTIONS,
    create_chart_skill,
    create_file_access_skill,
    create_file_skill,
    create_form_skill,
    create_image_display_skill,
    create_mermaid_skill,
    create_multimodal_skill,
    create_optionsblock_skill,
    create_pdf_skill,
    create_pdf_with_images_skill,
    create_table_skill,
    create_web_search_skill,
    get_all_builtin_skills,
)
from .discovery_prompt import (
    SKILLS_DISCOVERY_PROMPT,
    get_skills_discovery_prompt,
)
from .tools import (
    create_skill_tools,
    list_skills,
    load_skill,
    unload_skill,
)


__all__ = [
    # Core classes
    "Skill",
    "SkillMetadata",
    "SkillRegistry",
    "LoadedSkillContext",
    "SkillCategory",
    # Mixin
    "SkillsMixin",
    # Discovery prompt
    "SKILLS_DISCOVERY_PROMPT",
    "get_skills_discovery_prompt",
    # Skill tools
    "create_skill_tools",
    "list_skills",
    "load_skill",
    "unload_skill",
    # Built-in skills factory
    "get_all_builtin_skills",
    # Built-in skill creators
    "create_chart_skill",
    "create_mermaid_skill",
    "create_table_skill",
    "create_file_skill",
    "create_pdf_skill",
    "create_pdf_with_images_skill",
    "create_file_access_skill",
    "create_web_search_skill",
    "create_multimodal_skill",
    "create_form_skill",
    "create_optionsblock_skill",
    "create_image_display_skill",
    # Built-in skill instructions
    "CHART_INSTRUCTIONS",
    "MERMAID_INSTRUCTIONS",
    "TABLE_INSTRUCTIONS",
    "FILE_INSTRUCTIONS",
    "PDF_INSTRUCTIONS",
    "PDF_WITH_IMAGES_INSTRUCTIONS",
    "FILE_ACCESS_INSTRUCTIONS",
    "WEB_SEARCH_INSTRUCTIONS",
    "MULTIMODAL_INSTRUCTIONS",
    "FORM_INSTRUCTIONS",
    "OPTIONSBLOCK_INSTRUCTIONS",
    "IMAGE_DISPLAY_INSTRUCTIONS",
]
