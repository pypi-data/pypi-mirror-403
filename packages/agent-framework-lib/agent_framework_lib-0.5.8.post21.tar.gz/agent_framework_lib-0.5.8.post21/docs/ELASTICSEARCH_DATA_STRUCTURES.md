# Elasticsearch Data Structures - Agent Framework

Ce document décrit les structures JSON des documents stockés dans Elasticsearch par l'Agent Framework, ainsi que les endpoints API qui les génèrent.

## Vue d'ensemble des Index

| Index | Description | Préfixe par défaut |
|-------|-------------|-------------------|
| `agent-sessions-metadata` | Métadonnées des sessions | `ELASTICSEARCH_SESSION_INDEX_PREFIX` |
| `agent-sessions-messages` | Messages de conversation | `ELASTICSEARCH_SESSION_INDEX_PREFIX` |
| `agent-sessions-states` | États des agents | `ELASTICSEARCH_SESSION_INDEX_PREFIX` |
| `agent-sessions-insights` | Insights et métadonnées des messages | `ELASTICSEARCH_SESSION_INDEX_PREFIX` |
| `agent-sessions-lifecycle` | Événements du cycle de vie des agents | `ELASTICSEARCH_SESSION_INDEX_PREFIX` |
| `agent-configs` | Configurations dynamiques des agents | `ELASTICSEARCH_CONFIG_INDEX` |
| `agent-logs-{date}` | Logs centralisés (rotation quotidienne) | `ELASTICSEARCH_LOG_INDEX_PATTERN` |
| `agent-files-metadata` | Métadonnées des fichiers stockés | Index fixe |

## Résumé des Endpoints par Index

| Index | Endpoints qui écrivent | Endpoints qui lisent |
|-------|------------------------|----------------------|
| `metadata` | `POST /init`, `POST /message`, `POST /end`, `PUT /session/{id}/label`, `POST /feedback/*` | `GET /sessions`, `GET /sessions/info`, `GET /session/{id}/status` |
| `messages` | `POST /message`, `POST /stream` | `GET /sessions/{id}/history` |
| `states` | Automatique (AgentManager) | Automatique (AgentManager) |
| `insights` | Non exposé (usage interne) | Non exposé (usage interne) |
| `lifecycle` | Automatique (AgentManager) | `GET /agents/{id}/lifecycle` |
| `configs` | `PUT /config/agents/{id}` | `GET /config/agents/{id}`, `GET /config/agents/{id}/versions` |
| `logs` | Automatique (logging) | Non exposé (Kibana/ES direct) |
| `files-metadata` | Via FileStorageManager | Via FileStorageManager |

---

## 1. Sessions Metadata (`agent-sessions-metadata`)

Stocke les métadonnées de chaque session de conversation.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | `POST /init` | Crée une nouvelle session avec configuration |
| Création implicite | `POST /message` | Crée la session si elle n'existe pas |
| Mise à jour | `POST /end` | Marque la session comme fermée |
| Mise à jour | `PUT /session/{id}/label` | Met à jour le label de la session |
| Mise à jour | `POST /feedback/message`, `POST /feedback/flag` | Ajoute feedback dans metadata |
| Lecture | `GET /sessions` | Liste les session_id de l'utilisateur |
| Lecture | `GET /sessions/info` | Liste les sessions avec détails |
| Lecture | `GET /session/{id}/status` | Statut d'une session |

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "agent_type": { "type": "keyword" },
      "agent_instance_config": { "type": "object", "enabled": false },
      "session_configuration": { "type": "object", "enabled": false },
      "config_reference": {
        "type": "object",
        "properties": {
          "doc_id": { "type": "keyword" },
          "version": { "type": "integer" }
        }
      },
      "session_overrides": { "type": "object", "enabled": true },
      "correlation_id": { "type": "keyword" },
      "session_label": { 
        "type": "text", 
        "fields": { "keyword": { "type": "keyword" } }
      },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "last_update": { "type": "date" },
      "metadata": { "type": "object", "enabled": false }
    }
  }
}
```

### Description des nouveaux champs

| Champ | Type | Description |
|-------|------|-------------|
| `config_reference` | object | Référence vers la configuration ES utilisée |
| `config_reference.doc_id` | keyword | ID du document de configuration dans `agent-configs` |
| `config_reference.version` | integer | Version de la configuration utilisée |
| `session_overrides` | object | Overrides spécifiques à la session (model, temperature, etc.) |
| `last_update` | date | Timestamp de la dernière activité (mis à jour à chaque message) |
| `agent_instance_config` | object | **DEPRECATED** - Conservé pour compatibilité, ne plus utiliser |

### Exemple de Document

```json
{
  "_id": "user123_session456",
  "_source": {
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "agent_instance_config": {},
    "session_configuration": {
      "system_prompt": "Tu es un assistant technique spécialisé...",
      "model_name": "gpt-4-turbo",
      "model_config": {
        "temperature": 0.7,
        "max_tokens": 4096
      },
      "enable_rich_content": true
    },
    "config_reference": {
      "doc_id": "config-abc-123",
      "version": 3
    },
    "session_overrides": {
      "temperature": 0.8,
      "model_name": "gpt-4-turbo"
    },
    "correlation_id": "req-abc-123",
    "session_label": "Discussion sur le projet X",
    "created_at": "2024-12-10T10:30:00.000Z",
    "updated_at": "2024-12-10T11:45:00.000Z",
    "metadata": {
      "status": "active",
      "data": { "project_name": "MonProjet" },
      "original_configuration": { "system_prompt": "Tu es un assistant pour {{data.project_name}}" },
      "agent_identity": {
        "agent_id": "support-agent-001",
        "agent_type": "llamaindex"
      },
      "feedback": {
        "messages": {
          "interaction-uuid-1": "up",
          "interaction-uuid-1_timestamp": "2024-12-10T10:35:00.000Z"
        },
        "flag_message": "Session à revoir",
        "flag_timestamp": "2024-12-10T11:00:00.000Z"
      }
    }
  }
}
```

### Où est stocké le System Prompt Override ?

Le `system_prompt` personnalisé est stocké dans **`session_configuration.system_prompt`** :

1. **À la création** (`POST /init`) : Le system_prompt fourni dans `configuration.system_prompt` est stocké dans `session_configuration`
2. **Templating** : Si `data` est fourni, les placeholders `{{data.key}}` sont remplacés avant stockage
3. **Priorité** : `session_configuration.system_prompt` > `agent-configs` (ES) > prompt par défaut de l'agent

```json
// Exemple de requête POST /init
{
  "user_id": "user123",
  "configuration": {
    "system_prompt": "Tu es un assistant pour le projet {{data.project_name}}",
    "model_name": "gpt-4-turbo"
  },
  "data": {
    "project_name": "MonProjet"
  }
}

