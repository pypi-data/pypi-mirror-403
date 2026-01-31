import abc
import base64
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# Define a type alias for the content part, which can be text or an image dictionary
# Following OpenAI/AutoGen structure: {"type": "text", "text": "..."} or {"type": "image_url", "image_url": {"url": "..."}}
# For simplicity in the interface, we accept Dict for images, specific validation happens in server/agent.
# AgentInputContent = List[Union[str, Dict[str, Any]]] # OLD TYPE, to be replaced


# --- Agent Configuration Model ---
class AgentConfig(BaseModel):
    """
    Configuration settings for agent behavior that can be set per session.
    All fields are optional to maintain backward compatibility.
    """

    # Model parameters
    temperature: float | None = Field(
        None, ge=0.0, le=2.0, description="Controls randomness (0.0-2.0)"
    )
    max_tokens: int | None = Field(None, ge=1, le=100000, description="Maximum tokens in response")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float | None = Field(
        None, ge=-2.0, le=2.0, description="Reduces repetition of frequent tokens"
    )
    presence_penalty: float | None = Field(
        None, ge=-2.0, le=2.0, description="Reduces repetition of any tokens"
    )
    stop_sequences: list[str] | None = Field(
        None, description="Custom stop sequences for response termination"
    )

    # Client behavior parameters
    timeout: int | None = Field(None, ge=1, le=600, description="Request timeout in seconds")
    max_retries: int | None = Field(None, ge=0, le=10, description="Maximum retry attempts")
    model_selection: str | None = Field(None, description="Override default model for session")

    # Response preferences
    response_format: str | None = Field(None, description="Preferred response format hints")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Top_p must be between 0.0 and 1.0")
        return v


# --- Input Part Models ---
class TextInputPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageUrlInputPart(BaseModel):
    type: Literal["image_url"] = "image_url"
    # Enhanced to support both file uploads and URLs with MIME type
    image_url: dict[str, str] | None = Field(
        None, json_schema_extra={"example": {"url": "data:image/png;base64,..."}}
    )
    file: bytes | None = Field(None, description="Binary file content")
    url: str | None = Field(None, description="Image URL")
    mime_type: str | None = Field(None, description="MIME type (e.g., image/png, image/jpeg)")

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_source(cls, data: Any) -> Any:
        """Ensure at least one of image_url, file, or url is present."""
        if isinstance(data, dict):
            if not ("file" in data or "url" in data or "image_url" in data):
                raise ValueError("At least one of image_url, file, or url must be present")
        return data


class FileDataInputPart(BaseModel):
    type: Literal["file_data"] = "file_data"
    filename: str
    content_base64: str  # Base64 encoded file content
    mime_type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_source(cls, data: Any) -> Any:
        """Ensure content_base64 is present."""
        if isinstance(data, dict):
            if "content_base64" not in data:
                raise ValueError("content_base64 must be present")
        return data

    def set_binary_content(self, binary_data: bytes):
        """Helper method to set binary content as base64"""
        self.content_base64 = base64.b64encode(binary_data).decode("utf-8")

    def get_binary_content(self) -> bytes | None:
        """Helper method to get binary content from base64"""
        if self.content_base64 is None:
            return None
        try:
            return base64.b64decode(self.content_base64)
        except Exception:
            return None


# StructuredAgentInput will be defined after all part classes

# --- Output Part Models ---
# These models represent the various types of structured content an agent can produce.


class TextOutputPart(BaseModel):
    type: Literal["text_output"] = "text_output"  # Changed from "text" to avoid conflict with input
    text: str  # Can be markdown, plain text, etc.


class TextOutputStreamPart(BaseModel):
    type: Literal["text_output_stream"] = "text_output_stream"
    text: str  # Streaming content with special markers


class JsonOutputPart(BaseModel):
    type: Literal["json_data"] = "json_data"
    data: Any  # Parsed JSON data (Python dict/list)
    filename: str | None = None  # Optional filename if it represents a savable JSON file


