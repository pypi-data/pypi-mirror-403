"""
Adaptive CSS generation for PDF images.

This module provides the AdaptivePDFCSS class for generating CSS rules
that ensure images are properly sized, centered, and spaced within PDF documents.
"""

from dataclasses import dataclass
from typing import Literal

from .sizing_config import ImageSizingConfig


# Type alias for size preferences
SizePreference = Literal["small", "medium", "large", "full"]


@dataclass
class PDFImageConfig:
    """Configuration for image embedding in PDF.

    Attributes:
        size_preference: Desired size ("small", "medium", "large", "full")
        center_images: Whether to center images horizontally
        vertical_margin_px: Vertical margin above and below images in pixels
        maintain_aspect_ratio: Whether to preserve aspect ratio when scaling
        fit_to_page: Whether to fit images within page boundaries
        enable_page_breaks: Whether to enable page break handling for large images
    """

    size_preference: SizePreference = "large"
    center_images: bool = True
    vertical_margin_px: int = 20
    maintain_aspect_ratio: bool = True
    fit_to_page: bool = True
    enable_page_breaks: bool = True


class AdaptivePDFCSS:
    """Generates adaptive CSS for PDF images.

    This class provides methods to generate CSS rules for:
    - Image sizing based on size preferences (small=50%, medium=75%, large/full=100%)
    - Horizontal centering of images
    - Consistent vertical spacing between images
    - Maximum width constraints to prevent overflow

    Example:
        css_generator = AdaptivePDFCSS()

        # Generate CSS for medium-sized images
        image_css = css_generator.generate_image_css(size_preference="medium")

        # Generate container CSS for centering
        container_css = css_generator.generate_container_css()

        # Get complete CSS for PDF
        full_css = css_generator.generate_complete_css(
            size_preference="large",
            vertical_margin_px=30
        )
    """

    # Size preference to percentage mapping
    SIZE_PERCENTAGES: dict[str, int] = {
        "small": 50,
        "medium": 75,
        "large": 100,
        "full": 100,
    }

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the CSS generator with optional custom configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        self.config = config or ImageSizingConfig()

    def get_size_percentage(self, size_preference: SizePreference = "large") -> int:
        """Get the percentage for a given size preference.

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")

        Returns:
            Percentage as an integer (50, 75, or 100)
        """
        return self.SIZE_PERCENTAGES.get(size_preference, 100)

    def generate_image_css(
        self,
        size_preference: SizePreference = "large",
        vertical_margin_px: int = 20,
        max_height_px: int | None = None,
    ) -> str:
        """Generate CSS for image sizing and centering.

        Creates CSS rules that:
        - Set image width based on size preference percentage
        - Enforce maximum width to prevent page overflow
        - Enforce maximum height to prevent page overflow (if specified)
        - Center images horizontally using auto margins
        - Add vertical margins for spacing
        - Maintain aspect ratio with height: auto

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")
            vertical_margin_px: Vertical margin in pixels (default: 20)
            max_height_px: Maximum height in pixels (optional). If provided,
                          adds max-height constraint while preserving aspect ratio.

        Returns:
            CSS string for image styling
        """
        percentage = self.get_size_percentage(size_preference)

        # Build height constraint CSS if max_height is specified
        height_constraint = ""
        if max_height_px is not None:
            height_constraint = f"\n    max-height: {max_height_px}px;"

        css = f"""
/* Adaptive image sizing - {size_preference} ({percentage}% width) */
img {{
    width: {percentage}%;
    max-width: 100%;
    height: auto;{height_constraint}
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: {vertical_margin_px}px;
    margin-bottom: {vertical_margin_px}px;
}}
"""
        return css.strip()

    # Threshold for minimum page space to attempt fitting (50% = half page)
    # Images will only be resized to fit if at least this much space is available
    # This prevents images from becoming too small to read
    MIN_FIT_THRESHOLD: float = 0.25

    def generate_page_fit_css(
        self,
        size_preference: SizePreference = "large",
        max_height_px: int | None = None,
        enable_page_breaks: bool = True,
        vertical_margin_px: int = 20,
    ) -> str:
        """Generate CSS with width AND height constraints for page fitting.

        Creates CSS rules that ensure images fit within page boundaries:
        - Set max-width based on size preference percentage
        - Set max-height to 70% of page height (leaves room for text + caption)
        - page-break-inside: avoid keeps image whole
        - Center images horizontally
        - Maintain aspect ratio

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")
            max_height_px: Maximum height in pixels. If None, uses 70% of page height.
            enable_page_breaks: Whether to prevent image splitting (default: True)
            vertical_margin_px: Vertical margin in pixels (default: 20)

        Returns:
            CSS string for page-fitted image styling
        """
        percentage = self.get_size_percentage(size_preference)

        # 95% of page height - images are pre-resized in Python to fit available space
        # This CSS max-height is just a safety net
        if max_height_px is None:
            max_height_px = int(self.config.pdf_page_height_px * 0.95)

        # No page-break-inside:avoid - images are pre-resized in Python to fit
        # Adding page-break rules causes WeasyPrint to force unwanted page breaks

        css = f"""
/* Page-fitted image sizing - {size_preference} ({percentage}% max width) */
/* Images are pre-resized in Python to fit available space on each page */
/* NO page-break rules here - let content flow naturally */
img {{
    width: auto;
    max-width: {percentage}%;
    height: auto;
    max-height: {max_height_px}px;
    object-fit: contain;
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: {vertical_margin_px}px;
    margin-bottom: {vertical_margin_px}px;
}}
"""
        return css.strip()

    def generate_container_css(
        self,
        vertical_margin_px: int = 20,
    ) -> str:
        """Generate CSS for image container.

        Creates CSS rules for a container element that:
        - Centers its content horizontally
        - Provides consistent vertical spacing
        - Ensures proper text alignment for captions

        Args:
            vertical_margin_px: Vertical margin in pixels (default: 20)

        Returns:
            CSS string for container styling
        """
        css = f"""
/* Image container for centering and spacing */
.image-container {{
    text-align: center;
    margin-top: {vertical_margin_px}px;
    margin-bottom: {vertical_margin_px}px;
    width: 100%;
}}

.image-container img {{
    margin-top: 0;
    margin-bottom: 0;
}}

/* Figure element styling for images with captions */
figure {{
    text-align: center;
    margin: {vertical_margin_px}px auto;
    padding: 0;
}}

figure img {{
    margin-bottom: 10px;
}}

figcaption {{
    font-size: 0.9em;
    color: #666;
    font-style: italic;
}}
"""
        return css.strip()

    def generate_complete_css(
        self,
        size_preference: SizePreference = "large",
        vertical_margin_px: int = 20,
        include_base_styles: bool = True,
        enable_page_breaks: bool = True,
        max_height_px: int | None = None,
    ) -> str:
        """Generate complete CSS for PDF with images.

        Combines image CSS, container CSS, page break CSS, and optional base styles
        into a complete stylesheet for PDF generation.

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")
            vertical_margin_px: Vertical margin in pixels (default: 20)
            include_base_styles: Whether to include base page styles (default: True)
            enable_page_breaks: Whether to include page break CSS rules (default: True)
            max_height_px: Maximum height in pixels for images. If None, uses 90%
                          of pdf_page_height_px from config.

        Returns:
            Complete CSS string for PDF styling
        """
        parts = []

        if include_base_styles:
            parts.append(self._generate_base_styles())

        parts.append(
            self.generate_page_fit_css(
                size_preference, max_height_px, enable_page_breaks, vertical_margin_px
            )
        )
        parts.append(self.generate_container_css(vertical_margin_px))

        if enable_page_breaks:
            parts.append(self.generate_page_break_css())
            parts.append(self.generate_large_image_css(size_preference, max_height_px))

        return "\n\n".join(parts)

    def _generate_base_styles(self) -> str:
        """Generate base styles for PDF document.

        Returns:
            CSS string with base document styles
        """
        css = """
/* Base PDF document styles */
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}

p {
    margin-bottom: 1em;
}

/* Section container - groups related content */
.section {
    margin-bottom: 1.5em;
}

/* Force page break before element (ONLY for major sections with break-before class) */
.break-before {
    page-break-before: always;
}

/* Figure styling - NO page-break-inside:avoid to let images flow naturally */
/* Images are pre-resized in Python to fit available space */
figure {
    margin: 0.5em auto;
    text-align: center;
}

figure img {
    margin-bottom: 0.5em;
}

figcaption {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
}
"""
        return css.strip()

    def generate_page_break_css(
        self,
        force_page_break: bool = False,
    ) -> str:
        """Generate CSS rules for page break handling.

        Creates CSS rules to:
        - Prevent images from being split across pages (page-break-inside: avoid)
        - Optionally force a page break before large images (page-break-before: always)

        Args:
            force_page_break: If True, includes page-break-before: always
                             to force the image onto a new page.

        Returns:
            CSS string for page break handling
        """
        css_rules = ["page-break-inside: avoid"]

        if force_page_break:
            css_rules.insert(0, "page-break-before: always")

        css = f"""
/* Page break handling for images */
.page-break-avoid {{
    page-break-inside: avoid;
}}

.page-break-before {{
    page-break-before: always;
}}

.large-image {{
    page-break-inside: avoid;
    {'; '.join(css_rules)};
}}
"""
        return css.strip()

    def generate_large_image_css(
        self,
        size_preference: SizePreference = "large",
        max_height_px: int | None = None,
        vertical_margin_px: int = 20,
    ) -> str:
        """Generate CSS for large images that need their own page.

        Creates CSS rules specifically for images marked with .large-image class.
        These are images that are too tall to fit with any text content.

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")
            max_height_px: Maximum height in pixels. If None, uses 90% of page height.
            vertical_margin_px: Vertical margin in pixels (default: 20)

        Returns:
            CSS string for large image styling with page breaks
        """
        percentage = self.get_size_percentage(size_preference)

        # Large images get 90% of page height (they have their own page)
        if max_height_px is None:
            max_height_px = int(self.config.pdf_page_height_px * 0.9)

        css = f"""
/* Large image - gets its own page (for images > 70% page height) */
img.large-image {{
    width: auto;
    max-width: {percentage}%;
    height: auto;
    max-height: {max_height_px}px;
    object-fit: contain;
    page-break-before: always;
    page-break-inside: avoid;
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: {vertical_margin_px}px;
    margin-bottom: {vertical_margin_px}px;
}}
"""
        return css.strip()

    def generate_inline_style(
        self,
        size_preference: SizePreference = "large",
        vertical_margin_px: int = 20,
        max_height_px: int | None = None,
        enable_page_breaks: bool = False,
    ) -> str:
        """Generate inline style attribute for a single image.

        Useful when you need to apply styles directly to an img tag
        rather than using a stylesheet.

        Args:
            size_preference: Desired size ("small", "medium", "large", "full")
            vertical_margin_px: Vertical margin in pixels (default: 20)
            max_height_px: Maximum height in pixels (optional). If provided,
                          adds max-height constraint.
            enable_page_breaks: Whether to include page-break-inside: avoid
                               (default: False, as inline styles have limited
                               page break support)

        Returns:
            Style attribute value (without the style="" wrapper)
        """
        percentage = self.get_size_percentage(size_preference)

        style_parts = [
            f"width: {percentage}%",
            "max-width: 100%",
            "height: auto",
        ]

        if max_height_px is not None:
            style_parts.append(f"max-height: {max_height_px}px")
            style_parts.append("object-fit: contain")

        style_parts.extend(
            [
                "display: block",
                "margin-left: auto",
                "margin-right: auto",
                f"margin-top: {vertical_margin_px}px",
                f"margin-bottom: {vertical_margin_px}px",
            ]
        )

        if enable_page_breaks:
            style_parts.append("page-break-inside: avoid")

        return "; ".join(style_parts)

    def can_fit_with_resize(
        self,
        image_height: int,
        remaining_page_height: int,
    ) -> bool:
        """Check if an image can fit on the current page by resizing.

        If more than 50% of the page remains, we can resize the image to fit
        rather than forcing a page break. This provides better page utilization.

        Args:
            image_height: Height of the image in pixels
            remaining_page_height: Remaining height on current page in pixels

        Returns:
            True if the image can be resized to fit on the current page
        """
        # If more than 50% of page height remains, we can resize to fit
        half_page_height = int(self.config.pdf_page_height_px * 0.5)
        min_readable_height = self.config.min_readable_height

        # Can fit if:
        # 1. More than 50% of page remains
        # 2. The remaining space is at least min_readable_height (so image stays readable)
        return (
            remaining_page_height >= half_page_height
            and remaining_page_height >= min_readable_height
        )

    def should_force_page_break(
        self,
        image_height: int,
        remaining_page_height: int,
    ) -> bool:
        """Determine if an image should force a page break.

        An image should force a page break only if:
        1. It doesn't fit in the remaining space AND
        2. It can't be reasonably resized to fit (less than 50% page remaining) AND
        3. It would fit on a new page

        Args:
            image_height: Height of the image in pixels
            remaining_page_height: Remaining height on current page in pixels

        Returns:
            True if the image should force a page break
        """
        # If image fits in remaining space, no page break needed
        if image_height <= remaining_page_height:
            return False

        # If we can resize to fit (more than 50% page remaining), don't force page break
        if self.can_fit_with_resize(image_height, remaining_page_height):
            return False

        # Check if it would fit on a new page (90% of page height)
        max_page_height = int(self.config.pdf_page_height_px * 0.9)
        return image_height <= max_page_height

    def get_image_css_class(
        self,
        image_height: int,
        remaining_page_height: int | None = None,
    ) -> str:
        """Get the appropriate CSS class for an image based on its size.

        Determines whether an image should use the standard image class
        or the large-image class with page break handling.

        Logic:
        - Images <= 70% of page height: standard (can fit with text)
        - Images > 70% of page height: large-image (needs own page)

        Args:
            image_height: Height of the image in pixels
            remaining_page_height: Remaining height on current page in pixels.
                                  If None, only checks against page height.

        Returns:
            CSS class name to apply to the image
        """
        # 70% threshold - images larger than this get their own page
        threshold = int(self.config.pdf_page_height_px * 0.70)

        # If image is larger than 70% of page height, it needs its own page
        if image_height > threshold:
            return "large-image"

        return ""


__all__ = ["AdaptivePDFCSS", "PDFImageConfig", "SizePreference"]
