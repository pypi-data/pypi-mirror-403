"""
Agent Framework Tools

Reusable tools for agents including file operations, PDF creation, and more.

This module provides a collection of tools that can be used across different
agents with proper dependency injection and error handling. All tools inherit
from the AgentTool base class and follow a consistent pattern for initialization
and usage.

Available Tools:
    - PDF Tools: Create professional PDFs from Markdown or HTML
    - File Tools: Create, list, and read files from storage
    - Multimodal Tools: Process images, audio, and other media
    - Chart Tools: Generate chart images from data
    - Mermaid Tools: Generate diagram images from Mermaid code
    - Table Tools: Generate table images from data
    - Adaptive Sizing: Calculate optimal image dimensions for content

Adaptive Image Sizing:
    The framework includes an adaptive image sizing system that automatically
    calculates optimal dimensions for generated images (charts, diagrams, tables)
    and handles their integration into PDF documents.

    Key components:
    - ImageSizingConfig: Configuration for all sizing parameters
    - ImageDimensionCalculator: Calculates optimal dimensions based on content
    - PDFImageScaler: Handles image scaling for PDF embedding
    - AdaptivePDFCSS: Generates CSS for proper image display in PDFs

Example:
    from agent_framework.tools import CreateFileTool, CreatePDFFromMarkdownTool
    
    # Initialize tools
    file_tool = CreateFileTool()
    pdf_tool = CreatePDFFromMarkdownTool()
    
    # Inject dependencies
    file_tool.set_context(
        file_storage=storage_manager,
        user_id="user123",
        session_id="session456"
    )
    pdf_tool.set_context(
        file_storage=storage_manager,
        user_id="user123",
        session_id="session456"
    )
    
    # Get tool functions for agent use
    create_file_func = file_tool.get_tool_function()
    create_pdf_func = pdf_tool.get_tool_function()

    # Use adaptive sizing for image generation
    from agent_framework.tools import ImageSizingConfig, ImageDimensionCalculator
    
    config = ImageSizingConfig()
    calculator = ImageDimensionCalculator(config)
    
    # Calculate optimal chart dimensions for 15 data points
    width, height = calculator.calculate_chart_dimensions(data_point_count=15)
"""

# Base classes and exceptions
from .base import AgentTool, ToolDependencyError

# File storage tools (always available)
from .file_tools import (
    CreateFileTool,
    ListFilesTool,
    ReadFileTool,
)

# PDF generation tools (optional - requires system dependencies)
# DEPRECATED: CreatePDFFromMarkdownTool and CreatePDFFromHTMLTool are deprecated.
# Use CreateUnifiedPDFTool instead for consistent PDF rendering.
try:
    from .pdf_tools import (
        CreatePDFFromMarkdownTool,  # Deprecated: Use CreateUnifiedPDFTool
        CreatePDFFromHTMLTool,  # Deprecated: Use CreateUnifiedPDFTool
    )
    PDF_TOOLS_AVAILABLE = True
except (ImportError, OSError) as e:
    # OSError can occur when weasyprint's system dependencies are missing
    import warnings
    
    if isinstance(e, OSError) and "libgobject" in str(e):
        warnings.warn(
            "\n" + "="*60 + "\n"
            "PDF generation tools are not available!\n"
            "System dependencies are missing. Install them with:\n\n"
            "macOS:\n"
            "  brew install pango gdk-pixbuf libffi\n"
            "  export DYLD_LIBRARY_PATH=\"/opt/homebrew/lib:$DYLD_LIBRARY_PATH\"\n\n"
            "Ubuntu/Debian:\n"
            "  sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev\n\n"
            "Fedora/RHEL:\n"
            "  sudo dnf install pango gdk-pixbuf2 libffi-devel\n"
            + "="*60,
            ImportWarning,
            stacklevel=2
        )
    elif isinstance(e, ImportError):
        warnings.warn(
            f"PDF generation tools are not available: {e}\n"
            "Install with: uv add weasyprint markdown",
            ImportWarning,
            stacklevel=2
        )
    
    PDF_TOOLS_AVAILABLE = False
    CreatePDFFromMarkdownTool = None
    CreatePDFFromHTMLTool = None

# Image generation tools
from .chart_tools import ChartToImageTool
from .mermaid_tools import MermaidToImageTool
from .tabledata_tools import TableToImageTool

# File access tools
from .file_access_tools import (
    GetFilePathTool,
)

# PDF with images tool
# DEPRECATED: CreatePDFWithImagesTool is deprecated. Use CreateUnifiedPDFTool instead.
from .pdf_with_images_tool import CreatePDFWithImagesTool  # Deprecated: Use CreateUnifiedPDFTool

# Unified PDF tool (recommended - replaces all legacy PDF tools)
from .unified_pdf_tool import CreateUnifiedPDFTool

# Web search tools
from .web_search_tools import WebSearchTool, WebNewsSearchTool

# Adaptive image sizing components
from .sizing_config import ImageSizingConfig, ImageDimensionCalculator
from .pdf_image_scaler import PDFImageScaler
from .adaptive_pdf_css import AdaptivePDFCSS, PDFImageConfig

__all__ = [
    # Base classes
    "AgentTool",
    "ToolDependencyError",
    # Unified PDF tool (recommended)
    "CreateUnifiedPDFTool",
    # Legacy PDF tools (deprecated - use CreateUnifiedPDFTool instead)
    "CreatePDFFromMarkdownTool",  # Deprecated
    "CreatePDFFromHTMLTool",  # Deprecated
    "CreatePDFWithImagesTool",  # Deprecated
    "PDF_TOOLS_AVAILABLE",
    # Image generation tools
    "ChartToImageTool",
    "MermaidToImageTool",
    "TableToImageTool",
    # File tools
    "CreateFileTool",
    "ListFilesTool",
    "ReadFileTool",
    # File access tools
    "GetFilePathTool",
    # Web search tools
    "WebSearchTool",
    "WebNewsSearchTool",
    # Adaptive image sizing
    "ImageSizingConfig",
    "ImageDimensionCalculator",
    "PDFImageScaler",
    "AdaptivePDFCSS",
    "PDFImageConfig",
    # Legacy exports
    "multimodal_tools",
]
