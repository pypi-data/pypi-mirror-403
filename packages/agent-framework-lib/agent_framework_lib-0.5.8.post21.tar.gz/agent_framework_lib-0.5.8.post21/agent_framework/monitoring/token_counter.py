"""
Token Counter Module

Provides token counting functionality using tiktoken library with model-aware
encoding selection. Supports OpenAI, Anthropic, and Gemini models with
appropriate encoding fallbacks.

This module provides:
- Accurate token counting using tiktoken
- Model-specific encoding selection
- Pattern-based fallback for unknown models
- Support for both single text and chat message lists
"""

from typing import Optional

from pydantic import BaseModel


class TokenCount(BaseModel):
    """Token count result with encoding metadata."""

    count: int
    encoding_name: str
    model_name: Optional[str] = None


class TokenCounter:
    """
    Count tokens using tiktoken with model-aware encoding selection.

    This class provides accurate token counting for LLM interactions by selecting
    the appropriate tiktoken encoding based on the model name. For non-OpenAI models
    (Claude, Gemini), it uses cl100k_base as an approximation.

    Attributes:
        model_name: Optional model name for encoding selection
        MODEL_ENCODINGS: Mapping of specific model names to encodings
        PROVIDER_ENCODINGS: Pattern-based encoding detection
        DEFAULT_ENCODING: Fallback encoding when model is unknown

    Example:
        ```python
        counter = TokenCounter(model_name="gpt-5-mini")
        result = counter.count_tokens("Hello, world!")
        print(f"Tokens: {result.count}, Encoding: {result.encoding_name}")
        ```
    """

    # Model to encoding mapping based on framework's model_config.py
    # OpenAI models use tiktoken natively, Claude/Gemini use approximations
    MODEL_ENCODINGS: dict[str, str] = {
        # OpenAI GPT-5 series (o200k_base - latest encoding)
        "gpt-5.1": "o200k_base",
        "gpt-5": "o200k_base",
        "gpt-5-mini": "o200k_base",
        "gpt-5-nano": "o200k_base",
        "gpt-5-mini-turbo": "o200k_base",
        "gpt-5-minio": "o200k_base",
        "gpt-5-minio-mini": "o200k_base",
        # OpenAI GPT-4o series (o200k_base)
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4o-2024-05-13": "o200k_base",
        "gpt-4o-2024-08-06": "o200k_base",
        # OpenAI GPT-4 series (cl100k_base)
        "gpt-4": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-4-turbo-preview": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-0125-preview": "cl100k_base",
        "gpt-4-1106-preview": "cl100k_base",
        # OpenAI GPT-3.5 series (cl100k_base)
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-16k": "cl100k_base",
        "gpt-3.5-turbo-0125": "cl100k_base",
        "gpt-3.5-turbo-1106": "cl100k_base",
        # OpenAI o1/o3/o4 reasoning series (o200k_base)
        "o1-preview": "o200k_base",
        "o1-mini": "o200k_base",
        "o1": "o200k_base",
        "o3": "o200k_base",
        "o3-mini": "o200k_base",
        "o4-mini": "o200k_base",
        # Anthropic Claude models (cl100k_base approximation)
        "claude-haiku-4-5-20251001": "cl100k_base",
        "claude-sonnet-4-5-20250929": "cl100k_base",
        "claude-opus-4-5-20251101": "cl100k_base",
        "claude-3-opus-20240229": "cl100k_base",
        "claude-3-sonnet-20240229": "cl100k_base",
        "claude-3-haiku-20240307": "cl100k_base",
        "claude-3-5-sonnet-20240620": "cl100k_base",
        "claude-3-5-sonnet-20241022": "cl100k_base",
        "claude-3-5-haiku-20241022": "cl100k_base",
        "claude-2.1": "cl100k_base",
        "claude-2.0": "cl100k_base",
        "claude-instant-1.2": "cl100k_base",
        # Google Gemini models (cl100k_base approximation)
        "gemini-3-pro-preview": "cl100k_base",
        "gemini-2.5-pro": "cl100k_base",
        "gemini-2.5-flash": "cl100k_base",
        "gemini-2.5-flash-lite": "cl100k_base",
        "gemini-2.5-flash-preview-04-17": "cl100k_base",
        "gemini-2.0-flash-exp": "cl100k_base",
        "gemini-1.5-pro": "cl100k_base",
        "gemini-1.5-flash": "cl100k_base",
        "gemini-pro": "cl100k_base",
        "gemini-pro-vision": "cl100k_base",
    }

    # Pattern-based encoding detection for unknown models
    PROVIDER_ENCODINGS: dict[str, str] = {
        "gpt-5": "o200k_base",  # GPT-5 series
        "gpt-4o": "o200k_base",  # GPT-4o series
        "gpt-4": "cl100k_base",  # GPT-4 series
        "gpt-3": "cl100k_base",  # GPT-3.5 series
        "o1": "o200k_base",  # o1 reasoning models
        "o3": "o200k_base",  # o3 reasoning models
        "o4": "o200k_base",  # o4 reasoning models
        "claude": "cl100k_base",  # All Claude models
        "gemini": "cl100k_base",  # All Gemini models
    }

    DEFAULT_ENCODING: str = "cl100k_base"

    def __init__(self, model_name: Optional[str] = None) -> None:
        """
        Initialize the token counter.

        Args:
            model_name: Optional model name for encoding selection.
                       If not provided, uses DEFAULT_ENCODING.
        """
        self.model_name = model_name
        self._encoding: Optional[object] = None
        self._encoding_name: Optional[str] = None

    def _get_encoding(self) -> tuple[object, str]:
        """
        Get tiktoken encoding for the model.

        Returns:
            Tuple of (encoding object, encoding name string)

        Note:
            Uses lazy initialization and caches the encoding for reuse.
            Falls back to cl100k_base if model encoding is not available.
        """
        if self._encoding is not None and self._encoding_name is not None:
            return self._encoding, self._encoding_name

        try:
            import tiktoken
        except ImportError as e:
            raise ImportError(
                "tiktoken is required for token counting. "
                "Install it with: pip install tiktoken"
            ) from e

        encoding_name = self.DEFAULT_ENCODING

        if self.model_name:
            model_lower = self.model_name.lower()

            # Try exact match first from MODEL_ENCODINGS
            if self.model_name in self.MODEL_ENCODINGS:
                encoding_name = self.MODEL_ENCODINGS[self.model_name]
            elif model_lower in self.MODEL_ENCODINGS:
                encoding_name = self.MODEL_ENCODINGS[model_lower]
            else:
                # Try pattern-based detection
                for pattern, enc_name in self.PROVIDER_ENCODINGS.items():
                    if pattern in model_lower:
                        encoding_name = enc_name
                        break

                # Try tiktoken's built-in model lookup as last resort
                if encoding_name == self.DEFAULT_ENCODING:
                    try:
                        self._encoding = tiktoken.encoding_for_model(self.model_name)
                        self._encoding_name = self._encoding.name
                        return self._encoding, self._encoding_name
                    except KeyError:
                        pass  # Model not found, use default encoding

        self._encoding = tiktoken.get_encoding(encoding_name)
        self._encoding_name = encoding_name
        return self._encoding, self._encoding_name

    def count_tokens(self, text: str) -> TokenCount:
        """
        Count tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            TokenCount with count, encoding name, and model name

        Example:
            ```python
            counter = TokenCounter(model_name="gpt-5-mini")
            result = counter.count_tokens("Hello, world!")
            print(f"Token count: {result.count}")
            ```
        """
        if not text:
            return TokenCount(
                count=0, encoding_name=self.DEFAULT_ENCODING, model_name=self.model_name
            )

        encoding, encoding_name = self._get_encoding()
        tokens = encoding.encode(text)
        return TokenCount(count=len(tokens), encoding_name=encoding_name, model_name=self.model_name)

    def count_messages(self, messages: list[dict[str, str]]) -> TokenCount:
        """
        Count tokens in a list of chat messages.

        This method counts tokens for each message including role and content,
        and adds per-message overhead to approximate the actual token usage
        in chat completions.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            TokenCount with total count across all messages

        Example:
            ```python
            counter = TokenCounter(model_name="gpt-5-mini")
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
            result = counter.count_messages(messages)
            print(f"Total tokens: {result.count}")
            ```

        Note:
            The per-message overhead (4 tokens) is an approximation based on
            OpenAI's chat format. Actual overhead may vary by provider.
        """
        if not messages:
            return TokenCount(
                count=0, encoding_name=self.DEFAULT_ENCODING, model_name=self.model_name
            )

        total = 0
        encoding, encoding_name = self._get_encoding()

        for message in messages:
            # Count role and content
            role = message.get("role", "")
            content = message.get("content", "")

            if role:
                total += len(encoding.encode(role))
            if content:
                total += len(encoding.encode(content))

            # Add overhead per message (approximation for chat format)
            # This accounts for special tokens like <|im_start|>, <|im_sep|>, etc.
            total += 4

        return TokenCount(count=total, encoding_name=encoding_name, model_name=self.model_name)
