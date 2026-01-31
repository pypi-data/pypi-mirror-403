"""
Multi-Provider Model Client Factory

Creates appropriate model clients (OpenAI, Anthropic, Gemini, etc.) based on model configuration.
This module is framework-agnostic and uses native client libraries.
"""

import json
import logging
import re
from typing import Any, Dict, Optional, Union, Type
from .model_config import ModelConfigManager, ModelProvider, model_config
from .agent_interface import AgentConfig

logger = logging.getLogger(__name__)


def _patch_openai_client_for_sanitization(llm: Any) -> None:
    """
    Patch the LlamaIndex OpenAI LLM to sanitize messages before API calls.
    
    This fixes cross-provider compatibility issues when switching from Claude/Gemini
    to OpenAI mid-session. The main issue is that Claude/Gemini store tool_calls
    arguments as Python dicts, but OpenAI API requires them as JSON strings.
    
    LlamaIndex's OpenAI LLM uses _get_aclient() to get/create the AsyncOpenAI client.
    We patch this method to wrap the returned client with message sanitization.
    
    Args:
        llm: The LlamaIndex OpenAI LLM instance to patch.
    """
    
    def _sanitize_openai_messages(messages: list) -> list:
        """
        Sanitize messages for OpenAI API compatibility.
        
        Converts tool_calls[].function.arguments from dicts to JSON strings.
        This is called at the AsyncOpenAI client level, so messages are already
        in OpenAI API format (dicts, not ChatMessage objects).
        """
        if not messages:
            return messages
        
        sanitized = []
        for msg in messages:
            if not isinstance(msg, dict):
                sanitized.append(msg)
                continue
            
            msg_copy = dict(msg)
            modified = False
            
            # Handle tool_calls - convert arguments to JSON strings
            if 'tool_calls' in msg_copy and msg_copy['tool_calls']:
                sanitized_tool_calls = []
                for tc in msg_copy['tool_calls']:
                    if not isinstance(tc, dict):
                        sanitized_tool_calls.append(tc)
                        continue
                    
                    tc_copy = dict(tc)
                    if 'function' in tc_copy and isinstance(tc_copy['function'], dict):
                        func = dict(tc_copy['function'])
                        args = func.get('arguments')
                        
                        # Convert dict/list arguments to JSON string
                        if args is not None and not isinstance(args, str):
                            try:
                                func['arguments'] = json.dumps(args)
                                tc_copy['function'] = func
                                modified = True
                                logger.info(
                                    f"[OpenAI Sanitizer] Converted tool_call arguments "
                                    f"from {type(args).__name__} to JSON string"
                                )
                            except (TypeError, ValueError) as e:
                                logger.warning(
                                    f"[OpenAI Sanitizer] Failed to convert "
                                    f"tool_call arguments to JSON: {e}"
                                )
                                func['arguments'] = str(args)
                                tc_copy['function'] = func
                                modified = True
                    
                    sanitized_tool_calls.append(tc_copy)
                
                msg_copy['tool_calls'] = sanitized_tool_calls
            
            # Remove empty tool_calls arrays (OpenAI rejects them)
            if 'tool_calls' in msg_copy and not msg_copy['tool_calls']:
                del msg_copy['tool_calls']
                modified = True
            
            if modified:
                logger.debug(f"[OpenAI Sanitizer] Sanitized {msg_copy.get('role', 'unknown')} message")
            
            sanitized.append(msg_copy)
        
        return sanitized
    
    def _patch_client(client: Any) -> Any:
        """Patch an AsyncOpenAI client's chat.completions.create method."""
        if getattr(client, '_sanitization_patched', False):
            return client
        
        chat_completions = getattr(client.chat, 'completions', None)
        if chat_completions is None:
            logger.warning("[OpenAI Sanitizer] Could not find chat.completions, skipping patch")
            return client
        
        original_create = chat_completions.create
        
        async def sanitizing_create(*args, **kwargs):
            """Wrapper that sanitizes messages before calling OpenAI API."""
            if 'messages' in kwargs:
                kwargs['messages'] = _sanitize_openai_messages(kwargs['messages'])
            return await original_create(*args, **kwargs)
        
        chat_completions.create = sanitizing_create
        client._sanitization_patched = True
        logger.debug("[OpenAI Sanitizer] Patched AsyncOpenAI client instance")
        return client
    
    # Check if already patched
    if getattr(llm, '_sanitization_patched', False):
        logger.debug("[OpenAI Sanitizer] LLM already patched, skipping")
        return
    
    # Store original _get_aclient method
    original_get_aclient = llm._get_aclient
    
    def patched_get_aclient():
        """Wrapper that patches the client returned by _get_aclient."""
        client = original_get_aclient()
        return _patch_client(client)
    
    # Replace _get_aclient method
    llm._get_aclient = patched_get_aclient
    
    # Also patch _get_client for sync calls (if it exists)
    if hasattr(llm, '_get_client'):
        original_get_client = llm._get_client
        
        def patched_get_client():
            """Wrapper that patches the sync client."""
            client = original_get_client()
            if getattr(client, '_sanitization_patched', False):
                return client
            
            chat_completions = getattr(client.chat, 'completions', None)
            if chat_completions is None:
                return client
            
            original_create = chat_completions.create
            
            def sanitizing_create_sync(*args, **kwargs):
                """Wrapper that sanitizes messages before calling OpenAI API."""
                if 'messages' in kwargs:
                    kwargs['messages'] = _sanitize_openai_messages(kwargs['messages'])
                return original_create(*args, **kwargs)
            
            chat_completions.create = sanitizing_create_sync
            client._sanitization_patched = True
            return client
        
        llm._get_client = patched_get_client
    
    # Mark LLM as patched
    llm._sanitization_patched = True
    
    logger.info("[OpenAI Sanitizer] Patched LlamaIndex OpenAI LLM for cross-provider compatibility")


