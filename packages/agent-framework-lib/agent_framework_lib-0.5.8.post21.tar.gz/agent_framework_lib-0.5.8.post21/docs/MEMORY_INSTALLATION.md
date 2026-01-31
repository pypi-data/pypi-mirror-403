# Memory Module - Installation & Setup Guide

Complete guide for installing and configuring the Memory Module in Agent Framework.

## Quick Installation

### Option 1: Memori Only (Simplest)

```bash
# Install with Memori support
uv add agent-framework-lib[memori]

# Or with pip
pip install agent-framework-lib[memori]
```

**No additional setup required!** Uses SQLite by default.

### Option 2: Graphiti Only

```bash
# Install with Graphiti support
uv add agent-framework-lib[graphiti]

# Requires graph database (see below)
```

### Option 3: Both Providers (Hybrid)

```bash
# Install both memory providers
uv add agent-framework-lib[memory]

# This installs both memori and graphiti-core
```

### Option 4: Everything

```bash
# Install all optional dependencies
uv add agent-framework-lib[all]
```

---

## Database Setup

### Memori Databases

#### SQLite (Default - No Setup)

```python
from agent_framework.memory import MemoryConfig

# Uses sqlite:///agent_memory.db automatically
config = MemoryConfig.memori_simple()
```

**Pros:**
- Zero setup
- Perfect for development
- Single file database

**Cons:**
- Not suitable for high concurrency
- Limited to single machine

#### PostgreSQL (Production)

```bash
# 1. Install PostgreSQL
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql
sudo systemctl start postgresql

# 2. Create database
createdb agent_memory

# 3. Configure connection
export MEMORI_DATABASE_URL="postgresql://user:password@localhost/agent_memory"
```

```python
config = MemoryConfig.memori_simple(
    database_url="postgresql://user:password@localhost/agent_memory"
)
```

**Pros:**
- Production-ready
- High concurrency
- ACID compliance
- Scalable

#### MySQL/MariaDB

```bash
# 1. Install MySQL
brew install mysql  # macOS
sudo apt-get install mysql-server  # Ubuntu

# 2. Create database
mysql -u root -p
CREATE DATABASE agent_memory;

# 3. Configure
export MEMORI_DATABASE_URL="mysql://user:password@localhost/agent_memory"
```

```python
config = MemoryConfig.memori_simple(
    database_url="mysql://user:password@localhost/agent_memory"
)
```

---

### Graphiti Databases

#### FalkorDB (Recommended - Simpler)

```bash
# 1. Start FalkorDB with Docker
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest

# 2. Verify it's running
docker ps | grep falkordb

# 3. Configure environment
export GRAPHITI_USE_FALKORDB=true
export FALKORDB_HOST=localhost
export FALKORDB_PORT=6379
```

```python
config = MemoryConfig.graphiti_simple(
    use_falkordb=True,
    falkordb_host="localhost",
    falkordb_port=6379
)
```

**Pros:**
- Simpler than Neo4j
- Redis-compatible protocol
- Lightweight
- Fast setup

**Cons:**
- Newer project (less mature)
- Smaller community

#### Neo4j (Enterprise-Grade)

```bash
# 1. Start Neo4j with Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 2. Access web interface
open http://localhost:7474

# 3. Configure environment
export GRAPHITI_USE_FALKORDB=false
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
```

```python
from agent_framework.memory import MemoryConfig, GraphitiConfig

config = MemoryConfig(
    primary_provider="graphiti",
    graphiti=GraphitiConfig(
        use_falkordb=False,
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
)
```

**Pros:**
- Mature, battle-tested
- Rich ecosystem
- Advanced features
- Great tooling

**Cons:**
- More complex setup
- Heavier resource usage

#### Neo4j Aura (Cloud - Managed)

Neo4j Aura is a fully managed cloud service. Perfect for production without infrastructure management.

```bash
# 1. Create a Neo4j Aura instance at https://neo4j.com/cloud/aura/
# 2. Get your connection URI (neo4j+s://xxx.databases.neo4j.io)
# 3. Configure environment
export GRAPHITI_USE_FALKORDB=false
export NEO4J_URI="neo4j+s://xxx.databases.neo4j.io"
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your-aura-password
export GRAPHITI_SKIP_INDEX_CREATION=true  # Required for Aura!
```

```python
config = MemoryConfig.graphiti_simple(
    use_falkordb=False,
    neo4j_uri="neo4j+s://xxx.databases.neo4j.io",
    neo4j_user="neo4j",
    neo4j_password="your-aura-password",
    skip_index_creation=True,  # Aura manages indices
)
```

**Important:** Set `skip_index_creation=True` for Neo4j Aura because:
- Aura may already have indices created
- Some index operations require elevated permissions
- Avoids "index already exists" errors

