### v0.2.0 ###
import asyncio  # Added asyncio
import base64  # Added for file preview content encoding
import importlib
import io  # Added for file streaming
import json  # Added json
import logging  # Added logging
import os
import secrets  # Ensure secrets is imported for compare_digest
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal, Union

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.routing import APIRoute
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)  # Crucial import for Basic Auth and API Key
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# Configure logging based on environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create logger for this module
logger = logging.getLogger(__name__)

from ..core.agent_interface import (
    AgentInputPartUnion,
    AgentInterface,
    AgentOutputPartUnion,
    FileDataInputPart,
    StructuredAgentInput,
    StructuredAgentOutput,
    TextInputPart,
    TextOutputPart,
    consolidate_text_parts,
    strip_technical_details,
)  # Import new models

# State management utilities (if needed, import from state_manager)
from ..core.agent_provider import AgentManager
from ..core.model_clients import client_factory
from ..core.model_config import model_config
from ..core.state_manager import StateManager
from ..core.step_display_config import DisplayConfigManager

# Error logging imports
from ..monitoring.error_logging import configure_error_logging

# Session storage imports
from ..session.session_storage import (
    MessageData,
    MessageInsight,
    SessionData,
    SessionStorageFactory,
    SessionStorageInterface,
    history_message_to_message_data,
    message_data_to_history_message,
)

# File storage imports
from ..storage.file_system_management import FileStorageFactory, process_response_file_links

# Session title generator imports
from ..utils.session_title_generator import get_title_generator


# Global variable for agent class (used by convenience function)
_GLOBAL_AGENT_CLASS: type[AgentInterface] | None = None


# --- Helper Function to Load Agent --- >
def _load_agent_dynamically() -> type[AgentInterface]:
    """Loads the agent class from global variable or AGENT_CLASS_PATH environment variable."""

    # First, check if agent class is set via global variable (convenience function)
    if _GLOBAL_AGENT_CLASS is not None:
        logger.info(
            f"[Agent Loading] Using agent class from global variable: {_GLOBAL_AGENT_CLASS.__name__}"
        )
        return _GLOBAL_AGENT_CLASS

    # Fallback to environment variable method
    # For this session, we will hardcode the streaming agent to demonstrate the new functionality.
    # In a real application, you would set this environment variable to:
    # AGENT_CLASS_PATH="examples.simple_autogen_assistant:StreamingAutoGenAssistant"
    # agent_path = "examples.simple_autogen_assistant:StreamingAutoGenAssistant"
    agent_path = os.environ.get("AGENT_CLASS_PATH")
    if not agent_path:
        raise OSError(
            "No agent class available. Either:\n"
            "1. Use create_basic_agent_server(MyAgent) from agent_framework, or\n"
            "2. Set AGENT_CLASS_PATH environment variable (format: 'module_name:ClassName'), or\n"
            "3. Create a server.py file that imports the agent_framework.server app\n"
            "\nExample using convenience function:\n"
            "  from agent_framework import create_basic_agent_server\n"
            "  create_basic_agent_server(MyAgent, port=8000)"
        )

    try:
        module_name, class_name = agent_path.split(":")
    except ValueError:
        raise ValueError(
            f"Invalid AGENT_CLASS_PATH format: '{agent_path}'. Expected format: 'module_name:ClassName'"
        )

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(
            f"Could not import agent module '{module_name}' from AGENT_CLASS_PATH: {e}"
        )

    try:
        agent_class = getattr(module, class_name)
    except AttributeError:
        raise AttributeError(f"Could not find class '{class_name}' in module '{module_name}'")

    if not issubclass(agent_class, AgentInterface):
        raise TypeError(f"Agent class '{agent_path}' must inherit from AgentInterface")

    logger.info(
        f"[Agent Loading] Successfully loaded agent class from AGENT_CLASS_PATH: {agent_path}"
    )
    return agent_class


# < --- Helper Function ---


# --- Content Part Models (for request validation) --- >
class TextContentPart(BaseModel):
    type: str = "text"
    text: str


class ImageUrl(BaseModel):
    url: str
    # detail: Optional[str] = "auto" # Optional detail field if needed later


class ImageUrlContentPart(BaseModel):
    type: str = "image_url"
    image_url: ImageUrl


# Type alias for content parts accepted in requests
InputContentPart = Union[TextContentPart, ImageUrlContentPart]
# < --- Content Part Models ---


# --- History Message Model --- >
class HistoryMessage(BaseModel):
    role: str
    text_content: str | None = None  # Made optional
    parts: list[AgentOutputPartUnion] | None = None  # Field for structured parts (UI display)
    activity_parts: list[dict[str, Any]] | None = (
        None  # Raw activity dicts for "Under the Hood" display (same format as __STREAM_ACTIVITY__)
    )
    response_text_main: str | None = None  # To store StructuredAgentOutput.response_text
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    interaction_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )  # Unique ID for each interaction exchange
    processing_time_ms: float | None = None  # Processing time for agent responses
    processed_at: str | None = None  # When the response was processed
    model_used: str | None = None  # AI model used to generate the response
    selection_mode: str | None = None  # How the model was selected ("auto" or "manual")
    is_welcome_message: bool = False  # True if this is a welcome message


# < --- History Message Model ---


# --- Global Application State ---

# Session storage backend (set during startup)
session_storage: SessionStorageInterface | None = None

# Default user ID for single-user deployments
DEFAULT_USER_ID = "default_user"


# Pydantic model for incoming messages, now uses content list
class MessageRequest(BaseModel):
    # This model directly mirrors StructuredAgentInput for the request body
    query: str | None = None
    parts: list[AgentInputPartUnion] = Field(default_factory=list)
    session_id: str | None = (
        None  # session_id from query param will take precedence if both provided
    )
    correlation_id: str | None = None  # Optional correlation ID to link sessions across agents
    model_preference: str | None = Field(
        None, description="Model preference: 'auto' for automatic routing or specific model name"
    )


# Pydantic model for the response, includes session_id
class SessionMessageResponse(BaseModel):
    # This model directly mirrors StructuredAgentOutput for the response body
    response_text: str | None = None
    parts: list[AgentOutputPartUnion] = Field(default_factory=list)
    session_id: str
    user_id: str  # Include user_id in the response for clarity
    correlation_id: str | None = None  # Include correlation_id in response
    interaction_id: str  # Include the interaction ID for this exchange
    processing_time_ms: float | None = None  # Include processing time if available
    model_used: str | None = None  # Include model used to generate the response
    selection_mode: str | None = None  # How the model was selected ("auto" or "manual")
    # Agent identity fields
    agent_id: str | None = None  # Unique identifier for the agent instance
    agent_type: str | None = None  # Agent class name
    agent_metadata: dict[str, Any] | None = None  # Additional agent metadata
    is_welcome_message: bool = False  # True if this is a welcome message


class SessionInfo(BaseModel):
    session_id: str
    session_label: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None
    agent_id: str | None = None
    agent_type: str | None = None
    session_configuration: dict[str, Any] | None = None
    # Enhanced with agent lifecycle information
    agent_lifecycle: list[dict[str, Any]] | None = None


# --- Config Sync Function --- >
async def sync_all_agent_configs_to_elasticsearch(agent_class: type[AgentInterface]) -> None:
    """
    Sync all registered agent configs to Elasticsearch at server startup.

    This function:
    1. Creates a temporary instance of the agent to get its configuration
    2. Compares the hardcoded config with the latest ES version
    3. Pushes a new version to ES if different and use_remote_config=False

    Args:
        agent_class: The agent class to sync configuration for
    """
    # Check if ES is enabled
    es_enabled = os.getenv("ELASTICSEARCH_ENABLED", "").lower() == "true"
    if not es_enabled:
        logger.debug("[CONFIG SYNC] Elasticsearch not enabled, skipping config sync")
        return

    # Check if agent uses remote config (skip push if True)
    if agent_class.get_use_remote_config():
        logger.info(
            f"[CONFIG SYNC] Agent {agent_class.__name__} has use_remote_config=True, "
            "skipping hardcoded config push to ES"
        )
        return

    try:
        # Create a temporary instance to get agent configuration
        temp_agent = agent_class()

        # Get agent identity
        from ..core.state_manager import StateManager

        agent_identity = StateManager.create_agent_identity(temp_agent)
        agent_id = agent_identity.agent_id
        agent_type = agent_identity.agent_type

        logger.info(f"[CONFIG SYNC] Syncing config for agent_id={agent_id}, type={agent_type}")

        # Build hardcoded config from agent class
        hardcoded_config: dict[str, Any] = {}

        # Get agent metadata (name, description, capabilities)
        agent_name: str | None = None
        agent_description: str | None = None
        if hasattr(temp_agent, "get_metadata"):
            try:
                metadata = await temp_agent.get_metadata()
                if metadata.get("name"):
                    agent_name = metadata["name"]
                    hardcoded_config["name"] = agent_name
                if metadata.get("description"):
                    agent_description = metadata["description"]
                    hardcoded_config["description"] = agent_description
            except Exception as e:
                logger.warning(f"[CONFIG SYNC] Could not get agent metadata: {e}")

        # Get system prompt if available
        if hasattr(temp_agent, "get_agent_prompt"):
            try:
                system_prompt = temp_agent.get_agent_prompt()
                if system_prompt:
                    hardcoded_config["system_prompt"] = system_prompt
            except Exception as e:
                logger.warning(f"[CONFIG SYNC] Could not get agent prompt: {e}")
        elif hasattr(temp_agent, "get_system_prompt"):
            try:
                system_prompt = await temp_agent.get_system_prompt()
                if system_prompt:
                    hardcoded_config["system_prompt"] = system_prompt
            except Exception as e:
                logger.warning(f"[CONFIG SYNC] Could not get system prompt: {e}")

        # Get default model if available
        if hasattr(temp_agent, "_default_model") and temp_agent._default_model:
            hardcoded_config["model_name"] = temp_agent._default_model

        # Get model config if available
        if hasattr(temp_agent, "_model_config") and temp_agent._model_config:
            hardcoded_config["model_config"] = temp_agent._model_config

        # If no hardcoded config found, skip
        if not hardcoded_config:
            logger.debug(
                f"[CONFIG SYNC] No hardcoded config found for agent_id={agent_id}, skipping"
            )
            return

        # Initialize ES config provider
        from ..core.elasticsearch_config_provider import ElasticsearchConfigProvider

        es_config_provider = ElasticsearchConfigProvider()
        await es_config_provider.initialize()

        if es_config_provider.client is None:
            logger.warning("[CONFIG SYNC] Elasticsearch client not available, skipping config sync")
            return

        # Get current ES config
        es_config = await es_config_provider.get_agent_config(agent_id)

        # Compare configs
        configs_match = _compare_agent_configs(hardcoded_config, es_config)

        if configs_match:
            logger.debug(
                f"[CONFIG SYNC] Hardcoded config matches ES config for agent_id={agent_id}, "
                "skipping push"
            )
            return

        # Push new config to ES
        logger.info(
            f"[CONFIG SYNC] Hardcoded config differs from ES config for agent_id={agent_id}, "
            "pushing new version"
        )

        result = await es_config_provider.update_agent_config(
            agent_id=agent_id,
            config=hardcoded_config,
            agent_type=agent_type,
            name=agent_name,
            description=agent_description,
            updated_by="server-startup",
            metadata={"sync_source": "hardcoded", "agent_class": agent_class.__name__},
            active=True,
        )

        if result:
            logger.info(
                f"[CONFIG SYNC] Successfully pushed config to ES for agent_id={agent_id} "
                f"(version={result.get('version')}, doc_id={result.get('doc_id')})"
            )
        else:
            logger.warning(f"[CONFIG SYNC] Failed to push config to ES for agent_id={agent_id}")

    except Exception as e:
        logger.warning(f"[CONFIG SYNC] Error syncing agent config to ES: {e}")


def _compare_agent_configs(
    hardcoded_config: dict[str, Any], es_config: dict[str, Any] | None
) -> bool:
    """
    Compare hardcoded config with ES config to determine if they match.

    Args:
        hardcoded_config: The hardcoded configuration from the agent class
        es_config: The configuration from Elasticsearch (may be None)

    Returns:
        True if configs match (or ES config is None and hardcoded is empty), False otherwise
    """
    if es_config is None:
        # No ES config exists, configs don't match (need to push)
        return False

    # Compare relevant fields
    for key, hardcoded_value in hardcoded_config.items():
        es_value = es_config.get(key)

        if isinstance(hardcoded_value, dict) and isinstance(es_value, dict):
            # Deep compare for nested dicts
            if not _compare_agent_configs(hardcoded_value, es_value):
                return False
        elif hardcoded_value != es_value:
            logger.debug(
                f"[CONFIG SYNC] Config mismatch on key '{key}': "
                f"hardcoded={hardcoded_value!r}, es={es_value!r}"
            )
            return False

    return True


# < --- Config Sync Function ---