// Résultat stocké dans session_configuration
{
  "system_prompt": "Tu es un assistant pour le projet MonProjet",
  "model_name": "gpt-4-turbo"
}
```

---

## 2. Messages (`agent-sessions-messages`)

Stocke chaque message de la conversation (utilisateur et agent).

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | `POST /message` | Ajoute message utilisateur + réponse agent |
| Création | `POST /stream` | Idem, en mode streaming |
| Lecture | `GET /sessions/{id}/history` | Récupère l'historique de conversation |

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "message_id": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "agent_type": { "type": "keyword" },
      "interaction_id": { "type": "keyword" },
      "sequence_number": { "type": "integer" },
      "message_type": { "type": "keyword" },
      "role": { "type": "keyword" },
      "text_content": { "type": "text" },
      "parts": { "type": "object", "enabled": false },
      "response_text_main": { "type": "text" },
      "created_at": { "type": "date" },
      "processed_at": { "type": "date" },
      "parent_message_id": { "type": "keyword" },
      "related_message_ids": { "type": "keyword" },
      "processing_time_ms": { "type": "integer" },
      "model_used": { "type": "keyword" },
      "selection_mode": { "type": "keyword" },
      "token_count": { "type": "object", "enabled": false }
    }
  }
}
```

### Description des champs multi-model

| Champ | Type | Description |
|-------|------|-------------|
| `model_used` | keyword | Identifiant du modèle qui a généré la réponse (ex: `gpt-4-turbo`, `claude-sonnet`) |
| `selection_mode` | keyword | Mode de sélection du modèle: `auto` (routage intelligent) ou `manual` (choix utilisateur) |

### Exemple de Document - Message Utilisateur

```json
{
  "_id": "msg-uuid-001",
  "_source": {
    "message_id": "msg-uuid-001",
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "interaction_id": "interaction-001",
    "sequence_number": 1,
    "message_type": "user_message",
    "role": "user",
    "text_content": "Comment puis-je configurer l'authentification OAuth2 ?",
    "parts": [
      {
        "type": "text",
        "content": "Comment puis-je configurer l'authentification OAuth2 ?"
      }
    ],
    "response_text_main": null,
    "created_at": "2024-12-10T10:30:15.000Z",
    "processed_at": null,
    "parent_message_id": null,
    "related_message_ids": [],
    "processing_time_ms": null,
    "model_used": null,
    "selection_mode": null,
    "token_count": null
  }
}
```

### Exemple de Document - Réponse Agent

```json
{
  "_id": "msg-uuid-002",
  "_source": {
    "message_id": "msg-uuid-002",
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "interaction_id": "interaction-001",
    "sequence_number": 2,
    "message_type": "assistant_message",
    "role": "assistant",
    "text_content": null,
    "parts": [
      {
        "type": "text",
        "content": "Pour configurer OAuth2, suivez ces étapes..."
      }
    ],
    "response_text_main": "Pour configurer OAuth2, suivez ces étapes...",
    "created_at": "2024-12-10T10:30:18.000Z",
    "processed_at": "2024-12-10T10:30:18.500Z",
    "parent_message_id": "msg-uuid-001",
    "related_message_ids": ["msg-uuid-001"],
    "processing_time_ms": 3500,
    "model_used": "gpt-4-turbo",
    "selection_mode": "auto",
    "token_count": {
      "prompt_tokens": 150,
      "completion_tokens": 320,
      "total_tokens": 470
    }
  }
}
```