class YamlOutputPart(BaseModel):
    type: Literal["yaml_data"] = "yaml_data"
    data: Any  # Parsed YAML data (Python dict/list) or raw YAML string
    filename: str | None = None


class FileContentOutputPart(BaseModel):  # Renamed from FileDataOutputPart for clarity
    type: Literal["file_content_output"] = "file_content_output"  # Changed from "file_data"
    filename: str
    content_base64: str  # Base64 encoded file content
    mime_type: str | None = None


class FileReferenceInputPart(BaseModel):
    """Reference to a file stored in the file storage system"""

    type: Literal["file_reference"] = "file_reference"
    file_id: str  # Reference to stored file
    filename: str | None = None  # Optional filename for convenience


class FileReferenceOutputPart(BaseModel):
    """Reference to a file stored in the file storage system"""

    type: Literal["file_reference_output"] = "file_reference_output"
    file_id: str
    filename: str
    mime_type: str | None = None
    download_url: str | None = None  # API endpoint to download
    size_bytes: int | None = None  # File size information


# Define the Union types after all classes are defined
AgentInputPartUnion = Union[
    TextInputPart, ImageUrlInputPart, FileDataInputPart, FileReferenceInputPart
]


class StructuredAgentInput(BaseModel):
    """
    Represents structured input to the agent, potentially including a main query
    and a list of various content parts.
    """

    query: str | None = None  # Optional main text query.
    # If parts also contain text, agent logic should decide how to combine/prioritize.
    parts: list[AgentInputPartUnion] = Field(default_factory=list)
    system_prompt: str | None = None  # Optional system prompt to set or override for this session
    agent_config: AgentConfig | None = None  # Optional configuration settings for agent behavior
    # # session_id is handled by the server and passed directly to agent methods, not part of this model.


class MediaPartType(BaseModel):
    """New output part type for images and videos from image detection"""

    type: Literal["media"] = "media"
    name: str
    mime_type: str
    content: str | None = Field(None, description="Binary content as base64 string (optional)")
    url: str | None = Field(None, description="Media URL (optional)")

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_source(cls, data: Any) -> Any:
        """Ensure either content or url is present."""
        if isinstance(data, dict):
            if not ("content" in data or "url" in data):
                raise ValueError("Either content or url must be present")
        return data

    def set_binary_content(self, binary_data: bytes):
        """Helper method to set binary content as base64"""
        self.content = base64.b64encode(binary_data).decode("utf-8")

    def get_binary_content(self) -> bytes | None:
        """Helper method to get binary content from base64"""
        if self.content is None:
            return None
        try:
            return base64.b64decode(self.content)
        except Exception:
            return None


class MermaidOutputPart(BaseModel):
    type: Literal["mermaid_diagram"] = "mermaid_diagram"
    definition: str  # The Mermaid syntax string
    width: str | None = None  # e.g., "600px", "100%"
    height: str | None = None  # e.g., "400px", "auto"
    max_width: str | None = None  # e.g., "800px"
    max_height: str | None = None  # e.g., "600px"


class ChartJsOutputPart(BaseModel):
    type: Literal["chart_js"] = "chart_js"
    config: dict[str, Any]  # The Chart.js configuration object
    width: str | None = None  # Suggestion for container/canvas style
    height: str | None = None
    max_width: str | None = None
    max_height: str | None = None


class TableDataOutputPart(BaseModel):
    type: Literal["table_data"] = "table_data"
    caption: str | None = None
    headers: list[str]
    rows: list[list[Any]]


class FormDefinitionOutputPart(BaseModel):
    type: Literal["form_definition"] = "form_definition"
    definition: dict[str, Any]  # The formDefinition object as expected by the frontend


class OptionsBlockOutputPart(BaseModel):
    type: Literal["options_block"] = "options_block"
    definition: dict[str, Any]  # The optionsblock JSON object as expected by the frontend


