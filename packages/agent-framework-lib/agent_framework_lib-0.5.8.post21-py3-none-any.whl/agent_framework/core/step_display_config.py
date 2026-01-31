"""Step display configuration models for the agent framework.

This module provides Pydantic models for configuring display information
for steps, tools, and events in the streaming system. It enables friendly
names, icons, and visual metadata for technical identifiers.
"""

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator


if TYPE_CHECKING:
    from agent_framework.core.elasticsearch_config_provider import ElasticsearchConfigProvider

logger = logging.getLogger(__name__)


class StepDisplayInfo(BaseModel):
    """Display information for a step, tool, or event.

    This model contains all the visual metadata needed to render
    a step, tool, or event in a user-friendly way in the UI.

    Attributes:
        id: Technical identifier (non-empty string).
        friendly_name: User-friendly display name (non-empty string).
        description: Brief description of the step/tool (optional).
        icon: Emoji or icon identifier (defaults to "⚙️").
        category: Category for grouping (defaults to "general").
        color: Color code for UI styling (optional).

    Example:
        >>> info = StepDisplayInfo(
        ...     id="tool_request",
        ...     friendly_name="🔧 Appel d'outil",
        ...     description="L'agent appelle un outil",
        ...     icon="🔧",
        ...     category="tool"
        ... )
    """

    id: str = Field(..., min_length=1, description="Technical identifier")
    friendly_name: str = Field(..., min_length=1, description="User-friendly display name")
    description: str | None = Field(None, description="Brief description of the step/tool")
    icon: str | None = Field("⚙️", description="Emoji or icon identifier")
    category: str | None = Field("general", description="Category for grouping")
    color: str | None = Field(None, description="Color code for UI styling")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that the id is non-empty.

        Args:
            v: The id to validate.

        Returns:
            The validated id.

        Raises:
            ValueError: If the id is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError("id cannot be empty")
        return v

    @field_validator("friendly_name")
    @classmethod
    def validate_friendly_name(cls, v: str) -> str:
        """Validate that the friendly_name is non-empty.

        Args:
            v: The friendly_name to validate.

        Returns:
            The validated friendly_name.

        Raises:
            ValueError: If the friendly_name is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError("friendly_name cannot be empty")
        return v


class StepDisplayConfig(BaseModel):
    """Complete display configuration containing all display mappings.

    This model holds dictionaries mapping technical identifiers to their
    display information for steps, tools, and events.

    Attributes:
        steps: Display info for agent steps, keyed by step identifier.
        tools: Display info for tools, keyed by tool name.
        events: Display info for streaming events, keyed by event type.

    Example:
        >>> config = StepDisplayConfig(
        ...     steps={"thinking": StepDisplayInfo(id="thinking", friendly_name="💭 Réflexion")},
        ...     tools={"search_web": StepDisplayInfo(id="search_web", friendly_name="🔍 Recherche")},
        ...     events={"chunk": StepDisplayInfo(id="chunk", friendly_name="💬 Réponse")}
        ... )
    """

    steps: dict[str, StepDisplayInfo] = Field(
        default_factory=dict, description="Display info for agent steps"
    )
    tools: dict[str, StepDisplayInfo] = Field(
        default_factory=dict, description="Display info for tools"
    )
    events: dict[str, StepDisplayInfo] = Field(
        default_factory=dict, description="Display info for streaming events"
    )


# =============================================================================
# Default Display Configurations
# =============================================================================

DEFAULT_EVENT_DISPLAY: dict[str, StepDisplayInfo] = {
    "tool_request": StepDisplayInfo(
        id="tool_request",
        friendly_name="🔧 Appel d'outil",
        description="L'agent appelle un outil",
        icon="🔧",
        category="tool",
    ),
    "tool_result": StepDisplayInfo(
        id="tool_result",
        friendly_name="✅ Résultat",
        description="Résultat de l'exécution de l'outil",
        icon="✅",
        category="tool",
    ),
    "chunk": StepDisplayInfo(
        id="chunk",
        friendly_name="💬 Réponse",
        description="Fragment de réponse en streaming",
        icon="💬",
        category="response",
    ),
    "activity": StepDisplayInfo(
        id="activity",
        friendly_name="🧠 Raisonnement",
        description="Raisonnement de l'agent",
        icon="🧠",
        category="status",
    ),
    "error": StepDisplayInfo(
        id="error",
        friendly_name="❌ Erreur",
        description="Une erreur s'est produite",
        icon="❌",
        category="error",
    ),
    "routing": StepDisplayInfo(
        id="routing",
        friendly_name="🔀 Sélection du modèle",
        description="Sélection du modèle LLM",
        icon="🔀",
        category="routing",
    ),
    "done": StepDisplayInfo(
        id="done",
        friendly_name="✨ Réflexion terminé",
        description="Traitement terminé",
        icon="✨",
        category="status",
    ),
    "other": StepDisplayInfo(
        id="other",
        friendly_name="⚙️ Événement interne",
        description="Événement interne de l'agent",
        icon="⚙️",
        category="general",
    ),
}
"""Default display information for streaming events.