---

## 3. Agent States (`agent-sessions-states`)

Stocke l'état interne de l'agent pour chaque session.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création/MAJ | Automatique | Sauvegardé par `AgentManager` après chaque interaction |
| Lecture | Automatique | Chargé par `AgentManager` au démarrage de session |

L'état est géré automatiquement par le `_ManagedAgentProxy` et n'est pas exposé directement via l'API REST.

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "session_id": { "type": "keyword" },
      "state": { "type": "object", "enabled": false },
      "updated_at": { "type": "date" }
    }
  }
}
```

### Exemple de Document

```json
{
  "_id": "session456",
  "_source": {
    "session_id": "session456",
    "state": {
      "memory": {
        "chat_history": [...],
        "context_window": [...]
      },
      "tools_state": {
        "last_tool_used": "search_docs",
        "tool_results_cache": {}
      },
      "custom_data": {
        "user_preferences": {
          "language": "fr",
          "verbosity": "detailed"
        }
      }
    },
    "updated_at": "2024-12-10T11:45:00.000Z"
  }
}
```

---

## 4. Insights (`agent-sessions-insights`)

Stocke les insights et métadonnées dérivés des messages.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | `POST /feedback/message` | Crée un insight de type `message_feedback` |
| Création | `POST /feedback/session` | Crée un insight de type `session_feedback` |
| Création | `POST /feedback/flag` | Crée un insight de type `session_flag` |
| Création | Non exposé | Usage interne via `add_insight()` / `add_metadata()` |
| Lecture | Non exposé | Usage interne via `get_message_with_details()` |

Cet index stocke les insights et métadonnées dérivés des messages, incluant les feedbacks utilisateurs, l'analyse de sentiment, la détection d'intention, et l'extraction de topics.

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "insight_id": { "type": "keyword" },
      "message_id": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "agent_type": { "type": "keyword" },
      "insight_type": { "type": "keyword" },
      "insight_data": { "type": "object", "enabled": false },
      "created_at": { "type": "date" },
      "created_by": { "type": "keyword" }
    }
  }
}
```

### Exemple de Document - Insight

```json
{
  "_id": "insight-uuid-001",
  "_source": {
    "insight_id": "insight-uuid-001",
    "message_id": "msg-uuid-001",
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "insight_type": "sentiment_analysis",
    "insight_data": {
      "sentiment": "neutral",
      "confidence": 0.85,
      "topics": ["oauth2", "authentication", "configuration"],
      "intent": "technical_question"
    },
    "created_at": "2024-12-10T10:30:16.000Z",
    "created_by": "insight-processor"
  }
}
```

### Exemple de Document - Metadata

```json
{
  "_id": "metadata-uuid-001",
  "_source": {
    "metadata_id": "metadata-uuid-001",
    "message_id": "msg-uuid-002",
    "session_id": "session456",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "metadata_type": "tool_usage",
    "metadata": {
      "tools_called": ["search_docs", "format_response"],
      "sources_used": [
        { "doc_id": "doc-123", "relevance": 0.92 },
        { "doc_id": "doc-456", "relevance": 0.87 }
      ]
    },
    "created_at": "2024-12-10T10:30:18.000Z",
    "created_by": "agent-processor"
  }
}
```

### Exemple de Document - Message Feedback

```json
{
  "_id": "insight-feedback-001",
  "_source": {
    "insight_id": "insight-feedback-001",
    "message_id": "msg-uuid-002",
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "insight_type": "message_feedback",
    "insight_data": {
      "feedback": "up",
      "timestamp": "2024-12-10T10:35:00.000Z"
    },
    "created_at": "2024-12-10T10:35:00.000Z",
    "created_by": "user"
  }
}
```

### Exemple de Document - Session Feedback

```json
{
  "_id": "insight-session-001",
  "_source": {
    "insight_id": "insight-session-001",
    "message_id": null,
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "insight_type": "session_feedback",
    "insight_data": {
      "rating": 5,
      "comment": "Très utile, merci!",
      "timestamp": "2024-12-10T11:00:00.000Z"
    },
    "created_at": "2024-12-10T11:00:00.000Z",
    "created_by": "user"
  }
}
```

### Exemple de Document - Session Flag

```json
{
  "_id": "insight-flag-001",
  "_source": {
    "insight_id": "insight-flag-001",
    "message_id": "",
    "session_id": "session456",
    "user_id": "user123",
    "agent_id": null,
    "agent_type": null,
    "insight_type": "session_flag",
    "insight_data": {
      "flag_message": "Session à revoir par l'équipe QA",
      "timestamp": "2024-12-10T11:00:00.000Z",
      "previous_flag": null,
      "flag_changed": true
    },
    "created_at": "2024-12-10T11:00:00.000Z",
    "created_by": "user"
  }
}
```

### Types d'insights courants

