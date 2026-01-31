# Spec: Cross-Model History Conversion

## Problème

Quand un utilisateur change de modèle LLM en cours de session (ex: OpenAI → Gemini, Claude → Gemini), l'historique de conversation contient des formats de messages incompatibles.

### Erreur observée

```
ValueError: Unsupported content block type: ToolCallBlock
```

L'erreur se produit dans `llama_index/llms/gemini/utils.py` car Gemini ne comprend pas les `ToolCallBlock` générés par OpenAI/Claude.

### État actuel du framework

Le fichier `llamaindex_memory_adapter.py` contient une méthode `_sanitize_chat_messages()` qui :
- Supprime les `tool_calls` vides (OpenAI les rejette)
- Ne convertit PAS entre les formats de différents providers

**Ce qui manque** : Conversion complète des tool calls entre providers.

## Matrice des conversions nécessaires

| Source | Target | Statut | Complexité |
|--------|--------|--------|------------|
| OpenAI → Claude | ❓ À vérifier | Faible (formats similaires) |
| OpenAI → Gemini | ❌ Non implémenté | Moyenne |
| Claude → OpenAI | ❓ À vérifier | Faible |
| Claude → Gemini | ❌ Non implémenté | Moyenne |
| Gemini → OpenAI | ❌ Non implémenté | Moyenne |
| Gemini → Claude | ❌ Non implémenté | Moyenne |

## Formats des Tool Calls par Provider

### OpenAI Format (LlamaIndex)

```python
# Dans ChatMessage.additional_kwargs
{
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "search_database",
                "arguments": '{"query": "tickets"}'
            }
        }
    ]
}

# Tool Result (role="tool")
ChatMessage(
    role="tool",
    content="42 tickets found",
    additional_kwargs={"tool_call_id": "call_abc123"}
)
```

### Claude/Anthropic Format (LlamaIndex)

```python
# Dans ChatMessage.blocks ou additional_kwargs
# ToolUseBlock
{
    "type": "tool_use",
    "id": "toolu_abc123",
    "name": "search_database",
    "input": {"query": "tickets"}
}

# ToolResultBlock
{
    "type": "tool_result",
    "tool_use_id": "toolu_abc123",
    "content": "42 tickets found"
}
```

### Gemini Format (LlamaIndex)

```python
# FunctionCall (dans la réponse du modèle)
from google.ai.generativelanguage import FunctionCall
FunctionCall(
    name="search_database",
    args={"query": "tickets"}
)

# FunctionResponse (résultat)
from google.ai.generativelanguage import FunctionResponse
FunctionResponse(
    name="search_database",
    response={"result": "42 tickets found"}
)
```

## Solution proposée

### 1. Créer un HistoryConverter

Nouveau fichier : `agent_framework/implementations/history_converter.py`