Maps event types to their display information. These are used when
no custom override is configured for an event type.
"""

DEFAULT_STEP_DISPLAY: dict[str, StepDisplayInfo] = {
    "agent_loop_started": StepDisplayInfo(
        id="agent_loop_started",
        friendly_name="🤖 Agent en réflexion",
        description="L'agent commence à traiter la requête",
        icon="🤖",
        category="agent",
    ),
    "thinking": StepDisplayInfo(
        id="thinking",
        friendly_name="💭 Réflexion",
        description="L'agent réfléchit",
        icon="💭",
        category="agent",
    ),
    "processing": StepDisplayInfo(
        id="processing",
        friendly_name="⚙️ Traitement",
        description="Traitement en cours",
        icon="⚙️",
        category="agent",
    ),
}
"""Default display information for agent steps.

Maps step identifiers to their display information. These are used when
no custom override is configured for a step.
"""

DEFAULT_TOOL_DISPLAY: dict[str, StepDisplayInfo] = {
    # ==========================================================================
    # Web & Search Tools
    # ==========================================================================
    "search_web": StepDisplayInfo(
        id="search_web",
        friendly_name="🔍 Recherche web en cours",
        description="Recherche d'informations sur le web",
        icon="🔍",
        category="search",
    ),
    # ==========================================================================
    # Chart & Visualization Tools
    # ==========================================================================
    "save_chart_as_image": StepDisplayInfo(
        id="save_chart_as_image",
        friendly_name="📊 Génération du graphique",
        description="Sauvegarde d'un graphique en image",
        icon="📊",
        category="chart",
    ),
    "generate_chart": StepDisplayInfo(
        id="generate_chart",
        friendly_name="📈 Génération du graphique",
        description="Génération d'un graphique",
        icon="📈",
        category="chart",
    ),
    # ==========================================================================
    # File Operations Tools
    # ==========================================================================
    "read_file": StepDisplayInfo(
        id="read_file",
        friendly_name="📄 Lecture du fichier",
        description="Lecture du contenu d'un fichier",
        icon="📄",
        category="file",
    ),
    "write_file": StepDisplayInfo(
        id="write_file",
        friendly_name="💾 Écriture du fichier",
        description="Écriture de contenu dans un fichier",
        icon="💾",
        category="file",
    ),
    "list_files": StepDisplayInfo(
        id="list_files",
        friendly_name="📁 Récuration de la liste des fichiers",
        description="Liste des fichiers dans un répertoire",
        icon="📁",
        category="file",
    ),
    "delete_file": StepDisplayInfo(
        id="delete_file",
        friendly_name="🗑️ Suppression du fichier",
        description="Suppression d'un fichier",
        icon="🗑️",
        category="file",
    ),
    "create_file": StepDisplayInfo(
        id="create_file",
        friendly_name="📝 Création du fichier",
        description="Création d'un nouveau fichier",
        icon="📝",
        category="file",
    ),
    # ==========================================================================
    # Code Execution Tools
    # ==========================================================================
    "execute_code": StepDisplayInfo(
        id="execute_code",
        friendly_name="▶️ Exécution du code",
        description="Exécution de code",
        icon="▶️",
        category="code",
    ),
    # ==========================================================================
    # Database Tools
    # ==========================================================================
    "query_database": StepDisplayInfo(
        id="query_database",
        friendly_name="🗄️ Requête dans la base de données",
        description="Exécution d'une requête sur la base de données",
        icon="🗄️",
        category="database",
    ),
    # ==========================================================================
    # Communication Tools
    # ==========================================================================
    "send_email": StepDisplayInfo(
        id="send_email",
        friendly_name="📧 Envoi de l'email",
        description="Envoi d'un email",
        icon="📧",
        category="communication",
    ),
    # ==========================================================================
    # API Tools
    # ==========================================================================
    "call_api": StepDisplayInfo(
        id="call_api",
        friendly_name="🌐 Appel API",
        description="Appel à une API externe",
        icon="🌐",
        category="api",
    ),
    # ==========================================================================
    # Calculator Tools (simple_agent.py, custom_framework_agent.py)
    # ==========================================================================
    "add": StepDisplayInfo(
        id="add",
        friendly_name="➕ Addition",
        description="Additionne deux nombres",
        icon="➕",
        category="calculator",
    ),
    "multiply": StepDisplayInfo(
        id="multiply",
        friendly_name="✖️ Multiplication",
        description="Multiplie deux nombres",
        icon="✖️",
        category="calculator",
    ),
    "divide": StepDisplayInfo(
        id="divide",
        friendly_name="➗ Division",
        description="Divise deux nombres",
        icon="➗",
        category="calculator",
    ),
    # ==========================================================================
    # Memory Tools (agent_with_memory_*.py)
    # ==========================================================================
    "recall_memory": StepDisplayInfo(
        id="recall_memory",
        friendly_name="🧠 Recherche dans la mémoire",
        description="Recherche d'informations en mémoire",
        icon="🧠",
        category="memory",
    ),
    "store_memory": StepDisplayInfo(
        id="store_memory",
        friendly_name="💾 Stockage de l'information en mémoire",
        description="Sauvegarde d'informations en mémoire",
        icon="💾",
        category="memory",
    ),
    "forget_memory": StepDisplayInfo(
        id="forget_memory",
        friendly_name="🗑️ Invalidation d'un fait en mémoire",
        description="Suppression d'informations de la mémoire",
        icon="🗑️",
        category="memory",
    ),
    # ==========================================================================
    # MCP Tools (agent_with_mcp.py)
    # ==========================================================================
    "greet": StepDisplayInfo(
        id="greet",
        friendly_name="👋 Salutation",
        description="Salue un utilisateur par son nom",
        icon="👋",
        category="general",
    ),
    # ==========================================================================
    # Skills Management Tools (skills_demo_agent.py, simple_agent.py)
    # ==========================================================================
    "list_skills": StepDisplayInfo(
        id="list_skills",
        friendly_name="📋 Chargement de la liste des capacités",
        description="Affiche tous les skills disponibles",
        icon="📋",
        category="skills",
    ),
    "load_skill": StepDisplayInfo(
        id="load_skill",
        friendly_name="📥 Chargement de la capacité :",
        description="Charge un skill à la demande",
        icon="📥",
        category="skills",
    ),
    "unload_skill": StepDisplayInfo(
        id="unload_skill",
        friendly_name="📤 DéChargement de la capacité : :",
        description="Décharge un skill pour libérer le contexte",
        icon="📤",
        category="skills",
    ),
    "search_skills": StepDisplayInfo(
        id="search_skills",
        friendly_name="🔎 Recherche d'une capacité",
        description="Recherche de skills par mot-clé",
        icon="🔎",
        category="skills",
    ),
    "get_loaded_skills": StepDisplayInfo(
        id="get_loaded_skills",
        friendly_name="📊 Récupération de la liste des capacités chargés",
        description="Affiche les skills actuellement chargés",
        icon="📊",
        category="skills",
    ),
    "get_skills_summary": StepDisplayInfo(
        id="get_skills_summary",
        friendly_name="📈 Récupération des instructions de la capacité",
        description="Résumé du système de skills",
        icon="📈",
        category="skills",
    ),
    # ==========================================================================
    # Mermaid Diagram Tools (MermaidToImageTool)
    # ==========================================================================
    "save_mermaid_as_image": StepDisplayInfo(
        id="save_mermaid_as_image",
        friendly_name="🔀 Génération du diagramme",
        description="Convertit un diagramme Mermaid en image PNG",
        icon="🔀",
        category="diagram",
    ),
    # ==========================================================================
    # Table Tools (TableToImageTool)
    # ==========================================================================
    "save_table_as_image": StepDisplayInfo(
        id="save_table_as_image",
        friendly_name="📋 Génération du tableau",
        description="Convertit des données tabulaires en image PNG",
        icon="📋",
        category="table",
    ),
    # ==========================================================================
    # PDF Generation Tools (CreatePDFFromMarkdownTool, CreatePDFFromHTMLTool)
    # ==========================================================================
    "create_pdf_from_markdown": StepDisplayInfo(
        id="create_pdf_from_markdown",
        friendly_name="📄 Création du PDF",
        description="Génère un PDF à partir de contenu Markdown",
        icon="📄",
        category="pdf",
    ),
    "create_pdf_from_html": StepDisplayInfo(
        id="create_pdf_from_html",
        friendly_name="📄 Création du PDF",
        description="Génère un PDF à partir de contenu HTML",
        icon="📄",
        category="pdf",
    ),
    "create_pdf_with_images": StepDisplayInfo(
        id="create_pdf_with_images",
        friendly_name="📄 Création du PDF",
        description="Génère un PDF avec images intégrées automatiquement",
        icon="📄",
        category="pdf",
    ),
    # ==========================================================================
    # File Access Tools (GetFilePathTool)
    # ==========================================================================
    "get_file_path": StepDisplayInfo(
        id="get_file_path",
        friendly_name="🔗 Localisation du fichier",
        description="Obtient le chemin ou l'URL d'un fichier stocké",
        icon="🔗",
        category="file",
    ),
    # ==========================================================================
    # Web Search Tools (WebSearchTool, WebNewsSearchTool)
    # ==========================================================================
    "web_search": StepDisplayInfo(
        id="web_search",
        friendly_name="🔍 Recherche web",
        description="Recherche d'informations sur le web via DuckDuckGo",
        icon="🔍",
        category="search",
    ),
    "news_search": StepDisplayInfo(
        id="news_search",
        friendly_name="📰 Recherche d'actualités",
        description="Recherche d'articles d'actualité récents",
        icon="📰",
        category="search",
    ),
    # ==========================================================================
    # Multimodal Image Analysis Tools (ImageAnalysisTool)
    # ==========================================================================
    "describe_image": StepDisplayInfo(
        id="describe_image",
        friendly_name="🖼️ Description de l'image",
        description="Génère une description détaillée de l'image",
        icon="🖼️",
        category="multimodal",
    ),
    "answer_about_image": StepDisplayInfo(
        id="answer_about_image",
        friendly_name="❓ Question sur l'image",
        description="Répond à une question spécifique sur l'image",
        icon="❓",
        category="multimodal",
    ),
    "extract_text_from_image": StepDisplayInfo(
        id="extract_text_from_image",
        friendly_name="📝 Extraction de texte (OCR)",
        description="Extrait le texte visible dans l'image",
        icon="📝",
        category="multimodal",
    ),
    "analyze_image": StepDisplayInfo(
        id="analyze_image",
        friendly_name="🔬 Analyse de l'image",
        description="Analyse complète du contenu de l'image",
        icon="🔬",
        category="multimodal",
    ),
    # ==========================================================================
    # Skills Management Tools
    # ==========================================================================
    "list_skills_tool": StepDisplayInfo(
        id="list_skills_tool",
        friendly_name="📋 Liste des compétences",
        description="Liste les compétences disponibles",
        icon="📋",
        category="skills",
    ),
    "load_skill_tool": StepDisplayInfo(
        id="load_skill_tool",
        friendly_name="⬇️ Chargement de compétence",
        description="Charge une compétence spécifique",
        icon="⬇️",
        category="skills",
    ),
    "unload_skill_tool": StepDisplayInfo(
        id="unload_skill_tool",
        friendly_name="⬆️ Déchargement de compétence",
        description="Décharge une compétence",
        icon="⬆️",
        category="skills",
    ),
    # ==========================================================================
    # Memory Tools
    # ==========================================================================
    "remember": StepDisplayInfo(
        id="remember",
        friendly_name="💾 Mémorisation",
        description="Enregistre une information en mémoire",
        icon="💾",
        category="memory",
    ),
    "recall": StepDisplayInfo(
        id="recall",
        friendly_name="🔍 Rappel mémoire",
        description="Recherche dans la mémoire",
        icon="🔍",
        category="memory",
    ),
    "forget": StepDisplayInfo(
        id="forget",
        friendly_name="🗑️ Oubli",
        description="Supprime une information de la mémoire",
        icon="🗑️",
        category="memory",
    ),
    # ==========================================================================
    # Skill Names (for display when loading/unloading skills)
    # Format: skill:<skill_name> -> friendly display name
    # ==========================================================================
    "skill:chart": StepDisplayInfo(
        id="skill:chart",
        friendly_name="📊 Génération des graphiques",
        description="Affichage, génération et enregistrement en image des graphiques Chart.js",
        icon="📊",
        category="skill",
    ),
    "skill:mermaid": StepDisplayInfo(
        id="skill:mermaid",
        friendly_name="🔀 Génération des diagrammes gantt, timeline, flowchart, mindmap...",
        description="Création, affichage et enregistrement en image de diagrammes flowcharts, séquences, classes, gantt etc.)",
        icon="🔀",
        category="skill",
    ),
    "skill:table": StepDisplayInfo(
        id="skill:table",
        friendly_name="📋 Génération de Tableaux",
        description="Affichage et génération d'images de tableaux de données",
        icon="📋",
        category="skill",
    ),
    "skill:pdf": StepDisplayInfo(
        id="skill:pdf",
        friendly_name="📄 Génération de PDF",
        description="Création de documents PDF à partir de Markdown ou HTML",
        icon="📄",
        category="skill",
    ),
    "skill:pdf_with_images": StepDisplayInfo(
        id="skill:pdf_with_images",
        friendly_name="📄 Génération de PDF avec des images",
        description="Création de PDF avec images intégrées automatiquement",
        icon="📄",
        category="skill",
    ),
    "skill:file": StepDisplayInfo(
        id="skill:file",
        friendly_name="📁 Gestion de fichiers",
        description="Création, lecture et listage de fichiers",
        icon="📁",
        category="skill",
    ),
    "skill:file_access": StepDisplayInfo(
        id="skill:file_access",
        friendly_name="🔗 Accès aux fichiers",
        description="Obtention des chemins et URLs des fichiers stockés",
        icon="🔗",
        category="skill",
    ),
    "skill:web_search": StepDisplayInfo(
        id="skill:web_search",
        friendly_name="🔍 Recherche sur Internet",
        description="Recherche d'informations et d'actualités sur le web",
        icon="🔍",
        category="skill",
    ),
    "skill:multimodal": StepDisplayInfo(
        id="skill:multimodal",
        friendly_name="🖼️ Analyse d'images",
        description="Description, OCR et analyse d'images par IA",
        icon="🖼️",
        category="skill",
    ),
    "skill:image_display": StepDisplayInfo(
        id="skill:image_display",
        friendly_name="🖼️ Affichage d'images",
        description="Affichage d'images depuis des URLs avec téléchargement",
        icon="🖼️",
        category="skill",
    ),
    "skill:form": StepDisplayInfo(
        id="skill:form",
        friendly_name="📝 Création de formulaires",
        description="Génération de formulaires interactifs",
        icon="📝",
        category="skill",
    ),
    "skill:optionsblock": StepDisplayInfo(
        id="skill:optionsblock",
        friendly_name="🔘 Options de réponses cliquables",
        description="Génération de boutons d'options interactifs",
        icon="🔘",
        category="skill",
    ),
    "skill:unified_pdf": StepDisplayInfo(
        id="skill:unified_pdf",
        friendly_name="📄 Génération de PDF unifié",
        description="Création de PDF avec images intégrées automatiquement",
        icon="📄",
        category="skill",
    ),
    # ==========================================================================
    # Diagram Type-Specific Configurations (Mermaid)
    # ==========================================================================
    "diagram_gantt": StepDisplayInfo(
        id="diagram_gantt",
        friendly_name="📊 Génération de diagramme Gantt",
        description="Enregistrement en image d'un diagramme généré",
        icon="📊",
        category="diagram",
    ),
    "diagram_mindmap": StepDisplayInfo(
        id="diagram_mindmap",
        friendly_name="🧠 Génération de diagramme Mind Map",
        description="Enregistrement en image d'un diagramme généré",
        icon="🧠",
        category="diagram",
    ),
    "diagram_flowchart": StepDisplayInfo(
        id="diagram_flowchart",
        friendly_name="🔀 Génération de diagramme Flowchart",
        description="Enregistrement en image d'un diagramme généré",
        icon="🔀",
        category="diagram",
    ),
    "diagram_sequence": StepDisplayInfo(
        id="diagram_sequence",
        friendly_name="📋 Génération de diagramme Séquence",
        description="Enregistrement en image d'un diagramme généré",
        icon="📋",
        category="diagram",
    ),
    "diagram_class": StepDisplayInfo(
        id="diagram_class",
        friendly_name="📦 Génération de diagramme Classe",
        description="Enregistrement en image d'un diagramme généré",
        icon="📦",
        category="diagram",
    ),
    "diagram_state": StepDisplayInfo(
        id="diagram_state",
        friendly_name="🔄 Génération de diagramme État",
        description="Enregistrement en image d'un diagramme généré",
        icon="🔄",
        category="diagram",
    ),
    "diagram_er": StepDisplayInfo(
        id="diagram_er",
        friendly_name="🔗 Génération de diagramme Entité-Relation",
        description="Enregistrement en image d'un diagramme généré",
        icon="🔗",
        category="diagram",
    ),
    "diagram_pie": StepDisplayInfo(
        id="diagram_pie",
        friendly_name="🥧 Génération de diagramme Camembert",
        description="Enregistrement en image d'un diagramme généré",
        icon="🥧",
        category="diagram",
    ),
    "diagram_journey": StepDisplayInfo(
        id="diagram_journey",
        friendly_name="🚶 Génération de diagramme Parcours",
        description="Enregistrement en image d'un diagramme généré",
        icon="🚶",
        category="diagram",
    ),
    "diagram_timeline": StepDisplayInfo(
        id="diagram_timeline",
        friendly_name="📅 Génération de diagramme Timeline",
        description="Enregistrement en image d'un diagramme généré",
        icon="📅",
        category="diagram",
    ),
    "diagram_quadrant": StepDisplayInfo(
        id="diagram_quadrant",
        friendly_name="📐 Génération de diagramme Quadrant",
        description="Enregistrement en image d'un diagramme généré",
        icon="📐",
        category="diagram",
    ),
    "diagram_requirement": StepDisplayInfo(
        id="diagram_requirement",
        friendly_name="📝 Génération de diagramme Exigences",
        description="Enregistrement en image d'un diagramme généré",
        icon="📝",
        category="diagram",
    ),
    "diagram_gitgraph": StepDisplayInfo(
        id="diagram_gitgraph",
        friendly_name="🌳 Génération de diagramme Git",
        description="Enregistrement en image d'un diagramme généré",
        icon="🌳",
        category="diagram",
    ),
    "diagram_c4context": StepDisplayInfo(
        id="diagram_c4context",
        friendly_name="🏗️ Génération de diagramme C4 Context",
        description="Enregistrement en image d'un diagramme généré",
        icon="🏗️",
        category="diagram",
    ),
    "diagram_sankey": StepDisplayInfo(
        id="diagram_sankey",
        friendly_name="📈 Génération de diagramme Sankey",
        description="Enregistrement en image d'un diagramme généré",
        icon="📈",
        category="diagram",
    ),
    "diagram_block": StepDisplayInfo(
        id="diagram_block",
        friendly_name="🧱 Génération de diagramme Block",
        description="Enregistrement en image d'un diagramme généré",
        icon="🧱",
        category="diagram",
    ),
    "diagram_packet": StepDisplayInfo(
        id="diagram_packet",
        friendly_name="📦 Génération de diagramme Packet",
        description="Enregistrement en image d'un diagramme généré",
        icon="📦",
        category="diagram",
    ),
    "diagram_architecture": StepDisplayInfo(
        id="diagram_architecture",
        friendly_name="🏛️ Génération de diagramme Architecture",
        description="Enregistrement en image d'un diagramme généré",
        icon="🏛️",
        category="diagram",
    ),
    # ==========================================================================
    # Chart Type-Specific Configurations (Chart.js)
    # ==========================================================================
    "chart_bar": StepDisplayInfo(
        id="chart_bar",
        friendly_name="📊 Génération de graphique barres",
        description="Enregistrement en image d'un graphique généré",
        icon="📊",
        category="chart",
    ),
    "chart_line": StepDisplayInfo(
        id="chart_line",
        friendly_name="📈 Génération de graphique courbes",
        description="Enregistrement en image d'un graphique généré",
        icon="📈",
        category="chart",
    ),
    "chart_pie": StepDisplayInfo(
        id="chart_pie",
        friendly_name="🥧 Génération de graphique camembert",
        description="Enregistrement en image d'un graphique généré",
        icon="🥧",
        category="chart",
    ),
    "chart_doughnut": StepDisplayInfo(
        id="chart_doughnut",
        friendly_name="🍩 Génération de graphique anneau",
        description="Enregistrement en image d'un graphique généré",
        icon="🍩",
        category="chart",
    ),
    "chart_radar": StepDisplayInfo(
        id="chart_radar",
        friendly_name="📡 Génération de graphique radar",
        description="Enregistrement en image d'un graphique généré",
        icon="📡",
        category="chart",
    ),
    "chart_scatter": StepDisplayInfo(
        id="chart_scatter",
        friendly_name="⚬ Génération de graphique nuage de points",
        description="Enregistrement en image d'un graphique généré",
        icon="⚬",
        category="chart",
    ),
    "chart_bubble": StepDisplayInfo(
        id="chart_bubble",
        friendly_name="🫧 Génération de graphique bulles",
        description="Enregistrement en image d'un graphique généré",
        icon="🫧",
        category="chart",
    ),
    "chart_polararea": StepDisplayInfo(
        id="chart_polararea",
        friendly_name="🎯 Génération de graphique aire polaire",
        description="Enregistrement en image d'un graphique généré",
        icon="🎯",
        category="chart",
    ),
    "chart_horizontalbar": StepDisplayInfo(
        id="chart_horizontalbar",
        friendly_name="📊 Génération de graphique barres horizontales",
        description="Enregistrement en image d'un graphique généré",
        icon="📊",
        category="chart",
    ),
    # ==========================================================================
    # Skill Loading Consolidated
    # ==========================================================================
    "skill_loading": StepDisplayInfo(
        id="skill_loading",
        friendly_name="📥 Recherche et chargement de capacité",
        description="Recherche et charge une capacité spécifique",
        icon="📥",
        category="skills",
    ),
}
"""Default display information for common tools.