| insight_type | Description |
|--------------|-------------|
| `sentiment_analysis` | Analyse de sentiment du message |
| `message_feedback` | Feedback utilisateur sur un message (up/down) |
| `session_feedback` | Feedback utilisateur sur la session (rating, comment) |
| `session_flag` | Flag/commentaire verbal sur la session |
| `tool_usage` | Métadonnées sur les outils utilisés |

---

## 5. Lifecycle Events (`agent-sessions-lifecycle`)

Stocke les événements du cycle de vie des agents.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | Automatique | Enregistré par `AgentManager` lors des événements |
| Lecture | `GET /agents/{agent_id}/lifecycle` | Liste les événements d'un agent |

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "lifecycle_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "agent_type": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "metadata": { "type": "object", "enabled": false }
    }
  }
}
```

### Exemple de Document

```json
{
  "_id": "lifecycle-uuid-001",
  "_source": {
    "lifecycle_id": "lifecycle-uuid-001",
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "event_type": "agent_started",
    "session_id": "session456",
    "user_id": "user123",
    "timestamp": "2024-12-10T10:30:00.000Z",
    "metadata": {
      "initialization_time_ms": 250,
      "model_loaded": "gpt-4-turbo",
      "tools_loaded": ["search_docs", "format_response", "calculator"]
    }
  }
}
```

### Types d'événements courants

| event_type | Description |
|------------|-------------|
| `agent_started` | Agent initialisé |
| `agent_stopped` | Agent arrêté |
| `session_created` | Nouvelle session créée |
| `session_resumed` | Session reprise |
| `error_occurred` | Erreur survenue |
| `tool_executed` | Outil exécuté |

---

## 6. Agent Configs (`agent-configs`)

Stocke les configurations dynamiques des agents avec versioning.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création/MAJ | `PUT /config/agents/{agent_id}` | Crée une nouvelle version de config |
| Lecture | `GET /config/agents/{agent_id}` | Récupère la config active |
| Lecture | `GET /config/agents/{agent_id}/versions` | Historique des versions |
| Suppression | `DELETE /config/agents/{agent_id}` | Supprime toutes les configs |

### Différence avec session_configuration

| Aspect | `agent-configs` | `session_configuration` |
|--------|-----------------|-------------------------|
| Scope | Global par agent_id | Par session |
| Persistance | Permanent | Durée de la session |
| Modification | Via API `/config/agents/*` | Via `POST /init` uniquement |
| Priorité | Fallback si pas de session_config | Prioritaire |

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "agent_id": { "type": "keyword" },
      "agent_type": { "type": "keyword" },
      "version": { "type": "integer" },
      "updated_at": { "type": "date" },
      "updated_by": { "type": "keyword" },
      "config": { "type": "object", "enabled": true },
      "metadata": { "type": "object", "enabled": true },
      "tags": {
        "type": "nested",
        "properties": {
          "name": { "type": "keyword" },
          "color": { "type": "keyword" }
        }
      },
      "image_url": { "type": "keyword" },
      "active": { "type": "boolean" }
    }
  }
}
```

### Description des champs de métadonnées agent

| Champ | Type | Description |
|-------|------|-------------|
| `tags` | nested | Liste de tags pour catégoriser l'agent (name + color hex) |
| `image_url` | keyword | URL de l'image/avatar de l'agent |

### Exemple de Document

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "agent_id": "support-agent-001",
    "agent_type": "llamaindex",
    "version": 3,
    "updated_at": "2024-12-10T09:00:00.000Z",
    "updated_by": "admin@company.com",
    "tags": [
      { "name": "production", "color": "#28A745" },
      { "name": "support", "color": "#007BFF" }
    ],
    "image_url": "https://example.com/agents/support-agent.png",
    "config": {
      "system_prompt": "Tu es un assistant technique spécialisé...",
      "model": "gpt-4-turbo",
      "temperature": 0.7,
      "max_tokens": 4096,
      "tools": ["search_docs", "format_response"],
      "rag_settings": {
        "top_k": 5,
        "similarity_threshold": 0.75
      }
    },
    "metadata": {
      "description": "Configuration production v3",
      "changelog": "Ajout du tool format_response"
    },
    "active": true
  }
}
```

### Notes sur le versioning

- Seule la configuration avec `active: true` est utilisée
- Les anciennes versions sont conservées avec `active: false`
- Le champ `version` est auto-incrémenté à chaque mise à jour

---

## 7. Logs (`agent-logs-{date}`)

Stocke les logs centralisés avec rotation quotidienne.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | Automatique | Via `ElasticsearchLoggingHandler` |
| Lecture | Non exposé | Accès direct via Kibana ou API ES |

Les logs sont envoyés automatiquement par le handler de logging Python. Ils ne sont pas exposés via l'API REST mais peuvent être consultés via Kibana ou l'API Elasticsearch directement.

### Structure du Document

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "@timestamp": "2024-12-10T10:30:15.123Z",
    "level": "INFO",
    "logger_name": "agent_framework.core.agent_manager",
    "message": "Agent initialized successfully",
    "module": "agent_manager",
    "function": "initialize_agent",
    "line_number": 142,
    "context": {
      "agent_id": "support-agent-001",
      "session_id": "session456",
      "user_id": "user123"
    },
    "error": null,
    "trace": {
      "trace_id": "abc123def456",
      "span_id": "span789"
    },
    "exception": null
  }
}
```

### Exemple avec erreur

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "@timestamp": "2024-12-10T10:35:22.456Z",
    "level": "ERROR",
    "logger_name": "agent_framework.implementations.llamaindex_agent",
    "message": "Failed to process user message",
    "module": "llamaindex_agent",
    "function": "process_message",
    "line_number": 287,
    "context": {
      "agent_id": "support-agent-001",
      "session_id": "session456",
      "message_id": "msg-uuid-003"
    },
    "error": {
      "type": "LLMConnectionError",
      "severity": "high",
      "technical_details": "Connection timeout after 30s"
    },
    "trace": {
      "trace_id": "abc123def456",
      "span_id": "span790"
    },
    "exception": {
      "type": "TimeoutError",
      "message": "Connection to OpenAI API timed out",
      "stack_trace": "Traceback (most recent call last):\n  File..."
    }
  }
}
```

---

## Variables d'environnement

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `ELASTICSEARCH_ENABLED` | `false` | Active l'intégration Elasticsearch |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | URL du cluster Elasticsearch |
| `ELASTICSEARCH_SESSION_INDEX_PREFIX` | `agent-sessions` | Préfixe des index de session |
| `ELASTICSEARCH_CONFIG_INDEX` | `agent-configs` | Index des configurations |
| `ELASTICSEARCH_LOG_INDEX_PATTERN` | `agent-logs-{date}` | Pattern des index de logs |
| `ELASTICSEARCH_LOG_BATCH_SIZE` | `100` | Taille du batch pour les logs |
| `ELASTICSEARCH_LOG_FLUSH_INTERVAL` | `5.0` | Intervalle de flush en secondes |
| `ELASTICSEARCH_CONFIG_CACHE_TTL` | `300` | TTL du cache de config en secondes |

---

## 8. File Metadata (`agent-files-metadata`)

Stores metadata for all files managed by the Agent Framework file storage system, enabling full-text search and efficient querying across file metadata.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | Via `FileStorageManager` | Metadata created when file is stored |
| Lecture | Via `FileStorageManager` | Metadata retrieved with file operations |
| Mise à jour | Via `FileStorageManager` | Metadata updated on file modifications |
| Suppression | Via `FileStorageManager` | Metadata deleted when file is removed |

File metadata operations are managed internally by the `MetadataStorageManager` and are not directly exposed via REST API. They are accessed through the file storage backends (Local, S3, MinIO, GCP).

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "file_id": { "type": "keyword" },
      "filename": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "mime_type": { "type": "keyword" },
      "size_bytes": { "type": "long" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "user_id": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "is_generated": { "type": "boolean" },
      "tags": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "custom_metadata": { "type": "object", "enabled": false },
      "storage_backend": { "type": "keyword" },
      "storage_path": { "type": "keyword" },
      "markdown_content": { "type": "text", "index": false },
      "markdown_file_id": { "type": "keyword" },
      "conversion_status": { "type": "keyword" },
      "conversion_timestamp": { "type": "date" },
      "conversion_error": { "type": "text", "index": false },
      "has_visual_content": { "type": "boolean" },
      "image_analysis_result": { "type": "object", "enabled": false },
      "multimodal_processing_status": { "type": "keyword" },
      "processing_errors": { "type": "text", "index": false },
      "processing_warnings": { "type": "text", "index": false },
      "total_processing_time_ms": { "type": "float" },
      "generation_model": { "type": "keyword" },
      "generation_prompt": { "type": "text", "index": false },
      "generation_parameters": { "type": "object", "enabled": false }
    }
  }
}
```

### Description des champs

| Champ | Type | Description |
|-------|------|-------------|
| `file_id` | keyword | Identifiant unique du fichier (utilisé comme document ID) |
| `filename` | text/keyword | Nom original du fichier avec recherche full-text |
| `mime_type` | keyword | Type MIME du fichier |
| `size_bytes` | long | Taille du fichier en octets |
| `created_at` | date | Timestamp de création |
| `updated_at` | date | Timestamp de dernière mise à jour |
| `user_id` | keyword | ID de l'utilisateur propriétaire |
| `session_id` | keyword | ID de la session associée |
| `agent_id` | keyword | ID de l'agent associé |
| `is_generated` | boolean | Indique si le fichier a été généré par l'IA |
| `tags` | text/keyword | Tags du fichier avec recherche full-text |
| `custom_metadata` | object | Métadonnées personnalisées (non indexées) |
| `storage_backend` | keyword | Backend de stockage (local, s3, minio, gcp) |
| `storage_path` | keyword | Chemin de stockage spécifique au backend |
| `markdown_content` | text | Contenu markdown converti (non indexé) |
| `markdown_file_id` | keyword | ID du fichier markdown associé |
| `conversion_status` | keyword | Statut de conversion (not_attempted, success, failed) |
| `conversion_timestamp` | date | Timestamp de la conversion |
| `conversion_error` | text | Message d'erreur de conversion (non indexé) |
| `has_visual_content` | boolean | Contient du contenu visuel |
| `image_analysis_result` | object | Résultat d'analyse d'image (non indexé) |
| `multimodal_processing_status` | keyword | Statut du traitement multimodal |
| `processing_errors` | text | Erreurs de traitement (non indexé) |
| `processing_warnings` | text | Avertissements de traitement (non indexé) |
| `total_processing_time_ms` | float | Temps total de traitement en ms |
| `generation_model` | keyword | Modèle utilisé pour la génération |
| `generation_prompt` | text | Prompt utilisé pour la génération (non indexé) |
| `generation_parameters` | object | Paramètres de génération (non indexé) |

### Exemple de Document

```json
{
  "_id": "file-uuid-001",
  "_source": {
    "file_id": "file-uuid-001",
    "filename": "rapport-technique-2024.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 2457600,
    "created_at": "2024-12-10T10:30:00.000Z",
    "updated_at": "2024-12-10T10:35:00.000Z",
    "user_id": "user123",
    "session_id": "session456",
    "agent_id": "support-agent-001",
    "is_generated": false,
    "tags": ["rapport", "technique", "2024"],
    "custom_metadata": {
      "department": "engineering",
      "project": "alpha"
    },
    "storage_backend": "s3",
    "storage_path": "agent-files/user123/file-uuid-001.pdf",
    "markdown_content": "# Rapport Technique 2024\n\n## Introduction...",
    "markdown_file_id": "file-uuid-001-md",
    "conversion_status": "success",
    "conversion_timestamp": "2024-12-10T10:32:00.000Z",
    "conversion_error": null,
    "has_visual_content": true,
    "image_analysis_result": {
      "charts_detected": 3,
      "tables_detected": 5
    },
    "multimodal_processing_status": "completed",
    "processing_errors": [],
    "processing_warnings": [],
    "total_processing_time_ms": 1250.5,
    "generation_model": null,
    "generation_prompt": null,
    "generation_parameters": null
  }
}
```

### Exemple de Document - Fichier généré par IA

```json
{
  "_id": "file-uuid-002",
  "_source": {
    "file_id": "file-uuid-002",
    "filename": "generated-chart.png",
    "mime_type": "image/png",
    "size_bytes": 45678,
    "created_at": "2024-12-10T11:00:00.000Z",
    "updated_at": "2024-12-10T11:00:00.000Z",
    "user_id": "user123",
    "session_id": "session456",
    "agent_id": "chart-agent-001",
    "is_generated": true,
    "tags": ["chart", "generated", "sales"],
    "custom_metadata": {},
    "storage_backend": "local",
    "storage_path": "files/file-uuid-002.png",
    "markdown_content": null,
    "markdown_file_id": null,
    "conversion_status": "not_attempted",
    "conversion_timestamp": null,
    "conversion_error": null,
    "has_visual_content": true,
    "image_analysis_result": null,
    "multimodal_processing_status": "not_attempted",
    "processing_errors": [],
    "processing_warnings": [],
    "total_processing_time_ms": 850.0,
    "generation_model": "dall-e-3",
    "generation_prompt": "Create a bar chart showing quarterly sales data",
    "generation_parameters": {
      "size": "1024x1024",
      "quality": "standard"
    }
  }
}
```

### Exemples de requêtes

```json
// Trouver tous les fichiers d'un utilisateur
GET agent-files-metadata/_search
{
  "query": {
    "term": { "user_id": "user123" }
  }
}

// Recherche full-text sur le nom de fichier
GET agent-files-metadata/_search
{
  "query": {
    "match": { "filename": "rapport" }
  }
}

// Filtrer par backend de stockage et plage de dates
GET agent-files-metadata/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "storage_backend": "s3" } },
        { "range": { "created_at": { "gte": "2024-01-01" } } }
      ]
    }
  }
}

// Trouver les fichiers générés par l'IA
GET agent-files-metadata/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "is_generated": true } },
        { "term": { "user_id": "user123" } }
      ]
    }
  }
}

// Rechercher par tags
GET agent-files-metadata/_search
{
  "query": {
    "match": { "tags": "rapport technique" }
  }
}

// Filtrer par session et agent
GET agent-files-metadata/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "session_id": "session456" } },
        { "term": { "agent_id": "support-agent-001" } }
      ]
    }
  }
}

// Trouver les fichiers avec erreurs de conversion
GET agent-files-metadata/_search
{
  "query": {
    "term": { "conversion_status": "failed" }
  }
}

// Fichiers avec contenu visuel traité
GET agent-files-metadata/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "has_visual_content": true } },
        { "term": { "multimodal_processing_status": "completed" } }
      ]
    }
  }
}
```

### Notes sur le fallback

Lorsque Elasticsearch est indisponible ou désactivé (`ELASTICSEARCH_ENABLED=false`), les métadonnées de fichiers sont stockées localement dans un répertoire `metadata/` sous forme de fichiers JSON individuels (`{file_id}.json`). Le `MetadataStorageManager` gère automatiquement le basculement via le circuit breaker.

---

## 9. LLM Metrics (`agent-metrics-llm-{date}`)

Stocke les métriques de chaque appel LLM avec rotation quotidienne.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | Automatique | Via `LLMMetricsLogger` après chaque appel LLM |
| Lecture | Non exposé | Accès direct via Kibana ou API ES |

Les métriques sont collectées automatiquement par le `LLMMetricsCollector` intégré dans `LlamaIndexAgent`. Elles ne sont pas exposées via l'API REST mais peuvent être consultées via Kibana ou l'API Elasticsearch directement.

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "model_name": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "agent_id": { "type": "keyword" },
      "api_request_id": { "type": "keyword" },
      "input_tokens": { "type": "integer" },
      "output_tokens": { "type": "integer" },
      "thinking_tokens": { "type": "integer" },
      "total_tokens": { "type": "integer" },
      "duration_ms": { "type": "float" },
      "time_to_first_token_ms": { "type": "float" },
      "tokens_per_second": { "type": "float" },
      "tool_call_count": { "type": "integer" },
      "tool_call_duration_ms": { "type": "float" },
      "is_streaming": { "type": "boolean" },
      "trace_id": { "type": "keyword" },
      "span_id": { "type": "keyword" }
    }
  }
}
```

### Description des champs

| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Timestamp de début de l'appel LLM |
| `model_name` | keyword | Nom du modèle utilisé (ex: `gpt-5-mini`, `claude-sonnet-4`) |
| `session_id` | keyword | ID de la session associée |
| `agent_id` | keyword | ID de l'agent qui a fait l'appel |
| `api_request_id` | keyword | ID de la requête API pour corrélation |
| `input_tokens` | integer | Nombre de tokens en entrée |
| `output_tokens` | integer | Nombre de tokens en sortie |
| `thinking_tokens` | integer | Nombre de tokens de réflexion (modèles avec thinking) |
| `total_tokens` | integer | Total des tokens (input + output + thinking) |
| `duration_ms` | float | Durée totale de l'appel LLM en ms |
| `time_to_first_token_ms` | float | Temps jusqu'au premier token (streaming) |
| `tokens_per_second` | float | Débit de génération (output_tokens / duration) |
| `tool_call_count` | integer | Nombre d'appels d'outils pendant l'appel |
| `tool_call_duration_ms` | float | Durée totale des appels d'outils |
| `is_streaming` | boolean | Indique si l'appel était en mode streaming |
| `trace_id` | keyword | ID de trace OpenTelemetry |
| `span_id` | keyword | ID de span OpenTelemetry |

### Exemple de Document

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "@timestamp": "2024-12-10T10:30:15.000Z",
    "model_name": "gpt-5-mini",
    "session_id": "session456",
    "agent_id": "support-agent-001",
    "api_request_id": "req-abc-123",
    "input_tokens": 150,
    "output_tokens": 320,
    "thinking_tokens": 0,
    "total_tokens": 470,
    "duration_ms": 2450.5,
    "time_to_first_token_ms": 180.2,
    "tokens_per_second": 130.6,
    "tool_call_count": 1,
    "tool_call_duration_ms": 450.0,
    "is_streaming": true,
    "trace_id": "abc123def456",
    "span_id": "span789"
  }
}
```

### Exemples de requêtes

```json
// Métriques moyennes par modèle
GET agent-metrics-llm-*/_search
{
  "size": 0,
  "aggs": {
    "by_model": {
      "terms": { "field": "model_name" },
      "aggs": {
        "avg_duration": { "avg": { "field": "duration_ms" } },
        "avg_tokens": { "avg": { "field": "total_tokens" } },
        "avg_throughput": { "avg": { "field": "tokens_per_second" } }
      }
    }
  }
}