# --- Lifespan Event Handler --- >
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events using modern lifespan approach."""
    global session_storage

    # Startup
    try:
        # Initialize OpenTelemetry (before other components)
        otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
        if otel_enabled:
            try:
                from ..monitoring.otel_setup import get_otel_setup

                otel_setup = get_otel_setup()
                if otel_setup.initialize():
                    logger.info("[OTEL] OpenTelemetry initialized successfully")
                else:
                    logger.warning("[OTEL] OpenTelemetry initialization failed or disabled")
            except Exception as e:
                logger.warning(f"[OTEL] Failed to initialize OpenTelemetry: {e}")

        # Load agent class
        agent_class = _load_agent_dynamically()
        logger.info(f"Startup event: Setting app.state.agent_class to {agent_class.__name__}")
        app.state.agent_class = agent_class

        # Initialize session storage
        session_storage = await SessionStorageFactory.create_storage()
        app.state.session_storage = session_storage
        logger.info(f"Session storage initialized: {session_storage.__class__.__name__}")

        # Initialize file storage
        file_storage_manager = await FileStorageFactory.create_storage_manager()
        app.state.file_storage_manager = file_storage_manager
        logger.info(
            f"File storage manager initialized with backends: {list(file_storage_manager.backends.keys())}"
        )

        # Initialize the AgentManager
        agent_manager = AgentManager(session_storage)
        app.state.agent_manager = agent_manager
        logger.info("AgentManager initialized.")

        # Configure Elasticsearch logging (if ES enabled)
        es_enabled = os.getenv("ELASTICSEARCH_ENABLED", "").lower() == "true"
        if es_enabled:
            try:
                es_index_pattern = os.getenv("ELASTICSEARCH_LOG_INDEX_PATTERN", "agent-logs-{date}")
                await configure_error_logging(
                    enable_elasticsearch=True, es_index_pattern=es_index_pattern
                )
                logger.info(
                    f"[ES LOGGING] Elasticsearch logging enabled with index pattern: {es_index_pattern}"
                )
            except Exception as e:
                # Log warning but don't block startup
                logger.warning(f"[ES LOGGING] Failed to configure Elasticsearch logging: {e}")

        # Sync agent configs to Elasticsearch (if ES enabled)
        try:
            await sync_all_agent_configs_to_elasticsearch(agent_class)
        except Exception as e:
            # Log warning but don't block startup
            logger.warning(f"[CONFIG SYNC] Failed to sync agent configs to ES: {e}")

        # Initialize ES metrics logger for Kibana dashboards (if enabled)
        es_metrics_logging_enabled = (
            os.getenv("METRICS_ES_LOGGING_ENABLED", "false").lower() == "true"
        )
        if es_metrics_logging_enabled:
            try:
                from ..monitoring.observability_manager import get_observability_manager

                obs_manager = get_observability_manager()
                if await obs_manager.initialize_es_metrics_logger():
                    logger.info("[ES METRICS] ES metrics logging initialized for Kibana dashboards")
                else:
                    logger.warning(
                        "[ES METRICS] ES metrics logging enabled but initialization failed"
                    )
            except Exception as e:
                logger.warning(f"[ES METRICS] Failed to initialize ES metrics logger: {e}")

        # Initialize DisplayConfigManager for streaming display info
        try:
            from ..core.elasticsearch_config_provider import ElasticsearchConfigProvider

            es_config_provider = None
            if es_enabled:
                try:
                    es_config_provider = ElasticsearchConfigProvider()
                    await es_config_provider.initialize()
                    logger.info("[DISPLAY CONFIG] ElasticsearchConfigProvider initialized")
                except Exception as e:
                    logger.warning(f"[DISPLAY CONFIG] Failed to initialize ES provider: {e}")
                    es_config_provider = None

            display_config_manager = DisplayConfigManager(config_provider=es_config_provider)
            await display_config_manager.initialize()
            app.state.display_config_manager = display_config_manager
            logger.info("[DISPLAY CONFIG] DisplayConfigManager initialized")
        except Exception as e:
            # Log warning but don't block startup - use memory-only fallback
            logger.warning(f"[DISPLAY CONFIG] Failed to initialize DisplayConfigManager: {e}")
            app.state.display_config_manager = DisplayConfigManager()
            logger.info("[DISPLAY CONFIG] Using memory-only DisplayConfigManager")

    except (OSError, ValueError, ImportError, AttributeError, TypeError) as e:
        # Log the specific error and raise a runtime error to prevent startup
        logger.critical(f"CRITICAL STARTUP ERROR: Failed to load agent class - {e}")
        raise RuntimeError(f"Server startup failed: Could not load agent. {e}") from e
    except Exception as e:
        # Catch any other unexpected errors during loading
        logger.critical(
            f"CRITICAL STARTUP ERROR: An unexpected error occurred during startup - {e}"
        )
        raise RuntimeError(f"Server startup failed: Unexpected error. {e}") from e

    yield

    # Shutdown
    # Flush and shutdown ES metrics logger
    es_metrics_logging_enabled = os.getenv("METRICS_ES_LOGGING_ENABLED", "false").lower() == "true"
    if es_metrics_logging_enabled:
        try:
            from ..monitoring.observability_manager import get_observability_manager

            obs_manager = get_observability_manager()
            await obs_manager.flush_es_metrics()
            logger.info("[ES METRICS] ES metrics flushed before shutdown")
        except Exception as e:
            logger.warning(f"[ES METRICS] Error flushing ES metrics: {e}")

    # Shutdown OpenTelemetry
    otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    if otel_enabled:
        try:
            from ..monitoring.otel_setup import get_otel_setup

            otel_setup = get_otel_setup()
            otel_setup.shutdown()
            logger.info("[OTEL] OpenTelemetry shutdown complete")
        except Exception as e:
            logger.warning(f"[OTEL] Error during OpenTelemetry shutdown: {e}")

    if session_storage is not None:
        await session_storage.cleanup()
        logger.info("Session storage cleaned up")


# < --- Lifespan Event Handler ---

# Initialize FastAPI app
app = FastAPI(title="Generic Agent Server", lifespan=lifespan)

# --- Authentication Setup ---
logger.debug(f"[AUTH DEBUG] Raw REQUIRE_AUTH env var: {os.environ.get('REQUIRE_AUTH')}")
REQUIRE_AUTH_STR = os.environ.get("REQUIRE_AUTH", "false").lower()
REQUIRE_AUTH = REQUIRE_AUTH_STR == "true"

# Basic Auth Configuration
BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME", "admin")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "password")

# API Key Authentication Configuration
API_KEYS = os.environ.get("API_KEYS", "").strip()
VALID_API_KEYS = (
    set(key.strip() for key in API_KEYS.split(",") if key.strip()) if API_KEYS else set()
)

# Admin Mode Password Configuration
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Initialize security schemes
basic_security = HTTPBasic(auto_error=False)
bearer_security = HTTPBearer(auto_error=False)

logger.debug(f"[AUTH DEBUG] Authentication configured - REQUIRE_AUTH: {REQUIRE_AUTH}")
logger.debug(f"[AUTH DEBUG] Valid API keys configured: {len(VALID_API_KEYS)} keys")
logger.debug("[AUTH DEBUG] Both Basic Auth and API Key authentication available")
logger.info(f"[AUTH] Admin password configured (length: {len(ADMIN_PASSWORD)} chars)")


async def get_current_user(
    basic_credentials: HTTPBasicCredentials | None = Depends(basic_security),
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """
    Unified authentication function that supports both Basic Auth and API Key authentication.
    Tries API Key first, then falls back to Basic Auth.
    """
    # Re-evaluate all auth settings on each call to respect test fixtures
    require_auth = os.environ.get("REQUIRE_AUTH", "false").lower() == "true"
    basic_auth_username = os.environ.get("BASIC_AUTH_USERNAME", "admin")
    basic_auth_password = os.environ.get("BASIC_AUTH_PASSWORD", "password")
    api_keys_str = os.environ.get("API_KEYS", "").strip()
    valid_api_keys = (
        set(key.strip() for key in api_keys_str.split(",") if key.strip())
        if api_keys_str
        else set()
    )

    logger.debug(f"[AUTH DEBUG] Inside get_current_user. REQUIRE_AUTH is: {require_auth}")

    if not require_auth:
        logger.debug(
            "[AUTH DEBUG] REQUIRE_AUTH is false, bypassing auth check. Returning anonymous user."
        )
        return "anonymous"

    # Try API Key authentication first (from Bearer token)
    if bearer_credentials and bearer_credentials.credentials:
        api_key = bearer_credentials.credentials
        logger.debug("[AUTH DEBUG] Attempting API key authentication with Bearer token")
        if api_key in valid_api_keys:
            logger.debug("[AUTH DEBUG] API key authentication successful (Bearer)")
            return f"api_key_user_{hash(api_key) % 10000}"
        else:
            logger.debug("[AUTH DEBUG] Invalid API key provided via Bearer token")

    # Try API Key authentication from X-API-Key header
    if x_api_key:
        logger.debug("[AUTH DEBUG] Attempting API key authentication with X-API-Key header")
        if x_api_key in valid_api_keys:
            logger.debug("[AUTH DEBUG] API key authentication successful (X-API-Key)")
            return f"api_key_user_{hash(x_api_key) % 10000}"
        else:
            logger.debug("[AUTH DEBUG] Invalid API key provided via X-API-Key header")

    # Try Basic Auth authentication
    if basic_credentials:
        logger.debug("[AUTH DEBUG] Attempting basic authentication")
        correct_username = secrets.compare_digest(basic_credentials.username, basic_auth_username)
        correct_password = secrets.compare_digest(basic_credentials.password, basic_auth_password)

        if correct_username and correct_password:
            logger.debug(
                f"[AUTH DEBUG] Basic auth successful for user: {basic_credentials.username}"
            )
            return basic_credentials.username
        else:
            logger.debug(f"[AUTH DEBUG] Basic auth failed for user: {basic_credentials.username}")

    # If we reach here, authentication failed
    logger.debug("[AUTH DEBUG] All authentication methods failed. Raising 401.")
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Use Basic Auth (username/password) or API Key (Bearer token or X-API-Key header).",
        headers={"WWW-Authenticate": "Basic", "X-Auth-Methods": "Basic, Bearer, X-API-Key"},
    )


# --- End Authentication Setup ---

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add API Timing middleware (if enabled)
API_TIMING_ENABLED = os.getenv("API_TIMING_ENABLED", "true").lower() == "true"
if API_TIMING_ENABLED:
    from .api_timing_middleware import APITimingMiddleware

    app.add_middleware(APITimingMiddleware, enabled=True)
    logger.info("[SERVER] API timing middleware enabled")

# Add OTel Tracing middleware (if enabled)
OTEL_TRACING_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() == "true"
if OTEL_TRACING_ENABLED:
    from .otel_tracing_middleware import OTelTracingMiddleware

    app.add_middleware(OTelTracingMiddleware, enabled=True)
    logger.info("[SERVER] OTel tracing middleware enabled")

# --- Admin Router Registration ---
# The admin router provides endpoints for user management, session viewing, KPIs,
# and configuration management. It requires Elasticsearch to be enabled.
# The router's endpoints handle ES availability through the require_elasticsearch dependency,
# returning HTTP 503 when ES is not available.
from .admin_router import admin_router


app.include_router(admin_router)
logger.info("[SERVER] Admin router registered at /api/admin")
# --- End Admin Router Registration ---

# --- Session Management is now handled by AgentManager ---


# --- Message persistence helpers --- >
async def _persist_user_message_to_storage(
    user_id: str,
    session_id: str,
    interaction_id: str,
    user_message: HistoryMessage,
    agent_id: str | None = None,
    agent_type: str | None = None,
) -> bool:
    """Persist user input to storage."""
    global session_storage
    try:
        user_msg_data = history_message_to_message_data(
            user_message,
            session_id,
            user_id,
            interaction_id,
            "user_input",
            agent_id=agent_id,
            agent_type=agent_type,
        )
        success = await session_storage.add_message(user_msg_data)
        if success:
            logger.debug(f"Persisted user message for interaction {interaction_id}")
        return success
    except Exception as e:
        logger.error(f"Error persisting user message for interaction {interaction_id}: {e}")
        return False


async def _persist_agent_response_to_storage(
    user_id: str,
    session_id: str,
    interaction_id: str,
    agent_response_obj: StructuredAgentOutput,
    processing_time_ms: float,
    model_used: str | None,
    selection_mode: str | None,
    agent_id: str | None,
    agent_type: str | None,
) -> None:
    """Persists the agent's response to storage."""
    global session_storage
    try:
        # Store UI parts and streaming activities separately
        # UI parts are for display, streaming_activities are for "Under the Hood" replay
        # streaming_activities are raw dicts in __STREAM_ACTIVITY__ format
        agent_message = HistoryMessage(
            role="assistant",
            parts=agent_response_obj.parts,
            activity_parts=agent_response_obj.streaming_activities,  # Raw dicts for ES storage
            response_text_main=agent_response_obj.response_text,
            interaction_id=interaction_id,
            processing_time_ms=processing_time_ms,
            processed_at=datetime.now(timezone.utc).isoformat(),
            model_used=model_used,
            selection_mode=selection_mode,
        )

        agent_msg_data = history_message_to_message_data(
            agent_message,
            session_id,
            user_id,
            interaction_id,
            "agent_response",
            agent_id=agent_id,
            agent_type=agent_type,
        )

        result = await session_storage.add_message(agent_msg_data)
        logger.info(f"[PERSIST DEBUG] add_message result: {result}")
        logger.info(f"[PERSIST DEBUG] Persisted agent response for interaction {interaction_id}")
    except Exception as e:
        logger.error(
            f"[PERSIST DEBUG] Error persisting agent response for interaction {interaction_id}: {e}",
            exc_info=True,
        )


# --- Helper to extract text from content for history --- >
def _extract_text_for_history_from_input(agent_input: StructuredAgentInput) -> str:
    """Extracts a primary text representation from StructuredAgentInput for history logging."""
    if agent_input.query:
        return agent_input.query
    # Fallback: concatenate text from TextInputParts if no primary query
    text_from_parts = [p.text for p in agent_input.parts if isinstance(p, TextInputPart)]
    if text_from_parts:
        return "\n".join(text_from_parts)
    # Fallback for non-text inputs if no query or text parts
    if agent_input.parts:  # If there are parts but no text ones
        return f"[Structured input with {len(agent_input.parts)} part(s), e.g., {type(agent_input.parts[0]).__name__}]"
    return "[Empty input]".strip()


def _extract_text_for_history_from_output(agent_output: StructuredAgentOutput) -> str:
    """Extracts the primary text response from StructuredAgentOutput for history logging."""
    if agent_output.response_text is not None:
        return agent_output.response_text
    # Fallback: If no primary response_text, find the first TextOutputPart
    for part in agent_output.parts:
        if isinstance(part, TextOutputPart):
            return part.text
    if agent_output.parts:  # If parts exist but no text ones
        return f"[Structured response with {len(agent_output.parts)} part(s), e.g., {type(agent_output.parts[0]).__name__}]"
    return "[Empty or non-text response]".strip()


async def _auto_generate_session_title_if_needed(
    user_id: str, session_id: str, user_message_text: str, agent_response_text: str
) -> None:
    """
    Background task to auto-generate session title after first exchange.

    This function is designed to run asynchronously without blocking the main
    message flow. Any errors are logged but not propagated.

    Args:
        user_id: User identifier
        session_id: Session identifier
        user_message_text: The user's message text
        agent_response_text: The agent's response text
    """
    global session_storage
    try:
        title_generator = get_title_generator()
        await title_generator.auto_generate_if_needed(
            session_storage=session_storage,
            user_id=user_id,
            session_id=session_id,
            user_message=user_message_text,
            agent_response=agent_response_text,
        )
    except Exception as e:
        # Log error but don't propagate - title generation should never break main flow
        logger.error(
            f"[SESSION TITLE] Error in background title generation for session {session_id}: {e}"
        )


