"""
Memory Providers for Agent Framework.

Available providers:
- MemoriProvider: SQL-native, simple setup, fast extraction
- GraphitiProvider: Knowledge graph, temporal queries, complex relationships

Usage:
    ```python
    from agent_framework.memory.providers import MemoriProvider, GraphitiProvider
    from agent_framework.memory.config import MemoriConfig, GraphitiConfig
    
    # Memori (simple)
    memori = MemoriProvider(MemoriConfig(database_url="sqlite:///memory.db"))
    await memori.initialize()
    
    # Graphiti (advanced)
    graphiti = GraphitiProvider(GraphitiConfig(use_falkordb=True))
    await graphiti.initialize()
    ```

Version: 0.1.0
"""

from .graphiti_provider import GRAPHITI_AVAILABLE, GraphitiProvider
from .memori_provider import MEMORI_AVAILABLE, MemoriProvider


__all__ = [
    "MemoriProvider",
    "MEMORI_AVAILABLE",
    "GraphitiProvider",
    "GRAPHITI_AVAILABLE",
]