#### Environment Isolation (Multi-Environment)

Share a single Neo4j/FalkorDB instance across dev, staging, and production by prefixing `group_id` with an environment name:

```bash
# Development
export GRAPHITI_ENVIRONMENT=dev

# Staging
export GRAPHITI_ENVIRONMENT=staging

# Production
export GRAPHITI_ENVIRONMENT=prod
```

```python
config = MemoryConfig.graphiti_simple(
    use_falkordb=False,
    neo4j_uri="neo4j+s://xxx.databases.neo4j.io",
    neo4j_user="neo4j",
    neo4j_password="password",
    environment="dev",  # Prefixes all group_ids with "dev_"
)
```

**How it works:**
- User "alice" in dev → `group_id = "dev_alice"`
- User "alice" in prod → `group_id = "prod_alice"`
- Data is completely isolated between environments
- Query with Cypher: `MATCH (n) WHERE n.group_id STARTS WITH 'dev_' RETURN n`

---

## Environment Variables

### Complete Environment Configuration

```bash
# ============================================================================
# Memory Provider Selection
# ============================================================================
export MEMORY_PRIMARY_PROVIDER=memori        # memori | graphiti | none
export MEMORY_SECONDARY_PROVIDER=graphiti    # Optional for hybrid mode

# ============================================================================
# Passive Injection Settings
# ============================================================================
export MEMORY_PASSIVE_INJECTION=true         # Auto-inject context
export MEMORY_PASSIVE_MAX_FACTS=10           # Max facts to inject
export MEMORY_PASSIVE_MIN_CONFIDENCE=0.5     # Min relevance score

# ============================================================================
# Performance Optimization Settings
# ============================================================================
export MEMORY_ASYNC_STORE=true               # Fire-and-forget storage (default: true)
export MEMORY_PASSIVE_PRIMARY_ONLY=true      # Primary-only passive injection (default: true)
export MEMORY_ASYNC_MAX_CONCURRENT=10        # Max concurrent background tasks
export MEMORY_ASYNC_TIMEOUT=30.0             # Shutdown timeout for pending tasks (seconds)

# ============================================================================
# Behavior Settings
# ============================================================================
export MEMORY_AUTO_STORE=true                # Auto-store interactions
export MEMORY_MAX_CONTEXT_FACTS=20           # Max facts for tools

# ============================================================================
# Memori Configuration
# ============================================================================
export MEMORI_DATABASE_URL=sqlite:///agent_memory.db
# Or PostgreSQL:
# export MEMORI_DATABASE_URL=postgresql://user:pass@localhost/agent_memory
# Or MySQL:
# export MEMORI_DATABASE_URL=mysql://user:pass@localhost/agent_memory

export MEMORI_API_KEY=                       # Optional: Memori API key

# ============================================================================
# Graphiti Configuration (FalkorDB)
# ============================================================================
export GRAPHITI_USE_FALKORDB=true
export FALKORDB_HOST=localhost
export FALKORDB_PORT=6379
export FALKORDB_PASSWORD=                    # Optional

# ============================================================================
# Graphiti Configuration (Neo4j)
# ============================================================================
export GRAPHITI_USE_FALKORDB=false
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
export NEO4J_DATABASE=neo4j

# ============================================================================
# Graphiti Advanced Settings (v0.5.0+)
# ============================================================================
export GRAPHITI_ENVIRONMENT=dev              # Environment prefix (dev, staging, prod)
export GRAPHITI_SKIP_INDEX_CREATION=false    # Skip index creation (for Neo4j Aura)

# ============================================================================
# LLM Configuration (for fact extraction)
# ============================================================================
export GRAPHITI_LLM_MODEL=gpt-4o-mini
export GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small
export GRAPHITI_EMBEDDING_DIM=1536
```

---

## Performance Optimization

The Memory Module includes performance optimizations that significantly reduce agent response latency, especially in hybrid mode.

### Async Storage (Fire-and-Forget)

When `async_store=True` (default), memory storage operations run in the background without blocking agent responses.

**Benefits:**
- Agent responses return immediately
- Storage happens asynchronously in background tasks
- No latency impact from slow secondary providers (e.g., Graphiti)

**Trade-offs:**
- Potential data loss if process crashes before storage completes
- Pending tasks are tracked and completed gracefully on shutdown

**Configuration:**
```python
# Via code
config = MemoryConfig.hybrid(
    async_store=True,  # Default: True
)

# Via environment
export MEMORY_ASYNC_STORE=true
export MEMORY_ASYNC_MAX_CONCURRENT=10  # Max concurrent background tasks
export MEMORY_ASYNC_TIMEOUT=30.0       # Shutdown timeout (seconds)
```

### Primary-Only Passive Injection

When `passive_injection_primary_only=True` (default), automatic context injection only queries the fast primary provider (Memori).

