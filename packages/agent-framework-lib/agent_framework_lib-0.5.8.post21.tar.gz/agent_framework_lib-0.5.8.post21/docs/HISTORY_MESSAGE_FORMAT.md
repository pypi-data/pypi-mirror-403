# History Message Format

This document describes the format of messages returned by the `/sessions/{session_id}/history` endpoint.

## Overview

When loading a session's conversation history, the API returns an array of `HistoryMessage` objects. Each message contains the display content (`parts`) and activity information (`activity_parts`) that can be rendered inline in the conversation.

### Parts vs Activity Parts

The `parts` array now includes `ActivityOutputPart` entries that preserve the chronological order of activities relative to text content. The `activity_parts` field remains available for backward compatibility.

| Field | Contains Activities | Order Preserved | Recommended For |
|-------|---------------------|-----------------|-----------------|
| `parts` | ✅ Yes (as `ActivityOutputPart`) | ✅ Yes | New frontends |
| `activity_parts` | ✅ Yes (raw dicts) | ❌ No (separate array) | Legacy frontends |

## HistoryMessage Structure

```typescript
interface HistoryMessage {
  role: "user" | "assistant";
  text_content: string | null;           // Plain text content (mainly for user messages)
  parts: OutputPart[] | null;            // Structured UI parts (for assistant messages)
  activity_parts: ActivityPart[] | null; // Activities displayed inline in the message
  response_text_main: string | null;     // Main response text (assistant messages)
  timestamp: string;                     // ISO 8601 format: "2026-01-22T21:47:29.763430"
  interaction_id: string;                // UUID linking user message to agent response
  processing_time_ms: number | null;     // Processing time in milliseconds
  processed_at: string | null;           // When response was completed
  model_used: string | null;             // AI model used (e.g., "gpt-5-mini")
  selection_mode: string | null;         // "auto" or "manual"
}
```

## Parts Array (UI Display)

The `parts` array contains structured content for rendering in the chat UI. Each part has a `type` field.

### Supported Part Types

| Type | Description | Key Fields |
|------|-------------|------------|
| `text_output` | Markdown text content | `text` |
| `activity` | Agent activity (tool calls, results, thoughts) | `activity_type`, `tools`, `results`, `display_info` |
| `options_block` | Clickable option buttons | `definition.question`, `definition.options[]` |
| `mermaid_diagram` | Mermaid diagram code | `definition` |
| `chart` | Chart.js configuration | `chartConfig` |
| `table` | Table data | `headers`, `rows` |
| `file_content_output` | File download link | `filename`, `content_base64`, `mime_type` |
| `image` | Image display | `url`, `alt` |
| `form` | Interactive form | `definition` |

### ActivityOutputPart (type: "activity")

The `ActivityOutputPart` represents agent activities directly in the `parts` array, preserving chronological order with text content.

```typescript
interface ActivityOutputPart {
  type: "activity";                    // Always "activity"
  activity_type: string;               // "tool_request", "tool_result", "thought", "activity", "error"
  source: string;                      // Origin (e.g., "llamaindex_agent", "base_agent")
  content: string | null;              // Activity description
  timestamp: string;                   // ISO 8601 format
  tools: ToolCall[] | null;            // For tool_request
  results: ToolResult[] | null;        // For tool_result
  display_info: DisplayInfo | null;    // UI rendering metadata
}
```

For detailed documentation on `ActivityOutputPart`, see [ACTIVITY_OUTPUT_PART.md](./ACTIVITY_OUTPUT_PART.md).

### Example: Text with Options

```json
{
  "role": "assistant",
  "parts": [
    {
      "type": "text_output",
      "text": "Bonjour ! Comment puis-je vous aider ?"
    },
    {
      "type": "options_block",
      "definition": {
        "question": "Que souhaitez-vous faire ?",
        "options": [
          { "text": "📊 Créer un graphique", "value": "create_chart" },
          { "text": "📄 Générer un PDF", "value": "create_pdf" },
          { "text": "🔍 Rechercher", "value": "search" }
        ]
      }
    }
  ]
}
```

### Example: Parts with ActivityOutputPart (Chronological Order)

This example shows how activities appear in the `parts` array in chronological order with text:

