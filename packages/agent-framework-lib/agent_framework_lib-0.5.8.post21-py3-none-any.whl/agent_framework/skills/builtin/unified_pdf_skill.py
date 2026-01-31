"""
Unified PDF Skill - Single PDF document generation capability.

This skill provides a unified approach to creating PDF documents from HTML content,
replacing the separate pdf_skill and pdf_with_images_skill. It wraps the
CreateUnifiedPDFTool with comprehensive instructions for proper usage.
"""

from ...tools import PDF_TOOLS_AVAILABLE
from ..base import Skill, SkillCategory, SkillMetadata


# Conditionally import the unified PDF tool
if PDF_TOOLS_AVAILABLE:
    from ...tools.unified_pdf_tool import CreateUnifiedPDFTool


UNIFIED_PDF_INSTRUCTIONS = """
## Unified PDF Generation Instructions

You can create professional PDF documents from HTML content with automatic image embedding.
This is the single, unified tool for all PDF generation needs.

### Available Tool

**create_pdf** - Create PDF from HTML content with optional image embedding

### Parameters

- `title`: Document title (used for filename and header)
- `html_content`: HTML content (fragment or complete document)
- `template_style`: Style template - "professional", "minimal", or "modern" (default: "professional")
- `image_size`: Image sizing preference - "small", "medium", "large", or "full" (default: "large")
- `author`: Optional author name

### Template Styles

1. **professional** (default)
   - Blue color scheme with serif fonts
   - Page numbers and document title in header
   - Elegant borders and styling
   - Best for: Business reports, formal documents

2. **minimal**
   - Black and white, clean design
   - Sans-serif fonts
   - Simple borders
   - Best for: Technical documentation, simple reports

3. **modern**
   - Gradient colors (purple/blue)
   - Contemporary sans-serif fonts
   - Rounded corners, modern aesthetics
   - Best for: Marketing materials, presentations

### Image Size Preferences

| Size | Width | Best For |
|------|-------|----------|
| small | 50% | Multiple images per page, thumbnails |
| medium | 75% | Balanced reports, mixed content |
| large | 100% | Single chart per section, detailed visuals (default) |
| full | 100% | Same as large |

### Embedding Images with file_id Syntax

Images stored in file storage can be embedded using the special `file_id:UUID` syntax:

```html
<img src="file_id:abc-123-def-456" alt="Description">
```

The tool automatically:
1. Retrieves the image from file storage using the UUID
2. Converts it to a data URI (base64 encoded)
3. Embeds it directly in the PDF
4. Applies adaptive sizing based on your preference
5. Downsamples images larger than 4000px to optimize PDF size

### Recommended HTML Structure

**ALWAYS wrap images in `<figure>` tags** to keep image and caption together:

```html
<div class="section">
    <h1>Report Title</h1>
    <p>Introduction paragraph...</p>
</div>

<div class="section break-before">
    <h2>1. First Section</h2>
    <p>Brief intro text (2-3 lines max before image)...</p>
    <figure>
        <img src="file_id:xxx-xxx-xxx" alt="Description">
        <figcaption>Figure 1: Caption here</figcaption>
    </figure>
</div>

<div class="section break-before">
    <h2>2. Second Section</h2>
    <p>Content for second section...</p>
    <figure>
        <img src="file_id:yyy-yyy-yyy" alt="Description">
        <figcaption>Figure 2: Another caption</figcaption>
    </figure>
</div>
```

### Why `<figure>` is Required

- Keeps image and caption together on the same page (never separated)
- Image resizes to fit available space automatically
- Professional appearance with centered caption

### CSS Classes

- `break-before`: Forces a new page (use ONLY for major sections 1., 2., 3.)
- `section`: Groups content together

### Complete Example

```python
result = await create_pdf(
    title="Quarterly Sales Report",
    html_content=\"\"\"
<div class="section">
    <h1>Quarterly Sales Report Q4 2024</h1>
    <p>This report presents the quarterly sales analysis with visualizations.</p>
</div>

<div class="section break-before">
    <h2>1. Revenue Overview</h2>
    <p>The following chart shows monthly revenue trends for Q4 2024.</p>
    <figure>
        <img src="file_id:abc-123-chart" alt="Revenue Chart">
        <figcaption>Figure 1: Monthly Revenue Trends Q4 2024</figcaption>
    </figure>
</div>

<div class="section break-before">
    <h2>2. Regional Performance</h2>
    <p>Regional breakdown of sales performance across all territories.</p>
    <figure>
        <img src="file_id:def-456-chart" alt="Regional Sales">
        <figcaption>Figure 2: Sales by Region</figcaption>
    </figure>
    <table>
        <tr><th>Region</th><th>Sales</th><th>Growth</th></tr>
        <tr><td>North</td><td>$450K</td><td>+12%</td></tr>
        <tr><td>South</td><td>$380K</td><td>+8%</td></tr>
        <tr><td>East</td><td>$520K</td><td>+15%</td></tr>
        <tr><td>West</td><td>$410K</td><td>+10%</td></tr>
    </table>
</div>

<div class="section break-before">
    <h2>3. Conclusions</h2>
    <p>Key findings and recommendations based on the analysis.</p>
    <ul>
        <li>Revenue increased 15% quarter-over-quarter</li>
        <li>Eastern region showed strongest growth</li>
        <li>Recommend expanding marketing in Southern region</li>
    </ul>
</div>
\"\"\",
    author="Analytics Team",
    template_style="professional",
    image_size="large"
)
```

### Simple Example (No Images)

```python
result = await create_pdf(
    title="Meeting Notes",
    html_content=\"\"\"
<h1>Team Meeting Notes</h1>
<p><strong>Date:</strong> January 15, 2025</p>
<p><strong>Attendees:</strong> Alice, Bob, Charlie</p>

<h2>Agenda Items</h2>
<ol>
    <li>Project status update</li>
    <li>Budget review</li>
    <li>Next steps</li>
</ol>

<h2>Action Items</h2>
<table>
    <tr><th>Task</th><th>Owner</th><th>Due Date</th></tr>
    <tr><td>Complete design review</td><td>Alice</td><td>Jan 20</td></tr>
    <tr><td>Update budget forecast</td><td>Bob</td><td>Jan 22</td></tr>
</table>
\"\"\",
    template_style="minimal"
)
```

### Workflow: Creating Reports with Charts

1. **Generate charts first** using the chart skill:
   ```python
   # Create a chart and get its file_id
   chart_result = await save_chart_as_image(chart_config, "revenue_chart")
   # Returns file_id like "abc-123-def-456"
   ```

2. **Create the PDF with embedded charts:**
   ```python
   await create_pdf(
       title="Report",
       html_content='<figure><img src="file_id:abc-123-def-456" alt="Chart"><figcaption>Figure 1</figcaption></figure>',
       image_size="large"
   )
   ```

### HTML Features Supported

- Headers (h1, h2, h3, etc.)
- Paragraphs and text formatting (strong, em, u)
- Lists (ordered and unordered)
- Tables with headers
- Images (via file_id syntax or data URIs)
- Figures with captions
- Blockquotes
- Code blocks (pre, code)
- Custom CSS classes

### Page Layout Notes

- Default page size is A4
- Margins are automatically set by the template
- Page numbers are included automatically (professional and modern styles)
- Long content will span multiple pages
- Tables and code blocks handle page breaks gracefully
- Images are automatically sized to fit available space

### Supported Image Formats

- PNG (recommended for charts and diagrams)
- JPEG (good for photos)
- GIF
- WebP

### Error Handling

- Empty title or content will return a descriptive error
- Invalid template_style defaults to "professional"
- Invalid image_size defaults to "large"
- Invalid file_id will return an error with the specific ID
- Missing images will prevent PDF generation
- Large images (>4000px) are automatically downsampled for optimal PDF size
- System dependency errors will provide installation instructions

### Best Practices

1. **Use HTML structure** - Organize content with sections and headers
2. **One main image per section** works best for readability
3. **Keep intro text short** (2-3 lines) before each image
4. **Use `break-before`** only for major numbered sections
5. **Always include `<figcaption>`** for professional appearance
6. **Use `image_size="medium"`** when you have multiple images per page
7. **Test with professional template first** - It works well for most use cases
"""


