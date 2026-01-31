# Guide d'Implémentation d'un Nouvel Agent Framework

Ce document détaille toutes les spécificités à respecter lors de la création d'une nouvelle implémentation d'agent (comme `LlamaIndexAgent`). Il est basé sur l'analyse approfondie de `llamaindex_agent.py` et `base_agent.py`.

## Table des Matières

1. [Architecture Générale](#1-architecture-générale)
2. [Méthodes Abstraites à Implémenter](#2-méthodes-abstraites-à-implémenter)
3. [Gestion du Streaming](#3-gestion-du-streaming)
4. [Format des Événements Streaming](#4-format-des-événements-streaming)
5. [Gestion des Activités](#5-gestion-des-activités)
6. [Métriques LLM](#6-métriques-llm)
7. [Gestion de la Mémoire](#7-gestion-de-la-mémoire)
8. [Gestion du Contexte et État](#8-gestion-du-contexte-et-état)
9. [Display Config et Enrichissement](#9-display-config-et-enrichissement)
10. [Rich Content et Validation](#10-rich-content-et-validation)
11. [Checklist d'Implémentation](#11-checklist-dimplémentation)

---

## 1. Architecture Générale

### Hiérarchie des Classes

```
AgentInterface (ABC)
    └── BaseAgent (SkillsMixin, MemoryMixin)
            └── LlamaIndexAgent (implémentation concrète)
            └── VotreNouvelAgent (nouvelle implémentation)
```

### Principe de Séparation des Responsabilités

```
┌─────────────────────────────────────────────────────────────┐
│  Votre Implémentation (ex: OpenAIAgent)                     │
│                                                             │
│  run_agent(stream=True)                                     │
│    └─> Yields RAW framework-specific events                 │
│         (événements bruts de votre framework)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  BaseAgent.handle_message_stream() [NE PAS OVERRIDE]        │
│                                                             │
│  Orchestre le flux streaming:                               │
│    1. Appelle run_agent(stream=True)                        │
│    2. Pour chaque event, appelle process_streaming_event()  │
│    3. Convertit en StructuredAgentOutput                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Votre Implémentation                                       │
│                                                             │
│  process_streaming_event(event)                             │
│    └─> Convertit l'événement framework en format unifié     │
│         Returns: {"type": "chunk", "content": "...", ...}   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Méthodes Abstraites à Implémenter

### 2.1 Méthodes OBLIGATOIRES

```python
class VotreNouvelAgent(BaseAgent):
    
    def get_agent_prompt(self) -> str:
        """Retourne le prompt système par défaut de l'agent."""
        return """Vous êtes un assistant IA..."""
    
    def get_agent_tools(self) -> list[callable]:
        """Retourne la liste des outils disponibles pour l'agent."""
        return [self.tool_1, self.tool_2]
    
    async def initialize_agent(
        self, 
        model_name: str, 
        system_prompt: str, 
        tools: list[callable], 
        **kwargs
    ) -> None:
        """Initialise l'agent avec le framework sous-jacent.
        
        IMPORTANT: Stocker l'instance dans self._agent_instance
        """
        # Créer le LLM avec le helper
        llm = self.create_llm(model_name)
        
        # Initialiser votre agent framework
        self._agent_instance = VotreFramework.create_agent(
            llm=llm,
            tools=tools,
            system_prompt=system_prompt
        )
    
    def create_fresh_context(self) -> Any:
        """Crée un nouveau contexte vide pour l'agent."""
        return VotreContextClass()
    
    def serialize_context(self, ctx: Any) -> dict[str, Any]:
        """Sérialise le contexte pour la persistance."""
        return ctx.to_dict()
    
    def deserialize_context(self, state: dict[str, Any]) -> Any:
        """Désérialise le contexte depuis l'état sauvegardé."""
        return VotreContextClass.from_dict(state)
    
    async def run_agent(
        self, 
        query: str, 
        ctx: Any, 
        stream: bool = False
    ) -> str | AsyncGenerator:
        """Exécute l'agent avec une requête.
        
        CRITIQUE: En mode streaming, doit retourner un AsyncGenerator
        qui yield des événements BRUTS de votre framework.
        """
        if not stream:
            response = await self._agent_instance.chat(query, ctx)
            return str(response)
        else:
            async def event_generator():
                async for event in self._agent_instance.stream(query, ctx):
                    yield event  # Événement BRUT
            return event_generator()
```

### 2.2 Méthodes OPTIONNELLES (mais recommandées)

```python
async def process_streaming_event(self, event: Any) -> dict[str, Any] | None:
    """Convertit les événements framework en format unifié.
    
    DOIT retourner un dict avec:
    - type: "chunk" | "tool_call" | "tool_result" | "activity" | "error"
    - content: str
    - metadata: dict (optionnel)
    
    Retourner None pour ignorer l'événement.
    """
    pass

def get_mcp_server_params(self) -> dict[str, Any] | None:
    """Configuration MCP si nécessaire."""
    return None

def get_model_config(self) -> dict[str, Any]:
    """Configuration par défaut du modèle."""
    return {"temperature": 0.7}
```

---

## 3. Gestion du Streaming

### 3.1 Structure du handle_message_stream (NE PAS OVERRIDE)

Le `handle_message_stream` de `BaseAgent` gère:
1. Validation de l'input
2. Construction de la requête complète
3. Injection de mémoire passive
4. Buffering du rich content
5. Consolidation des tool calls
6. Émission des événements formatés

### 3.2 Implémentation de process_streaming_event

```python
async def process_streaming_event(self, event: Any) -> dict[str, Any] | None:
    """Exemple d'implémentation pour un framework custom."""
    event_type = type(event).__name__
    
    # Token deltas (texte streamé)
    if event_type == "TextChunk":
        chunk = getattr(event, "text", "")
        if chunk:
            return {
                "type": "chunk",
                "content": chunk,
                "metadata": {
                    "source": "votre_agent",
                    "timestamp": datetime.now().isoformat(),
                },
            }
        return None
    
    # Appel d'outil
    if event_type == "ToolCall":
        return {
            "type": "tool_call",
            "content": "",
            "metadata": {
                "source": "votre_agent",
                "tool_name": event.tool_name,
                "tool_arguments": event.arguments,
                "call_id": event.call_id,
                "timestamp": datetime.now().isoformat(),
            },
        }
    
    # Résultat d'outil
    if event_type == "ToolResult":
        return {
            "type": "tool_result",
            "content": str(event.result),
            "metadata": {
                "source": "votre_agent",
                "tool_name": event.tool_name,
                "call_id": event.call_id,
                "is_error": event.is_error,
                "timestamp": datetime.now().isoformat(),
            },
        }
    
    # Événements à ignorer
    if event_type in {"StartEvent", "StopEvent"}:
        return None
    
    # Fallback pour autres événements
    return {
        "type": "activity",
        "content": str(event),
        "metadata": {
            "source": "votre_agent",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
        },
    }
```

---

## 4. Format des Événements Streaming

### 4.1 Types d'Événements Unifiés

| Type | Description | Champs metadata requis |
|------|-------------|------------------------|
| `chunk` | Fragment de texte | `source`, `timestamp` |
| `tool_call` | Appel d'outil | `tool_name`, `tool_arguments`, `call_id`, `timestamp` |
| `tool_result` | Résultat d'outil | `tool_name`, `call_id`, `is_error`, `timestamp` |
| `activity` | Activité générale | `source`, `timestamp` |
| `error` | Erreur | `timestamp` |

### 4.2 Format de Sortie (StructuredAgentOutput)

```python
# Pour les chunks de texte
yield StructuredAgentOutput(
    response_text="",
    parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{chunk}")]
)

# Pour les activités (tool calls, etc.)
yield StructuredAgentOutput(
    response_text="",
    parts=[
        activity_part,  # ActivityOutputPart pour l'ordre
        TextOutputStreamPart(
            text=f"__STREAM_ACTIVITY__{json.dumps(activity_dict)}"
        )  # Backward compatibility
    ]
)

# Message final
yield StructuredAgentOutput(
    response_text=cleaned_text,
    parts=[TextOutputPart(text=cleaned_text), *special_parts],
    streaming_activities=accumulated_activities  # Pour ES
)
```

---

## 5. Gestion des Activités

### 5.1 Utilisation de StreamingPartsAccumulator

```python
from agent_framework.core.streaming_parts_accumulator import StreamingPartsAccumulator
from agent_framework.core.activity_formatter import ActivityFormatter

# Initialisation
activity_accumulator = StreamingPartsAccumulator(source=self.name or "votre_agent")
activity_formatter = ActivityFormatter(source=self.name or "votre_agent")
```

### 5.2 Consolidation Tool Request + Tool Result

**IMPORTANT**: Les tool_request et tool_result doivent être consolidés en une seule activité.

```python
# Lors du tool_result, créer une activité consolidée
activity_part = activity_formatter.format_tool_execution(
    tool_name=tool_name,
    arguments=tool_kwargs,
    result=tool_output,
    execution_time_ms=execution_time_ms,
    is_error=False,
)
activity_part.source = self.name or "votre_agent"

# Ajouter à l'accumulateur
activity_accumulator.add_activity(activity_part)

# Créer l'événement backward-compatible
tool_call_event = {
    "type": "tool_call",
    "source": self.name or "votre_agent",
    "tools": [{"name": tool_name, "arguments": tool_kwargs, "id": call_id}],
    "results": [
        {
            "name": tool_name,
            "content": tool_output,
            "is_error": False,
            "call_id": call_id,
        }
    ],
    "timestamp": activity_part.timestamp,
    "display_info": activity_part.display_info,
}
```

### 5.3 Cas Spéciaux d'Activités

```python
# Skill loading
if tool_name in ("load_skill", "load_skill_tool"):
    activity_part = activity_formatter.format_skill_loading(
        skill_name=skill_name,
        skill_description=skill_description,
        loaded_prompt=tool_output,
        execution_time_ms=execution_time_ms,
        display_name=display_name,
        display_icon=display_icon,
    )

# Diagram generation
elif tool_name == "save_mermaid_as_image":
    activity_part = activity_formatter.format_diagram_generation(
        diagram_type=diagram_type,
        file_name=file_name,
        content=mermaid_code,
        execution_time_ms=execution_time_ms,
    )

# Chart generation
elif tool_name == "save_chart_as_image":
    activity_part = activity_formatter.format_chart_generation(
        chart_type=chart_type,
        file_name=file_name,
        content=content,
        execution_time_ms=execution_time_ms,
    )
```

---

## 6. Métriques LLM

### 6.1 Attributs Requis

```python
def __init__(self, ...):
    # Métriques LLM
    self._metrics_enabled: bool = True  # Configurable via env ENABLE_LLM_METRICS
    self._metrics_collector: LLMMetricsCollector | None = None
    self._last_llm_metrics: LLMMetrics | None = None
    self._api_timing_tracker: Any | None = None
```

### 6.2 Cycle de Vie des Métriques

```python
# 1. Création du collector au début de l'appel
self._metrics_collector = self._create_metrics_collector()
if self._metrics_collector:
    self._metrics_collector.start()
    self._metrics_collector.count_input(full_query)

# 2. Pendant le streaming
if not first_token_recorded and self._metrics_collector:
    self._metrics_collector.record_first_token()
    first_token_recorded = True

# 3. Pour les tool calls
if self._metrics_collector:
    self._metrics_collector.start_tool_call(call_id)
    # ... après exécution ...
    self._metrics_collector.end_tool_call(call_id)
    self._metrics_collector.count_tool_call_tokens(tool_call_data)
    self._metrics_collector.count_thinking(tool_output)

# 4. À la fin
if self._metrics_collector:
    self._metrics_collector.count_output(full_output)
    self._last_llm_metrics = self._finish_metrics_collection()
    if self._last_llm_metrics:
        await self._update_session_llm_stats(self._last_llm_metrics)
    self._metrics_collector = None
```

---

## 7. Gestion de la Mémoire

### 7.1 Attributs de Session

```python
def __init__(self, ...):
    self._session_storage: Any | None = None
    self._memory_adapter: Any | None = None  # SPÉCIFIQUE AU FRAMEWORK
    self._current_memory: Any | None = None  # Type dépend du framework
    self._current_session_id: str | None = None
    self._current_user_id: str | None = None
    self._current_model: str | None = None
```

### 7.2 Configuration de Session avec Mémoire

```python
async def configure_session(self, session_configuration: dict[str, Any]) -> None:
    user_id = session_configuration.get("user_id")
    session_id = session_configuration.get("session_id")
    
    session_changed = (
        session_id != self._current_session_id or 
        user_id != self._current_user_id
    )
    
    # TOUJOURS mettre à jour user_id et session_id
    if user_id:
        self._current_user_id = user_id
    if session_id:
        self._current_session_id = session_id
    
    if session_changed and session_id and user_id:
        self._current_memory = await self._load_memory_for_session(
            session_id, user_id, self._current_model
        )
    
    await super().configure_session(session_configuration)
```

### 7.3 Memory Adapter - SPÉCIFIQUE AU FRAMEWORK

⚠️ **IMPORTANT**: Le Memory Adapter est **entièrement spécifique au framework**.

`LlamaIndexMemoryAdapter` manipule des classes LlamaIndex:
- `ChatMemoryBuffer` - buffer de mémoire LlamaIndex
- `ChatMessage` - format de message LlamaIndex
- `ToolCallBlock` - blocs d'appels d'outils LlamaIndex
- `chat_store.store[store_key]` - structure interne LlamaIndex

**Pour un nouveau framework, vous devez créer votre propre Memory Adapter** qui:
1. Charge l'historique depuis `SessionStorage` (interface commune)
2. Convertit les `MessageData` vers le format de votre framework
3. Crée l'objet mémoire de votre framework
4. Gère la sanitization cross-provider pour VOTRE framework

```python
# Exemple de structure pour un nouveau Memory Adapter
class VotreFrameworkMemoryAdapter:
    """Adapter entre SessionStorage et la mémoire de VotreFramework."""
    
    def __init__(self, session_storage: SessionStorageInterface):
        self.session_storage = session_storage
        self._memory_cache: dict[str, VotreMemoryType] = {}
    
    async def get_memory_for_session(
        self, 
        session_id: str,
        user_id: str,
        model_name: str | None = None,
    ) -> VotreMemoryType:
        """Charge ou crée la mémoire pour une session."""
        # 1. Charger l'historique depuis SessionStorage (commun)
        message_history = await self.session_storage.get_conversation_history(
            session_id=session_id,
            limit=100
        )
        
        # 2. Convertir vers le format de VOTRE framework
        framework_messages = self._convert_to_framework_messages(message_history)
        
        # 3. Créer l'objet mémoire de VOTRE framework
        memory = VotreFramework.create_memory(framework_messages)
        
        return memory
    
    def sanitize_memory_buffer(
        self, 
        memory: VotreMemoryType, 
        target_provider: str | None = None
    ) -> None:
        """Sanitize la mémoire pour compatibilité cross-provider.
        
        DOIT gérer les incompatibilités spécifiques à VOTRE framework:
        - Format des tool_calls (OpenAI vs Anthropic vs Gemini)
        - Champs spécifiques aux providers
        - Structures internes de VOTRE framework
        """
        # Accéder aux messages internes de VOTRE framework
        messages = memory.get_messages()  # API de votre framework
        
        for msg in messages:
            # Sanitizer selon le target_provider
            if target_provider == 'openai':
                # OpenAI: tool_calls.function.arguments = JSON string
                # Supprimer champs Anthropic
                pass
            elif target_provider in ('anthropic', 'gemini'):
                # Anthropic/Gemini: tool_calls.input = dict
                # Supprimer champs OpenAI
                pass
```

### 7.4 Incompatibilités Cross-Provider à Gérer

Lors du changement de modèle (ex: GPT-4 → Claude), la mémoire contient des messages
formatés pour l'ancien provider. Votre sanitization doit gérer:

| Aspect | OpenAI | Anthropic | Gemini |
|--------|--------|-----------|--------|
| Tool call args | `function.arguments` (JSON string) | `input` (dict) | `args` (dict) |
| Empty tool_calls | ❌ Rejeté | ✅ OK | ✅ OK |
| Champs spécifiques | `function_call`, `refusal` | `stop_reason`, `usage` | - |

```python
# Exemple de conversion OpenAI → Anthropic
def _convert_tool_call_openai_to_anthropic(self, tc: dict) -> dict:
    """Convertit un tool_call format OpenAI vers Anthropic."""
    func = tc.get('function', {})
    args_str = func.get('arguments', '{}')
    
    # OpenAI: arguments est un JSON string
    # Anthropic: input est un dict
    try:
        args_dict = json.loads(args_str)
    except json.JSONDecodeError:
        args_dict = {}
    
    return {
        'id': tc.get('id', ''),
        'name': func.get('name', ''),
        'input': args_dict  # dict, pas string
    }
```

---

## 8. Gestion du Contexte et État

### 8.1 get_state et load_state

```python
async def get_state(self) -> dict[str, Any]:
    """Récupère l'état actuel de l'agent."""
    if self._state_ctx is None:
        return {}
    try:
        return self.serialize_context(self._state_ctx)
    finally:
        # Pattern one-time retrieval
        self._state_ctx = None

async def load_state(self, state: dict[str, Any]):
    """Charge l'état de l'agent depuis un dictionnaire."""
    await self._async_ensure_agent_built()
    if state:
        try:
            self._state_ctx = self.deserialize_context(state)
        except Exception as e:
            logger.error(f"Failed to load context state: {e}. Starting fresh.")
            self._state_ctx = self.create_fresh_context()
    else:
        self._state_ctx = self.create_fresh_context()
```

### 8.2 Sauvegarde du Contexte Après Streaming

```python
# À la fin du streaming
final_response = await handler
self._state_ctx = ctx  # IMPORTANT: sauvegarder le contexte
```

---

## 9. Display Config et Enrichissement

### 9.1 Configuration du DisplayConfigManager

```python
def set_display_config_manager(self, manager: DisplayConfigManager | None) -> None:
    """Configure le manager pour l'enrichissement des événements."""
    self._display_config_manager = manager

def _enrich_event(self, event: dict[str, Any]) -> dict[str, Any]:
    """Enrichit un événement avec les infos d'affichage."""
    if self._display_config_manager is not None:
        return enrich_event_with_display_info(
            event, 
            self._display_config_manager, 
            agent_id=self.agent_id
        )
    return event
```

### 9.2 Utilisation dans le Streaming

```python
# Enrichir chaque événement avant émission
loop_activity = {
    "type": "activity",
    "source": "agent",
    "content": "Agent loop started",
    "timestamp": datetime.now(timezone.utc).isoformat(),
}
loop_activity = self._enrich_event(loop_activity)
```

---

## 10. Rich Content et Validation

### 10.1 Buffering du Rich Content

```python
import re

pending_buffer = ""
RICH_CONTENT_PATTERN = re.compile(
    r"^[ \t]*```(mermaid|chart|chartjs|tabledata)\s*\n(.*?)^[ \t]*```",
    re.DOTALL | re.MULTILINE,
)

# Pendant le streaming
pending_buffer += chunk

while True:
    match = RICH_CONTENT_PATTERN.search(pending_buffer)
    if match:
        # Envoyer le texte avant le bloc
        before = pending_buffer[: match.start()]
        if before:
            yield StructuredAgentOutput(
                response_text="",
                parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{before}")]
            )
        
        # Valider et envoyer le bloc
        block = match.group(0)
        try:
            from ..processing.rich_content_validation import validate_rich_content
            validated = validate_rich_content(block)
            yield StructuredAgentOutput(
                response_text="",
                parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")]
            )
        except Exception:
            yield StructuredAgentOutput(
                response_text="",
                parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{block}")]
            )
        
        pending_buffer = pending_buffer[match.end():]
    else:
        # Vérifier si on est dans un bloc ouvert
        # ... logique de détection ...
        break
```

### 10.2 Flush du Buffer Avant Tool Call

**CRITIQUE**: Toujours flush le buffer AVANT d'émettre une activité tool.

```python
if pending_buffer:
    try:
        validated = validate_rich_content(pending_buffer)
        yield StructuredAgentOutput(
            response_text="",
            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{validated}")]
        )
    except Exception:
        yield StructuredAgentOutput(
            response_text="",
            parts=[TextOutputStreamPart(text=f"__STREAM_CHUNK__{pending_buffer}")]
        )
    pending_buffer = ""

# Puis émettre l'activité tool
```

---

## 11. Checklist d'Implémentation

### Validation Automatique

Utilisez le validateur intégré pour vérifier votre implémentation:

```python
from agent_framework.core.implementation_validator import validate_agent_implementation

# Valider une classe
report = await validate_agent_implementation(MonNouvelAgent)

# Ou valider une instance (inclut les tests runtime)
agent = MonNouvelAgent(agent_id="test", name="Test", description="Test")
report = await validate_agent_implementation(agent)

# Vérifier le résultat
if report.is_valid:
    print("✅ Implémentation valide!")
else:
    print("❌ Erreurs à corriger:")
    print(report)
```

Le validateur vérifie:
- ✅ Héritage correct (BaseAgent)
- ✅ Méthodes requises implémentées
- ✅ Signatures de méthodes correctes
- ✅ Méthodes finales non overridées
- ✅ Attributs requis initialisés
- ✅ Méthodes async correctement définies
- ✅ Handler d'événements streaming
- ✅ Pattern Memory Adapter
- ✅ Tests runtime (prompt, tools, context roundtrip)

### Checklist Manuelle

### Méthodes Obligatoires
- [ ] `get_agent_prompt()` - Prompt système par défaut
- [ ] `get_agent_tools()` - Liste des outils
- [ ] `initialize_agent()` - Initialisation du framework
- [ ] `create_fresh_context()` - Création de contexte
- [ ] `serialize_context()` - Sérialisation
- [ ] `deserialize_context()` - Désérialisation
- [ ] `run_agent()` - Exécution (streaming et non-streaming)

### Streaming
- [ ] `process_streaming_event()` - Conversion des événements
- [ ] Gestion des chunks de texte
- [ ] Gestion des tool_call
- [ ] Gestion des tool_result
- [ ] Consolidation tool_request + tool_result
- [ ] Buffering du rich content
- [ ] Flush du buffer avant tool activities

### Activités
- [ ] Utilisation de `StreamingPartsAccumulator`
- [ ] Utilisation de `ActivityFormatter`
- [ ] Cas spéciaux (skill loading, diagram, chart)
- [ ] Format backward-compatible `__STREAM_ACTIVITY__`

### Métriques
- [ ] Initialisation du collector
- [ ] Count input tokens
- [ ] Record first token
- [ ] Track tool call timing
- [ ] Count output tokens
- [ ] Update session stats

### Mémoire
- [ ] Gestion de `_current_user_id` et `_current_session_id`
- [ ] **Créer un Memory Adapter spécifique à votre framework**
- [ ] Chargement de la mémoire par session
- [ ] Sanitization cross-provider **pour votre framework**
- [ ] Injection passive de mémoire

### État
- [ ] Sauvegarde du contexte après streaming
- [ ] Implémentation de `get_state()` et `load_state()`

### Display
- [ ] Support de `DisplayConfigManager`
- [ ] Enrichissement des événements avec `_enrich_event()`

### Métadonnées
- [ ] Override de `get_metadata()` avec les capacités spécifiques

---

## Exemple Complet Minimal

```python
"""Exemple d'implémentation minimale d'un nouvel agent."""

from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from agent_framework.core.base_agent import BaseAgent
from agent_framework.core.agent_interface import (
    StructuredAgentInput,
    StructuredAgentOutput,
    TextOutputStreamPart,
)


class MonNouvelAgent(BaseAgent):
    """Implémentation d'agent pour MonFramework."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        **kwargs
    ):
        self._agent_instance = None
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            **kwargs
        )

    def get_agent_prompt(self) -> str:
        return "Vous êtes un assistant IA utile."

    def get_agent_tools(self) -> list[callable]:
        return []

    async def initialize_agent(
        self,
        model_name: str,
        system_prompt: str,
        tools: list[callable],
        **kwargs
    ) -> None:
        llm = self.create_llm(model_name)
        # Initialiser votre framework ici
        self._agent_instance = ...

    def create_fresh_context(self) -> Any:
        return {}

    def serialize_context(self, ctx: Any) -> dict[str, Any]:
        return ctx

    def deserialize_context(self, state: dict[str, Any]) -> Any:
        return state

    async def run_agent(
        self,
        query: str,
        ctx: Any,
        stream: bool = False
    ) -> str | AsyncGenerator:
        if not stream:
            # Mode non-streaming
            response = await self._agent_instance.chat(query)
            return str(response)
        else:
            # Mode streaming
            async def generator():
                async for event in self._agent_instance.stream(query):
                    yield event
            return generator()

    async def process_streaming_event(self, event: Any) -> dict[str, Any] | None:
        event_type = type(event).__name__
        
        if event_type == "TextChunk":
            return {
                "type": "chunk",
                "content": event.text,
                "metadata": {"timestamp": datetime.now().isoformat()},
            }
        
        return None
```


---

## Annexe A: Spécificités LlamaIndex à Reproduire

### A.1 Gestion des Événements LlamaIndex

LlamaIndex émet des événements spécifiques qu'il faut mapper:

| Événement LlamaIndex | Type Unifié | Action |
|---------------------|-------------|--------|
| `AgentStream` | `chunk` | Extraire `event.delta` |
| `ToolCallResult` | `tool_call` + `tool_result` | Consolider en une activité |
| `AgentInput` / `InputEvent` | `activity` | "Agent loop started" |
| `AgentOutput` | - | Ignorer |
| `StopEvent` / `StartEvent` | - | Ignorer |
| `ToolCall` | - | Tracker timing, ne pas émettre |

### A.2 Pattern de Streaming LlamaIndex

```python
async def handle_message_stream(self, session_id, agent_input):
    # 1. Initialisation
    handler = self._run_agent_stream_internal(full_query, ctx, **run_kwargs)
    
    # 2. Boucle sur les événements
    async for event in handler.stream_events():
        event_type = type(event).__name__
        
        # AgentStream = chunks de texte
        if event_type == "AgentStream":
            chunk = getattr(event, "delta", "")
            # ... traitement ...
        
        # ToolCallResult = résultat d'outil (consolidé)
        elif event_type == "ToolCallResult":
            tool_name = getattr(event, "tool_name", "unknown_tool")
            tool_kwargs = getattr(event, "tool_kwargs", {})
            call_id = getattr(event, "call_id", "unknown")
            tool_output = str(getattr(event, "tool_output", ""))
            # ... créer activité consolidée ...
    
    # 3. Résultat final
    final_response = await handler
    self._state_ctx = ctx
```

### A.3 Helper create_llm

LlamaIndexAgent fournit un helper pour créer les LLM:

```python
def create_llm(
    self, 
    model_name: str = None, 
    agent_config: AgentConfig = None, 
    **override_params
) -> Any:
    """Crée un LLM LlamaIndex via ModelClientFactory."""
    return client_factory.create_llamaindex_llm(
        model_name=model_name, 
        agent_config=agent_config, 
        **override_params
    )
```

---

## Annexe B: Structures de Données Clés

### B.1 ActivityOutputPart

```python
class ActivityOutputPart(BaseModel):
    type: Literal["activity"] = "activity"
    activity_type: str  # "tool_call", "skill_loading", "diagram_generation", etc.
    source: str  # Nom de l'agent
    content: str | None = None  # Texte user-friendly
    timestamp: str  # ISO 8601
    tools: list[dict[str, Any]] | None = None  # Pour tool_request
    results: list[dict[str, Any]] | None = None  # Pour tool_result
    display_info: dict[str, Any] | None = None  # Métadonnées UI
    technical_details: TechnicalDetails | None = None  # Pour ES uniquement
```

### B.2 TechnicalDetails

```python
class TechnicalDetails(BaseModel):
    function_name: str
    arguments: dict[str, Any]
    raw_result: str  # JSON string pour ES
    execution_time_ms: int
    timestamp: str
    status: Literal["success", "error"]
    error_message: str | None = None
```

### B.3 Format __STREAM_ACTIVITY__

```python
{
    "type": "tool_call",  # ou "activity", "error", "other"
    "source": "agent_name",
    "tools": [{"name": "...", "arguments": {...}, "id": "..."}],
    "results": [{"name": "...", "content": "...", "is_error": False, "call_id": "..."}],
    "timestamp": "2024-01-15T10:30:00Z",
    "display_info": {
        "id": "tool_search_web",
        "friendly_name": "🔍 Recherche web",
        "description": "...",
        "icon": "🔍",
        "category": "search"
    }
}
```

---

## Annexe C: Imports Essentiels

```python
# Core
from agent_framework.core.base_agent import BaseAgent, SKILLS_AVAILABLE
from agent_framework.core.agent_interface import (
    ActivityOutputPart,
    AgentConfig,
    StructuredAgentInput,
    StructuredAgentOutput,
    TextOutputPart,
    TextOutputStreamPart,
)
from agent_framework.core.model_clients import client_factory

# Streaming et Activités
from agent_framework.core.streaming_parts_accumulator import StreamingPartsAccumulator
from agent_framework.core.activity_formatter import ActivityFormatter
from agent_framework.core.step_display_config import (
    DisplayConfigManager, 
    enrich_event_with_display_info
)

# Utilitaires
from agent_framework.utils.special_blocks import parse_special_blocks_from_text

# Métriques (optionnel)
try:
    from agent_framework.monitoring import LLMMetrics, LLMMetricsCollector
    LLM_METRICS_AVAILABLE = True
except ImportError:
    LLM_METRICS_AVAILABLE = False
```

---

## Annexe D: Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `ENABLE_LLM_METRICS` | Active la collecte de métriques | `true` |
| `ENABLE_SKILLS` | Active le système de skills | `true` |
| `OPENAI_API_MODEL` | Modèle par défaut | - |

---

## Annexe E: Erreurs Courantes à Éviter

1. **Ne pas override `handle_message_stream`** - Utiliser `run_agent` et `process_streaming_event`

2. **Oublier de flush le buffer avant les tool activities** - Cause des problèmes d'ordre

3. **Ne pas consolider tool_request + tool_result** - Crée du bruit dans l'UI

4. **Oublier de sauvegarder `self._state_ctx`** - Perte de l'historique de conversation

5. **Ne pas mettre à jour `_current_user_id`** - Problèmes d'isolation Graphiti

6. **Réutiliser `LlamaIndexMemoryAdapter` pour un autre framework** - Le Memory Adapter est 100% spécifique au framework. Vous DEVEZ créer votre propre adapter.

7. **Ne pas enrichir les événements** - Perte des friendly names dans l'UI