```json
{
  "role": "assistant",
  "parts": [
    {
      "type": "text_output",
      "text": "Let me search for that information..."
    },
    {
      "type": "activity",
      "activity_type": "tool_request",
      "source": "llamaindex_agent",
      "content": null,
      "timestamp": "2024-01-15T10:30:00.000000",
      "tools": [
        {
          "name": "search_web",
          "arguments": {"query": "weather Paris"},
          "id": "call_abc123"
        }
      ],
      "results": null,
      "display_info": {
        "id": "tool_request",
        "friendly_name": "🔍 Recherche web",
        "icon": "🔍",
        "category": "search"
      }
    },
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
          "content": "Weather in Paris: 18°C, partly cloudy",
          "is_error": false,
          "call_id": "call_abc123"
        }
      ],
      "display_info": {
        "id": "tool_result",
        "friendly_name": "✅ Résultat",
        "icon": "✅",
        "category": "search"
      }
    },
    {
      "type": "text_output",
      "text": "The current weather in Paris is 18°C and partly cloudy."
    }
  ],
  "activity_parts": [
    {"type": "tool_request", "source": "llamaindex_agent", "tools": [...], "timestamp": "..."},
    {"type": "tool_result", "source": "llamaindex_agent", "results": [...], "timestamp": "..."}
  ]
}
```

> **Note**: Both `parts` (with `ActivityOutputPart`) and `activity_parts` contain the same activities. Use `parts` for chronological rendering, or `activity_parts` for legacy compatibility.

## Activity Parts (Legacy - Backward Compatibility)

The `activity_parts` array contains activities that occurred during message generation. This field is maintained for **backward compatibility** with existing frontends.

> **Recommendation**: New frontends should use `ActivityOutputPart` entries in the `parts` array instead, as they preserve chronological order with text content.

### Activity Types

| Type | Description | Default Icon |
|------|-------------|--------------|
| `activity` | Agent reasoning/loop started | 🧠 |
| `tool_request` | Tool call initiated | 🔧 |
| `tool_result` | Tool execution result | ✅ or ❌ |
| `other` | Other events | ⚙️ |
| `error` | Error during processing | ❌ |

### Activity Structure

```typescript
interface ActivityPart {
  type: "activity" | "tool_request" | "tool_result" | "other" | "error";
  source: string;           // "agent", "llamaindex_agent", etc.
  content?: string;         // Activity description
  timestamp: string;        // ISO 8601 format
  display_info?: {
    id: string;
    friendly_name: string;  // Human-readable name displayed in the message
    description: string;
    icon: string;
    category: string;
    color: string | null;
  };
  
  // For tool_request
  tools?: Array<{
    name: string;
    arguments: object;
    id: string;
  }>;
  
  // For tool_result
  results?: Array<{
    name: string;
    content: string;
    is_error: boolean;
    call_id: string;
  }>;
}
```

### friendly_name Field

The `friendly_name` field in `display_info` provides a human-readable label that should be displayed directly in the message. This replaces technical identifiers with user-friendly text:

| Activity Type | friendly_name Example |
|---------------|----------------------|
| `activity` | "🧠 Raisonnement" |
| `tool_request` | "🔧 Appel d'outil" |
| `tool_result` | "✅ Résultat" |
| `error` | "❌ Erreur" |

### Example: Activity Parts in Message

```json
{
  "role": "assistant",
  "parts": [
    {
      "type": "text_output",
      "text": "Voici les informations demandées..."
    }
  ],
  "activity_parts": [
    {
      "type": "activity",
      "source": "agent",
      "content": "Agent loop started",
      "timestamp": "2026-01-22T21:47:29.763430",
      "display_info": {
        "id": "activity",
        "friendly_name": "🧠 Raisonnement",
        "description": "Raisonnement de l'agent",
        "icon": "🧠",
        "category": "status"
      }
    },
    {
      "type": "tool_request",
      "source": "llamaindex_agent",
      "tools": [
        {
          "name": "search_database",
          "arguments": { "query": "utilisateurs actifs" },
          "id": "call_123"
        }
      ],
      "timestamp": "2026-01-22T21:48:52.495825",
      "display_info": {
        "id": "tool_request",
        "friendly_name": "🔧 Recherche base de données",
        "description": "Recherche dans la base de données",
        "icon": "🔧",
        "category": "tool"
      }
    },
    {
      "type": "tool_result",
      "source": "llamaindex_agent",
      "results": [
        {
          "name": "search_database",
          "content": "Found 42 active users",
          "is_error": false,
          "call_id": "call_123"
        }
      ],
      "timestamp": "2026-01-22T21:48:52.498078",
      "display_info": {
        "id": "tool_result",
        "friendly_name": "✅ Résultat de recherche",
        "description": "Résultat de la recherche",
        "icon": "✅",
        "category": "tool"
      }
    }
  ]
}
```

