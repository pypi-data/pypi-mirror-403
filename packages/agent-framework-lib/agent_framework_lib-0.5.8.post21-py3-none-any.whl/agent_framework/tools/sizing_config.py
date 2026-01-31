"""
Configuration for adaptive image sizing.

This module provides configuration dataclasses and dimension calculation utilities
for generating optimally-sized images (charts, diagrams, tables) and their
integration into PDF documents.
"""

import re
from dataclasses import dataclass
from datetime import datetime


def _parse_gantt_date(date_str: str, date_format: str) -> datetime | None:
    """Parse a date string using the Mermaid Gantt date format.

    Args:
        date_str: The date string to parse
        date_format: The Mermaid dateFormat (e.g., 'YYYY-MM-DD')

    Returns:
        Parsed datetime or None if parsing fails
    """
    # Convert Mermaid date format to Python strptime format
    format_map = {
        "YYYY": "%Y",
        "YY": "%y",
        "MM": "%m",
        "DD": "%d",
        "HH": "%H",
        "mm": "%M",
        "ss": "%S",
    }

    py_format = date_format
    for mermaid_fmt, py_fmt in format_map.items():
        py_format = py_format.replace(mermaid_fmt, py_fmt)

    try:
        return datetime.strptime(date_str.strip(), py_format)
    except ValueError:
        return None


@dataclass
class ImageSizingConfig:
    """Configuration for adaptive image sizing.

    This dataclass defines all default dimensions and constraints for:
    - Chart image generation
    - Mermaid diagram generation
    - Table image generation
    - PDF embedding constraints

    Attributes:
        chart_min_width: Minimum width for chart images (default: 1200px)
        chart_min_height: Minimum height for chart images (default: 900px)
        chart_width_per_datapoint: Additional width per data point beyond 10 (default: 80px)
        mermaid_base_width: Base width for Mermaid diagrams (default: 1200px)
        mermaid_base_height: Base height for Mermaid diagrams (default: 800px)
        mermaid_width_per_node: Additional width per node beyond 15 (default: 50px)
        mermaid_height_per_node: Additional height per node beyond 15 (default: 40px)
        table_min_width: Minimum width for table images (default: 800px)
        table_width_per_column: Width allocated per column (default: 150px)
        table_min_width_many_columns: Minimum width for tables with >5 columns (default: 1200px)
        absolute_min_width: Absolute minimum width for any image (default: 600px)
        absolute_min_height: Absolute minimum height for any image (default: 400px)
        pdf_page_width_px: PDF page width in pixels at 96 DPI (default: 793px for A4)
        pdf_page_height_px: PDF page height in pixels at 96 DPI (default: 1122px for A4 minus margins)
        pdf_max_image_dimension: Maximum dimension before downsampling (default: 4000px)
        pdf_min_dpi: Minimum DPI for print quality (default: 150)
        min_readable_width: Minimum width for readable images (default: 400px)
        min_readable_height: Minimum height for readable images (default: 300px)
    """

    # Chart defaults
    chart_min_width: int = 1200
    chart_min_height: int = 900
    chart_width_per_datapoint: int = 80  # Additional width per data point > 10

    # Mermaid defaults
    mermaid_base_width: int = 1200
    mermaid_base_height: int = 800
    mermaid_width_per_node: int = 50  # Additional width per node > 15
    mermaid_height_per_node: int = 40  # Additional height per node > 15

    # Table defaults
    table_min_width: int = 800
    table_width_per_column: int = 150
    table_min_width_many_columns: int = 1200  # For > 5 columns

    # Absolute minimums
    absolute_min_width: int = 600
    absolute_min_height: int = 400

    # PDF constraints
    pdf_page_width_px: int = 793  # A4 at 96 DPI minus margins
    pdf_page_height_px: int = 1122  # A4 at 96 DPI minus 2cm margins
    pdf_max_image_dimension: int = 4000
    pdf_min_dpi: int = 150

    # Minimum readable dimensions
    min_readable_width: int = 400
    min_readable_height: int = 300

    # Gantt-specific sizing
    gantt_min_width: int = 2000  # Gantt charts need more horizontal space
    gantt_width_per_day: int = 20  # Width per day in the timeline
    gantt_width_per_week: int = 140  # Width per week for longer timelines
    gantt_max_width: int = 12000  # Maximum width to prevent excessive images
    gantt_height_per_task: int = 40  # Height per task row


