"""
Session Title Generator Service

Provides automatic session title generation using LLM with fallback to simple extraction.
All operations are async and non-blocking to avoid impacting the main conversation flow.

Key Features:
- LLM-based title generation from first conversation exchange
- Fallback to simple word extraction when LLM fails
- Title sanitization with length limits and character filtering
- Configurable via environment variables

Environment Variables:
- AUTO_GENERATE_SESSION_TITLES: Enable/disable auto-generation (default: "true")
- SESSION_TITLE_MODEL: LLM model for generation (default: "gpt-5-nano")
- SESSION_TITLE_MAX_TOKENS: Max tokens for title (default: 20)
- SESSION_TITLE_TEMPERATURE: LLM temperature (default: 0.3)
"""

import logging
import os
import re

from ..core.model_clients import OPENAI_AVAILABLE, ModelClientFactory
from ..session.session_storage import SessionStorageInterface


logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_AUTO_GENERATE = True
DEFAULT_MODEL = "gpt-4o-mini"  # More reliable than gpt-5-mini for this task
DEFAULT_MAX_TOKENS = 30  # Increased for better title generation
DEFAULT_TEMPERATURE = 0.3
DEFAULT_LABEL = "Nouvelle session"
MAX_TITLE_LENGTH = 100

# Characters to remove from titles (could cause display issues)
UNSAFE_CHARS_PATTERN = re.compile(r"[<>{}[\]\\]")

# Title generation prompt template
TITLE_GENERATION_PROMPT = """Génère un titre court et descriptif (3-6 mots maximum) pour une conversation qui commence ainsi :

Utilisateur: {user_message}
Assistant: {agent_response}

RÈGLES STRICTES pour le titre :
- Doit être un TITRE NOMINAL (pas une question, pas une phrase complète)
- Doit capturer le SUJET PRINCIPAL, pas reprendre les premiers mots de la question
- Format: "Nom du sujet" ou "Action + Objet" (ex: "Génération de graphiques", "Analyse de données")
- 3-6 mots maximum
- Pas de guillemets, pas de ponctuation finale
- Commence par une majuscule

EXEMPLES CORRECTS :
- "Génération de graphiques Mermaid"
- "Analyse de performances"
- "Configuration Docker"

EXEMPLES INCORRECTS (à éviter) :
- "Peux générer random graph" ❌ (reprend la question)
- "Comment faire un graphique ?" ❌ (question)
- "Je veux créer un graph" ❌ (phrase complète)

Titre:"""