**Benefits:**
- Passive injection latency reduced from ~200-500ms to ~50-100ms
- Agent responses feel much faster
- Active recall tools still query both providers for comprehensive results

**Trade-offs:**
- Passive context may miss complex relationships from Graphiti
- Use active `recall_memory()` tool when you need full hybrid results

**Configuration:**
```python
# Via code
config = MemoryConfig.hybrid(
    passive_injection_primary_only=True,  # Default: True
)

# Via environment
export MEMORY_PASSIVE_PRIMARY_ONLY=true
```

### Performance Comparison

| Scenario | Before Optimization | After Optimization |
|----------|--------------------|--------------------|
| Passive injection (hybrid) | ~200-500ms (both providers) | ~50-100ms (primary only) |
| Store interaction | Blocks response | Returns immediately |
| Agent response latency | Includes store time | Excludes store time |

### When to Disable Optimizations

**Disable async storage (`async_store=False`) when:**
- You need guaranteed storage before response
- Running in environments where background tasks may be killed
- Debugging storage issues

**Disable primary-only passive (`passive_injection_primary_only=False`) when:**
- You need Graphiti's complex relationships in every response
- Primary provider is unreliable
- Latency is not a concern

**Example with optimizations disabled:**
```python
config = MemoryConfig.hybrid(
    async_store=False,  # Wait for storage to complete
    passive_injection_primary_only=False,  # Query both providers
)
```

---

## Docker Compose Setup

### Complete Stack (Memori + Graphiti)

```yaml
version: '3.8'

services:
  # Your agent application
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Memory configuration
      - MEMORY_PRIMARY_PROVIDER=memori
      - MEMORY_SECONDARY_PROVIDER=graphiti
      - MEMORY_PASSIVE_INJECTION=true
      
      # Memori (PostgreSQL)
      - MEMORI_DATABASE_URL=postgresql://postgres:password@postgres/agent_memory
      
      # Graphiti (FalkorDB)
      - GRAPHITI_USE_FALKORDB=true
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      
      # LLM
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - falkordb

  # PostgreSQL for Memori
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: agent_memory
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # FalkorDB for Graphiti
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data

volumes:
  postgres_data:
  falkordb_data:
```

**Usage:**
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f agent

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Verification & Testing

### 1. Check Installation

```bash
# Check if packages are installed
uv pip list | grep memori
uv pip list | grep graphiti
```

### 2. Test Database Connections

```python
# test_memory_setup.py
import asyncio
from agent_framework.memory import MemoryConfig, MemoryManager

async def test_memori():
    """Test Memori connection."""
    config = MemoryConfig.memori_simple()
    manager = MemoryManager(config)
    
    success = await manager.initialize()
    if success:
        print("✅ Memori initialized successfully")
        status = manager.get_provider_status()
        print(f"Status: {status}")
    else:
        print("❌ Memori initialization failed")
    
    await manager.close()

async def test_graphiti():
    """Test Graphiti connection."""
    config = MemoryConfig.graphiti_simple()
    manager = MemoryManager(config)
    
    success = await manager.initialize()
    if success:
        print("✅ Graphiti initialized successfully")
        status = manager.get_provider_status()
        print(f"Status: {status}")
    else:
        print("❌ Graphiti initialization failed")
    
    await manager.close()

async def main():
    print("Testing Memory Module Setup\n")
    print("=" * 50)
    
    print("\n1. Testing Memori...")
    await test_memori()
    
    print("\n2. Testing Graphiti...")
    await test_graphiti()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
# Run test
uv run python test_memory_setup.py
```

### 3. Run Unit Tests

```bash
# Run memory configuration tests
uv run pytest tests/test_memory_config.py -v

# Run with coverage
uv run pytest tests/test_memory_config.py --cov=agent_framework.memory
```

### 4. Run Example

```bash
# Run memory example
uv run python examples/agent_with_memory_graphiti.py``
uv run python examples/agent_with_memory_simple.py
uv run python examples/agent_with_memory_hybrid.py

```

---

## Troubleshooting

### Issue: "Memori is not installed"

**Solution:**
```bash
uv add memori
# or
pip install memori
```

### Issue: "Graphiti is not installed"

**Solution:**
```bash
uv add graphiti-core
# For FalkorDB support:
uv add graphiti-core[falkordb]
```

### Issue: "Failed to connect to FalkorDB"

**Check if running:**
```bash
docker ps | grep falkordb
```

**Start if not running:**
```bash
docker run -d -p 6379:6379 falkordb/falkordb:latest
```

**Test connection:**
```bash
# Install redis-cli
brew install redis  # macOS
sudo apt-get install redis-tools  # Ubuntu

# Test connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

### Issue: "Failed to connect to PostgreSQL"

**Check if running:**
```bash
# macOS
brew services list | grep postgresql