def _patch_anthropic_client_for_sanitization(llm: Any) -> None:
    """
    Patch the LlamaIndex Anthropic LLM to sanitize messages before API calls.
    
    This fixes cross-provider compatibility issues when switching from OpenAI
    to Claude mid-session. The main issue is that OpenAI stores tool_calls in format:
    {"id": "...", "function": {"name": "...", "arguments": "JSON string"}}
    
    But Anthropic expects format:
    {"id": "...", "name": "...", "input": {dict}}
    
    Args:
        llm: The LlamaIndex Anthropic LLM instance to patch.
    """
    
    def _sanitize_anthropic_messages(messages: list) -> list:
        """
        Sanitize messages for Anthropic API compatibility.
        
        Converts OpenAI tool_calls format to Anthropic format.
        This is called at the AsyncAnthropic client level.
        """
        if not messages:
            return messages
        
        sanitized = []
        for msg in messages:
            if not isinstance(msg, dict):
                sanitized.append(msg)
                continue
            
            msg_copy = dict(msg)
            modified = False
            
            # Anthropic uses 'content' as a list of content blocks
            if 'content' in msg_copy and isinstance(msg_copy['content'], list):
                sanitized_content = []
                for block in msg_copy['content']:
                    if not isinstance(block, dict):
                        sanitized_content.append(block)
                        continue
                    
                    block_copy = dict(block)
                    
                    # Handle tool_use blocks - convert input from JSON string to dict
                    if block_copy.get('type') == 'tool_use':
                        tool_input = block_copy.get('input')
                        if isinstance(tool_input, str):
                            try:
                                block_copy['input'] = json.loads(tool_input)
                                modified = True
                                logger.info(
                                    f"[Anthropic Sanitizer] Converted tool_use input "
                                    f"from JSON string to dict"
                                )
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(
                                    f"[Anthropic Sanitizer] Failed to parse "
                                    f"tool_use input from JSON: {e}"
                                )
                    
                    sanitized_content.append(block_copy)
                
                msg_copy['content'] = sanitized_content
            
            if modified:
                logger.debug(f"[Anthropic Sanitizer] Sanitized {msg_copy.get('role', 'unknown')} message")
            
            sanitized.append(msg_copy)
        
        return sanitized
    
    def _patch_client(client: Any) -> Any:
        """Patch an AsyncAnthropic client's messages.create method."""
        if getattr(client, '_sanitization_patched', False):
            return client
        
        messages_api = getattr(client, 'messages', None)
        if messages_api is None:
            logger.warning("[Anthropic Sanitizer] Could not find messages API, skipping patch")
            return client
        
        original_create = messages_api.create
        
        async def sanitizing_create(*args, **kwargs):
            """Wrapper that sanitizes messages before calling Anthropic API."""
            if 'messages' in kwargs:
                kwargs['messages'] = _sanitize_anthropic_messages(kwargs['messages'])
            return await original_create(*args, **kwargs)
        
        messages_api.create = sanitizing_create
        client._sanitization_patched = True
        logger.debug("[Anthropic Sanitizer] Patched AsyncAnthropic client instance")
        return client
    
    # Check if already patched
    if getattr(llm, '_sanitization_patched', False):
        logger.debug("[Anthropic Sanitizer] LLM already patched, skipping")
        return
    
    # LlamaIndex Anthropic LLM uses _aclient directly
    # We need to patch it when it's accessed
    
    # Try to patch _aclient if it exists
    if hasattr(llm, '_aclient') and llm._aclient is not None:
        llm._aclient = _patch_client(llm._aclient)
        logger.debug("[Anthropic Sanitizer] Patched existing _aclient")
    
    # Mark LLM as patched
    llm._sanitization_patched = True
    
    logger.info("[Anthropic Sanitizer] Patched LlamaIndex Anthropic LLM for cross-provider compatibility")