class ImageOutputPart(BaseModel):
    """Output part for displaying images from URLs in chat responses."""

    type: Literal["image"] = "image"
    url: str = Field(..., description="URL of the image to display")
    alt: str | None = Field(None, description="Alt text for accessibility")
    caption: str | None = Field(None, description="Caption displayed below the image")
    width: str | None = Field(None, description="CSS width (e.g., '400px', '100%')")
    height: str | None = Field(None, description="CSS height (e.g., '300px', 'auto')")
    filename: str | None = Field(
        None, description="Filename for download (derived from URL if not provided)"
    )
    filestorage: str | None = Field(
        None, description="Storage type: web, s3, gcp, azure, local, minio, data_uri, unknown"
    )


class FileDownloadLinkOutputPart(BaseModel):
    type: Literal["file_download_link"] = "file_download_link"
    file_id: str
    label: str
    action: Literal["download", "preview"] = "download"
    icon: str | None = None
    metadata: dict[str, Any] | None = None


class ToolRequestOutputPart(BaseModel):
    """Output part representing a tool invocation request."""

    type: Literal["tool_request"] = "tool_request"
    tool_name: str
    arguments: dict[str, Any]
    call_id: str
    timestamp: str
    friendly_name: str | None = None
    icon: str | None = None


class ToolResultOutputPart(BaseModel):
    """Output part representing a tool execution result."""

    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    result_content: str
    is_error: bool = False
    call_id: str
    timestamp: str
    friendly_name: str | None = None
    icon: str | None = None


