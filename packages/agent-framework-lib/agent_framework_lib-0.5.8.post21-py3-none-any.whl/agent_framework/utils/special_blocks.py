import json
import re
import logging
from typing import Tuple, List

from agent_framework.core.agent_interface import (
    OptionsBlockOutputPart,
    FormDefinitionOutputPart,
    ImageOutputPart,
)
from agent_framework.utils.source_detector import SourceDetector

logger = logging.getLogger(__name__)

# Singleton instance for source detection
_source_detector = SourceDetector()


def _create_image_output_part(image_data: dict) -> ImageOutputPart:
    """
    Create an ImageOutputPart with automatic filestorage detection.
    
    Args:
        image_data: Dictionary containing image properties (url, alt, caption, etc.)
        
    Returns:
        ImageOutputPart with filestorage auto-populated from URL detection
    """
    url = image_data.get("url", "")
    
    # Auto-detect filestorage if not provided
    filestorage = image_data.get("filestorage")
    if filestorage is None and url:
        storage_info = _source_detector.detect(url)
        filestorage = storage_info.type.value if hasattr(storage_info.type, 'value') else str(storage_info.type)
    
    return ImageOutputPart(
        url=url,
        alt=image_data.get("alt"),
        caption=image_data.get("caption"),
        width=image_data.get("width"),
        height=image_data.get("height"),
        filename=image_data.get("filename"),
        filestorage=filestorage,
    )


def _try_parse_raw_json_with_key(text: str, key: str) -> Tuple[dict, int, int] | None:
    """
    Try to find and parse a raw JSON object containing a specific key in the text.
    
    Returns (parsed_json, start_index, end_index) or None if not found.
    """
    # Look for {"key" or { "key" patterns (with optional whitespace)
    pattern = rf'\{{\s*"{key}"'
    match = re.search(pattern, text)
    if not match:
        return None
    
    start_idx = match.start()
    
    # Find the matching closing brace by counting braces
    brace_count = 0
    end_idx = start_idx
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue
        if char == '\\' and in_string:
            escape_next = True
            continue
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if brace_count != 0:
        return None
    
    json_str = text[start_idx:end_idx]
    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, dict) and key in parsed:
            return parsed, start_idx, end_idx
    except json.JSONDecodeError:
        pass
    
    return None


