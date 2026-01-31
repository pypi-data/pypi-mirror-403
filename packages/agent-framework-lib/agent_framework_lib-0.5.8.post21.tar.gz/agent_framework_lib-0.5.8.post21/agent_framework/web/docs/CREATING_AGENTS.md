# Creating Agents Guide

This comprehensive guide explains how to create custom agents with the Agent Framework. Whether you're using LlamaIndex or integrating a custom AI framework, this guide provides everything you need to build production-ready agents.

## Table of Contents

- [Quick Start](#quick-start)
- [Choosing Your Approach](#choosing-your-approach)
- [LlamaIndex Agent Creation](#llamaindex-agent-creation)
- [BaseAgent (Custom Framework) Creation](#baseagent-custom-framework-creation)
- [Adding Memory to Your Agent](#adding-memory-to-your-agent)
- [Skills Integration](#skills-integration)
- [Streaming Architecture](#streaming-architecture)
- [Tool Integration](#tool-integration)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Quick Start

The fastest way to create an agent is to inherit from `LlamaIndexAgent`:

```python
from agent_framework import LlamaIndexAgent, create_basic_agent_server
from typing import List

class MyAgent(LlamaIndexAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_v1",
            name="My Agent",
            description="A helpful assistant."
        )
    
    def get_agent_prompt(self) -> str:
        return "You are a helpful assistant."
  
    def get_agent_tools(self) -> List[callable]:
        return []

# Start the server
create_basic_agent_server(MyAgent, port=8000)
```

That's it! You now have a fully functional agent with automatic conversation memory, session management, streaming responses, and a web interface.

### Agent Tags and Image URL

You can add visual metadata to your agents for better organization and UI display:

```python
from agent_framework import LlamaIndexAgent
from agent_framework.core.models import Tag

class MyAgent(LlamaIndexAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_v1",
            name="My Agent",
            description="A helpful assistant.",
            # Tags can be Tag objects, dicts, or strings
            tags=[
                Tag(name="production", color="#28A745"),  # Tag object with explicit color
                {"name": "support", "color": "#007BFF"},  # Dict with color
                {"name": "v2"},                           # Dict without color (random color)
                "experimental"                            # String only (random color)
            ],
            image_url="https://example.com/agents/my-agent.png"
        )
```

Tags without colors automatically get random colors assigned via `Tag.generate_random_color()`.

You can also create tags programmatically:

```python
from agent_framework.core.models import Tag

# Create tag with random color
tag = Tag.from_name("development")

# Generate a random hex color
color = Tag.generate_random_color()  # Returns "#A3F2C1" format
```

## Choosing Your Approach

The Agent Framework provides two ways to create agents:

### Decision Tree

```
Do you want to use LlamaIndex?
│
├─ YES → Use LlamaIndexAgent
│   ├─ ✅ Fastest to implement (3 required methods)
│   ├─ ✅ Automatic memory management
│   ├─ ✅ Built-in streaming support
│   ├─ ✅ Rich ecosystem of tools
│   └─ 📖 See: LlamaIndex Agent Creation
│
└─ NO → Use BaseAgent
    ├─ ✅ Framework-agnostic (LangChain, Haystack, custom, etc.)
    ├─ ✅ Full control over agent behavior
    ├─ ✅ Custom streaming implementation
    ├─ ⚠️  More methods to implement (7 required)
    └─ 📖 See: BaseAgent Creation
```

### Comparison Table

| Feature | LlamaIndexAgent | BaseAgent |
|---------|----------------|-----------|
| **Required Methods** | 3 | 7 |
| **Complexity** | Low | Medium |
| **Framework** | LlamaIndex only | Any framework |
| **Memory** | Automatic | Manual |
| **Streaming** | Built-in | Custom implementation |
| **Best For** | Quick prototypes, LlamaIndex users | Custom frameworks, full control |

---

## LlamaIndex Agent Creation

### Overview

`LlamaIndexAgent` is a concrete implementation that provides LlamaIndex-specific functionality with automatic memory management and streaming support.

### Required Methods

You must implement these 3 methods:

#### 1. `get_agent_prompt() -> str`

Define the agent's system prompt.

```python
def get_agent_prompt(self) -> str:
    """Return the system prompt for the agent."""
    return """You are a helpful calculator assistant.
    You can perform basic arithmetic operations.
    Always show your work and explain the calculation steps."""
```

**Purpose**: Defines the agent's behavior, personality, and capabilities.

**Note**: Rich content capabilities (Mermaid diagrams, Chart.js charts, forms, options blocks, tables) are automatically injected into all agent system prompts. You don't need to add these instructions manually.

**Tips**:
- Be specific about the agent's role
- List available capabilities
- Provide behavioral guidelines
- Include examples if helpful

#### 2. `get_agent_tools() -> List[callable]`

Define the tools available to the agent.

```python
def get_agent_tools(self) -> List[callable]:
    """Return list of tools for the agent."""
    
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b
    
    return [add, multiply]
```

**Purpose**: Extends the agent's capabilities beyond text generation.

**Requirements**:
- Each tool must have a clear function name
- Docstring (LLM reads this to understand the tool)
- Type hints (helps LLM understand parameters)
- Return value (sent back to LLM)

#### 3. `initialize_agent(model_name, system_prompt, tools, **kwargs) -> None`

Initialize the LlamaIndex agent.

```python
async def initialize_agent(
    self,
    model_name: str,
    system_prompt: str,
    tools: List[callable],
    **kwargs
) -> None:
    """Initialize the LlamaIndex agent."""
    from llama_index.core.agent.workflow import FunctionAgent
    
    # Create LLM using helper method
    llm = self.create_llm(model_name)
    
    # Create agent
    self._agent_instance = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=system_prompt,
        verbose=kwargs.get('verbose', True)
    )
```

**Purpose**: Sets up the LlamaIndex agent with your configuration.

**Helper Method**: Use `self.create_llm(model_name)` to automatically create the correct LLM client (OpenAI, Anthropic, or Gemini) based on the model name.

### Optional Methods

Override these methods for advanced customization:

#### Context Management

```python
def create_fresh_context(self) -> Any:
    """Create a new conversation context."""
    from llama_index.core.workflow import Context
    return Context(self._agent_instance)

def serialize_context(self, ctx: Any) -> Dict[str, Any]:
    """Serialize context for persistence."""
    from llama_index.core.workflow import JsonSerializer
    return ctx.to_dict(serializer=JsonSerializer())

def deserialize_context(self, state: Dict[str, Any]) -> Any:
    """Deserialize context from saved state."""
    from llama_index.core.workflow import Context, JsonSerializer
    return Context.from_dict(
        self._agent_instance, 
        state, 
        serializer=JsonSerializer()
    )
```

**When to override**: If you need custom context management or state persistence.

#### MCP Tools

```python
def get_mcp_server_params(self) -> List[StdioServerParams]:
    """Configure external MCP tools."""
    from autogen_ext.tools.mcp import StdioServerParams
    from agent_framework import get_deno_command

    return [
        StdioServerParams(
            command=get_deno_command(),  # Automatically uses the correct Deno path
            args=['run', '-N', 'jsr:@pydantic/mcp-run-python', 'stdio'],
            read_timeout_seconds=120
        )
    ]
```

**When to override**: If you want to add Model Context Protocol tools (Python execution, file system access, etc.).

#### Welcome Message

```python
async def get_welcome_message(self) -> Optional[str]:
    """Return a greeting message for new sessions."""
    return f"Bonjour ! Je suis {self.name}.\n\n{self.description}"
```

**When to override**: When you want your agent to greet users when they start a new conversation.

**Behavior**:
- Called automatically when a new session is created via `/init`
- Message is saved as the first assistant message in the session
- Returned in `SessionInitResponse.welcome_message` field
- Default returns `None` (no welcome message)

#### Remote Configuration (Ops-Managed Agents)

```python
@classmethod
def get_use_remote_config(cls) -> bool:
    """Enable Elasticsearch-only configuration management."""
    return True
```

**When to override**: When you want the agent to be configured entirely via Elasticsearch, without code deployments overwriting the config.

**Code-Managed vs Ops-Managed Agents:**

| Aspect | Code-Managed (`False`) | Ops-Managed (`True`) |
|--------|------------------------|----------------------|
| Config source | Hardcoded in Python | Elasticsearch only |
| Server startup | Pushes config to ES if different | Skips pushing to ES |
| Session init | Merges ES + hardcoded | Reads ES only |
| Use case | Developer-controlled agents | Runtime-configurable agents |

**Example: Ops-Managed Agent**

```python
from agent_framework import LlamaIndexAgent

class OpsConfiguredAgent(LlamaIndexAgent):
    """Agent configured entirely via Elasticsearch."""
    
    def __init__(self):
        super().__init__(
            agent_id="ops_agent_v1",
            name="Ops Configured Agent",
            description="An agent managed by ops team via ES."
        )
    
    @classmethod
    def get_use_remote_config(cls) -> bool:
        """Config is managed via Elasticsearch/Kibana."""
        return True
    
    def get_agent_prompt(self) -> str:
        # Fallback prompt if ES config not available
        return "You are a helpful assistant."
    
    def get_agent_tools(self) -> list:
        return []
```

**Fallback behavior**: If `use_remote_config=True` but no ES config exists, the system:
1. Logs a warning
2. Falls back to hardcoded config
3. Pushes the hardcoded config to ES for future use

### Rich Content Configuration

All agents automatically receive rich content capabilities (Mermaid diagrams, Chart.js charts, forms, options blocks, tables). This is enabled by default.

To disable rich content for a specific session:

```python
# Via session configuration
session_config = {
    "user_id": "user123",
    "session_id": "session456",
    "enable_rich_content": False  # Disable rich content
}
```

Or via the Web UI by unchecking the "Enable rich content capabilities" checkbox.

### Complete Example

See [examples/simple_agent.py](../examples/simple_agent.py) for a complete working example.

```python
from agent_framework import LlamaIndexAgent, create_basic_agent_server
from typing import List

class CalculatorAgent(LlamaIndexAgent):
    """A simple calculator agent."""
    
    def __init__(self):
        super().__init__(
            agent_id="calculator_agent_v1",
            name="Calculator Agent",
            description="A helpful calculator assistant that can perform basic math operations."
        )
    
    def get_agent_prompt(self) -> str:
        return """You are a helpful calculator assistant.
        Use the provided tools to perform calculations."""
    
    def get_agent_tools(self) -> List[callable]:
        def add(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
        
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers together."""
            return a * b
        
        return [add, multiply]
    
    async def initialize_agent(
        self,
        model_name: str,
        system_prompt: str,
        tools: List[callable],
        **kwargs
    ) -> None:
        from llama_index.core.agent.workflow import FunctionAgent
        
        llm = self.create_llm(model_name)
        self._agent_instance = FunctionAgent(
            tools=tools,
            llm=llm,
            system_prompt=system_prompt,
            verbose=True
        )

if __name__ == "__main__":
    create_basic_agent_server(CalculatorAgent, port=8000)
```

---

## BaseAgent (Custom Framework) Creation

### Overview

`BaseAgent` is a framework-agnostic base class that allows you to integrate ANY AI framework (LangChain, Haystack, custom implementations, etc.) with the Agent Framework.

### Required Methods

You must implement these 7 methods:

#### 1. `get_agent_prompt() -> str`

Same as LlamaIndex - define the agent's system prompt.

```python
def get_agent_prompt(self) -> str:
    """Return the system prompt for the agent."""
    return "You are a helpful assistant with calculator capabilities."
```

#### 2. `get_agent_tools() -> List[callable]`

Same as LlamaIndex - define the tools available to the agent.

```python
def get_agent_tools(self) -> List[callable]:
    """Return list of tools for the agent."""
    
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    return [add]
```

#### 3. `initialize_agent(model_name, system_prompt, tools, **kwargs) -> None`

Initialize your custom framework's agent.

```python
async def initialize_agent(
    self,
    model_name: str,
    system_prompt: str,
    tools: List[callable],
    **kwargs
) -> None:
    """Initialize your custom framework's agent."""
    from agent_framework.core.model_clients import client_factory
    
    # Get LLM client (handles OpenAI, Anthropic, Gemini automatically)
    self._llm_client = client_factory.create_client(model_name=model_name)
    
    # Store configuration
    self._system_prompt = system_prompt
    self._tools = {tool.__name__: tool for tool in tools}
    
    # Initialize your framework here
    # Example for LangChain:
    # from langchain.agents import create_openai_functions_agent
    # self._agent = create_openai_functions_agent(...)
    
    # Example for Haystack:
    # from haystack.agents import Agent
    # self._agent = Agent(...)
```

**Purpose**: Set up your framework's agent with the provided configuration.

**Key Points**:
- Use `client_factory.create_client()` for automatic LLM provider detection
- Store system prompt and tools for use in `run_agent()`
- Initialize your framework's agent instance

#### 4. `create_fresh_context() -> Any`

Create a new conversation context.

```python
def create_fresh_context(self) -> Any:
    """Create a new conversation context."""
    return {
        "messages": [],  # Conversation history
        "metadata": {
            "session_id": self.current_session_id,
            "user_id": self.current_user_id,
        }
    }
```

**Purpose**: Initialize context for a new conversation.

**Return**: Any object your framework needs for context (dict, list, custom class, etc.).

**Examples**:
- LangChain: `return []` (list of messages)
- Haystack: `return {"conversation_history": [], "documents": []}`
- Custom: `return MyCustomContext()`

#### 5. `serialize_context(ctx) -> Dict[str, Any]`

Serialize context to dictionary for persistence.

```python
def serialize_context(self, ctx: Any) -> Dict[str, Any]:
    """Serialize context for persistence."""
    # For dict context, return as-is
    return ctx
    
    # For custom objects, extract data:
    # return {
    #     "messages": [msg.to_dict() for msg in ctx.messages],
    #     "metadata": ctx.metadata
    # }
```

**Purpose**: Convert context to JSON-serializable format for saving to database.

**Requirements**:
- Must return JSON-serializable dict (str, int, float, bool, None, list, dict)
- No custom objects, functions, or lambdas
- Convert datetime to ISO string if needed

#### 6. `deserialize_context(state) -> Any`

Deserialize dictionary to context object.

```python
def deserialize_context(self, state: Dict[str, Any]) -> Any:
    """Deserialize context from saved state."""
    # For dict context, return as-is
    return state
    
    # For custom objects, reconstruct:
    # ctx = MyCustomContext()
    # ctx.messages = [Message.from_dict(m) for m in state["messages"]]
    # return ctx
```

**Purpose**: Reconstruct context object from saved dictionary.

**Requirements**:
- Must return same type as `create_fresh_context()`
- Reconstruct any custom objects from the dict

#### 7. `run_agent(query, ctx, stream=False) -> Union[str, AsyncGenerator]`

Execute the agent with a query.

```python
async def run_agent(
    self,
    query: str,
    ctx: Any,
    stream: bool = False
) -> Union[str, AsyncGenerator]:
    """Execute the agent with a query."""
    if stream:
        return self._run_streaming(query, ctx)
    else:
        return await self._run_non_streaming(query, ctx)
```

**Purpose**: Main execution method that runs your framework's agent.

**Modes**:
- **Non-streaming** (`stream=False`): Return final response as string
- **Streaming** (`stream=True`): Return AsyncGenerator yielding RAW framework events

**Important**: When streaming, yield RAW framework-specific events. They will be converted to unified format via `process_streaming_event()`.

### Optional Methods

#### `process_streaming_event(event) -> Optional[Dict[str, Any]]`

Convert framework-specific streaming events to unified format.

```python
async def process_streaming_event(self, event: Any) -> Optional[Dict[str, Any]]:
    """Convert framework events to unified format."""
    # For dict events already in unified format
    if isinstance(event, dict) and "type" in event:
        return event
    
    # For LangChain events
    # if isinstance(event, dict) and event.get("type") == "llm_new_token":
    #     return {
    #         "type": "chunk",
    #         "content": event["token"],
    #         "metadata": {"source": "langchain"}
    #     }
    
    # Skip unknown events
    return None
```

**Purpose**: Normalize framework-specific events to standard format.

**Unified Format**:
```python
{
    "type": "chunk" | "tool_call" | "tool_result" | "activity" | "error",
    "content": str,
    "metadata": {...}  # Optional
}
```

**When to override**: Always override this when implementing streaming support.

### Complete Example

See [examples/custom_framework_agent.py](../examples/custom_framework_agent.py) for a complete working example with extensive comments.

```python
from agent_framework.core.base_agent import BaseAgent
from typing import List, Any, Dict, Union, AsyncGenerator

class CustomFrameworkAgent(BaseAgent):
    """Agent using custom AI framework."""
    
    def __init__(self):
        super().__init__(
            agent_id="custom_agent_v1",
            name="Custom Framework Agent",
            description="A helpful assistant using a custom AI framework."
        )
    
    def get_agent_prompt(self) -> str:
        return "You are a helpful assistant."
    
    def get_agent_tools(self) -> List[callable]:
        def add(a: float, b: float) -> float:
            """Add two numbers."""
            return a + b
        return [add]
    
    async def initialize_agent(
        self,
        model_name: str,
        system_prompt: str,
        tools: List[callable],
        **kwargs
    ) -> None:
        from agent_framework.core.model_clients import client_factory
        
        self._llm_client = client_factory.create_client(model_name=model_name)
        self._system_prompt = system_prompt
        self._tools = {tool.__name__: tool for tool in tools}
    
    def create_fresh_context(self) -> Any:
        return {"messages": []}
    
    def serialize_context(self, ctx: Any) -> Dict[str, Any]:
        return ctx
    
    def deserialize_context(self, state: Dict[str, Any]) -> Any:
        return state
    
    async def run_agent(
        self,
        query: str,
        ctx: Any,
        stream: bool = False
    ) -> Union[str, AsyncGenerator]:
        # Add user message to context
        ctx["messages"].append({"role": "user", "content": query})
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._system_prompt},
            *ctx["messages"]
        ]
        
        if stream:
            # Return streaming generator
            return self._stream_response(messages, ctx)
        else:
            # Return final response
            response = await self._llm_client.create(messages=messages)
            final_text = response.choices[0].message.content
            ctx["messages"].append({"role": "assistant", "content": final_text})
            return final_text
    
    async def _stream_response(self, messages, ctx):
        """Stream response chunks."""
        stream = await self._llm_client.create(messages=messages, stream=True)
        accumulated = ""
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                accumulated += delta.content
                yield {
                    "type": "chunk",
                    "content": delta.content,
                    "metadata": {}
                }
        
        ctx["messages"].append({"role": "assistant", "content": accumulated})
    
    async def process_streaming_event(self, event: Any) -> Optional[Dict[str, Any]]:
        """Convert events to unified format."""
        if isinstance(event, dict) and "type" in event:
            return event
        return None
```

---

## Adding Memory to Your Agent

The Memory Module provides long-term semantic memory capabilities for your agents. It enables agents to remember information across conversations, extract facts automatically, and provide personalized, context-aware responses.

### Overview

Memory is **completely optional** - agents work perfectly without it. When enabled, memory provides:

- **Automatic fact extraction** from conversations
- **Passive context injection** - relevant memories injected into prompts automatically
- **Active memory tools** - agent can explicitly recall, store, and forget information
- **Multiple providers** - Memori (SQL-native) and Graphiti (knowledge graph)
- **Hybrid mode** - use both providers simultaneously

### Enabling Memory

To enable memory, override the `get_memory_config()` method in your agent:

```python
from agent_framework import LlamaIndexAgent
from agent_framework.memory import MemoryConfig

class MyMemoryAgent(LlamaIndexAgent):
    def __init__(self):
        super().__init__(
            agent_id="memory_agent_v1",
            name="Memory Agent",
            description="An agent with long-term memory."
        )
    
    def get_agent_prompt(self) -> str:
        return "You are a helpful assistant with memory capabilities."
    
    def get_agent_tools(self) -> list:
        return []
    
    def get_memory_config(self):
        """Enable memory with Memori (SQLite)."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///agent_memory.db",
            passive_injection=True,
            auto_store_interactions=True
        )
```

### Memory Configuration Options

#### Memori (SQL-Native) - Simplest Setup

```python
def get_memory_config(self):
    return MemoryConfig.memori_simple(
        database_url="sqlite:///memory.db",  # SQLite, PostgreSQL, or MySQL
        passive_injection=True,               # Auto-inject context into prompts
        auto_store_interactions=True          # Auto-store conversations
    )
```

#### Graphiti (Knowledge Graph) - Advanced Relationships

```python
def get_memory_config(self):
    return MemoryConfig.graphiti_simple(
        use_falkordb=True,                    # Use FalkorDB (or Neo4j)
        falkordb_host="localhost",
        falkordb_port=6379,
        passive_injection=True,
        auto_store_interactions=True
    )
```

#### Hybrid Mode - Best of Both

```python
def get_memory_config(self):
    return MemoryConfig.hybrid(
        memori_database_url="sqlite:///memory.db",
        graphiti_use_falkordb=True,
        graphiti_falkordb_host="localhost",
        passive_injection=True,
        auto_store_interactions=True
    )
```

#### Disabled (Default)

```python
def get_memory_config(self):
    return None  # Or simply don't override the method
```

### Active Tools vs Passive Injection

Memory operates in two complementary modes:

#### Passive Injection (Automatic)

When `passive_injection=True`, the system automatically:
1. Retrieves relevant facts before each message
2. Injects them into the system prompt
3. Agent sees context without explicitly calling tools

**Best for:** General context awareness, user preferences, background information.

```python
# Passive injection settings
MemoryConfig.memori_simple(
    passive_injection=True,
    passive_injection_max_facts=10,      # Limit injected facts
    passive_injection_min_confidence=0.5  # Minimum relevance score
)
```

#### Active Tools (Agent-Controlled)

When memory is enabled, the agent automatically gets these tools:

- **`recall_memory(query)`** - Search memory for relevant facts
- **`store_memory(fact, fact_type)`** - Explicitly store a fact
- **`forget_memory(query)`** - Create a forget directive

**Best for:** Explicit memory operations, when agent needs to decide what to remember.

```python
# Active-only mode (no automatic injection)
def get_memory_config(self):
    return MemoryConfig.memori_simple(
        database_url="sqlite:///memory.db",
        passive_injection=False,           # Agent uses tools explicitly
        auto_store_interactions=True
    )
```

### Complete Memory Agent Example

```python
from typing import List
from agent_framework import LlamaIndexAgent, create_basic_agent_server
from agent_framework.memory import MemoryConfig

class PersonalAssistant(LlamaIndexAgent):
    """An assistant that remembers user preferences and history."""
    
    def __init__(self):
        super().__init__(
            agent_id="personal_assistant_v1",
            name="Personal Assistant",
            description="A helpful assistant that remembers your preferences."
        )
    
    def get_agent_prompt(self) -> str:
        return """You are a personal assistant with memory capabilities.
        
        You can remember:
        - User preferences (favorite foods, colors, etc.)
        - Important dates and events
        - Previous conversations and context
        
        Use your memory to provide personalized responses.
        When you learn something new about the user, acknowledge it.
        """
    
    def get_agent_tools(self) -> List[callable]:
        def set_reminder(event: str, date: str) -> str:
            """Set a reminder for an event on a specific date."""
            return f"Reminder set: {event} on {date}"
        
        return [set_reminder]
    
    def get_memory_config(self):
        """Enable memory with both passive injection and active tools."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///personal_assistant_memory.db",
            passive_injection=True,
            passive_injection_max_facts=10,
            auto_store_interactions=True
        )

if __name__ == "__main__":
    create_basic_agent_server(PersonalAssistant, port=8000)
```

### Installation

Memory providers are optional dependencies:

```bash
# Install with all memory support
uv add agent-framework-lib[memory]

# Or install providers separately
uv add agent-framework-lib[memori]    # SQL-native memory
uv add agent-framework-lib[graphiti]  # Knowledge graph memory
```

### Database Setup

**Memori (SQLite - No Setup Required):**
```python
database_url="sqlite:///memory.db"  # File created automatically
```

**Memori (PostgreSQL):**
```bash
# Start PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```
```python
database_url="postgresql://postgres:password@localhost/memory"
```

**Graphiti (FalkorDB):**
```bash
# Start FalkorDB
docker run -d -p 6379:6379 falkordb/falkordb:latest
```
```python
MemoryConfig.graphiti_simple(
    use_falkordb=True,
    falkordb_host="localhost",
    falkordb_port=6379
)
```

### Environment Variables

Memory can also be configured via environment variables:

```env
# Provider selection
MEMORY_PRIMARY_PROVIDER=memori
MEMORY_SECONDARY_PROVIDER=graphiti

# Behavior
MEMORY_PASSIVE_INJECTION=true
MEMORY_AUTO_STORE_INTERACTIONS=true

# Memori settings
MEMORI_DATABASE_URL=sqlite:///memory.db

# Graphiti settings
GRAPHITI_USE_FALKORDB=true
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
```

### More Information

- **[Memory Installation Guide](MEMORY_INSTALLATION.md)** - Detailed setup instructions
- **[Memory Examples](../examples/)** - Working code examples
  - `agent_with_memory_simple.py` - Memori with SQLite
  - `agent_with_memory_graphiti.py` - Graphiti with FalkorDB
  - `agent_with_memory_hybrid.py` - Both providers

---

## Skills Integration

The Skills System provides a modular way to organize agent capabilities into on-demand packages. Instead of loading all instructions into the system prompt (~3000 tokens), skills deliver instructions on-demand via tool responses, significantly reducing token consumption.

### Overview

Skills bundle together:
- **Metadata**: Lightweight info for discovery (~50 tokens per skill)
- **Instructions**: Detailed usage instructions (loaded on-demand)
- **Tools**: Associated tool functions (auto-loaded at initialization)
- **Dependencies**: Other skills required

### Key Insight: Auto-Loading

**Skill tools are automatically loaded at agent initialization.** You don't need to override `get_agent_tools()` to use skills - they work out of the box.

- **Tools are cheap** (~50-100 tokens each) - loaded automatically at init
- **Instructions are expensive** (~500 tokens each) - loaded on-demand via `load_skill()`

This means:
- Skill tools (e.g., `save_chart_as_image`) are always available
- Skill instructions are loaded only when the agent needs guidance
- No manual tool registration required

### Token Optimization

```
BEFORE (Rich Content Prompt):
  System Prompt = Base (~500 tokens) + Rich Content (~3000 tokens)
  Total per message: ~3500 tokens

AFTER (Skills System):
  System Prompt = Base (~500 tokens) + Skills Discovery (~200 tokens)
  Total per message: ~700 tokens
  
  When agent needs chart capability:
  → Skill tools already available (auto-loaded at init)
  → Agent calls load_skill("chart") for detailed instructions
  → Tool returns instructions (~500 tokens, ONE TIME)
  → Instructions are in conversation context, not repeated
```

### Enabling Skills in Your Agent

Skills are automatically available in all agents that inherit from `LlamaIndexAgent` or `BaseAgent`. **No special configuration is needed** - skill tools are auto-loaded.

```python
from agent_framework import LlamaIndexAgent

class MySkillsAgent(LlamaIndexAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_skills_agent",
            name="Skills Agent",
            description="An agent with on-demand skills."
        )
        # Built-in skills are automatically registered by BaseAgent.__init__
        # No need to call register_builtin_skills() manually
    
    def get_agent_prompt(self) -> str:
        return """You are a helpful assistant with access to a Skills System.
        
        Skill tools are always available to you.
        Use list_skills() to see available skills and their descriptions.
        Use load_skill("skill_name") to get detailed instructions for using a skill."""
    
    def get_agent_tools(self) -> list:
        # No need to add skill tools here - they're added automatically!
        # Only return custom tools specific to your agent
        return []
```

**What happens automatically:**
1. Built-in skills are registered at `BaseAgent.__init__`
2. Skill management tools (`list_skills`, `load_skill`, `unload_skill`) are added
3. **All skill tools** from registered skills are added to the agent
4. Skills discovery prompt is appended to your system prompt

> **Note**: `BaseAgent` already inherits from `SkillsMixin`, so all agents automatically have access to skills methods like `register_builtin_skills()`, `load_skill()`, `get_skill_tools()`, etc.

### Built-in Skills

The framework provides 12 built-in skills:

| Category | Skills | Description |
|----------|--------|-------------|
| **Visualization** | chart, mermaid, table | Chart.js charts, Mermaid diagrams, table images |
| **Document** | file, pdf, pdf_with_images, file_access | File operations, PDF generation |
| **Web** | web_search | Web and news search |
| **Multimodal** | multimodal | Image analysis |
| **UI** | form, optionsblock, image_display | Forms, option buttons, image display |

### Skill Management Operations

```python
# Built-in skills are automatically registered by BaseAgent.__init__
# No need to call register_builtin_skills() manually

# Register a custom skill (optional)
self.register_skill(my_custom_skill)

# Load a skill to get detailed instructions (tools are already available)
instructions = self.load_skill("chart")

# Unload a skill (frees context, tools remain available)
self.unload_skill("chart")

# Get skill management tools (automatically added to agent)
# list_skills, load_skill, unload_skill

# Get tools from loaded skills (for advanced use cases)
loaded_tools = self.get_loaded_skill_tools()

# Get instructions from loaded skills
instructions = self.get_loaded_skill_instructions()
```

**Important**: Skill tools are auto-loaded at initialization. The `load_skill()` function is for getting detailed instructions into the conversation context, not for making tools available.

### Creating Custom Skills

```python
from agent_framework.skills import Skill, SkillMetadata

WEATHER_INSTRUCTIONS = """
## Weather Skill Instructions

Use the get_weather() tool to fetch current weather.

**Parameters:**
- city: City name (e.g., "Paris", "New York")
- units: "celsius" or "fahrenheit" (default: celsius)

**Example:**
User: "What's the weather in Tokyo?"
→ Call get_weather(city="Tokyo", units="celsius")
"""

def create_weather_skill() -> Skill:
    def get_weather(city: str, units: str = "celsius") -> str:
        """Get current weather for a city."""
        # Your implementation here
        return f"Weather in {city}: Sunny, 22°{units[0].upper()}"
    
    return Skill(
        metadata=SkillMetadata(
            name="weather",
            description="Get current weather for any city",
            trigger_patterns=["weather", "temperature", "forecast"],
            category="web",
            version="1.0.0"
        ),
        instructions=WEATHER_INSTRUCTIONS,
        tools=[get_weather],
        dependencies=[],
        config={}
    )

# Register in your agent
custom_skill = create_weather_skill()
self.register_skill(custom_skill)
```

### File Storage Integration

Skills that use file storage (chart, pdf, file, etc.) need context injection during session configuration. Use the `configure_skill_tools_context()` method provided by `SkillsMixin`:

```python
async def configure_session(self, session_configuration):
    user_id = session_configuration.get('user_id', 'default_user')
    session_id = session_configuration.get('session_id')
    
    await self._ensure_file_storage()
    
    # Call parent to build the agent (this collects skill tool instances)
    await super().configure_session(session_configuration)
    
    # Configure context for ALL registered skill tools
    # This must be called AFTER super().configure_session()
    self.configure_skill_tools_context(
        file_storage=self.file_storage,
        user_id=user_id,
        session_id=session_id
    )
```

**Important**: Call `configure_skill_tools_context()` **after** `super().configure_session()` because that's when the skill tool instances are collected by `get_all_registered_skill_tools()`.

### Skills + Memory Combined Usage

Skills and Memory work together seamlessly. Both systems add their tools automatically at initialization:

**Tool Loading Order:**
1. Agent's custom tools (from `get_agent_tools()`)
2. Skill management tools (`list_skills`, `load_skill`, `unload_skill`)
3. All skill tools (chart, pdf, mermaid, etc.)
4. Memory tools (`recall_memory`, `store_memory`, `forget_memory`)

```python
from agent_framework import LlamaIndexAgent
from agent_framework.memory import MemoryConfig

class SkillsAndMemoryAgent(LlamaIndexAgent):
    """Agent with both skills and memory - no manual tool setup needed."""
    
    def __init__(self):
        super().__init__(
            agent_id="skills_memory_agent",
            name="Skills & Memory Agent",
            description="An agent with skills and long-term memory."
        )
        # Skills are automatically registered
        # Memory is configured via get_memory_config()
    
    def get_agent_prompt(self) -> str:
        return """You are a helpful assistant with skills and memory.
        
        Skills: Use list_skills() to see available capabilities.
        Memory: Use recall_memory() to remember past conversations."""
    
    def get_agent_tools(self) -> list:
        # No need to add skill or memory tools - they're added automatically!
        return []
    
    def get_memory_config(self):
        """Enable memory alongside skills."""
        return MemoryConfig.memori_simple(
            database_url="sqlite:///agent_memory.db",
            passive_injection=True,
            auto_store_interactions=True
        )
```

**Key Points:**
- `ENABLE_SKILLS` and memory configuration are independent settings
- No tool name conflicts between skills and memory
- Both systems can be used in the same conversation
- Skill tools and memory tools are both auto-loaded

### Environment Variable Control

Skills can be disabled via environment variable:

```bash
# Disable skills entirely (default: true)
ENABLE_SKILLS=false
```

When `ENABLE_SKILLS=false`:
- No skill management tools are added
- No skill tools are added
- Memory tools (if configured) still work normally

### Complete Skills Agent Example

See [examples/agent_example_multi_skills.py](../examples/agent_example_multi_skills.py) for a complete working example demonstrating:
- Automatic skill tools loading (no `get_agent_tools()` override needed)
- On-demand skill instruction loading via `load_skill()`
- File storage integration for file-related skills

See [examples/skills_demo_agent.py](../examples/skills_demo_agent.py) for a comprehensive example showing:
- All skill management operations
- Custom skill creation
- Skill search and discovery
- Token optimization best practices

### Skills vs Rich Content Prompt

| Aspect | Rich Content Prompt | Skills System |
|--------|---------------------|---------------|
| Token usage | ~3000 tokens always | ~200 tokens + on-demand instructions |
| Tool availability | All tools always | All tools always (auto-loaded) |
| Instructions | Always in prompt | Loaded on-demand via `load_skill()` |
| Flexibility | All or nothing | Load instructions as needed |
| Customization | Limited | Create custom skills |
| Discovery | None | Agent can search skills |
| Setup required | None | None (auto-configured) |

**Migration**: The Skills System is designed to complement or replace the rich content prompt. Built-in skills provide the same capabilities (charts, forms, tables, etc.) with better token efficiency. No code changes needed - skills work automatically.

### More Information

- **[Tools and MCP Guide](TOOLS_AND_MCP_GUIDE.md#converting-tools-to-skills)** - Converting tools to skills
- **[Skills Demo Example](../examples/skills_demo_agent.py)** - Comprehensive skills demonstration

---

## Streaming Architecture

### Overview

The Agent Framework uses a clear separation of concerns for streaming:

```
┌─────────────────────────────────────────────────────────────┐
│  Your Agent Implementation                                  │
│                                                             │
│  run_agent(stream=True)                                     │
│    └─> Yields RAW framework-specific events                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  BaseAgent.handle_message_stream() [FINAL - DO NOT OVERRIDE]│
│                                                             │
│  Orchestrates the streaming flow:                           │
│    1. Calls run_agent(stream=True)                          │
│    2. For each event, calls process_streaming_event()       │
│    3. Converts to StructuredAgentOutput                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Your Agent Implementation                                  │
│                                                             │
│  process_streaming_event(event)                             │
│    └─> Converts framework event to unified format          │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **`run_agent()`** = Framework-specific logic, yields RAW events
2. **`process_streaming_event()`** = Conversion layer, framework-specific
3. **`handle_message_stream()`** = Orchestration, framework-agnostic (DO NOT OVERRIDE)

### Event Flow

```
Your Framework          BaseAgent                    Client
───────────────         ─────────                    ──────
      │                     │                          │
      │  run_agent(stream)  │                          │
      │◄────────────────────│                          │
      │                     │                          │
      │  yield raw_event_1  │                          │
      ├────────────────────►│                          │
      │                     │                          │
      │                     │ process_streaming_event()│
      │                     │ (converts to unified)    │
      │                     │                          │
      │                     │  StructuredAgentOutput   │
      │                     ├─────────────────────────►│
      │                     │                          │
      │  yield raw_event_2  │                          │
      ├────────────────────►│                          │
      │                     │                          │
```

### Unified Event Format

All streaming events must be converted to this format:

```python
{
    "type": "chunk" | "tool_call" | "tool_result" | "activity" | "error",
    "content": str,
    "metadata": {...}  # Optional additional data
}
```

**Event Types**:
- **chunk**: Text content being streamed to the user
- **tool_call**: Agent is calling a tool
- **tool_result**: Result from a tool execution
- **activity**: General activity message (e.g., "thinking", "processing")
- **error**: Error occurred during processing

### Implementation Examples

#### Non-Streaming Mode

```python
async def run_agent(self, query, ctx, stream=False):
    if not stream:
        # Call your framework
        response = await my_framework.chat(query, ctx)
        # Return final response as string
        return response.text
```

#### Streaming Mode

```python
async def run_agent(self, query, ctx, stream=False):
    if stream:
        # Return async generator
        async def event_generator():
            async for event in my_framework.stream_chat(query, ctx):
                # Yield RAW framework events
                # DO NOT convert here - that happens in process_streaming_event()
                yield event
        return event_generator()
```

#### Event Conversion

```python
async def process_streaming_event(self, event):
    # Convert framework events to unified format
    if event.type == "text_chunk":
        return {
            "type": "chunk",
            "content": event.text,
            "metadata": {"source": "my_framework"}
        }
    elif event.type == "tool_request":
        return {
            "type": "tool_call",
            "content": "",
            "metadata": {
                "tool_name": event.tool_name,
                "tool_arguments": event.arguments
            }
        }
    # Skip unknown events
    return None
```

---

## Tool Integration

### Basic Tools

Tools are Python functions with clear docstrings and type hints:

```python
def calculate_total(items: List[Dict[str, float]]) -> float:
    """Calculate the total price of items.
    
    Args:
        items: List of items with 'price' and 'quantity' keys
    
    Returns:
        Total price
    """
    return sum(item['price'] * item['quantity'] for item in items)
```

### Tool Requirements

Each tool must have:
1. **Clear function name** (becomes tool name for LLM)
2. **Docstring** (LLM reads this to understand the tool)
3. **Type hints** (helps LLM understand parameters)
4. **Return value** (sent back to LLM)

### Accessing Session Context

Tools can access session context via `self`:

```python
def get_user_data(self) -> dict:
    """Get current user's data."""
    user_id = self.current_user_id
    session_id = self.current_session_id
    return {"user_id": user_id, "session_id": session_id}
```

### MCP Tools (Model Context Protocol)

Add external tools via MCP servers:

```python
def get_mcp_server_params(self) -> List[StdioServerParams]:
    """Configure external MCP tools."""
    from autogen_ext.tools.mcp import StdioServerParams
    from agent_framework import get_deno_command

    return [
        # Python execution
        StdioServerParams(
            command=get_deno_command(),  # Automatically uses the correct Deno path
            args=['run', '-N', 'jsr:@pydantic/mcp-run-python', 'stdio'],
            read_timeout_seconds=120
        ),
        # File system access
        StdioServerParams(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
            read_timeout_seconds=60
        )
    ]
```

See [agent_with_mcp.py](../examples/agent_with_mcp.py) for a complete example.

---

## Best Practices

### 1. System Prompts

**Good System Prompt**:
```python
def get_agent_prompt(self) -> str:
    return """You are a financial advisor assistant.

    Your capabilities:
    - Calculate investment returns
    - Analyze portfolio risk
    - Provide market insights
    
    Your guidelines:
    - Always show calculations step-by-step
    - Explain financial terms when used
    - Provide disclaimers for investment advice
    
    Your personality:
    - Professional but friendly
    - Patient and educational
    """
```

### 2. Tool Design

**Good Tool Design**:
```python
def calculate_roi(
    initial_investment: float,
    final_value: float,
    years: int
) -> Dict[str, float]:
    """Calculate return on investment with annualized rate.
    
    Args:
        initial_investment: Initial investment amount in dollars
        final_value: Final value in dollars
        years: Number of years invested
    
    Returns:
        Dictionary with 'total_return' and 'annualized_return'
    
    Example:
        >>> calculate_roi(1000, 1500, 5)
        {'total_return': 50.0, 'annualized_return': 8.45}
    """
    total_return = ((final_value - initial_investment) / initial_investment) * 100
    annualized_return = ((final_value / initial_investment) ** (1/years) - 1) * 100
    
    return {
        "total_return": round(total_return, 2),
        "annualized_return": round(annualized_return, 2)
    }
```

### 3. Error Handling

**Good Error Handling**:
```python
def divide(a: float, b: float) -> Union[float, str]:
    """Divide a by b with error handling."""
    try:
        if b == 0:
            return "Error: Cannot divide by zero"
        return a / b
    except Exception as e:
        logger.error(f"Division error: {e}")
        return f"Error: {str(e)}"
```

### 4. State Management

**Good State Management**:
```python
async def get_state(self) -> Dict[str, Any]:
    """Save only necessary state."""
    state = await super().get_state()
    
    # Save only what's needed
    state['user_preferences'] = self.user_preferences
    state['session_stats'] = {
        'messages': self.message_count,
        'tools_used': self.tools_used
    }
    
    # Don't save large temporary data
    # state['large_cache'] = self.cache  # ❌ Bad
    
    return state
```

---

## Examples

### LlamaIndex Examples

- **[simple_agent.py](../examples/simple_agent.py)** - Basic calculator agent
- **[agent_with_file_storage.py](../examples/agent_with_file_storage.py)** - Agent with file upload/download
- **[agent_with_mcp.py](../examples/agent_with_mcp.py)** - Agent with MCP tools

### Memory Examples

- **[agent_with_memory_simple.py](../examples/agent_with_memory_simple.py)** - Memori with SQLite (simplest setup)
- **[agent_with_memory_graphiti.py](../examples/agent_with_memory_graphiti.py)** - Graphiti with FalkorDB
- **[agent_with_memory_hybrid.py](../examples/agent_with_memory_hybrid.py)** - Both providers combined

### BaseAgent Examples

- **[custom_framework_agent.py](../examples/custom_framework_agent.py)** - Complete custom framework integration with extensive comments

### Running Examples

```bash
# Install dependencies
uv add agent-framework[llamaindex]

# Set API key
export OPENAI_API_KEY=your-key-here

# Run an example
python examples/simple_agent.py

# Open browser to http://localhost:8100/testapp
```

---

## Next Steps

- **[Tools and MCP Guide](TOOLS_AND_MCP_GUIDE.md)** - Advanced tool integration
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Architecture](../ARCHITECTURE.md)** - System architecture details
- **[Testing Guide](UV_TESTING_GUIDE.md)** - Testing best practices

---

**Need Help?**

- Review the [examples](../examples/) directory
- Check the [API Reference](api-reference.md)
- Open an issue on GitHub
