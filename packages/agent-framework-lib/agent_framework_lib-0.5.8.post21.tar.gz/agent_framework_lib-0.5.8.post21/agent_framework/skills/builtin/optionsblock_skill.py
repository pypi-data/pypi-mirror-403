"""
Options Block Skill - Clickable options generation capability.

This skill provides the ability to present users with clickable options
for simple single-question scenarios. Options are rendered as buttons
that users can click to respond.

Note: This is a UI-only skill with no associated tools - it provides
instructions for generating optionsblock JSON that the frontend renders.
"""

from ..base import Skill, SkillMetadata, SkillCategory


OPTIONSBLOCK_INSTRUCTIONS = """
## Options Block Instructions

## 🚨 CRITICAL: USE OPTIONSBLOCK EVERYWHERE!

Options blocks are the **DEFAULT way to interact with users**. They make conversations faster, 
clearer, and more user-friendly. **Use them as often as possible!**

**Golden Rule**: If you're asking the user ANYTHING, use an optionsblock.

---

## ✅ ALWAYS Use Optionsblock When...

You MUST use an optionsblock in these situations:

1. **ANY question to the user** - Yes/no, multiple choice, or even open-ended with suggestions
2. **ANY offer to do something** - "Would you like...", "Should I...", "I can..."
3. **ANY completion of a task** - Offer next steps
4. **ANY time you're waiting for user input** - Don't leave them hanging
5. **ANY time you mention multiple options in text** - Convert to clickable buttons
6. **EVEN when you're not sure** - Better to offer options than not!

### Mandatory Trigger Phrases

If you use ANY of these phrases, you MUST follow with an optionsblock:

| Phrase | Action Required |
|--------|-----------------|
| "Would you like..." | Add optionsblock with Yes/No or specific options |
| "Do you want..." | Add optionsblock with Yes/No or specific options |
| "Should I..." | Add optionsblock with Yes/No |
| "Let me know if..." | Add optionsblock with relevant options |
| "I can help you with..." | Add optionsblock listing the options |
| "Here are your options..." | Add optionsblock with the options |
| "What would you prefer..." | Add optionsblock with choices |
| "Is there anything else..." | Add optionsblock with Yes/No/specific suggestions |

---

## 📝 After EVERY Response

**Always end your responses with options when possible!**

After completing a task, offer:
```optionsblock
{
  "question": "What would you like to do next?",
  "options": [
    {"text": "✅ That's perfect, thanks!", "value": "done"},
    {"text": "🔄 Make some changes", "value": "modify"},
    {"text": "➕ Something else", "value": "other"}
  ]
}
```

After providing information, offer:
```optionsblock
{
  "question": "Was this helpful?",
  "options": [
    {"text": "👍 Yes, thanks!", "value": "helpful"},
    {"text": "🤔 I need more details", "value": "more_details"},
    {"text": "❓ I have another question", "value": "another_question"}
  ]
}
```

---

## 🔄 Before/After Conversion Examples

### ❌ BAD (No options):
"I can create a chart, generate a PDF, or help you with data analysis. Let me know what you'd like!"

### ✅ GOOD (With options):
"I can help you with several things:"

```optionsblock
{
  "question": "What would you like me to do?",
  "options": [
    {"text": "📊 Create a chart", "value": "create_chart"},
    {"text": "📄 Generate a PDF", "value": "generate_pdf"},
    {"text": "📈 Data analysis", "value": "data_analysis"},
    {"text": "🤔 Something else", "value": "other"}
  ]
}
```

---

### ❌ BAD (Question without options):
"Would you like me to save this as a PDF?"

### ✅ GOOD (Question with options):
```optionsblock
{
  "question": "Would you like me to save this as a PDF?",
  "options": [
    {"text": "Yes, save as PDF", "value": "yes_pdf"},
    {"text": "No, just show it", "value": "no_display"},
    {"text": "Save in a different format", "value": "other_format"}
  ]
}
```

---

### ❌ BAD (Task completion without next steps):
"Done! I've created the chart for you."

### ✅ GOOD (Task completion with next steps):
"Done! I've created the chart for you."

```optionsblock
{
  "question": "What's next?",
  "options": [
    {"text": "💾 Save as image", "value": "save_image"},
    {"text": "📄 Add to PDF", "value": "add_to_pdf"},
    {"text": "✏️ Modify the chart", "value": "modify"},
    {"text": "✅ That's all", "value": "done"}
  ]
}
```

---

## ⚠️ Anti-Patterns (What NOT to Do)

### ❌ DON'T: Ask questions without options
"Do you want me to continue?"  
→ Always add Yes/No optionsblock!

### ❌ DON'T: List options in text only
"You can choose A, B, or C."  
→ Convert to clickable optionsblock!

### ❌ DON'T: End without next steps
"Here's your result."  
→ Add "What's next?" optionsblock!

### ❌ DON'T: Use vague prompts
"Let me know what you think."  
→ Add specific feedback options!

---

## 📋 Formatting Requirements

**You MUST use a fenced code block with triple backticks and the language identifier `optionsblock`.**

### Options Block Structure

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `question` | string | No | Question text displayed above options |
| `options` | array | Yes | Array of option objects |
| `id` | string | No | Unique identifier for tracking |

### Option Object Structure

Each option in the `options` array must have:
- `text` (string): The text displayed on the button (can include emojis!)
- `value` (string): The value sent back when clicked

### CRITICAL: JSON Validity

- **NO trailing commas** after the last item in arrays or objects
- All strings must be in double quotes
- Property names must be in double quotes

**WRONG (trailing comma):**
```json
{
  "options": [
    {"text": "Yes", "value": "yes"},
    {"text": "No", "value": "no"},
  ]
}
```

**CORRECT:**
```json
{
  "options": [
    {"text": "Yes", "value": "yes"},
    {"text": "No", "value": "no"}
  ]
}
```

---

## 🎯 Common Patterns

### Simple Yes/No:
```optionsblock
{
  "question": "Would you like to continue?",
  "options": [
    {"text": "✅ Yes", "value": "yes"},
    {"text": "❌ No", "value": "no"}
  ]
}
```

### Multiple Actions:
```optionsblock
{
  "question": "What would you like to do?",
  "options": [
    {"text": "📊 View chart", "value": "view_chart"},
    {"text": "📥 Download", "value": "download"},
    {"text": "✏️ Edit", "value": "edit"},
    {"text": "🗑️ Delete", "value": "delete"}
  ]
}
```

### Feedback:
```optionsblock
{
  "question": "How was this response?",
  "options": [
    {"text": "👍 Helpful", "value": "helpful"},
    {"text": "👎 Not helpful", "value": "not_helpful"},
    {"text": "🤔 Needs more detail", "value": "more_detail"}
  ]
}
```

### Best Practices

1. **Keep options concise** - Button text should be short and clear
2. **Limit number of options** - 2-5 options work best
3. **Use emojis** - They help distinguish options visually
4. **Always include an escape hatch** - "Something else" or "Cancel"
5. **Use descriptive values** - Values should be meaningful for processing
"""


def create_optionsblock_skill() -> Skill:
    """
    Create the options block generation skill.

    This skill provides instructions for generating clickable options.
    It has no associated tools - options are rendered by the UI from JSON.

    Returns:
        Skill instance for options block generation
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="optionsblock",
            description="Generate clickable option buttons for user interaction. USE AS OFTEN AS POSSIBLE! Always offer options after questions, task completions, and when presenting choices.",
            trigger_patterns=[
                "options",
                "choices",
                "select",
                "buttons",
                "yes or no",
                "choose",
                "pick one",
                "which option",
                "confirmation",
            ],
            category=SkillCategory.UI,
            version="1.0.0",
        ),
        instructions=OPTIONSBLOCK_INSTRUCTIONS,
        tools=[],  # UI-only skill, no tools
        dependencies=[],
        config={},
    )
    skill._display_name = "Options de réponses"
    skill._display_icon = "🔘"
    return skill


__all__ = ["create_optionsblock_skill", "OPTIONSBLOCK_INSTRUCTIONS"]
