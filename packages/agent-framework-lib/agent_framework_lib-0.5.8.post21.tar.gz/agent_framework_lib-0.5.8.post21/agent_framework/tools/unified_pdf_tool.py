"""
Unified PDF generation tool from HTML content.

This module provides a single unified tool for generating PDF documents from HTML,
replacing the three existing tools (CreatePDFFromMarkdownTool, CreatePDFFromHTMLTool,
CreatePDFWithImagesTool) to ensure consistent visual rendering across all PDFs.
"""

import base64
import logging
import re
from collections.abc import Callable
from typing import Literal

from .adaptive_pdf_css import AdaptivePDFCSS
from .base import AgentTool, ToolDependencyError
from .html_content_analyzer import HTMLContentAnalyzer, PageConfig
from .pdf_image_scaler import PDFImageScaler
from .pdf_tools import TEMPLATE_STYLES
from .sizing_config import ImageSizingConfig


# Optional dependencies - will be checked at runtime
try:
    from weasyprint import HTML  # noqa: F401

    WEASYPRINT_AVAILABLE = True
    WEASYPRINT_ERROR = None
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(e)

# Optional PIL for image processing
try:
    import io

    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type aliases
TemplateStyle = Literal["professional", "minimal", "modern"]
SizePreference = Literal["small", "medium", "large", "full"]

# Valid values for validation
VALID_TEMPLATE_STYLES: set[str] = {"professional", "minimal", "modern"}
VALID_SIZE_PREFERENCES: set[str] = {"small", "medium", "large", "full"}

# Default values
DEFAULT_TEMPLATE_STYLE: TemplateStyle = "professional"
DEFAULT_SIZE_PREFERENCE: SizePreference = "large"