def _patch_gemini_llm_for_sanitization(llm: Any) -> None:
    """
    Patch the LlamaIndex Gemini LLM to sanitize ChatMessages before conversion.
    
    This fixes cross-provider compatibility issues when switching from OpenAI
    to Gemini mid-session. The main issue is that OpenAI stores tool_calls with
    arguments as JSON strings, but Gemini's ToolCallBlock.tool_kwargs must be a dict.
    
    The Gemini LLM uses chat_message_to_gemini() which iterates over message.blocks
    and expects ToolCallBlock.tool_kwargs to be a dict for types.Part.from_function_call().
    
    We patch the _achat method to sanitize messages before they're converted.
    
    Args:
        llm: The LlamaIndex GoogleGenAI LLM instance to patch.
    """
    
    def _sanitize_chat_messages_for_gemini(messages: list) -> list:
        """
        Sanitize ChatMessage objects for Gemini compatibility.
        
        Converts:
        1. ToolCallBlock.tool_kwargs from JSON strings to dicts
        2. tool_calls in additional_kwargs from OpenAI format to Gemini format
        """
        if not messages:
            return messages
        
        try:
            from llama_index.core.base.llms.types import ChatMessage, ToolCallBlock
        except ImportError:
            logger.warning("[Gemini Sanitizer] Could not import ChatMessage/ToolCallBlock")
            return messages
        
        sanitized = []
        for msg in messages:
            if not isinstance(msg, ChatMessage):
                sanitized.append(msg)
                continue
            
            blocks_modified = False
            kwargs_modified = False
            new_blocks = None
            new_kwargs = None
            
            # 1. Sanitize blocks - convert ToolCallBlock.tool_kwargs from JSON string to dict
            if hasattr(msg, 'blocks') and msg.blocks:
                new_blocks = []
                for block in msg.blocks:
                    if isinstance(block, ToolCallBlock):
                        # Check if tool_kwargs is a JSON string
                        if isinstance(block.tool_kwargs, str):
                            try:
                                parsed_kwargs = json.loads(block.tool_kwargs)
                                new_block = ToolCallBlock(
                                    tool_call_id=block.tool_call_id,
                                    tool_name=block.tool_name,
                                    tool_kwargs=parsed_kwargs
                                )
                                new_blocks.append(new_block)
                                blocks_modified = True
                                logger.info(
                                    f"[Gemini Sanitizer] Converted ToolCallBlock.tool_kwargs "
                                    f"from JSON string to dict for tool '{block.tool_name}'"
                                )
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(
                                    f"[Gemini Sanitizer] Failed to parse tool_kwargs: {e}"
                                )
                                new_blocks.append(block)
                        else:
                            new_blocks.append(block)
                    else:
                        new_blocks.append(block)
            
            # 2. Sanitize additional_kwargs - convert OpenAI tool_calls format to Gemini format
            # OpenAI: {"id": "...", "function": {"name": "...", "arguments": "JSON string"}}
            # Gemini: {"name": "...", "args": {dict}}
            if msg.additional_kwargs and 'tool_calls' in msg.additional_kwargs:
                tool_calls = msg.additional_kwargs.get('tool_calls', [])
                if tool_calls:
                    new_tool_calls = []
                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            new_tool_calls.append(tc)
                            continue
                        
                        # Check if it's OpenAI format (has 'function' key)
                        if 'function' in tc:
                            func = tc.get('function', {})
                            if isinstance(func, dict):
                                name = func.get('name', '')
                                args = func.get('arguments', '{}')
                                
                                # Parse JSON string to dict
                                if isinstance(args, str):
                                    try:
                                        args = json.loads(args)
                                    except (json.JSONDecodeError, TypeError):
                                        logger.warning(
                                            f"[Gemini Sanitizer] Failed to parse tool_call arguments, using empty dict"
                                        )
                                        args = {}
                                
                                # Convert to Gemini format
                                gemini_tc = {
                                    'name': name,
                                    'args': args
                                }
                                new_tool_calls.append(gemini_tc)
                                kwargs_modified = True
                                logger.info(
                                    f"[Gemini Sanitizer] Converted tool_call from OpenAI format "
                                    f"to Gemini format for tool '{name}'"
                                )
                            else:
                                new_tool_calls.append(tc)
                        elif 'name' in tc:
                            # Already Gemini format, ensure args is a dict
                            args = tc.get('args', {})
                            if isinstance(args, str):
                                try:
                                    tc = dict(tc)
                                    tc['args'] = json.loads(args)
                                    kwargs_modified = True
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            new_tool_calls.append(tc)
                        else:
                            new_tool_calls.append(tc)
                    
                    if kwargs_modified:
                        new_kwargs = dict(msg.additional_kwargs)
                        new_kwargs['tool_calls'] = new_tool_calls
            
            # Create new message if anything was modified
            if blocks_modified or kwargs_modified:
                final_blocks = new_blocks if blocks_modified else (msg.blocks if hasattr(msg, 'blocks') else None)
                final_kwargs = new_kwargs if kwargs_modified else msg.additional_kwargs
                
                if final_blocks:
                    new_msg = ChatMessage(
                        role=msg.role,
                        blocks=final_blocks,
                        additional_kwargs=final_kwargs
                    )
                else:
                    new_msg = ChatMessage(
                        role=msg.role,
                        content=msg.content,
                        additional_kwargs=final_kwargs
                    )
                sanitized.append(new_msg)
            else:
                sanitized.append(msg)
        
        return sanitized
    
    # Check if already patched
    if getattr(llm, '_sanitization_patched', False):
        logger.debug("[Gemini Sanitizer] LLM already patched, skipping")
        return
    
    # Patch the _achat method which is called for async chat
    if hasattr(llm, '_achat'):
        original_achat = llm._achat
        
        async def sanitizing_achat(messages, **kwargs):
            """Wrapper that sanitizes messages before calling Gemini."""
            sanitized_messages = _sanitize_chat_messages_for_gemini(messages)
            return await original_achat(sanitized_messages, **kwargs)
        
        llm._achat = sanitizing_achat
        logger.debug("[Gemini Sanitizer] Patched _achat method")
    
    # Also patch _chat for sync calls
    if hasattr(llm, '_chat'):
        original_chat = llm._chat
        
        def sanitizing_chat(messages, **kwargs):
            """Wrapper that sanitizes messages before calling Gemini."""
            sanitized_messages = _sanitize_chat_messages_for_gemini(messages)
            return original_chat(sanitized_messages, **kwargs)
        
        llm._chat = sanitizing_chat
        logger.debug("[Gemini Sanitizer] Patched _chat method")
    
    # Patch _astream_chat for async streaming calls
    # Note: _astream_chat is an async function that RETURNS an async generator,
    # so we can patch it by wrapping and returning the generator from the original.
    if hasattr(llm, '_astream_chat'):
        original_astream_chat = llm._astream_chat
        
        async def sanitizing_astream_chat(messages, **kwargs):
            """Wrapper that sanitizes messages before calling Gemini streaming."""
            sanitized_messages = _sanitize_chat_messages_for_gemini(messages)
            return await original_astream_chat(sanitized_messages, **kwargs)
        
        llm._astream_chat = sanitizing_astream_chat
        logger.debug("[Gemini Sanitizer] Patched _astream_chat method")
    
    # Also patch _stream_chat for sync streaming calls
    if hasattr(llm, '_stream_chat'):
        original_stream_chat = llm._stream_chat
        
        def sanitizing_stream_chat(messages, **kwargs):
            """Wrapper that sanitizes messages before calling Gemini sync streaming."""
            sanitized_messages = _sanitize_chat_messages_for_gemini(messages)
            return original_stream_chat(sanitized_messages, **kwargs)
        
        llm._stream_chat = sanitizing_stream_chat
        logger.debug("[Gemini Sanitizer] Patched _stream_chat method")
    
    # Mark LLM as patched
    llm._sanitization_patched = True
    
    logger.info("[Gemini Sanitizer] Patched LlamaIndex Gemini LLM for cross-provider compatibility")

