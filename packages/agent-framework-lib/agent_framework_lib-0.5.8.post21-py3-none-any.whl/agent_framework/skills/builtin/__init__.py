"""
Built-in Skills for Agent Framework

This module provides pre-built skills that wrap existing tools with
appropriate instructions and metadata for on-demand loading.

Available Skills:
    Visualization:
        - chart_skill: Chart.js chart generation
        - mermaid_skill: Mermaid diagram generation
        - table_skill: Table image generation

    Document:
        - file_skill: File operations (create, list, read)
        - unified_pdf_skill: Unified PDF generation from HTML (RECOMMENDED)
        - pdf_skill: PDF generation from Markdown/HTML (DEPRECATED - use unified_pdf_skill)
        - pdf_with_images_skill: PDF with embedded images (DEPRECATED - use unified_pdf_skill)
        - file_access_skill: File path and data URI access

    Web:
        - web_search_skill: Web and news search

    Multimodal:
        - multimodal_skill: Image analysis

    UI:
        - form_skill: Form generation
        - optionsblock_skill: Options block generation
        - image_display_skill: Image display

Example:
    from agent_framework.skills.builtin import get_all_builtin_skills

    # Get all built-in skills
    skills = get_all_builtin_skills()

    # Register with an agent's skill registry
    for skill in skills:
        agent.register_skill(skill)
"""

from ..base import Skill

# Visualization skills
from .chart_skill import create_chart_skill, CHART_INSTRUCTIONS
from .mermaid_skill import create_mermaid_skill, MERMAID_INSTRUCTIONS
from .table_skill import create_table_skill, TABLE_INSTRUCTIONS

# Document skills
from .file_skill import create_file_skill, FILE_INSTRUCTIONS
# DEPRECATED: Use create_unified_pdf_skill instead - provides unified HTML-based PDF generation
from .pdf_skill import create_pdf_skill, PDF_INSTRUCTIONS
# DEPRECATED: Use create_unified_pdf_skill instead - provides unified HTML-based PDF generation
from .pdf_with_images_skill import create_pdf_with_images_skill, PDF_WITH_IMAGES_INSTRUCTIONS
from .file_access_skill import create_file_access_skill, FILE_ACCESS_INSTRUCTIONS
# Unified PDF skill (replaces pdf_skill and pdf_with_images_skill)
from .unified_pdf_skill import create_unified_pdf_skill, UNIFIED_PDF_INSTRUCTIONS

# Web skills
from .web_search_skill import create_web_search_skill, WEB_SEARCH_INSTRUCTIONS

# Multimodal skills
from .multimodal_skill import create_multimodal_skill, MULTIMODAL_INSTRUCTIONS

# UI skills
from .form_skill import create_form_skill, FORM_INSTRUCTIONS
from .optionsblock_skill import create_optionsblock_skill, OPTIONSBLOCK_INSTRUCTIONS
from .image_display_skill import create_image_display_skill, IMAGE_DISPLAY_INSTRUCTIONS


def get_all_builtin_skills() -> list[Skill]:
    """
    Get all built-in skills.

    Returns a list of all pre-built skills that can be registered
    with an agent's skill registry.

    Returns:
        List of Skill instances for all built-in skills
    """
    skills: list[Skill] = []

    # Visualization skills
    skills.append(create_chart_skill())
    skills.append(create_mermaid_skill())
    skills.append(create_table_skill())

    # Document skills
    skills.append(create_file_skill())
    # Use unified PDF skill instead of legacy pdf_skill and pdf_with_images_skill
    skills.append(create_unified_pdf_skill())
    skills.append(create_file_access_skill())

    # Web skills
    skills.append(create_web_search_skill())

    # Multimodal skills
    skills.append(create_multimodal_skill())

    # UI skills
    skills.append(create_form_skill())
    skills.append(create_optionsblock_skill())
    skills.append(create_image_display_skill())

    return skills


__all__ = [
    # Factory function
    "get_all_builtin_skills",
    # Visualization skill creators
    "create_chart_skill",
    "create_mermaid_skill",
    "create_table_skill",
    # Document skill creators
    "create_file_skill",
    # DEPRECATED: Use create_unified_pdf_skill instead
    "create_pdf_skill",
    # DEPRECATED: Use create_unified_pdf_skill instead
    "create_pdf_with_images_skill",
    "create_file_access_skill",
    # Unified PDF skill (recommended)
    "create_unified_pdf_skill",
    # Web skill creators
    "create_web_search_skill",
    # Multimodal skill creators
    "create_multimodal_skill",
    # UI skill creators
    "create_form_skill",
    "create_optionsblock_skill",
    "create_image_display_skill",
    # Instruction constants
    "CHART_INSTRUCTIONS",
    "MERMAID_INSTRUCTIONS",
    "TABLE_INSTRUCTIONS",
    "FILE_INSTRUCTIONS",
    # DEPRECATED: Use UNIFIED_PDF_INSTRUCTIONS instead
    "PDF_INSTRUCTIONS",
    # DEPRECATED: Use UNIFIED_PDF_INSTRUCTIONS instead
    "PDF_WITH_IMAGES_INSTRUCTIONS",
    "FILE_ACCESS_INSTRUCTIONS",
    # Unified PDF instructions (recommended)
    "UNIFIED_PDF_INSTRUCTIONS",
    "WEB_SEARCH_INSTRUCTIONS",
    "MULTIMODAL_INSTRUCTIONS",
    "FORM_INSTRUCTIONS",
    "OPTIONSBLOCK_INSTRUCTIONS",
    "IMAGE_DISPLAY_INSTRUCTIONS",
]
