# Docker Development Environment Setup

This guide explains how to use Docker Compose to run all external services required by the Agent Framework for local development.

## Available Services

| Service | Port(s) | Profile | Purpose | Default Credentials |
|---------|---------|---------|---------|---------------------|
| Elasticsearch | 9200 | storage, all | Session storage, logging, configuration | None (security disabled) |
| MongoDB | 27017 | storage, all | Alternative session storage | None (no auth) |
| PostgreSQL | 5432 | memory, all | Memori memory provider | postgres / postgres |
| FalkorDB | 6379 | memory, all | Graphiti memory provider (Redis-compatible) | None (no auth) |
| MinIO | 9000 (API), 9001 (Console) | storage, all | S3-compatible file storage | minioadmin / minioadmin |

## Quick Start

### Start All Services

```bash
# Start all services
docker-compose --profile all up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Configure Your Application

```bash
# Copy the Docker environment template
cp .env.docker .env

# Edit .env to add your LLM API keys
# OPENAI_API_KEY=sk-your-key-here
```

### Stop Services

```bash
# Stop all services (preserves data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Using Profiles

Profiles allow you to start only the services you need, reducing resource usage.

### Storage Profile
Start session storage and file storage services:
```bash
docker-compose --profile storage up -d
```
Services: Elasticsearch, MongoDB, MinIO

### Memory Profile
Start memory provider services:
```bash
docker-compose --profile memory up -d
```
Services: PostgreSQL, FalkorDB

### All Profile
Start the complete stack:
```bash
docker-compose --profile all up -d
```
Services: All of the above

### Individual Services
Start specific services by name:
```bash
# Just Elasticsearch
docker-compose up -d elasticsearch

# Elasticsearch and MongoDB
docker-compose up -d elasticsearch mongodb
```

## Service Details

### Elasticsearch (Session Storage)

Primary backend for production deployments. Provides session storage, centralized logging, and dynamic configuration.

```bash
# Test connection
curl http://localhost:9200/_cluster/health

# View indices
curl http://localhost:9200/_cat/indices?v
```

Environment variables:
```env
SESSION_STORAGE_TYPE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_ENABLED=true
```

### MongoDB (Alternative Session Storage)

Simpler alternative to Elasticsearch for session storage.

```bash
# Test connection
mongosh --eval "db.adminCommand('ping')"
```

Environment variables:
```env
SESSION_STORAGE_TYPE=mongodb
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
```

### PostgreSQL (Memori Memory Provider)

SQL-based memory provider for semantic memory features.

```bash
# Test connection
pg_isready -h localhost -p 5432

# Connect to database
psql -h localhost -U postgres -d agent_memory
```

Environment variables:
```env
MEMORI_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_memory
```

### FalkorDB (Graphiti Memory Provider)

Graph database for knowledge graph-based memory. Uses Redis-compatible protocol.

```bash
# Test connection
redis-cli -p 6379 ping
```

Environment variables:
```env
GRAPHITI_USE_FALKORDB=true
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
```

### MinIO (File Storage)

S3-compatible object storage for file uploads and storage.

```bash
# Test API health
curl http://localhost:9000/minio/health/live

# Access web console
open http://localhost:9001
```

Environment variables:
```env
FILE_STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=agent-files
MINIO_SECURE=false
```

## Common Use Cases

### Development with Elasticsearch Only

For testing session storage and logging:
```bash
docker-compose up -d elasticsearch
```

### Testing Memory Features

For testing Memori and Graphiti memory providers:
```bash
docker-compose --profile memory up -d
```

### Full Production-Like Environment

For comprehensive testing with all backends:
```bash
docker-compose --profile all up -d
cp .env.docker .env
# Add your LLM API keys to .env
```

### Running Example Agents

```bash
# Start required services
docker-compose --profile all up -d

# Configure environment
cp .env.docker .env
# Edit .env with your API keys

# Run an example agent
cd examples
uv run python simple_agent.py
```

## Troubleshooting

### Port Conflicts

If a port is already in use:

```bash
# Check what's using the port
lsof -i :9200

# Option 1: Stop the conflicting service
# Option 2: Create docker-compose.override.yml with different ports
```

Example `docker-compose.override.yml`:
```yaml
services:
  elasticsearch:
    ports:
      - "9201:9200"
```

### Service Won't Start

Check service logs:
```bash
docker-compose logs elasticsearch
docker-compose logs postgres
```

### Elasticsearch Memory Issues

If Elasticsearch fails with memory errors:

1. Increase Docker memory allocation (Docker Desktop → Settings → Resources)
2. Or reduce heap size in docker-compose.override.yml:
```yaml
services:
  elasticsearch:
    environment:
      - ES_JAVA_OPTS=-Xms256m -Xmx512m
```

### Health Check Failures

Services may take time to become healthy. Check status:
```bash
docker-compose ps
```

Wait for all services to show "healthy" status before connecting.

### Data Persistence

Data is stored in named volumes. To reset:
```bash
# Remove specific volume
docker volume rm agentframework_elasticsearch_data

# Remove all project volumes
docker-compose down -v
```

### Connection Refused Errors

Ensure services are running and healthy:
```bash
docker-compose ps
docker-compose logs <service-name>
```

For Elasticsearch, wait for the cluster to be ready:
```bash
curl http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=60s
```

## Resource Requirements

Minimum recommended resources for running all services:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 10 GB free space

For limited resources, use profiles to run only needed services.
