"""
Mermaid to image conversion tool for saving diagrams as PNG files.

This module provides adaptive sizing for Mermaid diagrams based on
diagram complexity (node count).
"""

import logging
from collections.abc import Callable

from .base import AgentTool, ToolDependencyError
from .sizing_config import ImageDimensionCalculator, ImageSizingConfig


# Optional dependencies - lazy loaded
PLAYWRIGHT_AVAILABLE = None  # None = not checked yet
PLAYWRIGHT_ERROR = None


def _ensure_playwright():
    """Ensure Playwright is available, attempting auto-install if needed."""
    global PLAYWRIGHT_AVAILABLE, PLAYWRIGHT_ERROR

    if PLAYWRIGHT_AVAILABLE is not None:
        return PLAYWRIGHT_AVAILABLE, PLAYWRIGHT_ERROR

    try:
        from playwright.async_api import async_playwright  # noqa: F401

        # Playwright module is available, now ensure browsers are installed
        from ..utils.post_install import ensure_playwright_browsers

        success, error = ensure_playwright_browsers()
        if success:
            PLAYWRIGHT_AVAILABLE = True
            PLAYWRIGHT_ERROR = None
        else:
            PLAYWRIGHT_AVAILABLE = False
            PLAYWRIGHT_ERROR = error
    except ImportError as e:
        PLAYWRIGHT_AVAILABLE = False
        PLAYWRIGHT_ERROR = (
            f"Playwright is not installed: {e}\n"
            "Install with:\n"
            "  uv add playwright\n"
            "  playwright install chromium"
        )

    return PLAYWRIGHT_AVAILABLE, PLAYWRIGHT_ERROR


def _get_linux_deps_error_message(original_error: str) -> str:
    """Generate a helpful error message for Linux system dependency issues."""
    import platform

    if platform.system().lower() != "linux":
        return original_error

    if "missing dependencies" in original_error.lower() or "install-deps" in original_error.lower():
        return (
            "Playwright browser cannot launch due to missing system dependencies.\n\n"
            "Please run one of the following commands:\n\n"
            "  Option 1 (recommended):\n"
            "    sudo playwright install-deps chromium\n\n"
            "  Option 2 (apt-get on Debian/Ubuntu):\n"
            "    sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libasound2t64\n\n"
            "  Option 3 (if libasound2t64 not found):\n"
            "    sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libasound2"
        )
    return original_error


logger = logging.getLogger(__name__)