class ImageDimensionCalculator:
    """Calculates optimal image dimensions based on content.

    This class provides methods to calculate appropriate dimensions for
    different types of generated images (charts, Mermaid diagrams, tables)
    based on their content complexity.

    Example:
        calculator = ImageDimensionCalculator()

        # Calculate chart dimensions for 15 data points
        width, height = calculator.calculate_chart_dimensions(data_point_count=15)

        # Calculate Mermaid dimensions from diagram code
        width, height = calculator.calculate_mermaid_dimensions(mermaid_code)

        # Calculate table dimensions for 8 columns
        width, height = calculator.calculate_table_dimensions(column_count=8, row_count=10)
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the calculator with optional custom configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        self.config = config or ImageSizingConfig()

    def _apply_minimums_with_aspect_ratio(
        self,
        width: int,
        height: int,
        min_width: int,
        min_height: int,
    ) -> tuple[int, int]:
        """Apply minimum dimensions while preserving aspect ratio.

        If either dimension is below the minimum, scale up both dimensions
        proportionally to meet the minimum while preserving the original
        aspect ratio.

        Args:
            width: Current width
            height: Current height
            min_width: Minimum required width
            min_height: Minimum required height

        Returns:
            Tuple of (width, height) that meets minimums while preserving ratio
        """
        if width <= 0 or height <= 0:
            return (min_width, min_height)

        # Calculate scale factors needed to meet each minimum
        width_scale = min_width / width if width < min_width else 1.0
        height_scale = min_height / height if height < min_height else 1.0

        # Use the larger scale factor to ensure both minimums are met
        scale = max(width_scale, height_scale)

        if scale > 1.0:
            # Scale up both dimensions proportionally
            new_width = int(width * scale)
            new_height = int(height * scale)
            return (new_width, new_height)

        return (width, height)

    def calculate_chart_dimensions(
        self,
        data_point_count: int,
        requested_width: int | None = None,
        requested_height: int | None = None,
    ) -> tuple[int, int]:
        """Calculate optimal chart dimensions based on data complexity.

        For charts with more than 10 data points, the width is automatically
        increased to accommodate labels without overlap. If user-requested
        dimensions are provided, they are scaled up proportionally to meet
        minimum requirements while preserving the aspect ratio.

        Args:
            data_point_count: Number of data points in the chart
            requested_width: User-requested width (optional)
            requested_height: User-requested height (optional)

        Returns:
            Tuple of (width, height) in pixels
        """
        # If user provided both dimensions, preserve their aspect ratio
        if requested_width is not None and requested_height is not None:
            width, height = self._apply_minimums_with_aspect_ratio(
                requested_width,
                requested_height,
                self.config.chart_min_width,
                self.config.chart_min_height,
            )
            # Still scale for many data points if needed
            if data_point_count > 10:
                extra_points = data_point_count - 10
                extra_width = extra_points * self.config.chart_width_per_datapoint
                if width < self.config.chart_min_width + extra_width:
                    # Scale both dimensions to accommodate data points
                    scale = (self.config.chart_min_width + extra_width) / width
                    width = int(width * scale)
                    height = int(height * scale)
            return (width, height)

        # Start with minimum dimensions
        width = self.config.chart_min_width
        height = self.config.chart_min_height

        # Scale width for many data points
        if data_point_count > 10:
            extra_points = data_point_count - 10
            width += extra_points * self.config.chart_width_per_datapoint

        # Apply user-requested dimensions if provided (single dimension)
        if requested_width is not None:
            width = max(requested_width, self.config.chart_min_width)

        if requested_height is not None:
            height = max(requested_height, self.config.chart_min_height)

        return (width, height)

    def count_mermaid_nodes(self, mermaid_code: str) -> int:
        """Count the number of nodes in a Mermaid diagram.

        Uses regex patterns to identify node definitions in various
        Mermaid diagram types (flowchart, sequence, class, etc.).

        Args:
            mermaid_code: The Mermaid diagram code

        Returns:
            Estimated number of nodes in the diagram
        """
        if not mermaid_code:
            return 0

        # Clean the code
        clean_code = mermaid_code.strip()

        # Remove markdown code block markers if present
        if clean_code.startswith("```"):
            clean_code = re.sub(r"```\w*\n?", "", clean_code)
            clean_code = clean_code.replace("```", "").strip()

        nodes: set[str] = set()

        # Pattern for flowchart/graph nodes: A, B[text], C{text}, D((text)), E>text], F[(text)]
        # Matches node IDs at the start of lines or after arrows
        flowchart_pattern = r"(?:^|\s|-->|--\>|->|--|-\.-|==>|==\>|-.->)([A-Za-z_][A-Za-z0-9_]*)(?:\[|\{|\(|\>|$|\s|;)"

        # Pattern for sequence diagram participants
        sequence_pattern = r"(?:participant|actor)\s+([A-Za-z_][A-Za-z0-9_]*)"

        # Pattern for class diagram classes
        class_pattern = r"(?:class)\s+([A-Za-z_][A-Za-z0-9_]*)"

        # Pattern for state diagram states
        state_pattern = r'(?:state)\s+(?:"[^"]*"\s+as\s+)?([A-Za-z_][A-Za-z0-9_]*)'

        # Pattern for ER diagram entities
        er_pattern = r"([A-Za-z_][A-Za-z0-9_]*)\s+(?:\{|\|\||\|o|o\|)"

        # Pattern for gantt tasks
        gantt_pattern = r"^\s*([A-Za-z_][A-Za-z0-9_ ]*?)\s*:"

        # Pattern for pie chart sections
        pie_pattern = r'"([^"]+)"\s*:\s*\d+'

        # Apply all patterns
        for pattern in [
            flowchart_pattern,
            sequence_pattern,
            class_pattern,
            state_pattern,
            er_pattern,
        ]:
            matches = re.findall(pattern, clean_code, re.MULTILINE | re.IGNORECASE)
            nodes.update(m for m in matches if m and len(m) > 0)

        # Gantt and pie patterns (count lines/sections)
        gantt_matches = re.findall(gantt_pattern, clean_code, re.MULTILINE)
        pie_matches = re.findall(pie_pattern, clean_code)

        # Add gantt tasks and pie sections
        nodes.update(f"gantt_{i}" for i, _ in enumerate(gantt_matches))
        nodes.update(f"pie_{i}" for i, _ in enumerate(pie_matches))

        # Fallback: count lines with arrows or relationships as a minimum
        if len(nodes) == 0:
            arrow_lines = re.findall(r".*(?:-->|->|--|==>|=>|\.->).*", clean_code)
            return max(len(arrow_lines) * 2, 2)  # At least 2 nodes per arrow line

        return len(nodes)

    def _is_gantt_diagram(self, mermaid_code: str) -> bool:
        """Check if the Mermaid code is a Gantt diagram.

        Args:
            mermaid_code: The Mermaid diagram code

        Returns:
            True if this is a Gantt diagram
        """
        clean_code = mermaid_code.strip().lower()
        if clean_code.startswith("```"):
            clean_code = re.sub(r"```\w*\n?", "", clean_code)
            clean_code = clean_code.replace("```", "").strip()

        first_line = clean_code.split("\n")[0].strip()
        return first_line.startswith("gantt")

    def _parse_gantt_info(self, mermaid_code: str) -> tuple[int, int]:
        """Parse Gantt diagram to extract task count and date range span.

        Args:
            mermaid_code: The Mermaid Gantt diagram code

        Returns:
            Tuple of (task_count, days_span) where days_span is the timeline duration
        """
        clean_code = mermaid_code.strip()
        if clean_code.startswith("```"):
            clean_code = re.sub(r"```\w*\n?", "", clean_code)
            clean_code = clean_code.replace("```", "").strip()

        # Extract dateFormat (default: YYYY-MM-DD)
        # Note: dateFormat is parsed but dates are extracted using common patterns
        # since Mermaid supports various date formats
        _ = re.search(r"dateFormat\s+(\S+)", clean_code)  # For future use

        # Count tasks (lines with : that aren't directives)
        task_pattern = r"^\s*[^:\s][^:]*\s*:\s*(?!dateFormat|title|excludes|section)"
        task_lines = re.findall(task_pattern, clean_code, re.MULTILINE)
        task_count = len(task_lines)

        # Also count section headers as they take vertical space
        section_count = len(re.findall(r"^\s*section\s+", clean_code, re.MULTILINE))

        # Extract all dates from the diagram
        # Pattern for dates in task definitions: task : status, date, duration
        # or task : date, duration
        dates: list[datetime] = []

        # Common date patterns in Gantt charts
        # Format: YYYY-MM-DD
        date_matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", clean_code)
        for date_str in date_matches:
            parsed = _parse_gantt_date(date_str, "YYYY-MM-DD")
            if parsed:
                dates.append(parsed)

        # Also try to parse duration-based tasks to estimate end dates
        # Pattern: after task1, 5d or 2w
        duration_pattern = r"(\d+)([dwmh])"
        duration_matches = re.findall(duration_pattern, clean_code)

        # Calculate days span
        if len(dates) >= 2:
            min_date = min(dates)
            max_date = max(dates)
            days_span = (max_date - min_date).days

            # Add estimated duration from duration patterns
            total_duration_days = 0
            for amount, unit in duration_matches:
                amount = int(amount)
                if unit == "d":
                    total_duration_days += amount
                elif unit == "w":
                    total_duration_days += amount * 7
                elif unit == "m":
                    total_duration_days += amount * 30

            # Use the larger of explicit date range or estimated duration
            days_span = max(days_span, total_duration_days // 2)  # Divide by 2 as tasks overlap
        elif duration_matches:
            # No explicit dates, estimate from durations
            total_duration_days = 0
            for amount, unit in duration_matches:
                amount = int(amount)
                if unit == "d":
                    total_duration_days += amount
                elif unit == "w":
                    total_duration_days += amount * 7
                elif unit == "m":
                    total_duration_days += amount * 30
            days_span = max(30, total_duration_days // 2)  # Minimum 30 days
        else:
            # Default to 30 days if we can't determine
            days_span = 30

        return (task_count + section_count, max(days_span, 7))

    def calculate_gantt_dimensions(
        self,
        mermaid_code: str,
        requested_width: int | None = None,
        requested_height: int | None = None,
    ) -> tuple[int, int]:
        """Calculate optimal Gantt diagram dimensions based on timeline and tasks.

        Gantt diagrams need special handling because their width depends on
        the timeline duration, not just the number of nodes.

        Args:
            mermaid_code: The Mermaid Gantt diagram code
            requested_width: User-requested width (optional)
            requested_height: User-requested height (optional)

        Returns:
            Tuple of (width, height) in pixels
        """
        task_count, days_span = self._parse_gantt_info(mermaid_code)

        # Calculate width based on timeline duration
        if days_span <= 14:
            # Short timeline: use per-day width
            timeline_width = days_span * self.config.gantt_width_per_day
        elif days_span <= 90:
            # Medium timeline: use per-week width
            weeks = (days_span + 6) // 7
            timeline_width = weeks * self.config.gantt_width_per_week
        else:
            # Long timeline: scale down to fit
            months = (days_span + 29) // 30
            timeline_width = months * 200  # 200px per month

        # Ensure minimum width and cap at maximum
        min_width = max(self.config.gantt_min_width, timeline_width + 400)  # +400 for labels
        min_width = min(min_width, self.config.gantt_max_width)

        # Calculate height based on task count
        min_height = max(
            self.config.mermaid_base_height,
            100 + (task_count * self.config.gantt_height_per_task),
        )

        # If user provided both dimensions, preserve their aspect ratio
        if requested_width is not None and requested_height is not None:
            width, height = self._apply_minimums_with_aspect_ratio(
                requested_width,
                requested_height,
                min_width,
                min_height,
            )
            return (width, height)

        # Start with calculated minimum dimensions
        width = min_width
        height = min_height

        # Apply user-requested dimensions if provided (single dimension)
        if requested_width is not None:
            width = max(requested_width, min_width)

        if requested_height is not None:
            height = max(requested_height, min_height)

        return (width, height)

    def calculate_mermaid_dimensions(
        self,
        mermaid_code: str,
        requested_width: int | None = None,
        requested_height: int | None = None,
    ) -> tuple[int, int]:
        """Calculate optimal Mermaid diagram dimensions based on complexity.

        For diagrams with more than 15 nodes, dimensions are automatically
        increased proportionally to ensure readability. If user-requested
        dimensions are provided, they are scaled up proportionally to meet
        minimum requirements while preserving the aspect ratio.

        Gantt diagrams receive special handling with timeline-based width
        calculation.

        Args:
            mermaid_code: The Mermaid diagram code
            requested_width: User-requested width (optional)
            requested_height: User-requested height (optional)

        Returns:
            Tuple of (width, height) in pixels
        """
        # Check if this is a Gantt diagram - use specialized calculation
        if self._is_gantt_diagram(mermaid_code):
            return self.calculate_gantt_dimensions(mermaid_code, requested_width, requested_height)

        # Count nodes to determine complexity
        node_count = self.count_mermaid_nodes(mermaid_code)

        # Calculate minimum dimensions based on complexity
        min_width = self.config.mermaid_base_width
        min_height = self.config.mermaid_base_height

        if node_count > 15:
            extra_nodes = node_count - 15
            min_width += extra_nodes * self.config.mermaid_width_per_node
            min_height += extra_nodes * self.config.mermaid_height_per_node

        # If user provided both dimensions, preserve their aspect ratio
        if requested_width is not None and requested_height is not None:
            width, height = self._apply_minimums_with_aspect_ratio(
                requested_width,
                requested_height,
                min_width,
                min_height,
            )
            return (width, height)

        # Start with calculated minimum dimensions
        width = min_width
        height = min_height

        # Apply user-requested dimensions if provided (single dimension)
        if requested_width is not None:
            width = max(requested_width, min_width)

        if requested_height is not None:
            height = max(requested_height, min_height)

        return (width, height)

    def calculate_table_dimensions(
        self,
        column_count: int,
        row_count: int,
        content_lengths: list[int] | None = None,
        requested_width: int | None = None,
        requested_height: int | None = None,
    ) -> tuple[int, int]:
        """Calculate optimal table dimensions based on content.

        Width is calculated based on column count, with a minimum of 1200px
        for tables with more than 5 columns. If user-requested dimensions
        are provided, they are scaled up proportionally to meet minimum
        requirements while preserving the aspect ratio.

        Args:
            column_count: Number of columns in the table
            row_count: Number of rows in the table
            content_lengths: Optional list of average content lengths per column
            requested_width: User-requested width (optional)
            requested_height: User-requested height (optional)

        Returns:
            Tuple of (width, height) in pixels
        """
        # Calculate minimum width from column count
        min_width = max(
            self.config.table_min_width, column_count * self.config.table_width_per_column
        )

        # Enforce minimum for many columns
        if column_count > 5:
            min_width = max(min_width, self.config.table_min_width_many_columns)

        # Adjust for content lengths if provided
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            if avg_length > 20:  # Long content
                min_width = int(min_width * 1.2)

        # Calculate minimum height based on row count
        row_height = 40
        header_height = 50
        padding = 60
        min_height = max(
            self.config.absolute_min_height, header_height + (row_count * row_height) + padding
        )

        # If user provided both dimensions, preserve their aspect ratio
        if requested_width is not None and requested_height is not None:
            width, height = self._apply_minimums_with_aspect_ratio(
                requested_width,
                requested_height,
                min_width,
                min_height,
            )
            return (width, height)

        # Start with calculated minimum dimensions
        width = min_width
        height = min_height

        # Apply user-requested dimensions if provided (single dimension)
        if requested_width is not None:
            width = max(requested_width, min_width)

        if requested_height is not None:
            height = max(requested_height, min_height)

        return (width, height)


__all__ = ["ImageSizingConfig", "ImageDimensionCalculator"]
