"""
PDF generation tool with automatic image embedding from file storage.

This tool extends the PDF generation capabilities to automatically embed
images from file storage using file IDs, with adaptive sizing support
for optimal PDF rendering.
"""

import logging
import base64
import re
from typing import Callable, Literal, Optional

from .base import AgentTool, ToolDependencyError
from .pdf_image_scaler import PDFImageScaler
from .adaptive_pdf_css import AdaptivePDFCSS
from .sizing_config import ImageSizingConfig
from .html_content_analyzer import HTMLContentAnalyzer, PageConfig

# Optional dependencies
try:
    from weasyprint import HTML

    WEASYPRINT_AVAILABLE = True
    WEASYPRINT_ERROR = None
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(e)

# Optional PIL for image processing
try:
    from PIL import Image
    import io

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type alias for size preferences
SizePreference = Literal["small", "medium", "large", "full"]


class CreatePDFWithImagesTool(AgentTool):
    """Tool for creating PDF documents from HTML with automatic image embedding.

    This tool supports adaptive image sizing with the following features:
    - Size preferences (small=50%, medium=75%, large/full=100% of page width)
    - Automatic downsampling of large images (>4000px)
    - Centered images with consistent vertical spacing
    - Dimension metadata reading from stored images
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the tool with optional custom configuration.

        Args:
            config: Custom sizing configuration. If None, uses defaults.
        """
        super().__init__()
        self.config = config or ImageSizingConfig()
        self.image_scaler = PDFImageScaler(self.config)
        self.css_generator = AdaptivePDFCSS(self.config)
        self.html_analyzer = HTMLContentAnalyzer(PageConfig(
            page_height_px=self.config.pdf_page_height_px,
            page_width_px=self.config.pdf_page_width_px,
            min_image_height_px=self.config.min_readable_height,
        ))

    def get_tool_function(self) -> Callable:
        """Return the PDF creation function with image support."""

        async def create_pdf_with_images(
            title: str,
            html_content: str,
            author: Optional[str] = None,
            image_size: SizePreference = "large",
        ) -> str:
            """
            Create a PDF document from HTML content with automatic image embedding.

            This tool automatically detects file_id references in img tags and
            replaces them with embedded data URIs. Images are adaptively sized
            based on the image_size parameter.

            Args:
                title: Document title
                html_content: HTML content with special img tags using file_id
                             Format: <img src="file_id:YOUR_FILE_ID" alt="...">
                author: Optional author name
                image_size: Image sizing preference:
                           - "small": 50% of page width (compact reports)
                           - "medium": 75% of page width (balanced, recommended)
                           - "large": 100% of page width (default)
                           - "full": 100% of page width

            Returns:
                Success message with file_id

            LAYOUT GOAL: Create beautiful, readable PDFs that fill pages efficiently.

            CRITICAL RULES:
                1. ALWAYS wrap images in <figure> tags to keep image + caption together
                2. Page breaks ONLY for major sections (1., 2., 3.) - NEVER for images
                3. Images auto-resize to max 70% page height (fits with title + text)

            CORRECT HTML STRUCTURE:
                <div class="section break-before">
                    <h2>1. Section Title</h2>
                    <p>Brief intro text (2-3 lines max before image)...</p>
                    <figure>
                        <img src="file_id:xxx" alt="Description">
                        <figcaption>Figure 1: Caption here</figcaption>
                    </figure>
                </div>

                <div class="section break-before">
                    <h2>2. Next Section</h2>
                    <p>Intro...</p>
                    <figure>
                        <img src="file_id:yyy" alt="Description">
                        <figcaption>Figure 2: Caption</figcaption>
                    </figure>
                </div>

            WHY <figure> IS REQUIRED:
                - Keeps image and caption together on same page (never separated)
                - Image resizes to fit available space
                - Professional appearance with centered caption

            CSS CLASSES:
                - break-before: New page (ONLY for major sections 1., 2., 3.)
                - section: Groups content together

            TIPS:
                - Keep intro text SHORT (2-3 lines) before each image
                - One main image per section works best
                - Use image_size="medium" for multiple images per page
            """
            self._ensure_initialized()

            # Check for required dependencies
            if not WEASYPRINT_AVAILABLE:
                error_msg = "Error: WeasyPrint is not available. "
                if WEASYPRINT_ERROR and "libgobject" in WEASYPRINT_ERROR:
                    error_msg += "System dependencies are missing. Install them with:\n"
                    error_msg += "  macOS: brew install pango gdk-pixbuf libffi\n"
                    error_msg += (
                        "  Ubuntu/Debian: sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0\n"
                    )
                else:
                    error_msg += "Install with: uv add weasyprint"
                return error_msg

            # Validate inputs
            if not title or not title.strip():
                return "Error: Title cannot be empty"

            if not html_content or not html_content.strip():
                return "Error: HTML content cannot be empty"

            # Validate image_size parameter (Requirement 6.4 - default to "large")
            valid_sizes = ("small", "medium", "large", "full")
            if image_size not in valid_sizes:
                logger.warning(f"Invalid image_size '{image_size}', defaulting to 'large'")
                image_size = "large"

            # Check file storage availability
            if not self.file_storage:
                raise ToolDependencyError(
                    "File storage is required but was not provided. "
                    "Ensure file_storage is set via set_context()."
                )

            try:
                # Find all file_id references in img tags
                # Pattern: <img src="file_id:SOME-UUID" ...>
                file_id_pattern = r'src="file_id:([a-f0-9\-]+)"'
                matches = re.findall(file_id_pattern, html_content)

                logger.info(f"Found {len(matches)} file_id references in HTML")

                # Analyze HTML to calculate available space for each image
                image_placements = self.html_analyzer.analyze_html(html_content)
                logger.info(f"Analyzed {len(image_placements)} image placements")

                # Replace each file_id with actual data URI
                processed_html = html_content
                image_dimensions: dict[str, tuple[int, int]] = {}

                for file_id in matches:
                    try:
                        logger.info(f"Retrieving file {file_id} for embedding")

                        # Retrieve file content and metadata
                        content, metadata = await self.file_storage.retrieve_file(file_id)

                        # Read dimension metadata if available (Requirement 8.3)
                        original_width = None
                        original_height = None
                        if hasattr(metadata, "extra") and metadata.extra:
                            original_width = metadata.extra.get("width_px")
                            original_height = metadata.extra.get("height_px")
                            content_type = metadata.extra.get("content_type", "unknown")
                            logger.info(
                                f"Image metadata: {original_width}x{original_height}, "
                                f"type={content_type}"
                            )

                        # Get target height from HTML analysis (available space)
                        target_height = None
                        if file_id in image_placements:
                            placement = image_placements[file_id]
                            if placement.should_resize and placement.target_height_px:
                                target_height = placement.target_height_px
                                logger.info(
                                    f"Image {file_id}: available space = {placement.available_height_px}px, "
                                    f"target height = {target_height}px"
                                )

                        # Process image: downsample and resize to fit available space
                        processed_content, fitted_width, fitted_height = (
                            self._process_image_for_pdf(
                                content, original_width, original_height, target_height
                            )
                        )

                        # Store dimensions for CSS generation
                        image_dimensions[file_id] = (fitted_width, fitted_height)

                        # Encode as base64
                        base64_content = base64.b64encode(processed_content).decode("utf-8")

                        # Get MIME type
                        mime_type = metadata.mime_type or "application/octet-stream"

                        # Create data URI
                        data_uri = f"data:{mime_type};base64,{base64_content}"

                        # Determine CSS class based on image height (Requirements 9.1, 9.2)
                        css_class = self.css_generator.get_image_css_class(fitted_height)

                        # Replace in HTML with appropriate CSS class
                        old_src = f'src="file_id:{file_id}"'
                        if css_class:
                            new_src = f'class="{css_class}" src="{data_uri}"'
                        else:
                            new_src = f'src="{data_uri}"'
                        processed_html = processed_html.replace(old_src, new_src)

                        logger.info(
                            f"Embedded file {file_id} ({metadata.filename}, "
                            f"{len(base64_content)} base64 chars, "
                            f"fitted: {fitted_width}x{fitted_height}, class: {css_class or 'none'})"
                        )

                    except Exception as e:
                        logger.error(f"Failed to embed file {file_id}: {e}")
                        return f"Error: Failed to embed image {file_id}: {str(e)}"

                # Wrap in complete HTML document if needed
                if not processed_html.strip().upper().startswith("<!DOCTYPE"):
                    # Generate adaptive CSS with page fitting
                    # Images can take up to 90% of page height
                    # WeasyPrint handles page breaks automatically
                    adaptive_css = self.css_generator.generate_complete_css(
                        size_preference=image_size,
                        vertical_margin_px=20,
                        include_base_styles=True,
                        enable_page_breaks=True,
                        # max_height_px=None uses default 90% of page height
                    )

                    # Add additional base styles
                    additional_css = """
                        code {
                            background-color: #f5f5f5;
                            padding: 2pt 4pt;
                            border-radius: 3pt;
                        }
                        table {
                            border-collapse: collapse;
                            width: 100%;
                            margin: 12pt 0;
                        }
                        th, td {
                            border: 1pt solid #ddd;
                            padding: 8pt;
                            text-align: left;
                        }
                    """

                    processed_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
{adaptive_css}
{additional_css}
    </style>
