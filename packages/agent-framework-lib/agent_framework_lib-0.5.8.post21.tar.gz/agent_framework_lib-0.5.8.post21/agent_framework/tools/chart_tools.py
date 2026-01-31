"""
Chart.js to image conversion tool for saving charts as PNG files.

This module provides adaptive sizing for chart images based on data complexity,
ensuring charts are large enough to be readable while respecting minimum dimensions.
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


class ChartToImageTool(AgentTool):
    """Tool for converting Chart.js configurations to PNG images.

    This tool uses adaptive sizing to ensure charts are large enough to be readable.
    Default dimensions are 1200x900 pixels, with automatic width scaling for charts
    with more than 10 data points.

    Attributes:
        dimension_calculator: Calculator for optimal image dimensions
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the ChartToImageTool with optional sizing configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        super().__init__()
        self.dimension_calculator = ImageDimensionCalculator(config)

    def _count_data_points(self, chart_config: dict) -> int:
        """Count the total number of data points in a chart configuration.

        Analyzes the chart's data structure to determine complexity for
        adaptive sizing calculations.

        Args:
            chart_config: Parsed Chart.js configuration dictionary

        Returns:
            Total number of data points across all datasets
        """
        data = chart_config.get("data", {})
        datasets = data.get("datasets", [])

        if not datasets:
            # Fallback to labels count if no datasets
            labels = data.get("labels", [])
            return len(labels)

        # Count data points across all datasets
        total_points = 0
        for dataset in datasets:
            dataset_data = dataset.get("data", [])
            if isinstance(dataset_data, list):
                total_points = max(total_points, len(dataset_data))

        return total_points

    def get_tool_function(self) -> Callable:
        """Return the chart to image conversion function."""

        async def save_chart_as_image(
            chart_config: str,
            filename: str,
            width: int | None = None,
            height: int | None = None,
            background_color: str = "white",
        ) -> str:
            """
            Convert a Chart.js configuration to a PNG image and save it to file storage.

            Uses adaptive sizing to ensure charts are large enough to be readable.
            Default dimensions are 1200x900 pixels, with automatic width scaling
            for charts with more than 10 data points.

            Args:
                chart_config: JSON string containing the Chart.js configuration
                             (the complete chartConfig object with type, data, options)
                filename: Name for the output PNG file (without extension)
                width: Width of the chart in pixels (default: auto-calculated, min 1200)
                height: Height of the chart in pixels (default: auto-calculated, min 900)
                background_color: Background color for the chart (default: "white")

            Returns:
                Success message with file_id

            Example chart_config:
            {
                "type": "bar",
                "data": {
                    "labels": ["Mon", "Tue", "Wed"],
                    "datasets": [{
                        "label": "Sales",
                        "data": [120, 150, 100],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)"
                    }]
                },
                "options": {
                    "responsive": true,
                    "plugins": {
                        "title": {
                            "display": true,
                            "text": "Weekly Sales"
                        }
                    }
                }
            }
            """
            self._ensure_initialized()

            # Check for required dependencies (with auto-install attempt)
            available, error = _ensure_playwright()
            if not available:
                return f"Error: {error}"

            # Validate inputs
            if not chart_config or not chart_config.strip():
                return "Error: chart_config cannot be empty"

            if not filename or not filename.strip():
                return "Error: filename cannot be empty"

            # Check file storage availability
            if not self.file_storage:
                raise ToolDependencyError(
                    "File storage is required but was not provided. "
                    "Ensure file_storage is set via set_context()."
                )

            try:
                # Parse the chart config
                try:
                    config = json.loads(chart_config)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in chart_config: {str(e)}"

                # Validate and auto-correct chart config before rendering
                try:
                    from ..processing.rich_content_validation import ChartValidator

                    validator = ChartValidator()
                    # Re-serialize to string for validator
                    validation_result = validator.validate(json.dumps(config))

                    if validation_result.corrected_content:
                        logger.info(
                            f"Chart config auto-corrected. Repairs: {validation_result.repairs_made}"
                        )
                        config = json.loads(validation_result.corrected_content)
                    elif validation_result.errors:
                        logger.warning(f"Chart validation errors: {validation_result.errors}")
                except ImportError:
                    logger.debug("ChartValidator not available, skipping validation")

                # Extract chartConfig if wrapped (validator adds wrapper for frontend)
                # For rendering, we need the raw Chart.js config
                if (
                    isinstance(config, dict)
                    and config.get("type") == "chartjs"
                    and "chartConfig" in config
                ):
                    config = config["chartConfig"]

                # Validate chart config structure
                if "type" not in config:
                    return "Error: chart_config must include a 'type' field"
                if "data" not in config:
                    return "Error: chart_config must include a 'data' field"

                # Count data points for metadata
                data_point_count = self._count_data_points(config)

                # Get minimum dimensions from config
                min_width = self.dimension_calculator.config.chart_min_width
                min_height = self.dimension_calculator.config.chart_min_height

                # Render at high resolution using deviceScaleFactor
                # This ensures crisp rendering without pixelization
                render_size = 1600
                device_scale = 2  # 2x resolution for crisp images

                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: {background_color};
        }}
        #chartContainer {{
            display: inline-block;
            background-color: {background_color};
        }}
        #chartWrapper {{
            width: {render_size}px;
            height: {render_size}px;
            position: relative;
        }}
    </style>