```python
from typing import List, Optional, Tuple
from llama_index.core.llms import ChatMessage, MessageRole
import json
import logging

logger = logging.getLogger(__name__)


class ModelFamily:
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    UNKNOWN = "unknown"


class HistoryConverter:
    """Convertit l'historique de conversation entre différents formats de modèles LLM"""
    
    # Mapping des préfixes de modèles vers leurs familles
    MODEL_FAMILY_PREFIXES = {
        "gpt-": ModelFamily.OPENAI,
        "o1-": ModelFamily.OPENAI,
        "o3-": ModelFamily.OPENAI,
        "claude-": ModelFamily.ANTHROPIC,
        "gemini-": ModelFamily.GEMINI,
    }
    
    @classmethod
    def detect_model_family(cls, model_name: str) -> str:
        """Détecte la famille du modèle à partir de son nom"""
        if not model_name:
            return ModelFamily.UNKNOWN
        
        model_lower = model_name.lower()
        for prefix, family in cls.MODEL_FAMILY_PREFIXES.items():
            if model_lower.startswith(prefix):
                return family
        
        return ModelFamily.UNKNOWN
    
    @classmethod
    def needs_conversion(cls, source_model: str, target_model: str) -> bool:
        """Vérifie si une conversion est nécessaire entre deux modèles"""
        source_family = cls.detect_model_family(source_model)
        target_family = cls.detect_model_family(target_model)
        
        # Pas de conversion si même famille ou famille inconnue
        if source_family == target_family:
            return False
        if source_family == ModelFamily.UNKNOWN or target_family == ModelFamily.UNKNOWN:
            return False
        
        return True
    
    @classmethod
    def convert_history(
        cls,
        messages: List[ChatMessage],
        source_model: str,
        target_model: str,
        strategy: str = "simplify"
    ) -> List[ChatMessage]:
        """
        Convertit l'historique vers le format du modèle cible.
        
        Args:
            messages: Liste des messages à convertir
            source_model: Nom du modèle source
            target_model: Nom du modèle cible
            strategy: "simplify" (défaut), "full", ou "strip"
                - simplify: Convertit les tool calls en texte lisible
                - full: Tente une conversion complète (peut échouer)
                - strip: Supprime tous les tool calls
        
        Returns:
            Liste des messages convertis
        """
        if not cls.needs_conversion(source_model, target_model):
            return messages
        
        source_family = cls.detect_model_family(source_model)
        target_family = cls.detect_model_family(target_model)
        
        logger.info(f"🔄 Converting history from {source_family} to {target_family} (strategy: {strategy})")
        
        if strategy == "strip":
            return cls._strip_tool_calls(messages)
        elif strategy == "simplify":
            return cls._simplify_tool_calls(messages, source_family)
        elif strategy == "full":
            return cls._full_conversion(messages, source_family, target_family)
        else:
            logger.warning(f"Unknown strategy '{strategy}', using 'simplify'")
            return cls._simplify_tool_calls(messages, source_family)
    
    @classmethod
    def _strip_tool_calls(cls, messages: List[ChatMessage]) -> List[ChatMessage]:
        """Supprime tous les messages liés aux tool calls"""
        result = []
        for msg in messages:
            # Skip tool role messages
            if msg.role == MessageRole.TOOL:
                continue
            
            # Skip assistant messages that only contain tool calls
            if msg.role == MessageRole.ASSISTANT:
                kwargs = msg.additional_kwargs or {}
                if kwargs.get("tool_calls") and not msg.content:
                    continue
            
            # Clean additional_kwargs
            clean_kwargs = {
                k: v for k, v in (msg.additional_kwargs or {}).items()
                if k not in ("tool_calls", "tool_call_id")
            }
            
            result.append(ChatMessage(
                role=msg.role,
                content=msg.content or "",
                additional_kwargs=clean_kwargs
            ))
        
        return result
    
    @classmethod
    def _simplify_tool_calls(
        cls, 
        messages: List[ChatMessage], 
        source_family: str
    ) -> List[ChatMessage]:
        """
        Convertit les tool calls en texte lisible.
        
        Exemple:
        - Tool call: search_database(query="tickets")
        - Tool result: 42 tickets found
        
        Devient:
        "J'ai utilisé l'outil search_database avec les paramètres: query='tickets'.
         Résultat: 42 tickets found"
        """
        result = []
        pending_tool_calls = {}  # id -> tool call info
        
        for msg in messages:
            if msg.role == MessageRole.ASSISTANT:
                kwargs = msg.additional_kwargs or {}
                tool_calls = kwargs.get("tool_calls", [])
                
                if tool_calls:
                    # Store tool calls for later matching with results
                    for tc in tool_calls:
                        tc_id = cls._extract_tool_call_id(tc, source_family)
                        tc_name = cls._extract_tool_name(tc, source_family)
                        tc_args = cls._extract_tool_args(tc, source_family)
                        if tc_id:
                            pending_tool_calls[tc_id] = {
                                "name": tc_name,
                                "args": tc_args
                            }
                    
                    # If there's also content, keep it
                    if msg.content:
                        result.append(ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=msg.content
                        ))
                else:
                    # Regular assistant message
                    result.append(ChatMessage(
                        role=msg.role,
                        content=msg.content or "",
                        additional_kwargs={}
                    ))
            
            elif msg.role == MessageRole.TOOL:
                # Match with pending tool call
                tc_id = (msg.additional_kwargs or {}).get("tool_call_id")
                tool_info = pending_tool_calls.get(tc_id, {})
                
                tool_name = tool_info.get("name", "unknown_tool")
                tool_args = tool_info.get("args", {})
                tool_result = msg.content or ""
                
                # Create simplified text
                simplified = cls._format_tool_call_as_text(tool_name, tool_args, tool_result)
                
                result.append(ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=simplified
                ))
                
                # Remove from pending
                if tc_id in pending_tool_calls:
                    del pending_tool_calls[tc_id]
            
            else:
                # User, system messages - keep as is
                result.append(ChatMessage(
                    role=msg.role,
                    content=msg.content or "",
                    additional_kwargs={}
                ))
        
        return result
    
    @classmethod
    def _full_conversion(
        cls,
        messages: List[ChatMessage],
        source_family: str,
        target_family: str
    ) -> List[ChatMessage]:
        """
        Tente une conversion complète des formats de tool calls.
        
        Note: Cette méthode est complexe et peut ne pas fonctionner
        pour toutes les combinaisons. Utiliser avec précaution.
        """
        # Pour l'instant, fallback sur simplify
        # TODO: Implémenter les conversions complètes si nécessaire
        logger.warning("Full conversion not yet implemented, falling back to simplify")
        return cls._simplify_tool_calls(messages, source_family)
    
    @staticmethod
    def _extract_tool_call_id(tool_call: dict, family: str) -> Optional[str]:
        """Extrait l'ID du tool call selon le format du provider"""
        if isinstance(tool_call, dict):
            # OpenAI format
            if "id" in tool_call:
                return tool_call["id"]
            # Anthropic format
            if "id" in tool_call and tool_call.get("type") == "tool_use":
                return tool_call["id"]
        return None
    
    @staticmethod
    def _extract_tool_name(tool_call: dict, family: str) -> str:
        """Extrait le nom de l'outil selon le format du provider"""
        if isinstance(tool_call, dict):
            # OpenAI format
            if "function" in tool_call:
                return tool_call["function"].get("name", "unknown")
            # Anthropic format
            if "name" in tool_call:
                return tool_call["name"]
        return "unknown"
    
    @staticmethod
    def _extract_tool_args(tool_call: dict, family: str) -> dict:
        """Extrait les arguments selon le format du provider"""
        if isinstance(tool_call, dict):
            # OpenAI format
            if "function" in tool_call:
                args_str = tool_call["function"].get("arguments", "{}")
                try:
                    return json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    return {"raw": args_str}
            # Anthropic format
            if "input" in tool_call:
                return tool_call["input"]
        return {}
    
    @staticmethod
    def _format_tool_call_as_text(name: str, args: dict, result: str) -> str:
        """Formate un tool call et son résultat en texte lisible"""
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
        return f"[Outil utilisé: {name}({args_str})]\nRésultat: {result}"
```

