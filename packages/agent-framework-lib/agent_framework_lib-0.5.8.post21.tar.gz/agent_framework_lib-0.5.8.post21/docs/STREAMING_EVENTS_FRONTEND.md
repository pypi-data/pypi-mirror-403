# Guide d'intégration Frontend - Événements de Streaming

Ce document décrit le format des événements de streaming envoyés par l'Agent Framework.

## Vue d'ensemble

L'Agent Framework utilise Server-Sent Events (SSE) pour streamer les événements en temps réel. Chaque événement contient des métadonnées d'affichage (`display_info`) permettant de rendre des noms conviviaux et des icônes.

### Technical Details Stripping

Les activités stockées dans Elasticsearch contiennent un champ `technical_details` avec les données techniques brutes (nom de fonction, arguments, résultat brut, temps d'exécution). Ce champ est **automatiquement supprimé** avant l'envoi au frontend, que ce soit en streaming ou lors du chargement de l'historique.

Cela signifie que les frontends ne verront jamais le champ `technical_details` - ils reçoivent uniquement les informations user-friendly dans `display_info` et `content`.

## Format des événements

Chaque ligne SSE contient un préfixe indiquant le type de données :

| Préfixe | Description |
|---------|-------------|
| `__STREAM_CHUNK__` | Fragment de texte de la réponse |
| `__STREAM_ACTIVITY__` | Événement d'activité (JSON) |
| `__STREAM_ROUTING__` | Information de routage du modèle |
| `__STREAM_DONE__` | Fin du streaming |

## Types d'événements d'activité

### 1. `activity` - Activité générale de l'agent

```json
{
    "type": "activity",
    "source": "agent",
    "content": "Agent loop started",
    "timestamp": "2026-01-22T14:30:00.000000",
    "display_info": {
        "id": "activity",
        "friendly_name": "⏳ Activité",
        "description": "Activité de l'agent",
        "icon": "⏳",
        "category": "status",
        "color": null
    }
}
```

### 2. `tool_request` - Appel d'outil

```json
{
    "type": "tool_request",
    "source": "llamaindex_agent",
    "tools": [
        {
            "name": "search_web",
            "arguments": {"query": "météo Paris"},
            "id": "call_abc123"
        }
    ],
    "timestamp": "2026-01-22T14:30:01.000000",
    "display_info": {
        "id": "tool_request",
        "friendly_name": "🔧 Appel d'outil",
        "description": "L'agent appelle un outil",
        "icon": "🔧",
        "category": "tool",
        "color": null
    },
    "tools_display_info": [
        {
            "id": "search_web",
            "friendly_name": "🔍 Recherche web en cours",
            "description": "Recherche d'informations sur le web",
            "icon": "🔍",
            "category": "search",
            "color": null
        }
    ]
}
```

### 3. `tool_request` avec chargement de compétence

Quand l'outil est `load_skill_tool` ou `unload_skill_tool`, un champ `skill_display_info` est ajouté :

```json
{
    "type": "tool_request",
    "source": "llamaindex_agent",
    "tools": [
        {
            "name": "load_skill_tool",
            "arguments": {"skill_name": "chart"},
            "id": "call_xyz789"
        }
    ],
    "timestamp": "2026-01-22T14:30:01.000000",
    "display_info": {
        "id": "tool_request",
        "friendly_name": "🔧 Appel d'outil",
        "icon": "🔧",
        "category": "tool"
    },
    "tools_display_info": [
        {
            "id": "load_skill_tool",
            "friendly_name": "⬇️ Chargement de compétence",
            "description": "Charge une compétence spécifique",
            "icon": "⬇️",
            "category": "skills",
            "skill_display_info": {
                "id": "skill:chart",
                "friendly_name": "📊 Graphiques",
                "description": "Affichage, génération et enregistrement en image des graphiques Chart.js",
                "icon": "📊",
                "category": "skill"
            }
        }
    ]
}
```

### 4. `tool_result` - Résultat d'outil

```json
{
    "type": "tool_result",
    "source": "llamaindex_agent",
    "results": [
        {
            "name": "search_web",
            "content": "Résultats de la recherche...",
            "is_error": false,
            "call_id": "call_abc123"
        }
    ],
    "timestamp": "2026-01-22T14:30:02.000000",
    "display_info": {
        "id": "tool_result",
        "friendly_name": "✅ Résultat",
        "description": "Résultat de l'exécution de l'outil",
        "icon": "✅",
        "category": "tool"
    },
    "results_display_info": [
        {
            "id": "search_web",
            "friendly_name": "🔍 Recherche web en cours",
            "description": "Recherche d'informations sur le web",
            "icon": "🔍",
            "category": "search"
        }
    ]
}
```

### 5. `routing` - Sélection du modèle LLM

```json
{
    "type": "routing",
    "source": "model_router",
    "model": "gpt-4o",
    "provider": "openai",
    "timestamp": "2026-01-22T14:30:00.000000",
    "display_info": {
        "id": "routing",
        "friendly_name": "🔀 Sélection du modèle",
        "description": "Sélection du modèle LLM",
        "icon": "🔀",
        "category": "routing"
    }
}
```

### 6. `error` - Erreur

```json
{
    "type": "error",
    "content": "Description de l'erreur",
    "timestamp": "2026-01-22T14:30:00.000000",
    "display_info": {
        "id": "error",
        "friendly_name": "❌ Erreur",
        "description": "Une erreur s'est produite",
        "icon": "❌",
        "category": "error"
    }
}
```

## Structure `display_info`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Identifiant technique |
| `friendly_name` | string | Nom convivial à afficher |
| `description` | string \| null | Description détaillée |
| `icon` | string \| null | Emoji ou identifiant d'icône |
| `category` | string \| null | Catégorie pour le regroupement |
| `color` | string \| null | Code couleur pour le style |

## Outils disponibles

| Identifiant | Nom convivial | Icône | Catégorie |
|-------------|---------------|-------|-----------|
| `search_web` | Recherche web en cours | 🔍 | search |
| `save_chart_as_image` | Génération du graphique | 📊 | chart |
| `generate_chart` | Génération du graphique | 📈 | chart |
| `read_file` | Lecture du fichier | 📄 | file |
| `write_file` | Écriture du fichier | 💾 | file |
| `list_files` | Récupération de la liste des fichiers | 📁 | file |
| `save_mermaid_as_image` | Génération du diagramme | 🔀 | diagram |
| `save_table_as_image` | Génération du tableau | � | table |
| `create_pdf_from_markdown` | Création du PDF | 📄 | pdf |
| `create_pdf_from_html` | Création du PDF | 📄 | pdf |
| `create_pdf_with_images` | Création du PDF | 📄 | pdf |
| `get_file_path` | Localisation du fichier | 🔗 | file |
| `web_search` | Recherche web | � | search |
| `news_search` | Recherche d'actualités | 📰 | search |
| `describe_image` | Description de l'image | 🖼️ | multimodal |
| `answer_about_image` | Question sur l'image | ❓ | multimodal |
| `extract_text_from_image` | Extraction de texte (OCR) | 📝 | multimodal |
| `analyze_image` | Analyse de l'image | 🔬 | multimodal |
| `list_skills_tool` | Liste des compétences | 📋 | skills |
| `load_skill_tool` | Chargement de compétence | ⬇️ | skills |
| `unload_skill_tool` | Déchargement de compétence | ⬆️ | skills |
| `remember` | Mémorisation | 💾 | memory |
| `recall` | Rappel mémoire | 🔍 | memory |
| `forget` | Oubli | 🗑️ | memory |

## Compétences (Skills) disponibles

| Identifiant | Nom convivial | Description |
|-------------|---------------|-------------|
| `skill:chart` | 📊 Graphiques | Affichage, génération et enregistrement en image des graphiques Chart.js |
| `skill:mermaid` | 🔀 Diagrammes Mermaid | Création de diagrammes (flowcharts, séquences, classes, etc.) |
| `skill:table` | 📋 Tableaux | Affichage et génération d'images de tableaux de données |
| `skill:pdf` | 📄 Génération PDF | Création de documents PDF à partir de Markdown ou HTML |
| `skill:pdf_with_images` | 📄 PDF avec images | Création de PDF avec images intégrées automatiquement |
| `skill:file` | 📁 Gestion de fichiers | Création, lecture et listage de fichiers |
| `skill:file_access` | 🔗 Accès aux fichiers | Obtention des chemins et URLs des fichiers stockés |
| `skill:web_search` | 🔍 Recherche web | Recherche d'informations et d'actualités sur le web |
| `skill:multimodal` | 🖼️ Analyse d'images | Description, OCR et analyse d'images par IA |
| `skill:image_display` | 🖼️ Affichage d'images | Affichage d'images depuis des URLs avec téléchargement |
| `skill:form` | � Formulaires | Génération de formulaires interactifs |
| `skill:optionsblock` | 🔘 Options cliquables | Génération de boutons d'options interactifs |

## API de configuration

Endpoint pour récupérer la configuration complète :

```
GET /api/v1/display-config
GET /api/v1/display-config/{agent_id}
```

Réponse :

```json
{
    "steps": {
        "agent_loop_started": {
            "id": "agent_loop_started",
            "friendly_name": "🤖 Agent en réflexion",
            "description": "L'agent commence à traiter la requête",
            "icon": "🤖",
            "category": "agent"
        }
    },
    "tools": {
        "search_web": {
            "id": "search_web",
            "friendly_name": "🔍 Recherche web en cours",
            "description": "Recherche d'informations sur le web",
            "icon": "🔍",
            "category": "search"
        },
        "skill:chart": {
            "id": "skill:chart",
            "friendly_name": "📊 Graphiques",
            "description": "Affichage, génération et enregistrement en image des graphiques Chart.js",
            "icon": "📊",
            "category": "skill"
        }
    },
    "events": {
        "tool_request": {
            "id": "tool_request",
            "friendly_name": "🔧 Appel d'outil",
            "description": "L'agent appelle un outil",
            "icon": "🔧",
            "category": "tool"
        }
    }
}
```
