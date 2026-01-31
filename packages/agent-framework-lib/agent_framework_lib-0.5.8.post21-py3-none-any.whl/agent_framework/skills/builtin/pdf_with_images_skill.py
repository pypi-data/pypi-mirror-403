"""
PDF with Images Skill - PDF document generation with embedded images.

This skill provides the ability to create PDF documents from HTML content
with automatic image embedding from file storage. It wraps the
CreatePDFWithImagesTool with detailed instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import CreatePDFWithImagesTool


PDF_WITH_IMAGES_INSTRUCTIONS = """
## PDF with Images Generation Instructions

You can create professional PDF documents with embedded images from file storage.
This tool automatically embeds images using their file IDs.

### Available Tool

**create_pdf_with_images** - Create PDF from HTML with automatic image embedding

### How Image Embedding Works

Images are referenced using a special `file_id:` syntax in img tags:
```html
<img src="file_id:YOUR_FILE_ID" alt="Description">
```

The tool automatically:
1. Retrieves the image from file storage
2. Converts it to a data URI
3. Embeds it directly in the PDF
4. Applies adaptive sizing based on your preference

### Parameters

- `title`: Document title
- `html_content`: HTML content with file_id references in img tags
- `author`: Optional author name
- `image_size`: Image sizing preference:
  - `"small"`: 50% of page width (compact reports)
  - `"medium"`: 75% of page width (balanced, recommended)
  - `"large"`: 100% of page width (default)
  - `"full"`: 100% of page width

### CRITICAL HTML STRUCTURE

**ALWAYS wrap images in `<figure>` tags** to keep image and caption together:

```html
<div class="section break-before">
    <h2>1. Section Title</h2>
    <p>Brief intro text (2-3 lines max before image)...</p>
    <figure>
        <img src="file_id:xxx" alt="Description">
        <figcaption>Figure 1: Caption here</figcaption>
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
result = await create_pdf_with_images(
    title="Sales Analysis Report",
    html_content=\"\"\"
<div class="section">
    <h1>Sales Analysis Report</h1>
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
</div>

<div class="section break-before">
    <h2>3. Conclusions</h2>
    <p>Key findings and recommendations based on the analysis.</p>
    <ul>
        <li>Revenue increased 15% quarter-over-quarter</li>
        <li>Western region showed strongest growth</li>
        <li>Recommend expanding marketing in Eastern region</li>
    </ul>
</div>
\"\"\",
    author="Analytics Team",
    image_size="large"
)
```

### Workflow: Creating Reports with Charts

1. **Generate charts first** using the chart skill:
   ```python
   # Create a chart and get its file_id
   chart_result = await save_chart_as_image(chart_config, "revenue_chart")
   # Returns file_id like "abc-123"
   ```

2. **Create the PDF with embedded charts:**
   ```python
   await create_pdf_with_images(
       title="Report",
       html_content='<figure><img src="file_id:abc-123" alt="Chart"></figure>',
       image_size="large"
   )
   ```

### Image Size Guidelines

| Size | Width | Best For |
|------|-------|----------|
| small | 50% | Multiple images per page, thumbnails |
| medium | 75% | Balanced reports, mixed content |
| large | 100% | Single chart per section, detailed visuals |
| full | 100% | Same as large |

### Best Practices

1. **One main image per section** works best for readability
2. **Keep intro text short** (2-3 lines) before each image
3. **Use `break-before`** only for major numbered sections
4. **Always include `<figcaption>`** for professional appearance
5. **Use `image_size="medium"`** when you have multiple images per page

### Supported Image Formats

- PNG (recommended for charts and diagrams)
- JPEG (good for photos)
- GIF
- WebP

### Error Handling

- Invalid file_id will return an error with the specific ID
- Missing images will prevent PDF generation
- Large images are automatically downsampled for optimal PDF size
"""


def create_pdf_with_images_skill() -> Skill:
    """
    Create the PDF with images generation skill.

    Returns:
        Skill instance for PDF generation with embedded images
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="pdf_with_images",
            description="Create PDF documents with embedded images from file storage",
            trigger_patterns=[
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
        instructions=PDF_WITH_IMAGES_INSTRUCTIONS,
        tools=[CreatePDFWithImagesTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "PDF avec images"
    skill._display_icon = "📄"
    return skill


__all__ = ["create_pdf_with_images_skill", "PDF_WITH_IMAGES_INSTRUCTIONS"]