# Ubuntu
sudo systemctl status postgresql
```

**Test connection:**
```bash
psql -h localhost -U postgres -d agent_memory
```

### Issue: "Memory not initializing"

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your agent
```

**Check provider availability:**
```python
from agent_framework.memory.providers import MEMORI_AVAILABLE, GRAPHITI_AVAILABLE

print(f"Memori available: {MEMORI_AVAILABLE}")
print(f"Graphiti available: {GRAPHITI_AVAILABLE}")
```

### Issue: "SQLAlchemy errors with Memori"

**Install database driver:**
```bash
# PostgreSQL
uv add psycopg2-binary

# MySQL
uv add pymysql
```

---

## Production Deployment

### Recommended Setup

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Stack                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Agent Application                                           │
│    ├─ Memory: Hybrid (Memori + Graphiti)                    │
│    ├─ Passive Injection: Enabled                            │
│    └─ Auto-store: Enabled                                   │
│                                                              │
│  Memori → PostgreSQL (managed service)                      │
│    ├─ AWS RDS / Google Cloud SQL / Azure Database           │
│    ├─ Automated backups                                     │
│    └─ Read replicas for scaling                             │
│                                                              │
│  Graphiti → Neo4j (managed service)                         │
│    ├─ Neo4j Aura / AWS / GCP                                │
│    ├─ Automated backups                                     │
│    └─ Clustering for HA                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Environment Variables (Production)

```bash
# Use managed database URLs
export MEMORI_DATABASE_URL="postgresql://user:pass@rds.amazonaws.com/memory"
export NEO4J_URI="neo4j+s://xxx.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="${NEO4J_PASSWORD}"  # From secrets manager

# Optimize for production
export MEMORY_PASSIVE_INJECTION=true
export MEMORY_PASSIVE_MAX_FACTS=15
export MEMORY_AUTO_STORE=true

# Performance optimizations (recommended for production)
export MEMORY_ASYNC_STORE=true               # Fire-and-forget storage
export MEMORY_PASSIVE_PRIMARY_ONLY=true      # Fast primary-only passive injection
export MEMORY_ASYNC_MAX_CONCURRENT=10        # Limit concurrent background tasks
export MEMORY_ASYNC_TIMEOUT=30.0             # Graceful shutdown timeout
```

### Monitoring

```python
# Check memory status in your application
status = agent.get_memory_status()
logger.info(f"Memory status: {status}")

# Monitor provider health
if not status["initialized"]:
    logger.error("Memory system not initialized!")
    # Alert / fallback logic
```

---

## Memory Tools Are Added Automatically

When you define `get_memory_config()` in your agent, the framework automatically adds memory tools to your agent:
- `recall_memory(query)` - Search memory for relevant facts
- `store_memory(fact, fact_type)` - Save new facts to memory
- `forget_memory(query)` - Mark facts as outdated

**No need to add these tools manually!** Just define `get_memory_config()`:

```python
class MyAgent(LlamaIndexAgent):
    def get_memory_config(self):
        return MemoryConfig.hybrid(
            memori_database_url="sqlite:///agent_memory.db",
            graphiti_use_falkordb=True,
            passive_injection=True,
        )
    
    def get_agent_tools(self):
        # Your custom tools here - memory tools are added automatically
        return [my_custom_tool]
```

**⚠️ Important:** If you override `initialize_agent()` (e.g., for MCP integration), use the `tools` parameter which already contains memory tools:

```python
async def initialize_agent(self, model_name, system_prompt, tools, **kwargs):
    # 'tools' already contains get_agent_tools() + memory tools
    all_tools = list(tools) + self.mcp_tools  # Add your extra tools
    await super().initialize_agent(model_name, system_prompt, all_tools, **kwargs)
```

See `TOOLS_AND_MCP_GUIDE.md` for more details.

---

## Next Steps

1. ✅ Install memory providers
2. ✅ Setup databases
3. ✅ Configure environment
4. ✅ Test connections
5. 📖 Read `agent_framework/memory/README.md`
6. 💻 Try `examples/agent_with_memory_simple.py`
7. 📚 Review `docs/SPEC_MEMORY_MODULE.MD`

---

## Support

- **Documentation**: `docs/SPEC_MEMORY_MODULE.MD`
- **Examples**: `examples/agent_with_memory_simple.py`
- **Tests**: `tests/test_memory_config.py`
- **Issues**: GitHub Issues

## Version

Current version: 0.5.0

### Changelog
- **0.5.0**: Added environment isolation, skip_index_creation, Neo4j Aura support, improved memory tools
- **0.2.0**: Added performance optimizations (async storage, primary-only passive injection)
- **0.1.0**: Initial release with Memori and Graphiti support
