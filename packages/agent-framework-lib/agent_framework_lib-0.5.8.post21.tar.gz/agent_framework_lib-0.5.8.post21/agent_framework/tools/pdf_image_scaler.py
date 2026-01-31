"""
PDF image scaling utilities for adaptive image sizing.

This module provides the PDFImageScaler class for calculating optimal image
dimensions when embedding images in PDF documents, handling downsampling
of large images, and managing size preferences.
"""

import io
import logging
from typing import Literal

from .sizing_config import ImageSizingConfig


# Optional PIL dependency for image processing
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type alias for size preferences
SizePreference = Literal["small", "medium", "large", "full"]


class PDFImageScaler:
    """Handles image scaling for PDF embedding.

    This class provides methods to:
    - Calculate optimal dimensions for PDF embedding based on size preferences
    - Determine if images need downsampling
    - Downsample large images while maintaining quality
    - Get scale factors for different size preferences

    Example:
        scaler = PDFImageScaler()

        # Calculate dimensions for medium-sized image
        width, height = scaler.calculate_pdf_dimensions(
            original_width=2000,
            original_height=1500,
            size_preference="medium"
        )

        # Check if downsampling is needed
        if scaler.should_downsample(4500, 3000):
            new_bytes = scaler.downsample_image(image_bytes, 4000)
    """

    # Size preference to percentage mapping
    SIZE_PERCENTAGES: dict[str, int] = {
        "small": 50,
        "medium": 75,
        "large": 100,
        "full": 100,
    }

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the scaler with optional custom configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        self.config = config or ImageSizingConfig()

    def get_scale_factor(
        self,
        original_width: int,
        size_preference: SizePreference = "large",
    ) -> float:
        """Get scale factor based on size preference.

        Calculates the scale factor to apply to an image based on the
        user's size preference and the PDF page width constraint.

        Args:
            original_width: Original image width in pixels
            size_preference: Desired size ("small", "medium", "large", "full")

        Returns:
            Scale factor as a float (0.0 to 1.0)

        """
        # Get percentage for size preference (default to "large" if invalid)
        percentage = self.SIZE_PERCENTAGES.get(size_preference, 100)

        # Calculate target width based on percentage of page width
        target_width = (self.config.pdf_page_width_px * percentage) / 100

        # If original is smaller than target, don't upscale
        if original_width <= target_width:
            return percentage / 100

        # Calculate scale factor to fit within target width
        scale_factor = target_width / original_width

        return scale_factor

    def calculate_pdf_dimensions(
        self,
        original_width: int,
        original_height: int,
        size_preference: SizePreference = "large",
    ) -> tuple[int, int]:
        """Calculate dimensions for PDF embedding.

        Calculates the optimal dimensions for embedding an image in a PDF
        based on the original dimensions and size preference. Always maintains
        aspect ratio and never exceeds page width.

        Args:
            original_width: Original image width in pixels
            original_height: Original image height in pixels
            size_preference: Desired size ("small", "medium", "large", "full")

        Returns:
            Tuple of (width, height) in pixels for PDF embedding
        """
        if original_width <= 0 or original_height <= 0:
            logger.warning(
                f"Invalid dimensions: {original_width}x{original_height}, using defaults"
            )
            return (self.config.pdf_page_width_px, self.config.pdf_page_width_px)

        # Get percentage for size preference
        percentage = self.SIZE_PERCENTAGES.get(size_preference, 100)

        # Calculate target width based on percentage of page width
        target_width = int((self.config.pdf_page_width_px * percentage) / 100)

        # Calculate aspect ratio
        aspect_ratio = original_width / original_height

        # If original width fits within target, use it (but apply percentage)
        if original_width <= target_width:
            # Apply the percentage scaling
            new_width = int((original_width * percentage) / 100)
            # But don't exceed page width
            new_width = min(new_width, self.config.pdf_page_width_px)
            new_height = int(new_width / aspect_ratio)
        else:
            # Scale down to fit target width
            new_width = target_width
            new_height = int(new_width / aspect_ratio)

        # Ensure we never exceed page width
        if new_width > self.config.pdf_page_width_px:
            new_width = self.config.pdf_page_width_px
            new_height = int(new_width / aspect_ratio)

        logger.debug(
            f"PDF dimensions: {original_width}x{original_height} -> "
            f"{new_width}x{new_height} (size_preference={size_preference})"
        )

        return (new_width, new_height)

    def calculate_page_fit_dimensions(
        self,
        original_width: int,
        original_height: int,
        page_width: int | None = None,
        page_height: int | None = None,
    ) -> tuple[int, int]:
        """Calculate dimensions to fit image within page boundaries.

        Scales the image to fit within both page width AND page height
        while preserving the original aspect ratio. The scaling is based
        on the most constraining dimension.

        Args:
            original_width: Original image width in pixels
            original_height: Original image height in pixels
            page_width: Maximum page width in pixels. If None, uses config default.
            page_height: Maximum page height in pixels. If None, uses config default.

        Returns:
            Tuple of (width, height) in pixels that fits within page boundaries
        """
        if page_width is None:
            page_width = self.config.pdf_page_width_px
        if page_height is None:
            page_height = self.config.pdf_page_height_px

        if original_width <= 0 or original_height <= 0:
            logger.warning(
                f"Invalid dimensions: {original_width}x{original_height}, using page defaults"
            )
            return (page_width, page_height)

        # Calculate aspect ratios
        image_aspect_ratio = original_width / original_height
        page_aspect_ratio = page_width / page_height

        # Determine constraining dimension and calculate fitted dimensions
        constraining = self.get_constraining_dimension(image_aspect_ratio, page_aspect_ratio)

        if constraining == "width":
            # Width is the constraining dimension
            if original_width > page_width:
                new_width = page_width
                new_height = int(new_width / image_aspect_ratio)
            else:
                new_width = original_width
                new_height = original_height
        else:
            # Height is the constraining dimension
            if original_height > page_height:
                new_height = page_height
                new_width = int(new_height * image_aspect_ratio)
            else:
                new_width = original_width
                new_height = original_height

        # Final check: ensure both dimensions fit within page
        if new_width > page_width:
            new_width = page_width
            new_height = int(new_width / image_aspect_ratio)

        if new_height > page_height:
            new_height = page_height
            new_width = int(new_height * image_aspect_ratio)

        logger.debug(
            f"Page fit dimensions: {original_width}x{original_height} -> "
            f"{new_width}x{new_height} (page: {page_width}x{page_height}, "
            f"constraining: {constraining})"
        )

        return (new_width, new_height)

    def get_constraining_dimension(
        self,
        image_aspect_ratio: float,
        page_aspect_ratio: float,
    ) -> Literal["width", "height"]:
        """Determine which dimension constrains scaling.

        Compares the image aspect ratio to the page aspect ratio to determine
        whether width or height will be the limiting factor when fitting
        the image to the page.

        Args:
            image_aspect_ratio: Image width / height ratio
            page_aspect_ratio: Page width / height ratio

        Returns:
            "width" if image is wider than page ratio (constrain by width)
            "height" if image is taller than page ratio (constrain by height)
        """
        if image_aspect_ratio > page_aspect_ratio:
            # Image is wider relative to its height than the page
            # Width will hit the limit first
            return "width"
        else:
            # Image is taller relative to its width than the page
            # Height will hit the limit first
            return "height"

    def should_downsample(self, width: int, height: int) -> bool:
        """Check if image needs downsampling.

        Determines if an image exceeds the maximum dimension threshold
        and should be downsampled before PDF embedding.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            True if either dimension exceeds pdf_max_image_dimension
        """
        return width > self.config.pdf_max_image_dimension or (
            height > self.config.pdf_max_image_dimension
        )

    def downsample_image(
        self,
        image_bytes: bytes,
        target_max_dimension: int | None = None,
    ) -> bytes:
        """Downsample image while maintaining quality.

        Reduces image dimensions while preserving aspect ratio and
        maintaining sufficient resolution for print quality.

        Args:
            image_bytes: Original image as bytes
            target_max_dimension: Maximum dimension for the result.
                                  If None, uses pdf_max_image_dimension.

        Returns:
            Downsampled image as bytes (PNG format)

        Raises:
            ImportError: If PIL is not available
            ValueError: If image_bytes is invalid
        """
        if not PIL_AVAILABLE:
            raise ImportError(
                "PIL/Pillow is required for image downsampling. " "Install with: uv add pillow"
            )

        if target_max_dimension is None:
            target_max_dimension = self.config.pdf_max_image_dimension

        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            original_width, original_height = image.size

            logger.info(f"Downsampling image: original size {original_width}x{original_height}")

            # Check if downsampling is actually needed
            if not self.should_downsample(original_width, original_height):
                logger.debug("Image does not need downsampling")
                return image_bytes

            # Calculate new dimensions maintaining aspect ratio
            aspect_ratio = original_width / original_height

            if original_width >= original_height:
                # Width is the limiting dimension
                new_width = target_max_dimension
                new_height = int(new_width / aspect_ratio)
            else:
                # Height is the limiting dimension
                new_height = target_max_dimension
                new_width = int(new_height * aspect_ratio)

            # Ensure minimum DPI equivalent (Requirement 7.2)
            # At 150 DPI, a standard A4 page (8.27" wide) needs ~1240px width
            min_width_for_dpi = int(8.27 * self.config.pdf_min_dpi)
            if new_width < min_width_for_dpi and original_width >= min_width_for_dpi:
                # Don't downsample below minimum DPI threshold
                new_width = min_width_for_dpi
                new_height = int(new_width / aspect_ratio)

            # Perform the resize using high-quality resampling
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to bytes (PNG for lossless quality)
            output_buffer = io.BytesIO()

            # Handle different image modes
            if resized_image.mode in ("RGBA", "LA", "P"):
                # Keep alpha channel for PNG
                resized_image.save(output_buffer, format="PNG", optimize=True)
            else:
                # Convert to RGB for JPEG compatibility, but save as PNG
                if resized_image.mode != "RGB":
                    resized_image = resized_image.convert("RGB")
                resized_image.save(output_buffer, format="PNG", optimize=True)

            result_bytes = output_buffer.getvalue()

            # Log the results (Requirement 7.3)
            logger.info(
                f"Downsampled image: {original_width}x{original_height} -> "
                f"{new_width}x{new_height} "
                f"({len(image_bytes)} bytes -> {len(result_bytes)} bytes)"
            )

            return result_bytes

        except Exception as e:
            logger.error(f"Failed to downsample image: {e}")
            raise ValueError(f"Failed to downsample image: {e}") from e


__all__ = ["PDFImageScaler", "SizePreference"]
