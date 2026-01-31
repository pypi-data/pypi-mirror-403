"""
Mermaid Skill - Mermaid diagram generation capability.

This skill provides the ability to generate Mermaid diagrams as PNG images.
It wraps the MermaidToImageTool with detailed instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import MermaidToImageTool


MERMAID_INSTRUCTIONS = """
## Mermaid Diagram Instructions

You have TWO ways to create diagrams:
1. **🖥️ Interactive Display** (DEFAULT) - Show diagram directly in chat using ```mermaid code block
2. **💾 Save as Image** - Create PNG file using `save_mermaid_as_image` tool
3. You can do both.

### ⚡ Quick Decision Guide

```
User wants to see a diagram?
├── Just "show me" / "create" / "display" → Use Interactive Display (```mermaid)
├── "Save as image" / "download" / "PNG" → Use Save as Image tool
├── "Put in PDF" / "embed in document" → Use Save as Image tool
├── Not sure? → Default to Interactive Display
└── Everytime you create a chart you display it just don't do it if say otherwise

```

**DEFAULT BEHAVIOR**: Always use Interactive Display unless the user explicitly needs a file.

---

## 🖥️ Interactive Display (DEFAULT)

To display a diagram directly in the chat, use a fenced code block with the `mermaid` language identifier.
The frontend renders Mermaid diagrams automatically - no tool needed!

**Format:**
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[End]
```

### Complete Interactive Display Examples

**Flowchart:**
```mermaid
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]
```

**Sequence Diagram:**
```mermaid
sequenceDiagram
    participant U as User
    participant S as Server
    participant D as Database
    U->>S: Request data
    S->>D: Query
    D-->>S: Results
    S-->>U: Response
```

**Class Diagram:**
```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    Animal <|-- Dog
```

---

## 💾 Save as Image (For PDFs/Downloads ONLY)

**⚠️ WARNING**: Only use `save_mermaid_as_image` when the user explicitly needs a PNG file.
Do NOT use this tool just to show a diagram - use Interactive Display instead!

**Use Save as Image ONLY for:**
- Creating a PDF document with embedded diagram
- User explicitly asks to "save", "download", or "export" the diagram
- Sharing the diagram externally (email, etc.)

### Tool Parameters
- `mermaid_code`: Mermaid diagram code (without ```mermaid``` markers)
- `filename`: Name for the output file (without .png extension)
- `width`: Optional width in pixels (default: auto-calculated)
- `height`: Optional height in pixels (default: auto-calculated)
- `background_color`: Background color (default: "white")
- `theme`: Mermaid theme - "default", "dark", "forest", "neutral"

### Tool Output

The tool returns a message with a view URL for displaying the image in chat.

**View URL (for displaying in chat):**
The returned URL uses `/files/{id}/view` which displays the image inline.
```
Mermaid diagram saved successfully as PNG!

![diagram_name.png](/files/{file_id}/view)
```

**Download URL (for forcing file download):**
If the user wants to download the image file, replace `/view` with `/download`:
```
[Download diagram_name.png](/files/{file_id}/download)
```

**To display the saved diagram image in JSON format:**
```json
{"image": {"url": "/files/{file_id}/view", "alt": "Diagram"}}
```

**⚠️ DO NOT call get_file_path after save_mermaid_as_image!**
The URL returned by save_mermaid_as_image is already ready to use.

### Using Saved Diagrams in PDFs

After saving a diagram, you get a file_id. To embed in a PDF:
```html
<img src="file_id:YOUR_FILE_ID" alt="Diagram Description">
```

Then use `create_pdf_with_images` to generate the PDF.

---

## Diagram Syntax Reference

### Supported Diagram Types
- Flowcharts (`graph` or `flowchart`)
- Sequence diagrams (`sequenceDiagram`)
- Class diagrams (`classDiagram`)
- State diagrams (`stateDiagram-v2`)
- Entity Relationship diagrams (`erDiagram`)
- Gantt charts (`gantt`)
- Pie charts (`pie`)
- User Journey diagrams (`journey`)

### Flowchart Syntax

Direction options:
- `TD` or `TB` - Top to bottom
- `BT` - Bottom to top
- `LR` - Left to right
- `RL` - Right to left

Node shapes:
- `[text]` - Rectangle
- `(text)` - Rounded rectangle
- `{text}` - Diamond (decision)
- `([text])` - Stadium shape
- `[[text]]` - Subroutine
- `[(text)]` - Cylinder (database)
- `((text))` - Circle

### Sequence Diagram Arrow Types
- `->` - Solid line without arrow
- `-->` - Dotted line without arrow
- `->>` - Solid line with arrow
- `-->>` - Dotted line with arrow
- `-x` - Solid line with cross
- `--x` - Dotted line with cross

### Class Diagram Relationships
- `<|--` - Inheritance
- `*--` - Composition
- `o--` - Aggregation
- `-->` - Association
- `--` - Link (solid)
- `..>` - Dependency
- `..|>` - Realization

### State Diagram Syntax
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Complete: Success
    Processing --> Error: Failure
    Complete --> [*]
    Error --> Idle: Retry
```

### Entity Relationship Diagram
Cardinality:
- `||` - Exactly one
- `o|` - Zero or one
- `}|` - One or more
- `}o` - Zero or more

### Gantt Chart Syntax
```mermaid
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Planning
    Research     :a1, 2024-01-01, 30d
    Design       :a2, after a1, 20d
```

### Pie Chart Syntax
```mermaid
pie title Distribution
    "Category A" : 45
    "Category B" : 30
    "Category C" : 25
```

### Best Practices
1. Keep diagrams simple and readable
2. Use meaningful node labels
3. Group related elements together
4. Use appropriate diagram type for your content
5. Add titles where supported
6. Use consistent naming conventions
"""


def create_mermaid_skill() -> Skill:
    """
    Create the mermaid diagram generation skill.

    Returns:
        Skill instance for mermaid diagram generation
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="mermaid",
            description="Display interactive Mermaid diagrams in chat OR save as PNG images. Use ```mermaid code blocks for display (default), save_mermaid_as_image tool for files.",
            trigger_patterns=[
                "mermaid",
                "diagram",
                "flowchart",
                "sequence",
                "sequence diagram",
                "class diagram",
                "state diagram",
                "er diagram",
                "entity relationship",
                "gantt",
                "architecture",
            ],
            category=SkillCategory.VISUALIZATION,
            version="1.0.0",
        ),
        instructions=MERMAID_INSTRUCTIONS,
        tools=[MermaidToImageTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Génération des diagrammes"
    skill._display_icon = "🔀"
    return skill


__all__ = ["create_mermaid_skill", "MERMAID_INSTRUCTIONS"]