## Frontend Rendering Guidelines

### Rendering Parts

```javascript
function formatMessageContent(message) {
  if (message.parts && Array.isArray(message.parts) && message.parts.length > 0) {
    message.parts.forEach(part => {
      switch (part.type) {
        case 'text_output':
          renderMarkdown(part.text);
          break;
        case 'activity':
          // NEW: Render ActivityOutputPart inline with text
          renderActivityPart(part);
          break;
        case 'options_block':
          renderOptionsButtons(part.definition);
          break;
        case 'mermaid_diagram':
          renderMermaid(part.definition);
          break;
        // ... other types
      }
    });
  } else {
    renderMarkdown(message.text_content || message.response_text_main || '');
  }
}

// NEW: Render ActivityOutputPart from parts array
function renderActivityPart(activity) {
  const displayName = activity.display_info?.friendly_name || activity.activity_type;
  const icon = activity.display_info?.icon || getDefaultIcon(activity.activity_type);
  
  renderInlineActivity({
    name: displayName,
    icon: icon,
    type: activity.activity_type,
    timestamp: activity.timestamp,
    tools: activity.tools,
    results: activity.results,
    content: activity.content,
    isError: activity.activity_type === 'error' || activity.results?.some(r => r.is_error)
  });
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

### Rendering Activity Parts Inline (Legacy)

For frontends still using `activity_parts`, activities should be rendered as part of the message content:

```javascript
function renderActivitiesInline(message) {
  if (!message.activity_parts || message.activity_parts.length === 0) {
    return;
  }
  
  message.activity_parts.forEach(activity => {
    // Use friendly_name for display - it's the human-readable label
    const displayName = activity.display_info?.friendly_name || activity.type;
    
    renderInlineActivity({
      name: displayName,
      type: activity.type,
      timestamp: activity.timestamp,
      tools: activity.tools,
      results: activity.results,
      isError: activity.type === 'error' || activity.results?.some(r => r.is_error)
    });
  });
}
```

## Elasticsearch Storage

Messages are stored in the `agent-sessions-messages` index with the following key fields:

- `parts`: Array of output parts (stored as JSON objects)
- `activity_parts`: Array of activity parts (stored as JSON objects)
- `created_at`: ISO 8601 timestamp

### Parts Order Preservation

The `parts` array maintains **chronological order** - parts appear in the exact order they were emitted during streaming. This means:

1. Text parts and activity parts are interleaved based on when they occurred
2. The order is preserved when storing to Elasticsearch
3. The order is preserved when loading from history

Example order: `[text, activity, text, activity, text]` - not `[activity, activity, text, text, text]`

### Technical Details in ES Storage

`ActivityOutputPart` entries stored in Elasticsearch include a `technical_details` field containing:

```json
{
  "technical_details": {
    "function_name": "save_chart_as_image",
    "arguments": {"chart_type": "bar", "file_name": "sales.png"},
    "raw_result": {"file_path": "/tmp/sales.png", "size_bytes": 45000},
    "execution_time_ms": 1200,
    "timestamp": "2024-01-15T10:30:00.000000",
    "status": "success",
    "error_message": null
  }
}
```

> **Important**: This field is **stripped before sending to the frontend**. When loading history via the API, `technical_details` is removed from all `ActivityOutputPart` entries.

### Important Notes

1. **Timestamps must be ISO 8601 format** - Elasticsearch rejects timestamps with spaces (e.g., `2026-01-22 21:44:10`) and requires the `T` separator (e.g., `2026-01-22T21:44:10`)

2. **Parts arrays are never null** - Always use empty arrays `[]` instead of `null` to avoid ES mapping errors

3. **Activity parts are accumulated during streaming** - All streaming events (tool calls, reasoning, etc.) are collected and saved when the message is persisted

4. **friendly_name is the display label** - Always use `display_info.friendly_name` for rendering activities in the UI, not the technical `type` field

## Migration Guide: From activity_parts to ActivityOutputPart

This section helps frontend developers migrate from the legacy `activity_parts` field to the new `ActivityOutputPart` in the `parts` array.

### Why Migrate?

| Aspect | `activity_parts` (Legacy) | `parts` with `ActivityOutputPart` (New) |
|--------|---------------------------|----------------------------------------|
| Chronological order | ❌ Activities separate from text | ✅ Activities interleaved with text |
| Rendering complexity | Higher (merge two arrays) | Lower (single array iteration) |
| Future support | Maintained for compatibility | Recommended approach |

### Migration Steps

#### Step 1: Update Part Rendering Logic

Add handling for `type: "activity"` in your parts renderer:

```javascript
// Before: Only handled text, options, etc.
switch (part.type) {
  case 'text_output':
    renderMarkdown(part.text);
    break;
  // ...
}

