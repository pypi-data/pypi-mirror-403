"""
LlamaIndex Memory Adapter

This module provides an adapter between the framework's SessionStorage
and LlamaIndex's Memory system, allowing seamless integration of conversation
history into LlamaIndex agents.

The adapter:
- Loads conversation history from SessionStorage
- Converts MessageData to LlamaIndex ChatMessage format
- Creates a Memory object that can be used with LlamaIndex agents
- Keeps memory synchronized with SessionStorage
- Supports model-specific cache keys for proper tokenization on model changes

Version: 0.2.0
"""

import logging
from typing import Optional, List
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer

from ..session.session_storage import SessionStorageInterface, MessageData

logger = logging.getLogger(__name__)

# Global memory cache shared across all adapter instances
# Cache key format: {user_id}:{session_id}:{model_name} or {user_id}:{session_id} for backward compat
_GLOBAL_MEMORY_CACHE: dict[str, ChatMemoryBuffer] = {}



class LlamaIndexMemoryAdapter:
    """
    Adapter that bridges SessionStorage and LlamaIndex Memory.
    
    This adapter loads conversation history from SessionStorage and creates
    a LlamaIndex Memory object that can be used with agents.
    """
    
    def __init__(self, session_storage: SessionStorageInterface):
        """
        Initialize the memory adapter.
        
        Args:
            session_storage: The session storage backend to use
        """
        self.session_storage = session_storage
        # Use global cache instead of instance cache
        self._memory_cache = _GLOBAL_MEMORY_CACHE
    
    def _build_cache_key(
        self, user_id: str, session_id: str, model_name: Optional[str] = None
    ) -> str:
        """
        Build a cache key for memory storage.
        
        Args:
            user_id: The user identifier
            session_id: The session identifier
            model_name: Optional model name for model-specific caching
            
        Returns:
            Cache key string in format {user_id}:{session_id}:{model_name}
            or {user_id}:{session_id} if model_name is None
        """
        if model_name:
            return f"{user_id}:{session_id}:{model_name}"
        return f"{user_id}:{session_id}"

    def _invalidate_other_model_caches(
        self, user_id: str, session_id: str, current_model: str
    ) -> int:
        """
        Invalidate cache entries for the same session but different models.
        
        When a model changes mid-session, old cache entries with different
        tokenization should be invalidated to ensure proper memory handling.
        
        Args:
            user_id: The user identifier
            session_id: The session identifier
            current_model: The current model (entries for this model are kept)
            
        Returns:
            Number of cache entries invalidated
        """
        prefix = f"{user_id}:{session_id}:"
        current_key = f"{user_id}:{session_id}:{current_model}"
        legacy_key = f"{user_id}:{session_id}"
        
        keys_to_remove = []
        for key in self._memory_cache.keys():
            # Match keys for this session but different models
            if key.startswith(prefix) and key != current_key:
                keys_to_remove.append(key)
            # Also remove legacy key without model suffix
            elif key == legacy_key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._memory_cache[key]
            logger.info(f"🗑️ Invalidated cache entry: {key}")
        
        return len(keys_to_remove)

    async def get_memory_for_session(
        self, 
        session_id: str,
        user_id: str,
        model_name: Optional[str] = None,
        token_limit: int = 30000
    ) -> ChatMemoryBuffer:
        """
        Get or create a Memory object for a session.
        
        This method:
        1. Checks if memory is already cached (with model-specific key)
        2. Invalidates old cache entries for same session with different models
        3. If not cached, loads conversation history from SessionStorage
        4. Converts messages to LlamaIndex format
        5. Creates a Memory object with the history
        
        Args:
            session_id: The session identifier
            user_id: The user identifier
            model_name: Optional model name for model-specific caching.
                       When provided, cache key includes model for proper
                       tokenization handling on model changes.
            token_limit: Maximum tokens for short-term memory
            
        Returns:
            Memory object ready to use with LlamaIndex agents
        """
        # Build cache key (includes model if provided)
        cache_key = self._build_cache_key(user_id, session_id, model_name)
        
        # Invalidate old cache entries for different models if model is specified
        if model_name:
            invalidated = self._invalidate_other_model_caches(user_id, session_id, model_name)
            if invalidated > 0:
                logger.info(
                    f"🔄 Invalidated {invalidated} old cache entries for session {session_id} "
                    f"due to model change to {model_name}"
                )
        
        # Check cache
        if cache_key in self._memory_cache:
            logger.info(f"✅ Using cached memory for session {session_id} (model: {model_name or 'default'})")
            return self._memory_cache[cache_key]
        
        # Create new memory
        logger.info(f"🆕 Creating new memory for session {session_id} (model: {model_name or 'default'})")
        memory = ChatMemoryBuffer.from_defaults(
            token_limit=token_limit,
        )
        
        # Load conversation history from SessionStorage
        try:
            message_history = await self.session_storage.get_conversation_history(
                session_id=session_id,
                limit=100  # Load last 100 messages
            )
            
            if message_history:
                # Convert to LlamaIndex ChatMessage format
                chat_messages = self._convert_to_chat_messages(message_history)
                
                # Put messages into memory
                if chat_messages:
                    memory.put_messages(chat_messages)
                    logger.info(f"📚 Loaded {len(chat_messages)} messages into memory for session {session_id}")
                    logger.info(f"📝 First message: {chat_messages[0].content[:50]}..." if chat_messages else "")
                    
                    # Sanitize to ensure no empty tool_calls arrays
                    self.sanitize_memory_buffer(memory)
            else:
                logger.info(f"⚠️ No existing history for session {session_id}, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading conversation history for session {session_id}: {e}")
            # Continue with empty memory rather than failing
        
        # Cache the memory
        self._memory_cache[cache_key] = memory
        
        return memory
    
    def _convert_to_chat_messages(self, message_data_list: List[MessageData]) -> List[ChatMessage]:
        """
        Convert MessageData objects to LlamaIndex ChatMessage objects.
        
        Args:
            message_data_list: List of MessageData from SessionStorage
            
        Returns:
            List of ChatMessage objects for LlamaIndex
        """
        chat_messages = []
        
        for msg_data in message_data_list:
            # Determine role
            if msg_data.role == "user":
                role = MessageRole.USER
            elif msg_data.role == "assistant":
                role = MessageRole.ASSISTANT
            elif msg_data.role == "system":
                role = MessageRole.SYSTEM
            else:
                logger.warning(f"Unknown role '{msg_data.role}', defaulting to USER")
                role = MessageRole.USER
            
            # Get content - prefer text_content, fallback to response_text_main
            content = msg_data.text_content or msg_data.response_text_main or ""
            
            # Create ChatMessage with clean additional_kwargs
            # OpenAI rejects empty tool_calls arrays, so we never include them
            chat_message = ChatMessage(
                role=role,
                content=content,
                additional_kwargs={}
            )
            
            chat_messages.append(chat_message)
        
        return chat_messages

    def _sanitize_chat_messages(
        self, messages: List[ChatMessage], target_provider: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Sanitize ChatMessage objects for cross-provider compatibility.
        
        Handles incompatibilities when switching between providers:
        - OpenAI rejects empty tool_calls arrays
        - OpenAI uses format: {"id": "...", "function": {"name": "...", "arguments": "JSON string"}}
        - Anthropic/Gemini use format: {"id": "...", "name": "...", "input": {dict}}
        - Gemini uses ToolCallBlock.tool_kwargs which must be a dict (not JSON string)
        - OpenAI rejects Anthropic-specific fields (stop_reason, etc.)
        - Some providers add metadata that others reject
        
        Args:
            messages: List of ChatMessage objects to sanitize
            target_provider: Target provider ('openai', 'anthropic', 'gemini')
                           If None, applies generic sanitization for all providers.
            
        Returns:
            List of sanitized ChatMessage objects
        """
        import json
        
        # Fields that are provider-specific and should be removed for cross-provider compat
        ANTHROPIC_SPECIFIC_FIELDS = {
            'stop_reason', 'stop_sequence', 'usage', 'model', 'id', 'type',
            'content_block', 'index', 'message', 'delta'
        }
        OPENAI_SPECIFIC_FIELDS = {
            'function_call', 'refusal', 'audio', 'logprobs'
        }
        # Fields that cause issues across all providers
        PROBLEMATIC_FIELDS = {
            'raw_response', 'raw', '_raw', 'response_metadata'
        }
        
        sanitized = []
        for msg_idx, msg in enumerate(messages):
            additional_kwargs = dict(msg.additional_kwargs or {})
            modified = False
            
            # 0. Sanitize message.blocks for Gemini/Anthropic compatibility
            # Gemini uses ToolCallBlock.tool_kwargs which must be a dict, not a JSON string
            sanitized_blocks = None
            if target_provider in ('anthropic', 'gemini'):
                if hasattr(msg, 'blocks') and msg.blocks:
                    try:
                        from llama_index.core.base.llms.types import ToolCallBlock
                        new_blocks = []
                        blocks_modified = False
                        
                        logger.debug(f"🔍 Message {msg_idx} ({msg.role}): checking {len(msg.blocks)} blocks")
                        
                        for block_idx, block in enumerate(msg.blocks):
                            block_type = type(block).__name__
                            logger.debug(f"🔍 Block {block_idx}: type={block_type}")
                            
                            if isinstance(block, ToolCallBlock):
                                kwargs_type = type(block.tool_kwargs).__name__
                                logger.info(f"🔍 Found ToolCallBlock: tool_name={block.tool_name}, tool_kwargs type={kwargs_type}")
                                
                                # Check if tool_kwargs is a JSON string that needs parsing
                                if isinstance(block.tool_kwargs, str):
                                    try:
                                        parsed_kwargs = json.loads(block.tool_kwargs)
                                        # Create new ToolCallBlock with parsed kwargs
                                        new_block = ToolCallBlock(
                                            tool_call_id=block.tool_call_id,
                                            tool_name=block.tool_name,
                                            tool_kwargs=parsed_kwargs
                                        )
                                        new_blocks.append(new_block)
                                        blocks_modified = True
                                        logger.info(
                                            f"🔄 [{target_provider.title()}] Parsed ToolCallBlock.tool_kwargs "
                                            f"from JSON string to dict for tool '{block.tool_name}'"
                                        )
                                    except (json.JSONDecodeError, TypeError) as e:
                                        logger.warning(
                                            f"Failed to parse ToolCallBlock.tool_kwargs: {e}, keeping original"
                                        )
                                        new_blocks.append(block)
                                else:
                                    logger.debug(f"🔍 ToolCallBlock.tool_kwargs already a dict, keeping as-is")
                                    new_blocks.append(block)
                            else:
                                new_blocks.append(block)
                        
                        if blocks_modified:
                            sanitized_blocks = new_blocks
                            modified = True
                            logger.info(f"🔄 Message {msg_idx}: blocks were modified")
                        else:
                            logger.debug(f"🔍 Message {msg_idx}: no blocks needed modification")
                    except ImportError as e:
                        logger.warning(f"Could not import ToolCallBlock: {e}")
                else:
                    logger.debug(f"🔍 Message {msg_idx} ({msg.role}): no blocks attribute or empty blocks")
            
            # 1. Handle tool_calls - convert format based on target provider
            if 'tool_calls' in additional_kwargs:
                if not additional_kwargs['tool_calls']:
                    del additional_kwargs['tool_calls']
                    modified = True
                    logger.debug(f"Removed empty tool_calls from {msg.role} message")
                elif target_provider == 'openai':
                    # OpenAI format: {"id": "...", "function": {"name": "...", "arguments": "JSON string"}}
                    # Convert from Anthropic format if needed
                    sanitized_tool_calls = []
                    for tc in additional_kwargs['tool_calls']:
                        tc_copy = dict(tc) if isinstance(tc, dict) else tc
                        if not isinstance(tc_copy, dict):
                            sanitized_tool_calls.append(tc_copy)
                            continue
                        
                        # Check if it's Anthropic format (has 'input' and 'name' at top level)
                        if 'input' in tc_copy and 'name' in tc_copy and 'function' not in tc_copy:
                            # Convert Anthropic → OpenAI format
                            args = tc_copy.get('input', {})
                            if not isinstance(args, str):
                                try:
                                    args = json.dumps(args)
                                except (TypeError, ValueError):
                                    args = str(args)
                            
                            openai_tc = {
                                'id': tc_copy.get('id', ''),
                                'type': 'function',
                                'function': {
                                    'name': tc_copy.get('name', ''),
                                    'arguments': args
                                }
                            }
                            sanitized_tool_calls.append(openai_tc)
                            modified = True
                            logger.info(
                                f"🔄 [OpenAI] Converted tool_call from Anthropic format "
                                f"(input→function.arguments)"
                            )
                        elif 'function' in tc_copy:
                            # Already OpenAI format, just ensure arguments is a string
                            func = tc_copy.get('function', {})
                            if isinstance(func, dict):
                                func_copy = dict(func)
                                args = func_copy.get('arguments')
                                if args is not None and not isinstance(args, str):
                                    try:
                                        func_copy['arguments'] = json.dumps(args)
                                        tc_copy = dict(tc_copy)
                                        tc_copy['function'] = func_copy
                                        modified = True
                                        logger.info(
                                            f"🔄 [OpenAI] Converted tool_call arguments from "
                                            f"{type(args).__name__} to JSON string"
                                        )
                                    except (TypeError, ValueError) as e:
                                        logger.warning(f"Failed to convert arguments to JSON: {e}")
                                        func_copy['arguments'] = str(args)
                                        tc_copy = dict(tc_copy)
                                        tc_copy['function'] = func_copy
                                        modified = True
                            sanitized_tool_calls.append(tc_copy)
                        else:
                            sanitized_tool_calls.append(tc_copy)
                    
                    additional_kwargs['tool_calls'] = sanitized_tool_calls
                    
                elif target_provider in ('anthropic', 'gemini'):
                    # Anthropic/Gemini format: {"id": "...", "name": "...", "input": {dict}} or {"args": {dict}}
                    # Convert from OpenAI format if needed
                    sanitized_tool_calls = []
                    for tc in additional_kwargs['tool_calls']:
                        tc_copy = dict(tc) if isinstance(tc, dict) else tc
                        if not isinstance(tc_copy, dict):
                            sanitized_tool_calls.append(tc_copy)
                            continue
                        
                        # Check if it's OpenAI format (has 'function' key)
                        if 'function' in tc_copy:
                            # Convert OpenAI → Anthropic/Gemini format
                            func = tc_copy.get('function', {})
                            args = func.get('arguments', '{}') if isinstance(func, dict) else '{}'
                            
                            # Parse JSON string to dict
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except (json.JSONDecodeError, TypeError):
                                    logger.warning(f"Failed to parse arguments JSON, using empty dict")
                                    args = {}
                            
                            # Gemini uses 'args', Anthropic uses 'input'
                            if target_provider == 'gemini':
                                converted_tc = {
                                    'name': func.get('name', '') if isinstance(func, dict) else '',
                                    'args': args
                                }
                            else:
                                converted_tc = {
                                    'id': tc_copy.get('id', ''),
                                    'name': func.get('name', '') if isinstance(func, dict) else '',
                                    'input': args
                                }
                            sanitized_tool_calls.append(converted_tc)
                            modified = True
                            logger.info(
                                f"🔄 [{target_provider.title()}] Converted tool_call from OpenAI format "
                                f"(function.arguments→{'args' if target_provider == 'gemini' else 'input'})"
                            )
                        elif 'input' in tc_copy or 'args' in tc_copy:
                            # Already Anthropic/Gemini format, ensure input/args is a dict
                            key = 'args' if 'args' in tc_copy else 'input'
                            tool_input = tc_copy.get(key)
                            if isinstance(tool_input, str):
                                try:
                                    tc_copy = dict(tc_copy)
                                    tc_copy[key] = json.loads(tool_input)
                                    modified = True
                                    logger.info(
                                        f"🔄 [{target_provider.title()}] Parsed tool_call {key} "
                                        f"from JSON string to dict"
                                    )
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            sanitized_tool_calls.append(tc_copy)
                        else:
                            sanitized_tool_calls.append(tc_copy)
                    
                    additional_kwargs['tool_calls'] = sanitized_tool_calls
            
            # 2. Remove provider-specific fields based on target
            if target_provider == 'openai':
                # Remove Anthropic-specific fields when targeting OpenAI
                for field in ANTHROPIC_SPECIFIC_FIELDS:
                    if field in additional_kwargs:
                        del additional_kwargs[field]
                        modified = True
                        logger.debug(f"Removed Anthropic field '{field}' for OpenAI compat")
            
            elif target_provider in ('anthropic', 'gemini'):
                # Remove OpenAI-specific fields when targeting Anthropic/Gemini
                for field in OPENAI_SPECIFIC_FIELDS:
                    if field in additional_kwargs:
                        del additional_kwargs[field]
                        modified = True
                        logger.debug(f"Removed OpenAI field '{field}' for {target_provider} compat")
            
            # 3. Always remove known problematic fields
            for field in PROBLEMATIC_FIELDS:
                if field in additional_kwargs:
                    del additional_kwargs[field]
                    modified = True
                    logger.debug(f"Removed problematic field '{field}'")
            
            # 4. Remove any nested objects that might cause serialization issues
            keys_to_remove = []
            for key, value in additional_kwargs.items():
                if value is None:
                    keys_to_remove.append(key)
                elif isinstance(value, (dict, list)) and not value:
                    # Empty dicts/lists can cause issues
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del additional_kwargs[key]
                modified = True
                logger.debug(f"Removed empty/None field '{key}'")
            
            if modified:
                logger.debug(f"Sanitized {msg.role} message, remaining kwargs: {list(additional_kwargs.keys())}")
            
            # Create new message with sanitized kwargs and optionally sanitized blocks
            if sanitized_blocks is not None:
                # When we have sanitized blocks, we must NOT pass content parameter
                # because ChatMessage will override blocks with content if both are provided.
                # The blocks already contain TextBlock for the content.
                sanitized_msg = ChatMessage(
                    role=msg.role,
                    blocks=sanitized_blocks,
                    additional_kwargs=additional_kwargs
                )
                logger.debug(
                    f"Created sanitized message with {len(sanitized_blocks)} blocks "
                    f"(content derived from blocks)"
                )
            else:
                sanitized_msg = ChatMessage(
                    role=msg.role,
                    content=msg.content,
                    additional_kwargs=additional_kwargs
                )
            sanitized.append(sanitized_msg)
        
        return sanitized

    def sanitize_memory_buffer(
        self, memory: ChatMemoryBuffer, target_provider: Optional[str] = None
    ) -> None:
        """
        Sanitize all messages in a ChatMemoryBuffer in-place for cross-provider compatibility.
        
        This removes/transforms fields that cause issues when switching between providers:
        - Empty tool_calls arrays (OpenAI rejects)
        - Anthropic-specific fields when targeting OpenAI
        - OpenAI-specific fields when targeting Anthropic
        - Empty/None values that cause serialization issues
        
        Call this before using memory with a different model/provider.
        
        Args:
            memory: The ChatMemoryBuffer to sanitize
            target_provider: Target provider ('openai', 'anthropic', 'gemini').
                           If None, applies generic sanitization.
        """
        logger.info(f"🔧 sanitize_memory_buffer called with target_provider={target_provider}")
        try:
            # Access the internal chat store
            chat_store = memory.chat_store
            store_key = memory.chat_store_key
            
            logger.info(f"🔧 chat_store type: {type(chat_store)}, store_key: {store_key}")
            
            if hasattr(chat_store, 'store') and store_key in chat_store.store:
                messages = chat_store.store[store_key]
                logger.info(f"🔧 Found {len(messages)} messages to sanitize")
                
                # Log details about blocks in messages
                for i, msg in enumerate(messages):
                    if hasattr(msg, 'blocks') and msg.blocks:
                        for j, block in enumerate(msg.blocks):
                            block_type = type(block).__name__
                            if hasattr(block, 'tool_kwargs'):
                                kwargs_type = type(block.tool_kwargs).__name__
                                logger.info(f"🔧 Message {i}, Block {j}: {block_type}, tool_kwargs type: {kwargs_type}")
                
                sanitized = self._sanitize_chat_messages(messages, target_provider)
                chat_store.store[store_key] = sanitized
                logger.info(
                    f"🧹 Sanitized {len(messages)} messages in memory buffer"
                    f"{f' for {target_provider}' if target_provider else ''}"
                )
                
                # Log details about sanitized blocks
                for i, msg in enumerate(sanitized):
                    if hasattr(msg, 'blocks') and msg.blocks:
                        for j, block in enumerate(msg.blocks):
                            block_type = type(block).__name__
                            if hasattr(block, 'tool_kwargs'):
                                kwargs_type = type(block.tool_kwargs).__name__
                                logger.info(f"🔧 AFTER: Message {i}, Block {j}: {block_type}, tool_kwargs type: {kwargs_type}")
            else:
                logger.warning(f"🔧 Could not find messages in chat_store (has store: {hasattr(chat_store, 'store')}, key exists: {store_key in getattr(chat_store, 'store', {})})")
        except Exception as e:
            logger.warning(f"Could not sanitize memory buffer: {e}")
            import traceback
            logger.warning(f"Traceback: {traceback.format_exc()}")
    
    def clear_cache(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Clear memory cache.
        
        Args:
            session_id: If provided, clear only this session
            user_id: If provided, clear all sessions for this user
            model_name: If provided with session_id and user_id, clear only
                       the cache for that specific model. If not provided,
                       clears all model variants for the session.
        """
        if session_id and user_id:
            if model_name:
                # Clear specific model cache
                cache_key = self._build_cache_key(user_id, session_id, model_name)
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                    logger.info(f"Cleared memory cache for session {session_id} model {model_name}")
            else:
                # Clear all model variants for this session
                prefix = f"{user_id}:{session_id}"
                keys_to_remove = [
                    k for k in self._memory_cache.keys()
                    if k == prefix or k.startswith(f"{prefix}:")
                ]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                logger.info(
                    f"Cleared memory cache for session {session_id} "
                    f"({len(keys_to_remove)} entries including all model variants)"
                )
        elif user_id:
            # Clear all sessions for user
            keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._memory_cache[key]
            logger.info(f"Cleared memory cache for user {user_id} ({len(keys_to_remove)} sessions)")
        else:
            # Clear all
            self._memory_cache.clear()
            logger.info("Cleared all memory cache")