async def _resolve_model_for_request(
    agent_instance: AgentInterface,
    model_preference: str | None,
    query: str,
    context: list[dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Resolve which model to use based on backward compatibility rules.

    Priority order:
    1. If agent has _default_model and no model_preference → use agent default (bypass router)
    2. If model_preference provided → use ModelRouter
    3. If neither → use DEFAULT_MODEL_MODE via router

    Args:
        agent_instance: The agent instance to check for default model
        model_preference: User's model preference from request (None, "auto", or specific model)
        query: The user's query text for classification
        context: Conversation context for classification

    Returns:
        Tuple of (selected_model, routing_info) where routing_info contains
        tier, reason, fallback_used, classification_skipped if routing was used,
        or None if using agent's default model.
    """
    from ..core.model_router import RoutingResult, model_router

    # Check if agent has a hardcoded default model (backward compatibility)
    agent_default_model = getattr(agent_instance, "_default_model", None)

    # Case 1: Agent has default model and no model_preference provided
    # → Use agent's default (bypass router entirely)
    if agent_default_model and not model_preference:
        logger.info(
            f"[MODEL ROUTING] Using agent's default model: {agent_default_model} "
            "(backward compatibility mode)"
        )
        return agent_default_model, None

    # Case 2 & 3: Use ModelRouter
    # - If model_preference provided → use it
    # - If no preference and no agent default → use DEFAULT_MODEL_MODE
    effective_preference = model_preference if model_preference else model_router.default_mode

    try:
        routing_result: RoutingResult = await model_router.route(
            query=query, context=context, model_preference=effective_preference
        )

        routing_info = {
            "model": routing_result.model,
            "tier": routing_result.tier.value,
            "reason": routing_result.reason,
            "fallback_used": routing_result.fallback_used,
            "classification_skipped": routing_result.classification_skipped,
        }

        logger.info(
            f"[MODEL ROUTING] Selected model: {routing_result.model} "
            f"(tier: {routing_result.tier.value}, reason: {routing_result.reason})"
        )

        return routing_result.model, routing_info

    except Exception as e:
        logger.error(f"[MODEL ROUTING] Error during routing: {e}")
        # If routing fails and agent has a default, fall back to it
        if agent_default_model:
            logger.warning(
                f"[MODEL ROUTING] Falling back to agent's default model: {agent_default_model}"
            )
            return agent_default_model, None
        # Otherwise, re-raise the exception
        raise


# < --- Helper --- >


@app.post("/message", response_model=SessionMessageResponse)
async def handle_message_endpoint(
    request: Request,
    msg_request_body: MessageRequest,
    user_id: str = Query(DEFAULT_USER_ID, description="Identifier for the user session"),
    current_user: str = Depends(get_current_user),
):
    """
    Handles incoming messages using the session storage backend.
    """
    global session_storage
    agent_class_to_use: type[AgentInterface] = request.app.state.agent_class
    agent_manager: AgentManager = request.app.state.agent_manager

    # Determine session_id: query param > body.session_id > new UUID
    session_id_from_query = request.query_params.get("session_id")
    effective_session_id = session_id_from_query or msg_request_body.session_id or str(uuid.uuid4())

    # Update API timing tracker with context (session_id, user_id)
    # agent_id will be set later once we have the agent instance
    from .api_timing_middleware import get_api_timing_tracker

    api_tracker = get_api_timing_tracker(request)
    if api_tracker:
        api_tracker.set_context(session_id=effective_session_id, user_id=user_id)

    # Construct StructuredAgentInput from the request body
    query_from_request = msg_request_body.query
    if query_from_request is None:
        query_from_request = ""

    agent_input = StructuredAgentInput(query=query_from_request, parts=msg_request_body.parts)

    # Process file inputs if present (convert to markdown, store files, etc.)
    from ..storage.file_system_management import process_file_inputs

    # Check if there are any FileDataInputPart in the input
    has_files = any(isinstance(part, FileDataInputPart) for part in agent_input.parts)

    if has_files and hasattr(request.app.state, "file_storage_manager"):
        logger.info(
            f"Processing {sum(1 for p in agent_input.parts if isinstance(p, FileDataInputPart))} file(s) for session {effective_session_id}"
        )
        # Process files: decode, convert to markdown, store, etc.
        agent_input, uploaded_files = await process_file_inputs(
            agent_input=agent_input,
            file_storage_manager=request.app.state.file_storage_manager,
            user_id=user_id,
            session_id=effective_session_id,
            store_files=True,
            include_text_content=True,
            convert_to_markdown=True,
            enable_multimodal_processing=True,
        )
        logger.info(
            f"✅ Processed {len(uploaded_files)} file(s): {[f.get('filename') for f in uploaded_files]}"
        )

    # Ensure session metadata exists (create if needed for sessions created through messaging)
    existing_session = await session_storage.load_session(user_id, effective_session_id)
    if not existing_session:
        # Create minimal session metadata for sessions created through messaging
        session_data = SessionData(
            session_id=effective_session_id,
            user_id=user_id,
            agent_instance_config={},  # DEPRECATED - kept for backward compatibility
            correlation_id=msg_request_body.correlation_id,
            metadata={"status": "active"},  # Ensure new sessions are marked as active
            config_reference=None,  # Will be populated when ES config is used
            session_overrides=None,  # No overrides for messaging-created sessions
        )
        await session_storage.save_session(user_id, effective_session_id, session_data)
        logger.info(f"Created session metadata for messaging session {effective_session_id}")
    else:
        # Check if session is closed (prevent messaging)
        if existing_session.metadata and existing_session.metadata.get("status") == "closed":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot send message to closed session {effective_session_id}",
            )

    # Use AgentManager to get a ready-to-use agent instance (proxy)
    agent_instance = await agent_manager.get_agent(
        effective_session_id, agent_class_to_use, user_id
    )

    # Update API timing tracker with agent_id now that we have the agent instance
    if api_tracker and hasattr(agent_instance, "agent_id"):
        api_tracker.set_context(agent_id=agent_instance.agent_id)

    # Inject DisplayConfigManager for streaming event enrichment
    if hasattr(request.app.state, "display_config_manager"):
        display_manager = request.app.state.display_config_manager
        agent_instance.set_display_config_manager(display_manager)
        # Register custom tool display info from agent (e.g., MCP tools)
        if hasattr(agent_instance, "get_custom_tool_display_info"):
            custom_info = agent_instance.get_custom_tool_display_info()
            if custom_info:
                display_manager.register_agent_tool_display_info(
                    agent_instance.agent_id, custom_info
                )

    # --- Backward Compatibility Model Routing ---
    # Resolve which model to use based on:
    # 1. Agent's _default_model (if set and no model_preference) → bypass router
    # 2. model_preference provided → use ModelRouter
    # 3. Neither → use DEFAULT_MODEL_MODE via router
    conversation_context: list[dict[str, Any]] = []
    try:
        # Get conversation history for classification context
        message_history = await session_storage.get_conversation_history(effective_session_id)
        conversation_context = [
            {"role": msg.role, "content": msg.text_content or ""}
            for msg in message_history[-10:]  # Last 10 messages for context
        ]
    except Exception as ctx_err:
        logger.warning(f"[MODEL ROUTING] Could not load conversation context: {ctx_err}")

    selected_model, routing_info = await _resolve_model_for_request(
        agent_instance=agent_instance,
        model_preference=msg_request_body.model_preference,
        query=query_from_request,
        context=conversation_context,
    )
    # --- End Model Routing ---

    # Generate an interaction ID for this exchange
    interaction_id = str(uuid.uuid4())

    # Check if agent has a preprocess_input method to transform the query
    # This allows agents to transform prompt descriptions to content before persistence
    processed_input = agent_input
    if hasattr(agent_instance, "preprocess_input"):
        try:
            processed_input = await agent_instance.preprocess_input(agent_input)
            logger.debug("[MESSAGE] Agent preprocessed input query")
        except Exception as preprocess_err:
            logger.warning(f"[MESSAGE] Could not preprocess input: {preprocess_err}")
            processed_input = agent_input

    # Create and persist the user message (using processed input)
    user_text_for_history = _extract_text_for_history_from_input(processed_input)
    user_message = HistoryMessage(
        role="user", text_content=user_text_for_history, interaction_id=interaction_id
    )

    # Get agent identity from the agent instance managed by AgentManager
    # The AgentManager already ensures agent identity, so we can extract it from the agent instance
    agent_identity = StateManager.create_agent_identity(agent_instance)
    await _persist_user_message_to_storage(
        user_id,
        effective_session_id,
        interaction_id,
        user_message,
        agent_identity.agent_id,
        agent_identity.agent_type,
    )

    try:
        # Capture start time for processing measurement
        start_time = datetime.now(timezone.utc)

        # Configure the agent with the selected model before handling the message
        if selected_model:
            session_config_for_model = {
                "user_id": user_id,
                "session_id": effective_session_id,
            }
            # Check if agent supports configure_session_with_model
            if hasattr(agent_instance, "configure_session_with_model"):
                await agent_instance.configure_session_with_model(
                    session_config_for_model, selected_model
                )
                logger.info(f"[MODEL ROUTING] Configured agent with model: {selected_model}")

        # Handle the message using the agent proxy
        agent_response_obj: StructuredAgentOutput = await agent_instance.handle_message(
            effective_session_id, processed_input
        )

        # Capture end time and calculate processing duration
        end_time = datetime.now(timezone.utc)
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # Use the selected model from routing, fallback to agent's current model
        model_used = selected_model or await agent_instance.get_current_model(effective_session_id)

        # Determine selection mode based on how the model was selected
        # "manual" if user specified a specific model, "auto" if router selected it
        selection_mode: str | None = None
        if msg_request_body.model_preference and msg_request_body.model_preference != "auto":
            selection_mode = "manual"
        elif routing_info is not None:
            selection_mode = "auto"

        # Persist the agent response to storage
        await _persist_agent_response_to_storage(
            user_id=user_id,
            session_id=effective_session_id,
            interaction_id=interaction_id,
            agent_response_obj=agent_response_obj,
            processing_time_ms=processing_time_ms,
            model_used=model_used,
            selection_mode=selection_mode,
            agent_id=agent_identity.agent_id,
            agent_type=agent_identity.agent_type,
        )

        # Trigger async session title generation (non-blocking)
        # This runs in the background after the first exchange to generate a descriptive title
        asyncio.create_task(
            _auto_generate_session_title_if_needed(
                user_id=user_id,
                session_id=effective_session_id,
                user_message_text=user_text_for_history,
                agent_response_text=_extract_text_for_history_from_output(agent_response_obj),
            )
        )

        # Process file links in response (only if file storage is available)
        file_storage_available = (
            hasattr(request.app.state, "file_storage_manager")
            and request.app.state.file_storage_manager is not None
        )
        response_text_processed = agent_response_obj.response_text
        parts_processed = agent_response_obj.parts

        if file_storage_available:
            if agent_response_obj.response_text:
                response_text_processed = process_response_file_links(
                    agent_response_obj.response_text
                )
            parts_processed = []
            for part in agent_response_obj.parts:
                if isinstance(part, TextOutputPart) and part.text:
                    processed_text = process_response_file_links(part.text)
                    parts_processed.append(TextOutputPart(text=processed_text))
                else:
                    parts_processed.append(part)

        # Create response
        response = SessionMessageResponse(
            response_text=response_text_processed,
            parts=parts_processed,
            session_id=effective_session_id,
            user_id=user_id,
            correlation_id=msg_request_body.correlation_id,
            interaction_id=interaction_id,
            processing_time_ms=processing_time_ms,
            model_used=model_used,
            selection_mode=selection_mode,
            # Agent identity fields
            agent_id=agent_identity.agent_id,
            agent_type=agent_identity.agent_type,
            agent_metadata=agent_identity.to_dict(),
        )

        logger.info(
            f"[SERVER RESPONSE] session_id={effective_session_id}, response_length={len(response.response_text) if response.response_text else 0}, parts={len(response.parts)}"
        )
        return response

    except Exception as e:
        logger.error(
            f"Error processing message for session {effective_session_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# --- NEW STREAMING ENDPOINT --- >

from fastapi import Body


@app.post("/stream")
async def handle_stream_endpoint(
    request: Request,
    session_id: str | None = None,
    msg_request_body: MessageRequest = Body(...),
    user_id: str = Query(DEFAULT_USER_ID, description="Identifier for the user session"),
    current_user: str = Depends(get_current_user),
):
    """
    Handles streaming messages using the session storage backend.
    Available at:
      - POST /sessions/{session_id}/stream (session_id in path, user_id as query)
      - POST /stream?session_id=...&user_id=... (both as query)
    """
    global session_storage

    # Support both /sessions/{session_id}/stream and /stream?session_id=...
    # If session_id is not provided as a path parameter, try to get it from query/body
    if session_id is None:
        # Try to get from query params (for /stream?session_id=...)
        session_id = request.query_params.get("session_id")
        if not session_id:
            # Try to get from body (if present)
            session_id = getattr(msg_request_body, "session_id", None)
        if not session_id:
            raise HTTPException(
                status_code=400, detail="session_id is required as a path or query parameter."
            )

    agent_class_to_use: type[AgentInterface] = request.app.state.agent_class
    agent_manager: AgentManager = request.app.state.agent_manager

    # Update API timing tracker with context (session_id, user_id)
    # agent_id will be set later once we have the agent instance
    from .api_timing_middleware import get_api_timing_tracker

    api_tracker = get_api_timing_tracker(request)
    if api_tracker:
        api_tracker.set_context(session_id=session_id, user_id=user_id)

    # Construct StructuredAgentInput from the request body
    query_from_request = msg_request_body.query
    if query_from_request is None:
        query_from_request = ""

    agent_input = StructuredAgentInput(query=query_from_request, parts=msg_request_body.parts)

    # Process file inputs if present (convert to markdown, store files, etc.)
    from ..storage.file_system_management import process_file_inputs

    # Check if there are any FileDataInputPart in the input
    has_files = any(isinstance(part, FileDataInputPart) for part in agent_input.parts)

    if has_files and hasattr(request.app.state, "file_storage_manager"):

        # Process files: decode, convert to markdown, store, etc.
        agent_input, uploaded_files = await process_file_inputs(
            agent_input=agent_input,
            file_storage_manager=request.app.state.file_storage_manager,
            user_id=user_id,
            session_id=session_id,
            store_files=True,
            include_text_content=True,
            convert_to_markdown=True,
            enable_multimodal_processing=True,
        )

    # Ensure session metadata exists (create if needed for sessions created through streaming)
    existing_session = await session_storage.load_session(user_id, session_id)
    if not existing_session:
        # Create minimal session metadata for sessions created through streaming
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            agent_instance_config={},  # DEPRECATED - kept for backward compatibility
            correlation_id=msg_request_body.correlation_id,
            metadata={"status": "active"},  # Ensure new sessions are marked as active
            config_reference=None,  # Will be populated when ES config is used
            session_overrides=None,  # No overrides for streaming-created sessions
        )
        await session_storage.save_session(user_id, session_id, session_data)
    else:
        # Check if session is closed (prevent streaming)
        if existing_session.metadata and existing_session.metadata.get("status") == "closed":
            raise HTTPException(
                status_code=400, detail=f"Cannot send message to closed session {session_id}"
            )

    # Use AgentManager to get a ready-to-use agent instance (proxy)
    agent_instance = await agent_manager.get_agent(session_id, agent_class_to_use, user_id)

    # Update API timing tracker with agent_id now that we have the agent instance
    if api_tracker and hasattr(agent_instance, "agent_id"):
        api_tracker.set_context(agent_id=agent_instance.agent_id)

    # Inject DisplayConfigManager for streaming event enrichment
    if hasattr(request.app.state, "display_config_manager"):
        display_manager = request.app.state.display_config_manager
        agent_instance.set_display_config_manager(display_manager)
        # Register custom tool display info from agent (e.g., MCP tools)
        if hasattr(agent_instance, "get_custom_tool_display_info"):
            custom_info = agent_instance.get_custom_tool_display_info()
            if custom_info:
                display_manager.register_agent_tool_display_info(
                    agent_instance.agent_id, custom_info
                )

    # --- Backward Compatibility Model Routing ---
    # Resolve which model to use based on:
    # 1. Agent's _default_model (if set and no model_preference) → bypass router
    # 2. model_preference provided → use ModelRouter
    # 3. Neither → use DEFAULT_MODEL_MODE via router
    conversation_context: list[dict[str, Any]] = []
    try:
        # Get conversation history for classification context
        message_history = await session_storage.get_conversation_history(session_id)
        conversation_context = [
            {"role": msg.role, "content": msg.text_content or ""}
            for msg in message_history[-10:]  # Last 10 messages for context
        ]
    except Exception as ctx_err:
        logger.warning(f"[STREAM MODEL ROUTING] Could not load conversation context: {ctx_err}")

    selected_model, routing_info = await _resolve_model_for_request(
        agent_instance=agent_instance,
        model_preference=msg_request_body.model_preference,
        query=query_from_request,
        context=conversation_context,
    )
    # --- End Model Routing ---

    # Generate an interaction ID for this exchange
    interaction_id = str(uuid.uuid4())

    # Apply the selected model to the agent instance before streaming
    # Use configure_session_with_model to properly rebuild the agent with the new LLM
    if selected_model and hasattr(agent_instance, "configure_session_with_model"):
        try:
            session_config_for_model = {
                "user_id": user_id,
                "session_id": session_id,
            }
            await agent_instance.configure_session_with_model(
                session_config_for_model, selected_model
            )
            logger.debug(
                f"[STREAM] Applied model {selected_model} to agent for session {session_id}"
            )
        except Exception as model_err:
            logger.warning(f"[STREAM] Could not configure model for session: {model_err}")

    # Check if agent has a preprocess_input method to transform the query
    # This allows agents to transform prompt descriptions to content before persistence
    processed_input = agent_input
    if hasattr(agent_instance, "preprocess_input"):
        try:
            processed_input = await agent_instance.preprocess_input(agent_input)
            logger.debug("[STREAM] Agent preprocessed input query")
        except Exception as preprocess_err:
            logger.warning(f"[STREAM] Could not preprocess input: {preprocess_err}")
            processed_input = agent_input

    # Create and persist the user message (using processed input)
    user_text_for_history = _extract_text_for_history_from_input(processed_input)
    user_message = HistoryMessage(
        role="user", text_content=user_text_for_history, interaction_id=interaction_id
    )

    # Get agent identity from the agent instance managed by AgentManager
    agent_identity = StateManager.create_agent_identity(agent_instance)
    await _persist_user_message_to_storage(
        user_id,
        session_id,
        interaction_id,
        user_message,
        agent_identity.agent_id,
        agent_identity.agent_type,
    )

    async def stream_generator():
        nonlocal routing_info, processed_input  # Make routing_info and processed_input accessible
        final_agent_response = None
        # Track ALL parts with their emission order to preserve chronological order
        # Format: list of (order_index, part) tuples
        all_streamed_parts: list[tuple[int, AgentOutputPartUnion]] = []
        part_order_counter = 0
        try:
            start_time = datetime.now(timezone.utc)

            # --- Emit routing event before response chunks ---
            # This allows the UI to display which model was selected and why
            if routing_info:
                model_value = routing_info.get("model")
                routing_event = {
                    "event": "routing",
                    "model": model_value,
                    "model_used": model_value,
                    "model_routed": model_value,
                    "tier": routing_info.get("tier"),
                    "reason": routing_info.get("reason"),
                    "fallback_used": routing_info.get("fallback_used", False),
                    "classification_skipped": routing_info.get("classification_skipped", False),
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                }
                routing_line = f"data: {json.dumps(routing_event, ensure_ascii=False, separators=(',', ':'))}\n\n"
                yield routing_line.encode("utf-8").decode("utf-8")
                logger.debug(
                    f"[STREAM] Emitted routing event: model_used={routing_info.get('model')}, tier={routing_info.get('tier')}"
                )
            # --- End routing event emission ---

            # The handle_message_stream call on the proxy will now stream and save state automatically
            # Note: The selected_model will be used by the agent when task 7 is implemented
            response_stream = agent_instance.handle_message_stream(session_id, processed_input)

            # Check if file storage is available for link processing
            file_storage_available = (
                hasattr(request.app.state, "file_storage_manager")
                and request.app.state.file_storage_manager is not None
            )

            async for output_chunk in response_stream:
                try:
                    # For each yielded StructuredAgentOutput, create a SessionMessageResponse
                    # and send it over SSE.
                    final_agent_response = output_chunk  # Keep track of the latest state

                    # Accumulate ALL parts with their emission order for chronological preservation
                    for part in output_chunk.parts:
                        all_streamed_parts.append((part_order_counter, part))
                        part_order_counter += 1

                    # Process file links in response (only if file storage is available)
                    response_text_processed = output_chunk.response_text
                    parts_processed = output_chunk.parts

                    if file_storage_available:
                        if output_chunk.response_text:
                            response_text_processed = process_response_file_links(
                                output_chunk.response_text
                            )
                        parts_processed = []
                        for part in output_chunk.parts:
                            if isinstance(part, TextOutputPart) and part.text:
                                processed_text = process_response_file_links(part.text)
                                parts_processed.append(TextOutputPart(text=processed_text))
                            else:
                                parts_processed.append(part)

                    # Strip technical_details from parts before sending to frontend
                    # Technical details are only for Elasticsearch storage, not for UI display
                    parts_for_frontend = strip_technical_details(parts_processed)

                    chunk_response = SessionMessageResponse(
                        response_text=response_text_processed,
                        parts=parts_for_frontend,
                        session_id=session_id,
                        user_id=user_id,
                        correlation_id=msg_request_body.correlation_id,
                        interaction_id=interaction_id,
                        # Agent identity fields
                        agent_id=agent_identity.agent_id,
                        agent_type=agent_identity.agent_type,
                        agent_metadata=agent_identity.to_dict(),
                    )
                    # Use explicit JSON serialization to avoid encoding issues
                    json_data = json.dumps(
                        chunk_response.model_dump(), ensure_ascii=False, separators=(",", ":")
                    )
                    # Encode to bytes then decode to ensure proper UTF-8 handling
                    data_line = f"data: {json_data}\n\n"
                    yield data_line.encode("utf-8").decode("utf-8")

                except Exception as chunk_error:
                    logger.error(f"Error processing chunk in stream: {chunk_error}", exc_info=True)
                    # Send error for this chunk but continue streaming
                    error_chunk = {"error": f"Chunk processing error: {str(chunk_error)}"}
                    error_line = f"data: {json.dumps(error_chunk, ensure_ascii=False, separators=(',', ':'))}\n\n"
                    yield error_line.encode("utf-8").decode("utf-8")

            # The stream is finished, now handle final persistence of the complete response
            end_time = datetime.now(timezone.utc)
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            model_used = await agent_instance.get_current_model(session_id)

            # Record API timing metrics for streaming endpoint
            # This captures the real end-to-end timing since middleware can't wait for stream completion
            try:
                from ..monitoring.api_timing_tracker import APITimingData
                from ..monitoring.observability_manager import get_observability_manager

                obs_manager = get_observability_manager()

                # Get LLM metrics from agent if available
                llm_metrics = None
                total_llm_duration = 0.0
                llm_call_count = 0
                if hasattr(agent_instance, "get_llm_metrics"):
                    llm_metrics = agent_instance.get_llm_metrics()
                    if llm_metrics:
                        total_llm_duration = llm_metrics.duration_ms or 0.0
                        llm_call_count = 1

                timing_data = APITimingData(
                    request_start=start_time,
                    request_end=end_time,
                    total_api_duration_ms=processing_time_ms,
                    total_llm_duration_ms=total_llm_duration,
                    llm_call_count=llm_call_count,
                    endpoint="/stream",
                    method="POST",
                    session_id=session_id,
                    user_id=user_id,
                    agent_id=agent_identity.agent_id,
                    is_streaming=True,
                )
                obs_manager.record_api_timing(timing_data)

                # Also record LLM metrics if available
                if llm_metrics:
                    obs_manager.record_llm_call(llm_metrics)

                logger.debug(
                    f"[STREAM] Recorded API timing: {processing_time_ms:.2f}ms, LLM: {total_llm_duration:.2f}ms"
                )
            except Exception as metrics_err:
                logger.warning(f"[STREAM] Failed to record API timing metrics: {metrics_err}")

            # Determine selection mode based on how the model was selected
            # "manual" if user specified a specific model, "auto" if router selected it
            selection_mode: str | None = None
            if msg_request_body.model_preference and msg_request_body.model_preference != "auto":
                selection_mode = "manual"
            elif routing_info is not None:
                selection_mode = "auto"

            if final_agent_response:
                # Merge accumulated parts into final_agent_response.parts
                # This ensures parts are persisted in chronological order (text → activity → text)
                if all_streamed_parts:
                    # Sort by emission order and extract parts to preserve chronological order
                    merged_parts: list[AgentOutputPartUnion] = [
                        part for _, part in sorted(all_streamed_parts, key=lambda x: x[0])
                    ]
                    # Consolidate consecutive text_output_stream into text_output
                    # This reduces noise in history while preserving order with activities
                    consolidated_parts = consolidate_text_parts(merged_parts)
                    # Create a new StructuredAgentOutput with consolidated parts
                    final_agent_response = StructuredAgentOutput(
                        response_text=final_agent_response.response_text,
                        parts=consolidated_parts,
                        streaming_activities=final_agent_response.streaming_activities,
                    )

                await _persist_agent_response_to_storage(
                    user_id=user_id,
                    session_id=session_id,
                    interaction_id=interaction_id,
                    agent_response_obj=final_agent_response,
                    processing_time_ms=processing_time_ms,
                    model_used=model_used,
                    selection_mode=selection_mode,
                    agent_id=agent_identity.agent_id,
                    agent_type=agent_identity.agent_type,
                )

                # Send final message with complete parts to frontend
                # This ensures the frontend receives the same parts array that's stored in ES
                # Strip technical_details before sending to frontend (ES keeps them)
                parts_for_final_response = strip_technical_details(final_agent_response.parts)
                final_response = SessionMessageResponse(
                    response_text=final_agent_response.response_text,
                    parts=parts_for_final_response,
                    session_id=session_id,
                    user_id=user_id,
                    correlation_id=msg_request_body.correlation_id,
                    interaction_id=interaction_id,
                    agent_id=agent_identity.agent_id,
                    agent_type=agent_identity.agent_type,
                    processing_time_ms=processing_time_ms,
                    model_used=model_used,
                    selection_mode=selection_mode,
                )
                final_json = json.dumps(
                    final_response.model_dump(), ensure_ascii=False, separators=(",", ":")
                )
                final_line = f"data: {final_json}\n\n"
                yield final_line.encode("utf-8").decode("utf-8")

                # Trigger async session title generation (non-blocking)
                # This runs in the background after the first exchange to generate a descriptive title
                asyncio.create_task(
                    _auto_generate_session_title_if_needed(
                        user_id=user_id,
                        session_id=session_id,
                        user_message_text=user_text_for_history,
                        agent_response_text=_extract_text_for_history_from_output(
                            final_agent_response
                        ),
                    )
                )

            # Send a final "done" message with model info
            done_message = {
                "status": "done",
                "session_id": session_id,
                "interaction_id": interaction_id,
                "model_used": model_used,
                "model_routed": model_used,
                "selection_mode": selection_mode,
            }
            done_line = (
                f"data: {json.dumps(done_message, ensure_ascii=False, separators=(',', ':'))}\n\n"
            )
            yield done_line.encode("utf-8").decode("utf-8")

        except Exception as e:
            logger.error(f"Error during streaming for session {session_id}: {e}", exc_info=True)
            error_payload = {"error": "An error occurred during processing."}
            error_line = (
                f"data: {json.dumps(error_payload, ensure_ascii=False, separators=(',', ':'))}\n\n"
            )
            yield error_line.encode("utf-8").decode("utf-8")

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.get("/sessions", response_model=list[str])
async def list_sessions_endpoint(
    request: Request,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user whose sessions to list"
    ),
    current_user: str = Depends(get_current_user),
):
    """Lists all active session IDs for a given user_id, filtered by current agent ID."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Get current agent ID from the server's agent class
        temp_agent = request.app.state.agent_class()
        agent_identity = StateManager.create_agent_identity(temp_agent)
        current_agent_id = agent_identity.agent_id

        # Use agent-filtered session retrieval by agent_id (not agent_type)
        user_sessions = await session_storage.get_user_sessions_by_agent(
            user_id, agent_id=current_agent_id
        )
        return user_sessions
    except Exception as e:
        logger.error(f"Error listing sessions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user sessions")


@app.get("/sessions/info", response_model=list[SessionInfo])
async def list_sessions_with_info_endpoint(
    request: Request,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user whose sessions to list"
    ),
    agent_id: str | None = Query(None, description="Filter by specific agent ID"),
    agent_type: str | None = Query(None, description="Filter by specific agent type"),
    current_user: str = Depends(get_current_user),
):
    """Lists all sessions for a user with detailed information including labels, with optional agent filtering."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # If no agent_id filter is provided, use current agent's ID (not type!)
        if not agent_type and not agent_id:
            temp_agent = request.app.state.agent_class()
            agent_identity = StateManager.create_agent_identity(temp_agent)
            agent_id = agent_identity.agent_id  # Use agent_id instead of agent_type

        # Use SessionStorage to get all sessions with info for the user
        sessions_info = await session_storage.list_user_sessions_with_info(user_id)

        # Apply agent filters
        if agent_id or agent_type:
            filtered_sessions = []
            for session in sessions_info:
                # Check agent_id filter (primary filter)
                if agent_id and session.get("agent_id") != agent_id:
                    continue
                # Check agent_type filter (secondary, optional)
                if agent_type and session.get("agent_type") != agent_type:
                    continue
                filtered_sessions.append(session)
            sessions_info = filtered_sessions

        return sessions_info
    except Exception as e:
        logger.error(f"Error listing sessions with info for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user sessions with info")


@app.get("/sessions/info/{session_id}", response_model=SessionInfo)
async def get_session_info_endpoint(
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """Get detailed information for a specific session by its ID."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        session_data = await session_storage.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return SessionInfo(
            session_id=session_data.session_id,
            session_label=session_data.session_label,
            created_at=session_data.created_at,
            updated_at=session_data.updated_at,
            correlation_id=session_data.correlation_id,
            metadata=session_data.metadata,
            agent_id=session_data.agent_id,
            agent_type=session_data.agent_type,
            session_configuration=session_data.session_configuration,
            agent_lifecycle=session_data.agent_lifecycle,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve session info")


@app.get("/sessions/by-correlation/{correlation_id}")
async def get_sessions_by_correlation_endpoint(
    correlation_id: str, current_user: str = Depends(get_current_user)
):
    """Retrieves all sessions across all users that share the same correlation_id."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Check if storage supports correlation search (Elasticsearch only)
        if hasattr(session_storage, "search_sessions_by_correlation"):
            sessions = await session_storage.search_sessions_by_correlation(correlation_id)
            return {
                "correlation_id": correlation_id,
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "user_id": s.user_id,
                        "agent_id": s.agent_id,
                        "agent_type": s.agent_type,
                        "session_label": s.session_label,
                        "created_at": s.created_at,
                        "updated_at": s.updated_at,
                        "metadata": s.metadata,
                    }
                    for s in sessions
                ],
            }
        else:
            # Fallback for non-Elasticsearch storage backends
            return {
                "correlation_id": correlation_id,
                "sessions": [],
                "message": "Correlation search is only available with Elasticsearch storage backend",
            }
    except Exception as e:
        logger.error(f"Error searching for correlation {correlation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search for correlated sessions")


@app.get("/users", response_model=list[str])
async def list_users_endpoint(current_user: str = Depends(get_current_user)):
    """Lists all user IDs who have at least one session. Admin-only endpoint."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Get all users who have sessions
        users_with_sessions = await session_storage.list_all_users_with_sessions()
        # Remove 'admin' from the list as requested - admin should not be displayed as a user
        filtered_users = [user for user in users_with_sessions if user != "admin"]
        return filtered_users
    except Exception as e:
        logger.error(f"Error listing users with sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@app.get("/sessions/{session_id}/history", response_model=list[HistoryMessage])
async def get_history_endpoint(
    session_id: str,
    user_id: str = Query(DEFAULT_USER_ID, description="Identifier for the user owning the session"),
    current_user: str = Depends(get_current_user),
):
    """Retrieves the message history for a specific session_id owned by user_id."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    # Check if session exists
    session_data = await session_storage.load_session(user_id, session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load conversation history from message storage
    message_data_list = await session_storage.get_conversation_history(session_id)

    # Convert MessageData back to HistoryMessage objects
    history = []
    for msg_data in message_data_list:
        history_msg = message_data_to_history_message(msg_data, HistoryMessage)
        history.append(history_msg)

    return history


@app.get("/metadata")
async def get_metadata_endpoint(request: Request, current_user: str = Depends(get_current_user)):
    """Gets the agent's metadata card using the loaded agent class from app.state."""
    # Access the agent_class from app.state, which was set during startup
    agent_class_to_use: type[AgentInterface] = request.app.state.agent_class
    try:
        # Create a temporary instance of the loaded agent class to get metadata
        temp_agent = agent_class_to_use()
        metadata = await temp_agent.get_metadata()
        return metadata
    except Exception as e:
        logger.error(f"Error retrieving metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving metadata")


@app.get("/system-prompt")
async def get_system_prompt_endpoint(
    request: Request, current_user: str = Depends(get_current_user)
):
    """Gets the agent's default system prompt using the loaded agent class from app.state."""
    # Access the agent_class from app.state, which was set during startup
    agent_class_to_use: type[AgentInterface] = request.app.state.agent_class
    try:
        # Create a temporary instance of the loaded agent class to get system prompt
        temp_agent = agent_class_to_use()
        system_prompt = await temp_agent.get_system_prompt()

        if system_prompt is None:
            # Return 404 if no system prompt is configured
            raise HTTPException(
                status_code=404, detail="No default system prompt configured for this agent"
            )

        return {"system_prompt": system_prompt}
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error retrieving system prompt: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving system prompt"
        )


@app.get("/config/models")
async def get_model_configuration(current_user: str = Depends(get_current_user)) -> dict[str, Any]:
    """Get model configuration information including supported models and providers."""
    try:
        config_status = model_config.validate_configuration()
        model_list = model_config.get_model_list()
        supported_providers = client_factory.get_supported_providers()

        return {
            "default_model": model_config.default_model,
            "configuration_status": config_status,
            "supported_models": model_list,
            "supported_providers": supported_providers,
            "fallback_provider": model_config.fallback_provider.value,
        }
    except Exception as e:
        logger.error(f"Error retrieving model configuration: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving model configuration"
        )


# --- Display Configuration API Endpoint --- >


class DisplayConfigResponse(BaseModel):
    """Response model for display configuration."""

    steps: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Display info for steps"
    )
    tools: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Display info for tools"
    )
    events: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Display info for events"
    )
    agent_id: str | None = Field(None, description="Agent ID if agent-specific config requested")


