"""ActivityFormatter for formatting activities with user-friendly content.

This module provides the ActivityFormatter class that formats activities
with specific friendly_name/description per function/skill. It creates
ActivityOutputPart instances with user-friendly content for display in
the frontend and TechnicalDetails for Elasticsearch storage.

The formatter handles:
- Skill loading activities
- Diagram generation activities (Gantt, Mind Map, Flowchart, etc.)
- Chart generation activities (bar, line, pie, etc.)
- Generic tool execution activities
"""

from datetime import datetime, timezone
from typing import Any

from agent_framework.core.agent_interface import (
    ActivityOutputPart,
    TechnicalDetails,
)
from agent_framework.core.step_display_config import DEFAULT_TOOL_DISPLAY


# =============================================================================
# Diagram Type Mappings
# =============================================================================

DIAGRAM_TYPE_DISPLAY: dict[str, dict[str, str]] = {
    "gantt": {
        "friendly_name": "Génération de diagramme Gantt",
        "icon": "📊",
    },
    "mindmap": {
        "friendly_name": "Génération de diagramme Mind Map",
        "icon": "🧠",
    },
    "flowchart": {
        "friendly_name": "Génération de diagramme Flowchart",
        "icon": "🔀",
    },
    "sequence": {
        "friendly_name": "Génération de diagramme Séquence",
        "icon": "📋",
    },
    "class": {
        "friendly_name": "Génération de diagramme Classe",
        "icon": "📦",
    },
    "state": {
        "friendly_name": "Génération de diagramme État",
        "icon": "🔄",
    },
    "er": {
        "friendly_name": "Génération de diagramme Entité-Relation",
        "icon": "🔗",
    },
    "pie": {
        "friendly_name": "Génération de diagramme Camembert",
        "icon": "🥧",
    },
    "journey": {
        "friendly_name": "Génération de diagramme Parcours",
        "icon": "🚶",
    },
    "timeline": {
        "friendly_name": "Génération de diagramme Timeline",
        "icon": "📅",
    },
    "quadrant": {
        "friendly_name": "Génération de diagramme Quadrant",
        "icon": "📐",
    },
    "requirement": {
        "friendly_name": "Génération de diagramme Exigences",
        "icon": "📝",
    },
    "gitgraph": {
        "friendly_name": "Génération de diagramme Git",
        "icon": "🌳",
    },
    "c4context": {
        "friendly_name": "Génération de diagramme C4 Context",
        "icon": "🏗️",
    },
    "sankey": {
        "friendly_name": "Génération de diagramme Sankey",
        "icon": "📈",
    },
    "block": {
        "friendly_name": "Génération de diagramme Block",
        "icon": "🧱",
    },
    "packet": {
        "friendly_name": "Génération de diagramme Packet",
        "icon": "📦",
    },
    "architecture": {
        "friendly_name": "Génération de diagramme Architecture",
        "icon": "🏛️",
    },
}
"""Mapping of Mermaid diagram types to their display information."""


# =============================================================================
# Chart Type Mappings
# =============================================================================

CHART_TYPE_DISPLAY: dict[str, dict[str, str]] = {
    "bar": {
        "friendly_name": "Génération de graphique barres",
        "icon": "📊",
    },
    "line": {
        "friendly_name": "Génération de graphique courbes",
        "icon": "📈",
    },
    "pie": {
        "friendly_name": "Génération de graphique camembert",
        "icon": "🥧",
    },
    "doughnut": {
        "friendly_name": "Génération de graphique anneau",
        "icon": "🍩",
    },
    "radar": {
        "friendly_name": "Génération de graphique radar",
        "icon": "📡",
    },
    "scatter": {
        "friendly_name": "Génération de graphique nuage de points",
        "icon": "⚬",
    },
    "bubble": {
        "friendly_name": "Génération de graphique bulles",
        "icon": "🫧",
    },
    "polarArea": {
        "friendly_name": "Génération de graphique aire polaire",
        "icon": "🎯",
    },
    "horizontalBar": {
        "friendly_name": "Génération de graphique barres horizontales",
        "icon": "📊",
    },
}
"""Mapping of Chart.js chart types to their display information."""