# Try importing OpenAI client
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("[ModelClientFactory] OpenAI client not available. Install with: uv add openai")
    OPENAI_AVAILABLE = False

# Try importing Anthropic client
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("[ModelClientFactory] Anthropic client not available. Install with: uv add anthropic")
    ANTHROPIC_AVAILABLE = False

# Try importing Google Gemini client
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("[ModelClientFactory] Google Gemini client not available. Install with: uv add google-generativeai")
    GEMINI_AVAILABLE = False

class ModelClientFactory:
    """
    Factory class for creating appropriate model clients based on model names.
    Framework-agnostic implementation using native client libraries.
    """
    
    def __init__(self, config_manager: ModelConfigManager = None):
        """
        Initialize the client factory.
        
        Args:
            config_manager: Optional ModelConfigManager instance. If None, uses global instance.
        """
        self.config = config_manager or model_config
    
    def create_client(
        self, 
        model_name: str = None, 
        agent_config: AgentConfig = None,
        **override_params
    ) -> Any:
        """
        Create an appropriate model client for the given model.
        
        Args:
            model_name: Name of the model. If None, uses default model.
            agent_config: Optional agent configuration with overrides.
            **override_params: Additional parameters to override defaults.
            
        Returns:
            Configured model client instance (AsyncOpenAI, AsyncAnthropic, or genai client).
        """
        # Use default model if none specified
        if not model_name:
            model_name = self.config.default_model
            logger.debug(f"[ModelClientFactory] No model specified, using default: {model_name}")
        
        # Determine provider and get configuration
        provider = self.config.get_provider_for_model(model_name)
        api_key = self.config.get_api_key_for_provider(provider)
        defaults = self.config.get_defaults_for_provider(provider)
        
        logger.debug(f"[ModelClientFactory] Creating client for model '{model_name}':")
        logger.debug(f"  - Provider: {provider.value}")
        logger.debug(f"  - API key configured: {'✓' if api_key else '✗'}")
        logger.debug(f"  - Provider defaults: {defaults}")
        
        if not api_key:
            raise ValueError(f"No API key configured for provider {provider.value} (model: {model_name})")
        
        # Build parameters with precedence: override_params > agent_config > defaults
        params = defaults.copy()
        params.update(override_params)
        
        # Apply agent config overrides if provided
        if agent_config:
            logger.debug(f"[ModelClientFactory] Applying agent configuration overrides:")
            logger.debug(f"  - Agent config: {agent_config.dict(exclude_unset=True)}")
            
            if agent_config.temperature is not None:
                params["temperature"] = agent_config.temperature
                logger.debug(f"  - Temperature override: {agent_config.temperature}")
            if agent_config.timeout is not None:
                params["timeout"] = agent_config.timeout
                logger.debug(f"  - Timeout override: {agent_config.timeout}")
            if agent_config.max_retries is not None:
                params["max_retries"] = agent_config.max_retries
                logger.debug(f"  - Max retries override: {agent_config.max_retries}")
            if agent_config.model_selection is not None:
                old_model = model_name
                model_name = agent_config.model_selection
                logger.debug(f"  - Model override: {old_model} → {model_name}")
                # Re-determine provider if model was overridden
                provider = self.config.get_provider_for_model(model_name)
                api_key = self.config.get_api_key_for_provider(provider)
                logger.debug(f"  - Provider changed to: {provider.value}")
        
        # Add required parameters
        params.update({
            "model": model_name,
            "api_key": api_key
        })
        
        # Create client based on provider
        if provider == ModelProvider.OPENAI:
            return self._create_openai_client(params, agent_config)
        elif provider == ModelProvider.GEMINI:
            return self._create_gemini_client(params, agent_config)
        elif provider == ModelProvider.ANTHROPIC:
            return self._create_anthropic_client(params, agent_config)
        else:
            logger.warning(f"[ModelClientFactory] Unknown provider {provider}, falling back to OpenAI")
            return self._create_openai_client(params, agent_config)
    
    def _create_openai_client(self, params: Dict[str, Any], agent_config: AgentConfig = None) -> Any:
        """Create an OpenAI client with the given parameters."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI client not available. Install with: uv add openai")
        
        # Build OpenAI client parameters
        client_params = {
            "api_key": params["api_key"],
        }
        
        # Add optional parameters if present
        if "timeout" in params:
            client_params["timeout"] = params["timeout"]
        if "max_retries" in params:
            client_params["max_retries"] = params["max_retries"]
        
        # Store model configuration for later use
        model_params = {
            "model": params["model"],
            "temperature": params.get("temperature", 0.7),
        }
        
        # Apply agent config overrides for OpenAI-specific parameters
        if agent_config:
            if agent_config.max_tokens is not None:
                model_params["max_tokens"] = agent_config.max_tokens
            if agent_config.top_p is not None:
                model_params["top_p"] = agent_config.top_p
            if agent_config.frequency_penalty is not None:
                model_params["frequency_penalty"] = agent_config.frequency_penalty
            if agent_config.presence_penalty is not None:
                model_params["presence_penalty"] = agent_config.presence_penalty
            if agent_config.stop_sequences is not None:
                model_params["stop"] = agent_config.stop_sequences
        
        logger.info(f"[ModelClientFactory] Creating OpenAI client for model: {model_params['model']}")
        logger.debug(f"[ModelClientFactory] OpenAI client params: {list(client_params.keys())}")
        logger.debug(f"[ModelClientFactory] Model params: {list(model_params.keys())}")
        
        try:
            client = AsyncOpenAI(**client_params)
            # Attach model parameters to client for easy access
            client._model_params = model_params
            return client
        except Exception as e:
            logger.error(f"[ModelClientFactory] Failed to create OpenAI client: {e}")
            raise
    
    def _create_gemini_client(self, params: Dict[str, Any], agent_config: AgentConfig = None) -> Any:
        """Create a Google Gemini client with the given parameters."""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini client not available. Install with: uv add google-generativeai")
        
        # Configure Gemini API
        genai.configure(api_key=params["api_key"])
        
        # Build generation config
        generation_config = {
            "temperature": params.get("temperature", 0.7),
        }
        
        # Apply agent config overrides for Gemini-specific parameters
        if agent_config:
            if agent_config.max_tokens is not None:
                generation_config["max_output_tokens"] = agent_config.max_tokens
            if agent_config.top_p is not None:
                generation_config["top_p"] = agent_config.top_p
            if agent_config.stop_sequences is not None:
                generation_config["stop_sequences"] = agent_config.stop_sequences
            
            # Log unsupported parameters
            unsupported = []
            if agent_config.frequency_penalty is not None:
                unsupported.append("frequency_penalty")
            if agent_config.presence_penalty is not None:
                unsupported.append("presence_penalty")
            if unsupported:
                logger.warning(f"[ModelClientFactory] Gemini does not support: {unsupported}")
        
        logger.info(f"[ModelClientFactory] Creating Gemini client for model: {params['model']}")
        logger.debug(f"[ModelClientFactory] Gemini generation config: {generation_config}")
        
        try:
            # Create Gemini model instance
            model = genai.GenerativeModel(
                model_name=params["model"],
                generation_config=generation_config
            )
            # Attach model parameters for easy access
            model._model_params = {
                "model": params["model"],
                **generation_config
            }
            return model
        except Exception as e:
            logger.error(f"[ModelClientFactory] Failed to create Gemini client: {e}")
            raise
    
    def _create_anthropic_client(self, params: Dict[str, Any], agent_config: AgentConfig = None) -> Any:
        """Create an Anthropic client with the given parameters."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic client not available. Install with: uv add anthropic")
        
        # Build Anthropic client parameters
        client_params = {
            "api_key": params["api_key"],
        }
        
        # Add optional parameters if present
        if "timeout" in params:
            client_params["timeout"] = params["timeout"]
        if "max_retries" in params:
            client_params["max_retries"] = params["max_retries"]
        
        # Store model configuration for later use
        model_params = {
            "model": params["model"],
            "temperature": params.get("temperature", 0.7),
        }
        
        # Apply agent config overrides for Anthropic-specific parameters
        if agent_config:
            if agent_config.max_tokens is not None:
                model_params["max_tokens"] = agent_config.max_tokens
            if agent_config.top_p is not None:
                model_params["top_p"] = agent_config.top_p
            if agent_config.stop_sequences is not None:
                model_params["stop_sequences"] = agent_config.stop_sequences
            
            # Log unsupported parameters
            unsupported = []
            if agent_config.frequency_penalty is not None:
                unsupported.append("frequency_penalty")
            if agent_config.presence_penalty is not None:
                unsupported.append("presence_penalty")
            if unsupported:
                logger.warning(f"[ModelClientFactory] Anthropic does not support: {unsupported}")
        
        logger.info(f"[ModelClientFactory] Creating Anthropic client for model: {model_params['model']}")
        logger.debug(f"[ModelClientFactory] Anthropic client params: {list(client_params.keys())}")
        logger.debug(f"[ModelClientFactory] Model params: {list(model_params.keys())}")
        
        try:
            client = AsyncAnthropic(**client_params)
            # Attach model parameters to client for easy access
            client._model_params = model_params
            return client
        except Exception as e:
            logger.error(f"[ModelClientFactory] Failed to create Anthropic client: {e}")
            raise
    
    def get_supported_providers(self) -> Dict[str, bool]:
        """
        Get information about which providers are available.
        
        Returns:
            Dictionary mapping provider names to availability status.
        """
        return {
            "openai": OPENAI_AVAILABLE,
            "anthropic": ANTHROPIC_AVAILABLE,
            "gemini": GEMINI_AVAILABLE
        }
    
    def validate_model_support(self, model_name: str) -> Dict[str, Any]:
        """
        Validate if a model is supported and properly configured.
        
        Args:
            model_name: The model name to validate.
            
        Returns:
            Dictionary with validation results.
        """
        provider = self.config.get_provider_for_model(model_name)
        api_key = self.config.get_api_key_for_provider(provider)
        
        result = {
            "model": model_name,
            "provider": provider.value,
            "supported": False,
            "api_key_configured": bool(api_key),
            "client_available": False,
            "issues": []
        }
        
        # Check if client is available
        if provider == ModelProvider.OPENAI and OPENAI_AVAILABLE:
            result["client_available"] = True
        elif provider == ModelProvider.ANTHROPIC and ANTHROPIC_AVAILABLE:
            result["client_available"] = True
        elif provider == ModelProvider.GEMINI and GEMINI_AVAILABLE:
            result["client_available"] = True
        else:
            result["issues"].append(f"Client for {provider.value} not available")
        
        # Check API key
        if not api_key:
            result["issues"].append(f"API key for {provider.value} not configured")
        
        # Overall support
        result["supported"] = result["client_available"] and result["api_key_configured"]
        
        return result
    
    def create_llamaindex_llm(
        self, 
        model_name: str = None, 
        agent_config: AgentConfig = None,
        **override_params
    ) -> Any:
        """
        Create a LlamaIndex LLM instance for the given model.
        
        Handles provider-specific imports and parameter compatibility.
        
        Args:
            model_name: Name of the model. If None, uses default model.
            agent_config: Optional agent configuration with overrides.
            **override_params: Additional parameters to override defaults.
            
        Returns:
            Configured LlamaIndex LLM instance (OpenAI, Anthropic, or Gemini).
        """
        # Use default model if none specified
        if not model_name:
            model_name = self.config.default_model
            logger.debug(f"[ModelClientFactory] No model specified, using default: {model_name}")
        
        # Determine provider and get configuration
        provider = self.config.get_provider_for_model(model_name)
        api_key = self.config.get_api_key_for_provider(provider)
        defaults = self.config.get_defaults_for_provider(provider)
        
        logger.debug(f"[ModelClientFactory] Creating LlamaIndex LLM for model '{model_name}':")
        logger.debug(f"  - Provider: {provider.value}")
        logger.debug(f"  - API key configured: {'✓' if api_key else '✗'}")
        
        if not api_key:
            raise ValueError(f"No API key configured for provider {provider.value} (model: {model_name})")
        
        # Build parameters with precedence: override_params > agent_config > defaults
        params = defaults.copy()
        params.update(override_params)
        
        # Apply agent config overrides if provided
        if agent_config:
            logger.debug(f"[ModelClientFactory] Applying agent configuration overrides")
            
            if agent_config.temperature is not None:
                params["temperature"] = agent_config.temperature
            if agent_config.max_tokens is not None:
                params["max_tokens"] = agent_config.max_tokens
            if agent_config.top_p is not None:
                params["top_p"] = agent_config.top_p
            if agent_config.model_selection is not None:
                old_model = model_name
                model_name = agent_config.model_selection
                logger.debug(f"  - Model override: {old_model} → {model_name}")
                # Re-determine provider if model was overridden
                provider = self.config.get_provider_for_model(model_name)
                api_key = self.config.get_api_key_for_provider(provider)
        
        # Add required parameters
        params.update({
            "model": model_name,
            "api_key": api_key
        })
        
        # Create LLM based on provider
        if provider == ModelProvider.OPENAI:
            return self._create_llamaindex_openai(params)
        elif provider == ModelProvider.ANTHROPIC:
            return self._create_llamaindex_anthropic(params)
        elif provider == ModelProvider.GEMINI:
            return self._create_llamaindex_gemini(params)
        else:
            logger.warning(f"[ModelClientFactory] Unknown provider {provider}, falling back to OpenAI")
            return self._create_llamaindex_openai(params)
    
    def _create_llamaindex_openai(self, params: Dict[str, Any]) -> Any:
        """
        Create a LlamaIndex OpenAI LLM with error handling.
        
        Patches the internal AsyncOpenAI client to sanitize messages before API calls,
        fixing cross-provider compatibility issues (e.g., Claude → OpenAI transitions
        where tool_calls arguments are dicts instead of JSON strings).
        
        Args:
            params: Dictionary of parameters for the LLM.
            
        Returns:
            Configured LlamaIndex OpenAI LLM instance (with patched client for sanitization).
        """
        try:
            from llama_index.llms.openai import OpenAI
        except ImportError as e:
            raise ImportError(
                f"LlamaIndex OpenAI LLM not available: {e}\n"
                f"Install with: uv add llama-index-llms-openai"
            )
        
        logger.info(f"[ModelClientFactory] Creating LlamaIndex OpenAI LLM for model: {params['model']}")
        
        # Try with all parameters
        try:
            llm = OpenAI(**params)
        except TypeError as e:
            # Remove unsupported parameters and retry
            logger.warning(f"[ModelClientFactory] Parameter error: {e}, retrying without problematic params")
            llm = self._retry_without_unsupported_params(OpenAI, params, e)
        
        # Patch the internal AsyncOpenAI client for cross-provider compatibility
        _patch_openai_client_for_sanitization(llm)
        
        return llm
    
    def _create_llamaindex_anthropic(self, params: Dict[str, Any]) -> Any:
        """
        Create a LlamaIndex Anthropic LLM with error handling.
        
        Patches the internal AsyncAnthropic client to sanitize messages before API calls,
        fixing cross-provider compatibility issues (e.g., OpenAI → Claude transitions
        where tool_calls are in OpenAI format instead of Anthropic format).
        
        Args:
            params: Dictionary of parameters for the LLM.
            
        Returns:
            Configured LlamaIndex Anthropic LLM instance (with patched client for sanitization).
        """
        try:
            from llama_index.llms.anthropic import Anthropic
        except ImportError as e:
            raise ImportError(
                f"LlamaIndex Anthropic LLM not available: {e}\n"
                f"Install with: uv add llama-index-llms-anthropic"
            )
        
        logger.info(f"[ModelClientFactory] Creating LlamaIndex Anthropic LLM for model: {params['model']}")
        
        # Try with all parameters
        try:
            llm = Anthropic(**params)
        except TypeError as e:
            # Remove unsupported parameters and retry
            logger.warning(f"[ModelClientFactory] Parameter error: {e}, retrying without problematic params")
            llm = self._retry_without_unsupported_params(Anthropic, params, e)
        
        # Patch the internal AsyncAnthropic client for cross-provider compatibility
        _patch_anthropic_client_for_sanitization(llm)
        
        return llm
    
    def _create_llamaindex_gemini(self, params: Dict[str, Any]) -> Any:
        """
        Create a LlamaIndex Gemini LLM with error handling.
        
        Patches the LLM to sanitize ChatMessages before conversion,
        fixing cross-provider compatibility issues (e.g., OpenAI → Gemini transitions
        where ToolCallBlock.tool_kwargs are JSON strings instead of dicts).
        
        Args:
            params: Dictionary of parameters for the LLM.
            
        Returns:
            Configured LlamaIndex Gemini LLM instance (with patched methods for sanitization).
        """
        try:
            from llama_index.llms.google_genai import GoogleGenAI
        except ImportError as e:
            raise ImportError(
                f"LlamaIndex Google GenAI LLM not available: {e}\n"
                f"Install with: uv add llama-index-llms-google-genai"
            )
        
        logger.info(f"[ModelClientFactory] Creating LlamaIndex Google GenAI LLM for model: {params['model']}")
        
        # Try with all parameters
        try:
            llm = GoogleGenAI(**params)
        except TypeError as e:
            # Remove unsupported parameters and retry
            logger.warning(f"[ModelClientFactory] Parameter error: {e}, retrying without problematic params")
            llm = self._retry_without_unsupported_params(GoogleGenAI, params, e)
        
        # Patch the LLM for cross-provider compatibility
        _patch_gemini_llm_for_sanitization(llm)
        
        return llm
    
    def _retry_without_unsupported_params(
        self, 
        llm_class: Type, 
        params: Dict[str, Any], 
        error: TypeError
    ) -> Any:
        """
        Retry LLM creation by removing unsupported parameters.
        
        Parses the TypeError message to identify problematic parameters
        and removes them before retrying.
        
        Args:
            llm_class: The LLM class to instantiate.
            params: Dictionary of parameters.
            error: The TypeError that was raised.
            
        Returns:
            Configured LLM instance.
            
        Raises:
            TypeError: If the error message cannot be parsed or retry fails.
        """
        # Extract parameter name from error message
        # e.g., "unexpected keyword argument 'temperature'"
        # or "__init__() got an unexpected keyword argument 'temperature'"
        match = re.search(r"(?:unexpected keyword argument|got an unexpected keyword argument)\s+'(\w+)'", str(error))
        
        if match:
            param_to_remove = match.group(1)
            logger.info(f"[ModelClientFactory] Removing unsupported parameter: {param_to_remove}")
            params_copy = params.copy()
            params_copy.pop(param_to_remove, None)
            
            try:
                return llm_class(**params_copy)
            except TypeError as retry_error:
                # If we still get an error, try removing another parameter
                logger.warning(f"[ModelClientFactory] Still getting error after removing {param_to_remove}: {retry_error}")
                return self._retry_without_unsupported_params(llm_class, params_copy, retry_error)
        else:
            # Can't parse error, raise original
            logger.error(f"[ModelClientFactory] Cannot parse TypeError message: {error}")
            raise error

# Global factory instance
client_factory = ModelClientFactory() 