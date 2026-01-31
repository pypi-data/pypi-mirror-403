"""Core Pydantic models for the agent framework."""

import random
import re

from pydantic import BaseModel, field_validator


class Tag(BaseModel):
    """Represents an agent tag with name and color.

    Tags are used to categorize and visually identify agents in the UI.
    Each tag has a name and an associated hex color.

    Attributes:
        name: The display name of the tag (non-empty, trimmed).
        color: The hex color code in #RGB or #RRGGBB format (normalized to uppercase).

    Example:
        >>> tag = Tag(name="production", color="#FF5733")
        >>> tag = Tag.from_name("development")  # Random color generated
    """

    name: str
    color: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that the tag name is non-empty and trim whitespace.

        Args:
            v: The tag name to validate.

        Returns:
            The trimmed tag name.

        Raises:
            ValueError: If the tag name is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate that the color is a valid hex color format.

        Accepts both #RGB (3 hex digits) and #RRGGBB (6 hex digits) formats.
        The color is normalized to uppercase.

        Args:
            v: The hex color string to validate.

        Returns:
            The validated color string in uppercase.

        Raises:
            ValueError: If the color format is invalid.
        """
        pattern = r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid hex color format: {v}. Expected #RGB or #RRGGBB")
        return v.upper()

    @classmethod
    def generate_random_color(cls) -> str:
        """Generate a random hex color in #RRGGBB format.

        Returns:
            A random hex color string (e.g., "#A3F2C1").
        """
        return f"#{random.randint(0, 0xFFFFFF):06X}"

    @classmethod
    def from_name(cls, name: str) -> "Tag":
        """Create a tag with a random color.

        This is a convenience method for creating tags when only the name
        is known and a random color should be assigned.

        Args:
            name: The tag name.

        Returns:
            A new Tag instance with the given name and a random color.
        """
        return cls(name=name, color=cls.generate_random_color())