// Appels LLM les plus lents
GET agent-metrics-llm-*/_search
{
  "size": 10,
  "sort": [{ "duration_ms": "desc" }],
  "query": {
    "range": { "@timestamp": { "gte": "now-1h" } }
  }
}
```

---

## 10. API Timing Metrics (`agent-metrics-api-{date}`)

Stocke les métriques de timing end-to-end des requêtes API avec rotation quotidienne.

### Endpoints associés

| Action | Endpoint | Description |
|--------|----------|-------------|
| Création | Automatique | Via `APITimingMiddleware` pour chaque requête |
| Lecture | Non exposé | Accès direct via Kibana ou API ES |

Les métriques sont collectées automatiquement par le middleware FastAPI `APITimingMiddleware`. Elles permettent d'analyser la performance de bout en bout des requêtes API.

### Mapping Elasticsearch

```json
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "request_id": { "type": "keyword" },
      "endpoint": { "type": "keyword" },
      "method": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "is_streaming": { "type": "boolean" },
      "total_api_duration_ms": { "type": "float" },
      "preprocessing_duration_ms": { "type": "float" },
      "llm_duration_ms": { "type": "float" },
      "postprocessing_duration_ms": { "type": "float" },
      "time_to_first_chunk_ms": { "type": "float" },
      "llm_call_count": { "type": "integer" },
      "total_llm_duration_ms": { "type": "float" },
      "llm_percentage": { "type": "float" },
      "overhead_ms": { "type": "float" }
    }
  }
}
```

### Description des champs

| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Timestamp de début de la requête |
| `request_id` | keyword | ID unique de la requête pour corrélation |
| `endpoint` | keyword | Chemin de l'endpoint (ex: `/message`, `/stream`) |
| `method` | keyword | Méthode HTTP (GET, POST, etc.) |
| `session_id` | keyword | ID de la session associée |
| `user_id` | keyword | ID de l'utilisateur |
| `is_streaming` | boolean | Indique si la réponse était en streaming |
| `total_api_duration_ms` | float | Durée totale de la requête API |
| `preprocessing_duration_ms` | float | Temps avant le premier appel LLM |
| `llm_duration_ms` | float | Durée du dernier appel LLM |
| `postprocessing_duration_ms` | float | Temps après le dernier appel LLM |
| `time_to_first_chunk_ms` | float | Temps jusqu'au premier chunk (streaming) |
| `llm_call_count` | integer | Nombre d'appels LLM dans la requête |
| `total_llm_duration_ms` | float | Durée totale de tous les appels LLM |
| `llm_percentage` | float | Pourcentage du temps passé dans les LLM |
| `overhead_ms` | float | Overhead non-LLM (preprocessing + postprocessing) |

### Exemple de Document

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "@timestamp": "2024-12-10T10:30:15.000Z",
    "request_id": "req-abc-123",
    "endpoint": "/message",
    "method": "POST",
    "session_id": "session456",
    "user_id": "user123",
    "is_streaming": false,
    "total_api_duration_ms": 3250.5,
    "preprocessing_duration_ms": 150.2,
    "llm_duration_ms": 2450.5,
    "postprocessing_duration_ms": 649.8,
    "time_to_first_chunk_ms": null,
    "llm_call_count": 1,
    "total_llm_duration_ms": 2450.5,
    "llm_percentage": 75.4,
    "overhead_ms": 800.0
  }
}
```