def parse_special_blocks_from_text(text: str) -> Tuple[str, List]:
    """
    Parse optionsblock, formDefinition, and image code blocks from text and return cleaned text + parts.

    Returns a tuple of (cleaned_text, parts) where parts contains instances of
    FormDefinitionOutputPart, OptionsBlockOutputPart, and ImageOutputPart.
    
    Supports:
    - Standard ```json code blocks
    - Raw JSON objects without code block markers (fallback)
    """
    if not text:
        return text, []

    special_parts = []
    cleaned_text = text
    found_form_in_code_block = False
    found_image_in_code_block = False
    image_json_blocks_to_remove = []

    # Pattern to match ```json blocks
    json_formdefinition_pattern = r"```json\s*\n(.*?)\n```"
    json_matches = re.findall(json_formdefinition_pattern, text, re.DOTALL)

    for match in json_matches:
        try:
            json_data = json.loads(match.strip())
            if isinstance(json_data, dict) and "formDefinition" in json_data:
                form_part = FormDefinitionOutputPart(definition=json_data["formDefinition"])
                special_parts.append(form_part)
                found_form_in_code_block = True
            elif isinstance(json_data, dict) and "image" in json_data:
                image_data = json_data["image"]
                if isinstance(image_data, dict) and "url" in image_data:
                    image_part = _create_image_output_part(image_data)
                    special_parts.append(image_part)
                    found_image_in_code_block = True
                    image_json_blocks_to_remove.append(match)
            else:
                continue
        except json.JSONDecodeError:
            continue
    
    # Fallback: try to find raw JSON with formDefinition if not found in code blocks
    if not found_form_in_code_block:
        result = _try_parse_raw_json_with_key(text, "formDefinition")
        if result:
            json_data, start_idx, end_idx = result
            form_part = FormDefinitionOutputPart(definition=json_data["formDefinition"])
            special_parts.append(form_part)
            # Remove the raw JSON from cleaned text
            cleaned_text = cleaned_text[:start_idx] + cleaned_text[end_idx:]
            logger.debug(f"Parsed raw formDefinition JSON (no code block markers)")

    # Fallback: try to find raw JSON with image if not found in code blocks
    if not found_image_in_code_block:
        # Find all raw image JSON blocks
        while True:
            result = _try_parse_raw_json_with_key(cleaned_text, "image")
            if not result:
                break
            json_data, start_idx, end_idx = result
            image_data = json_data["image"]
            if isinstance(image_data, dict) and "url" in image_data:
                image_part = _create_image_output_part(image_data)
                special_parts.append(image_part)
                cleaned_text = cleaned_text[:start_idx] + cleaned_text[end_idx:]
                logger.debug("Parsed raw image JSON (no code block markers)")
            else:
                break

    # Pattern to match ```optionsblock...``` blocks
    optionsblock_pattern = r"```optionsblock\s*\n(.*?)\n```"
    optionsblock_matches = re.findall(optionsblock_pattern, text, re.DOTALL)
    found_options_in_code_block = False

    for match in optionsblock_matches:
        try:
            options_data = json.loads(match.strip())
            options_part = OptionsBlockOutputPart(definition=options_data)
            special_parts.append(options_part)
            found_options_in_code_block = True
        except json.JSONDecodeError:
            continue
    
    # Fallback 1: try to find "optionsblock{...}" format (word followed by JSON)
    if not found_options_in_code_block:
        # Pattern: optionsblock followed by JSON object (with optional whitespace)
        inline_optionsblock_pattern = r'optionsblock\s*(\{.*?\})\s*(?=\n|$|[^\}])'
        
        # More robust: find "optionsblock" and then extract the JSON
        optionsblock_inline_match = re.search(r'optionsblock\s*(\{)', cleaned_text)
        if optionsblock_inline_match:
            json_start = optionsblock_inline_match.start(1)
            # Find matching closing brace
            brace_count = 0
            json_end = json_start
            in_string = False
            escape_next = False
            
            for i, char in enumerate(cleaned_text[json_start:], start=json_start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if brace_count == 0:
                json_str = cleaned_text[json_start:json_end]
                try:
                    options_data = json.loads(json_str)
                    if isinstance(options_data, dict) and "options" in options_data:
                        options_part = OptionsBlockOutputPart(definition=options_data)
                        special_parts.append(options_part)
                        found_options_in_code_block = True
                        # Remove the entire "optionsblock{...}" from cleaned text
                        full_start = optionsblock_inline_match.start()
                        cleaned_text = cleaned_text[:full_start] + cleaned_text[json_end:]
                        logger.debug("Parsed inline optionsblock{...} format")
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse inline optionsblock JSON: {e}")
    
    # Fallback 2: try to find raw JSON with "optionsblock" key wrapper
    if not found_options_in_code_block:
        result = _try_parse_raw_json_with_key(cleaned_text, "optionsblock")
        if result:
            json_data, start_idx, end_idx = result
            options_part = OptionsBlockOutputPart(definition=json_data["optionsblock"])
            special_parts.append(options_part)
            cleaned_text = cleaned_text[:start_idx] + cleaned_text[end_idx:]
            logger.debug(f"Parsed raw optionsblock JSON (no code block markers)")

    # Remove all optionsblock code blocks from the text
    cleaned_text = re.sub(optionsblock_pattern, "", cleaned_text, flags=re.DOTALL)

    # Remove JSON blocks that contain formDefinition
    for match in json_matches:
        try:
            json_data = json.loads(match.strip())
            if isinstance(json_data, dict) and "formDefinition" in json_data:
                block_pattern = r"```json\s*\n" + re.escape(match) + r"\n```"
                cleaned_text = re.sub(block_pattern, "", cleaned_text, flags=re.DOTALL)
        except json.JSONDecodeError:
            continue

    # Remove JSON blocks that contain image
    for match in image_json_blocks_to_remove:
        block_pattern = r"```json\s*\n" + re.escape(match) + r"\n```"
        cleaned_text = re.sub(block_pattern, "", cleaned_text, flags=re.DOTALL)

    # Clean up extra whitespace
    cleaned_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_text).strip()

    return cleaned_text, special_parts
