"""
Chart Skill - Chart.js chart generation capability.

This skill provides the ability to generate Chart.js charts as PNG images.
It wraps the ChartToImageTool with detailed instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import ChartToImageTool


CHART_INSTRUCTIONS = """
## Chart Generation Instructions

You have TWO ways to create charts:
1. **🖥️ Interactive Display** (DEFAULT) - Show chart directly in chat using ```chart code block
2. **💾 Save as Image** - Create PNG file using `save_chart_as_image` tool
3. You can do both.

### ⚡ Quick Decision Guide

```
User wants to see a chart?
├── Just "show me" / "create" / "display" → Use Interactive Display (```chart)
├── "Save as image" / "download" / "PNG" → Use Save as Image tool
├── "Put in PDF" / "embed in document" → Use Save as Image tool
├── Not sure? → Default to Interactive Display
└── Everytime you create a chart you display it just don't do it if say otherwise
```

**DEFAULT BEHAVIOR**: Always use Interactive Display unless the user explicitly needs a file.

---

## 🖥️ Interactive Display (DEFAULT)

To display a chart directly in the chat, use a fenced code block with the `chart` language identifier.

**Format:**
```chart
{
  "type": "chartjs",
  "chartConfig": {
    "type": "bar",
    "data": { ... },
    "options": { ... }
  }
}
```

**CRITICAL**: The wrapper structure MUST be:
```json
{
  "type": "chartjs",
  "chartConfig": { /* Your Chart.js config here */ }
}
```

### Complete Interactive Display Example

```chart
{
  "type": "chartjs",
  "chartConfig": {
    "type": "bar",
    "data": {
      "labels": ["January", "February", "March", "April", "May"],
      "datasets": [{
        "label": "Sales 2024",
        "data": [65, 59, 80, 81, 56],
        "backgroundColor": "rgba(54, 162, 235, 0.6)",
        "borderColor": "rgba(54, 162, 235, 1)",
        "borderWidth": 1
      }]
    },
    "options": {
      "responsive": true,
      "plugins": {
        "title": {"display": true, "text": "Monthly Sales"},
        "legend": {"display": true}
      },
      "scales": {
        "y": {"beginAtZero": true}
      }
    }
  }
}
```

### More Interactive Display Examples

**Line Chart:**
```chart
{
  "type": "chartjs",
  "chartConfig": {
    "type": "line",
    "data": {
      "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
      "datasets": [{
        "label": "Revenue",
        "data": [1200, 1900, 1500, 2100],
        "borderColor": "rgba(75, 192, 192, 1)",
        "backgroundColor": "rgba(75, 192, 192, 0.2)",
        "fill": true,
        "tension": 0.4
      }]
    },
    "options": {
      "responsive": true,
      "plugins": {
        "title": {"display": true, "text": "Weekly Revenue Trend"}
      }
    }
  }
}
```

**Pie Chart:**
```chart
{
  "type": "chartjs",
  "chartConfig": {
    "type": "pie",
    "data": {
      "labels": ["Product A", "Product B", "Product C"],
      "datasets": [{
        "data": [300, 150, 100],
        "backgroundColor": [
          "rgba(255, 99, 132, 0.8)",
          "rgba(54, 162, 235, 0.8)",
          "rgba(255, 206, 86, 0.8)"
        ]
      }]
    },
    "options": {
      "responsive": true,
      "plugins": {
        "title": {"display": true, "text": "Product Distribution"},
        "legend": {"display": true, "position": "right"}
      }
    }
  }
}
```

---

## 💾 Save as Image (For PDFs/Downloads ONLY)

**⚠️ WARNING**: Only use `save_chart_as_image` when the user explicitly needs a PNG file.
Do NOT use this tool just to show a chart - use Interactive Display instead!

**Use Save as Image ONLY for:**
- Creating a PDF document with embedded chart
- User explicitly asks to "save", "download", or "export" the chart
- Sharing the chart externally (email, etc.)

### Tool Parameters
- `chart_config`: JSON string with the Chart.js configuration (same as chartConfig above)
- `filename`: Name for the output file (without .png extension)
- `width`: Optional width in pixels (default: auto-calculated, min 1200)
- `height`: Optional height in pixels (default: auto-calculated, min 900)
- `background_color`: Background color (default: "white")

### Tool Output

The tool returns a message with a view URL for displaying the image in chat.

**View URL (for displaying in chat):**
The returned URL uses `/files/{id}/view` which displays the image inline.
```
Chart saved successfully as PNG!

![chart_name.png](/files/{file_id}/view)
```

**Download URL (for forcing file download):**
If the user wants to download the image file, replace `/view` with `/download`:
```
[Download chart_name.png](/files/{file_id}/download)
```

**To display the saved chart image in JSON format:**
```json
{"image": {"url": "/files/{file_id}/view", "alt": "Chart"}}
```

**⚠️ DO NOT call get_file_path after save_chart_as_image!**
The URL returned by save_chart_as_image is already ready to use.

### Using Saved Charts in PDFs

After saving a chart, you get a file_id. To embed in a PDF:
```html
<img src="file_id:YOUR_FILE_ID" alt="Chart Description">
```

Then use `create_pdf_with_images` to generate the PDF.

---

## Chart Configuration Reference

### Supported Chart Types
- `bar` - Bar charts (vertical)
- `line` - Line charts
- `pie` - Pie charts
- `doughnut` - Doughnut charts
- `polarArea` - Polar area charts
- `radar` - Radar charts
- `scatter` - Scatter plots
- `bubble` - Bubble charts

### CRITICAL: NO JAVASCRIPT FUNCTIONS ALLOWED
The chartConfig must be PURE JSON - NO JavaScript functions or callbacks.
Do NOT use: `function()`, arrow functions `=>`, or any JavaScript code.

### Color Formats
Use RGBA format for colors: `rgba(red, green, blue, alpha)`
- red, green, blue: 0-255
- alpha: 0-1 (transparency)

Common colors:
- Red: `rgba(255, 99, 132, 0.6)`
- Blue: `rgba(54, 162, 235, 0.6)`
- Yellow: `rgba(255, 206, 86, 0.6)`
- Green: `rgba(75, 192, 192, 0.6)`
- Purple: `rgba(153, 102, 255, 0.6)`
- Orange: `rgba(255, 159, 64, 0.6)`

### Best Practices
1. Always include a title in options.plugins.title
2. Use descriptive labels for datasets
3. Choose appropriate chart type for your data
4. Use consistent color schemes
5. Keep data readable - avoid too many data points in pie charts
"""


def create_chart_skill() -> Skill:
    """
    Create the chart generation skill.

    Returns:
        Skill instance for chart generation
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="chart",
            description="Display interactive Chart.js charts in chat OR save as PNG images. Use ```chart code blocks for display (default), save_chart_as_image tool for files.",
            trigger_patterns=[
                "chart",
                "graph",
                "plot",
                "visualization",
                "bar chart",
                "line chart",
                "pie chart",
                "doughnut",
                "scatter",
                "radar",
            ],
            category=SkillCategory.VISUALIZATION,
            version="1.0.0",
        ),
        instructions=CHART_INSTRUCTIONS,
        tools=[ChartToImageTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Génération des graphiques"
    skill._display_icon = "📊"
    return skill


__all__ = ["create_chart_skill", "CHART_INSTRUCTIONS"]