class CreateUnifiedPDFTool(AgentTool):
    """Unified tool for creating PDF documents from HTML content.

    This tool provides a single, consistent pipeline for PDF generation,
    supporting:
    - Multiple template styles (professional, minimal, modern)
    - Automatic image embedding from file storage via file_id:UUID syntax
    - Adaptive image sizing with size preferences (small, medium, large, full)
    - Automatic downsampling of large images (>4000px)
    - Consistent CSS rendering across all generated PDFs

    Example:
        tool = CreateUnifiedPDFTool()
        tool.set_context(file_storage=storage, user_id="user123", session_id="session456")
        create_pdf = tool.get_tool_function()
        result = await create_pdf(
            title="My Report",
            html_content="<h1>Report</h1><p>Content here...</p>",
            template_style="professional",
            image_size="large"
        )
    """

    def __init__(self, config: ImageSizingConfig | None = None):
        """Initialize the tool with optional custom configuration.

        Args:
            config: Custom sizing configuration for image processing.
                   If None, uses default ImageSizingConfig.
        """
        super().__init__()
        self.config = config or ImageSizingConfig()
        self.image_scaler = PDFImageScaler(self.config)
        self.css_generator = AdaptivePDFCSS(self.config)
        self.html_analyzer = HTMLContentAnalyzer(
            PageConfig(
                page_height_px=self.config.pdf_page_height_px,
                page_width_px=self.config.pdf_page_width_px,
                min_image_height_px=self.config.min_readable_height,
            )
        )

    def _validate_template_style(self, template_style: str) -> TemplateStyle:
        """Validate and normalize template style.

        Args:
            template_style: The template style to validate.

        Returns:
            Valid template style, defaults to "professional" if invalid.
        """
        if template_style in VALID_TEMPLATE_STYLES:
            return template_style  # type: ignore[return-value]
        logger.warning(
            f"Invalid template style '{template_style}', using default '{DEFAULT_TEMPLATE_STYLE}'"
        )
        return DEFAULT_TEMPLATE_STYLE

    def _validate_size_preference(self, image_size: str) -> SizePreference:
        """Validate and normalize size preference.

        Args:
            image_size: The size preference to validate.

        Returns:
            Valid size preference, defaults to "large" if invalid.
        """
        if image_size in VALID_SIZE_PREFERENCES:
            return image_size  # type: ignore[return-value]
        logger.warning(
            f"Invalid size preference '{image_size}', using default '{DEFAULT_SIZE_PREFERENCE}'"
        )
        return DEFAULT_SIZE_PREFERENCE

    def get_tool_function(self) -> Callable:
        """Return the PDF creation function.

        Returns:
            Async callable function for creating PDFs from HTML content.
        """

        async def create_pdf(
            title: str,
            html_content: str,
            template_style: str = "professional",
            image_size: str = "large",
            author: str | None = None,
        ) -> str:
            """
            Create a PDF document from HTML content.

            Args:
                title: Document title (used for filename and header)
                html_content: HTML content (fragment or complete document)
                template_style: Style template ("professional", "minimal", "modern")
                image_size: Image sizing preference ("small", "medium", "large", "full")
                author: Optional author name

            Returns:
                Success message with download link, or error message
            """
            self._ensure_initialized()

            # Validate inputs - empty title
            if not title or not title.strip():
                return "Error: Title cannot be empty"

            # Validate inputs - empty content
            if not html_content or not html_content.strip():
                return "Error: HTML content cannot be empty"

            # Validate and normalize template style (defaults to "professional" if invalid)
            validated_style = self._validate_template_style(template_style)

            # Validate and normalize size preference (defaults to "large" if invalid)
            validated_size = self._validate_size_preference(image_size)

            # Process images (to be implemented in task 1.3)
            processed_html = await self._process_images(html_content, validated_size)

            # Wrap HTML fragment if needed (to be implemented in task 1.4)
            final_html = self._wrap_html_fragment(
                processed_html, title, validated_style, validated_size, author
            )

            # Generate and store PDF (to be implemented in task 1.5)
            return await self._generate_and_store_pdf(final_html, title)

        return create_pdf

    async def _process_images(
        self, html_content: str, image_size: SizePreference  # noqa: ARG002
    ) -> str:
        """Process file_id references and embed images as Data URIs.

        Args:
            html_content: HTML content with potential file_id:UUID references.
            image_size: Size preference for image scaling (used for CSS class selection).

        Returns:
            HTML content with images embedded as Data URIs.

        Raises:
            ValueError: If a file_id reference cannot be found in storage.
        """
        # Pattern to detect file_id:UUID references in img src attributes
        file_id_pattern = r'src="file_id:([a-f0-9\-]+)"'
        matches = re.findall(file_id_pattern, html_content)

        if not matches:
            return html_content

        logger.info(f"Found {len(matches)} file_id references in HTML")

        # Analyze HTML to calculate available space for each image
        image_placements = self.html_analyzer.analyze_html(html_content)
        logger.info(f"Analyzed {len(image_placements)} image placements")

        processed_html = html_content

        # Check file storage availability before processing images
        if not self.file_storage:
            raise ToolDependencyError(
                "File storage is required for image embedding but was not provided. "
                "Ensure file_storage is set via set_context()."
            )

        for file_id in matches:
            try:
                logger.info(f"Retrieving file {file_id} for embedding")

                # Retrieve file content and metadata from FileStorage
                content, metadata = await self.file_storage.retrieve_file(file_id)

                # Read dimension metadata if available
                original_width = None
                original_height = None
                if hasattr(metadata, "extra") and metadata.extra:
                    original_width = metadata.extra.get("width_px")
                    original_height = metadata.extra.get("height_px")
                    content_type = metadata.extra.get("content_type", "unknown")
                    logger.info(
                        f"Image metadata: {original_width}x{original_height}, type={content_type}"
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
                processed_content, fitted_width, fitted_height = self._process_image_for_pdf(
                    content, original_width, original_height, target_height
                )

                # Encode as base64
                base64_content = base64.b64encode(processed_content).decode("utf-8")

                # Get MIME type
                mime_type = metadata.mime_type or "application/octet-stream"

                # Create data URI
                data_uri = f"data:{mime_type};base64,{base64_content}"

                # Determine CSS class based on image height
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

            except FileNotFoundError:
                error_msg = f"Error: Image file_id '{file_id}' not found in storage"
                logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"Error: Failed to embed image {file_id}: {str(e)}"
                logger.error(error_msg)
                return error_msg

        return processed_html

    def _process_image_for_pdf(
        self,
        image_bytes: bytes,
        original_width: int | None,
        original_height: int | None,
        target_height: int | None = None,
    ) -> tuple[bytes, int, int]:
        """Process image for PDF embedding, resizing to fit available space.

        Args:
            image_bytes: Original image bytes.
            original_width: Original width from metadata (optional).
            original_height: Original height from metadata (optional).
            target_height: Target height to resize to (from HTML analysis).

        Returns:
            Tuple of (processed image bytes, fitted width, fitted height).
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

            # Check if downsampling is needed (very large images > 4000px)
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

    def _wrap_html_fragment(
        self,
        content: str,
        title: str,
        template_style: TemplateStyle,
        image_size: SizePreference,
        author: str | None = None,
    ) -> str:
        """Wrap HTML fragment in a complete document with template styling.

        If the content is already a complete HTML document (has DOCTYPE or html tag),
        the CSS is injected into the existing document. Otherwise, the fragment is
        wrapped in a complete HTML document structure.

        The CSS is composed of:
        1. Template style CSS from TEMPLATE_STYLES (professional, minimal, modern)
        2. Adaptive image CSS from AdaptivePDFCSS for proper image sizing

        Args:
            content: HTML content (fragment or complete document).
            title: Document title.
            template_style: Style template to apply.
            image_size: Size preference for CSS generation.
            author: Optional author name.

        Returns:
            Complete HTML document with styling.
        """
        # Get template CSS from TEMPLATE_STYLES
        template_css = TEMPLATE_STYLES.get(template_style, TEMPLATE_STYLES["professional"])

        # Generate adaptive CSS for images
        adaptive_css = self.css_generator.generate_complete_css(
            size_preference=image_size,
            vertical_margin_px=20,
            include_base_styles=False,  # Template already has base styles
            enable_page_breaks=True,
        )

        # Merge template CSS with adaptive CSS
        combined_css = f"{template_css}\n\n/* Adaptive image CSS */\n{adaptive_css}"

        # Check if content is a complete HTML document
        if self._is_complete_html(content):
            # Inject CSS into existing document
            return self._inject_css_into_html(content, combined_css)
        else:
            # Wrap fragment in complete HTML document
            return self._create_html_document(content, title, combined_css, author)

    def _inject_css_into_html(self, html_content: str, css: str) -> str:
        """Inject CSS into an existing HTML document.

        Attempts to inject CSS before </head>. If no </head> is found,
        prepends a style tag to the content.

        Args:
            html_content: Complete HTML document.
            css: CSS to inject.

        Returns:
            HTML document with injected CSS.
        """
        css_tag = f"<style>\n{css}\n</style>"

        # Try to inject before </head>
        head_close_pattern = re.compile(r"</head>", re.IGNORECASE)
        if head_close_pattern.search(html_content):
            return head_close_pattern.sub(f"{css_tag}\n</head>", html_content, count=1)

        # If no </head>, try to inject after <head>
        head_open_pattern = re.compile(r"<head[^>]*>", re.IGNORECASE)
        if head_open_pattern.search(html_content):
            return head_open_pattern.sub(
                lambda m: f"{m.group(0)}\n{css_tag}", html_content, count=1
            )

        # Fallback: prepend style tag
        return f"{css_tag}\n{html_content}"

    def _create_html_document(
        self,
        content: str,
        title: str,
        css: str,
        author: str | None = None,
    ) -> str:
        """Create a complete HTML document from a fragment.

        Args:
            content: HTML fragment content.
            title: Document title.
            css: CSS styles to include.
            author: Optional author name for meta tag.

        Returns:
            Complete HTML document.
        """
        # Build meta tags
        meta_tags = '<meta charset="UTF-8">'
        if author:
            meta_tags += f'\n    <meta name="author" content="{author}">'

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    {meta_tags}
    <title>{title}</title>
    <style>
{css}
    </style>
</head>
<body>
    {content}
</body>
</html>"""

        return html_template

    def _is_complete_html(self, content: str) -> bool:
        """Detect if content is a complete HTML document.

        Args:
            content: HTML content to check.

        Returns:
            True if content has DOCTYPE or html tag, False otherwise.
        """
        content_lower = content.strip().lower()
        return content_lower.startswith("<!doctype") or content_lower.startswith("<html")

    async def _generate_and_store_pdf(self, html_content: str, title: str) -> str:
        """Generate PDF from HTML and store in file storage.

        Args:
            html_content: Complete HTML document.
            title: Document title for filename.

        Returns:
            Success message with download link, or error message.

        Raises:
            ToolDependencyError: If file storage is not available.
        """
        # Check for WeasyPrint availability
        if not WEASYPRINT_AVAILABLE:
            error_msg = "Error: WeasyPrint is not available. "
            if WEASYPRINT_ERROR and "libgobject" in WEASYPRINT_ERROR:
                error_msg += "System dependencies are missing. Install them with:\n"
                error_msg += '  macOS: brew install pango gdk-pixbuf libffi && export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"\n'
                error_msg += "  Ubuntu/Debian: sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev\n"
                error_msg += "  Fedora/RHEL: sudo dnf install pango gdk-pixbuf2 libffi-devel"
            else:
                error_msg += "Install with: uv add weasyprint"
            return error_msg

        # Check file storage availability
        if not self.file_storage:
            raise ToolDependencyError(
                "File storage is required for PDF creation but was not provided. "
                "Ensure file_storage is set via set_context()."
            )

        try:
            # Generate PDF using WeasyPrint
            pdf_bytes = HTML(string=html_content).write_pdf()

            # Create safe filename from title
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
            safe_title = safe_title.replace(" ", "_")
            filename = f"{safe_title}.pdf"

            # Prepare tags for storage
            tags = ["pdf", "generated", "unified-pdf-tool"]

            # Store PDF in file storage
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
            if hasattr(self.file_storage, "get_download_url"):
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
                f"Created unified PDF: {filename} (file_id: {file_id}, download URL: {download_url})"
            )
            return f"PDF created successfully!\n\nDownload link: [{filename}]({download_url})"

        except Exception as e:
            error_msg = f"Failed to create PDF: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Error creating PDF: {str(e)}"


__all__ = ["CreateUnifiedPDFTool"]
