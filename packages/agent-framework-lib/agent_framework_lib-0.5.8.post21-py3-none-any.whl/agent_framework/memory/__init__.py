"""
Memory Module for Agent Framework.

Provides long-term semantic memory capabilities for agents using:
- Memori: SQL-native, simple setup, fast fact extraction
- Graphiti: Temporal knowledge graph, complex relationships

Memory is optional and configured within agent classes following the
framework's encapsulation philosophy.

Quick Start:
    ```python
    from agent_framework import LlamaIndexAgent
    from agent_framework.memory import MemoryConfig
    
    class MyAgent(LlamaIndexAgent):
        def get_memory_config(self):
            # Simple Memori setup
            return MemoryConfig.memori_simple()
            
            # Or advanced Graphiti
            # return MemoryConfig.graphiti_simple()
            
            # Or hybrid (both)
            # return MemoryConfig.hybrid()
    ```

Configuration via Environment:
    ```bash
    export MEMORY_PRIMARY_PROVIDER=memori
    export MEMORI_DATABASE_URL=sqlite:///memory.db
    
    # For hybrid mode
    export MEMORY_SECONDARY_PROVIDER=graphiti
    export GRAPHITI_USE_FALKORDB=true
    ```

Available Classes:
    - MemoryConfig: Main configuration (with factory methods)
    - MemoriConfig: Memori-specific settings
    - GraphitiConfig: Graphiti-specific settings
    - MemoryManager: Orchestrates providers
    - MemoryProviderInterface: Base interface for providers
    - MemoryFact: Unified fact representation
    - MemoryContext: Retrieved memory context

Version: 0.1.0
"""

# Configuration
# Agent integration
from .agent_mixin import (
    MemoryMixin,
    inject_memory_into_prompt,
)

# Base types
from .base import (
    MemoryContext,
    MemoryFact,
    MemoryProviderInterface,
    MemoryType,
)
from .config import (
    GraphitiConfig,
    MemoriConfig,
    MemoryConfig,
)

# Manager
from .manager import (
    MemoryManager,
    create_memory_manager,
)

# Provider availability flags
# Providers (for advanced usage)
from .providers import (
    GRAPHITI_AVAILABLE,
    MEMORI_AVAILABLE,
    GraphitiProvider,
    MemoriProvider,
)

# Tools (auto-added to agents)
from .tools import (
    create_memory_tools,
    get_memory_tools_descriptions,
)


__all__ = [
    # Configuration
    "MemoryConfig",
    "MemoriConfig",
    "GraphitiConfig",

    # Base types
    "MemoryProviderInterface",
    "MemoryType",
    "MemoryFact",
    "MemoryContext",

    # Manager
    "MemoryManager",
    "create_memory_manager",

    # Agent integration
    "MemoryMixin",
    "inject_memory_into_prompt",

    # Tools (auto-added to agents)
    "create_memory_tools",
    "get_memory_tools_descriptions",

    # Availability flags
    "MEMORI_AVAILABLE",
    "GRAPHITI_AVAILABLE",

    # Providers
    "MemoriProvider",
    "GraphitiProvider",
]

__version__ = "0.3.5.1"
