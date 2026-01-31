"""
HTML Content Analyzer for PDF generation.

This module analyzes HTML content to estimate text heights and calculate
available space for images on each page, enabling dynamic image resizing.
"""

import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup, Tag


@dataclass
class PageConfig:
    """Configuration for page dimensions and typography."""

    # Page dimensions in pixels (A4 at 96 DPI with 2cm margins)
    page_height_px: int = 1122
    page_width_px: int = 794
    margin_top_px: int = 76  # ~2cm
    margin_bottom_px: int = 76  # ~2cm

    # Typography settings
    base_font_size_pt: int = 12
    line_height: float = 1.6  # Slightly higher for safety
    chars_per_line: int = 70  # More conservative (accounts for wider chars)

    # Element heights in pixels (more generous estimates)
    h1_height_px: int = 60
    h2_height_px: int = 55
    h3_height_px: int = 45
    h4_height_px: int = 40
    p_margin_px: int = 20  # margin-bottom
    figure_margin_px: int = 40  # margin top + bottom (more space)
    figcaption_height_px: int = 40  # More space for caption

    # Minimum image height to keep readable
    min_image_height_px: int = 120  # Lower minimum to allow more fitting

    # Threshold: if less than this % of page remains, don't try to fit
    min_fit_threshold: float = 0.25  # 25% - more aggressive fitting

    # Safety margin to subtract from available space (accounts for rendering differences)
    safety_margin_px: int = 50

    @property
    def usable_height_px(self) -> int:
        """Usable page height after margins."""
        return self.page_height_px - self.margin_top_px - self.margin_bottom_px

    @property
    def line_height_px(self) -> float:
        """Line height in pixels."""
        return self.base_font_size_pt * self.line_height * (96 / 72)  # pt to px


@dataclass
class ImagePlacement:
    """Information about an image and its available space."""

    file_id: str
    text_height_before_px: int
    available_height_px: int
    should_resize: bool
    target_height_px: Optional[int]
    is_new_page: bool  # True if section starts with break-before