### 2. Intégration dans LlamaIndexMemoryAdapter

Modifier `llamaindex_memory_adapter.py` :

```python
# Dans _load_memory_for_session(), après le chargement des messages:

from .history_converter import HistoryConverter

# Détecter si conversion nécessaire
if previous_model and model_name:
    if HistoryConverter.needs_conversion(previous_model, model_name):
        logger.info(f"🔄 Model change detected: {previous_model} → {model_name}")
        
        # Récupérer les messages actuels
        chat_store = memory.chat_store
        store_key = memory.chat_store_key
        
        if hasattr(chat_store, 'store') and store_key in chat_store.store:
            messages = chat_store.store[store_key]
            
            # Convertir l'historique
            converted = HistoryConverter.convert_history(
                messages=messages,
                source_model=previous_model,
                target_model=model_name,
                strategy="simplify"  # ou configurable
            )
            
            chat_store.store[store_key] = converted
            logger.info(f"✅ Converted {len(messages)} messages for {model_name}")
```

### 3. Tracking du modèle précédent

Ajouter dans la session metadata le dernier modèle utilisé :

```python
# Dans session storage, ajouter:
{
    "last_model_used": "gpt-4.1-mini",
    "last_model_family": "openai"
}
```

## Tests à écrire

### Tests unitaires

