"""
File Access Skill - File path and URL access capability.

This skill provides the ability to retrieve file paths and URLs
for embedding in HTML/PDF documents.
It wraps the GetFilePathTool with detailed instructions.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import GetFilePathTool


FILE_ACCESS_INSTRUCTIONS = """
## File Access Instructions

You can retrieve file paths and URLs for stored files to embed them
in HTML, PDF, or other documents.

### Available Tools

1. **get_file_path** - Get an accessible path or URL for a stored file

### Get File Path Tool

Use `get_file_path` to get an accessible reference to a stored file.

**Behavior by storage backend:**
- **Local storage**: Returns an absolute file path with `file://` protocol
- **S3/MinIO with presigned URLs**: Returns a presigned S3 URL (when S3_URL_MODE=presigned)
- **S3/MinIO with public URLs**: Returns a public S3 URL (when S3_URL_MODE=public)
- **S3/MinIO with API mode**: Returns an API URL `/files/{file_id}/download`

**Parameters:**
- `file_id` (required): The file ID returned from file storage operations

**Returns:**
- For local: `file:///absolute/path/to/file.png`
- For S3/MinIO (presigned): `https://bucket.s3.region.amazonaws.com/key?X-Amz-...`
- For S3/MinIO (public): `https://bucket.s3.region.amazonaws.com/key`
- For S3/MinIO (api mode): `/files/{file_id}/download`

**Example Usage:**
```python
# Get path for a chart image
path = await get_file_path("chart_abc123")
# Use in HTML: <img src="{path}">
```

### Common Use Cases

#### 1. Displaying Images in Chat

**IMPORTANT**: When you have a URL from `save_chart_as_image` or `save_mermaid_as_image`,
use it directly in the image JSON - DO NOT call `get_file_path`!

```json
{"image": {"url": "https://bucket.s3.region.amazonaws.com/key?X-Amz-...", "alt": "Chart"}}
```

#### 2. Embedding Images in HTML

```html
<!-- Using file path (local storage) -->
<img src="file:///path/to/image.png" alt="Chart">

<!-- Using S3 presigned URL -->
<img src="https://bucket.s3.region.amazonaws.com/key?X-Amz-..." alt="Chart">
```

#### 3. Creating PDFs with Images

When generating PDFs that include stored images:
1. Create the image (chart, diagram, etc.) and get the file_id
2. Use `get_file_path` to get a reference
3. Include the reference in your HTML/Markdown for PDF generation

```python
# Step 1: Create chart and get file_id
chart_file_id = await save_chart_as_image(chart_config, "sales_chart")

# Step 2: Get accessible path
image_path = await get_file_path(chart_file_id)

# Step 3: Use in HTML for PDF
html = f'''
<h1>Sales Report</h1>
<img src="{image_path}" alt="Sales Chart">
'''
```

### Best Practices

1. **Use URLs directly when available**: If you already have a URL from chart/mermaid tools, use it directly
2. **Use presigned URLs for S3**: Configure S3_URL_MODE=presigned for direct browser access
3. **Check file existence**: Handle cases where file_id may be invalid
4. **Cache paths**: If using the same file multiple times, cache the path/URL

### Error Handling

Common errors:
- "File with ID 'xxx' not found" → Invalid file_id
- "File exists in metadata but not on disk" → File was deleted
- "Failed to get file path" → Storage access error

### Limitations

- File paths only work on the same machine (not portable)
- Presigned URLs expire after a configured time (default: 1 hour)
"""


def create_file_access_skill() -> Skill:
    """
    Create the file access skill.

    Returns:
        Skill instance for file path and URL access
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="file_access",
            description="Get file paths and URLs for embedding files in documents",
            trigger_patterns=[
                "file path",
                "file access",
                "embed file",
                "file url",
                "embed image",
                "image path",
                "file reference",
            ],
            category=SkillCategory.DOCUMENT,
            version="1.1.0",
        ),
        instructions=FILE_ACCESS_INSTRUCTIONS,
        tools=[GetFilePathTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Accès aux fichiers"
    skill._display_icon = "🔗"
    return skill


__all__ = ["create_file_access_skill", "FILE_ACCESS_INSTRUCTIONS"]