class DisplayConfigUpdateRequest(BaseModel):
    """Request model for updating display configuration."""

    steps: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Step display overrides"
    )
    tools: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Tool display overrides"
    )
    events: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Event display overrides"
    )


@app.get("/config/display", response_model=DisplayConfigResponse)
async def get_display_config_endpoint(
    agent_id: str | None = Query(
        None, description="Optional agent ID for agent-specific overrides"
    ),
    current_user: str = Depends(get_current_user),
) -> DisplayConfigResponse:
    """
    Get display configuration for steps, tools, and events.

    Returns merged configuration (defaults + agent overrides if agent_id provided).
    """
    try:
        # Create manager (will use memory storage for now)
        manager = DisplayConfigManager()

        # Get merged config
        config = await manager.get_merged_config(agent_id=agent_id)

        return DisplayConfigResponse(
            steps={k: v.model_dump() for k, v in config.steps.items()},
            tools={k: v.model_dump() for k, v in config.tools.items()},
            events={k: v.model_dump() for k, v in config.events.items()},
            agent_id=agent_id,
        )
    except Exception as e:
        logger.error(f"[GET /config/display] Error retrieving display configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve display configuration: {str(e)}"
        )


@app.post("/config/display", response_model=DisplayConfigResponse)
async def update_display_config_endpoint(
    config_update: DisplayConfigUpdateRequest,
    agent_id: str = Query(..., description="Agent ID for scoped overrides (required)"),
    current_user: str = Depends(get_current_user),
) -> DisplayConfigResponse:
    """
    Update display configuration overrides for an agent.

    Accepts partial overrides that are merged with defaults.
    Requires agent_id to scope the overrides.
    """
    try:
        from ..core.step_display_config import StepDisplayConfig, StepDisplayInfo

        # Parse the request into StepDisplayConfig
        steps: dict[str, StepDisplayInfo] = {}
        for k, v in config_update.steps.items():
            try:
                steps[k] = StepDisplayInfo(**v)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid step config for '{k}': {e}")

        tools: dict[str, StepDisplayInfo] = {}
        for k, v in config_update.tools.items():
            try:
                tools[k] = StepDisplayInfo(**v)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid tool config for '{k}': {e}")

        events: dict[str, StepDisplayInfo] = {}
        for k, v in config_update.events.items():
            try:
                events[k] = StepDisplayInfo(**v)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid event config for '{k}': {e}")

        overrides = StepDisplayConfig(steps=steps, tools=tools, events=events)

        # Create manager and set overrides
        manager = DisplayConfigManager()
        success = await manager.set_overrides(agent_id, overrides)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save display configuration overrides"
            )

        # Return updated merged config
        config = await manager.get_merged_config(agent_id=agent_id)

        return DisplayConfigResponse(
            steps={k: v.model_dump() for k, v in config.steps.items()},
            tools={k: v.model_dump() for k, v in config.tools.items()},
            events={k: v.model_dump() for k, v in config.events.items()},
            agent_id=agent_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /config/display] Error updating display configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update display configuration: {str(e)}"
        )


# --- Model Router API Endpoint --- >