```python
# test_history_converter.py

import pytest
from agent_framework.implementations.history_converter import HistoryConverter, ModelFamily

class TestModelFamilyDetection:
    def test_detect_openai(self):
        assert HistoryConverter.detect_model_family("gpt-4") == ModelFamily.OPENAI
        assert HistoryConverter.detect_model_family("gpt-4.1-mini") == ModelFamily.OPENAI
        assert HistoryConverter.detect_model_family("o1-preview") == ModelFamily.OPENAI
    
    def test_detect_anthropic(self):
        assert HistoryConverter.detect_model_family("claude-3-opus") == ModelFamily.ANTHROPIC
        assert HistoryConverter.detect_model_family("claude-3.5-sonnet") == ModelFamily.ANTHROPIC
    
    def test_detect_gemini(self):
        assert HistoryConverter.detect_model_family("gemini-2.0-flash") == ModelFamily.GEMINI
        assert HistoryConverter.detect_model_family("gemini-2.5-flash-lite") == ModelFamily.GEMINI

class TestNeedsConversion:
    def test_same_family_no_conversion(self):
        assert not HistoryConverter.needs_conversion("gpt-4", "gpt-4.1-mini")
        assert not HistoryConverter.needs_conversion("claude-3-opus", "claude-3.5-sonnet")
    
    def test_different_family_needs_conversion(self):
        assert HistoryConverter.needs_conversion("gpt-4", "gemini-2.0-flash")
        assert HistoryConverter.needs_conversion("claude-3-opus", "gemini-2.0-flash")
        assert HistoryConverter.needs_conversion("gemini-2.0-flash", "gpt-4")

class TestConversionOpenAIToGemini:
    def test_simplify_tool_calls(self):
        # Message avec tool call OpenAI
        messages = [
            ChatMessage(role=MessageRole.USER, content="Cherche les tickets"),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content=None,
                additional_kwargs={
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "search_database",
                            "arguments": '{"query": "tickets"}'
                        }
                    }]
                }
            ),
            ChatMessage(
                role=MessageRole.TOOL,
                content="42 tickets trouvés",
                additional_kwargs={"tool_call_id": "call_123"}
            )
        ]
        
        converted = HistoryConverter.convert_history(
            messages, "gpt-4", "gemini-2.0-flash", strategy="simplify"
        )
        
        # Vérifier que les tool calls sont convertis en texte
        assert len(converted) == 2  # User + Assistant (simplifié)
        assert "search_database" in converted[1].content
        assert "42 tickets" in converted[1].content

class TestConversionClaudeToGemini:
    # Similar tests for Claude format
    pass

class TestConversionGeminiToOpenAI:
    # Tests for reverse conversion
    pass

class TestStripStrategy:
    def test_strip_removes_all_tool_messages(self):
        # ...
        pass
```

## Fichiers à modifier/créer

| Fichier | Action |
|---------|--------|
| `agent_framework/implementations/history_converter.py` | Créer |
| `agent_framework/implementations/llamaindex_memory_adapter.py` | Modifier |
| `agent_framework/implementations/llamaindex_agent.py` | Modifier (tracking modèle) |
| `agent_framework/session/elasticsearch_storage.py` | Modifier (stocker last_model) |
| `tests/test_implementations/test_history_converter.py` | Créer |

## Configuration

Ajouter une variable d'environnement pour la stratégie par défaut :

```bash
# Options: simplify, strip, full
HISTORY_CONVERSION_STRATEGY=simplify
```

## Priorité et effort

| Tâche | Priorité | Effort |
|-------|----------|--------|
| Créer HistoryConverter | Haute | 2-3h |
| Intégrer dans memory adapter | Haute | 1-2h |
| Tests unitaires | Haute | 2h |
| Tracking du modèle précédent | Moyenne | 1h |
| Documentation | Basse | 30min |

**Total estimé** : 6-8h de développement

## Workaround actuel

En attendant l'implémentation, créer une nouvelle session lors du changement de modèle entre familles différentes.