class TechnicalDetails(BaseModel):
    """Technical details for Elasticsearch storage only.

    This model captures raw technical data about tool/function executions
    for debugging and analysis purposes. It is stored in Elasticsearch
    but stripped from responses sent to the frontend.

    Note: raw_result is stored as a JSON string to ensure ES compatibility.
    When creating TechnicalDetails, you can pass any value for raw_result
    and it will be automatically serialized to JSON string via the validator.
    """

    function_name: str = Field(..., description="Name of the executed function/tool")
    arguments: dict[str, Any] = Field(..., description="Arguments passed to the function")
    raw_result: str = Field(..., description="Raw result from the function execution (JSON string)")
    execution_time_ms: int = Field(..., ge=0, description="Execution time in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp of execution")
    status: Literal["success", "error"] = Field(..., description="Execution status")
    error_message: str | None = Field(None, description="Error message if status is 'error'")

    @field_validator("raw_result", mode="before")
    @classmethod
    def serialize_raw_result(cls, v: Any) -> str:
        """Serialize raw_result to JSON string for ES compatibility.

        This ensures that any value passed to raw_result (dict, list, str, etc.)
        is stored as a JSON string, which is compatible with ES text field mapping.
        """
        import json

        if isinstance(v, str):
            return v
        try:
            return json.dumps(v, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(v)


class ActivityOutputPart(BaseModel):
    """Output part representing an activity event with optional technical details.

    This model represents agent activities such as tool calls, skill loading,
    diagram generation, chart generation, etc. It includes:
    - User-friendly content for display in the frontend
    - UI rendering metadata (display_info) for frontend presentation
    - Technical details for Elasticsearch storage (stripped before sending to frontend)
    """

    type: Literal["activity"] = "activity"
    activity_type: str  # "tool_call", "skill_loading", "diagram_generation", "chart_generation"
    source: str  # Agent name: "socrate", "james", "llamaindex_agent"
    content: str | None = None  # User-friendly result text (markdown/plain text)
    timestamp: str  # ISO 8601 format

    # Optional fields for tool-related activities
    tools: list[dict[str, Any]] | None = None  # For tool_request: list of tool calls
    results: list[dict[str, Any]] | None = None  # For tool_result: list of results

    # UI rendering metadata (sent to frontend)
    display_info: dict[str, Any] | None = None

    # Technical data (stored in ES, NOT sent to frontend)
    technical_details: TechnicalDetails | None = None


def activity_dict_to_output_part(activity: dict[str, Any]) -> ActivityOutputPart:
    """Convert a raw activity dictionary to an ActivityOutputPart.

    Args:
        activity: Raw activity dictionary with keys like 'type', 'source', 'content', etc.

    Returns:
        ActivityOutputPart instance with fields populated from the dictionary.
        Missing optional fields are set to defaults.
    """
    # Handle technical_details conversion if present
    technical_details = None
    if "technical_details" in activity and activity["technical_details"] is not None:
        td = activity["technical_details"]
        if isinstance(td, TechnicalDetails):
            technical_details = td
        elif isinstance(td, dict):
            technical_details = TechnicalDetails(**td)

    return ActivityOutputPart(
        activity_type=activity.get("type", "activity"),
        source=activity.get("source", "unknown"),
        content=activity.get("content"),
        timestamp=activity.get("timestamp", datetime.now(timezone.utc).isoformat()),
        tools=activity.get("tools"),
        results=activity.get("results"),
        display_info=activity.get("display_info"),
        technical_details=technical_details,
    )


def output_part_to_activity_dict(part: ActivityOutputPart) -> dict[str, Any]:
    """Convert an ActivityOutputPart to a raw activity dictionary.

    Args:
        part: ActivityOutputPart instance to convert.

    Returns:
        Dictionary with activity data. Only includes non-None optional fields.
    """
    result: dict[str, Any] = {
        "type": part.activity_type,
        "source": part.source,
        "timestamp": part.timestamp,
    }
    if part.content is not None:
        result["content"] = part.content
    if part.tools is not None:
        result["tools"] = part.tools
    if part.results is not None:
        result["results"] = part.results
    if part.display_info is not None:
        result["display_info"] = part.display_info
    if part.technical_details is not None:
        result["technical_details"] = part.technical_details.model_dump()
    return result


AgentOutputPartUnion = Union[
    TextOutputPart,
    TextOutputStreamPart,
    JsonOutputPart,
    YamlOutputPart,
    FileContentOutputPart,
    FileReferenceOutputPart,
    MediaPartType,
    MermaidOutputPart,
    ChartJsOutputPart,
    TableDataOutputPart,
    FormDefinitionOutputPart,
    OptionsBlockOutputPart,
    FileDownloadLinkOutputPart,
    ImageOutputPart,
    ToolRequestOutputPart,
    ToolResultOutputPart,
    ActivityOutputPart,
]


def strip_technical_details(
    parts: list[dict[str, Any]] | list[ActivityOutputPart] | list[AgentOutputPartUnion],
) -> list[dict[str, Any]] | list[ActivityOutputPart] | list[AgentOutputPartUnion]:
    """Strip technical_details from ActivityOutputPart before sending to frontend.

    This function removes the technical_details field from any ActivityOutputPart
    in the parts list. Technical details contain raw function names, arguments,
    and execution data that should only be stored in Elasticsearch for debugging
    and analysis purposes, not sent to the frontend.

    The function handles three input types:
    1. List of dictionaries (raw parts data)
    2. List of ActivityOutputPart Pydantic models
    3. List of AgentOutputPartUnion (mixed part types)

    Args:
        parts: List of parts to process. Can be dicts, ActivityOutputPart models,
               or mixed AgentOutputPartUnion types.

    Returns:
        A new list with the same structure as input, but with technical_details
        removed from any ActivityOutputPart. Non-activity parts are preserved
        unchanged.

    Examples:
        >>> # With dict input
        >>> parts = [{"type": "activity", "technical_details": {...}, "content": "..."}]
        >>> stripped = strip_technical_details(parts)
        >>> "technical_details" in stripped[0]
        False

        >>> # With Pydantic model input
        >>> part = ActivityOutputPart(activity_type="tool_call", ...)
        >>> stripped = strip_technical_details([part])
        >>> stripped[0].technical_details is None
        True
    """
    if not parts:
        return parts

    result: list[Any] = []

    for part in parts:
        # Handle dict input
        if isinstance(part, dict):
            if part.get("type") == "activity" and "technical_details" in part:
                # Create a new dict without technical_details
                stripped = {k: v for k, v in part.items() if k != "technical_details"}
                result.append(stripped)
            else:
                result.append(part)

        # Handle ActivityOutputPart Pydantic model
        elif isinstance(part, ActivityOutputPart):
            if part.technical_details is not None:
                # Create a copy without technical_details
                stripped_part = ActivityOutputPart(
                    activity_type=part.activity_type,
                    source=part.source,
                    content=part.content,
                    timestamp=part.timestamp,
                    tools=part.tools,
                    results=part.results,
                    display_info=part.display_info,
                    technical_details=None,  # Explicitly set to None
                )
                result.append(stripped_part)
            else:
                result.append(part)

        # Handle other part types (pass through unchanged)
        else:
            result.append(part)

    return result


def consolidate_text_parts(
    parts: list[AgentOutputPartUnion] | list[dict[str, Any]],
) -> list[AgentOutputPartUnion] | list[dict[str, Any]]:
    """Consolidate consecutive TextOutputStreamPart into single TextOutputPart.

    This function merges consecutive text_output_stream parts into single text_output
    parts while preserving the chronological order with activity parts. This is used
    before storing parts in Elasticsearch to reduce noise in history.

    The function:
    1. Merges consecutive text_output_stream parts into one text_output
    2. Strips __STREAM_CHUNK__ and __STREAM_ACTIVITY__ markers from text
    3. Extracts special blocks (optionsblock, formDefinition, image) from text
    4. Preserves activity parts in their original position
    5. Maintains chronological order (text → activity → text)

    Args:
        parts: List of parts to consolidate. Can be Pydantic models or dicts.

    Returns:
        A new list with consecutive text streams consolidated into text_output parts,
        and special blocks extracted as separate parts.

    Example:
        Input:
            [text_output_stream("Hello"), text_output_stream(" world"), activity, text_output_stream("Done")]
        Output:
            [text_output("Hello world"), activity, text_output("Done")]
    """
    from ..utils.special_blocks import parse_special_blocks_from_text

    if not parts:
        return parts

    result: list[Any] = []
    pending_text: list[str] = []

    def flush_pending_text() -> None:
        """Flush accumulated text as a single TextOutputPart, extracting special blocks."""
        if pending_text:
            combined_text = "".join(pending_text)
            if combined_text.strip():  # Only add if there's actual content
                # Extract special blocks (optionsblock, formDefinition, image) from text
                # This prevents duplication when special blocks are also parsed at the end
                cleaned_text, special_parts = parse_special_blocks_from_text(combined_text)

                # Add cleaned text as TextOutputPart if there's content left
                if cleaned_text.strip():
                    if result and isinstance(result[0], dict):
                        result.append({"type": "text_output", "text": cleaned_text})
                    else:
                        result.append(TextOutputPart(text=cleaned_text))

                # Add extracted special blocks (OptionsBlockOutputPart, etc.)
                for special_part in special_parts:
                    result.append(special_part)

            pending_text.clear()

    for part in parts:
        # Handle dict input
        if isinstance(part, dict):
            part_type = part.get("type")

            if part_type == "text_output_stream":
                # Extract text and strip markers
                text = part.get("text", "")
                # Remove streaming markers
                if text.startswith("__STREAM_CHUNK__"):
                    text = text[len("__STREAM_CHUNK__") :]
                elif text.startswith("__STREAM_ACTIVITY__"):
                    # Skip activity markers in text_output_stream (they're duplicates)
                    continue
                if text:
                    pending_text.append(text)

            elif part_type == "text_output":
                # Regular text_output - add to pending
                text = part.get("text", "")
                if text:
                    pending_text.append(text)

            else:
                # Non-text part (activity, etc.) - flush pending text first
                flush_pending_text()
                result.append(part)

        # Handle Pydantic models
        elif isinstance(part, TextOutputStreamPart):
            text = part.text
            # Remove streaming markers
            if text.startswith("__STREAM_CHUNK__"):
                text = text[len("__STREAM_CHUNK__") :]
            elif text.startswith("__STREAM_ACTIVITY__"):
                # Skip activity markers (they're duplicates of ActivityOutputPart)
                continue
            if text:
                pending_text.append(text)

        elif isinstance(part, TextOutputPart):
            # Regular text_output - add to pending
            if part.text:
                pending_text.append(part.text)

        else:
            # Non-text part (activity, etc.) - flush pending text first
            flush_pending_text()
            result.append(part)

    # Flush any remaining text
    flush_pending_text()

    return result


class StructuredAgentOutput(BaseModel):
    """
    Represents structured output from the agent.
    It can contain a primary textual response and a list of additional structured parts.
    """

    # Primary text response, often the main conversational reply.
    # This can be derived from a TextOutputPart or be a separate consolidated summary.
    response_text: str | None = None
    parts: list[AgentOutputPartUnion] = Field(default_factory=list)
    # Raw streaming activities for persistence (same format as __STREAM_ACTIVITY__ events).
    # These are stored in ES and used to replay "Under the Hood" on history load.
    streaming_activities: list[dict[str, Any]] = Field(default_factory=list)


class AgentInterface(abc.ABC):
    """Abstract interface for conversational agents."""

    @classmethod
    def get_use_remote_config(cls) -> bool:
        """
        Indicates whether this agent's configuration is managed entirely via Elasticsearch.

        If True:
            - The server will NOT push hardcoded config to ES at startup
            - Session initialization will read config from ES only, without merging hardcoded values
            - Ops engineers can modify prompts and models at runtime without code deployments

        If False (default):
            - Hardcoded config is pushed to ES if different at server startup
            - Session initialization merges ES config with hardcoded values

        Returns:
            bool: True if config is managed via ES, False otherwise (default)
        """
        return False

    @abc.abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """Returns metadata about the agent (name, description, capabilities)."""
        pass

    @abc.abstractmethod
    async def get_state(self) -> dict[str, Any]:
        """
        Retrieves the current state of the agent as a JSON-serializable dictionary.
        This state includes all necessary information to restore the agent later.
        """
        pass

    @abc.abstractmethod
    async def load_state(self, state: dict[str, Any]):
        """
        Loads the agent's state from a dictionary. This method is called to restore
        the agent to a previous state.

        Args:
            state: A JSON-serializable dictionary representing the agent's state.
        """
        pass

    async def get_system_prompt(self) -> str | None:
        """
        Returns the default system prompt for the agent.

        This method is optional - agents can override it to provide a default system prompt.
        If not overridden, returns None, indicating no default system prompt is configured.

        Returns:
            The default system prompt string, or None if no default is configured.
        """
        return None

    async def get_welcome_message(self) -> str | None:
        """
        Returns a welcome message to display when a new session is created.

        This method is optional - agents can override it to provide a greeting message
        that will be shown to users when they start a new conversation.

        Returns:
            The welcome message string, or None if no welcome message is configured.
        """
        return None

    async def get_current_model(self, session_id: str) -> str | None:
        """
        Returns the name/identifier of the model currently being used by the agent for a specific session.
        This method should return the model that would be used for the next request in that session.

        The implementation should account for:
        - Any session-specific model overrides
        - Agent-specific model preferences
        - Fallback to default model if none specified

        Args:
            session_id: The session identifier

        Returns:
            Optional[str]: The model identifier/name, or None if not applicable
        """
        return None

    async def configure_session(self, session_configuration: dict[str, Any]) -> None:
        """
        Configure the agent with session-level settings (system prompt, model config, etc.).
        This method is called by AgentManager after agent creation but before state loading.

        Args:
            session_configuration: Dictionary containing:
                - system_prompt: Optional[str] - Custom system prompt for this session
                - model_name: Optional[str] - Model to use for this session
                - model_config: Optional[Dict] - Model configuration parameters
        """
        # Default implementation does nothing - agents can override to handle configuration
        pass

    async def process_file_inputs(
        self,
        agent_input: StructuredAgentInput,
        session_id: str,
        user_id: str = "default_user",
        store_files: bool = True,
        include_text_content: bool = True,
        convert_to_markdown: bool = True,
        enable_multimodal_processing: bool = True,
        enable_progress_tracking: bool = True,
    ) -> tuple[StructuredAgentInput, list[dict[str, Any]]]:
        """
        Process FileDataInputPart in agent input and optionally store files.

        This is a convenience method that uses the framework's file processing utilities.
        Agents can override this method to customize file processing behavior.

        The default implementation:
        1. Looks for a file_storage_manager attribute on the agent
        2. Uses the framework's process_file_inputs utility
        3. Converts FileDataInputPart to TextInputPart for easier agent processing

        Args:
            agent_input: The original StructuredAgentInput with potential FileDataInputPart
            session_id: Session ID for file storage
            user_id: User ID for file storage (default: "default_user")
            store_files: Whether to store files persistently (default: True)
            include_text_content: Whether to include text file content inline (default: True)

        Returns:
            Tuple containing:
            - Modified StructuredAgentInput with files converted to text
            - List of file metadata dictionaries

        Example:
            ```python
            # In your agent's handle_message method:
            processed_input, files = await self.process_file_inputs(agent_input, session_id)
            # Now use processed_input which has files as TextInputPart
            ```
        """
        # Import here to avoid circular imports
        from .file_system_management import process_file_inputs

        # Try to find file storage manager on the agent
        file_storage_manager = getattr(self, "file_storage_manager", None) or getattr(
            self, "_file_storage_manager", None
        )

        return await process_file_inputs(
            agent_input=agent_input,
            file_storage_manager=file_storage_manager,
            user_id=user_id,
            session_id=session_id,
            store_files=store_files,
            include_text_content=include_text_content,
            convert_to_markdown=convert_to_markdown,
            enable_multimodal_processing=enable_multimodal_processing,
            enable_progress_tracking=enable_progress_tracking,
        )

    # --- Methods that subclasses must implement ---
    @abc.abstractmethod
    async def handle_message(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> StructuredAgentOutput:
        """
        Handles a user message (potentially multimodal and structured) in non-streaming mode.

        Args:
            session_id: The unique identifier for the current conversation session.
            agent_input: A StructuredAgentInput object containing the user's query and content parts.

        Returns:
            A StructuredAgentOutput object containing the agent's complete response.
        """
        pass

    async def handle_message_stream(
        self, session_id: str, agent_input: StructuredAgentInput
    ) -> AsyncGenerator[StructuredAgentOutput, None]:
        """
        Handles a user message in streaming mode, yielding responses as they become available.

        This default implementation provides a non-streaming fallback by calling
        `handle_message` and yielding its result once. Agents that support true
        streaming should override this method.

        Args:
            session_id: The unique identifier for the current conversation session.
            agent_input: A StructuredAgentInput object containing the user's query and content parts.

        Yields:
            A StructuredAgentOutput object for each part of the response.
        """
        result = await self.handle_message(session_id, agent_input)
        yield result

    def set_display_config_manager(self, manager: Any) -> None:
        """
        Set the display config manager for streaming event enrichment.

        This method is called by the server/framework to provide access
        to display configuration for enriching streaming events with
        friendly names and icons.

        The default implementation is a no-op. Agents that support streaming
        event enrichment (like LlamaIndexAgent) should override this method.

        Args:
            manager: DisplayConfigManager instance, or None to disable enrichment.
        """
        pass

    def get_custom_tool_display_info(self) -> dict[str, Any]:
        """
        Returns custom display info for agent-specific tools (e.g., MCP tools).

        Override this method to provide friendly names, icons, and descriptions
        for tools that are not in the framework's DEFAULT_TOOL_DISPLAY.

        Returns:
            Dictionary mapping tool names to StepDisplayInfo-compatible dicts.
            Each dict should have: id, friendly_name, and optionally icon, description, category.

        Example:
            ```python
            def get_custom_tool_display_info(self) -> dict[str, Any]:
                return {
                    "run_query": {
                        "id": "run_query",
                        "friendly_name": "🔍 Exécution de requête SQL",
                        "description": "Exécute une requête SQL sur Athena",
                        "icon": "🔍",
                        "category": "database",
                    },
                    "get_result": {
                        "id": "get_result",
                        "friendly_name": "📊 Récupération des résultats",
                        "description": "Récupère les résultats d'une requête",
                        "icon": "📊",
                        "category": "database",
                    },
                }
            ```
        """
        return {}