Maps tool names to their display information. These are used when
no custom override is configured for a tool and the tool does not
provide its own display info via get_display_info().
"""


# =============================================================================
# DisplayConfigManager
# =============================================================================


class DisplayConfigManager:
    """Manages display configuration with optional Elasticsearch persistence.

    This class provides centralized management of display information for steps,
    tools, and events. It supports optional persistence via ElasticsearchConfigProvider,
    benefiting from versioning, LRU cache, and circuit breaker patterns.

    The manager resolves display information with the following priority:
    1. Tool-provided display info (via get_display_info())
    2. Agent-specific overrides
    3. Default configurations
    4. Fallback (technical name as friendly name)

    Attributes:
        _defaults: Built-in default display configurations.
        _memory_overrides: In-memory fallback storage when ES is unavailable.
        _config_provider: Optional ElasticsearchConfigProvider for persistence.

    Example:
        >>> manager = DisplayConfigManager()
        >>> await manager.initialize()
        >>> info = manager.get_display_info("tool", "search_web")
        >>> print(info.friendly_name)
        🔍 Recherche web
    """

    def __init__(self, config_provider: "ElasticsearchConfigProvider | None" = None) -> None:
        """Initialize the DisplayConfigManager.

        Args:
            config_provider: Optional ElasticsearchConfigProvider for persistence.
                If not provided, the manager will use in-memory storage only.
        """
        self._defaults = StepDisplayConfig(
            steps=DEFAULT_STEP_DISPLAY.copy(),
            tools=DEFAULT_TOOL_DISPLAY.copy(),
            events=DEFAULT_EVENT_DISPLAY.copy(),
        )
        self._memory_overrides: dict[str, StepDisplayConfig] = {}
        self._config_provider = config_provider

        logger.info(
            f"[DisplayConfigManager] Initialized "
            f"(es_provider={'enabled' if config_provider else 'disabled'})"
        )

    async def initialize(self) -> None:
        """Initialize the manager.

        Uses the existing ElasticsearchConfigProvider if available.
        This method should be called after construction to ensure
        the provider is properly initialized.
        """
        if self._config_provider is not None:
            try:
                await self._config_provider.initialize()
                logger.info("[DisplayConfigManager] ElasticsearchConfigProvider initialized")
            except Exception as e:
                logger.warning(
                    f"[DisplayConfigManager] Failed to initialize ES provider: {e}. "
                    "Falling back to memory storage."
                )

    def register_agent_tool_display_info(
        self, agent_id: str, custom_display_info: dict[str, Any]
    ) -> None:
        """Register custom tool display info from an agent.

        This method allows agents to provide friendly names for their custom tools
        (e.g., MCP tools) that are not in DEFAULT_TOOL_DISPLAY.

        Args:
            agent_id: The agent identifier.
            custom_display_info: Dictionary mapping tool names to display info dicts.
                Each dict should have: id, friendly_name, and optionally icon, description, category.

        Example:
            >>> manager.register_agent_tool_display_info("athena-agent", {
            ...     "run_query": {
            ...         "id": "run_query",
            ...         "friendly_name": "🔍 Exécution de requête SQL",
            ...         "icon": "🔍",
            ...         "category": "database",
            ...     }
            ... })
        """
        if not custom_display_info:
            return

        # Get or create overrides for this agent
        if agent_id not in self._memory_overrides:
            self._memory_overrides[agent_id] = StepDisplayConfig(
                steps={}, tools={}, events={}
            )

        # Convert dict entries to StepDisplayInfo and add to tools
        for tool_name, info_dict in custom_display_info.items():
            try:
                # Ensure id is set
                if "id" not in info_dict:
                    info_dict["id"] = tool_name
                display_info = StepDisplayInfo(**info_dict)
                self._memory_overrides[agent_id].tools[tool_name] = display_info
                logger.debug(
                    f"[DisplayConfigManager] Registered custom display info for "
                    f"tool '{tool_name}' (agent_id={agent_id})"
                )
            except Exception as e:
                logger.warning(
                    f"[DisplayConfigManager] Invalid custom display info for "
                    f"tool '{tool_name}': {e}"
                )

        logger.info(
            f"[DisplayConfigManager] Registered {len(custom_display_info)} custom tool(s) "
            f"for agent_id={agent_id}"
        )

    def get_display_info(
        self,
        item_type: str,
        item_id: str,
        agent_id: str | None = None,
        tool_provided: StepDisplayInfo | None = None,
    ) -> StepDisplayInfo:
        """Get display info with priority resolution.

        Resolves display information with the following priority:
        1. tool_provided (if not None)
        2. Agent-specific overrides (if agent_id provided)
        3. Default configurations
        4. Fallback (technical name as friendly name)

        Args:
            item_type: Type of item - "step", "tool", or "event".
            item_id: Technical identifier (e.g., "save_chart_as_image", "tool_request").
            agent_id: Optional agent identifier for agent-specific overrides.
            tool_provided: Optional display info provided by the tool itself.

        Returns:
            StepDisplayInfo with resolved display information.

        Example:
            >>> info = manager.get_display_info("tool", "search_web", agent_id="my-agent")
            >>> print(info.friendly_name)
            🔍 Recherche web
        """
        # Priority 1: Tool-provided display info
        if tool_provided is not None:
            logger.debug(
                f"[DisplayConfigManager] Using tool-provided display info for {item_type}/{item_id}"
            )
            return tool_provided

        # Priority 2: Agent-specific overrides
        if agent_id is not None and agent_id in self._memory_overrides:
            overrides = self._memory_overrides[agent_id]
            override_info = self._get_from_config(overrides, item_type, item_id)
            if override_info is not None:
                logger.debug(
                    f"[DisplayConfigManager] Using override for {item_type}/{item_id} "
                    f"(agent_id={agent_id})"
                )
                return override_info

        # Priority 3: Default configurations
        default_info = self._get_from_config(self._defaults, item_type, item_id)
        if default_info is not None:
            logger.debug(f"[DisplayConfigManager] Using default for {item_type}/{item_id}")
            return default_info

        # Priority 4: Fallback - use technical name as friendly name
        logger.debug(f"[DisplayConfigManager] Using fallback for unknown {item_type}/{item_id}")
        return StepDisplayInfo(
            id=item_id,
            friendly_name=item_id,
            description=None,
            icon="⚙️",
            category="general",
            color=None,
        )

    def _get_from_config(
        self, config: StepDisplayConfig, item_type: str, item_id: str
    ) -> StepDisplayInfo | None:
        """Get display info from a configuration by type and id.

        Args:
            config: The StepDisplayConfig to search in.
            item_type: Type of item - "step", "tool", or "event".
            item_id: Technical identifier.

        Returns:
            StepDisplayInfo if found, None otherwise.
        """
        if item_type == "step":
            return config.steps.get(item_id)
        elif item_type == "tool":
            return config.tools.get(item_id)
        elif item_type == "event":
            return config.events.get(item_id)
        else:
            logger.warning(f"[DisplayConfigManager] Unknown item_type: {item_type}")
            return None

    async def get_merged_config(self, agent_id: str | None = None) -> StepDisplayConfig:
        """Get merged configuration (defaults + agent overrides).

        If agent_id is provided and ES is available, loads display_config
        from the agent config via ElasticsearchConfigProvider.

        Args:
            agent_id: Optional agent identifier for agent-specific overrides.

        Returns:
            StepDisplayConfig with merged configuration.

        Example:
            >>> config = await manager.get_merged_config(agent_id="my-agent")
            >>> print(config.tools.keys())
        """
        # Start with defaults
        merged = StepDisplayConfig(
            steps=self._defaults.steps.copy(),
            tools=self._defaults.tools.copy(),
            events=self._defaults.events.copy(),
        )

        if agent_id is None:
            return merged

        # Try to get overrides from ES first
        overrides = await self._load_overrides(agent_id)

        if overrides is not None:
            # Merge overrides into defaults
            merged.steps.update(overrides.steps)
            merged.tools.update(overrides.tools)
            merged.events.update(overrides.events)
            logger.debug(f"[DisplayConfigManager] Merged overrides for agent_id={agent_id}")

        return merged

    async def _load_overrides(self, agent_id: str) -> StepDisplayConfig | None:
        """Load overrides for an agent from ES or memory.

        Args:
            agent_id: Agent identifier.

        Returns:
            StepDisplayConfig with overrides if found, None otherwise.
        """
        # Try ES first if available
        if self._config_provider is not None and self._config_provider.client is not None:
            try:
                agent_config = await self._config_provider.get_agent_config(agent_id)
                if agent_config is not None and "display_config" in agent_config:
                    display_config_data = agent_config["display_config"]
                    return self._parse_display_config(display_config_data)
            except Exception as e:
                logger.warning(
                    f"[DisplayConfigManager] Failed to load overrides from ES "
                    f"for agent_id={agent_id}: {e}"
                )

        # Fallback to memory
        return self._memory_overrides.get(agent_id)

    def _parse_display_config(self, data: dict[str, Any]) -> StepDisplayConfig:
        """Parse display config data from ES into StepDisplayConfig.

        Args:
            data: Raw display config data from Elasticsearch.

        Returns:
            Parsed StepDisplayConfig.
        """
        steps: dict[str, StepDisplayInfo] = {}
        tools: dict[str, StepDisplayInfo] = {}
        events: dict[str, StepDisplayInfo] = {}

        for key, value in data.get("steps", {}).items():
            try:
                steps[key] = StepDisplayInfo(**value)
            except Exception as e:
                logger.warning(f"[DisplayConfigManager] Invalid step config for {key}: {e}")

        for key, value in data.get("tools", {}).items():
            try:
                tools[key] = StepDisplayInfo(**value)
            except Exception as e:
                logger.warning(f"[DisplayConfigManager] Invalid tool config for {key}: {e}")

        for key, value in data.get("events", {}).items():
            try:
                events[key] = StepDisplayInfo(**value)
            except Exception as e:
                logger.warning(f"[DisplayConfigManager] Invalid event config for {key}: {e}")

        return StepDisplayConfig(steps=steps, tools=tools, events=events)

    async def set_overrides(self, agent_id: str, overrides: StepDisplayConfig) -> bool:
        """Set display overrides for an agent.

        If ES is available, updates the display_config field in the agent's
        existing configuration (creates a new version). Otherwise, stores
        in memory.

        Args:
            agent_id: Agent identifier.
            overrides: Display configuration overrides to set.

        Returns:
            True if overrides were saved successfully, False otherwise.

        Example:
            >>> overrides = StepDisplayConfig(
            ...     tools={"my_tool": StepDisplayInfo(id="my_tool", friendly_name="My Tool")}
            ... )
            >>> success = await manager.set_overrides("my-agent", overrides)
        """
        if self._config_provider is not None and self._config_provider.client is not None:
            try:
                # Get current config
                current_config = await self._config_provider.get_agent_config(agent_id)

                # Add/update display_config
                updated_config = current_config or {}
                updated_config["display_config"] = overrides.model_dump()

                # Save with automatic versioning
                result = await self._config_provider.update_agent_config(
                    agent_id=agent_id,
                    config=updated_config,
                    updated_by="display-config-api",
                )

                if result is not None:
                    logger.info(
                        f"[DisplayConfigManager] Saved overrides to ES for agent_id={agent_id} "
                        f"(version={result.get('version')})"
                    )
                    # Also update memory cache for immediate access
                    self._memory_overrides[agent_id] = overrides
                    return True
                else:
                    logger.warning(
                        f"[DisplayConfigManager] Failed to save overrides to ES "
                        f"for agent_id={agent_id}"
                    )
                    # Fallback to memory
                    self._memory_overrides[agent_id] = overrides
                    return True

            except Exception as e:
                logger.error(
                    f"[DisplayConfigManager] Error saving overrides to ES "
                    f"for agent_id={agent_id}: {e}"
                )
                # Fallback to memory
                self._memory_overrides[agent_id] = overrides
                return True
        else:
            # Memory fallback
            self._memory_overrides[agent_id] = overrides
            logger.info(f"[DisplayConfigManager] Saved overrides to memory for agent_id={agent_id}")
            return True


# =============================================================================
# Helper Functions
# =============================================================================


def enrich_event_with_display_info(
    event: dict[str, Any],
    manager: DisplayConfigManager,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Enrich a streaming event with display information.

    This function adds display metadata to streaming events, enabling
    frontends to render user-friendly names and icons without maintaining
    separate mappings.

    The function is backward compatible - it creates a copy of the event
    and adds new fields without modifying the original event structure.

    Args:
        event: The streaming event dictionary to enrich.
        manager: DisplayConfigManager instance for resolving display info.
        agent_id: Optional agent identifier for agent-specific overrides.

    Returns:
        The enriched event dictionary with display_info added.
        For tool_request events, also adds tools_display_info.
        For tool_result events, also adds results_display_info.

    Example:
        >>> event = {"type": "tool_request", "tools": [{"name": "search_web"}]}
        >>> enriched = enrich_event_with_display_info(event, manager, "my-agent")
        >>> print(enriched["display_info"]["friendly_name"])
        🔧 Appel d'outil
        >>> print(enriched["tools_display_info"][0]["friendly_name"])
        🔍 Recherche web
    """
    # Make a copy to avoid modifying the original
    enriched = event.copy()

    # Get event type
    event_type = event.get("type", "activity")

    # Add display_info for the event type
    event_display_info = manager.get_display_info("event", event_type, agent_id=agent_id)
    display_info_dict = event_display_info.model_dump()
    
    # If the event provides a friendly_name, use it instead of the default
    if "friendly_name" in event and event["friendly_name"]:
        display_info_dict["friendly_name"] = event["friendly_name"]
    
    enriched["display_info"] = display_info_dict

    # For tool_request events, add display info for each tool
    if event_type == "tool_request" and "tools" in event:
        tools_display_info = []
        for tool in event["tools"]:
            tool_name = tool.get("name", "unknown")
            tool_display = manager.get_display_info("tool", tool_name, agent_id=agent_id)
            tool_info = tool_display.model_dump()

            # For skill loading/unloading tools, add skill_display_info
            if tool_name in ("load_skill_tool", "unload_skill_tool", "load_skill", "unload_skill"):
                arguments = tool.get("arguments", {})
                skill_name = arguments.get("skill_name") if isinstance(arguments, dict) else None
                if skill_name:
                    skill_key = f"skill:{skill_name}"
                    skill_display = manager.get_display_info("tool", skill_key, agent_id=agent_id)
                    tool_info["skill_display_info"] = skill_display.model_dump()

            tools_display_info.append(tool_info)
        enriched["tools_display_info"] = tools_display_info

    # For tool_result events, add display info for each result
    if event_type == "tool_result" and "results" in event:
        results_display_info = []
        for result in event["results"]:
            tool_name = result.get("tool_name", result.get("name", "unknown"))
            result_display = manager.get_display_info("tool", tool_name, agent_id=agent_id)
            results_display_info.append(result_display.model_dump())
        enriched["results_display_info"] = results_display_info

    return enriched


__all__ = [
    "StepDisplayInfo",
    "StepDisplayConfig",
    "DisplayConfigManager",
    "DEFAULT_EVENT_DISPLAY",
    "DEFAULT_STEP_DISPLAY",
    "DEFAULT_TOOL_DISPLAY",
    "enrich_event_with_display_info",
]