class MermaidToImageTool(AgentTool):
    """Tool for converting Mermaid diagrams to PNG images.

    This tool provides adaptive sizing based on diagram complexity:
    - Base dimensions: 1200x800 pixels
    - For diagrams with >15 nodes, dimensions scale proportionally
    - Minimum dimensions enforced: 600x400 pixels
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the tool with optional custom sizing configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        super().__init__()
        self._dimension_calculator = ImageDimensionCalculator(config)

    def get_tool_function(self) -> Callable:
        """Return the mermaid to image conversion function."""

        async def save_mermaid_as_image(
            mermaid_code: str,
            filename: str,
            width: int | None = None,
            height: int | None = None,
            background_color: str = "white",
            theme: str = "default",
        ) -> str:
            """
            Convert a Mermaid diagram to a PNG image and save it to file storage.

            Dimensions are automatically calculated based on diagram complexity:
            - Base dimensions: 1200x800 pixels
            - For diagrams with >15 nodes, dimensions scale proportionally
            - Custom dimensions can be specified but will respect minimums (600x400)

            Args:
                mermaid_code: Mermaid diagram code (without ```mermaid``` markers)
                filename: Name for the output PNG file (without extension)
                width: Width of the viewport in pixels (optional, auto-calculated if not provided)
                height: Height of the viewport in pixels (optional, auto-calculated if not provided)
                background_color: Background color for the diagram (default: "white")
                theme: Mermaid theme - "default", "dark", "forest", "neutral" (default: "default")

            Returns:
                Success message with file_id

            Example mermaid_code:
            graph TD
                A[Start] --> B{Decision}
                B -->|Yes| C[Process]
                B -->|No| D[End]
                C --> D
            """
            self._ensure_initialized()

            # Check for required dependencies (with auto-install attempt)
            available, error = _ensure_playwright()
            if not available:
                return f"Error: {error}"

            # Validate inputs
            if not mermaid_code or not mermaid_code.strip():
                return "Error: mermaid_code cannot be empty"

            if not filename or not filename.strip():
                return "Error: filename cannot be empty"

            # Check file storage availability
            if not self.file_storage:
                raise ToolDependencyError(
                    "File storage is required but was not provided. "
                    "Ensure file_storage is set via set_context()."
                )

            # Clean mermaid code (remove markdown code blocks if present)
            clean_code = mermaid_code.strip()

            # Debug: log the raw input to see if newlines are present
            logger.debug(f"Mermaid raw input (repr): {repr(mermaid_code[:200])}")

            if clean_code.startswith("```mermaid"):
                clean_code = clean_code.replace("```mermaid", "").replace("```", "").strip()
            elif clean_code.startswith("```"):
                clean_code = clean_code.replace("```", "").strip()

            # Validate and auto-correct mermaid syntax before rendering
            try:
                from ..processing.rich_content_validation import MermaidValidator

                validator = MermaidValidator()
                validation_result = validator.validate(clean_code)

                if validation_result.corrected_content:
                    logger.info(
                        f"Mermaid syntax auto-corrected. Repairs: {validation_result.repairs_made}"
                    )
                    clean_code = validation_result.corrected_content
                elif validation_result.errors:
                    logger.warning(f"Mermaid validation errors: {validation_result.errors}")

                # Debug: log the clean_code to verify newlines are preserved
                logger.debug(f"Mermaid clean_code after validation (repr): {repr(clean_code[:200])}")
            except ImportError:
                logger.debug("MermaidValidator not available, skipping validation")

            # Calculate optimal dimensions based on diagram complexity
            calculated_width, calculated_height = (
                self._dimension_calculator.calculate_mermaid_dimensions(
                    mermaid_code=clean_code,
                    requested_width=width,
                    requested_height=height,
                )
            )

            # Count nodes for metadata
            node_count = self._dimension_calculator.count_mermaid_nodes(clean_code)

            logger.debug(
                f"Mermaid diagram sizing: {node_count} nodes detected, "
                f"dimensions: {calculated_width}x{calculated_height}"
            )

            try:
                # Get minimum dimensions
                min_width = self._dimension_calculator.config.mermaid_base_width
                min_height = self._dimension_calculator.config.mermaid_base_height

                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{theme}',
            securityLevel: 'loose',
            gantt: {{
                useWidth: {calculated_width}
            }}
        }});
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 20px;
            background-color: {background_color};
        }}
        #diagram {{
            background-color: {background_color};
            display: inline-block;
            min-width: {calculated_width}px;
        }}
        #diagram svg {{
            min-width: {calculated_width}px !important;
        }}
        .mermaid {{
            min-width: {calculated_width}px;
        }}
    </style>
</head>
<body>
    <div id="diagram" class="mermaid">
{clean_code}
    </div>
</body>
</html>
"""

                # Import playwright here after ensuring it's available
                from playwright.async_api import async_playwright

                async def render_mermaid(
                    scale_factor: int, viewport_width: int, viewport_height: int
                ) -> tuple[bytes, int, int]:
                    """Render mermaid at given scale factor and return bytes + dimensions."""
                    async with async_playwright() as p:
                        browser = await p.chromium.launch()
                        page = await browser.new_page(
                            viewport={"width": viewport_width, "height": viewport_height},
                            device_scale_factor=scale_factor,
                        )
                        await page.set_content(html_content)
                        await page.wait_for_selector("#diagram svg", timeout=5000)
                        await page.wait_for_timeout(1000)

                        diagram_element = await page.query_selector("#diagram")
                        if diagram_element:
                            img_bytes = await diagram_element.screenshot(
                                type="png",
                                omit_background=(background_color.lower() == "transparent"),
                            )
                        else:
                            img_bytes = await page.screenshot(type="png")

                        await browser.close()

                    # Get actual dimensions
                    import io

                    from PIL import Image

                    img = Image.open(io.BytesIO(img_bytes))
                    return img_bytes, img.size[0], img.size[1]

                # Use calculated dimensions for viewport (with some padding)
                # This ensures Gantt charts and wide diagrams render properly
                viewport_width = max(3000, calculated_width + 200)
                viewport_height = max(3000, calculated_height + 200)

                # First render at scale 2
                screenshot_bytes, current_width, current_height = await render_mermaid(
                    2, viewport_width, viewport_height
                )

                # Check if we need higher resolution to meet minimums
                width_scale = min_width / current_width if current_width < min_width else 1.0
                height_scale = min_height / current_height if current_height < min_height else 1.0
                needed_scale = max(width_scale, height_scale)

                if needed_scale > 1.0:
                    # Re-render at higher scale factor (no PIL upscaling = no pixelization)
                    new_device_scale = int(2 * needed_scale) + 1  # Round up
                    new_device_scale = min(new_device_scale, 8)  # Cap at 8x
                    screenshot_bytes, current_width, current_height = await render_mermaid(
                        new_device_scale, viewport_width, viewport_height
                    )

                calculated_width = current_width
                calculated_height = current_height

                # Create safe filename
                safe_filename = "".join(
                    c for c in filename if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_filename = safe_filename.replace(" ", "_")
                if not safe_filename.lower().endswith(".png"):
                    safe_filename += ".png"

                # Detect diagram type from mermaid code
                diagram_type = "unknown"
                first_line = clean_code.split("\n")[0].strip().lower()
                if first_line.startswith("graph"):
                    diagram_type = "flowchart"
                elif first_line.startswith("sequencediagram"):
                    diagram_type = "sequence"
                elif first_line.startswith("classDiagram"):
                    diagram_type = "class"
                elif first_line.startswith("statediagram") or first_line.startswith("state "):
                    diagram_type = "state"
                elif first_line.startswith("erdiagram"):
                    diagram_type = "er"
                elif first_line.startswith("gantt"):
                    diagram_type = "gantt"
                elif first_line.startswith("pie"):
                    diagram_type = "pie"
                elif first_line.startswith("journey"):
                    diagram_type = "journey"

                # Store the image with dimension metadata
                tags = ["mermaid", "diagram", "png", "generated", f"diagram-type:{diagram_type}"]

                # Build custom metadata with dimension information
                custom_metadata = {
                    "width_px": calculated_width,
                    "height_px": calculated_height,
                    "content_type": "diagram",
                    "data_complexity": node_count,
                    "diagram_type": diagram_type,
                }

                file_id = await self.file_storage.store_file(
                    content=screenshot_bytes,
                    filename=safe_filename,
                    user_id=self.current_user_id,
                    session_id=self.current_session_id,
                    mime_type="image/png",
                    tags=tags,
                    is_generated=True,
                    custom_metadata=custom_metadata,
                )

                # Get view URL for displaying image in chat
                # For S3/MinIO in API mode, this returns /files/{id}/view (inline display)
                # For presigned/public modes, returns direct S3 URL
                # Use get_download_url() if you need to force file download instead
                if hasattr(self.file_storage, "get_view_url"):
                    try:
                        view_url = await self.file_storage.get_view_url(file_id)
                    except Exception as url_error:
                        logger.warning(
                            f"Failed to get view URL from storage backend: {url_error}, "
                            "falling back to API URL"
                        )
                        view_url = f"/files/{file_id}/view"
                else:
                    view_url = f"/files/{file_id}/view"

                logger.info(
                    f"Created mermaid diagram: {safe_filename} (file_id: {file_id}, "
                    f"dimensions: {calculated_width}x{calculated_height}, nodes: {node_count}, view URL: {view_url})"
                )
                return f"Mermaid diagram saved successfully as PNG!\n\n![{safe_filename}]({view_url})"

            except Exception as e:
                error_str = str(e)
                error_str = _get_linux_deps_error_message(error_str)
                error_msg = f"Failed to create mermaid diagram: {error_str}"
                logger.error(error_msg, exc_info=True)
                return f"Error creating mermaid diagram: {error_str}"

        return save_mermaid_as_image


__all__ = ["MermaidToImageTool"]
