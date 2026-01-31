# ActivityOutputPart - Frontend Developer Guide

This document describes the `ActivityOutputPart` type, a first-class part in the streaming and history system that represents agent activities (tool requests, tool results, thoughts, errors, etc.).

## Overview

`ActivityOutputPart` is a structured part type that can appear in the `parts` array of both streaming responses and history messages. It preserves the chronological order of activities relative to text content, enabling frontends to render activities inline with the conversation flow.

### Key Benefits

- **Chronological ordering**: Activities appear in the `parts` array in the exact order they occurred during execution
- **Unified rendering**: Activities can be rendered alongside text parts using the same rendering pipeline
- **Rich metadata**: Includes `display_info` for user-friendly names and icons
- **Backward compatible**: The legacy `activity_parts` field and `__STREAM_ACTIVITY__` markers continue to work

## ActivityOutputPart Structure

```typescript
interface ActivityOutputPart {
  type: "activity";                    // Always "activity" - identifies this part type
  activity_type: string;               // Type of activity (see Activity Types below)
  source: string;                      // Origin of the activity (e.g., "socrate", "james", "llamaindex_agent")
  content: string | null;              // User-friendly activity description (no raw function names)
  timestamp: string;                   // ISO 8601 format (e.g., "2024-01-15T10:30:00.000000")
  tools: ToolCall[] | null;            // For tool_call: list of tool calls
  results: ToolResult[] | null;        // For tool_call: list of results
  display_info: DisplayInfo | null;    // UI rendering metadata
  technical_details: TechnicalDetails | null;  // Technical data (ES storage only, stripped for frontend)
}

interface ToolCall {
  name: string;                        // Tool name
  arguments: object;                   // Tool arguments
  id: string;                          // Unique call ID
}

interface ToolResult {
  name: string;                        // Tool name
  content: string;                     // Result content
  is_error: boolean;                   // Whether the result is an error
  call_id: string;                     // Matching call ID from tool_request
}

interface DisplayInfo {
  id: string;                          // Technical identifier
  friendly_name: string;               // Human-readable name to display
  description: string | null;          // Detailed description
  icon: string | null;                 // Emoji or icon identifier
  category: string | null;             // Category for grouping
  color: string | null;                // Color code for styling
}

interface TechnicalDetails {
  function_name: string;               // Raw function/tool name
  arguments: object;                   // Arguments passed to the function
  raw_result: any;                     // Raw result from execution
  execution_time_ms: number;           // Execution time in milliseconds
  timestamp: string;                   // ISO 8601 format
  status: "success" | "error";         // Execution status
  error_message: string | null;        // Error message if status is "error"
}
```