# =============================================================================
# Skill Descriptions
# =============================================================================

SKILL_DESCRIPTIONS: dict[str, str] = {
    "chart": "Affichage, génération et enregistrement en image des graphiques Chart.js",
    "mermaid": "Création, affichage et enregistrement en image de diagrammes (flowcharts, séquences, classes, gantt, etc.)",
    "table": "Affichage et génération d'images de tableaux de données",
    "pdf": "Création de documents PDF à partir de Markdown ou HTML",
    "unified_pdf": "Création de PDF avec images intégrées automatiquement",
    "pdf_with_images": "Création de PDF avec images intégrées automatiquement",
    "file": "Création, lecture et listage de fichiers",
    "file_access": "Obtention des chemins et URLs des fichiers stockés",
    "web_search": "Recherche d'informations et d'actualités sur le web",
    "multimodal": "Description, OCR et analyse d'images par IA",
    "form": "Génération de formulaires interactifs",
    "optionsblock": "Génération de boutons d'options interactifs",
    "image_display": "Affichage d'images depuis des URLs avec téléchargement",
}
"""Mapping of skill names to their descriptions."""


class ActivityFormatter:
    """Formats activities with user-friendly content.

    This class creates ActivityOutputPart instances with specific friendly_name
    and description per function/skill. It ensures that:
    - User-facing content is in French as per requirements
    - Technical details are captured for Elasticsearch storage
    - Content is user-friendly without raw function names

    Example usage:
        formatter = ActivityFormatter(source="socrate")

        # Format skill loading
        activity = formatter.format_skill_loading(
            skill_name="chart",
            skill_description="Génération de graphiques",
            loaded_prompt="Instructions pour créer des graphiques...",
            execution_time_ms=50
        )

        # Format diagram generation
        activity = formatter.format_diagram_generation(
            diagram_type="gantt",
            file_name="project_timeline.png",
            content="gantt\\n    title Project Timeline...",
            execution_time_ms=1200
        )
    """

    def __init__(
        self,
        source: str = "agent",
        display_config_manager: Any = None,
        agent_id: str | None = None,
    ) -> None:
        """Initialize the ActivityFormatter.

        Args:
            source: The source identifier for activities (e.g., "socrate", "james",
                   "llamaindex_agent"). Defaults to "agent".
            display_config_manager: Optional DisplayConfigManager instance for
                resolving custom tool display info from agents.
            agent_id: Optional agent identifier for agent-specific display overrides.
        """
        self._source = source
        self._display_config_manager = display_config_manager
        self._agent_id = agent_id

    def format_skill_loading(
        self,
        skill_name: str,
        skill_description: str,
        loaded_prompt: str,
        execution_time_ms: int,
        display_name: str | None = None,
        display_icon: str | None = None,
    ) -> ActivityOutputPart:
        """Format skill loading activity with skill's display metadata.

        Creates an ActivityOutputPart for a skill loading event with:
        - friendly_name: "{display_icon} Chargement de la capacité : {display_name}"
        - description: What the skill does
        - content: User-friendly loaded prompt information

        Args:
            skill_name: Name of the skill being loaded (e.g., "chart", "mermaid").
            skill_description: Description of what the skill does.
            loaded_prompt: The prompt/instructions loaded for the skill.
            execution_time_ms: Time taken to load the skill in milliseconds.
            display_name: User-friendly display name for the skill. Falls back to
                skill_name if not provided.
            display_icon: Emoji icon for the skill. Falls back to "📥" if not provided.

        Returns:
            ActivityOutputPart with skill loading information.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Use provided display_name or fall back to skill_name
        friendly_display_name = display_name or skill_name
        icon = display_icon or "📥"

        # Build friendly name: "{icon} Chargement de la capacité : {display_name}"
        friendly_name = f"{icon} Chargement de la capacité : {friendly_display_name}"

        # Get skill description from mapping if not provided
        if not skill_description:
            skill_description = SKILL_DESCRIPTIONS.get(
                skill_name, f"Capacité {skill_name}"
            )

        # Create user-friendly content
        # Truncate loaded_prompt if too long for display
        display_prompt = f"{loaded_prompt[:300]}..." if len(loaded_prompt) > 300 else loaded_prompt

        content = f"Capacité '{skill_name}' chargée avec succès.\n\nInstructions chargées:\n{display_prompt}"

        # Create TechnicalDetails for Elasticsearch storage
        technical_details = TechnicalDetails(
            function_name="load_skill",
            arguments={"skill_name": skill_name},
            raw_result={"loaded_prompt": loaded_prompt},
            execution_time_ms=execution_time_ms,
            timestamp=timestamp,
            status="success",
            error_message=None,
        )

        # Create display_info
        display_info = {
            "id": f"skill_loading_{skill_name}",
            "friendly_name": friendly_name,
            "description": skill_description,
            "icon": icon,
            "category": "skills",
        }

        return ActivityOutputPart(
            activity_type="skill_loading",
            source=self._source,
            content=content,
            timestamp=timestamp,
            display_info=display_info,
            technical_details=technical_details,
        )

    def format_diagram_generation(
        self,
        diagram_type: str,
        file_name: str,
        content: str,
        execution_time_ms: int,
    ) -> ActivityOutputPart:
        """Format diagram generation activity.

        Creates an ActivityOutputPart for a diagram generation event with:
        - friendly_name: "Génération de diagramme {type}" (e.g., Gantt, Mind Map)
        - description: "Enregistrement en image d'un diagramme généré"
        - content: "{file_name} généré et enregistré en PNG avec le contenu suivant : {content}"

        Args:
            diagram_type: Type of diagram (e.g., "gantt", "mindmap", "flowchart").
            file_name: Name of the generated file.
            content: The Mermaid diagram content/definition.
            execution_time_ms: Time taken to generate the diagram in milliseconds.

        Returns:
            ActivityOutputPart with diagram generation information.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Normalize diagram type to lowercase for lookup
        diagram_type_lower = diagram_type.lower()

        # Get type-specific display info
        type_display = DIAGRAM_TYPE_DISPLAY.get(
            diagram_type_lower,
            {
                "friendly_name": f"Génération de diagramme {diagram_type}",
                "icon": "🔀",
            },
        )

        # Create user-friendly content
        # Truncate content if too long for display
        display_content = f"{content[:500]}..." if len(content) > 500 else content

        user_content = f"{file_name} généré et enregistré en PNG avec le contenu suivant :\n\n{display_content}"

        # Create TechnicalDetails for Elasticsearch storage
        technical_details = TechnicalDetails(
            function_name="save_mermaid_as_image",
            arguments={"diagram_type": diagram_type, "file_name": file_name},
            raw_result={"file_name": file_name, "content": content},
            execution_time_ms=execution_time_ms,
            timestamp=timestamp,
            status="success",
            error_message=None,
        )

        # Create display_info
        display_info = {
            "id": f"diagram_{diagram_type_lower}",
            "friendly_name": type_display["friendly_name"],
            "description": "Enregistrement en image d'un diagramme généré",
            "icon": type_display["icon"],
            "category": "diagram",
        }

        return ActivityOutputPart(
            activity_type="diagram_generation",
            source=self._source,
            content=user_content,
            timestamp=timestamp,
            display_info=display_info,
            technical_details=technical_details,
        )

    def format_chart_generation(
        self,
        chart_type: str,
        file_name: str,
        content: str,
        execution_time_ms: int,
    ) -> ActivityOutputPart:
        """Format chart generation activity.

        Creates an ActivityOutputPart for a chart generation event with:
        - friendly_name: "Génération de graphique {type}" (e.g., barres, courbes)
        - description: "Enregistrement en image d'un graphique généré"
        - content: "{file_name} généré et enregistré en PNG avec le contenu suivant : {content}"

        Args:
            chart_type: Type of chart (e.g., "bar", "line", "pie").
            file_name: Name of the generated file.
            content: The chart configuration or data description.
            execution_time_ms: Time taken to generate the chart in milliseconds.

        Returns:
            ActivityOutputPart with chart generation information.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Normalize chart type for lookup (handle both camelCase and lowercase)
        chart_type_normalized = chart_type.lower()

        # Get type-specific display info
        type_display = CHART_TYPE_DISPLAY.get(
            chart_type,  # Try exact match first (for camelCase like "polarArea")
            CHART_TYPE_DISPLAY.get(
                chart_type_normalized,  # Then try lowercase
                {
                    "friendly_name": f"Génération de graphique {chart_type}",
                    "icon": "📊",
                },
            ),
        )

        # Create user-friendly content
        # Truncate content if too long for display
        display_content = f"{content[:500]}..." if len(content) > 500 else content

        user_content = f"{file_name} généré et enregistré en PNG avec le contenu suivant :\n\n{display_content}"

        # Create TechnicalDetails for Elasticsearch storage
        technical_details = TechnicalDetails(
            function_name="save_chart_as_image",
            arguments={"chart_type": chart_type, "file_name": file_name},
            raw_result={"file_name": file_name, "content": content},
            execution_time_ms=execution_time_ms,
            timestamp=timestamp,
            status="success",
            error_message=None,
        )

        # Create display_info
        display_info = {
            "id": f"chart_{chart_type_normalized}",
            "friendly_name": type_display["friendly_name"],
            "description": "Enregistrement en image d'un graphique généré",
            "icon": type_display["icon"],
            "category": "chart",
        }

        return ActivityOutputPart(
            activity_type="chart_generation",
            source=self._source,
            content=user_content,
            timestamp=timestamp,
            display_info=display_info,
            technical_details=technical_details,
        )

    def format_tool_execution(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: str,
        execution_time_ms: int,
        is_error: bool = False,
    ) -> ActivityOutputPart:
        """Format generic tool execution as single consolidated activity.

        Creates an ActivityOutputPart for a tool execution event with:
        - friendly_name: Specific to the tool (not generic "Tool call")
        - description: What the tool does
        - content: User-friendly result (no raw function names)

        Args:
            tool_name: Name of the tool being executed.
            arguments: Arguments passed to the tool.
            result: The result from the tool execution.
            execution_time_ms: Time taken to execute the tool in milliseconds.
            is_error: Whether the tool execution resulted in an error.

        Returns:
            ActivityOutputPart with tool execution information.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create user-friendly content
        if is_error:
            user_content = f"Erreur lors de l'exécution: {result}"
        else:
            # Truncate long results for display
            user_content = f"{result[:500]}..." if len(result) > 500 else result

        # Create TechnicalDetails for Elasticsearch storage
        technical_details = TechnicalDetails(
            function_name=tool_name,
            arguments=arguments,
            raw_result=result,
            execution_time_ms=execution_time_ms,
            timestamp=timestamp,
            status="error" if is_error else "success",
            error_message=result if is_error else None,
        )

        # Generate friendly name based on tool name
        # Convert snake_case to user-friendly format
        friendly_name = self._get_tool_friendly_name(tool_name)
        description = self._get_tool_description(tool_name)
        icon = self._get_tool_icon(tool_name)

        # Create display_info
        display_info = {
            "id": f"tool_{tool_name}",
            "friendly_name": friendly_name,
            "description": description,
            "icon": icon,
            "category": "tool",
        }

        return ActivityOutputPart(
            activity_type="tool_call",
            source=self._source,
            content=user_content,
            timestamp=timestamp,
            tools=[{"name": tool_name, "arguments": arguments}],
            results=[{"name": tool_name, "content": result, "is_error": is_error}],
            display_info=display_info,
            technical_details=technical_details,
        )

    def _get_tool_friendly_name(self, tool_name: str) -> str:
        """Get user-friendly name for a tool.

        The lookup chain is:
        1. First check DisplayConfigManager for agent-specific overrides
        2. Then check DEFAULT_TOOL_DISPLAY for the tool's StepDisplayInfo
        3. Then check the internal tool_friendly_names mapping
        4. Finally generate a friendly name from the snake_case tool name

        Args:
            tool_name: Technical tool name (e.g., "search_web", "create_file").

        Returns:
            User-friendly name in French.
        """
        # Priority 1: Check DisplayConfigManager for agent-specific overrides
        if self._display_config_manager is not None and self._agent_id is not None:
            display_info = self._display_config_manager.get_display_info(
                "tool", tool_name, agent_id=self._agent_id
            )
            # If we got a non-fallback result (friendly_name != tool_name), use it
            if display_info.friendly_name != tool_name:
                return display_info.friendly_name

        # Priority 2: Check DEFAULT_TOOL_DISPLAY
        if tool_name in DEFAULT_TOOL_DISPLAY:
            return DEFAULT_TOOL_DISPLAY[tool_name].friendly_name

        # Fall back to internal mapping of common tool names to friendly names
        tool_friendly_names: dict[str, str] = {
            # Web & Search
            "search_web": "🔍 Recherche web",
            "web_search": "🔍 Recherche web",
            "news_search": "📰 Recherche d'actualités",
            # File Operations
            "read_file": "📄 Lecture du fichier",
            "write_file": "💾 Écriture du fichier",
            "create_file": "📝 Création du fichier",
            "list_files": "📁 Liste des fichiers",
            "delete_file": "🗑️ Suppression du fichier",
            "get_file_path": "🔗 Localisation du fichier",
            # Chart & Visualization
            "save_chart_as_image": "📊 Génération du graphique",
            "generate_chart": "📈 Génération du graphique",
            # Diagram
            "save_mermaid_as_image": "🔀 Génération du diagramme",
            # Table
            "save_table_as_image": "📋 Génération du tableau",
            # PDF
            "create_pdf": "📄 Création du PDF",
            "create_pdf_from_markdown": "📄 Création du PDF",
            "create_pdf_from_html": "📄 Création du PDF",
            "create_pdf_with_images": "📄 Création du PDF",
            # Skills (both variants: with and without _tool suffix)
            "list_skills": "📋 Liste des capacités",
            "list_skills_tool": "📋 Liste des capacités",
            "load_skill": "📥 Chargement de la capacité :",
            "load_skill_tool": "📥 Chargement de la capacité :",
            "unload_skill": "📤 DéChargement de la capacité :",
            "unload_skill_tool": "📤 DéChargement de la capacité :",
            "search_skills": "🔎 Recherche de capacité",
            "search_skills_tool": "🔎 Recherche de capacité",
            # Memory
            "recall_memory": "🧠 Recherche en mémoire",
            "store_memory": "💾 Stockage en mémoire",
            "forget_memory": "🗑️ Oubli en mémoire",
            "remember": "💾 Mémorisation",
            "recall": "🔍 Rappel mémoire",
            "forget": "🗑️ Oubli",
            # Multimodal
            "describe_image": "🖼️ Description de l'image",
            "answer_about_image": "❓ Question sur l'image",
            "extract_text_from_image": "📝 Extraction de texte (OCR)",
            "analyze_image": "🔬 Analyse de l'image",
            # Code
            "execute_code": "▶️ Exécution du code",
            # Database
            "query_database": "🗄️ Requête base de données",
            # Communication
            "send_email": "📧 Envoi d'email",
            # API
            "call_api": "🌐 Appel API",
        }

        if tool_name in tool_friendly_names:
            return tool_friendly_names[tool_name]

        # Generate a friendly name from the tool name
        # Convert snake_case to title case with spaces
        words = tool_name.replace("_", " ").title()
        return f"⚙️ {words}"

    def _get_tool_description(self, tool_name: str) -> str:
        """Get description for a tool.

        The lookup chain is:
        1. First check DisplayConfigManager for agent-specific overrides
        2. Then check DEFAULT_TOOL_DISPLAY for the tool's StepDisplayInfo
        3. Then check the internal tool_descriptions mapping
        4. Finally generate a generic description from the tool name

        Args:
            tool_name: Technical tool name.

        Returns:
            Description in French.
        """
        # Priority 1: Check DisplayConfigManager for agent-specific overrides
        if self._display_config_manager is not None and self._agent_id is not None:
            display_info = self._display_config_manager.get_display_info(
                "tool", tool_name, agent_id=self._agent_id
            )
            # If we got a non-fallback result, use its description
            if display_info.friendly_name != tool_name and display_info.description:
                return display_info.description

        # Priority 2: Check DEFAULT_TOOL_DISPLAY
        if tool_name in DEFAULT_TOOL_DISPLAY:
            description = DEFAULT_TOOL_DISPLAY[tool_name].description
            if description:
                return description

        # Fall back to internal mapping
        tool_descriptions: dict[str, str] = {
            "search_web": "Recherche d'informations sur le web",
            "web_search": "Recherche d'informations sur le web",
            "news_search": "Recherche d'articles d'actualité",
            "read_file": "Lecture du contenu d'un fichier",
            "write_file": "Écriture de contenu dans un fichier",
            "create_file": "Création d'un nouveau fichier",
            "list_files": "Liste des fichiers disponibles",
            "delete_file": "Suppression d'un fichier",
            "get_file_path": "Obtention du chemin d'un fichier",
            "save_chart_as_image": "Sauvegarde d'un graphique en image",
            "save_mermaid_as_image": "Sauvegarde d'un diagramme en image",
            "save_table_as_image": "Sauvegarde d'un tableau en image",
            "create_pdf": "Génération d'un document PDF",
            "list_skills": "Affichage des capacités disponibles",
            "list_skills_tool": "Affichage des capacités disponibles",
            "load_skill": "Chargement d'une capacité",
            "load_skill_tool": "Chargement d'une capacité",
            "unload_skill": "Déchargement d'une capacité",
            "unload_skill_tool": "Déchargement d'une capacité",
            "search_skills": "Recherche d'une capacité",
            "search_skills_tool": "Recherche d'une capacité",
            "recall_memory": "Recherche d'informations en mémoire",
            "store_memory": "Sauvegarde d'informations en mémoire",
            "describe_image": "Description détaillée d'une image",
            "analyze_image": "Analyse complète d'une image",
            "execute_code": "Exécution de code",
            "query_database": "Exécution d'une requête sur la base de données",
        }

        return tool_descriptions.get(tool_name, f"Exécution de {tool_name}")

    def _get_tool_icon(self, tool_name: str) -> str:
        """Get icon for a tool.

        The lookup chain is:
        1. First check DEFAULT_TOOL_DISPLAY for the tool's StepDisplayInfo
        2. Then check the internal tool_icons mapping
        3. Finally return the default icon "⚙️"

        Args:
            tool_name: Technical tool name.

        Returns:
            Emoji icon for the tool.
        """
        # Priority 1: Check DisplayConfigManager for agent-specific overrides
        if self._display_config_manager is not None and self._agent_id is not None:
            display_info = self._display_config_manager.get_display_info(
                "tool", tool_name, agent_id=self._agent_id
            )
            # If we got a non-fallback result, use its icon
            if display_info.friendly_name != tool_name and display_info.icon:
                return display_info.icon

        # Priority 2: Check DEFAULT_TOOL_DISPLAY
        if tool_name in DEFAULT_TOOL_DISPLAY:
            icon = DEFAULT_TOOL_DISPLAY[tool_name].icon
            if icon:
                return icon

        # Fall back to internal mapping
        tool_icons: dict[str, str] = {
            "search_web": "🔍",
            "web_search": "🔍",
            "news_search": "📰",
            "read_file": "📄",
            "write_file": "💾",
            "create_file": "📝",
            "list_files": "📁",
            "delete_file": "🗑️",
            "get_file_path": "🔗",
            "save_chart_as_image": "📊",
            "generate_chart": "📈",
            "save_mermaid_as_image": "🔀",
            "save_table_as_image": "📋",
            "create_pdf": "📄",
            "create_pdf_from_markdown": "📄",
            "create_pdf_from_html": "📄",
            "list_skills": "📋",
            "list_skills_tool": "📋",
            "load_skill": "📥",
            "load_skill_tool": "📥",
            "unload_skill": "📤",
            "unload_skill_tool": "📤",
            "search_skills": "🔎",
            "search_skills_tool": "🔎",
            "recall_memory": "🧠",
            "store_memory": "💾",
            "forget_memory": "🗑️",
            "describe_image": "🖼️",
            "analyze_image": "🔬",
            "execute_code": "▶️",
            "query_database": "🗄️",
            "send_email": "📧",
            "call_api": "🌐",
        }

        return tool_icons.get(tool_name, "⚙️")