</head>
<body>
    {processed_html}
</body>
</html>"""

                # Generate PDF
                pdf_bytes = HTML(string=processed_html).write_pdf()

                # Create filename
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_title = safe_title.replace(" ", "_")
                filename = f"{safe_title}.pdf"

                # Store PDF
                tags = ["pdf", "generated", "html", "with-images"]
                if author:
                    tags.append(f"author:{author}")
                if matches:
                    tags.append(f"embedded-images:{len(matches)}")
                tags.append(f"image-size:{image_size}")

                file_id = await self.file_storage.store_file(
                    content=pdf_bytes,
                    filename=filename,
                    user_id=self.current_user_id,
                    session_id=self.current_session_id,
                    mime_type="application/pdf",
                    tags=tags,
                    is_generated=True,
                )

                # Get download URL based on storage backend's URL mode configuration
                # For S3/MinIO, this respects S3_URL_MODE (api, presigned, public)
                if hasattr(self.file_storage, 'get_download_url'):
                    try:
                        download_url = await self.file_storage.get_download_url(file_id)
                    except Exception as url_error:
                        logger.warning(
                            f"Failed to get download URL from storage backend: {url_error}, "
                            "falling back to API URL"
                        )
                        download_url = f"/files/{file_id}/download"
                else:
                    download_url = f"/files/{file_id}/download"

                logger.info(
                    f"Created PDF with {len(matches)} embedded images: "
                    f"{filename} (file_id: {file_id}, image_size: {image_size}, download URL: {download_url})"
                )
                return (
                    f"PDF created successfully with {len(matches)} embedded image(s)!\n\n"
                    f"Download link: [{filename}]({download_url})"
                )

            except Exception as e:
                error_msg = f"Failed to create PDF: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return f"Error creating PDF: {str(e)}"

        return create_pdf_with_images

    def _process_image_for_pdf(
        self,
        image_bytes: bytes,
        original_width: int | None,
        original_height: int | None,
        target_height: int | None = None,
    ) -> tuple[bytes, int, int]:
        """Process image for PDF embedding, resizing to fit available space.

        Args:
            image_bytes: Original image bytes
            original_width: Original width from metadata (optional)
            original_height: Original height from metadata (optional)
            target_height: Target height to resize to (from HTML analysis)

        Returns:
            Tuple of (processed image bytes, fitted width, fitted height)
        """
        if not PIL_AVAILABLE:
            logger.debug("PIL not available, skipping image processing")
            width = original_width or self.config.pdf_page_width_px
            height = original_height or self.config.pdf_page_height_px
            return image_bytes, width, height

        try:
            # Get actual dimensions from image
            img = Image.open(io.BytesIO(image_bytes))
            actual_width, actual_height = img.size

            # Use metadata dimensions if available, otherwise use actual
            width = original_width or actual_width
            height = original_height or actual_height

            logger.info(f"Processing image for PDF: {width}x{height}")

            processed_bytes = image_bytes

            # Check if downsampling is needed (very large images)
            if self.image_scaler.should_downsample(width, height):
                logger.info(
                    f"Image exceeds {self.config.pdf_max_image_dimension}px, downsampling..."
                )
                processed_bytes = self.image_scaler.downsample_image(
                    image_bytes, self.config.pdf_max_image_dimension
                )
                img = Image.open(io.BytesIO(processed_bytes))
                width, height = img.size

            # If we have a target height and image is taller, resize to fit
            if target_height and height > target_height:
                # Calculate new dimensions preserving aspect ratio
                scale = target_height / height
                new_width = int(width * scale)
                new_height = target_height

                logger.info(
                    f"Resizing image to fit available space: "
                    f"{width}x{height} -> {new_width}x{new_height}"
                )

                # Resize the image
                img = Image.open(io.BytesIO(processed_bytes))
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Save to bytes
                output = io.BytesIO()
                img_format = img.format or "PNG"
                img_resized.save(output, format=img_format)
                processed_bytes = output.getvalue()

                width, height = new_width, new_height

            # Calculate final page fit dimensions
            fitted_width, fitted_height = self.image_scaler.calculate_page_fit_dimensions(
                width,
                height,
                self.config.pdf_page_width_px,
                self.config.pdf_page_height_px,
            )

            logger.info(
                f"Final dimensions: {width}x{height} -> fitted: {fitted_width}x{fitted_height}"
            )

            return processed_bytes, fitted_width, fitted_height

        except Exception as e:
            logger.warning(f"Failed to process image, using original: {e}")
            width = original_width or self.config.pdf_page_width_px
            height = original_height or self.config.pdf_page_height_px
            return image_bytes, width, height

    def _should_force_page_break(self, image_height: int) -> bool:
        """Determine if an image should force a page break.

        An image should force a page break if it's tall enough that it
        would likely not fit on the current page but would fit on a new page.

        Args:
            image_height: Height of the image in pixels

        Returns:
            True if the image should force a page break
        """
        # Force page break for images taller than 70% of page height
        threshold = int(self.config.pdf_page_height_px * 0.7)
        return image_height > threshold


__all__ = ["CreatePDFWithImagesTool"]