</head>
<body>
    <div id="chartContainer">
        <div id="chartWrapper">
            <canvas id="myChart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('myChart');
        const config = {json.dumps(config)};

        // Let Chart.js maintain natural aspect ratio
        if (!config.options) {{
            config.options = {{}};
        }}
        config.options.responsive = true;
        config.options.maintainAspectRatio = true;

        new Chart(ctx, config);
    </script>
</body>
</html>
"""

                # Import playwright here after ensuring it's available
                from playwright.async_api import async_playwright

                # Use Playwright to render at high resolution
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page(
                        viewport={"width": render_size + 100, "height": render_size + 100},
                        device_scale_factor=device_scale,
                    )

                    # Load the HTML
                    await page.set_content(html_content)

                    # Wait for Chart.js to render
                    await page.wait_for_timeout(1500)

                    # Get the actual rendered size of the canvas (in CSS pixels)
                    canvas_box = await page.evaluate(
                        """
                        () => {
                            const canvas = document.getElementById('myChart');
                            const rect = canvas.getBoundingClientRect();
                            return { width: rect.width, height: rect.height };
                        }
                    """
                    )

                    # Screenshot just the canvas area (high resolution due to device_scale)
                    screenshot_bytes = await page.screenshot(
                        type="png",
                        clip={
                            "x": 0,
                            "y": 0,
                            "width": canvas_box["width"],
                            "height": canvas_box["height"],
                        },
                    )

                    await browser.close()

                # Scale up if needed to meet minimums while preserving aspect ratio
                try:
                    import io

                    from PIL import Image

                    img = Image.open(io.BytesIO(screenshot_bytes))
                    current_width, current_height = img.size

                    # Calculate scale to meet BOTH minimums while preserving ratio
                    width_scale = min_width / current_width if current_width < min_width else 1.0
                    height_scale = (
                        min_height / current_height if current_height < min_height else 1.0
                    )
                    scale = max(width_scale, height_scale)

                    if scale > 1.0:
                        new_width = int(current_width * scale)
                        new_height = int(current_height * scale)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                        output = io.BytesIO()
                        img.save(output, format="PNG")
                        screenshot_bytes = output.getvalue()
                        final_width = new_width
                        final_height = new_height
                    else:
                        final_width = current_width
                        final_height = current_height

                    logger.debug(
                        f"Chart dimensions: {final_width}x{final_height} "
                        f"(original: {current_width}x{current_height}, scale: {scale:.2f})"
                    )

                except ImportError:
                    logger.warning("PIL not available, cannot resize image to meet minimums")
                    final_width = int(canvas_box["width"])
                    final_height = int(canvas_box["height"])

                # Create safe filename
                safe_filename = "".join(
                    c for c in filename if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_filename = safe_filename.replace(" ", "_")
                if not safe_filename.lower().endswith(".png"):
                    safe_filename += ".png"

                # Store the image with dimension metadata
                tags = ["chart", "png", "generated", f"chart-type:{config['type']}"]

                # Build custom metadata with image dimensions
                custom_metadata = {
                    "width_px": final_width,
                    "height_px": final_height,
                    "content_type": "chart",
                    "data_complexity": data_point_count,
                    "chart_type": config["type"],
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
                    f"Created chart image: {safe_filename} (file_id: {file_id}, "
                    f"dimensions: {final_width}x{final_height}, data_points: {data_point_count}, view URL: {view_url})"
                )
                return f"Chart saved successfully as PNG!\n\n![{safe_filename}]({view_url})"

            except Exception as e:
                error_str = str(e)
                # Check for Linux system dependency errors
                error_str = _get_linux_deps_error_message(error_str)
                error_msg = f"Failed to create chart image: {error_str}"
                logger.error(error_msg, exc_info=True)
                return f"Error creating chart image: {error_str}"

        return save_chart_as_image


__all__ = ["ChartToImageTool"]