@app.get("/api/models")
async def get_available_models_endpoint(
    current_user: str = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get available models grouped by tier with availability status.

    Returns models organized by tier (light, standard, advanced) with
    availability information based on configured API keys.
    """
    from ..core.model_router import model_router

    try:
        models_by_tier = model_router.get_available_models()

        return {
            "models_by_tier": models_by_tier,
            "default_mode": model_router.default_mode,
            "classifier_model": model_router.classifier_model,
        }
    except Exception as e:
        logger.error(f"Error retrieving available models: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving available models"
        )


# --- Configuration Management API Endpoints --- >


class AgentConfigUpdate(BaseModel):
    """Request model for updating agent configuration."""

    config: dict[str, Any] = Field(..., description="Agent configuration dictionary")
    agent_type: str | None = Field(None, description="Type of agent")
    updated_by: str | None = Field(None, description="User who updated the config")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    active: bool = Field(True, description="Whether configuration is active")


class AgentConfigResponse(BaseModel):
    """Response model for agent configuration."""

    agent_id: str = Field(..., description="Agent identifier")
    config: dict[str, Any] = Field(..., description="Agent configuration")
    version: int = Field(..., description="Configuration version")
    updated_at: str = Field(..., description="Last update timestamp")
    source: str = Field(..., description="Configuration source (elasticsearch, hardcoded, default)")
    agent_type: str | None = Field(None, description="Type of agent")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    active: bool | None = Field(None, description="Whether configuration is active")


class AgentConfigVersionResponse(BaseModel):
    """Response model for configuration version history."""

    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    version: int = Field(..., description="Configuration version")
    updated_at: str = Field(..., description="Update timestamp")
    updated_by: str = Field(..., description="User who updated")
    config: dict[str, Any] = Field(..., description="Configuration at this version")
    metadata: dict[str, Any] = Field(..., description="Version metadata")
    active: bool = Field(..., description="Whether this version is active")


@app.get("/config/agents/{agent_id}", response_model=AgentConfigResponse)
async def get_agent_config_endpoint(
    agent_id: str, current_user: str = Depends(get_current_user)
) -> AgentConfigResponse:
    """
    Get current effective configuration for an agent.

    Returns configuration from Elasticsearch if available, otherwise falls back to
    hardcoded or default configuration.

    """
    try:
        # Check if we have an enhanced model config manager with ES support
        if isinstance(model_config, type(model_config).__bases__[0]):
            # Standard ModelConfigManager - no ES support
            logger.warning(
                f"[GET /config/agents/{agent_id}] EnhancedModelConfigManager not initialized. "
                "Using default configuration."
            )
            default_config = {
                "system_prompt": "You are a helpful AI assistant.",
                "model_name": model_config.default_model,
                "model_config": {"temperature": 0.7, "max_tokens": 2000},
            }
            return AgentConfigResponse(
                agent_id=agent_id,
                config=default_config,
                version=0,
                updated_at=datetime.utcnow().isoformat(),
                source="default",
                agent_type="unknown",
            )

        # Get configuration with priority resolution
        config_with_source = await model_config.get_agent_configuration(agent_id)

        # Extract source and remove from config
        source = config_with_source.pop("_source", "unknown")

        # Determine version (0 for non-ES sources)
        version = 0
        updated_at = datetime.utcnow().isoformat()
        agent_type = "unknown"
        metadata = {}
        active = True

        # If from Elasticsearch, try to get additional metadata
        if source == "elasticsearch" and await model_config._ensure_es_provider_initialized():
            try:
                assert model_config._es_config_provider is not None
                versions = await model_config._es_config_provider.get_config_versions(
                    agent_id, limit=1
                )
                if versions:
                    latest = versions[0]
                    version = latest.get("version", 0)
                    updated_at = latest.get("updated_at", updated_at)
                    agent_type = latest.get("agent_type", agent_type)
                    metadata = latest.get("metadata", {})
                    active = latest.get("active", True)
            except Exception as e:
                logger.warning(f"[GET /config/agents/{agent_id}] Failed to get version info: {e}")

        return AgentConfigResponse(
            agent_id=agent_id,
            config=config_with_source,
            version=version,
            updated_at=updated_at,
            source=source,
            agent_type=agent_type,
            metadata=metadata,
            active=active,
        )

    except Exception as e:
        logger.error(f"[GET /config/agents/{agent_id}] Error retrieving configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent configuration: {str(e)}"
        )


@app.put("/config/agents/{agent_id}", response_model=AgentConfigResponse)
async def update_agent_config_endpoint(
    agent_id: str, config_update: AgentConfigUpdate, current_user: str = Depends(get_current_user)
) -> AgentConfigResponse:
    """
    Update agent configuration in Elasticsearch.

    Creates a new version of the configuration, deactivates old versions,
    and invalidates the cache. Returns HTTP 503 if Elasticsearch is unavailable.

    """
    try:
        # Ensure ES config provider is initialized
        if not await model_config._ensure_es_provider_initialized():
            logger.error(
                f"[PUT /config/agents/{agent_id}] Elasticsearch config provider not available"
            )
            raise HTTPException(
                status_code=503, detail="Elasticsearch configuration service is unavailable"
            )

        # Update configuration (now returns doc_id, version, agent_id)
        assert (
            model_config._es_config_provider is not None
        )  # Guaranteed by _ensure_es_provider_initialized
        result = await model_config._es_config_provider.update_agent_config(
            agent_id=agent_id,
            config=config_update.config,
            agent_type=config_update.agent_type,
            updated_by=config_update.updated_by or current_user,
            metadata=config_update.metadata,
            active=config_update.active,
        )

        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to update configuration in Elasticsearch"
            )

        # Extract doc_id and version from result
        doc_id = result["doc_id"]
        version = result["version"]

        # Get the full configuration details
        assert (
            model_config._es_config_provider is not None
        )  # Guaranteed by _ensure_es_provider_initialized
        versions = await model_config._es_config_provider.get_config_versions(agent_id, limit=1)

        if not versions:
            raise HTTPException(
                status_code=500, detail="Configuration updated but failed to retrieve new version"
            )

        latest = versions[0]

        return AgentConfigResponse(
            agent_id=agent_id,
            config=latest["config"],
            version=version,
            updated_at=latest["updated_at"],
            source="elasticsearch",
            agent_type=latest.get("agent_type"),
            metadata=latest.get("metadata", {}),
            active=latest.get("active", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /config/agents/{agent_id}] Error updating configuration: {e}")
        # Check if it's an ES connection error
        if "ConnectionError" in str(type(e).__name__) or "elasticsearch" in str(e).lower():
            raise HTTPException(status_code=503, detail="Elasticsearch service is unavailable")
        raise HTTPException(
            status_code=500, detail=f"Failed to update agent configuration: {str(e)}"
        )


@app.get("/config/agents/{agent_id}/versions", response_model=list[AgentConfigVersionResponse])
async def get_agent_config_versions_endpoint(
    agent_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of versions to return"),
    current_user: str = Depends(get_current_user),
) -> list[AgentConfigVersionResponse]:
    """
    Get configuration version history for an agent.

    Returns all configuration versions in chronological order (newest first).

    """
    try:
        # Ensure ES config provider is initialized
        if not await model_config._ensure_es_provider_initialized():
            logger.warning(
                f"[GET /config/agents/{agent_id}/versions] "
                "Elasticsearch config provider not available"
            )
            return []

        # Get version history
        assert (
            model_config._es_config_provider is not None
        )  # Guaranteed by _ensure_es_provider_initialized
        versions = await model_config._es_config_provider.get_config_versions(agent_id, limit=limit)
        # Convert to response models
        return [
            AgentConfigVersionResponse(
                agent_id=v["agent_id"],
                agent_type=v.get("agent_type", "unknown"),
                version=v["version"],
                updated_at=v["updated_at"],
                updated_by=v.get("updated_by", "unknown"),
                config=v["config"],
                metadata=v.get("metadata", {}),
                active=v.get("active", True),
            )
            for v in versions
        ]

    except Exception as e:
        logger.error(
            f"[GET /config/agents/{agent_id}/versions] Error retrieving version history: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configuration version history: {str(e)}"
        )


@app.delete("/config/agents/{agent_id}")
async def delete_agent_config_endpoint(
    agent_id: str, current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Delete all configurations for an agent.

    Removes all configuration versions from Elasticsearch and invalidates the cache.
    After deletion, the agent will fall back to hardcoded or default configuration.

    """
    try:
        # Ensure ES config provider is initialized
        if not await model_config._ensure_es_provider_initialized():
            logger.error(
                f"[DELETE /config/agents/{agent_id}] Elasticsearch config provider not available"
            )
            raise HTTPException(
                status_code=503, detail="Elasticsearch configuration service is unavailable"
            )

        # Delete configuration
        assert (
            model_config._es_config_provider is not None
        )  # Guaranteed by _ensure_es_provider_initialized
        success = await model_config._es_config_provider.delete_agent_config(agent_id)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to delete configuration from Elasticsearch"
            )

        logger.info(
            f"[DELETE /config/agents/{agent_id}] Configuration deleted. "
            "Agent will now use fallback configuration."
        )

        return {
            "success": True,
            "message": f"All configurations for agent {agent_id} have been deleted",
            "agent_id": agent_id,
            "fallback_behavior": "Agent will now use hardcoded or default configuration",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /config/agents/{agent_id}] Error deleting configuration: {e}")
        # Check if it's an ES connection error
        if "ConnectionError" in str(type(e).__name__) or "elasticsearch" in str(e).lower():
            raise HTTPException(status_code=503, detail="Elasticsearch service is unavailable")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete agent configuration: {str(e)}"
        )


# < --- Configuration Management API Endpoints ---


@app.post("/admin/authenticate")
async def authenticate_admin_endpoint(request: dict, current_user: str = Depends(get_current_user)):
    """
    Validates admin password for accessing admin features.
    This is a secondary authentication layer on top of the base auth.
    """
    try:
        password = request.get("password", "")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        # Use secrets.compare_digest for timing-safe comparison
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            return {"success": True, "message": "Admin authentication successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid admin password")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root(current_user: str = Depends(get_current_user)):
    return {
        "message": "Agent server is running. Visit /docs for API documentation or /ui for a interface human friendly with agent."
    }


# --- File Storage Endpoints --- >
@app.post("/files/upload")
async def upload_file(
    file: UploadFile,
    user_id: str = Query(...),
    session_id: str = Query(None),
    current_user: str = Depends(get_current_user),
):
    """Upload file to storage"""
    try:
        content = await file.read()

        file_id = await app.state.file_storage_manager.store_file(
            content=content,
            filename=file.filename or "upload",
            user_id=user_id,
            session_id=session_id,
            mime_type=file.content_type,
            is_generated=False,
        )

        logger.info(f"File uploaded: {file_id} ({file.filename}) by user {user_id}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size_bytes": len(content),
            "mime_type": file.content_type,
        }

    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    inline: bool = Query(False, description="If true, display inline instead of forcing download"),
    current_user: str = Depends(get_current_user),
):
    """Download file from storage. Use ?inline=true to display in browser instead of downloading."""
    try:
        logger.info(
            f"🔽 DOWNLOAD ENDPOINT - Attempting to download file: {file_id} for user: {current_user}, inline={inline}"
        )

        # Check if file storage manager is available
        if not hasattr(app.state, "file_storage_manager") or not app.state.file_storage_manager:
            logger.error("❌ DOWNLOAD ENDPOINT - File storage manager not available")
            raise HTTPException(status_code=500, detail="File storage system not available")

        # Attempt to retrieve the file
        content, metadata = await app.state.file_storage_manager.retrieve_file(file_id)
        logger.info(
            f"📄 DOWNLOAD ENDPOINT - File metadata: mime_type={metadata.mime_type}, storage_path={metadata.storage_path}"
        )

        # Use inline disposition for browser display, attachment for forced download
        disposition = "inline" if inline else "attachment"
        return StreamingResponse(
            io.BytesIO(content),
            media_type=metadata.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f"{disposition}; filename={metadata.filename}"},
        )

    except FileNotFoundError as e:
        logger.error(f"❌ DOWNLOAD ENDPOINT - File not found: {file_id} - {e}")
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"❌ DOWNLOAD ENDPOINT - Failed to download file {file_id}: {e}")
        logger.error(f"❌ DOWNLOAD ENDPOINT - Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ DOWNLOAD ENDPOINT - Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@app.get("/files/{file_id}/view")
async def view_file(file_id: str):
    """View file inline in browser (for displaying images in chat, etc.)

    This endpoint is PUBLIC (no authentication required) to allow images
    to be displayed directly in chat via <img src="..."> tags.
    Security is provided by the UUID file_id which is hard to guess.

    Unlike /download which forces file download and requires auth, this endpoint
    displays the file directly in the browser using Content-Disposition: inline.

    Use this endpoint for:
    - Displaying generated images (charts, diagrams) in chat
    - Viewing PDFs inline
    - Any file that should be displayed rather than downloaded
    """
    try:
        logger.info(f"👁️ VIEW ENDPOINT - Viewing file: {file_id} (public access)")

        if not hasattr(app.state, "file_storage_manager") or not app.state.file_storage_manager:
            logger.error("❌ VIEW ENDPOINT - File storage manager not available")
            raise HTTPException(status_code=500, detail="File storage system not available")

        content, metadata = await app.state.file_storage_manager.retrieve_file(file_id)
        logger.info(
            f"📄 VIEW ENDPOINT - File metadata: mime_type={metadata.mime_type}, filename={metadata.filename}"
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=metadata.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f"inline; filename={metadata.filename}"},
        )

    except FileNotFoundError as e:
        logger.error(f"❌ VIEW ENDPOINT - File not found: {file_id} - {e}")
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"❌ VIEW ENDPOINT - Failed to view file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to view file: {str(e)}")


@app.get("/files/{file_id}/metadata")
async def get_file_metadata(file_id: str, current_user: str = Depends(get_current_user)):
    """Get file metadata"""
    try:
        metadata = await app.state.file_storage_manager.get_file_metadata(file_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "file_id": metadata.file_id,
            "filename": metadata.filename,
            "mime_type": metadata.mime_type,
            "size_bytes": metadata.size_bytes,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "user_id": metadata.user_id,
            "session_id": metadata.session_id,
            "agent_id": metadata.agent_id,
            "is_generated": metadata.is_generated,
            "tags": metadata.tags,
            "storage_backend": metadata.storage_backend,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@app.get("/files/{file_id}/preview")
async def preview_file(file_id: str, current_user: str = Depends(get_current_user)):
    """Preview file content optimized for UI display"""
    try:
        # First check if file exists and get metadata
        metadata = await app.state.file_storage_manager.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Get the file content
        content, _ = await app.state.file_storage_manager.retrieve_file(file_id)

        # Determine preview type and prepare content
        mime_type = metadata.mime_type or "application/octet-stream"
        preview_type = "not_supported"
        preview_content = None
        content_base64 = None
        html_preview = None
        preview_available = True
        message = "Preview ready"

        # Handle different file types
        if mime_type.startswith("text/"):
            # Text files - return decoded content
            preview_type = "text"
            try:
                preview_content = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    preview_content = content.decode("latin-1")
                except UnicodeDecodeError:
                    preview_content = content.decode("utf-8", errors="replace")

        elif mime_type.startswith("image/"):
            # Images - return base64 encoded content
            preview_type = "image"
            content_base64 = base64.b64encode(content).decode("utf-8")

        elif mime_type == "application/json":
            # JSON files - format for display
            preview_type = "json"
            try:
                json_data = json.loads(content.decode("utf-8"))
                preview_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, UnicodeDecodeError):
                preview_type = "text"
                preview_content = content.decode("utf-8", errors="replace")

        elif mime_type in ["text/markdown", "application/markdown"]:
            # Markdown files - return both raw and HTML
            preview_type = "markdown"
            try:
                preview_content = content.decode("utf-8")
                # For HTML preview, we'd need a markdown library
                # For now, just return the raw markdown
                html_preview = preview_content  # TODO: Convert to HTML
            except UnicodeDecodeError:
                preview_content = content.decode("utf-8", errors="replace")
                html_preview = preview_content

        elif mime_type == "application/pdf":
            # PDF files - try to extract text or indicate preview not available
            preview_type = "binary"
            preview_available = False
            message = "PDF preview requires text extraction - use download instead"

        else:
            # Other binary files
            preview_type = "binary"
            preview_available = False
            message = f"Preview not available for {metadata.filename} ({mime_type})"

        # Build response
        response_data = {
            "file_id": file_id,
            "filename": metadata.filename,
            "mime_type": mime_type,
            "size_bytes": metadata.size_bytes,
            "preview_type": preview_type,
            "preview_available": preview_available,
            "message": message,
            "metadata": {
                "created_at": metadata.created_at.isoformat(),
                "is_generated": metadata.is_generated,
                "tags": metadata.tags,
                "session_id": metadata.session_id,
            },
        }

        # Add content based on type
        if preview_content is not None:
            response_data["content"] = preview_content
        if content_base64 is not None:
            response_data["content_base64"] = content_base64
        if html_preview is not None:
            response_data["html_preview"] = html_preview

        logger.info(f"File preview generated: {file_id} ({metadata.filename}) - {preview_type}")
        return response_data

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Failed to preview file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview file: {str(e)}")


