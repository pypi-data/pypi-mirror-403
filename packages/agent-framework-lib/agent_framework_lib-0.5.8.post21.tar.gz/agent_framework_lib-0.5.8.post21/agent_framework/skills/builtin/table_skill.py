"""
Table Skill - Table image generation capability.

This skill provides the ability to generate table images as PNG files.
It wraps the TableToImageTool with detailed instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import TableToImageTool


TABLE_INSTRUCTIONS = """
## Table Generation Instructions

You have TWO ways to create tables:
1. **🖥️ Interactive Display** (DEFAULT) - Show table directly in chat using ```tabledata code block
2. **💾 Save as Image** - Create PNG file using `save_table_as_image` tool
3. You can do both.

### ⚡ Quick Decision Guide

```
User wants to see a table?
├── Just "show me" / "create" / "display" → Use Interactive Display (```tabledata)
├── "Save as image" / "download" / "PNG" → Use Save as Image tool
├── "Put in PDF" / "embed in document" → Use Save as Image tool
├── Not sure? → Default to Interactive Display
└── Everytime you create a chart you display it just don't do it if say otherwise
```

**DEFAULT BEHAVIOR**: Always use Interactive Display unless the user explicitly needs a file.

---

## 🖥️ Interactive Display (DEFAULT)

To display a table directly in the chat, use a fenced code block with the `tabledata` language identifier.
The frontend renders tables automatically with professional styling - no tool needed!

**Format:**
```tabledata
{
  "caption": "Table Title",
  "headers": ["Column 1", "Column 2", "Column 3"],
  "rows": [
    ["Row 1 Cell 1", "Row 1 Cell 2", "Row 1 Cell 3"],
    ["Row 2 Cell 1", "Row 2 Cell 2", "Row 2 Cell 3"]
  ]
}
```

### Complete Interactive Display Examples

**Employee Directory:**
```tabledata
{
  "caption": "Employee Directory",
  "headers": ["Name", "Department", "Email"],
  "rows": [
    ["Alice Smith", "Engineering", "alice@example.com"],
    ["Bob Johnson", "Marketing", "bob@example.com"],
    ["Carol Williams", "Sales", "carol@example.com"]
  ]
}
```

**Sales Report:**
```tabledata
{
  "caption": "Quarterly Sales Report",
  "headers": ["Product", "Q1", "Q2", "Q3", "Q4", "Total"],
  "rows": [
    ["Widget A", "1200", "1350", "1100", "1500", "5150"],
    ["Widget B", "800", "950", "1200", "1100", "4050"],
    ["Widget C", "500", "600", "700", "800", "2600"]
  ]
}
```

**Feature Comparison:**
```tabledata
{
  "caption": "Feature Comparison",
  "headers": ["Feature", "Basic Plan", "Pro Plan", "Enterprise"],
  "rows": [
    ["Storage", "5 GB", "50 GB", "Unlimited"],
    ["Users", "1", "10", "Unlimited"],
    ["Support", "Email", "Priority", "24/7 Dedicated"],
    ["Price", "$9/mo", "$29/mo", "Custom"]
  ]
}
```

---

## 💾 Save as Image (For PDFs/Downloads ONLY)

**⚠️ WARNING**: Only use `save_table_as_image` when the user explicitly needs a PNG file.
Do NOT use this tool just to show a table - use Interactive Display instead!

**Use Save as Image ONLY for:**
- Creating a PDF document with embedded table
- User explicitly asks to "save", "download", or "export" the table
- Sharing the table externally (email, etc.)

### Tool Parameters
- `table_data`: JSON string with headers, rows, and optional caption
- `filename`: Name for the output file (without .png extension)
- `width`: Optional width in pixels (default: auto-calculated)
- `theme`: Color theme (default: "default")
- `font_size`: Font size in pixels (default: 14)
- `show_index`: Show row numbers (default: false)

### Available Themes
1. **default** - Clean white background with gray headers
2. **dark** - Dark background with light text
3. **blue** - Blue header with light blue alternating rows
4. **green** - Green header with light green alternating rows
5. **minimal** - Simple white design with subtle borders

### Tool Output

The tool returns a message with a view URL for displaying the image in chat.

**View URL (for displaying in chat):**
The returned URL uses `/files/{id}/view` which displays the image inline.
```
Table saved successfully as PNG! (X rows, Y columns)

![table_name.png](/files/{file_id}/view)
```

**Download URL (for forcing file download):**
If the user wants to download the image file, replace `/view` with `/download`:
```
[Download table_name.png](/files/{file_id}/download)
```

### Using Saved Tables in PDFs

After saving a table, you get a file_id. To embed in a PDF:
```html
<img src="file_id:YOUR_FILE_ID" alt="Table Description">
```

Then use `create_pdf_with_images` to generate the PDF.

---

## Table Data Reference

### JSON Structure
- `caption` (optional): Title displayed above the table
- `headers` (required): Array of column header strings
- `rows` (required): Array of row arrays, each containing cell values

### Best Practices
1. **Keep tables readable**: Limit columns to 6-8 for best readability
2. **Use clear headers**: Make column headers descriptive but concise
3. **Consistent data types**: Keep data in each column consistent
4. **Add captions**: Use captions to provide context
5. **Use consistent units**: In numeric columns, use consistent units

### Formatting Tips
- Numbers are displayed as-is (no automatic formatting)
- Long text will wrap within cells
- Empty cells should be represented as empty strings ""
- All cell values should be strings in the JSON
"""


def create_table_skill() -> Skill:
    """
    Create the table image generation skill.

    Returns:
        Skill instance for table image generation
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="table",
            description="Display interactive tables in chat OR save as PNG images. Use ```tabledata code blocks for display (default), save_table_as_image tool for files.",
            trigger_patterns=[
                "table",
                "tabledata",
                "grid",
                "data table",
                "spreadsheet",
                "tabular",
                "rows and columns",
            ],
            category=SkillCategory.VISUALIZATION,
            version="1.0.0",
        ),
        instructions=TABLE_INSTRUCTIONS,
        tools=[TableToImageTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Génération de tableaux"
    skill._display_icon = "📋"
    return skill


__all__ = ["create_table_skill", "TABLE_INSTRUCTIONS"]