class SessionTitleGenerator:
    """
    Service for generating and managing session titles.

    Provides LLM-based title generation with fallback to simple extraction.
    All operations are async and non-blocking.
    """

    def __init__(
        self,
        model_name: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        auto_generate_enabled: bool | None = None,
    ):
        """
        Initialize the session title generator.

        Args:
            model_name: LLM model to use for generation. Defaults to env var or gpt-5-nano.
            max_tokens: Maximum tokens for generated title. Defaults to env var or 20.
            temperature: LLM temperature. Defaults to env var or 0.3.
            auto_generate_enabled: Whether auto-generation is enabled. Defaults to env var or True.
        """
        # Load configuration from environment with fallbacks
        self.model_name = model_name or os.getenv("SESSION_TITLE_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens or int(
            os.getenv("SESSION_TITLE_MAX_TOKENS", DEFAULT_MAX_TOKENS)
        )
        self.temperature = temperature or float(
            os.getenv("SESSION_TITLE_TEMPERATURE", DEFAULT_TEMPERATURE)
        )

        # Parse auto-generate setting
        if auto_generate_enabled is not None:
            self.auto_generate_enabled = auto_generate_enabled
        else:
            env_value = os.getenv("AUTO_GENERATE_SESSION_TITLES", "true").lower()
            self.auto_generate_enabled = env_value not in ("false", "0", "no", "off")

        self._client_factory = ModelClientFactory()

        logger.debug(
            f"[SessionTitleGenerator] Initialized with model={self.model_name}, "
            f"max_tokens={self.max_tokens}, temperature={self.temperature}, "
            f"auto_generate={self.auto_generate_enabled}"
        )

    def sanitize_title(self, raw_title: str) -> str:
        """
        Clean and validate a generated title.

        Applies the following sanitization rules:
        - Limit length to MAX_TITLE_LENGTH characters
        - Remove unsafe characters (<>{}[]\\)
        - Strip surrounding quotes
        - Remove trailing punctuation
        - Capitalize first letter
        - Return DEFAULT_LABEL if result is empty

        Args:
            raw_title: The raw title string to sanitize.

        Returns:
            Sanitized title string, or DEFAULT_LABEL if empty after cleaning.
        """
        if not raw_title:
            return DEFAULT_LABEL

        title = raw_title.strip()

        # Remove unsafe characters
        title = UNSAFE_CHARS_PATTERN.sub("", title)

        # Strip surrounding quotes (single and double)
        if len(title) >= 2:
            if (title[0] == '"' and title[-1] == '"') or (title[0] == "'" and title[-1] == "'"):
                title = title[1:-1].strip()

        # Remove trailing punctuation
        title = title.rstrip(".,!?;:")

        # Truncate to max length
        if len(title) > MAX_TITLE_LENGTH:
            title = title[:MAX_TITLE_LENGTH].rstrip()

        # Capitalize first letter (if non-empty)
        if title:
            title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()

        # Return default if empty after cleaning
        if not title or not title.strip():
            return DEFAULT_LABEL

        return title.strip()

    def extract_simple_title(self, user_message: str) -> str:
        """
        Extract a simple title from the first significant words of a message.

        This is the fallback method when LLM-based generation fails.
        Extracts the first 3-4 significant words from the user message,
        removing common question words and filler phrases.

        Args:
            user_message: The user's message to extract title from.

        Returns:
            Extracted title string, or DEFAULT_LABEL if extraction fails.
        """
        if not user_message:
            return DEFAULT_LABEL

        # Clean the message
        text = user_message.strip()

        # Remove common greeting prefixes
        greetings = ["bonjour", "salut", "hello", "hi", "hey", "bonsoir"]
        text_lower = text.lower()
        for greeting in greetings:
            if text_lower.startswith(greeting):
                # Remove greeting and any following punctuation/whitespace
                text = text[len(greeting) :].lstrip(" ,!.?:")
                break

        # Remove common question words and filler phrases at the start
        question_starters = [
            "peux tu me",
            "peux tu",
            "peux-tu m'",
            "peux-tu me",
            "peux-tu",
            "pourrais tu me",
            "pourrais tu",
            "pourrais-tu m'",
            "pourrais-tu me",
            "pourrais-tu",
            "est-ce que tu peux me",
            "est-ce que tu peux",
            "est-ce que",
            "comment faire",
            "comment",
            "pourquoi",
            "quand",
            "où",
            "qui",
            "quoi",
            "quel",
            "quelle",
            "can you",
            "could you",
            "would you",
            "please",
            "stp",
            "s'il te plaît",
            "s'il vous plaît",
            "svp",
        ]

        text_lower = text.lower()
        for starter in question_starters:
            if text_lower.startswith(starter):
                # Remove the question starter
                text = text[len(starter) :].lstrip(" ,!.?:")
                text_lower = text.lower()
                break  # Only remove one starter

        # Remove common verb prefixes that might remain
        verb_prefixes = ["aider à", "aider", "faire", "créer", "générer"]
        for prefix in verb_prefixes:
            if text_lower.startswith(prefix):
                text = text[len(prefix) :].lstrip(" ,!.?:àà")
                text_lower = text.lower()
                break

        # Remove question marks and exclamation points
        text = text.rstrip("?!.")

        # Split into words and filter
        words = text.split()

        # Filter out very short words (articles, etc.) and common verbs
        skip_words = {
            "me",
            "m",
            "te",
            "t",
            "le",
            "la",
            "les",
            "l",
            "un",
            "une",
            "des",
            "de",
            "du",
            "d",
            "a",
            "à",
            "au",
            "aux",
            "ce",
            "cet",
            "cette",
            "ces",
        }
        significant_words = []

        for word in words:
            # Clean word of punctuation
            clean_word = re.sub(r"[^\w\s'-]", "", word)
            if clean_word and clean_word.lower() not in skip_words:
                significant_words.append(clean_word)
            if len(significant_words) >= 5:
                break

        if not significant_words:
            return DEFAULT_LABEL

        # Join and sanitize
        title = " ".join(significant_words)
        return self.sanitize_title(title)

    async def generate_session_title(
        self,
        user_message: str,
        agent_response: str,
        model_name: str | None = None,
    ) -> str:
        """
        Generate a descriptive session title using LLM.

        Uses the configured LLM to generate a short, descriptive title based on
        the first user message and agent response. Falls back to simple extraction
        if LLM call fails.

        Args:
            user_message: The user's first message in the session.
            agent_response: The agent's response to the first message.
            model_name: Optional override for the LLM model to use.

        Returns:
            Generated title string, or fallback title if generation fails.
        """
        effective_model = model_name or self.model_name

        # Check if OpenAI is available (primary provider for title generation)
        if not OPENAI_AVAILABLE:
            logger.warning(
                "[SessionTitleGenerator] OpenAI client not available, using simple extraction"
            )
            return self.extract_simple_title(user_message)

        try:
            # Build the prompt
            prompt = TITLE_GENERATION_PROMPT.format(
                user_message=user_message[:500],  # Limit input length
                agent_response=agent_response[:500],
            )

            # Create client and generate
            client = self._client_factory.create_client(
                model_name=effective_model or self.model_name
            )

            # Use max_completion_tokens for newer models (gpt-5-*), max_tokens for older ones
            completion_params = {
                "model": effective_model,
                "messages": [{"role": "user", "content": prompt}],
            }

            # gpt-5-* models use max_completion_tokens and only support temperature=1
            if effective_model.startswith("gpt-5"):
                completion_params["max_completion_tokens"] = self.max_tokens
                # gpt-5-mini only supports temperature=1 (default)
            else:
                completion_params["max_tokens"] = self.max_tokens
                completion_params["temperature"] = self.temperature

            response = await client.chat.completions.create(**completion_params)

            # Extract and sanitize the title
            raw_title = response.choices[0].message.content
            logger.debug(f"[SessionTitleGenerator] Raw LLM response: '{raw_title}'")
            title = self.sanitize_title(raw_title)

            logger.info(f"[SessionTitleGenerator] Generated title: '{title}'")
            return title

        except Exception as e:
            logger.warning(
                f"[SessionTitleGenerator] LLM title generation failed: {e}, "
                f"falling back to simple extraction"
            )
            return self.extract_simple_title(user_message)

    async def auto_generate_if_needed(
        self,
        session_storage: SessionStorageInterface,
        user_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
    ) -> str | None:
        """
        Generate and update session title if conditions are met.

        Conditions for auto-generation:
        - Auto-generation is enabled
        - Session label equals DEFAULT_LABEL ("Nouvelle session")
        - This is the first user message (exactly one user_input in history)
        
        Note: We only check for 1 user message, not agent responses, because
        sessions may have a welcome message from the agent before the user's
        first message.

        Args:
            session_storage: Storage interface for session operations.
            user_id: User identifier.
            session_id: Session identifier.
            user_message: The user's message text.
            agent_response: The agent's response text.

        Returns:
            Generated title if conditions met and generation successful, None otherwise.
        """
        # Check if auto-generation is enabled
        if not self.auto_generate_enabled:
            logger.debug("[SessionTitleGenerator] Auto-generation disabled")
            return None

        try:
            # Load session to check current label
            session = await session_storage.load_session(user_id, session_id)
            if not session:
                logger.warning(
                    f"[SessionTitleGenerator] Session {session_id} not found for user {user_id}"
                )
                return None

            # Check if label has been manually edited
            if session.session_label != DEFAULT_LABEL:
                logger.debug(
                    f"[SessionTitleGenerator] Session {session_id} has custom label, skipping"
                )
                return None

            # Check conversation history to verify this is the first user message
            history = await session_storage.get_conversation_history(session_id)

            # Count user messages only (ignore agent responses as there may be a welcome message)
            user_messages = [m for m in history if m.message_type == "user_input"]

            # Only generate on first user message
            if len(user_messages) != 1:
                logger.debug(
                    f"[SessionTitleGenerator] Session {session_id} has "
                    f"{len(user_messages)} user messages, skipping (not first user message)"
                )
                return None

            # Generate title
            title = await self.generate_session_title(user_message, agent_response)

            # Update session label
            success = await session_storage.update_session_label(user_id, session_id, title)

            if success:
                logger.info(
                    f"[SessionTitleGenerator] Updated session {session_id} title to: '{title}'"
                )
                return title
            else:
                logger.warning(
                    f"[SessionTitleGenerator] Failed to update session {session_id} label"
                )
                return None

        except Exception as e:
            # Log error but don't propagate - title generation should never break main flow
            logger.error(
                f"[SessionTitleGenerator] Error during auto-generation for session {session_id}: {e}"
            )
            return None


# Global instance for convenience
_title_generator: SessionTitleGenerator | None = None


def get_title_generator() -> SessionTitleGenerator:
    """
    Get or create the global SessionTitleGenerator instance.

    Returns:
        SessionTitleGenerator instance configured from environment.
    """
    global _title_generator
    if _title_generator is None:
        _title_generator = SessionTitleGenerator()
    return _title_generator
