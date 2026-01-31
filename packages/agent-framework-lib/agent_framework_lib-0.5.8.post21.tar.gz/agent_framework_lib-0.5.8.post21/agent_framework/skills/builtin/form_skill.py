"""
Form Skill - Form generation capability.

This skill provides the ability to generate interactive forms for gathering
structured information from users. Forms are rendered as JSON with a
formDefinition structure that the UI interprets.

Note: This is a UI-only skill with no associated tools - it provides
instructions for generating form JSON that the frontend renders.
"""

from ..base import Skill, SkillMetadata, SkillCategory


FORM_INSTRUCTIONS = """
## Form Generation Instructions

You can present interactive forms to users to gather structured information.
Forms are defined using a JSON structure with a `formDefinition` key.

### When to Use Forms
- Collecting multiple pieces of information at once
- Gathering structured data (emails, numbers, selections)
- Creating surveys or questionnaires
- User registration or profile updates

### Form Definition Structure

To present a form, output a JSON object with this structure:

```json
{
  "formDefinition": {
    "title": "Form Title",
    "description": "Optional description above the form",
    "fields": [...],
    "submitButton": {"text": "Submit"}
  }
}
```

### Field Types

Each field in the `fields` array must have:
- `name` (string): Unique identifier for the field
- `label` (string): Display label for the user
- `fieldType` (string): Type of input field

**Supported Field Types:**

| Type | Description | Extra Properties |
|------|-------------|------------------|
| `text` | Single-line text input | `placeholder` |
| `number` | Numeric input | `min`, `max`, `step` |
| `email` | Email address input | `placeholder` |
| `password` | Masked password input | `placeholder` |
| `textarea` | Multi-line text | `rows`, `placeholder` |
| `select` | Dropdown list | `options` (required) |
| `checkbox` | Single checkbox | `defaultValue` (boolean) |
| `radio` | Radio button group | `options` (required) |
| `date` | Date picker | - |

### Field Properties

**Common properties (all field types):**
- `placeholder` (string): Placeholder text
- `required` (boolean): Whether field is mandatory
- `defaultValue`: Default value for the field

**For `select` and `radio` fields:**
```json
"options": [
  {"value": "option1", "text": "Display Text 1"},
  {"value": "option2", "text": "Display Text 2"}
]
```

**For `number` fields:**
- `min` (number): Minimum allowed value
- `max` (number): Maximum allowed value
- `step` (number): Increment step

**For `textarea` fields:**
- `rows` (number): Number of visible text lines

### Complete Example

```json
{
  "formDefinition": {
    "title": "User Feedback Form",
    "description": "Please provide your valuable feedback.",
    "fields": [
      {
        "name": "user_email",
        "label": "Your Email:",
        "fieldType": "email",
        "placeholder": "name@example.com",
        "required": true
      },
      {
        "name": "rating",
        "label": "Overall Rating:",
        "fieldType": "select",
        "options": [
          {"value": "5", "text": "Excellent"},
          {"value": "4", "text": "Good"},
          {"value": "3", "text": "Average"},
          {"value": "2", "text": "Fair"},
          {"value": "1", "text": "Poor"}
        ],
        "required": true
      },
      {
        "name": "feedback_type",
        "label": "Feedback Type:",
        "fieldType": "radio",
        "options": [
          {"value": "bug", "text": "Bug Report"},
          {"value": "feature", "text": "Feature Request"},
          {"value": "general", "text": "General Feedback"}
        ]
      },
      {
        "name": "comments",
        "label": "Additional Comments:",
        "fieldType": "textarea",
        "rows": 4,
        "placeholder": "Let us know your thoughts..."
      },
      {
        "name": "subscribe_newsletter",
        "label": "Subscribe to our newsletter",
        "fieldType": "checkbox",
        "defaultValue": true
      }
    ],
    "submitButton": {
      "text": "Send Feedback"
    }
  }
}
```

### Best Practices

1. **Use descriptive labels** - Make it clear what information is needed
2. **Mark required fields** - Set `required: true` for mandatory fields
3. **Provide placeholders** - Help users understand expected format
4. **Use appropriate field types** - Email for emails, number for numbers, etc.
5. **Group related fields** - Keep the form logical and easy to follow
6. **Limit form length** - Break long forms into multiple steps if needed

### Important Notes

- Only use `formDefinition` JSON when you need to collect structured data
- For simple yes/no questions, use `optionsblock` instead
- The user's form submission will be sent back as their next message
- Validate that all required fields have appropriate types
"""


def create_form_skill() -> Skill:
    """
    Create the form generation skill.

    This skill provides instructions for generating interactive forms.
    It has no associated tools - forms are rendered by the UI from JSON.

    Returns:
        Skill instance for form generation
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="form",
            description="Generate interactive forms for collecting structured user input",
            trigger_patterns=[
                "form",
                "input",
                "survey",
                "questionnaire",
                "collect information",
                "gather data",
                "user input",
                "registration",
                "signup",
            ],
            category=SkillCategory.UI,
            version="1.0.0",
        ),
        instructions=FORM_INSTRUCTIONS,
        tools=[],  # UI-only skill, no tools
        dependencies=[],
        config={},
    )
    skill._display_name = "Création de formulaires"
    skill._display_icon = "📝"
    return skill


__all__ = ["create_form_skill", "FORM_INSTRUCTIONS"]