def create_unified_pdf_skill() -> Skill:
    """
    Create the unified PDF generation skill.

    This skill replaces both pdf_skill and pdf_with_images_skill,
    providing a single, consistent approach to PDF generation.

    Returns:
        Skill instance for unified PDF generation

    Note:
        If PDF tools are not available (missing system dependencies),
        the skill will be created with empty tools list. The instructions
        will still be available to inform the user about the capability.
    """
    tools = []
    if PDF_TOOLS_AVAILABLE:
        tools = [CreateUnifiedPDFTool()]

    skill = Skill(
        metadata=SkillMetadata(
            name="unified_pdf",
            description="Create PDF documents from HTML content with automatic image embedding",
            trigger_patterns=[
                "pdf",
                "document",
                "report",
                "create pdf",
                "generate pdf",
                "html to pdf",
                "export pdf",
                "pdf with images",
                "report with charts",
                "pdf with charts",
                "embed images",
                "pdf report",
                "document with images",
                "report with images",
                "pdf with figures",
            ],
            category=SkillCategory.DOCUMENT,
            version="1.0.0",
        ),
        instructions=UNIFIED_PDF_INSTRUCTIONS,
        tools=tools,
        dependencies=[],
        config={"pdf_tools_available": PDF_TOOLS_AVAILABLE},
    )
    skill._display_name = "Génération de PDF"
    skill._display_icon = "📄"
    return skill


__all__ = ["create_unified_pdf_skill", "UNIFIED_PDF_INSTRUCTIONS"]