@app.get("/files")
async def list_files(
    user_id: str = Query(...),
    session_id: str = Query(None),
    is_generated: bool = Query(None),
    current_user: str = Depends(get_current_user),
):
    """List files with filtering"""
    try:
        logger.info(
            f"🔍 FILES ENDPOINT - Parameters: user_id={user_id}, session_id={session_id}, is_generated={is_generated}"
        )

        files = await app.state.file_storage_manager.list_files(
            user_id=user_id, session_id=session_id, is_generated=is_generated
        )

        logger.info(f"📁 FILES ENDPOINT - Found {len(files)} files from storage manager")

        result = [
            {
                "file_id": f.file_id,
                "filename": f.filename,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "created_at": f.created_at.isoformat(),
                "is_generated": f.is_generated,
                "session_id": f.session_id,
                "tags": f.tags,
            }
            for f in files
        ]

        logger.info(f"✅ FILES ENDPOINT - Returning {len(result)} files")
        return result

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.delete("/files/{file_id}")
async def delete_file(file_id: str, current_user: str = Depends(get_current_user)):
    """Delete file from storage"""
    try:
        success = await app.state.file_storage_manager.delete_file(file_id)

        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(f"File deleted: {file_id} by user {current_user}")

        return {"success": True, "message": f"File {file_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@app.get("/files/stats")
async def get_file_storage_stats(current_user: str = Depends(get_current_user)):
    """Get file storage system statistics"""
    try:
        backend_info = app.state.file_storage_manager.get_backend_info()
        return backend_info

    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


# < --- File Storage Endpoints ---

# --- New Endpoint for Help/Listing --- >
# --- Agent-focused API endpoints --- >


@app.get("/agents", summary="List all agent types and their usage statistics")
async def list_agents_endpoint(current_user: str = Depends(get_current_user)) -> dict[str, Any]:
    """Get all agent types and their usage statistics."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        usage_stats = await session_storage.get_agent_usage_statistics()
        return {"success": True, "data": usage_stats}
    except Exception as e:
        logger.error(f"Error retrieving agent statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error retrieving agent statistics"
        )


@app.get("/agents/{agent_type}/sessions", summary="Get sessions for a specific agent type")
async def list_agent_type_sessions_endpoint(
    agent_type: str,
    user_id: str | None = Query(None, description="Filter by specific user"),
    current_user: str = Depends(get_current_user),
) -> dict[str, Any]:
    """List all sessions for a specific agent type, optionally filtered by user."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        if user_id:
            # Get sessions for specific user and agent type
            sessions = await session_storage.get_user_sessions_by_agent(
                user_id, agent_type=agent_type
            )
        else:
            # Get all sessions for agent type
            sessions = await session_storage.list_sessions_by_agent_type(agent_type)

        return {
            "success": True,
            "agent_type": agent_type,
            "user_id": user_id,
            "session_count": len(sessions),
            "sessions": sessions,
        }
    except Exception as e:
        logger.error(f"Error retrieving sessions for agent type {agent_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error retrieving sessions for agent type {agent_type}",
        )


@app.get("/agents/{agent_id}/lifecycle", summary="Get lifecycle events for a specific agent")
async def get_agent_lifecycle_endpoint(
    agent_id: str, current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    """Get lifecycle events for a specific agent instance."""
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        lifecycle_events = await session_storage.get_agent_lifecycle_events(agent_id)

        # Convert AgentLifecycleData objects to dictionaries for JSON response
        events_data = []
        for event in lifecycle_events:
            event_dict = {
                "lifecycle_id": event.lifecycle_id,
                "agent_id": event.agent_id,
                "agent_type": event.agent_type,
                "event_type": event.event_type,
                "session_id": event.session_id,
                "user_id": event.user_id,
                "timestamp": event.timestamp,
                "metadata": event.metadata,
            }
            events_data.append(event_dict)

        return {
            "success": True,
            "agent_id": agent_id,
            "event_count": len(events_data),
            "events": events_data,
        }
    except Exception as e:
        logger.error(f"Error retrieving lifecycle events for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error retrieving lifecycle events for agent {agent_id}",
        )


@app.get("/endpoints", summary="List available API endpoints")
async def list_api_endpoints(request: Request, current_user: str = Depends(get_current_user)):
    """
    Retrieves a list of all available API endpoints in the application,
    excluding WebSocket routes and static file mounts if desired.
    """
    route_list = []
    excluded_paths = {"/openapi.json", "/docs", "/redoc", "/endpoints", "/ui"}  # Exclude ui too

    for route in request.app.routes:
        if isinstance(route, APIRoute) and route.path not in excluded_paths:
            endpoint_info = {
                "path": route.path,
                "methods": list(route.methods),
                "summary": route.summary or "",  # Use defined summary if available
                "description": (
                    route.endpoint.__doc__.strip() if route.endpoint.__doc__ else "No description."
                ),
                "parameters": [],
                "request_body": None,
            }

            # Extract Path and Query Parameters (from Pydantic models if available)
            # Note: This gives basic info; more complex dependencies might not be fully captured.
            if hasattr(route, "dependant") and route.dependant:
                if route.dependant.path_params:
                    for param in route.dependant.path_params:
                        endpoint_info["parameters"].append(
                            {
                                "name": param.name,
                                "in": "path",
                                "required": True,
                                "type": (
                                    str(param.type_.__name__)
                                    if hasattr(param.type_, "__name__")
                                    else str(param.type_)
                                ),
                            }
                        )
                if route.dependant.query_params:
                    for param in route.dependant.query_params:
                        endpoint_info["parameters"].append(
                            {
                                "name": param.name,
                                "in": "query",
                                "required": param.required,
                                "type": (
                                    str(param.type_.__name__)
                                    if hasattr(param.type_, "__name__")
                                    else str(param.type_)
                                ),
                            }
                        )

                # Extract Request Body Info
                if route.dependant.body_params:
                    # Assuming one body param for simplicity, often the case
                    body_param = route.dependant.body_params[0]
                    body_model = body_param.type_
                    if hasattr(body_model, "__name__"):
                        endpoint_info["request_body"] = {
                            "model": body_model.__name__,
                            "required": body_param.required,
                            # Potentially list fields of the model here if needed
                        }
                    else:
                        endpoint_info["request_body"] = {
                            "type": str(body_model),
                            "required": body_param.required,
                        }

            route_list.append(endpoint_info)

    return route_list


# < --- New Endpoint --- >


@app.get("/ui", response_class=FileResponse, summary="Serve the modern UI application")
async def get_modern_ui(current_user: str = Depends(get_current_user)):
    """
    Serves the modern HTML UI application based on HTMX, Alpine.js, and BaseCoat UI.
    This is the new UI that coexists with the existing ui until migration is complete.
    """
    file_path = os.path.join(os.path.dirname(__file__), "modern_ui.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="modern_ui.html not found")
    return FileResponse(file_path)


# --- New Endpoint to Serve Test App --- >
@app.get("/testapp", response_class=FileResponse, summary="Serve the HTML test application")
async def get_test_app(current_user: str = Depends(get_current_user)):
    """
    Serves the static HTML test application.
    Ensure 'ui.html' is in the same directory as this server script or provide the correct path.
    """
    file_path = os.path.join(os.path.dirname(__file__), "test_app.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="test_app.html not found")
    return FileResponse(file_path)


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    """
    Serves a simple favicon or returns 204 No Content.
    This prevents 404 errors in browser requests.
    """
    # Check if a favicon file exists
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        # Return proper 204 No Content with explicit headers
        from fastapi.responses import Response

        return Response(status_code=204, headers={"Content-Length": "0"})


# Mount the React build directory using absolute path (if it exists)
react_build_path = os.path.join(os.path.dirname(__file__), "front", "chat", "dist")
if os.path.exists(react_build_path):
    app.mount("/static", StaticFiles(directory=react_build_path), name="static")
    logger.info(f"Mounted static files from: {react_build_path}")
else:
    logger.warning(
        f"React build directory not found: {react_build_path}. Static files not mounted."
    )


# --- Server Startup Helper Function --- >
def start_server(
    agent_class_to_serve: type[AgentInterface],
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
):
    """Configures and starts the Uvicorn server."""
    # This function might not be directly used if AGENT_CLASS_PATH is set for startup,
    # but kept for potential direct calls or future use.
    # global _AGENT_CLASS_TO_SERVE # Removed global as startup event handles it
    logger.info(
        f"Agent class passed to start_server (may be overridden by env var): {agent_class_to_serve.__name__}"
    )

    # Read host, port, and reload from environment variables, using provided function args as defaults
    host = os.getenv("AGENT_HOST", host)
    port = int(os.getenv("AGENT_PORT", str(port)))
    # Default reload to True if AGENT_RELOAD is not explicitly set to 'false'
    reload_env = os.getenv("AGENT_RELOAD", "true").lower()
    reload = reload_env != "false"

    logger.info(
        "Attempting to start Generic Agent Server (Agent loaded via AGENT_CLASS_PATH on startup)"
    )
    logger.info(f"Listening on {host}:{port} - Reload: {reload}")

    # Run the Uvicorn server - needs import string for reload
    # When reload is enabled, we need the full module path
    if reload:
        # For reload mode, use the full module path
        app_import_string = "agent_framework.server:app"
    else:
        # For non-reload mode, can use the app directly
        app_import_string = app

    logger.info(f"Using import string: {app_import_string}")

    uvicorn.run(app_import_string, host=host, port=port, reload=reload)


# < --- Server Startup Helper Function --- >


# --- Internal Helper for Dynamic Loading (used only in server.py's __main__) --- >
def _load_agent_dynamically_internal() -> type[AgentInterface]:
    # This function is problematic because it tries to load the agent *before* uvicorn potentially reloads.
    # The environment variable AGENT_CLASS_PATH set *before* running `python server.py`
    # combined with the startup event is the robust way.
    # Keeping this block but noting its potential issues if AGENT_CLASS_PATH isn't pre-set.
    agent_path = os.environ.get("AGENT_CLASS_PATH")
    if agent_path:
        try:
            return _load_agent_dynamically()  # Use the main loader
        except Exception as e:
            logger.error(
                f"Fatal Error in __main__: Could not load agent from AGENT_CLASS_PATH='{agent_path}'. {e}"
            )
            raise SystemExit(e)
    else:
        # Fallback to old environment variables if AGENT_CLASS_PATH is not set (less recommended)
        logger.warning(
            "Warning: AGENT_CLASS_PATH not set. Falling back to AGENT_MODULE/AGENT_CLASS (might not work reliably with reload)."
        )
        agent_module_name = os.getenv("AGENT_MODULE", "agent")  # Default module
        agent_class_name = os.getenv("AGENT_CLASS", "PersonalAssistantAgent")  # Default class
        try:
            module = importlib.import_module(agent_module_name)
            agent_class = getattr(module, agent_class_name)
            if not issubclass(agent_class, AgentInterface):
                raise TypeError(f"{agent_class_name} does not implement AgentInterface")
            # Manually set the environment variable so the startup event can find it
            # This is a workaround for running `python server.py` without pre-setting AGENT_CLASS_PATH
            os.environ["AGENT_CLASS_PATH"] = f"{agent_module_name}:{agent_class_name}"
            return agent_class
        except Exception as e:
            logger.error(
                f"Fatal Error in __main__: Could not load agent using fallback AGENT_MODULE/AGENT_CLASS. {e}"
            )
            raise SystemExit(e)


# < --- Internal Helper --- >

# --- Server Startup Main Block --- >
if __name__ == "__main__":
    # When running server.py directly, ensure AGENT_CLASS_PATH is available for the startup event.
    # The helper above tries to load it or set it based on older env vars.
    loaded_agent_class_for_start_server = _load_agent_dynamically_internal()
    # Call start_server. The actual agent used will be determined by the startup event
    # using the AGENT_CLASS_PATH environment variable.
    start_server(loaded_agent_class_for_start_server)
# < --- Server Startup Main Block --- >

# --- Session Workflow Endpoints (New) --- >


# Define new models for session initialization and feedback
class SessionInitRequest(BaseModel):
    user_id: str
    correlation_id: str | None = None
    session_id: str | None = None
    data: dict[str, Any] | None = None
    configuration: dict[str, Any] = Field(..., description="Session configuration")


class SessionInitResponse(BaseModel):
    user_id: str
    correlation_id: str | None = None
    session_id: str
    data: dict[str, Any] | None = None
    configuration: dict[str, Any]
    # Agent identity fields
    agent_id: str | None = None
    agent_type: str | None = None
    # Welcome message for new sessions
    welcome_message: str | None = None


class SessionEndRequest(BaseModel):
    session_id: str


class MessageFeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    feedback: Literal["up", "down"]


class SessionFlagRequest(BaseModel):
    session_id: str
    flag_message: str


class SessionLabelUpdateRequest(BaseModel):
    session_id: str
    label: str = Field(..., max_length=100, description="Session label (max 100 characters)")


class SessionFeedbackRequest(BaseModel):
    session_id: str
    rating: int = Field(..., ge=1, le=5, description="Session rating from 1 to 5")
    comment: str | None = Field(None, max_length=1000, description="Optional feedback comment")


def _template_system_prompt(base_prompt: str, data: Any) -> str:
    """
    Template a system prompt with data using advanced string replacement.
    Supports:
    - {{data}} for the entire data object
    - {{data.key}} for accessing dictionary keys with data prefix
    - {{data.key.subkey}} for nested access with data prefix
    - {{key}} for direct access without data prefix
    - {{key.subkey}} for nested access without data prefix
    """
    if not data or not base_prompt:
        return base_prompt or ""

    import re

    if isinstance(data, str):
        # Simple case: replace {{data}} with the string
        templated = base_prompt.replace("{{data}}", data)
        # Also replace any {{key}} if data is just a string value
        return templated
    elif isinstance(data, dict):
        # Complex case: support multiple template patterns
        templated = base_prompt

        # Replace {{data}} with the entire JSON object
        templated = templated.replace("{{data}}", json.dumps(data, indent=2))

        # Handle nested access like {{data.key}} or {{data.key.subkey}}
        data_pattern = r"\{\{data\.([^}]+)\}\}"
        data_matches = re.findall(data_pattern, templated)

        for match in data_matches:
            keys = match.split(".")
            value = data
            try:
                for key in keys:
                    if isinstance(value, dict):
                        value = value[key]
                    else:
                        # Can't traverse further
                        break
                templated = templated.replace(f"{{{{data.{match}}}}}", str(value))
            except (KeyError, TypeError, AttributeError):
                # Leave placeholder if key doesn't exist
                logger.warning(f"Template key 'data.{match}' not found in data")
                pass

        # Handle direct access like {{key}} or {{key.subkey}} (without data prefix)
        direct_pattern = r"\{\{(?!data\.)([^}]+)\}\}"
        direct_matches = re.findall(direct_pattern, templated)

        for match in direct_matches:
            keys = match.split(".")
            value = data
            try:
                for key in keys:
                    if isinstance(value, dict):
                        value = value[key]
                    else:
                        # Can't traverse further
                        break
                templated = templated.replace(f"{{{{{match}}}}}", str(value))
            except (KeyError, TypeError, AttributeError):
                # Leave placeholder if key doesn't exist
                logger.warning(f"Template key '{match}' not found in data")
                pass

        return templated
    else:
        # For other types (list, etc.), convert to string and replace {{data}}
        return base_prompt.replace(
            "{{data}}", json.dumps(data) if isinstance(data, (list, tuple)) else str(data)
        )


@app.post("/init", response_model=SessionInitResponse)
async def init_session_endpoint(
    init_request: SessionInitRequest,
    request: Request,
    current_user: str = Depends(get_current_user),
):
    """
    Initialize a new session for a user using SessionStorage with agent identity tracking.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Use provided session_id or generate new one
        session_id = init_request.session_id or str(uuid.uuid4())

        # Check if session already exists
        existing_session = await session_storage.load_session(init_request.user_id, session_id)
        if existing_session:
            raise HTTPException(
                status_code=409,
                detail=f"Session {session_id} already exists for user {init_request.user_id}",
            )

        # Get agent class and manager
        agent_class_to_use: type[AgentInterface] = request.app.state.agent_class
        agent_manager: AgentManager = request.app.state.agent_manager

        # Create temporary agent instance to get agent identity
        temp_agent = agent_class_to_use()
        agent_identity = StateManager.create_agent_identity(temp_agent)

        logger.info(
            f"Capturing agent identity for session {session_id}: {agent_identity.agent_id} ({agent_identity.agent_type})"
        )

        # Process the configuration - apply templating to system prompt if data is provided
        processed_configuration = init_request.configuration.copy()

        # If data is provided but no system_prompt in config, use agent's default prompt
        if init_request.data and "system_prompt" not in processed_configuration:
            if hasattr(temp_agent, "get_agent_prompt"):
                try:
                    agent_default_prompt = temp_agent.get_agent_prompt()
                    if agent_default_prompt:
                        processed_configuration["system_prompt"] = agent_default_prompt
                        logger.info(
                            f"Using agent's default prompt for templating (session {session_id})"
                        )
                except Exception as e:
                    logger.warning(f"Could not get agent's default prompt: {e}")

        if init_request.data and "system_prompt" in processed_configuration:
            original_prompt = processed_configuration["system_prompt"]
            templated_prompt = _template_system_prompt(original_prompt, init_request.data)
            processed_configuration["system_prompt"] = templated_prompt

            logger.info(f"Applied templating to system prompt for session {session_id}")
            logger.debug(f"Original prompt: {original_prompt}")
            logger.debug(f"Templated prompt: {templated_prompt}")
            logger.debug(f"Template data: {init_request.data}")

        # Create SessionData object with agent identity and configuration
        session_data = SessionData(
            session_id=session_id,
            user_id=init_request.user_id,
            agent_instance_config={},  # DEPRECATED - kept for backward compatibility
            correlation_id=init_request.correlation_id,
            session_configuration=processed_configuration,  # Store processed configuration
            # Agent identity fields
            agent_id=agent_identity.agent_id,
            agent_type=agent_identity.agent_type,
            metadata={
                "data": init_request.data,
                "status": "active",
                "original_configuration": init_request.configuration,  # Store original for reference
                "agent_identity": agent_identity.to_dict(),  # Store complete agent identity
            },
            # New fields for ES config tracking
            config_reference=None,  # Will be populated by AgentManager when ES config is used
            session_overrides=processed_configuration,  # Session-specific overrides
        )

        # Save session to storage
        success = await session_storage.save_session(init_request.user_id, session_id, session_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize session")

        logger.info(
            f"Successfully initialized session {session_id} for user {init_request.user_id} with agent {agent_identity.agent_id}"
        )

        # Get welcome message from agent and save as first assistant message
        welcome_message = None
        try:
            welcome_message = await temp_agent.get_welcome_message()
            if welcome_message:
                # Parse special blocks (optionsblock, formDefinition, etc.) from welcome message
                from ..core.agent_interface import TextOutputPart
                from ..utils.special_blocks import parse_special_blocks_from_text

                cleaned_text, special_parts = parse_special_blocks_from_text(welcome_message)

                # Build parts array: text_output first (if any), then special parts
                parts_dicts = None
                all_parts = []

                # Add text content as text_output part so frontend renders it
                if cleaned_text and cleaned_text.strip():
                    text_part = TextOutputPart(text=cleaned_text)
                    all_parts.append(text_part)

                # Add special parts (options_block, form_definition, etc.)
                if special_parts:
                    all_parts.extend(special_parts)

                if all_parts:
                    parts_dicts = [part.model_dump() for part in all_parts]

                # Save welcome message as first assistant message in the session
                welcome_msg_data = MessageData(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=init_request.user_id,
                    interaction_id=str(uuid.uuid4()),
                    sequence_number=1,
                    message_type="agent_response",
                    role="assistant",
                    text_content=cleaned_text,
                    parts=parts_dicts,
                    response_text_main=cleaned_text,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    is_welcome_message=True,
                )
                await session_storage.add_message(welcome_msg_data)
                logger.info(f"Added welcome message to session {session_id}")
        except Exception as e:
            logger.error(f"Could not get/save welcome message: {e}")

        return SessionInitResponse(
            user_id=init_request.user_id,
            correlation_id=init_request.correlation_id,
            session_id=session_id,
            data=init_request.data,
            configuration=processed_configuration,  # Return the templated configuration
            # Agent identity fields
            agent_id=agent_identity.agent_id,
            agent_type=agent_identity.agent_type,
            welcome_message=welcome_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize session: {e}")


@app.post("/end")
async def end_session_endpoint(
    request: SessionEndRequest,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Ends a session by updating its status in SessionStorage.
    """
    global session_storage
    session_id = request.session_id

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Load the session for the specified user
        session_data = await session_storage.load_session(user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Update session status to closed
        if session_data.metadata is None:
            session_data.metadata = {}
        session_data.metadata["status"] = "closed"
        session_data.metadata["closed_at"] = datetime.now(timezone.utc).isoformat()

        await session_storage.save_session(user_id, session_id, session_data)

        logger.info(f"Session {session_id} has been closed for user {user_id}")
        return {
            "message": f"Session {session_id} has been successfully closed",
            "session_id": session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end session: {e}")


@app.post("/feedback/message")
async def submit_message_feedback_endpoint(
    request: MessageFeedbackRequest,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Submit feedback for a specific message. Stores feedback in session metadata.
    Includes validation for session status, message existence, and duplicate feedback handling.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Find the session that contains this message
        session_data = await session_storage.load_session(user_id, request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")

        # Check if session is closed (prevent editing)
        if session_data.metadata and session_data.metadata.get("status") == "closed":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit feedback for closed session {request.session_id}",
            )

        # Validate that the message exists in this session
        # Note: The GUI sends interaction_id as message_id, so we need to search by interaction_id
        message_history = await session_storage.get_conversation_history(request.session_id)
        message_exists = any(msg.interaction_id == request.message_id for msg in message_history)
        if not message_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Message with interaction ID {request.message_id} not found in session {request.session_id}",
            )

        # Initialize feedback structure if needed
        if session_data.metadata is None:
            session_data.metadata = {}
        if "feedback" not in session_data.metadata:
            session_data.metadata["feedback"] = {}
        if "messages" not in session_data.metadata["feedback"]:
            session_data.metadata["feedback"]["messages"] = {}

        # Check for existing feedback (for duplicate prevention)
        existing_feedback = session_data.metadata["feedback"]["messages"].get(request.message_id)
        feedback_changed = existing_feedback != request.feedback

        # Store/update feedback
        session_data.metadata["feedback"]["messages"][request.message_id] = request.feedback
        feedback_timestamp = datetime.now(timezone.utc).isoformat()
        session_data.metadata["feedback"]["messages"][
            f"{request.message_id}_timestamp"
        ] = feedback_timestamp

        # Save updated session data
        await session_storage.save_session(user_id, request.session_id, session_data)

        # Create MessageInsight for the feedback and store in insights index
        insight = MessageInsight(
            insight_id=str(uuid.uuid4()),
            message_id=request.message_id,
            session_id=request.session_id,
            user_id=user_id,
            insight_type="message_feedback",
            insight_data={
                "feedback": request.feedback,
                "timestamp": feedback_timestamp,
                "previous_feedback": existing_feedback,
                "feedback_changed": feedback_changed,
            },
            agent_id=session_data.agent_id,
            created_at=feedback_timestamp,
            created_by="user",
        )

        # Store insight in dedicated insights index
        insight_stored = await session_storage.add_insight(insight)
        if not insight_stored:
            logger.warning(
                f"Failed to store message feedback insight for message {request.message_id}"
            )

        # Create response message
        if existing_feedback is None:
            status_message = (
                f"Feedback '{request.feedback}' recorded for message {request.message_id}"
            )
            logger.info(
                f"New feedback '{request.feedback}' submitted for message {request.message_id} in session {request.session_id}"
            )
        elif feedback_changed:
            status_message = f"Feedback updated from '{existing_feedback}' to '{request.feedback}' for message {request.message_id}"
            logger.info(
                f"Feedback changed from '{existing_feedback}' to '{request.feedback}' for message {request.message_id} in session {request.session_id}"
            )
        else:
            status_message = f"Feedback '{request.feedback}' confirmed for message {request.message_id} (no change)"
            logger.info(
                f"Duplicate feedback '{request.feedback}' submitted for message {request.message_id} in session {request.session_id}"
            )

        return {
            "status": "success",
            "message": status_message,
            "session_id": request.session_id,
            "message_id": request.message_id,
            "feedback": request.feedback,
            "previous_feedback": existing_feedback,
            "feedback_changed": feedback_changed,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting message feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e}")


@app.post("/feedback/session")
async def submit_session_feedback_endpoint(
    request: SessionFeedbackRequest,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Submit feedback for a session (rating and optional comment).
    Creates a SessionInsight with insight_type="session_feedback".
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Find the session
        session_data = await session_storage.load_session(user_id, request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")

        # Initialize feedback structure if needed
        if session_data.metadata is None:
            session_data.metadata = {}
        if "feedback" not in session_data.metadata:
            session_data.metadata["feedback"] = {}

        # Check for existing session feedback
        existing_rating = session_data.metadata["feedback"].get("session_rating")
        existing_comment = session_data.metadata["feedback"].get("session_comment")

        # Store session feedback in metadata
        feedback_timestamp = datetime.now(timezone.utc).isoformat()
        session_data.metadata["feedback"]["session_rating"] = request.rating
        session_data.metadata["feedback"]["session_comment"] = request.comment
        session_data.metadata["feedback"]["session_feedback_timestamp"] = feedback_timestamp

        # Save updated session data
        await session_storage.save_session(user_id, request.session_id, session_data)

        # Create SessionInsight for the feedback and store in insights index
        insight = MessageInsight(
            insight_id=str(uuid.uuid4()),
            message_id="",  # No specific message for session feedback
            session_id=request.session_id,
            user_id=user_id,
            insight_type="session_feedback",
            insight_data={
                "rating": request.rating,
                "comment": request.comment,
                "timestamp": feedback_timestamp,
                "previous_rating": existing_rating,
                "previous_comment": existing_comment,
            },
            agent_id=session_data.agent_id,
            created_at=feedback_timestamp,
            created_by="user",
        )

        # Store insight in dedicated insights index
        insight_stored = await session_storage.add_insight(insight)
        if not insight_stored:
            logger.warning(
                f"Failed to store session feedback insight for session {request.session_id}"
            )

        # Create response message
        rating_changed = existing_rating != request.rating
        comment_changed = existing_comment != request.comment

        if existing_rating is None:
            status_message = f"Session feedback recorded: rating {request.rating}/5"
        elif rating_changed or comment_changed:
            status_message = f"Session feedback updated: rating {request.rating}/5"
        else:
            status_message = f"Session feedback confirmed: rating {request.rating}/5 (no change)"

        logger.info(
            f"Session feedback submitted for session {request.session_id}: rating={request.rating}"
        )

        return {
            "status": "success",
            "message": status_message,
            "session_id": request.session_id,
            "rating": request.rating,
            "comment": request.comment,
            "previous_rating": existing_rating,
            "previous_comment": existing_comment,
            "feedback_changed": rating_changed or comment_changed,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting session feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit session feedback: {e}")


@app.post("/feedback/flag")
@app.put("/feedback/flag")
async def submit_session_flag_endpoint(
    request: SessionFlagRequest,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Submit or update session-level flag. Editable while session is open.
    """
    global session_storage
    session_id = request.session_id
    flag_message = request.flag_message

    # Check if session exists
    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Find the session
        session_data = await session_storage.load_session(user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Check if session is closed (prevent editing)
        if session_data.metadata and session_data.metadata.get("status") == "closed":
            raise HTTPException(
                status_code=400, detail=f"Cannot edit flag for closed session {session_id}"
            )

        # Store previous flag for comparison
        if session_data.metadata is None:
            session_data.metadata = {}
        previous_flag = session_data.metadata.get("flag_message")

        # Store/update session flag
        flag_timestamp = datetime.now(timezone.utc).isoformat()
        session_data.metadata["flag_message"] = flag_message
        session_data.metadata["flag_timestamp"] = flag_timestamp

        await session_storage.save_session(user_id, session_id, session_data)

        # Create insight for the session flag
        insight = MessageInsight(
            insight_id=str(uuid.uuid4()),
            message_id="",
            session_id=session_id,
            user_id=user_id,
            insight_type="session_flag",
            insight_data={
                "flag_message": flag_message,
                "timestamp": flag_timestamp,
                "previous_flag": previous_flag,
                "flag_changed": previous_flag != flag_message,
            },
            agent_id=session_data.agent_id,
            created_at=flag_timestamp,
            created_by="user",
        )

        insight_stored = await session_storage.add_insight(insight)
        if not insight_stored:
            logger.warning(f"Failed to store session flag insight for session {session_id}")

        # Create response message
        if previous_flag is None:
            status_message = "Session flag created"
            logger.info(f"New session flag created for {session_id}")
        elif previous_flag != flag_message:
            status_message = "Session flag updated"
            logger.info(f"Session flag updated for {session_id}")
        else:
            status_message = "Session flag confirmed (no change)"
            logger.info(f"Duplicate session flag submitted for {session_id}")

        return {
            "status": "success",
            "message": status_message,
            "session_id": session_id,
            "flag_message": flag_message,
            "previous_flag": previous_flag,
            "flag_changed": previous_flag != flag_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session flag: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update session flag: {e}")


@app.put("/session/{session_id}/label", response_model=SessionInfo)
async def update_session_label_endpoint(
    session_id: str,
    label_request: SessionLabelUpdateRequest,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Update the label of a specific session.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Load the session for the specified user to check if it exists
        session_data = await session_storage.load_session(user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Check if session is closed (prevent editing)
        if session_data.metadata and session_data.metadata.get("status") == "closed":
            raise HTTPException(
                status_code=400, detail=f"Cannot update label for closed session {session_id}"
            )

        # Use the dedicated update_session_label method
        success = await session_storage.update_session_label(
            user_id, session_id, label_request.label
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session label in storage")

        # Load the updated session data to return
        updated_session_data = await session_storage.load_session(user_id, session_id)
        if not updated_session_data:
            raise HTTPException(status_code=500, detail="Failed to load updated session data")

        logger.info(f"Session label updated for {session_id}")
        return updated_session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session label: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update session label: {e}")


# < --- Feedback Retrieval Endpoints --- >


@app.get("/feedback/session/{session_id}")
async def get_session_feedback_endpoint(
    session_id: str,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve all feedback data for a session (flag message and message feedback).
    """
    global session_storage
    # Check if session exists
    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Load session data
        session_data = await session_storage.load_session(user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Extract feedback data from SessionData object
        metadata = session_data.metadata or {}
        feedback_data = {
            "session_id": session_id,
            "user_id": user_id,
            "session_status": metadata.get("status", "active"),
            "flag_message": metadata.get("flag_message"),
            "flag_timestamp": metadata.get("flag_timestamp"),
            "message_feedback": metadata.get("feedback", {}).get("messages", {}),
        }

        return feedback_data

    except Exception as e:
        logger.error(f"Error retrieving session feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session feedback: {e}")


@app.get("/feedback/message/{message_id}")
async def get_message_feedback_endpoint(
    message_id: str,
    session_id: str = Query(..., description="Session ID required to locate message feedback"),
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve feedback for a specific message within a session.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Load session data to find the message feedback
        session_data = await session_storage.load_session(user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Extract message feedback from SessionData object
        metadata = session_data.metadata or {}
        message_feedback_data = metadata.get("feedback", {}).get("messages", {}).get(message_id)
        feedback_timestamp = (
            metadata.get("feedback", {}).get("messages", {}).get(f"{message_id}_timestamp")
        )

        return {
            "message_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "feedback": message_feedback_data,
            "feedback_timestamp": feedback_timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve message feedback: {e}")


# < --- Session Status Endpoints --- >


@app.get("/session/{session_id}/status")
async def get_session_status_endpoint(
    session_id: str,
    user_id: str = Query(
        DEFAULT_USER_ID, description="Identifier for the user who owns the session"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    Get the status of a specific session (active, closed, or not found).
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        # Check for session existence and get its status
        session_data = await session_storage.load_session(user_id, session_id)

        if session_data:
            # Session exists, check its actual status from metadata
            status = "active"  # Default status for sessions without explicit status
            if session_data.metadata:
                status = session_data.metadata.get("status", "active")

            return {
                "session_id": session_id,
                "user_id": user_id,
                "status": status,
                "created_at": session_data.created_at,
                "updated_at": session_data.updated_at,
                "closed_at": (
                    session_data.metadata.get("closed_at") if session_data.metadata else None
                ),
            }
        else:
            return {"session_id": session_id, "user_id": user_id, "status": "not_found"}

    except Exception as e:
        logger.error(f"Error checking session status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check session status: {e}")


# < --- Session Workflow Endpoints --- >

# --- Documentation Endpoint --- >
from .documentation_generator import DocumentationGenerator


@app.get("/documentation")
async def documentation_endpoint(current_user: str = Depends(get_current_user)):
    """
    Serve comprehensive documentation page with all guides.

    Returns:
        HTMLResponse: Complete documentation page with navigation
    """
    try:
        # Instantiate DocumentationGenerator
        generator = DocumentationGenerator()

        # Generate HTML documentation
        html = generator.generate_documentation_html()

        # Return HTML response with Content-Security-Policy headers
        return HTMLResponse(
            content=html,
            headers={
                "Content-Security-Policy": "default-src 'self' https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;"
            },
        )
    except FileNotFoundError as e:
        logger.error(f"Documentation directory not found: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation not available: {str(e)}")
    except ValueError as e:
        logger.error(f"Markdown conversion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate documentation: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error generating documentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# < --- Documentation Endpoint --- >


@app.get("/sessions/{session_id}/response-times")
async def get_session_response_times_endpoint(
    session_id: str,
    user_id: str = Query(DEFAULT_USER_ID, description="Identifier for the user owning the session"),
    current_user: str = Depends(get_current_user),
):
    """
    Get response times for all agent responses in a session.
    Calculates the time delta between user input and agent response messages.
    """
    if session_storage is None:
        raise HTTPException(status_code=500, detail="Session storage not available")

    # Check if session exists and belongs to user
    session_data = await session_storage.get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_data.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    # Get response times (only works with MongoDB storage)
    if hasattr(session_storage, "get_response_times_for_session"):
        response_times = await session_storage.get_response_times_for_session(session_id)
        return {
            "session_id": session_id,
            "user_id": user_id,
            "response_times": response_times,
            "total_responses": len(response_times),
            "average_response_time_ms": (
                sum(rt.get("response_time_ms", 0) for rt in response_times) / len(response_times)
                if response_times
                else 0
            ),
        }
    else:
        raise HTTPException(
            status_code=501, detail="Response time calculation only available with MongoDB storage"
        )


@app.get("/interactions/{interaction_id}/response-time")
async def get_interaction_response_time_endpoint(
    interaction_id: str, current_user: str = Depends(get_current_user)
):
    """
    Get response time for a specific interaction (user input + agent response pair).
    """
    if session_storage is None:
        raise HTTPException(status_code=500, detail="Session storage not available")

    # Get response time (only works with MongoDB storage)
    if hasattr(session_storage, "get_response_times_for_interaction"):
        response_time_data = await session_storage.get_response_times_for_interaction(
            interaction_id
        )
        if not response_time_data:
            raise HTTPException(status_code=404, detail="Interaction not found")

        return response_time_data
    else:
        raise HTTPException(
            status_code=501, detail="Response time calculation only available with MongoDB storage"
        )


# --- Framework Helper Agent Endpoints --- >
from .helper_agent import FrameworkHelperAgent


# Global lazy-loaded helper agent instances (per user)
_helper_agents: dict[str, FrameworkHelperAgent] = {}
_helper_knowledge_indexed: bool = False

# Helper agent ID constant for V2
HELPER_AGENT_ID = "framework_helper_v2"


def resolve_helper_user_id(authenticated_user: str) -> str:
    """
    Resolve the user_id for helper agent operations.

    Checks the HELPER_AGENT_USER_ID environment variable first.
    If set, uses that value for all requests (shared sessions mode).
    Otherwise, falls back to the authenticated user ID (per-user isolation mode).

    Args:
        authenticated_user: The authenticated user's ID from the request

    Returns:
        The effective user_id to use for helper agent operations
    """
    fixed_user_id = os.getenv("HELPER_AGENT_USER_ID")
    if fixed_user_id:
        logger.debug(f"[HELPER] Using fixed user_id from env: {fixed_user_id}")
        return fixed_user_id
    return authenticated_user


async def _create_graphiti_client_for_indexing() -> Any:
    """Create a Graphiti client for framework knowledge indexing."""
    try:
        from graphiti_core import Graphiti
        from graphiti_core.driver.falkordb_driver import FalkorDriver

        falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
        falkordb_port = int(os.getenv("FALKORDB_PORT", "6379"))
        falkordb_password = os.getenv("FALKORDB_PASSWORD", None)

        driver = FalkorDriver(
            host=falkordb_host,
            port=falkordb_port,
            password=falkordb_password,
            database="framework_knowledge",
        )

        graphiti_client = Graphiti(graph_driver=driver)
        await graphiti_client.build_indices_and_constraints()

        logger.info(
            f"[HELPER] Graphiti client created for framework_knowledge "
            f"({falkordb_host}:{falkordb_port})"
        )
        return graphiti_client

    except ImportError as e:
        logger.warning(f"[HELPER] Graphiti not available, using fallback indexing: {e}")
        return None
    except Exception as e:
        logger.warning(f"[HELPER] Failed to create Graphiti client: {e}")
        return None


async def _check_graphiti_knowledge_exists() -> bool:
    """Check if framework_knowledge graph already has data in FalkorDB."""
    try:
        from graphiti_core.driver.falkordb_driver import FalkorDriver

        falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
        falkordb_port = int(os.getenv("FALKORDB_PORT", "6379"))
        falkordb_password = os.getenv("FALKORDB_PASSWORD", None)

        driver = FalkorDriver(
            host=falkordb_host,
            port=falkordb_port,
            password=falkordb_password,
            database="framework_knowledge",
        )

        result = driver.execute_query("MATCH (n) RETURN count(n) as cnt")
        if result and len(result) > 0:
            count = result[0].get("cnt", 0)
            if count > 0:
                logger.info(f"[HELPER] Found existing framework_knowledge graph with {count} nodes")
                return True

        return False

    except Exception as e:
        logger.debug(f"[HELPER] Could not check existing graph: {e}")
        return False


async def _ensure_helper_knowledge_indexed() -> None:
    """Ensure shared knowledge is indexed (called once at first helper access)."""
    global _helper_knowledge_indexed
    if not _helper_knowledge_indexed:
        # Check if graph already exists in FalkorDB
        exists, episode_count = await asyncio.to_thread(_check_graphiti_knowledge_exists_sync)
        if exists:
            logger.info(
                f"[HELPER] Using existing framework_knowledge graph from FalkorDB "
                f"({episode_count} indexed files)"
            )
            graphiti_client = await _create_graphiti_client_for_indexing()
            FrameworkHelperAgent._shared_graphiti_client = graphiti_client
            FrameworkHelperAgent._graphiti_episode_count = episode_count
            FrameworkHelperAgent._shared_knowledge_indexed = True
            _helper_knowledge_indexed = True
            return

        logger.info("[HELPER] Indexing shared framework knowledge...")

        graphiti_client = await _create_graphiti_client_for_indexing()
        await FrameworkHelperAgent.index_shared_knowledge(graphiti_client=graphiti_client)

        _helper_knowledge_indexed = True
        logger.info("[HELPER] Knowledge indexing complete")


def _check_graphiti_knowledge_exists_sync() -> tuple[bool, int]:
    """Synchronous check if framework_knowledge graph already has data.

    Returns:
        Tuple of (exists: bool, episode_count: int)
    """
    try:
        from falkordb import FalkorDB

        falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
        falkordb_port = int(os.getenv("FALKORDB_PORT", "6379"))

        db = FalkorDB(host=falkordb_host, port=falkordb_port)
        graph = db.select_graph("framework_knowledge")

        # Count total nodes
        result = graph.query("MATCH (n) RETURN count(n) as cnt")
        total_nodes = 0
        if result.result_set and len(result.result_set) > 0:
            total_nodes = result.result_set[0][0]

        # Count episodic nodes (indexed files)
        episode_result = graph.query("MATCH (e:Episodic) RETURN count(e) as cnt")
        episode_count = 0
        if episode_result.result_set and len(episode_result.result_set) > 0:
            episode_count = episode_result.result_set[0][0]

        if total_nodes > 0:
            logger.info(
                f"[HELPER] Found existing framework_knowledge graph: "
                f"{total_nodes} nodes, {episode_count} indexed files"
            )
            return True, episode_count

        return False, 0

    except Exception as e:
        logger.debug(f"[HELPER] Could not check existing graph: {e}")
        return False, 0


async def _get_or_create_helper_agent(user_id: str) -> FrameworkHelperAgent:
    """Get or create a helper agent instance for a user."""
    global _helper_agents

    await _ensure_helper_knowledge_indexed()

    if user_id not in _helper_agents:
        logger.info(f"[HELPER] Creating helper agent for user: {user_id}")
        agent = FrameworkHelperAgent()
        _helper_agents[user_id] = agent

    return _helper_agents[user_id]


@app.get("/helper", response_class=FileResponse, summary="Serve the Framework Helper UI")
async def get_helper_ui(current_user: str = Depends(get_current_user)):
    """
    Serves the Framework Helper Agent UI.

    The helper agent provides expert assistance for creating agents
    using the Agent Framework library.
    """
    file_path = os.path.join(os.path.dirname(__file__), "helper_ui.html")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="helper_ui.html not found")
    return FileResponse(file_path)


@app.get("/helper/status")
async def get_helper_status(current_user: str = Depends(get_current_user)):
    """
    Get the status of the Framework Helper Agent.

    Returns comprehensive information about:
    - Whether the agent is loaded and ready
    - Graphiti knowledge graph connection status
    - Storage backend type (elasticsearch, mongodb, memory)
    - Number of indexed documentation files
    - Any warnings about degraded functionality
    """
    global _helper_knowledge_indexed, session_storage

    # Determine storage backend type from session_storage class
    storage_backend = "unknown"
    if session_storage is not None:
        class_name = session_storage.__class__.__name__
        if "Elasticsearch" in class_name:
            storage_backend = "elasticsearch"
        elif "MongoDB" in class_name or "Mongo" in class_name:
            storage_backend = "mongodb"
        elif "Memory" in class_name:
            storage_backend = "memory"
        else:
            storage_backend = class_name.lower().replace("sessionstorage", "")
    else:
        storage_backend = "not_initialized"

    # Check Graphiti connection status
    graphiti_connected = FrameworkHelperAgent._shared_graphiti_client is not None

    if not _helper_knowledge_indexed:
        return {
            "loaded": False,
            "agent_ready": False,
            "agent_id": FrameworkHelperAgent.AGENT_ID,
            "indexed_files": 0,
            "graphiti_connected": graphiti_connected,
            "storage_backend": storage_backend,
            "warnings": ["⚠️ Helper agent not yet initialized. Send a message to start using it."],
        }

    indexed_count = FrameworkHelperAgent.get_indexed_files_count()

    temp_agent = FrameworkHelperAgent()
    warnings = temp_agent.get_memory_status_warnings()

    return {
        "loaded": True,
        "agent_ready": True,
        "agent_id": FrameworkHelperAgent.AGENT_ID,
        "indexed_files": indexed_count,
        "knowledge_indexed": FrameworkHelperAgent.is_knowledge_indexed(),
        "graphiti_connected": graphiti_connected,
        "storage_backend": storage_backend,
        "warnings": warnings,
    }


class HelperChatRequest(BaseModel):
    """Request model for helper agent chat."""

    message: str
    session_id: str | None = None


class HelperChatResponse(BaseModel):
    """Response model for helper agent chat."""

    response: str
    session_id: str
    warnings: list[str] = []


@app.post("/helper/chat", response_model=HelperChatResponse)
async def helper_chat_endpoint(
    request: HelperChatRequest,
    user_id: str = Query(DEFAULT_USER_ID, description="User identifier"),
    current_user: str = Depends(get_current_user),
):
    """
    Send a message to the Framework Helper Agent.

    The helper agent can:
    - Answer questions about the Agent Framework
    - Provide code examples for creating agents
    - Search documentation and examples
    - Explain framework architecture and patterns

    Persists messages to SessionStorage for conversation history.
    """
    global session_storage

    try:
        # Resolve effective user_id (supports HELPER_AGENT_USER_ID env var override)
        effective_user_id = resolve_helper_user_id(user_id)

        agent = await _get_or_create_helper_agent(effective_user_id)

        session_id = request.session_id or str(uuid.uuid4())
        interaction_id = str(uuid.uuid4())

        # Ensure session metadata exists in SessionStorage
        if session_storage:
            existing_session = await session_storage.load_session(effective_user_id, session_id)
            if not existing_session:
                # Create session metadata for new helper sessions
                new_session_data = SessionData(
                    session_id=session_id,
                    user_id=effective_user_id,
                    agent_instance_config={},  # DEPRECATED - kept for backward compatibility
                    agent_id=HELPER_AGENT_ID,
                    agent_type="FrameworkHelperAgent",
                    metadata={"status": "active"},
                    config_reference=None,  # Helper agent doesn't use ES config
                    session_overrides=None,
                )
                await session_storage.save_session(effective_user_id, session_id, new_session_data)
                logger.info(f"[HELPER] Created session metadata for {session_id}")

        agent_input = StructuredAgentInput(query=request.message, parts=[])

        # Persist user message to storage
        if session_storage:
            try:
                existing_messages = await session_storage.get_conversation_history(session_id)
                sequence_number = len(existing_messages) + 1

                user_msg_data = MessageData(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=effective_user_id,
                    interaction_id=interaction_id,
                    sequence_number=sequence_number,
                    message_type="user_input",
                    role="user",
                    text_content=request.message,
                    agent_id=HELPER_AGENT_ID,
                    agent_type="FrameworkHelperAgent",
                )
                await session_storage.add_message(user_msg_data)
                logger.debug(f"[HELPER] Persisted user message for interaction {interaction_id}")
            except Exception as e:
                logger.warning(f"[HELPER] Failed to persist user message: {e}")

        response = await agent.handle_message(session_id, agent_input)

        warnings = agent.get_memory_status_warnings()

        response_text = response.response_text or ""
        if not response_text and response.parts:
            for part in response.parts:
                if hasattr(part, "text"):
                    response_text = part.text
                    break

        # Persist agent response to storage
        if session_storage and response_text:
            try:
                existing_messages = await session_storage.get_conversation_history(session_id)
                sequence_number = len(existing_messages) + 1

                agent_msg_data = MessageData(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=effective_user_id,
                    interaction_id=interaction_id,
                    sequence_number=sequence_number,
                    message_type="agent_response",
                    role="assistant",
                    text_content=response_text,
                    response_text_main=response_text,
                    agent_id=HELPER_AGENT_ID,
                    agent_type="FrameworkHelperAgent",
                )
                await session_storage.add_message(agent_msg_data)
                logger.debug(f"[HELPER] Persisted agent response for interaction {interaction_id}")
            except Exception as e:
                logger.warning(f"[HELPER] Failed to persist agent response: {e}")

        return HelperChatResponse(response=response_text, session_id=session_id, warnings=warnings)

    except ImportError as e:
        logger.error(f"[HELPER] Missing dependency: {e}")
        error_msg = str(e)
        return HelperChatResponse(
            response=f"❌ **Missing Dependencies**\n\n{error_msg}\n\n"
            "Run one of these commands to install:\n"
            "```bash\nuv sync --all-extras\n```\nor\n"
            "```bash\nuv add llama-index llama-index-llms-openai llama-index-llms-anthropic\n```",
            session_id=request.session_id or str(uuid.uuid4()),
            warnings=[error_msg],
        )

    except Exception as e:
        logger.error(f"[HELPER] Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Helper agent error: {str(e)}")


@app.post("/helper/stream")
async def helper_stream_endpoint(
    request: HelperChatRequest,
    user_id: str = Query(DEFAULT_USER_ID, description="User identifier"),
    current_user: str = Depends(get_current_user),
):
    """
    Stream a response from the Framework Helper Agent.

    Uses the SAME format as /stream endpoint for compatibility with modern_ui.
    Sends SessionMessageResponse chunks with parts containing stream markers.
    """
    global session_storage

    try:
        # Resolve effective user_id (supports HELPER_AGENT_USER_ID env var override)
        effective_user_id = resolve_helper_user_id(user_id)

        agent = await _get_or_create_helper_agent(effective_user_id)

        session_id = request.session_id or str(uuid.uuid4())
        interaction_id = str(uuid.uuid4())

        # Ensure session metadata exists in SessionStorage
        if session_storage:
            existing_session = await session_storage.load_session(effective_user_id, session_id)
            if not existing_session:
                # Create session metadata for new helper sessions
                new_session_data = SessionData(
                    session_id=session_id,
                    user_id=effective_user_id,
                    agent_instance_config={},  # DEPRECATED - kept for backward compatibility
                    agent_id=HELPER_AGENT_ID,
                    agent_type="FrameworkHelperAgent",
                    metadata={"status": "active"},
                    config_reference=None,  # Helper agent doesn't use ES config
                    session_overrides=None,
                )
                await session_storage.save_session(effective_user_id, session_id, new_session_data)
                logger.info(f"[HELPER] Created session metadata for {session_id}")

        agent_input = StructuredAgentInput(query=request.message, parts=[])

        # Persist user message to storage
        if session_storage:
            try:
                existing_messages = await session_storage.get_conversation_history(session_id)
                sequence_number = len(existing_messages) + 1

                user_msg_data = MessageData(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=effective_user_id,
                    interaction_id=interaction_id,
                    sequence_number=sequence_number,
                    message_type="user_input",
                    role="user",
                    text_content=request.message,
                    agent_id=HELPER_AGENT_ID,
                    agent_type="FrameworkHelperAgent",
                )
                await session_storage.add_message(user_msg_data)
                logger.debug(f"[HELPER] Persisted user message for interaction {interaction_id}")
            except Exception as e:
                logger.warning(f"[HELPER] Failed to persist user message: {e}")

        async def generate_stream() -> AsyncGenerator[str, None]:
            final_agent_response = None
            try:
                start_time = datetime.now(timezone.utc)
                response_stream = agent.handle_message_stream(session_id, agent_input)

                async for output_chunk in response_stream:
                    # Keep track of the latest response for persistence
                    final_agent_response = output_chunk

                    # Send chunk in SAME format as /stream endpoint (SessionMessageResponse)
                    chunk_response = SessionMessageResponse(
                        response_text=output_chunk.response_text or "",
                        parts=output_chunk.parts,
                        session_id=session_id,
                        user_id=effective_user_id,
                        interaction_id=interaction_id,
                        agent_id=HELPER_AGENT_ID,
                        agent_type="FrameworkHelperAgent",
                    )
                    json_data = json.dumps(
                        chunk_response.model_dump(), ensure_ascii=False, separators=(",", ":")
                    )
                    yield f"data: {json_data}\n\n"

                # Persist agent response after streaming completes
                end_time = datetime.now(timezone.utc)
                processing_time_ms = (end_time - start_time).total_seconds() * 1000

                if session_storage and final_agent_response:
                    try:
                        final_text = final_agent_response.response_text or ""
                        existing_messages = await session_storage.get_conversation_history(
                            session_id
                        )
                        sequence_number = len(existing_messages) + 1

                        agent_msg_data = MessageData(
                            message_id=str(uuid.uuid4()),
                            session_id=session_id,
                            user_id=effective_user_id,
                            interaction_id=interaction_id,
                            sequence_number=sequence_number,
                            message_type="agent_response",
                            role="assistant",
                            text_content=final_text,
                            response_text_main=final_text,
                            agent_id=HELPER_AGENT_ID,
                            agent_type="FrameworkHelperAgent",
                            processing_time_ms=processing_time_ms,
                        )
                        await session_storage.add_message(agent_msg_data)
                        logger.debug(
                            f"[HELPER] Persisted agent response for interaction {interaction_id}"
                        )

                        # Auto-generate session title after first exchange
                        asyncio.create_task(
                            _auto_generate_session_title_if_needed(
                                user_id=effective_user_id,
                                session_id=session_id,
                                user_message_text=request.message,
                                agent_response_text=final_text,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"[HELPER] Failed to persist agent response: {e}")

                # Send done message (same format as /stream)
                done_message = {
                    "status": "done",
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                }
                yield f"data: {json.dumps(done_message, ensure_ascii=False, separators=(',', ':'))}\n\n"

            except Exception as e:
                logger.error(f"[HELPER] Stream error: {e}", exc_info=True)
                error_payload = {"error": f"Stream error: {str(e)}"}
                yield f"data: {json.dumps(error_payload, ensure_ascii=False, separators=(',', ':'))}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

    except Exception as e:
        logger.error(f"[HELPER] Error starting stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Helper agent error: {str(e)}")


class HelperSessionInfo(BaseModel):
    """Session info model for helper agent sessions."""

    session_id: str
    session_label: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    agent_id: str | None = None
    agent_type: str | None = None
    metadata: dict[str, Any] | None = None


@app.get("/helper/sessions", response_model=list[HelperSessionInfo])
async def list_helper_sessions(
    user_id: str = Query(DEFAULT_USER_ID, description="User identifier"),
    current_user: str = Depends(get_current_user),
):
    """
    List all sessions for the Framework Helper Agent.

    Returns sessions filtered by user_id and agent_id="framework_helper_v2".
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        effective_user_id = resolve_helper_user_id(user_id)

        sessions_info = await session_storage.list_user_sessions_with_info(effective_user_id)

        helper_sessions = [
            HelperSessionInfo(
                session_id=session.get("session_id", ""),
                session_label=session.get("session_label"),
                created_at=session.get("created_at"),
                updated_at=session.get("updated_at"),
                agent_id=session.get("agent_id"),
                agent_type=session.get("agent_type"),
                metadata=session.get("metadata"),
            )
            for session in sessions_info
            if session.get("agent_id") == HELPER_AGENT_ID
        ]

        return helper_sessions

    except Exception as e:
        logger.error(f"[HELPER] Error listing sessions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve helper sessions")


@app.get("/helper/sessions/{session_id}/history", response_model=list[HistoryMessage])
async def get_helper_session_history(
    session_id: str,
    user_id: str = Query(DEFAULT_USER_ID, description="User identifier"),
    current_user: str = Depends(get_current_user),
):
    """
    Retrieve conversation history for a specific helper agent session.

    Returns the full message history for the given session_id.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        effective_user_id = resolve_helper_user_id(user_id)

        session_data = await session_storage.load_session(effective_user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_data.agent_id != HELPER_AGENT_ID:
            raise HTTPException(
                status_code=403, detail="Session does not belong to the helper agent"
            )

        message_data_list = await session_storage.get_conversation_history(session_id)

        history = []
        for msg_data in message_data_list:
            history_msg = message_data_to_history_message(msg_data, HistoryMessage)
            history.append(history_msg)

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[HELPER] Error getting history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve session history")


@app.delete("/helper/sessions/{session_id}")
async def delete_helper_session(
    session_id: str,
    user_id: str = Query(DEFAULT_USER_ID, description="User identifier"),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a helper agent session and all its messages.

    Returns success status.
    """
    global session_storage

    if not session_storage:
        raise HTTPException(status_code=500, detail="Session storage not available")

    try:
        effective_user_id = resolve_helper_user_id(user_id)

        session_data = await session_storage.load_session(effective_user_id, session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_data.agent_id != HELPER_AGENT_ID:
            raise HTTPException(
                status_code=403, detail="Session does not belong to the helper agent"
            )

        success = await session_storage.delete_session(effective_user_id, session_id)

        if success:
            logger.info(f"[HELPER] Deleted session {session_id} for user {effective_user_id}")
            return {"success": True, "message": f"Session {session_id} deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[HELPER] Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete session")


class ReindexResult(BaseModel):
    """Response model for reindex operation."""

    success: bool
    indexed_docs: int
    indexed_examples: int
    indexed_source: int
    total_indexed: int
    message: str


@app.post("/helper/reindex", response_model=ReindexResult)
async def reindex_helper_knowledge(
    current_user: str = Depends(get_current_user),
):
    """
    Re-index framework documentation into the knowledge base.

    This admin endpoint triggers a full re-indexing of:
    - Documentation files (docs/*.md)
    - Example agent files (examples/*.py)
    - Key source code files (agent_framework/**/*.py)

    The re-indexing clears existing indexed content and rebuilds the knowledge base.
    This is useful when documentation or examples have been updated.

    Returns:
        ReindexResult with counts of indexed files and status message.
    """
    global _helper_knowledge_indexed

    try:
        logger.info("[HELPER REINDEX] Starting knowledge re-indexing...")

        # Reset the indexed flag to force re-indexing
        _helper_knowledge_indexed = False

        # Clear existing indexed content lists
        FrameworkHelperAgent._shared_knowledge_indexed = False
        FrameworkHelperAgent._indexed_docs = []
        FrameworkHelperAgent._indexed_examples = []
        FrameworkHelperAgent._indexed_source = []

        # Perform the re-indexing with Graphiti client
        graphiti_client = await _create_graphiti_client_for_indexing()
        await FrameworkHelperAgent.index_shared_knowledge(graphiti_client=graphiti_client)

        # Update the global flag
        _helper_knowledge_indexed = True

        # Get counts
        docs_count = len(FrameworkHelperAgent._indexed_docs)
        examples_count = len(FrameworkHelperAgent._indexed_examples)
        source_count = len(FrameworkHelperAgent._indexed_source)
        total_count = docs_count + examples_count + source_count

        logger.info(
            f"[HELPER REINDEX] Complete - docs: {docs_count}, "
            f"examples: {examples_count}, source: {source_count}"
        )

        return ReindexResult(
            success=True,
            indexed_docs=docs_count,
            indexed_examples=examples_count,
            indexed_source=source_count,
            total_indexed=total_count,
            message=f"Successfully re-indexed {total_count} files",
        )

    except Exception as e:
        logger.error(f"[HELPER REINDEX] Error during re-indexing: {e}", exc_info=True)
        return ReindexResult(
            success=False,
            indexed_docs=0,
            indexed_examples=0,
            indexed_source=0,
            total_indexed=0,
            message=f"Re-indexing failed: {e!s}",
        )


# < --- Framework Helper Agent Endpoints ---
