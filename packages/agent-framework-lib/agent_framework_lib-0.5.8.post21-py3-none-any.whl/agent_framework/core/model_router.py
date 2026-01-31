"""
Multi-Model Router with Automatic Complexity-Based Selection

This module provides intelligent model routing based on query complexity.
It supports manual model selection or automatic routing via a classifier.

Key Features:
- Tier-based model organization (LIGHT, STANDARD, ADVANCED)
- Automatic complexity classification for "auto" mode
- Fallback chain when preferred models are unavailable
- Trivial message detection to skip classification
- Environment variable configuration for tier preferences

Environment Variables:
- PREFERRED_LIGHT_MODELS: Comma-separated list of light tier models
- PREFERRED_STANDARD_MODELS: Comma-separated list of standard tier models
- PREFERRED_ADVANCED_MODELS: Comma-separated list of advanced tier models
- AUTO_CLASSIFIER_MODEL: Model used for complexity classification
- DEFAULT_MODEL_MODE: Default mode when no preference ("auto" or model name)
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Maximum characters per message when formatting context for classification
MAX_MESSAGE_LENGTH_FOR_CLASSIFICATION: int = 500

# Maximum number of messages to include in classification context
MAX_CONTEXT_MESSAGES: int = 10

# Classification prompt template
CLASSIFICATION_PROMPT: str = """Analyze the complexity of the following user query and conversation context.

Respond with exactly ONE word: LIGHT, STANDARD, or ADVANCED.

Classification criteria:
- LIGHT: Simple questions, greetings, basic information requests, short factual answers
- STANDARD: Moderate complexity, explanations, comparisons, typical coding questions
- ADVANCED: Complex analysis, multi-step reasoning, creative writing, advanced coding, research tasks

Conversation context:
{context}

Current query: {query}