class HTMLContentAnalyzer:
    """Analyzes HTML content to calculate available space for images."""

    def __init__(self, config: Optional[PageConfig] = None):
        """Initialize the analyzer with page configuration.

        Args:
            config: Page configuration. If None, uses defaults.
        """
        self.config = config or PageConfig()

    def analyze_html(self, html_content: str) -> dict[str, ImagePlacement]:
        """Analyze HTML and calculate available space for each image.

        Args:
            html_content: HTML string to analyze

        Returns:
            Dictionary mapping file_id to ImagePlacement info
        """
        soup = BeautifulSoup(html_content, "html.parser")
        placements: dict[str, ImagePlacement] = {}

        # Find all sections or top-level content
        sections = soup.find_all("div", class_="section")

        if not sections:
            # No sections, analyze body directly
            sections = [soup.body] if soup.body else [soup]

        for section in sections:
            if not isinstance(section, Tag):
                continue

            # Check if section starts a new page
            is_new_page = "break-before" in section.get("class", [])

            # Find all images in this section
            figures = section.find_all("figure")

            for figure in figures:
                img = figure.find("img")
                if not img:
                    continue

                src = img.get("src", "")
                file_id_match = re.search(r"file_id:([a-f0-9\-]+)", src)
                if not file_id_match:
                    continue

                file_id = file_id_match.group(1)

                # Calculate text height before this figure
                text_height = self._calculate_text_height_before(section, figure)

                # Calculate available space
                available = self._calculate_available_space(text_height, is_new_page)

                # Determine if we should resize
                should_resize, target_height = self._should_resize_image(available)

                placements[file_id] = ImagePlacement(
                    file_id=file_id,
                    text_height_before_px=text_height,
                    available_height_px=available,
                    should_resize=should_resize,
                    target_height_px=target_height,
                    is_new_page=is_new_page,
                )

        return placements

    def _calculate_text_height_before(self, section: Tag, figure: Tag) -> int:
        """Calculate the height of text content before a figure.

        Args:
            section: The section containing the figure
            figure: The figure element

        Returns:
            Estimated height in pixels
        """
        total_height = 0

        for element in section.children:
            if element == figure:
                break

            if not isinstance(element, Tag):
                continue

            tag_name = element.name.lower() if element.name else ""

            if tag_name == "h1":
                total_height += self.config.h1_height_px
            elif tag_name == "h2":
                total_height += self.config.h2_height_px
            elif tag_name == "h3":
                total_height += self.config.h3_height_px
            elif tag_name == "p":
                total_height += self._estimate_paragraph_height(element)
            elif tag_name == "ul" or tag_name == "ol":
                total_height += self._estimate_list_height(element)
            elif tag_name == "figure":
                # Another figure before this one - skip to next page calculation
                # This is a simplification; in reality we'd need to track page breaks
                pass

        return total_height

    def _estimate_paragraph_height(self, p: Tag) -> int:
        """Estimate the height of a paragraph.

        Args:
            p: Paragraph element

        Returns:
            Estimated height in pixels
        """
        text = p.get_text()
        char_count = len(text)

        # Estimate number of lines
        lines = max(1, char_count // self.config.chars_per_line + 1)

        # Height = lines * line_height + margin
        height = int(lines * self.config.line_height_px + self.config.p_margin_px)

        return height

    def _estimate_list_height(self, list_elem: Tag) -> int:
        """Estimate the height of a list.

        Args:
            list_elem: UL or OL element

        Returns:
            Estimated height in pixels
        """
        items = list_elem.find_all("li")
        total_height = 0

        for item in items:
            text = item.get_text()
            char_count = len(text)
            lines = max(1, char_count // self.config.chars_per_line + 1)
            total_height += int(lines * self.config.line_height_px)

        # Add some margin
        total_height += self.config.p_margin_px

        return total_height

    def _calculate_available_space(self, text_height: int, is_new_page: bool) -> int:
        """Calculate available space for an image.

        Args:
            text_height: Height of text before the image
            is_new_page: Whether the section starts a new page

        Returns:
            Available height in pixels for the image
        """
        usable = self.config.usable_height_px

        # Subtract text height
        remaining = usable - text_height

        # Subtract figure margins and figcaption
        remaining -= self.config.figure_margin_px
        remaining -= self.config.figcaption_height_px

        # Ensure non-negative
        return max(0, remaining)

    def _should_resize_image(
        self, available_height: int
    ) -> tuple[bool, Optional[int]]:
        """Determine if an image should be resized and to what height.

        Logic:
        - If at least 30% of the page is available for the image, resize to fill it
        - The image can take ALL the available space (no need to leave room after)
        - Only skip to next page if less than 30% is available (image would be too small)

        Args:
            available_height: Available space in pixels for the image

        Returns:
            Tuple of (should_resize, target_height)
        """
        min_threshold = int(self.config.usable_height_px * self.config.min_fit_threshold)

        # If available space is less than minimum threshold (30% of page),
        # the image would be too small - go to next page instead
        if available_height < min_threshold:
            return False, None

        # If available space is less than minimum readable height, go to next page
        if available_height < self.config.min_image_height_px:
            return False, None

        # Resize to fill ALL available space (image can take 100% of remaining space)
        # Apply safety margin to account for rendering differences
        target = available_height - getattr(self.config, 'safety_margin_px', 30)
        target = max(target, self.config.min_image_height_px)
        
        return True, target

    def get_target_height_for_image(
        self,
        file_id: str,
        placements: dict[str, ImagePlacement],
        original_height: int,
    ) -> int:
        """Get the target height for an image based on analysis.

        Args:
            file_id: The file ID of the image
            placements: Dictionary of image placements from analyze_html
            original_height: Original height of the image

        Returns:
            Target height in pixels (may be original if no resize needed)
        """
        if file_id not in placements:
            return original_height

        placement = placements[file_id]

        if not placement.should_resize:
            return original_height

        if placement.target_height_px is None:
            return original_height

        # Only resize if image is taller than available space
        if original_height <= placement.target_height_px:
            return original_height

        return placement.target_height_px


__all__ = ["HTMLContentAnalyzer", "ImagePlacement", "PageConfig"]