// After: Also handle activity parts
switch (part.type) {
  case 'text_output':
    renderMarkdown(part.text);
    break;
  case 'activity':
    renderActivityPart(part);  // NEW
    break;
  // ...
}
```

#### Step 2: Create Activity Renderer

```javascript
function renderActivityPart(activity) {
  // activity.type is always "activity"
  // activity.activity_type tells you what kind: "tool_request", "tool_result", etc.
  
  const displayName = activity.display_info?.friendly_name || activity.activity_type;
  const icon = activity.display_info?.icon || '⚙️';
  
  // Render based on activity_type
  switch (activity.activity_type) {
    case 'tool_request':
      renderToolRequest(displayName, icon, activity.tools);
      break;
    case 'tool_result':
      renderToolResult(displayName, icon, activity.results);
      break;
    case 'thought':
    case 'activity':
      renderThought(displayName, icon, activity.content);
      break;
    case 'error':
      renderError(displayName, icon, activity.content);
      break;
  }
}
```

#### Step 3: Remove Separate Activity Rendering (Optional)

Once migrated, you can remove the separate `activity_parts` rendering:

```javascript
// Before: Rendered parts and activity_parts separately
function renderMessage(message) {
  renderParts(message.parts);
  renderActivitiesInline(message.activity_parts);  // Can be removed
}

// After: Parts array contains everything in order
function renderMessage(message) {
  renderParts(message.parts);  // Activities are included here
}
```

### Backward Compatibility Helper

If you need to support both old and new message formats:

```javascript
function hasActivityOutputParts(message) {
  return message.parts?.some(part => part.type === 'activity');
}

function renderMessage(message) {
  if (hasActivityOutputParts(message)) {
    // New format: activities are in parts array
    renderParts(message.parts);
  } else {
    // Legacy format: render parts and activity_parts separately
    renderParts(message.parts);
    renderActivitiesInline(message.activity_parts);
  }
}
```

### Key Differences in Data Structure

| Field | `activity_parts` | `ActivityOutputPart` |
|-------|------------------|----------------------|
| Type identifier | `type` (e.g., "tool_request") | `type` is always "activity", use `activity_type` |
| Location | Separate `activity_parts` array | Inside `parts` array |
| Order | Separate from text | Interleaved with text parts |

### Example: Same Data in Both Formats

```javascript
// In activity_parts (legacy):
{
  "type": "tool_request",
  "source": "llamaindex_agent",
  "tools": [...],
  "timestamp": "..."
}

// In parts as ActivityOutputPart (new):
{
  "type": "activity",           // Always "activity"
  "activity_type": "tool_request",  // The actual activity type
  "source": "llamaindex_agent",
  "tools": [...],
  "timestamp": "..."
}
```

## Related Documentation

- [ACTIVITY_OUTPUT_PART.md](./ACTIVITY_OUTPUT_PART.md) - Detailed ActivityOutputPart documentation
- [STREAMING_EVENTS_FRONTEND.md](./STREAMING_EVENTS_FRONTEND.md) - Streaming events and SSE format