Complexity classification (respond with ONE word only):"""

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """
    Model capability tiers for routing decisions.

    Attributes:
        LIGHT: Fast, cost-effective models for simple queries
        STANDARD: Balanced models for typical queries
        ADVANCED: Most capable models for complex queries
    """

    LIGHT = "light"
    STANDARD = "standard"
    ADVANCED = "advanced"


class NoModelAvailableError(Exception):
    """
    Raised when no model is available in any tier.

    This exception indicates that the routing system could not find
    any available model across all tiers (ADVANCED → STANDARD → LIGHT).
    """

    pass


@dataclass
class RoutingResult:
    """
    Result of a model routing decision.

    Attributes:
        model: The selected model identifier (e.g., "gpt-4o-mini")
        tier: The tier of the selected model
        reason: Human-readable explanation of the routing decision
        fallback_used: True if the original tier had no available model
        classification_skipped: True for trivial messages or direct selection
    """

    model: str
    tier: ModelTier
    reason: str
    fallback_used: bool = False
    classification_skipped: bool = False


# Patterns for trivial messages that skip classification
SKIP_CLASSIFICATION_PATTERNS: list[str] = [
    r"^(hi|hello|hey|bonjour|salut|coucou)[\s!.,?]*$",
    r"^(thanks|thank you|merci|thx)[\s!.,?]*$",
    r"^(ok|okay|yes|no|oui|non|d'accord)[\s!.,?]*$",
    r"^(bye|goodbye|au revoir|ciao)[\s!.,?]*$",
    r"^(sure|got it|understood|compris)[\s!.,?]*$",
]


class ModelRouter:
    """
    Routes requests to appropriate models based on complexity or user preference.

    The router supports two modes:
    1. Direct selection: User specifies a model, router validates and uses it
    2. Auto mode: Router classifies query complexity and selects appropriate tier

    Configuration is loaded from environment variables with sensible defaults.
    """

    # Default tier preferences (used when env vars not set)
    DEFAULT_LIGHT_MODELS: list[str] = [
        "gpt-5-nano",
        "gemini-2.5-flash-lite",
    ]
    DEFAULT_STANDARD_MODELS: list[str] = [
        "gpt-5-mini",
        "claude-haiku-4-5-20251001",
        "gemini-2.5-flash",
    ]
    DEFAULT_ADVANCED_MODELS: list[str] = [
        "gpt-5",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "gemini-2.5-pro",
        "gemini-3-pro-preview",
    ]

    def __init__(self) -> None:
        """
        Initialize the ModelRouter with configuration from environment variables.
        """
        self.light_models: list[str] = []
        self.standard_models: list[str] = []
        self.advanced_models: list[str] = []
        self.classifier_model: str = ""
        self.default_mode: str = ""

        self._load_configuration()

    def _load_configuration(self) -> None:
        """
        Load configuration from environment variables.

        Reads tier preferences, classifier model, and default mode.
        Falls back to defaults when environment variables are not set.
        """
        # Load tier preferences
        light_str = os.getenv("PREFERRED_LIGHT_MODELS", "")
        standard_str = os.getenv("PREFERRED_STANDARD_MODELS", "")
        advanced_str = os.getenv("PREFERRED_ADVANCED_MODELS", "")

        self.light_models = (
            self._parse_model_list(light_str) if light_str else self.DEFAULT_LIGHT_MODELS.copy()
        )
        self.standard_models = (
            self._parse_model_list(standard_str)
            if standard_str
            else self.DEFAULT_STANDARD_MODELS.copy()
        )
        self.advanced_models = (
            self._parse_model_list(advanced_str)
            if advanced_str
            else self.DEFAULT_ADVANCED_MODELS.copy()
        )

        # Load classifier and default mode
        self.classifier_model = os.getenv("AUTO_CLASSIFIER_MODEL", "gpt-4o-mini")
        self.default_mode = os.getenv("DEFAULT_MODEL_MODE", "auto")

        logger.info("[ModelRouter] Configuration loaded:")
        logger.info(f"  - Light models: {self.light_models}")
        logger.info(f"  - Standard models: {self.standard_models}")
        logger.info(f"  - Advanced models: {self.advanced_models}")
        logger.info(f"  - Classifier model: {self.classifier_model}")
        logger.info(f"  - Default mode: {self.default_mode}")

    def _parse_model_list(self, model_string: str) -> list[str]:
        """
        Parse a comma-separated string of model names.

        Args:
            model_string: Comma-separated model names (e.g., "gpt-4o,claude-3")

        Returns:
            List of trimmed, non-empty model names in order
        """
        if not model_string:
            return []
        return [m.strip() for m in model_string.split(",") if m.strip()]

    def _should_skip_classification(self, query: str) -> bool:
        """
        Determine if a query is trivial and should skip classification.

        Trivial messages include greetings, thanks, confirmations, and
        other short messages that don't require complex processing.

        Args:
            query: The user's query text

        Returns:
            True if classification should be skipped, False otherwise
        """
        if not query:
            return True

        # Skip if query is very short (under 15 characters)
        if len(query.strip()) < 15:
            query_lower = query.strip().lower()
            for pattern in SKIP_CLASSIFICATION_PATTERNS:
                if re.match(pattern, query_lower, re.IGNORECASE):
                    logger.debug(f"[ModelRouter] Trivial message detected: '{query}'")
                    return True

        return False

    def _get_models_for_tier(self, tier: ModelTier) -> list[str]:
        """
        Get the list of preferred models for a given tier.

        Args:
            tier: The model tier

        Returns:
            List of model names for the tier
        """
        if tier == ModelTier.LIGHT:
            return self.light_models
        elif tier == ModelTier.STANDARD:
            return self.standard_models
        elif tier == ModelTier.ADVANCED:
            return self.advanced_models
        return []

    def _infer_tier_for_model(self, model_name: str) -> ModelTier:
        """
        Get the tier for a model from the configured tier lists.

        Args:
            model_name: The model identifier

        Returns:
            ModelTier if found in tier lists, STANDARD as fallback for unknown models
        """
        if model_name in self.light_models:
            return ModelTier.LIGHT
        if model_name in self.standard_models:
            return ModelTier.STANDARD
        if model_name in self.advanced_models:
            return ModelTier.ADVANCED

        # Unknown model - default to STANDARD
        logger.warning(f"[ModelRouter] Model '{model_name}' not in any tier list, defaulting to STANDARD")
        return ModelTier.STANDARD

    def _is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available (has a valid API key configured).

        Args:
            model_name: The model identifier

        Returns:
            True if the model's provider has an API key configured, False otherwise
        """
        from agent_framework.core.model_config import model_config

        provider = model_config.get_provider_for_model(model_name)
        api_key = model_config.get_api_key_for_provider(provider)
        return bool(api_key)

    def _select_model_from_tier(self, tier: ModelTier) -> str | None:
        """
        Select the first available model from a tier.

        Iterates through the preferred models for the given tier and returns
        the first one that has a valid API key configured.

        Args:
            tier: The model tier to select from

        Returns:
            The first available model name, or None if no model is available
        """
        models = self._get_models_for_tier(tier)

        for model in models:
            if self._is_model_available(model):
                logger.debug(f"[ModelRouter] Selected model '{model}' from {tier.value} tier")
                return model

        logger.debug(f"[ModelRouter] No available model found in {tier.value} tier")
        return None

    def _select_with_fallback(self, tier: ModelTier) -> tuple[str, ModelTier, bool]:
        """
        Select a model from the given tier, falling back to lower tiers if needed.

        Implements the fallback chain: ADVANCED → STANDARD → LIGHT.
        If no model is available in any tier, raises NoModelAvailableError.

        Args:
            tier: The initial tier to try

        Returns:
            Tuple of (model_name, actual_tier, fallback_used)

        Raises:
            NoModelAvailableError: If no model is available in any tier
        """
        # Define fallback order based on starting tier
        if tier == ModelTier.ADVANCED:
            fallback_chain = [ModelTier.ADVANCED, ModelTier.STANDARD, ModelTier.LIGHT]
        elif tier == ModelTier.STANDARD:
            fallback_chain = [ModelTier.STANDARD, ModelTier.LIGHT]
        else:  # LIGHT
            fallback_chain = [ModelTier.LIGHT]

        original_tier = tier

        for current_tier in fallback_chain:
            model = self._select_model_from_tier(current_tier)
            if model:
                fallback_used = current_tier != original_tier
                if fallback_used:
                    logger.info(
                        f"[ModelRouter] Fallback from {original_tier.value} to "
                        f"{current_tier.value} tier, selected model: {model}"
                    )
                return (model, current_tier, fallback_used)

        # No model available in any tier
        logger.error("[ModelRouter] No model available in any tier")
        raise NoModelAvailableError(
            "No model available in any tier. Please configure at least one API key "
            "(OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY)."
        )

    def _format_context_for_classification(self, context: list[dict[str, Any]]) -> str:
        """
        Format conversation context for the classification prompt.

        Truncates messages longer than MAX_MESSAGE_LENGTH_FOR_CLASSIFICATION characters
        and limits to the last MAX_CONTEXT_MESSAGES messages.

        Args:
            context: List of message dictionaries with 'role' and 'content' keys

        Returns:
            Formatted string representation of the context
        """
        if not context:
            return "(No previous context)"

        # Take only the last N messages
        recent_context = context[-MAX_CONTEXT_MESSAGES:]

        formatted_messages: list[str] = []
        for msg in recent_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Truncate long messages
            if len(content) > MAX_MESSAGE_LENGTH_FOR_CLASSIFICATION:
                content = content[:MAX_MESSAGE_LENGTH_FOR_CLASSIFICATION] + "..."

            formatted_messages.append(f"{role}: {content}")

        return "\n".join(formatted_messages)

    async def _classify_complexity(
        self, query: str, context: list[dict[str, Any]]
    ) -> ModelTier:
        """
        Classify the complexity of a query using the classifier model.

        Uses an LLM to analyze the query and conversation context to determine
        the appropriate tier (LIGHT, STANDARD, or ADVANCED).

        Args:
            query: The user's current query
            context: List of previous messages in the conversation

        Returns:
            ModelTier indicating the classified complexity level.
            Defaults to STANDARD if classification fails or is ambiguous.
        """
        try:
            # Format the context for the prompt
            formatted_context = self._format_context_for_classification(context)

            # Build the classification prompt
            prompt = CLASSIFICATION_PROMPT.format(context=formatted_context, query=query)

            # Get the classifier model's provider and API key
            from agent_framework.core.model_config import model_config

            provider = model_config.get_provider_for_model(self.classifier_model)
            api_key = model_config.get_api_key_for_provider(provider)

            if not api_key:
                logger.warning(
                    f"[ModelRouter] No API key for classifier model {self.classifier_model}, "
                    "defaulting to STANDARD"
                )
                return ModelTier.STANDARD

            # Call the appropriate provider
            response_text = await self._call_classifier(provider, api_key, prompt)

            # Parse the response
            return self._parse_classification_response(response_text)

        except Exception as e:
            logger.warning(
                f"[ModelRouter] Classification failed with error: {e}, defaulting to STANDARD"
            )
            return ModelTier.STANDARD

    async def _call_classifier(self, provider: Any, api_key: str, prompt: str) -> str:
        """
        Call the classifier model to get a complexity classification.

        Args:
            provider: The ModelProvider enum value
            api_key: The API key for the provider
            prompt: The classification prompt

        Returns:
            The raw response text from the classifier
        """
        from agent_framework.core.model_config import ModelProvider

        if provider == ModelProvider.OPENAI:
            return await self._call_openai_classifier(api_key, prompt)
        elif provider == ModelProvider.ANTHROPIC:
            return await self._call_anthropic_classifier(api_key, prompt)
        elif provider == ModelProvider.GEMINI:
            return await self._call_gemini_classifier(api_key, prompt)
        else:
            # Default to OpenAI-style call
            return await self._call_openai_classifier(api_key, prompt)

    async def _call_openai_classifier(self, api_key: str, prompt: str) -> str:
        """Call OpenAI API for classification."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=self.classifier_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            logger.error("[ModelRouter] OpenAI client not available for classification")
            raise
        except Exception as e:
            logger.error(f"[ModelRouter] OpenAI classification call failed: {e}")
            raise

    async def _call_anthropic_classifier(self, api_key: str, prompt: str) -> str:
        """Call Anthropic API for classification."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model=self.classifier_model,
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}],
            )
            # Extract text from content blocks
            if response.content and len(response.content) > 0:
                first_block = response.content[0]
                # Check if it's a TextBlock with text attribute
                if hasattr(first_block, "text"):
                    return str(first_block.text) or ""
            return ""
        except ImportError:
            logger.error("[ModelRouter] Anthropic client not available for classification")
            raise
        except Exception as e:
            logger.error(f"[ModelRouter] Anthropic classification call failed: {e}")
            raise

    async def _call_gemini_classifier(self, api_key: str, prompt: str) -> str:
        """Call Google Gemini API for classification."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.classifier_model)
            response = await model.generate_content_async(
                prompt,
                generation_config={"max_output_tokens": 10, "temperature": 0.0},
            )
            return response.text or ""
        except ImportError:
            logger.error("[ModelRouter] Gemini client not available for classification")
            raise
        except Exception as e:
            logger.error(f"[ModelRouter] Gemini classification call failed: {e}")
            raise

    def _parse_classification_response(self, response: str | None) -> ModelTier:
        """
        Parse the classifier response to extract the tier.

        Args:
            response: Raw response text from the classifier

        Returns:
            ModelTier based on the response. Defaults to STANDARD if ambiguous.
        """
        if not response:
            logger.debug("[ModelRouter] Empty classifier response, defaulting to STANDARD")
            return ModelTier.STANDARD

        response_upper = response.strip().upper()

        # Check for exact matches first
        if "LIGHT" in response_upper:
            logger.debug(f"[ModelRouter] Classified as LIGHT from response: '{response}'")
            return ModelTier.LIGHT
        elif "ADVANCED" in response_upper:
            logger.debug(f"[ModelRouter] Classified as ADVANCED from response: '{response}'")
            return ModelTier.ADVANCED
        else:
            # Default to STANDARD for any other response (including "STANDARD")
            logger.debug(
                f"[ModelRouter] Classified as STANDARD from response: '{response}' "
                "(default for ambiguous responses)"
            )
            return ModelTier.STANDARD

    async def route(
        self,
        query: str,
        context: list[dict[str, Any]] | None = None,
        model_preference: str = "auto",
    ) -> RoutingResult:
        """
        Route a query to the appropriate model based on preference or complexity.

        This is the main entry point for model routing. It supports two modes:
        1. Direct selection: When model_preference is not "auto", validates and uses
           that specific model directly without classification.
        2. Auto mode: When model_preference is "auto", classifies the query complexity
           and routes to the appropriate tier.

        For trivial messages (greetings, thanks, etc.), classification is skipped
        and the query is routed directly to the LIGHT tier.

        Args:
            query: The user's query text
            context: Optional list of previous messages in the conversation
            model_preference: Either "auto" for automatic routing or a specific model name

        Returns:
            RoutingResult containing the selected model, tier, reason, and metadata

        Raises:
            NoModelAvailableError: If no model is available in any tier
        """
        if context is None:
            context = []

        # Direct model selection (not "auto")
        if model_preference.lower() != "auto":
            return self._handle_direct_selection(model_preference)

        # Auto mode: check for trivial messages first
        if self._should_skip_classification(query):
            return self._handle_trivial_message(query)

        # Auto mode: classify complexity and route
        return await self._handle_auto_routing(query, context)

    def _handle_direct_selection(self, model_preference: str) -> RoutingResult:
        """
        Handle direct model selection (non-auto mode).

        Validates the model is available and returns it directly without classification.

        Args:
            model_preference: The specific model name requested

        Returns:
            RoutingResult with the requested model

        Raises:
            NoModelAvailableError: If the requested model is not available
        """
        logger.info(f"[ModelRouter] Direct model selection: {model_preference}")

        # Check if the model is available
        if not self._is_model_available(model_preference):
            logger.warning(
                f"[ModelRouter] Requested model '{model_preference}' is not available, "
                "falling back to auto mode"
            )
            # Fall back to auto mode with STANDARD tier
            model, actual_tier, fallback_used = self._select_with_fallback(ModelTier.STANDARD)
            return RoutingResult(
                model=model,
                tier=actual_tier,
                reason=f"Fallback from unavailable model '{model_preference}'",
                fallback_used=True,
                classification_skipped=True,
            )

        # Infer the tier for the selected model
        tier = self._infer_tier_for_model(model_preference)

        return RoutingResult(
            model=model_preference,
            tier=tier,
            reason="Direct selection",
            fallback_used=False,
            classification_skipped=True,
        )

    def _handle_trivial_message(self, query: str) -> RoutingResult:
        """
        Handle trivial messages by routing directly to LIGHT tier.

        Skips classification for greetings, thanks, confirmations, etc.

        Args:
            query: The trivial message

        Returns:
            RoutingResult with a LIGHT tier model
        """
        logger.info(f"[ModelRouter] Trivial message detected, skipping classification: '{query}'")

        model, actual_tier, fallback_used = self._select_with_fallback(ModelTier.LIGHT)

        return RoutingResult(
            model=model,
            tier=actual_tier,
            reason="Trivial message - skipped classification",
            fallback_used=fallback_used,
            classification_skipped=True,
        )

    async def _handle_auto_routing(
        self, query: str, context: list[dict[str, Any]]
    ) -> RoutingResult:
        """
        Handle auto mode routing with complexity classification.

        Classifies the query complexity and routes to the appropriate tier.

        Args:
            query: The user's query
            context: Previous messages in the conversation

        Returns:
            RoutingResult with the selected model based on classification
        """
        # Classify the query complexity
        classified_tier = await self._classify_complexity(query, context)
        logger.info(f"[ModelRouter] Query classified as {classified_tier.value}")

        # Select model from the classified tier (with fallback)
        model, actual_tier, fallback_used = self._select_with_fallback(classified_tier)

        reason = f"Classified as {classified_tier.value}"
        if fallback_used:
            reason += f" (fallback to {actual_tier.value})"

        return RoutingResult(
            model=model,
            tier=actual_tier,
            reason=reason,
            fallback_used=fallback_used,
            classification_skipped=False,
        )

    def get_available_models(self) -> dict[str, list[dict[str, Any]]]:
        """
        Get all models grouped by tier with availability status.

        Returns a dictionary with tier names as keys and lists of model info as values.
        Each model info includes the model id, provider, and availability status.

        Returns:
            Dictionary mapping tier names to lists of model information:
            {
                "light": [{"id": "gpt-4o-mini", "provider": "openai", "available": True}, ...],
                "standard": [...],
                "advanced": [...]
            }
        """
        from agent_framework.core.model_config import model_config

        result: dict[str, list[dict[str, Any]]] = {
            "light": [],
            "standard": [],
            "advanced": [],
        }

        # Process each tier
        tier_models = {
            "light": self.light_models,
            "standard": self.standard_models,
            "advanced": self.advanced_models,
        }

        for tier_name, models in tier_models.items():
            for model_name in models:
                provider = model_config.get_provider_for_model(model_name)
                available = self._is_model_available(model_name)

                result[tier_name].append(
                    {
                        "id": model_name,
                        "provider": provider.value,
                        "available": available,
                    }
                )

        logger.debug(f"[ModelRouter] Available models by tier: {result}")
        return result


# Global instance
model_router = ModelRouter()