> **Important**: The `technical_details` field is stored in Elasticsearch but **stripped before sending to the frontend**. Frontend developers will never see this field in streaming or history responses.
```

## Activity Types

The `activity_type` field indicates what kind of activity occurred:

| activity_type | Description | Typical Fields Used |
|---------------|-------------|---------------------|
| `tool_call` | Consolidated tool execution (request + result) | `tools`, `results`, `display_info` |
| `skill_loading` | Skill/capability loaded | `content`, `display_info` |
| `diagram_generation` | Mermaid diagram generated | `content`, `display_info` |
| `chart_generation` | Chart.js chart generated | `content`, `display_info` |
| `thought` | Agent reasoning/thinking step | `content`, `display_info` |
| `activity` | General agent activity (e.g., loop started) | `content`, `display_info` |
| `error` | Error during processing | `content`, `display_info` |

> **Note**: Tool executions are now **consolidated** into a single `tool_call` activity instead of separate `tool_request` and `tool_result` activities. This provides a cleaner user experience.

## Display Info

The `display_info` field provides metadata for rendering activities in a user-friendly way.

### Specific Activity Formats

Activities now have specific `friendly_name` and `description` based on the activity type:

#### Skill Loading

```json
{
  "type": "activity",
  "activity_type": "skill_loading",
  "source": "socrate",
  "content": "Capacité 'chart' chargée avec succès.\n\nInstructions chargées:\n...",
  "timestamp": "2024-01-15T10:30:00.000000",
  "display_info": {
    "id": "skill_loading_chart",
    "friendly_name": "Chargement de la capacité : chart",
    "description": "Affichage, génération et enregistrement en image des graphiques Chart.js",
    "icon": "📥",
    "category": "skills"
  }
}
```

#### Diagram Generation

```json
{
  "type": "activity",
  "activity_type": "diagram_generation",
  "source": "james",
  "content": "project_timeline.png généré et enregistré en PNG avec le contenu suivant :\n\ngantt\n    title Project Timeline...",
  "timestamp": "2024-01-15T10:30:00.000000",
  "display_info": {
    "id": "diagram_gantt",
    "friendly_name": "Génération de diagramme Gantt",
    "description": "Enregistrement en image d'un diagramme généré",
    "icon": "📊",
    "category": "diagram"
  }
}
```

#### Chart Generation

```json
{
  "type": "activity",
  "activity_type": "chart_generation",
  "source": "socrate",
  "content": "sales_chart.png généré et enregistré en PNG avec le contenu suivant :\n\n{\"type\": \"bar\", ...}",
  "timestamp": "2024-01-15T10:30:00.000000",
  "display_info": {
    "id": "chart_bar",
    "friendly_name": "Génération de graphique barres",
    "description": "Enregistrement en image d'un graphique généré",
    "icon": "📊",
    "category": "chart"
  }
}
```

### Standard Display Info

```json
{
  "id": "tool_request",
  "friendly_name": "🔧 Appel d'outil",
  "description": "L'agent appelle un outil",
  "icon": "🔧",
  "category": "tool",
  "color": null
}
```

### Display Info for Skills

When the activity involves skill loading/unloading, additional skill information is included:

```json
{
  "id": "tool_request",
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
```

### Common Display Info Values

| Activity Type | friendly_name | icon |
|---------------|---------------|------|
| `activity` | 🧠 Raisonnement | 🧠 |
| `tool_request` | 🔧 Appel d'outil | 🔧 |
| `tool_result` (success) | ✅ Résultat | ✅ |
| `tool_result` (error) | ❌ Erreur | ❌ |
| `thought` | 💭 Réflexion | 💭 |
| `error` | ❌ Erreur | ❌ |

## Examples

### Tool Request Activity

```json
{
  "type": "activity",
  "activity_type": "tool_request",
  "source": "llamaindex_agent",
  "content": null,
  "timestamp": "2024-01-15T10:30:00.000000",
  "tools": [
    {
      "name": "search_web",
      "arguments": {"query": "weather in Paris"},
      "id": "call_abc123"
    }
  ],
  "results": null,
  "display_info": {
    "id": "tool_request",
    "friendly_name": "🔍 Recherche web",
    "description": "Recherche d'informations sur le web",
    "icon": "🔍",
    "category": "search"
  }
}
```

### Tool Result Activity

```json
{
  "type": "activity",
  "activity_type": "tool_result",
  "source": "llamaindex_agent",
  "content": null,
  "timestamp": "2024-01-15T10:30:01.500000",
  "tools": null,
  "results": [
    {
      "name": "search_web",
      "content": "Current weather in Paris: 18°C, partly cloudy",
      "is_error": false,
      "call_id": "call_abc123"
    }
  ],
  "display_info": {
    "id": "tool_result",
    "friendly_name": "✅ Résultat de recherche",
    "description": "Résultat de la recherche web",
    "icon": "✅",
    "category": "search"
  }
}
```

### Thought/Reasoning Activity

```json
{
  "type": "activity",
  "activity_type": "thought",
  "source": "llamaindex_agent",
  "content": "I need to search for the current weather before providing an answer.",
  "timestamp": "2024-01-15T10:29:59.000000",
  "tools": null,
  "results": null,
  "display_info": {
    "id": "thought",
    "friendly_name": "💭 Réflexion",
    "description": "Raisonnement de l'agent",
    "icon": "💭",
    "category": "reasoning"
  }
}
```

### Error Activity

```json
{
  "type": "activity",
  "activity_type": "error",
  "source": "llamaindex_agent",
  "content": "Failed to connect to external API: timeout after 30s",
  "timestamp": "2024-01-15T10:30:05.000000",
  "tools": null,
  "results": null,
  "display_info": {
    "id": "error",
    "friendly_name": "❌ Erreur",
    "description": "Une erreur s'est produite",
    "icon": "❌",
    "category": "error"
  }
}
```

## Streaming Sequence Example

During streaming, parts are emitted in chronological order. Here's an example sequence:

```json
// 1. Text chunk - agent starts responding
{"type": "text_output_stream", "text": "Let me search for that information..."}

// 2. Tool request activity - agent calls a tool
{"type": "activity", "activity_type": "tool_request", "source": "llamaindex_agent", "timestamp": "...", "tools": [{"name": "search_web", "arguments": {"query": "test"}, "id": "call_123"}], "display_info": {...}}

// 3. Legacy marker (for backward compatibility with older frontends)
{"type": "text_output_stream", "text": "__STREAM_ACTIVITY__{\"type\":\"tool_request\",...}"}

// 4. Tool result activity - tool execution completed
{"type": "activity", "activity_type": "tool_result", "source": "llamaindex_agent", "timestamp": "...", "results": [{"name": "search_web", "content": "...", "is_error": false, "call_id": "call_123"}], "display_info": {...}}

// 5. Legacy marker (for backward compatibility)
{"type": "text_output_stream", "text": "__STREAM_ACTIVITY__{\"type\":\"tool_result\",...}"}

// 6. Final text - agent provides the answer
{"type": "text_output_stream", "text": "Based on my search, here are the results..."}
```

## Rendering ActivityOutputPart in the UI

### Basic Rendering Logic

```javascript
function renderPart(part) {
  switch (part.type) {
    case 'text_output':
    case 'text_output_stream':
      renderMarkdown(part.text);
      break;
      
    case 'activity':
      renderActivity(part);
      break;
      
    // ... other part types
  }
}

function renderActivity(activity) {
  const displayName = activity.display_info?.friendly_name || activity.activity_type;
  const icon = activity.display_info?.icon || getDefaultIcon(activity.activity_type);
  
  // Render activity header
  renderActivityHeader(displayName, icon, activity.timestamp);
  
  // Render activity-specific content
  switch (activity.activity_type) {
    case 'tool_request':
      renderToolCalls(activity.tools);
      break;
      
    case 'tool_result':
      renderToolResults(activity.results);
      break;
      
    case 'thought':
    case 'activity':
    case 'error':
      if (activity.content) {
        renderActivityContent(activity.content);
      }
      break;
  }
}

function getDefaultIcon(activityType) {
  const icons = {
    'tool_request': '🔧',
    'tool_result': '✅',
    'thought': '💭',
    'activity': '🧠',
    'error': '❌'
  };
  return icons[activityType] || '⚙️';
}
```

### Rendering Tool Calls

```javascript
function renderToolCalls(tools) {
  if (!tools || tools.length === 0) return;
  
  tools.forEach(tool => {
    renderToolCall({
      name: tool.name,
      arguments: tool.arguments,
      callId: tool.id
    });
  });
}
```

### Rendering Tool Results

```javascript
function renderToolResults(results) {
  if (!results || results.length === 0) return;
  
  results.forEach(result => {
    renderToolResult({
      name: result.name,
      content: result.content,
      isError: result.is_error,
      callId: result.call_id
    });
  });
}
```

### Collapsible Activity Display

For a cleaner UI, activities can be rendered as collapsible elements:

```javascript
function renderCollapsibleActivity(activity) {
  const displayName = activity.display_info?.friendly_name || activity.activity_type;
  const icon = activity.display_info?.icon || '⚙️';
  
  return `
    <details class="activity-block ${activity.activity_type}">
      <summary>
        <span class="activity-icon">${icon}</span>
        <span class="activity-name">${displayName}</span>
        <span class="activity-time">${formatTime(activity.timestamp)}</span>
      </summary>
      <div class="activity-details">
        ${renderActivityDetails(activity)}
      </div>
    </details>
  `;
}
```

## Backward Compatibility with activity_parts

The `ActivityOutputPart` in the `parts` array coexists with the legacy `activity_parts` field. Both contain the same activity data, but in different formats:

| Field | Format | Order Preserved | Use Case |
|-------|--------|-----------------|----------|
| `parts` (with ActivityOutputPart) | Structured parts | ✅ Yes | New frontends - activities in chronological order with text |
| `activity_parts` | Raw activity dicts | ❌ No (separate array) | Legacy frontends - activities listed separately |

### Migration Strategy

**For new frontends**: Use the `parts` array and filter for `type === "activity"` to get activities in order.

**For existing frontends**: Continue using `activity_parts` - it will remain populated for backward compatibility.

### Checking for ActivityOutputPart Support

```javascript
function hasActivityOutputPartSupport(message) {
  return message.parts?.some(part => part.type === 'activity');
}

function getActivities(message) {
  // Prefer parts array (new format with order preserved)
  if (hasActivityOutputPartSupport(message)) {
    return message.parts.filter(part => part.type === 'activity');
  }
  
  // Fallback to activity_parts (legacy format)
  return message.activity_parts || [];
}
```

## Related Documentation

- [HISTORY_MESSAGE_FORMAT.md](./HISTORY_MESSAGE_FORMAT.md) - Complete history message structure
- [STREAMING_EVENTS_FRONTEND.md](./STREAMING_EVENTS_FRONTEND.md) - Streaming events and SSE format
