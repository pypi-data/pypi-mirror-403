"""
Image Display Skill - Image display capability.

This skill provides the ability to display images in the chat interface
from URLs. Images are rendered with download buttons and click-to-open
functionality.

Note: This is a UI-only skill with no associated tools - it provides
instructions for generating image JSON that the frontend renders.
"""

from ..base import Skill, SkillCategory, SkillMetadata


IMAGE_DISPLAY_INSTRUCTIONS = """
## Image Display Instructions

You can display images in the chat by using a JSON block with an "image" key.
Images are rendered with a download button and click-to-open functionality.

### When to Use Image Display
- Displaying charts, diagrams, or visualizations from external sources
- Showing screenshots or reference images
- Presenting generated images from image generation APIs
- Including logos, icons, or other visual assets
- Displaying images from URLs

### Image JSON Structure

Use a JSON object with an "image" key containing the image configuration:

```json
{
  "image": {
    "url": "https://example.com/image.png",
    "alt": "Description of the image",
    "caption": "Optional caption below the image"
  }
}
```

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | URL of the image (HTTP/HTTPS, S3, GCP, Azure, local path, or data URI) |
| `alt` | string | No | Alt text for accessibility |
| `caption` | string | No | Caption displayed below image |
| `width` | string | No | CSS width (e.g., "400px", "100%") |
| `height` | string | No | CSS height (e.g., "300px", "auto") |
| `filename` | string | No | Custom filename for download |
| `filestorage` | string | No | Storage type (auto-detected): `web`, `s3`, `gcp`, `azure`, `local`, `minio`, `data_uri`, `unknown` |

### File Storage Detection

The `filestorage` field is a simple string indicating where the image is stored.
This field is optional and is auto-detected from the URL pattern by the system.

#### Storage Types

| Type | Detection Patterns |
|------|-------------------|
| `s3` | `s3://` protocol, `s3.amazonaws.com`, `s3-*.amazonaws.com` |
| `gcp` | `gs://` protocol, `storage.googleapis.com`, `storage.cloud.google.com` |
| `azure` | `blob.core.windows.net`, `*.blob.core.windows.net` |
| `local` | `file://` protocol, `/path/to/file`, `./relative/path`, `C:\\windows\\path` |
| `minio` | Custom MinIO endpoints, ports 9000/9001 |
| `data_uri` | `data:image/*;base64,` prefix |
| `web` | Generic `http://` or `https://` URLs |
| `unknown` | No pattern match |

### Examples

**Simple image with just URL:**
```json
{"image": {"url": "https://example.com/chart.png"}}
```

**Image with alt text and caption:**
```json
{
  "image": {
    "url": "https://example.com/sales-chart.png",
    "alt": "Sales chart Q4 2024",
    "caption": "Quarterly sales performance"
  }
}
```

**Image with size constraints:**
```json
{
  "image": {
    "url": "https://example.com/diagram.png",
    "alt": "Architecture diagram",
    "caption": "System architecture overview",
    "width": "600px",
    "height": "auto",
    "filename": "architecture-diagram.png"
  }
}
```

**Full-width responsive image:**
```json
{
  "image": {
    "url": "https://example.com/banner.jpg",
    "alt": "Welcome banner",
    "width": "100%",
    "height": "auto"
  }
}
```

**Image from S3:**
```json
{
  "image": {
    "url": "https://my-bucket.s3.amazonaws.com/images/report.png",
    "alt": "Monthly report",
    "caption": "Generated from S3 storage"
  }
}
```

**Image from GCP Cloud Storage:**
```json
{
  "image": {
    "url": "https://storage.googleapis.com/my-bucket/chart.png",
    "alt": "Analytics chart"
  }
}
```

**Image from Azure Blob Storage:**
```json
{
  "image": {
    "url": "https://myaccount.blob.core.windows.net/images/logo.png",
    "alt": "Company logo"
  }
}
```

**Base64 encoded data URI:**
```json
{
  "image": {
    "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "alt": "Inline image"
  }
}
```

**Local file path:**
```json
{
  "image": {
    "url": "file:///home/user/images/screenshot.png",
    "alt": "Local screenshot"
  }
}
```

### Behavior

- Images are displayed with max-width constraints for responsive layout
- Clicking on the image opens it in a new tab for full-size viewing
- A download button (💾) appears below the image for easy downloading
- If the image fails to load, an error placeholder is shown with the alt text
- Multiple images can be included in a single response

### Best Practices

1. **Always include alt text** - Important for accessibility
2. **Use descriptive captions** - Help users understand the image context
3. **Specify dimensions when needed** - Prevent layout shifts
4. **Use HTTPS URLs** - Ensure secure image loading
5. **Provide meaningful filenames** - For better download experience

### Backward Compatibility

The `filestorage` field is fully backward compatible:

- **Optional field**: The `filestorage` field is not required. Existing image JSON
  without this field will continue to work normally.
- **Auto-detected**: The system automatically detects and adds the `filestorage` value
  based on the URL pattern. You don't need to provide it.
- **Simple string**: The `filestorage` is just a string like `"web"`, `"s3"`, `"gcp"`, etc.
- **No breaking changes**: All existing properties (`url`, `alt`, `caption`, `width`,
  `height`, `filename`) remain unchanged and work as before.

### URL Requirements

- Must be a valid URL or path (HTTP/HTTPS, S3, GCP, Azure, local path, or data URI)
- URL should point directly to an image file
- Supported formats: PNG, JPG, JPEG, GIF, WebP, SVG
- Cloud storage URLs (S3, GCP, Azure) must be publicly accessible or pre-signed
- Data URIs must use base64 encoding with proper MIME type

### When to Use Image Display

**USE image_display JSON for:**
- Web URLs (http://, https://) - Just put the URL directly in the JSON
- S3, GCP, Azure URLs - Just put the URL directly in the JSON
- Presigned S3 URLs - Just put the URL directly in the JSON
- Data URIs (base64) - Just put the data URI directly in the JSON
- Any publicly accessible image URL

**⚠️ IMPORTANT: DO NOT call get_file_path to display an image when you already have a URL!**
When you have a URL from `save_chart_as_image` or `save_mermaid_as_image`, use it DIRECTLY:

```json
{"image": {"url": "THE_URL_FROM_THE_TOOL", "alt": "Description"}}
```

**DO NOT do this:**
```python
# WRONG - Don't call get_file_path when you already have a URL!
url = await save_chart_as_image(...)  # Returns a URL
path = await get_file_path(file_id)  # DON'T DO THIS - unnecessary!
```

**DO this instead:**
```python
# CORRECT - Use the URL directly
result = await save_chart_as_image(...)  # Returns a URL in the message
# Then use that URL directly in the image JSON
```

### When NOT to Use Image Display

- For user-uploaded images → Use the file upload feature
- For generating NEW charts → Use the chart skill with save_chart_as_image
- For generating NEW diagrams → Use the mermaid skill with save_mermaid_as_image
- For local file paths (file://, /path/to/file) → Use file_access_skill first to get a data URI, then use image_display

### Multiple Images

You can include multiple images in a single response by using multiple
image JSON blocks:

```json
{"image": {"url": "https://example.com/image1.png", "caption": "First image"}}
```

```json
{"image": {"url": "https://example.com/image2.png", "caption": "Second image"}}
```
"""


def create_image_display_skill() -> Skill:
    """
    Create the image display skill.

    This skill provides instructions for displaying images from URLs.
    It has no associated tools - images are rendered by the UI from JSON.

    Returns:
        Skill instance for image display
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="image_display",
            description="Display images from URLs with download and view functionality",
            trigger_patterns=[
                "display image",
                "show image",
                "image url",
                "render image",
                "embed image",
                "picture",
                "photo",
                "screenshot",
            ],
            category=SkillCategory.UI,
            version="1.0.0",
        ),
        instructions=IMAGE_DISPLAY_INSTRUCTIONS,
        tools=[],  # UI-only skill, no tools
        dependencies=[],
        config={},
    )
    skill._display_name = "Affichage d'images"
    skill._display_icon = "🖼️"
    return skill


__all__ = ["create_image_display_skill", "IMAGE_DISPLAY_INSTRUCTIONS"]
