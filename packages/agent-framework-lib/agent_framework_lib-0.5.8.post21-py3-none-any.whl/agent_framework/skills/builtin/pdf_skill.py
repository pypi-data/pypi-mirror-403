"""
PDF Skill - PDF document generation capability.

This skill provides the ability to create PDF documents from Markdown or HTML content.
It wraps the CreatePDFFromMarkdownTool and CreatePDFFromHTMLTool with detailed
instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import PDF_TOOLS_AVAILABLE

# Conditionally import PDF tools
if PDF_TOOLS_AVAILABLE:
    from ...tools import CreatePDFFromMarkdownTool, CreatePDFFromHTMLTool


PDF_INSTRUCTIONS = """
## PDF Generation Instructions

You can create professional PDF documents from Markdown or HTML content.

### Available Tools

1. **create_pdf_from_markdown** - Create PDF from Markdown content
2. **create_pdf_from_html** - Create PDF from HTML content with custom CSS

### Creating PDF from Markdown

Use `create_pdf_from_markdown` for most document creation needs.

**Parameters:**
- `title`: Document title (used for filename and header)
- `content`: Markdown formatted content
- `author`: Optional author name
- `template_style`: 'professional', 'minimal', or 'modern' (default: 'professional')

**Template Styles:**

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

**Example:**
```python
result = await create_pdf_from_markdown(
    title="Quarterly Report",
    content=\"\"\"
# Quarterly Report Q4 2024

## Executive Summary

This quarter showed significant growth...

## Key Metrics

| Metric | Value | Change |
|--------|-------|--------|
| Revenue | $1.2M | +15% |
| Users | 50,000 | +25% |

## Conclusion

The results indicate positive momentum...
\"\"\",
    author="Analytics Team",
    template_style="professional"
)
```

**Markdown Features Supported:**
- Headers (# ## ### etc.)
- Bold (**text**) and italic (*text*)
- Lists (ordered and unordered)
- Tables (pipe syntax)
- Code blocks (``` ```)
- Inline code (`code`)
- Blockquotes (> quote)
- Links [text](url)

### Creating PDF from HTML

Use `create_pdf_from_html` for full control over styling.

**Parameters:**
- `title`: Document title
- `html_content`: Full HTML document or HTML fragment
- `custom_css`: Optional additional CSS to apply
- `author`: Optional author name

**Example with HTML Fragment:**
```python
result = await create_pdf_from_html(
    title="Custom Report",
    html_content=\"\"\"
<h1>Custom Report</h1>
<p>This is a <strong>custom</strong> report with HTML.</p>
<table>
    <tr><th>Item</th><th>Value</th></tr>
    <tr><td>Sales</td><td>$100,000</td></tr>
</table>
\"\"\",
    custom_css=\"\"\"
h1 { color: #2c5aa0; }
table { border: 2px solid #333; }
\"\"\"
)
```

**Example with Complete HTML Document:**
```python
result = await create_pdf_from_html(
    title="Full Document",
    html_content=\"\"\"
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial; }
        .highlight { background: yellow; }
    </style>
</head>
<body>
    <h1>My Document</h1>
    <p class="highlight">Important text here.</p>
</body>
</html>
\"\"\"
)
```

### Best Practices

1. **Use Markdown for most documents** - It's simpler and the templates look great
2. **Use HTML for complex layouts** - When you need precise control
3. **Keep content organized** - Use headers to structure your document
4. **Include tables for data** - Both Markdown and HTML tables render well
5. **Test with professional template first** - It works well for most use cases

### Page Layout Notes

- Default page size is A4
- Margins are automatically set by the template
- Page numbers are included automatically
- Long content will span multiple pages
- Tables and code blocks handle page breaks gracefully

### Error Handling

- Empty title or content will return an error
- Invalid template_style defaults to 'professional'
- System dependency errors will provide installation instructions
"""


def create_pdf_skill() -> Skill:
    """
    Create the PDF generation skill.

    Returns:
        Skill instance for PDF generation

    Note:
        If PDF tools are not available (missing system dependencies),
        the skill will be created with empty tools list. The instructions
        will still be available to inform the user about the capability.
    """
    tools = []
    if PDF_TOOLS_AVAILABLE:
        tools = [CreatePDFFromMarkdownTool(), CreatePDFFromHTMLTool()]

    skill = Skill(
        metadata=SkillMetadata(
            name="pdf",
            description="Create PDF documents from Markdown or HTML content",
            trigger_patterns=[
                "pdf",
                "document",
                "report",
                "create pdf",
                "generate pdf",
                "markdown to pdf",
                "html to pdf",
                "export pdf",
            ],
            category=SkillCategory.DOCUMENT,
            version="1.0.0",
        ),
        instructions=PDF_INSTRUCTIONS,
        tools=tools,
        dependencies=[],
        config={"pdf_tools_available": PDF_TOOLS_AVAILABLE},
    )
    skill._display_name = "Génération de PDF"
    skill._display_icon = "📄"
    return skill


__all__ = ["create_pdf_skill", "PDF_INSTRUCTIONS"]