### Exemple de Document - Streaming

```json
{
  "_id": "auto-generated-id",
  "_source": {
    "@timestamp": "2024-12-10T10:35:00.000Z",
    "request_id": "req-def-456",
    "endpoint": "/stream",
    "method": "POST",
    "session_id": "session456",
    "user_id": "user123",
    "is_streaming": true,
    "total_api_duration_ms": 5200.0,
    "preprocessing_duration_ms": 120.5,
    "llm_duration_ms": 4800.0,
    "postprocessing_duration_ms": 279.5,
    "time_to_first_chunk_ms": 350.2,
    "llm_call_count": 1,
    "total_llm_duration_ms": 4800.0,
    "llm_percentage": 92.3,
    "overhead_ms": 400.0
  }
}
```

### Exemples de requêtes

```json
// Performance moyenne par endpoint
GET agent-metrics-api-*/_search
{
  "size": 0,
  "aggs": {
    "by_endpoint": {
      "terms": { "field": "endpoint" },
      "aggs": {
        "avg_duration": { "avg": { "field": "total_api_duration_ms" } },
        "avg_llm_percentage": { "avg": { "field": "llm_percentage" } },
        "p95_duration": { "percentiles": { "field": "total_api_duration_ms", "percents": [95] } }
      }
    }
  }
}

// Requêtes avec overhead élevé (>30%)
GET agent-metrics-api-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "llm_percentage": { "lt": 70 } } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "sort": [{ "overhead_ms": "desc" }]
}

// Corrélation API + LLM metrics
GET agent-metrics-api-*,agent-metrics-llm-*/_search
{
  "query": {
    "term": { "request_id": "req-abc-123" }
  }
}
```

### Variables d'environnement

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `METRICS_ENABLED` | `true` | Active la collecte de métriques |
| `METRICS_INDEX_PREFIX` | `agent-metrics` | Préfixe des index de métriques |
| `METRICS_BATCH_SIZE` | `50` | Taille du batch pour l'envoi ES |
| `METRICS_FLUSH_INTERVAL` | `5.0` | Intervalle de flush en secondes |

---

## Circuit Breaker

Toutes les opérations Elasticsearch utilisent un circuit breaker partagé pour la résilience :

- **CLOSED** : Fonctionnement normal
- **OPEN** : Elasticsearch indisponible, fallback activé
- **HALF_OPEN** : Test de reconnexion en cours

En cas d'ouverture du circuit :
- Les logs basculent vers un fichier de fallback
- Les sessions utilisent le stockage mémoire temporaire
- Les configurations utilisent le cache local
- Les métadonnées de fichiers utilisent le stockage local (`metadata/` directory)

