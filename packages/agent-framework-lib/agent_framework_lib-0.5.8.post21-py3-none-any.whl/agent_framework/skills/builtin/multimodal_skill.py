"""
Multimodal Skill - Image analysis capability.

This skill provides the ability to analyze images using multimodal AI capabilities.
It wraps the ImageAnalysisTool with detailed instructions for image analysis,
description, question answering, and OCR text extraction.

Note: The ImageAnalysisTool requires a FileStorageManager to be provided at runtime.
This skill provides the instructions and metadata, but the tool must be configured
separately when the agent is initialized with file storage.
"""

from ..base import Skill, SkillMetadata, SkillCategory


MULTIMODAL_INSTRUCTIONS = """
## Image Analysis Instructions

You can analyze images using multimodal AI capabilities. This includes:
- Image description and scene analysis
- Question answering about image content
- OCR text extraction from images
- Object detection and recognition

### Prerequisites

Image analysis requires:
1. The `ENABLE_MULTIMODAL_ANALYSIS` environment variable set to `true`
2. A valid OpenAI API key (for GPT-4 Vision)
3. Images stored in the file storage system

### Available Capabilities

1. **Image Description** - Get detailed descriptions of image content
2. **Question Answering** - Ask specific questions about images
3. **OCR Text Extraction** - Extract text visible in images
4. **Object Detection** - Identify objects in images
5. **Scene Analysis** - Understand the overall scene and context

### Supported Image Formats

- JPEG/JPG
- PNG
- GIF
- WebP
- BMP
- TIFF

### How to Analyze Images

1. **Get the file_id**: When a user uploads an image, you receive a file_id
2. **Use analyze_image**: Call the analysis function with the file_id
3. **Provide context**: Optionally include a specific analysis prompt

### Analysis Methods

#### describe_image(file_id)
Get a detailed description of the image content.

**Example:**
```python
description = await describe_image("file_abc123")
# Returns: "The image shows a sunset over a mountain range..."
```

#### answer_about_image(file_id, question)
Answer specific questions about an image.

**Example:**
```python
answer = await answer_about_image("file_abc123", "What color is the car?")
# Returns: "The car in the image is red."
```

#### extract_text_from_image(file_id)
Extract all visible text from an image using OCR.

**Example:**
```python
text = await extract_text_from_image("file_abc123")
# Returns: "STOP\nSpeed Limit 35\nMain Street"
```

#### analyze_image(file_id, analysis_prompt)
Perform custom analysis with a specific prompt.

**Example:**
```python
result = await analyze_image("file_abc123", "Count the number of people in this image")
# Returns: ImageAnalysisResult with description, objects, etc.
```

### Best Practices

1. **Be specific**: Provide clear analysis prompts for better results
2. **Check file type**: Ensure the file is a supported image format
3. **Handle errors**: Analysis may fail if multimodal is disabled or API unavailable
4. **Use appropriate method**: Choose the right method for your task:
   - General understanding → `describe_image`
   - Specific questions → `answer_about_image`
   - Text extraction → `extract_text_from_image`
   - Custom analysis → `analyze_image`

### Error Handling

Common errors and solutions:
- "Multimodal analysis is not enabled" → Set ENABLE_MULTIMODAL_ANALYSIS=true
- "File type not supported" → Ensure file is a supported image format
- "Failed to retrieve file" → Check that file_id is valid
- "Vision API error" → Check OpenAI API key and quota

### Limitations

- Requires OpenAI API with GPT-4 Vision access
- Large images may take longer to process
- Some complex scenes may have reduced accuracy
- OCR works best with clear, high-contrast text
"""


def create_multimodal_skill() -> Skill:
    """
    Create the multimodal image analysis skill.

    Note: This skill does not include tools directly because ImageAnalysisTool
    requires a FileStorageManager at initialization. The tools should be
    configured separately when the agent is set up with file storage.

    Returns:
        Skill instance for multimodal image analysis
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="multimodal",
            description="Analyze images using AI vision (describe, OCR, question answering)",
            trigger_patterns=[
                "image",
                "analyze image",
                "describe image",
                "ocr",
                "text extraction",
                "image analysis",
                "what's in this image",
                "picture",
                "photo",
                "screenshot",
                "vision",
            ],
            category=SkillCategory.MULTIMODAL,
            version="1.0.0",
        ),
        instructions=MULTIMODAL_INSTRUCTIONS,
        tools=[],  # Tools require FileStorageManager, configured at agent level
        dependencies=[],
        config={
            "requires_file_storage": True,
            "requires_env": ["ENABLE_MULTIMODAL_ANALYSIS", "OPENAI_API_KEY"],
        },
    )
    skill._display_name = "Analyse d'images"
    skill._display_icon = "🖼️"
    return skill


__all__ = ["create_multimodal_skill", "MULTIMODAL_INSTRUCTIONS"]
