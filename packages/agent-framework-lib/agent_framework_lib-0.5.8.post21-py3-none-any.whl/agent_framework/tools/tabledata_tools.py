"""
Table data to image conversion tool for saving tables as PNG files.

This module provides adaptive sizing for table images based on content complexity,
ensuring tables are large enough to be readable while respecting minimum dimensions.
"""

import json
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


class TableToImageTool(AgentTool):
    """Tool for converting table data to PNG images.

    This tool uses adaptive sizing to ensure tables are large enough to be readable.
    Width is calculated based on column count, with a minimum of 1200px for tables
    with more than 5 columns.

    Attributes:
        dimension_calculator: Calculator for optimal image dimensions
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the TableToImageTool with optional sizing configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        super().__init__()
        self.dimension_calculator = ImageDimensionCalculator(config)

    def get_tool_function(self) -> Callable:
        """Return the table to image conversion function."""

        async def save_table_as_image(
            table_data: str,
            filename: str,
            width: int | None = None,
            theme: str = "default",
            font_size: int = 14,
            show_index: bool = False
        ) -> str:
            """
            Convert table data to a PNG image and save it to file storage.

            Uses adaptive sizing to ensure tables are large enough to be readable.
            Width is calculated based on column count, with a minimum of 1200px
            for tables with more than 5 columns.

            Args:
                table_data: JSON string containing table data with 'headers', 'rows', and optional 'caption'
                filename: Name for the output PNG file (without extension)
                width: Width of the table in pixels (default: auto-calculated based on columns)
                theme: Color theme - "default", "dark", "blue", "green", "minimal" (default: "default")
                font_size: Font size in pixels (default: 14)
                show_index: Show row numbers (default: False)

            Returns:
                Success message with file_id

            Example table_data format:
            {
                "caption": "Sales Report Q4 2024",
                "headers": ["Name", "Age", "City"],
                "rows": [
                    ["Alice", 30, "Paris"],
                    ["Bob", 25, "London"],
                    ["Charlie", 35, "Berlin"]
                ]
            }

            Note: 'caption' is optional. If not provided, no title will be shown.
            """
            self._ensure_initialized()

            # Check for required dependencies (with auto-install attempt)
            available, error = _ensure_playwright()
            if not available:
                return f"Error: {error}"

            # Validate inputs
            if not table_data or not table_data.strip():
                return "Error: table_data cannot be empty"

            if not filename or not filename.strip():
                return "Error: filename cannot be empty"

            # Check file storage availability
            if not self.file_storage:
                raise ToolDependencyError(
                    "File storage is required but was not provided. "
                    "Ensure file_storage is set via set_context()."
                )

            try:
                # Parse the table data
                try:
                    data = json.loads(table_data)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in table_data: {str(e)}"

                # Validate and auto-correct table data before rendering
                try:
                    from ..processing.rich_content_validation import TableValidator

                    validator = TableValidator()
                    # Re-serialize to string for validator
                    validation_result = validator.validate(json.dumps(data))

                    if validation_result.corrected_content:
                        logger.info(
                            f"Table data auto-corrected. Repairs: {validation_result.repairs_made}"
                        )
                        data = json.loads(validation_result.corrected_content)
                    elif validation_result.errors:
                        logger.warning(f"Table validation errors: {validation_result.errors}")
                except ImportError:
                    logger.debug("TableValidator not available, skipping validation")

                # Extract data
                if not isinstance(data, dict):
                    return "Error: table_data must be a JSON object"

                if "headers" not in data:
                    return "Error: table_data must include 'headers' field"

                if "rows" not in data:
                    return "Error: table_data must include 'rows' field"

                headers = data["headers"]
                rows = data["rows"]
                caption = data.get("caption", "")  # Optional caption

                if not headers:
                    return "Error: headers cannot be empty"
                if not rows:
                    return "Error: rows cannot be empty"

                # Add index column if requested
                if show_index:
                    headers = ["#"] + headers
                    rows = [[i + 1] + row for i, row in enumerate(rows)]

                # Calculate optimal dimensions based on content
                column_count = len(headers)
                row_count = len(rows)

                # Calculate content lengths for adaptive sizing
                content_lengths = []
                for col_idx in range(column_count):
                    col_lengths = [len(str(headers[col_idx]))]
                    for row in rows:
                        if col_idx < len(row):
                            col_lengths.append(len(str(row[col_idx])))
                    content_lengths.append(
                        sum(col_lengths) // len(col_lengths) if col_lengths else 0
                    )

                # Calculate optimal dimensions
                final_width, final_height = self.dimension_calculator.calculate_table_dimensions(
                    column_count=column_count,
                    row_count=row_count,
                    content_lengths=content_lengths,
                    requested_width=width,
                )

                logger.debug(
                    f"Table dimensions: {final_width}x{final_height} "
                    f"(columns: {column_count}, rows: {row_count}, requested: {width})"
                )

                # Theme configurations
                themes = {
                    "default": {
                        "bg": "#ffffff",
                        "header_bg": "#f8f9fa",
                        "header_color": "#212529",
                        "row_bg": "#ffffff",
                        "row_alt_bg": "#f8f9fa",
                        "border": "#dee2e6",
                        "text": "#212529"
                    },
                    "dark": {
                        "bg": "#1a1a1a",
                        "header_bg": "#2d2d2d",
                        "header_color": "#ffffff",
                        "row_bg": "#1a1a1a",
                        "row_alt_bg": "#252525",
                        "border": "#404040",
                        "text": "#e0e0e0"
                    },
                    "blue": {
                        "bg": "#ffffff",
                        "header_bg": "#0d6efd",
                        "header_color": "#ffffff",
                        "row_bg": "#ffffff",
                        "row_alt_bg": "#e7f1ff",
                        "border": "#0d6efd",
                        "text": "#212529"
                    },
                    "green": {
                        "bg": "#ffffff",
                        "header_bg": "#198754",
                        "header_color": "#ffffff",
                        "row_bg": "#ffffff",
                        "row_alt_bg": "#d1e7dd",
                        "border": "#198754",
                        "text": "#212529"
                    },
                    "minimal": {
                        "bg": "#ffffff",
                        "header_bg": "#ffffff",
                        "header_color": "#212529",
                        "row_bg": "#ffffff",
                        "row_alt_bg": "#ffffff",
                        "border": "#e0e0e0",
                        "text": "#212529"
                    }
                }

                theme_colors = themes.get(theme, themes["default"])

                # Build HTML table
                table_html = '<table>'

                # Add caption if provided
                if caption:
                    # Escape HTML in caption
                    safe_caption = caption.replace('<', '&lt;').replace('>', '&gt;')
                    table_html += f'<caption>{safe_caption}</caption>'

                # Add headers
                table_html += '<thead><tr>'
                for header in headers:
                    # Escape HTML in headers
                    safe_header = str(header).replace('<', '&lt;').replace('>', '&gt;')
                    table_html += f'<th>{safe_header}</th>'
                table_html += '</tr></thead>'

                # Add rows
                table_html += '<tbody>'
                for i, row in enumerate(rows):
                    table_html += '<tr>'
                    for cell in row:
                        # Escape HTML in cells
                        safe_cell = str(cell).replace('<', '&lt;').replace('>', '&gt;')
                        table_html += f'<td>{safe_cell}</td>'
                    table_html += '</tr>'
                table_html += '</tbody></table>'

                # Create HTML - let table render at natural size first
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 30px;
            background-color: {theme_colors['bg']};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        #tableContainer {{
            display: inline-block;
            background-color: {theme_colors['bg']};
        }}
        table {{
            border-collapse: collapse;
            font-size: {font_size}px;
            color: {theme_colors['text']};
        }}
        caption {{
            font-size: {font_size + 4}px;
            font-weight: bold;
            margin-bottom: 15px;
            text-align: left;
            color: {theme_colors['header_color']};
        }}
        th {{
            background-color: {theme_colors['header_bg']};
            color: {theme_colors['header_color']};
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            border: 1px solid {theme_colors['border']};
            white-space: nowrap;
        }}
        td {{
            padding: 10px 15px;
            border: 1px solid {theme_colors['border']};
            white-space: nowrap;
        }}
        tbody tr:nth-child(even) {{
            background-color: {theme_colors['row_alt_bg']};
        }}
        tbody tr:nth-child(odd) {{
            background-color: {theme_colors['row_bg']};
        }}
    </style>
</head>
<body>
    <div id="tableContainer">
        {table_html}
    </div>
</body>
</html>
"""

                # Import playwright here after ensuring it's available
                from playwright.async_api import async_playwright

                # Use Playwright to render at high resolution
                device_scale = 2  # 2x resolution for crisp images
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page(
                        viewport={"width": 3000, "height": 3000},
                        device_scale_factor=device_scale,
                    )

                    # Load the HTML
                    await page.set_content(html_content)

                    # Wait for content to render
                    await page.wait_for_timeout(500)

                    # Take screenshot of the table container at high resolution
                    table_element = await page.query_selector("#tableContainer")
                    if table_element:
                        screenshot_bytes = await table_element.screenshot(type="png")
                    else:
                        screenshot_bytes = await page.screenshot(type="png")

                    await browser.close()

                # Scale up if needed to meet minimums while preserving aspect ratio
                try:
                    import io

                    from PIL import Image

                    img = Image.open(io.BytesIO(screenshot_bytes))
                    current_width, current_height = img.size

                    min_width = self.dimension_calculator.config.table_min_width
                    min_height = self.dimension_calculator.config.absolute_min_height

                    width_scale = min_width / current_width if current_width < min_width else 1.0
                    height_scale = (
                        min_height / current_height if current_height < min_height else 1.0
                    )
                    scale = max(width_scale, height_scale)

                    if scale > 1.0:
                        new_width = int(current_width * scale)
                        new_height = int(current_height * scale)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        final_width = new_width
                        final_height = new_height

                        output = io.BytesIO()
                        img.save(output, format="PNG")
                        screenshot_bytes = output.getvalue()
                    else:
                        final_width = current_width
                        final_height = current_height

                except ImportError:
                    logger.warning("PIL not available, cannot resize image to meet minimums")

                # Create safe filename
                safe_filename = "".join(
                    c for c in filename if c.isalnum() or c in (' ', '-', '_')
                ).strip()
                safe_filename = safe_filename.replace(' ', '_')
                if not safe_filename.lower().endswith('.png'):
                    safe_filename += '.png'

                # Store the image with dimension metadata
                tags = [
                    "table",
                    "png",
                    "generated",
                    f"rows:{row_count}",
                    f"columns:{column_count}",
                    f"theme:{theme}"
                ]

                if caption:
                    tags.append("with-caption")

                # Build custom metadata with image dimensions
                custom_metadata = {
                    "width_px": final_width,
                    "height_px": final_height,
                    "content_type": "table",
                    "data_complexity": column_count,
                    "row_count": row_count,
                    "column_count": column_count,
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
                if hasattr(self.file_storage, 'get_view_url'):
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
                    f"Created table image: {safe_filename} (file_id: {file_id}, "
                    f"dimensions: {final_width}x{final_height}, columns: {column_count}, view URL: {view_url})"
                )
                caption_info = f" with caption '{caption}'" if caption else ""
                return f"Table saved successfully as PNG{caption_info}! ({row_count} rows, {column_count} columns)\n\n![{safe_filename}]({view_url})"

            except Exception as e:
                error_str = str(e)
                error_str = _get_linux_deps_error_message(error_str)
                error_msg = f"Failed to create table image: {error_str}"
                logger.error(error_msg, exc_info=True)
                return f"Error creating table image: {error_str}"

        return save_table_as_image


__all__ = ["TableToImageTool"]
