"""
File Skill - File operations capability.

This skill provides the ability to create, list, and read files from storage.
It wraps the CreateFileTool, ListFilesTool, and ReadFileTool with detailed
instructions for proper usage.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import CreateFileTool, ListFilesTool, ReadFileTool


FILE_INSTRUCTIONS = """
## File Operations Instructions

You can perform file operations using the file storage system. The following tools are available:

### Available Tools

1. **create_file** - Create a new text file
2. **list_files** - List all stored files for the current session
3. **read_file** - Read a file's content by its ID

### Creating Files

Use `create_file` to create new text files in storage.

**Parameters:**
- `filename`: Name for the new file (e.g., "report.txt", "data.json", "notes.md")
- `content`: Text content to write to the file

**Example:**
```python
result = await create_file(
    filename="summary.txt",
    content="This is a summary of the analysis..."
)
# Returns: "File 'summary.txt' created successfully with ID: abc-123"
```

**Supported File Types:**
- Text files (.txt)
- JSON files (.json)
- Markdown files (.md)
- CSV files (.csv)
- Any text-based format

**Best Practices:**
- Use descriptive filenames
- Include file extension in the filename
- Content must be text (not binary)

### Listing Files

Use `list_files` to see all files stored in the current session.

**Example:**
```python
result = await list_files()
# Returns:
# Files:
# 1. report.txt (ID: abc-123, Size: 1.2 KB)
# 2. data.json (ID: def-456, Size: 3.4 KB)
```

**Notes:**
- Shows both user-uploaded and agent-generated files
- Includes file ID needed for reading files
- Shows file size for reference

### Reading Files

Use `read_file` to retrieve and display a file's content.

**Parameters:**
- `file_id`: Unique identifier of the file (from list_files output)

**Example:**
```python
result = await read_file(file_id="abc-123")
# Returns:
# File: report.txt
# Content:
# This is the file content...
```

**Notes:**
- Only works with text files
- Binary files will return an error message
- Use the file ID from list_files output

### Workflow Example

1. **Create a file:**
   ```python
   await create_file("analysis.md", "# Analysis Report\\n\\n## Summary\\n...")
   ```

2. **List files to get IDs:**
   ```python
   await list_files()
   ```

3. **Read a specific file:**
   ```python
   await read_file("abc-123")
   ```

### Error Handling

- Empty filename or content will return an error
- Invalid file ID will return an error
- Binary files cannot be read as text
"""


def create_file_skill() -> Skill:
    """
    Create the file operations skill.

    Returns:
        Skill instance for file operations
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="file",
            description="Create, list, and read files from storage",
            trigger_patterns=[
                "file",
                "create file",
                "list files",
                "read file",
                "save file",
                "write file",
                "text file",
                "store file",
            ],
            category=SkillCategory.DOCUMENT,
            version="1.0.0",
        ),
        instructions=FILE_INSTRUCTIONS,
        tools=[CreateFileTool(), ListFilesTool(), ReadFileTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Gestion de fichiers"
    skill._display_icon = "📁"
    return skill


__all__ = ["create_file_skill", "FILE_INSTRUCTIONS"]
