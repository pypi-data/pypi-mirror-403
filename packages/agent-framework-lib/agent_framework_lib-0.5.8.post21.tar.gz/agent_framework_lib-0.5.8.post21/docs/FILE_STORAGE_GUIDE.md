# File Storage Guide - Agent Framework

This guide provides comprehensive documentation for the file storage system in the Agent Framework, including all storage backends, metadata management, configuration, and migration procedures.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Selection & Priority](#backend-selection--priority)
3. [Storage Backends](#storage-backends)
   - [Local File Storage](#local-file-storage)
   - [AWS S3 Storage](#aws-s3-storage)
   - [MinIO Storage](#minio-storage)
   - [GCP Cloud Storage](#gcp-cloud-storage)
4. [S3 Presigned URLs](#s3-presigned-urls)
5. [Metadata Storage](#metadata-storage)
   - [Local Metadata Storage](#local-metadata-storage)
   - [Elasticsearch Metadata Storage](#elasticsearch-metadata-storage)
   - [MetadataStorageManager](#metadatastoragemanager)
6. [Environment Variables](#environment-variables)
7. [Code Examples](#code-examples)
8. [Migration Guide](#migration-guide)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The Agent Framework file storage system is designed with a clear separation between:

1. **File Storage Backends**: Handle the actual storage of file content (Local, S3, MinIO, GCP)
2. **Metadata Storage**: Manages file metadata independently (Elasticsearch or local JSON files)

This separation allows for:
- Consistent metadata handling across all storage backends
- Flexible deployment options (cloud storage with local metadata, or full Elasticsearch integration)
- Resilient operation with automatic fallback mechanisms

```
┌─────────────────────────────────────────────────────────────────┐
│                     File Storage Backends                        │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│ LocalFileStorage│  S3FileStorage  │ MinIOFileStorage│GCPStorage │
└────────┬────────┴────────┬────────┴────────┬────────┴─────┬─────┘
         │                 │                 │              │
         └─────────────────┴─────────────────┴──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   MetadataStorageManager     │
                    │   (Circuit Breaker Pattern)  │
                    └──────────────┬───────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
┌─────────────────────────────┐       ┌─────────────────────────────┐
│ ElasticsearchMetadataStorage│       │   LocalMetadataStorage      │
│   (Primary - Production)    │       │   (Fallback - Development)  │
└─────────────────────────────┘       └─────────────────────────────┘
              │                                         │
              ▼                                         ▼
        Elasticsearch                          metadata/{file_id}.json
   (agent-files-metadata)
```

### Key Components

| Component | Description |
|-----------|-------------|
| `FileStorageInterface` | Abstract interface for file storage backends |
| `MetadataStorageInterface` | Abstract interface for metadata storage |
| `MetadataStorageManager` | Coordinates metadata storage with circuit breaker |
| `FileMetadata` | Data model for file metadata with serialization |
| `MetadataMigrationUtility` | Migrates from old metadata.json format |

---

## Backend Selection & Priority

When using `FileStorageFactory.create_storage_manager()`, multiple backends can be registered simultaneously. Understanding how the default backend is selected is important for production deployments.

### Registration Order

The factory registers backends in this order (if configured):

1. **Local** - Always registered as the initial default (`is_default=True`)
2. **S3** - Registered if `AWS_S3_BUCKET` is set
3. **MinIO** - Registered if `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, and `MINIO_SECRET_KEY` are all set
4. **GCP** - Registered if `GCP_STORAGE_BUCKET` is set

### Default Backend Selection

Unlike Session Storage (which has automatic priority: Elasticsearch > MongoDB > Memory), File Storage requires **explicit configuration** to change the default backend.

| Backend | Environment Variable | Effect |
|---------|---------------------|--------|
| Local | (always default) | Default if no `*_AS_DEFAULT` is set |
| S3 | `S3_AS_DEFAULT=true` | S3 becomes the default backend |
| MinIO | `MINIO_AS_DEFAULT=true` | MinIO becomes the default backend |
| GCP | `GCP_AS_DEFAULT=true` | GCP becomes the default backend |

### Important Notes

- **Bucket auto-creation**: Buckets are NOT created automatically. S3, MinIO, and GCP all require the bucket to exist before initialization. The storage will fail to initialize if the bucket doesn't exist or credentials lack access.

- **Multiple backends**: All configured backends are available even if not set as default. You can explicitly route files to specific backends using the `FileStorageManager.store_file()` method with a backend parameter.

- **Fallback behavior**: If the default backend fails, operations do NOT automatically fall back to another backend. Each backend operates independently.

- **Routing rules respect default backend**: When `S3_AS_DEFAULT=true` or `MINIO_AS_DEFAULT=true`, the routing rules for all file types (images, PDFs, videos, text) will also use that backend by default. You can still override individual types with environment variables like `IMAGE_STORAGE_BACKEND=local`.

### Example Configurations

**Development (Local only):**
```bash
LOCAL_STORAGE_PATH=./file_storage
```

**Production with S3 as default:**
```bash
LOCAL_STORAGE_PATH=./file_storage
AWS_S3_BUCKET=my-production-bucket
AWS_REGION=eu-west-1
S3_AS_DEFAULT=true
```

**Hybrid (Local default, S3 available for large files):**
```bash
LOCAL_STORAGE_PATH=./file_storage
AWS_S3_BUCKET=my-large-files-bucket
AWS_REGION=us-east-1
# S3_AS_DEFAULT not set - Local remains default
```

**Self-hosted with MinIO:**
```bash
LOCAL_STORAGE_PATH=./file_storage
MINIO_ENDPOINT=minio.internal:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=secretkey
MINIO_BUCKET=agent-files
MINIO_SECURE=false
MINIO_AS_DEFAULT=true
```

---

## Storage Backends

### Local File Storage

Local filesystem storage is ideal for development and single-server deployments.

**Directory Structure:**
```
./file_storage/
├── files/                    # Actual file content
│   ├── {file_id}_{filename}
│   └── ...
└── metadata/                 # Individual metadata JSON files
    ├── {file_id}.json
    └── ...
```

**Initialization:**
```python
from agent_framework.storage.file_storages import LocalFileStorage

storage = LocalFileStorage(base_path="./file_storage")
await storage.initialize()
```

**Configuration:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_path` | str | `"./file_storage"` | Base directory for storage |
| `metadata_storage_manager` | MetadataStorageManager | None | Optional shared manager |

---

### AWS S3 Storage

AWS S3 storage for scalable cloud deployments.

**Prerequisites:**
- Install boto3: `uv add boto3`
- Configure AWS credentials (environment variables, IAM role, or credentials file)

**Initialization:**
```python
from agent_framework.storage.file_storages import S3FileStorage

storage = S3FileStorage(
    bucket="my-agent-files",
    region="us-east-1",
    prefix="agent-files/"
)
await storage.initialize()
```

**Configuration:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | str | Required | S3 bucket name |
| `region` | str | `"us-east-1"` | AWS region |
| `prefix` | str | `"agent-files/"` | Key prefix for files |
| `metadata_storage_manager` | MetadataStorageManager | None | Optional shared manager |

**Environment Variables:**
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

---

### MinIO Storage

MinIO provides S3-compatible object storage for self-hosted deployments.

**Prerequisites:**
- Install minio: `uv add minio`
- Running MinIO server

**Initialization:**
```python
from agent_framework.storage.file_storages import MinIOFileStorage

storage = MinIOFileStorage(
    endpoint="minio.example.com:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    bucket="agent-files",
    secure=True,
    prefix="agent-files/"
)
await storage.initialize()
```

**Configuration:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `endpoint` | str | Required | MinIO server endpoint |
| `access_key` | str | Required | MinIO access key |
| `secret_key` | str | Required | MinIO secret key |
| `bucket` | str | Required | Bucket name |
| `secure` | bool | `True` | Use HTTPS |
| `prefix` | str | `"agent-files/"` | Key prefix for files |
| `metadata_storage_manager` | MetadataStorageManager | None | Optional shared manager |

**Environment Variables:**
```bash
MINIO_ENDPOINT=minio.example.com:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=agent-files
MINIO_SECURE=true
```

---

### GCP Cloud Storage

Google Cloud Storage for GCP deployments.

**Prerequisites:**
- Install google-cloud-storage: `uv add google-cloud-storage`
- Configure GCP credentials

**Initialization:**
```python
from agent_framework.storage.file_storages import GCPFileStorage

# Using explicit credentials
storage = GCPFileStorage(
    bucket="my-agent-bucket",
    project_id="my-gcp-project",
    credentials_path="/path/to/credentials.json",
    prefix="agent-files/"
)

# Or using Application Default Credentials
storage = GCPFileStorage(bucket="my-agent-bucket")

await storage.initialize()
```

**Configuration:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket` | str | Required | GCS bucket name |
| `project_id` | str | None | GCP project ID (uses default if not set) |
| `credentials_path` | str | None | Path to service account JSON |
| `prefix` | str | `"agent-files/"` | Key prefix for files |
| `metadata_storage_manager` | MetadataStorageManager | None | Optional shared manager |

**Environment Variables:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GCP_PROJECT_ID=my-gcp-project
GCP_BUCKET=my-agent-bucket
```

**Authentication Methods:**
1. Service account JSON file (via `credentials_path` or `GOOGLE_APPLICATION_CREDENTIALS`)
2. Application Default Credentials (ADC)
3. Default service account on GCP compute resources
4. gcloud CLI credentials

---

## S3 Presigned URLs

The Agent Framework supports generating presigned and public URLs for files stored on S3 and MinIO. This allows direct browser access to files without proxying through the API, which is particularly useful for displaying images in chat interfaces.

### URL Modes

The `S3_URL_MODE` environment variable controls how download URLs are generated:

| Mode | URL Format | Use Case |
|------|------------|----------|
| `api` (default) | `/files/{file_id}/download` | Proxied through API, works with any bucket configuration |
| `presigned` | `https://bucket.s3.region.amazonaws.com/key?X-Amz-...` | Temporary signed URLs, secure access without public bucket |
| `public` | `https://bucket.s3.region.amazonaws.com/key` | Permanent URLs, requires public bucket configuration |

### Configuration

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_URL_MODE` | `api` | URL generation mode: `api`, `presigned`, or `public` |
| `S3_MAX_PRESIGNED_URL_EXPIRATION` | `86400` | Maximum presigned URL expiration (seconds, 24 hours) |
| `S3_DEFAULT_PRESIGNED_URL_EXPIRATION` | `3600` | Default presigned URL expiration (seconds, 1 hour) |

**Example Configuration:**

```bash
# Use presigned URLs with 2-hour default expiration
S3_URL_MODE=presigned
S3_DEFAULT_PRESIGNED_URL_EXPIRATION=7200
S3_MAX_PRESIGNED_URL_EXPIRATION=86400
```

### Usage Examples

#### Generating Presigned URLs

```python
from agent_framework.storage.file_storages import S3FileStorage

storage = S3FileStorage(
    bucket="my-agent-files",
    region="us-east-1"
)
await storage.initialize()

# Generate presigned URL with default expiration (1 hour)
url = await storage.get_presigned_url(file_id)

# Generate presigned URL with custom expiration (30 minutes)
url = await storage.get_presigned_url(file_id, expires_in=1800)
```

#### Generating Public URLs

```python
# Generate public URL (requires public bucket)
url = await storage.get_public_url(file_id)
# Returns: https://my-agent-files.s3.us-east-1.amazonaws.com/agent-files/file-id_filename.ext
```

#### Using get_download_url (Respects URL Mode)

```python
# Returns URL based on S3_URL_MODE configuration
url = await storage.get_download_url(file_id)

# If S3_URL_MODE=api:      /files/{file_id}/download
# If S3_URL_MODE=presigned: https://bucket.s3.region.amazonaws.com/key?X-Amz-...
# If S3_URL_MODE=public:    https://bucket.s3.region.amazonaws.com/key
```

#### Storing Files with Presigned URLs

```python
from agent_framework.storage.file_storages import FileStorageManager

manager = FileStorageManager()
await manager.initialize()

# Store file and generate presigned URL in metadata
file_id = await manager.store_file(
    content=image_bytes,
    filename="chart.png",
    mime_type="image/png",
    generate_presigned_url=True  # Populates presigned_url field in metadata
)

# Access the presigned URL from metadata
metadata = await manager.get_file_metadata(file_id)
print(metadata.presigned_url)  # https://bucket.s3.region.amazonaws.com/key?X-Amz-...
print(metadata.presigned_url_expires_at)  # datetime when URL expires
```

### MinIO Presigned URLs

MinIO uses the same interface as S3:

```python
from agent_framework.storage.file_storages import MinIOFileStorage

storage = MinIOFileStorage(
    endpoint="minio.example.com:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    bucket="agent-files",
    secure=True
)
await storage.initialize()

# Generate presigned URL (uses configured MinIO endpoint)
url = await storage.get_presigned_url(file_id)
# Returns: https://minio.example.com:9000/agent-files/key?X-Amz-...

# Generate public URL
url = await storage.get_public_url(file_id)
# Returns: https://minio.example.com:9000/agent-files/key
```

### Image Display Integration

When `S3_URL_MODE=presigned` or `S3_URL_MODE=public`, image generation tools automatically return displayable URLs:

```python
# Chart generation returns S3 URL directly
from agent_framework.tools.chart_tools import save_chart_as_image

result = await save_chart_as_image(chart_config, storage_manager)
# result["url"] is a presigned S3 URL when S3_URL_MODE=presigned

# Mermaid diagram generation
from agent_framework.tools.mermaid_tools import save_mermaid_as_image

result = await save_mermaid_as_image(mermaid_code, storage_manager)
# result["url"] is a presigned S3 URL when S3_URL_MODE=presigned
```

### Security Considerations

1. **Presigned URLs are temporary**: They expire after the configured duration. Use appropriate expiration times based on your use case.

2. **Public URLs require public bucket**: Only use `S3_URL_MODE=public` if your bucket is configured for public access.

3. **Expiration limits**: The system enforces `S3_MAX_PRESIGNED_URL_EXPIRATION` to prevent excessively long-lived URLs.

4. **API mode is most secure**: `S3_URL_MODE=api` routes all downloads through your API, allowing you to enforce authentication and authorization.

### Error Handling

```python
try:
    url = await storage.get_presigned_url(file_id)
except FileNotFoundError:
    # File does not exist
    print(f"File {file_id} not found")
except NotImplementedError:
    # Backend does not support presigned URLs (e.g., LocalFileStorage)
    print("Presigned URLs not supported by this backend")
```

---

## Metadata Storage

### Local Metadata Storage

Stores metadata as individual JSON files in a `metadata/` directory.

**File Format:** `{file_id}.json`

**Example metadata file:**
```json
{
  "file_id": "abc123-def456",
  "filename": "report.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1024000,
  "created_at": "2024-12-10T10:30:00.000000",
  "updated_at": "2024-12-10T10:30:00.000000",
  "user_id": "user123",
  "session_id": "session456",
  "agent_id": "agent001",
  "is_generated": false,
  "tags": ["report", "quarterly"],
  "storage_backend": "local",
  "storage_path": "files/abc123-def456_report.pdf",
  "conversion_status": "success",
  "has_visual_content": true
}
```

---

### Elasticsearch Metadata Storage

Production-grade metadata storage with full-text search capabilities.

**Index Name:** `agent-files-metadata`

**Key Features:**
- Full-text search on filename and tags
- Efficient filtering by user_id, session_id, agent_id
- Date range queries on created_at, updated_at
- Document ID equals file_id for direct retrieval

See [ELASTICSEARCH_DATA_STRUCTURES.md](./ELASTICSEARCH_DATA_STRUCTURES.md) for complete index mapping and query examples.

---

### MetadataStorageManager

The `MetadataStorageManager` coordinates between Elasticsearch and local storage with automatic fallback.

**Features:**
- Dual backend support (Elasticsearch + Local)
- Circuit breaker integration for resilience
- Automatic fallback on ES failures
- Transparent operation for file storage backends

**Initialization:**
```python
from agent_framework.storage.file_storages import MetadataStorageManager

manager = MetadataStorageManager(
    elasticsearch_enabled=True,
    local_base_path="./file_storage"
)
await manager.initialize()
```

**Circuit Breaker States:**
| State | Behavior |
|-------|----------|
| CLOSED | Normal operation, uses Elasticsearch |
| OPEN | ES unavailable, uses local fallback |
| HALF_OPEN | Testing ES recovery |

---

## Environment Variables

### File Storage Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_STORAGE_PATH` | `./file_storage` | Base path for local file storage |
| `FILE_STORAGE_BACKEND` | `local` | Default storage backend (local, s3, minio, gcp) |

### Elasticsearch Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ELASTICSEARCH_ENABLED` | `false` | Enable Elasticsearch for metadata storage |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch cluster URL |

### AWS S3 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET` | - | S3 bucket name |
| `S3_PREFIX` | `agent-files/` | Key prefix |
| `S3_URL_MODE` | `api` | URL mode: `api`, `presigned`, or `public` |
| `S3_MAX_PRESIGNED_URL_EXPIRATION` | `86400` | Max presigned URL expiration (seconds) |
| `S3_DEFAULT_PRESIGNED_URL_EXPIRATION` | `3600` | Default presigned URL expiration (seconds) |

### MinIO Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | - | MinIO server endpoint |
| `MINIO_ACCESS_KEY` | - | MinIO access key |
| `MINIO_SECRET_KEY` | - | MinIO secret key |
| `MINIO_BUCKET` | - | Bucket name |
| `MINIO_SECURE` | `true` | Use HTTPS |

### GCP Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to service account JSON |
| `GCP_PROJECT_ID` | - | GCP project ID |
| `GCP_BUCKET` | - | GCS bucket name |

---

## Code Examples

### Basic File Operations

```python
import asyncio
from datetime import datetime
from agent_framework.storage.file_storages import (
    LocalFileStorage,
    FileMetadata
)

async def main():
    # Initialize storage
    storage = LocalFileStorage(base_path="./file_storage")
    await storage.initialize()
    
    # Create metadata for a new file
    metadata = FileMetadata(
        file_id="unique-file-id",
        filename="document.pdf",
        mime_type="application/pdf",
        size_bytes=0,  # Will be updated on store
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id="user123",
        session_id="session456",
        agent_id="agent001",
        is_generated=False,
        tags=["document", "important"]
    )
    
    # Store file
    with open("document.pdf", "rb") as f:
        content = f.read()
    
    file_id = await storage.store_file(content, "document.pdf", metadata)
    print(f"Stored file with ID: {file_id}")
    
    # Retrieve file
    content, retrieved_metadata = await storage.retrieve_file(file_id)
    print(f"Retrieved: {retrieved_metadata.filename}")
    
    # List files for user
    files = await storage.list_files(user_id="user123")
    for f in files:
        print(f"  - {f.filename} ({f.size_bytes} bytes)")
    
    # Delete file
    await storage.delete_file(file_id)
    print("File deleted")

asyncio.run(main())
```

### Using S3 with Elasticsearch Metadata

```python
import asyncio
import os
from datetime import datetime
from agent_framework.storage.file_storages import (
    S3FileStorage,
    MetadataStorageManager,
    FileMetadata
)

async def main():
    # Enable Elasticsearch
    os.environ["ELASTICSEARCH_ENABLED"] = "true"
    os.environ["ELASTICSEARCH_URL"] = "http://localhost:9200"
    
    # Create shared metadata manager
    metadata_manager = MetadataStorageManager(
        elasticsearch_enabled=True,
        local_base_path="./file_storage"
    )
    await metadata_manager.initialize()
    
    # Initialize S3 storage with shared metadata manager
    storage = S3FileStorage(
        bucket="my-agent-files",
        region="us-east-1",
        metadata_storage_manager=metadata_manager
    )
    await storage.initialize()
    
    # Store file (metadata goes to Elasticsearch)
    metadata = FileMetadata(
        file_id="s3-file-id",
        filename="report.pdf",
        mime_type="application/pdf",
        size_bytes=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id="user123",
        session_id=None,
        agent_id=None,
        is_generated=False
    )
    
    content = b"PDF content here..."
    file_id = await storage.store_file(content, "report.pdf", metadata)
    
    # Search files using Elasticsearch
    results = await metadata_manager.search_metadata("report")
    for r in results:
        print(f"Found: {r.filename}")

asyncio.run(main())
```

### FileMetadata Serialization

```python
from datetime import datetime
from agent_framework.storage.file_storages import FileMetadata

# Create metadata
metadata = FileMetadata(
    file_id="test-123",
    filename="test.txt",
    mime_type="text/plain",
    size_bytes=1024,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    user_id="user1",
    session_id="session1",
    agent_id="agent1",
    is_generated=False,
    tags=["test", "example"]
)

# Serialize to JSON
json_str = metadata.to_json()
print(json_str)

# Deserialize from JSON
restored = FileMetadata.from_json(json_str)
assert restored.file_id == metadata.file_id

# Serialize to dict
data = metadata.to_dict()

# Deserialize from dict
restored = FileMetadata.from_dict(data)
```

---

## Migration Guide

### Migrating from metadata.json to Individual Files

If you have an existing deployment using the old single `metadata.json` file format, use the `MetadataMigrationUtility` to migrate to the new individual file format.

**Migration Process:**

1. **Detect old format:**
```python
from pathlib import Path
from agent_framework.storage.file_storages import (
    MetadataMigrationUtility,
    LocalMetadataStorage
)

# Create target storage
target_storage = LocalMetadataStorage("./file_storage")
await target_storage.initialize()

# Create migration utility
utility = MetadataMigrationUtility(
    source_path=Path("./file_storage"),
    target_storage=target_storage
)

# Check if migration is needed
if await utility.detect_old_format():
    print("Old format detected - migration needed")
```

2. **Perform migration:**
```python
# Migrate (creates backup automatically)
report = await utility.migrate()

print(f"Migration complete:")
print(f"  - Total entries: {report['total_entries']}")
print(f"  - Migrated: {report['migrated_count']}")
print(f"  - Failed: {report['failed_count']}")
print(f"  - Backup: {report['backup_path']}")

if report['failed_entries']:
    print("Failed entries:")
    for entry in report['failed_entries']:
        print(f"  - {entry['file_id']}: {entry['error']}")
```

**What happens during migration:**

1. Original `metadata.json` is backed up to `metadata.json.backup`
2. Each entry is converted to an individual `{file_id}.json` file
3. Failed entries are logged but don't stop the migration
4. A detailed report is generated

**Post-migration:**

- Verify the migration was successful by checking the report
- Test file operations to ensure everything works
- Keep the backup file until you're confident the migration is complete
- The old `metadata.json` can be deleted after successful verification

---

## Troubleshooting

### Common Issues

#### 1. "Failed to initialize storage"

**Symptoms:** Storage initialization returns `False`

**Possible causes:**
- Missing permissions on storage directory
- Invalid credentials for cloud storage
- Network connectivity issues

**Solutions:**
```bash
# Check local storage permissions
ls -la ./file_storage/

# Verify AWS credentials
aws sts get-caller-identity

# Test MinIO connectivity
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc ls myminio/

# Test GCP credentials
gcloud auth application-default print-access-token
```

#### 2. "Elasticsearch metadata storage unavailable"

**Symptoms:** Metadata operations fall back to local storage

**Possible causes:**
- Elasticsearch not running
- Circuit breaker is open
- Network issues

**Solutions:**
```bash
# Check Elasticsearch status
curl -X GET "localhost:9200/_cluster/health?pretty"

# Check index exists
curl -X GET "localhost:9200/agent-files-metadata?pretty"

# Reset circuit breaker (restart application)
```

#### 3. "File not found" after migration

**Symptoms:** Files stored before migration cannot be retrieved

**Possible causes:**
- Migration incomplete
- Metadata file corrupted

**Solutions:**
```python
# Check if metadata file exists
from pathlib import Path
metadata_path = Path("./file_storage/metadata/{file_id}.json")
print(f"Exists: {metadata_path.exists()}")

# Manually check metadata content
import json
with open(metadata_path) as f:
    print(json.dumps(json.load(f), indent=2))
```

#### 4. "GCP authentication failed"

**Symptoms:** GCPFileStorage initialization fails with auth error

**Solutions:**
```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Or authenticate with gcloud
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

#### 5. "S3 bucket access denied"

**Symptoms:** S3FileStorage cannot access bucket

**Solutions:**
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket my-bucket

# Test access
aws s3 ls s3://my-bucket/

# Verify IAM permissions
aws iam get-user
```

### Logging

Enable debug logging for detailed troubleshooting:

```python
import logging

# Enable debug logging for file storage
logging.getLogger("agent_framework.storage").setLevel(logging.DEBUG)

# Enable all agent framework logging
logging.getLogger("agent_framework").setLevel(logging.DEBUG)
```

### Health Checks

```python
async def check_storage_health(storage):
    """Check if storage is healthy"""
    try:
        # Test initialization
        if not await storage.initialize():
            return {"status": "unhealthy", "error": "initialization failed"}
        
        # Test metadata storage
        manager = storage.metadata_storage
        if manager.elasticsearch_enabled:
            if manager._is_es_available():
                return {"status": "healthy", "backend": "elasticsearch"}
            else:
                return {"status": "degraded", "backend": "local_fallback"}
        
        return {"status": "healthy", "backend": "local"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## Related Documentation

- [ELASTICSEARCH_DATA_STRUCTURES.md](./ELASTICSEARCH_DATA_STRUCTURES.md) - Elasticsearch index mappings and queries
- [GETTING_STARTED.md](./GETTING_STARTED.md) - Quick start guide
- [CREATING_AGENTS.md](./CREATING_AGENTS.md) - Agent development guide
- [configuration.md](./configuration.md) - Configuration reference
