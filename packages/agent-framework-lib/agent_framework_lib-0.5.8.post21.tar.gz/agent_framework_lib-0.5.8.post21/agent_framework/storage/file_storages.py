"""
File Storage Implementations

Comprehensive file storage system with multiple backend implementations:
- Abstract interface for extensible storage backends
- Local filesystem storage
- AWS S3 storage
- MinIO storage

v 0.1.9 - Consolidated module
"""

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import aiofiles


logger = logging.getLogger(__name__)


# ===== S3 URL CONFIGURATION =====


class S3URLMode(Enum):
    """URL generation mode for S3 file storage.

    Determines how download URLs are generated for files stored in S3/MinIO:
    - API: Returns relative API URLs (/files/{file_id}/download) - proxied through API
    - PRESIGNED: Returns presigned S3 URLs with temporary access
    - PUBLIC: Returns public S3 URLs (requires public bucket configuration)
    """

    API = "api"
    PRESIGNED = "presigned"
    PUBLIC = "public"


@dataclass
class S3URLConfig:
    """Configuration for S3 presigned URL generation.

    Attributes:
        url_mode: How to generate download URLs (API, PRESIGNED, or PUBLIC)
        max_expiration: Maximum allowed expiration time in seconds (default: 86400 = 24 hours)
        default_expiration: Default expiration time in seconds (default: 3600 = 1 hour)
        min_image_expiration: Minimum expiration for image files (default: 3600 = 1 hour)
        api_base_url: Base URL for API mode URLs (e.g., https://agent.example.com)
    """

    url_mode: S3URLMode = S3URLMode.API
    max_expiration: int = 86400  # 24 hours
    default_expiration: int = 3600  # 1 hour
    min_image_expiration: int = 3600  # 1 hour minimum for images
    api_base_url: str = ""  # Base URL for API mode (empty = relative URLs)

    @classmethod
    def from_env(cls) -> "S3URLConfig":
        """Load S3URLConfig from environment variables.

        Environment variables:
            S3_URL_MODE: URL generation mode (api, presigned, public). Default: api
            S3_MAX_PRESIGNED_URL_EXPIRATION: Maximum expiration in seconds. Default: 86400
            S3_DEFAULT_PRESIGNED_URL_EXPIRATION: Default expiration in seconds. Default: 3600
            API_BASE_URL: Base URL for API mode URLs (e.g., https://agent.example.com)

        Returns:
            S3URLConfig instance with values from environment or defaults
        """
        mode_str = os.getenv("S3_URL_MODE", "api").lower()

        # Parse URL mode with fallback to API for invalid values
        try:
            url_mode = S3URLMode(mode_str)
        except ValueError:
            logger.warning(
                f"Invalid S3_URL_MODE value '{mode_str}', falling back to 'api'. "
                f"Valid values are: {[m.value for m in S3URLMode]}"
            )
            url_mode = S3URLMode.API

        # Parse max expiration with fallback
        try:
            max_expiration = int(os.getenv("S3_MAX_PRESIGNED_URL_EXPIRATION", "86400"))
            if max_expiration <= 0:
                logger.warning(
                    f"Invalid S3_MAX_PRESIGNED_URL_EXPIRATION value '{max_expiration}', "
                    "using default 86400"
                )
                max_expiration = 86400
        except ValueError:
            logger.warning("Invalid S3_MAX_PRESIGNED_URL_EXPIRATION value, using default 86400")
            max_expiration = 86400

        # Parse default expiration with fallback
        try:
            default_expiration = int(os.getenv("S3_DEFAULT_PRESIGNED_URL_EXPIRATION", "3600"))
            if default_expiration <= 0:
                logger.warning(
                    f"Invalid S3_DEFAULT_PRESIGNED_URL_EXPIRATION value '{default_expiration}', "
                    "using default 3600"
                )
                default_expiration = 3600
        except ValueError:
            logger.warning("Invalid S3_DEFAULT_PRESIGNED_URL_EXPIRATION value, using default 3600")
            default_expiration = 3600

        # Get API base URL (strip trailing slash if present)
        api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")

        return cls(
            url_mode=url_mode,
            max_expiration=max_expiration,
            default_expiration=default_expiration,
            api_base_url=api_base_url,
        )


# ===== ENHANCED ERROR HANDLING INTEGRATION =====

# Import comprehensive error handling system
from agent_framework.monitoring.error_handling import (
    ErrorHandler,
    ErrorSeverity,
    FileProcessingErrorType,
    StorageError,
    ValidationError,
)


# ===== FILE METADATA MODEL =====


@dataclass
class FileMetadata:
    """Enhanced file metadata with multimodal processing, AI generation tracking, and dual file storage"""

    # Core file identification and basic metadata
    file_id: str
    filename: str
    mime_type: str | None
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    user_id: str
    session_id: str | None
    agent_id: str | None
    is_generated: bool  # True if file was generated by agent
    tags: list[str] = field(default_factory=list)
    custom_metadata: dict[str, Any] = field(default_factory=dict)
    storage_backend: str = ""  # Which storage system contains this file
    storage_path: str = ""  # Backend-specific path/key

    # Enhanced markdown conversion fields for dual file storage
    markdown_content: str | None = None  # Converted markdown content (for quick access)
    markdown_file_id: str | None = None  # ID of stored markdown file version
    conversion_status: str = "not_attempted"  # success/failed/not_supported/not_attempted
    conversion_timestamp: datetime | None = None  # When conversion was attempted
    conversion_error: str | None = None  # Error message if conversion failed

    # Multimodal processing fields
    has_visual_content: bool = False  # True if file contains visual content (images, etc.)
    image_analysis_result: dict[str, Any] | None = None  # Results from image analysis
    multimodal_processing_status: str = (
        "not_attempted"  # success/failed/not_supported/not_attempted
    )

    # Enhanced processing status tracking
    processing_errors: list[str] = field(default_factory=list)  # List of processing errors
    processing_warnings: list[str] = field(default_factory=list)  # List of processing warnings
    total_processing_time_ms: float | None = None  # Total time spent processing file

    # AI generation tracking fields
    generation_model: str | None = None  # Model used to generate content (if is_generated=True)
    generation_prompt: str | None = None  # Prompt used for generation
    generation_parameters: dict[str, Any] | None = None  # Parameters used for generation

    # Download URL field
    download_url: str | None = None  # Auto-populated URL for file download endpoint

    # Presigned URL fields for direct S3/MinIO access
    presigned_url: str | None = None  # Presigned URL for direct file access
    presigned_url_expires_at: datetime | None = None  # Expiration time of presigned URL

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize FileMetadata to a dictionary with ISO 8601 datetime conversion.

        All datetime fields are converted to ISO 8601 format strings.
        All fields including optional ones with None values are included.

        Returns:
            Dict[str, Any]: Dictionary representation of the metadata
        """

        def serialize_datetime(dt: datetime | None) -> str | None:
            """Convert datetime to ISO 8601 string or None"""
            return dt.isoformat() if dt is not None else None

        return {
            # Core fields
            "file_id": self.file_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "created_at": serialize_datetime(self.created_at),
            "updated_at": serialize_datetime(self.updated_at),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "is_generated": self.is_generated,
            "tags": self.tags.copy() if self.tags else [],
            "custom_metadata": self.custom_metadata.copy() if self.custom_metadata else {},
            "storage_backend": self.storage_backend,
            "storage_path": self.storage_path,
            # Markdown conversion fields
            "markdown_content": self.markdown_content,
            "markdown_file_id": self.markdown_file_id,
            "conversion_status": self.conversion_status,
            "conversion_timestamp": serialize_datetime(self.conversion_timestamp),
            "conversion_error": self.conversion_error,
            # Multimodal fields
            "has_visual_content": self.has_visual_content,
            "image_analysis_result": (
                self.image_analysis_result.copy() if self.image_analysis_result else None
            ),
            "multimodal_processing_status": self.multimodal_processing_status,
            # Processing status fields
            "processing_errors": self.processing_errors.copy() if self.processing_errors else [],
            "processing_warnings": (
                self.processing_warnings.copy() if self.processing_warnings else []
            ),
            "total_processing_time_ms": self.total_processing_time_ms,
            # AI generation fields
            "generation_model": self.generation_model,
            "generation_prompt": self.generation_prompt,
            "generation_parameters": (
                self.generation_parameters.copy() if self.generation_parameters else None
            ),
            # Download URL field
            "download_url": self.download_url,
            # Presigned URL fields
            "presigned_url": self.presigned_url,
            "presigned_url_expires_at": serialize_datetime(self.presigned_url_expires_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadata":
        """
        Deserialize FileMetadata from a dictionary with datetime parsing.

        ISO 8601 format strings are parsed back to datetime objects.
        Missing optional fields are given default values for backward compatibility.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            FileMetadata: Deserialized metadata object

        Raises:
            ValueError: If required fields are missing or invalid
        """

        def parse_datetime(value: str | None) -> datetime | None:
            """Parse ISO 8601 string to datetime or return None"""
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            try:
                # Handle ISO 8601 format with optional timezone
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        # Validate required fields
        required_fields = ["file_id", "filename", "size_bytes", "user_id"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        # Parse datetime fields
        created_at = parse_datetime(data.get("created_at"))
        updated_at = parse_datetime(data.get("updated_at"))
        conversion_timestamp = parse_datetime(data.get("conversion_timestamp"))
        presigned_url_expires_at = parse_datetime(data.get("presigned_url_expires_at"))

        # Use current time as default for required datetime fields
        now = datetime.now()
        if created_at is None:
            created_at = now
        if updated_at is None:
            updated_at = now

        return cls(
            # Core fields
            file_id=data["file_id"],
            filename=data["filename"],
            mime_type=data.get("mime_type"),
            size_bytes=data["size_bytes"],
            created_at=created_at,
            updated_at=updated_at,
            user_id=data["user_id"],
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id"),
            is_generated=data.get("is_generated", False),
            tags=data.get("tags", []),
            custom_metadata=data.get("custom_metadata", {}),
            storage_backend=data.get("storage_backend", ""),
            storage_path=data.get("storage_path", ""),
            # Markdown conversion fields
            markdown_content=data.get("markdown_content"),
            markdown_file_id=data.get("markdown_file_id"),
            conversion_status=data.get("conversion_status", "not_attempted"),
            conversion_timestamp=conversion_timestamp,
            conversion_error=data.get("conversion_error"),
            # Multimodal fields
            has_visual_content=data.get("has_visual_content", False),
            image_analysis_result=data.get("image_analysis_result"),
            multimodal_processing_status=data.get("multimodal_processing_status", "not_attempted"),
            # Processing status fields
            processing_errors=data.get("processing_errors", []),
            processing_warnings=data.get("processing_warnings", []),
            total_processing_time_ms=data.get("total_processing_time_ms"),
            # AI generation fields
            generation_model=data.get("generation_model"),
            generation_prompt=data.get("generation_prompt"),
            generation_parameters=data.get("generation_parameters"),
            # Download URL field
            download_url=data.get("download_url"),
            # Presigned URL fields
            presigned_url=data.get("presigned_url"),
            presigned_url_expires_at=presigned_url_expires_at,
        )

    def to_json(self) -> str:
        """
        Serialize FileMetadata to a JSON string.

        Convenience method that converts to dict and then to JSON.

        Returns:
            str: JSON string representation of the metadata
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "FileMetadata":
        """
        Deserialize FileMetadata from a JSON string.

        Convenience method that parses JSON and then creates FileMetadata.

        Args:
            json_str: JSON string containing metadata

        Returns:
            FileMetadata: Deserialized metadata object

        Raises:
            json.JSONDecodeError: If JSON is invalid
            ValueError: If required fields are missing
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


# ===== METADATA STORAGE INTERFACE =====


class MetadataStorageInterface(ABC):
    """
    Abstract interface for file metadata storage backends.

    This interface defines the contract for storing and retrieving file metadata
    independently of the actual file content storage. Implementations can use
    different backends such as local filesystem (individual JSON files) or
    Elasticsearch for production environments.

    All methods are async to support non-blocking I/O operations.
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the metadata storage backend.

        This method should be called before any other operations. It should
        create necessary directories, indices, or connections as needed.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    async def store_metadata(self, metadata: FileMetadata) -> bool:
        """
        Store file metadata.

        Creates a new metadata entry for a file. The file_id in the metadata
        is used as the unique identifier.

        Args:
            metadata: FileMetadata object containing all file metadata

        Returns:
            bool: True if storage was successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_metadata(self, file_id: str) -> FileMetadata | None:
        """
        Retrieve file metadata by ID.

        Args:
            file_id: Unique identifier of the file

        Returns:
            FileMetadata if found, None if not found
        """
        pass

    @abstractmethod
    async def update_metadata(self, file_id: str, updates: dict[str, Any]) -> bool:
        """
        Update file metadata.

        Performs a partial update of the metadata, only modifying the fields
        specified in the updates dictionary. The updated_at field is
        automatically set to the current time.

        Args:
            file_id: Unique identifier of the file
            updates: Dictionary of field names and their new values

        Returns:
            bool: True if update was successful, False if file not found or error
        """
        pass

    @abstractmethod
    async def delete_metadata(self, file_id: str) -> bool:
        """
        Delete file metadata.

        Removes the metadata entry for the specified file.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if deletion was successful, False if file not found or error
        """
        pass

    @abstractmethod
    async def list_metadata(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
        storage_backend: str | None = None,
    ) -> list[FileMetadata]:
        """
        List file metadata with filtering.

        Returns metadata entries matching the specified filter criteria.
        All filters are optional except user_id which is required.

        Args:
            user_id: Required filter by user ID
            session_id: Optional filter by session ID
            agent_id: Optional filter by agent ID
            is_generated: Optional filter by whether file was AI-generated
            storage_backend: Optional filter by storage backend (local, s3, minio, gcp)

        Returns:
            List of FileMetadata objects matching the filters, sorted by created_at descending
        """
        pass

    @abstractmethod
    async def search_metadata(self, query: str) -> list[FileMetadata]:
        """
        Full-text search across metadata.

        Searches across searchable fields like filename and tags.

        Args:
            query: Search query string

        Returns:
            List of FileMetadata objects matching the search query
        """
        pass


# ===== LOCAL METADATA STORAGE IMPLEMENTATION =====


class LocalMetadataStorage(MetadataStorageInterface):
    """
    Local filesystem metadata storage using individual JSON files.

    This implementation stores each file's metadata as a separate JSON file
    in a `metadata/` subdirectory within the storage base path. This approach
    improves scalability and avoids file locking issues with concurrent operations.

    File naming convention: {file_id}.json

    Attributes:
        base_path: Base directory for file storage
        metadata_dir: Directory containing individual metadata JSON files
    """

    def __init__(self, base_path: str = "./file_storage"):
        """
        Initialize LocalMetadataStorage.

        Args:
            base_path: Base directory for file storage. The metadata directory
                      will be created as a subdirectory named 'metadata/'.
        """
        self.base_path = Path(base_path)
        self.metadata_dir = self.base_path / "metadata"
        self._metadata_lock: Any | None = None

    async def initialize(self) -> bool:
        """
        Initialize the metadata storage backend.

        Creates the metadata directory if it doesn't exist and initializes
        the async lock for concurrent write protection.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            import asyncio

            self._metadata_lock = asyncio.Lock()

            # Create base path and metadata directory
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Initialized LocalMetadataStorage at {self.metadata_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LocalMetadataStorage: {e}")
            return False

    async def store_metadata(self, metadata: FileMetadata) -> bool:
        """
        Store file metadata as an individual JSON file.

        Creates a JSON file named {file_id}.json containing the serialized
        metadata. Uses atomic write pattern for data integrity.

        Args:
            metadata: FileMetadata object containing all file metadata

        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            if self._metadata_lock is None:
                import asyncio

                self._metadata_lock = asyncio.Lock()

            async with self._metadata_lock:
                metadata_file = self.metadata_dir / f"{metadata.file_id}.json"

                # Serialize metadata to JSON
                json_content = metadata.to_json()

                # Write to temporary file first (atomic write pattern)
                temp_file = metadata_file.with_suffix(".json.tmp")
                try:
                    async with aiofiles.open(temp_file, "w", encoding="utf-8") as f:
                        await f.write(json_content)

                    # Atomic rename
                    temp_file.replace(metadata_file)

                    logger.debug(f"Stored metadata for file {metadata.file_id}")
                    return True
                finally:
                    # Clean up temp file if it still exists
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass

        except Exception as e:
            logger.error(f"Failed to store metadata for file {metadata.file_id}: {e}")
            return False

    async def get_metadata(self, file_id: str) -> FileMetadata | None:
        """
        Retrieve file metadata by ID.

        Reads the JSON file named {file_id}.json and deserializes it
        to a FileMetadata object.

        Args:
            file_id: Unique identifier of the file

        Returns:
            FileMetadata if found, None if not found
        """
        try:
            metadata_file = self.metadata_dir / f"{file_id}.json"

            if not metadata_file.exists():
                logger.debug(f"Metadata file not found for file {file_id}")
                return None

            async with aiofiles.open(metadata_file, encoding="utf-8") as f:
                json_content = await f.read()

            metadata = FileMetadata.from_json(json_content)
            logger.debug(f"Retrieved metadata for file {file_id}")
            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata file for {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve metadata for file {file_id}: {e}")
            return None

    async def update_metadata(self, file_id: str, updates: dict[str, Any]) -> bool:
        """
        Update file metadata.

        Performs a partial update of the metadata, only modifying the fields
        specified in the updates dictionary. The updated_at field is
        automatically set to the current time.

        Args:
            file_id: Unique identifier of the file
            updates: Dictionary of field names and their new values

        Returns:
            bool: True if update was successful, False if file not found or error
        """
        try:
            # Get existing metadata
            metadata = await self.get_metadata(file_id)
            if metadata is None:
                logger.warning(f"Cannot update metadata: file {file_id} not found")
                return False

            # Apply updates to allowed fields
            protected_fields = {"file_id", "created_at"}
            for key, value in updates.items():
                if key in protected_fields:
                    logger.warning(f"Skipping protected field: {key}")
                    continue
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
                else:
                    logger.warning(f"Unknown field in update: {key}")

            # Update the updated_at timestamp
            metadata.updated_at = datetime.now()

            # Store the updated metadata
            return await self.store_metadata(metadata)

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id}: {e}")
            return False

    async def delete_metadata(self, file_id: str) -> bool:
        """
        Delete file metadata.

        Removes the JSON file for the specified file.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if deletion was successful, False if file not found or error
        """
        try:
            metadata_file = self.metadata_dir / f"{file_id}.json"

            if not metadata_file.exists():
                logger.debug(f"Metadata file not found for deletion: {file_id}")
                return False

            metadata_file.unlink()
            logger.debug(f"Deleted metadata for file {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete metadata for file {file_id}: {e}")
            return False

    async def list_metadata(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
        storage_backend: str | None = None,
    ) -> list[FileMetadata]:
        """
        List file metadata with filtering.

        Reads all metadata files from the metadata directory and filters
        them based on the provided criteria.

        Args:
            user_id: Required filter by user ID
            session_id: Optional filter by session ID
            agent_id: Optional filter by agent ID
            is_generated: Optional filter by whether file was AI-generated
            storage_backend: Optional filter by storage backend

        Returns:
            List of FileMetadata objects matching the filters, sorted by created_at descending
        """
        try:
            results: list[FileMetadata] = []

            # Ensure metadata directory exists
            if not self.metadata_dir.exists():
                logger.debug("Metadata directory does not exist, returning empty list")
                return results

            # Read all metadata files
            for metadata_file in self.metadata_dir.glob("*.json"):
                # Skip temporary files
                if metadata_file.suffix == ".tmp":
                    continue

                try:
                    async with aiofiles.open(metadata_file, encoding="utf-8") as f:
                        json_content = await f.read()

                    metadata = FileMetadata.from_json(json_content)

                    # Apply filters
                    if metadata.user_id != user_id:
                        continue

                    if session_id is not None and metadata.session_id != session_id:
                        continue

                    if agent_id is not None and metadata.agent_id != agent_id:
                        continue

                    if is_generated is not None and metadata.is_generated != is_generated:
                        continue

                    if storage_backend is not None and metadata.storage_backend != storage_backend:
                        continue

                    results.append(metadata)

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid metadata file {metadata_file}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {e}")
                    continue

            # Sort by created_at descending
            results.sort(key=lambda x: x.created_at, reverse=True)

            logger.debug(f"Listed {len(results)} metadata entries for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to list metadata: {e}")
            return []

    async def search_metadata(self, query: str) -> list[FileMetadata]:
        """
        Full-text search across metadata.

        Searches across filename and tags fields for matches.
        The search is case-insensitive.

        Args:
            query: Search query string

        Returns:
            List of FileMetadata objects matching the search query
        """
        try:
            results: list[FileMetadata] = []
            query_lower = query.lower()

            # Ensure metadata directory exists
            if not self.metadata_dir.exists():
                logger.debug("Metadata directory does not exist, returning empty list")
                return results

            # Read all metadata files and search
            for metadata_file in self.metadata_dir.glob("*.json"):
                # Skip temporary files
                if metadata_file.suffix == ".tmp":
                    continue

                try:
                    async with aiofiles.open(metadata_file, encoding="utf-8") as f:
                        json_content = await f.read()

                    metadata = FileMetadata.from_json(json_content)

                    # Search in filename
                    if query_lower in metadata.filename.lower():
                        results.append(metadata)
                        continue

                    # Search in tags
                    for tag in metadata.tags:
                        if query_lower in tag.lower():
                            results.append(metadata)
                            break

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid metadata file {metadata_file}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {e}")
                    continue

            # Sort by created_at descending
            results.sort(key=lambda x: x.created_at, reverse=True)

            logger.debug(f"Search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to search metadata: {e}")
            return []


# ===== ELASTICSEARCH METADATA STORAGE IMPLEMENTATION =====


class ElasticsearchMetadataStorage(MetadataStorageInterface):
    """
    Elasticsearch metadata storage for production environments.

    This implementation stores file metadata as documents in an Elasticsearch
    index, enabling full-text search and efficient querying capabilities.
    The file_id is used as the document ID for direct retrieval.

    Index name: agent-files-metadata (configurable via ELASTICSEARCH_FILES_INDEX)

    Attributes:
        client: AsyncElasticsearch client instance
        index_name: Name of the Elasticsearch index

    Environment Variables:
        ELASTICSEARCH_FILES_INDEX: Index name for file metadata (default: agent-files-metadata)
    """

    DEFAULT_INDEX_NAME = "agent-files-metadata"

    # Index mapping for file metadata
    INDEX_MAPPING = {
        "mappings": {
            "properties": {
                "file_id": {"type": "keyword"},
                "filename": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "mime_type": {"type": "keyword"},
                "size_bytes": {"type": "long"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "user_id": {"type": "keyword"},
                "session_id": {"type": "keyword"},
                "agent_id": {"type": "keyword"},
                "is_generated": {"type": "boolean"},
                "tags": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "custom_metadata": {"type": "object", "enabled": False},
                "storage_backend": {"type": "keyword"},
                "storage_path": {"type": "keyword"},
                "markdown_content": {"type": "text", "index": False},
                "markdown_file_id": {"type": "keyword"},
                "conversion_status": {"type": "keyword"},
                "conversion_timestamp": {"type": "date"},
                "conversion_error": {"type": "text", "index": False},
                "has_visual_content": {"type": "boolean"},
                "image_analysis_result": {"type": "object", "enabled": False},
                "multimodal_processing_status": {"type": "keyword"},
                "processing_errors": {"type": "text", "index": False},
                "processing_warnings": {"type": "text", "index": False},
                "total_processing_time_ms": {"type": "float"},
                "generation_model": {"type": "keyword"},
                "generation_prompt": {"type": "text", "index": False},
                "generation_parameters": {"type": "object", "enabled": False},
            }
        }
    }

    def __init__(self, elasticsearch_client: Any | None = None, index_name: str | None = None):
        """
        Initialize ElasticsearchMetadataStorage.

        Args:
            elasticsearch_client: Optional AsyncElasticsearch client instance.
                                 If not provided, will use the shared client.
            index_name: Optional index name. If not provided, uses ELASTICSEARCH_FILES_INDEX
                       environment variable or defaults to 'agent-files-metadata'.
        """
        self.client = elasticsearch_client
        self.index_name = index_name or os.getenv(
            "ELASTICSEARCH_FILES_INDEX", self.DEFAULT_INDEX_NAME
        )
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the Elasticsearch connection and create index with mappings.

        Creates the agent-files-metadata index if it doesn't exist, with
        appropriate field mappings for efficient querying and full-text search.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Get shared Elasticsearch client if not provided
            if self.client is None:
                from agent_framework.session.session_storage import get_shared_elasticsearch_client

                self.client = await get_shared_elasticsearch_client()

            if self.client is None:
                logger.error("Failed to get Elasticsearch client")
                return False

            # Create index with mapping if it doesn't exist
            if not await self.client.indices.exists(index=self.index_name):
                await self.client.indices.create(index=self.index_name, body=self.INDEX_MAPPING)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
            else:
                logger.debug(f"Elasticsearch index already exists: {self.index_name}")

            self._initialized = True
            logger.info(f"Initialized ElasticsearchMetadataStorage with index: {self.index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ElasticsearchMetadataStorage: {e}")
            return False

    async def store_metadata(self, metadata: FileMetadata) -> bool:
        """
        Store file metadata in Elasticsearch.

        Uses the file_id as the document ID for idempotent updates and
        direct retrieval.

        Args:
            metadata: FileMetadata object containing all file metadata

        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return False

            # Convert metadata to dictionary for Elasticsearch
            doc = metadata.to_dict()

            # Use file_id as document ID for direct retrieval
            await self.client.index(
                index=self.index_name,
                id=metadata.file_id,
                document=doc,
                refresh="wait_for",  # Make data immediately available for search
            )

            logger.debug(f"Stored metadata for file {metadata.file_id} in Elasticsearch")
            return True

        except Exception as e:
            logger.error(
                f"Failed to store metadata for file {metadata.file_id} in Elasticsearch: {e}"
            )
            return False

    async def get_metadata(self, file_id: str) -> FileMetadata | None:
        """
        Retrieve file metadata by ID from Elasticsearch.

        Uses direct document retrieval by ID for efficient access.

        Args:
            file_id: Unique identifier of the file (used as document ID)

        Returns:
            FileMetadata if found, None if not found
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return None

            response = await self.client.get(index=self.index_name, id=file_id)

            if response and response.get("found"):
                source = response["_source"]
                metadata = FileMetadata.from_dict(source)
                logger.debug(f"Retrieved metadata for file {file_id} from Elasticsearch")
                return metadata

            return None

        except Exception as e:
            # Check if it's a "not found" error
            error_str = str(e).lower()
            if "not_found" in error_str or "404" in error_str:
                logger.debug(f"Metadata not found for file {file_id}")
                return None

            logger.error(f"Failed to retrieve metadata for file {file_id} from Elasticsearch: {e}")
            return None

    async def update_metadata(self, file_id: str, updates: dict[str, Any]) -> bool:
        """
        Update file metadata in Elasticsearch.

        Performs a partial document update, only modifying the fields
        specified in the updates dictionary. The updated_at field is
        automatically set to the current time.

        Args:
            file_id: Unique identifier of the file
            updates: Dictionary of field names and their new values

        Returns:
            bool: True if update was successful, False if file not found or error
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return False

            # Filter out protected fields
            protected_fields = {"file_id", "created_at"}
            filtered_updates = {k: v for k, v in updates.items() if k not in protected_fields}

            if not filtered_updates:
                logger.warning("No valid fields to update")
                return False

            # Add updated_at timestamp
            filtered_updates["updated_at"] = datetime.now().isoformat()

            # Perform partial update
            await self.client.update(
                index=self.index_name, id=file_id, doc=filtered_updates, refresh="wait_for"
            )

            logger.debug(f"Updated metadata for file {file_id} in Elasticsearch")
            return True

        except Exception as e:
            # Check if it's a "not found" error
            error_str = str(e).lower()
            if "not_found" in error_str or "404" in error_str:
                logger.warning(f"Cannot update metadata: file {file_id} not found")
                return False

            logger.error(f"Failed to update metadata for file {file_id} in Elasticsearch: {e}")
            return False

    async def delete_metadata(self, file_id: str) -> bool:
        """
        Delete file metadata from Elasticsearch.

        Removes the document with the specified file_id.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if deletion was successful, False if file not found or error
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return False

            response = await self.client.delete(
                index=self.index_name, id=file_id, refresh="wait_for"
            )

            # Check if document was actually deleted
            if response.get("result") == "deleted":
                logger.debug(f"Deleted metadata for file {file_id} from Elasticsearch")
                return True

            logger.debug(f"Metadata not found for deletion: {file_id}")
            return False

        except Exception as e:
            # Check if it's a "not found" error
            error_str = str(e).lower()
            if "not_found" in error_str or "404" in error_str:
                logger.debug(f"Metadata not found for deletion: {file_id}")
                return False

            logger.error(f"Failed to delete metadata for file {file_id} from Elasticsearch: {e}")
            return False

    async def list_metadata(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
        storage_backend: str | None = None,
    ) -> list[FileMetadata]:
        """
        List file metadata with filtering using Elasticsearch bool query.

        Builds a bool query with must clauses for each filter criterion.
        Results are sorted by created_at descending.

        Args:
            user_id: Required filter by user ID
            session_id: Optional filter by session ID
            agent_id: Optional filter by agent ID
            is_generated: Optional filter by whether file was AI-generated
            storage_backend: Optional filter by storage backend

        Returns:
            List of FileMetadata objects matching the filters
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return []

            # Build bool query with must clauses
            must_clauses = [{"term": {"user_id": user_id}}]

            if session_id is not None:
                must_clauses.append({"term": {"session_id": session_id}})

            if agent_id is not None:
                must_clauses.append({"term": {"agent_id": agent_id}})

            if is_generated is not None:
                must_clauses.append({"term": {"is_generated": is_generated}})

            if storage_backend is not None:
                must_clauses.append({"term": {"storage_backend": storage_backend}})

            # Execute search
            response = await self.client.search(
                index=self.index_name,
                body={
                    "query": {"bool": {"must": must_clauses}},
                    "sort": [{"created_at": {"order": "desc"}}],
                    "size": 10000,  # Reasonable limit
                },
            )

            # Parse results
            results = []
            for hit in response["hits"]["hits"]:
                try:
                    metadata = FileMetadata.from_dict(hit["_source"])
                    results.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to parse metadata from hit: {e}")
                    continue

            logger.debug(f"Listed {len(results)} metadata entries for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to list metadata from Elasticsearch: {e}")
            return []

    async def search_metadata(self, query: str) -> list[FileMetadata]:
        """
        Full-text search across metadata using Elasticsearch.

        Searches across filename and tags fields using multi_match query.
        Results are sorted by relevance score.

        Args:
            query: Search query string

        Returns:
            List of FileMetadata objects matching the search query
        """
        try:
            if not self._initialized:
                logger.error("ElasticsearchMetadataStorage not initialized")
                return []

            # Build multi_match query for full-text search
            response = await self.client.search(
                index=self.index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["filename", "tags"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    "size": 1000,  # Reasonable limit for search results
                },
            )

            # Parse results
            results = []
            for hit in response["hits"]["hits"]:
                try:
                    metadata = FileMetadata.from_dict(hit["_source"])
                    results.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to parse metadata from search hit: {e}")
                    continue

            logger.debug(f"Search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to search metadata in Elasticsearch: {e}")
            return []


# ===== METADATA STORAGE MANAGER =====


class MetadataStorageManager:
    """
    Manages metadata storage with automatic fallback between backends.

    This manager coordinates between Elasticsearch (primary) and local filesystem
    (fallback) metadata storage backends. It integrates with the circuit breaker
    pattern to automatically fall back to local storage when Elasticsearch is
    unavailable.

    Key Features:
    - Dual backend support (Elasticsearch + Local)
    - Circuit breaker integration for resilience
    - Automatic fallback on ES failures
    - Logging for state changes and operations

    Attributes:
        elasticsearch_enabled: Whether Elasticsearch is configured as primary
        primary_storage: Primary metadata storage backend (ES when enabled)
        fallback_storage: Fallback local metadata storage
        circuit_breaker: Circuit breaker for ES operations

    Example:
        ```python
        from agent_framework.storage.file_storages import MetadataStorageManager

        # Create manager with ES enabled
        manager = MetadataStorageManager(
            elasticsearch_enabled=True,
            local_base_path="./file_storage"
        )

        # Initialize
        await manager.initialize()

        # Store metadata (automatically uses ES or falls back to local)
        await manager.store_metadata(metadata)
        ```
    """

    def __init__(
        self,
        elasticsearch_enabled: bool = False,
        elasticsearch_client: Any | None = None,
        local_base_path: str = "./file_storage",
        circuit_breaker: Any | None = None,
    ):
        """
        Initialize the MetadataStorageManager.

        Args:
            elasticsearch_enabled: Whether to use Elasticsearch as primary storage.
                                  Falls back to local storage when ES is unavailable.
            elasticsearch_client: Optional AsyncElasticsearch client instance.
                                 If not provided and ES is enabled, will use shared client.
            local_base_path: Base path for local metadata storage.
            circuit_breaker: Optional ElasticsearchCircuitBreaker instance.
                            If not provided and ES is enabled, will use global instance.
        """
        self.elasticsearch_enabled = elasticsearch_enabled
        self._elasticsearch_client = elasticsearch_client
        self._local_base_path = local_base_path

        # Storage backends
        self.primary_storage: MetadataStorageInterface | None = None
        self.fallback_storage: LocalMetadataStorage | None = None

        # Circuit breaker for ES operations
        self._circuit_breaker = circuit_breaker

        # Initialization state
        self._initialized = False

        logger.debug(
            f"MetadataStorageManager created: "
            f"elasticsearch_enabled={elasticsearch_enabled}, "
            f"local_base_path={local_base_path}"
        )

    @property
    def circuit_breaker(self) -> Any | None:
        """
        Get the circuit breaker instance.

        Lazily initializes the global circuit breaker if ES is enabled
        and no circuit breaker was provided.

        Returns:
            ElasticsearchCircuitBreaker instance or None if ES is disabled
        """
        if self._circuit_breaker is None and self.elasticsearch_enabled:
            from agent_framework.monitoring.elasticsearch_circuit_breaker import (
                get_elasticsearch_circuit_breaker,
            )

            self._circuit_breaker = get_elasticsearch_circuit_breaker()
        return self._circuit_breaker

    async def initialize(self) -> bool:
        """
        Initialize the metadata storage backends.

        Creates and initializes both the primary (ES if enabled) and fallback
        (local) storage backends. The fallback storage is always initialized
        to ensure availability.

        Returns:
            bool: True if at least the fallback storage initialized successfully
        """
        try:
            # Always initialize local fallback storage
            self.fallback_storage = LocalMetadataStorage(base_path=self._local_base_path)
            fallback_initialized = await self.fallback_storage.initialize()

            if not fallback_initialized:
                logger.error("Failed to initialize fallback local metadata storage")
                return False

            logger.info("Initialized fallback local metadata storage")

            # Initialize Elasticsearch storage if enabled
            if self.elasticsearch_enabled:
                try:
                    self.primary_storage = ElasticsearchMetadataStorage(
                        elasticsearch_client=self._elasticsearch_client
                    )
                    primary_initialized = await self.primary_storage.initialize()

                    if primary_initialized:
                        logger.info("Initialized Elasticsearch metadata storage as primary")
                    else:
                        logger.warning(
                            "Failed to initialize Elasticsearch metadata storage, "
                            "will use local fallback"
                        )
                        self.primary_storage = None
                        # Record failure in circuit breaker
                        if self.circuit_breaker:
                            self.circuit_breaker.record_failure()

                except Exception as e:
                    logger.warning(
                        f"Exception initializing Elasticsearch metadata storage: {e}, "
                        "will use local fallback"
                    )
                    self.primary_storage = None
                    # Record failure in circuit breaker
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure()

            self._initialized = True
            logger.info(
                f"MetadataStorageManager initialized: "
                f"primary={'elasticsearch' if self.primary_storage else 'local'}, "
                f"fallback=local"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MetadataStorageManager: {e}")
            return False

    def _is_es_available(self) -> bool:
        """
        Check if Elasticsearch is available for operations.

        Checks both that ES is enabled and that the circuit breaker
        allows operations.

        Returns:
            bool: True if ES operations should be attempted
        """
        if not self.elasticsearch_enabled or self.primary_storage is None:
            return False

        if self.circuit_breaker:
            return self.circuit_breaker.is_available()

        return True

    def _get_active_storage(self) -> MetadataStorageInterface:
        """
        Get the currently active storage backend.

        Returns ES storage if available, otherwise returns local fallback.

        Returns:
            MetadataStorageInterface: The active storage backend
        """
        if self._is_es_available():
            return self.primary_storage  # type: ignore
        return self.fallback_storage  # type: ignore

    async def store_metadata(self, metadata: FileMetadata) -> bool:
        """
        Store file metadata with automatic fallback.

        Attempts to store in Elasticsearch if available, falls back to
        local storage on failure.

        Args:
            metadata: FileMetadata object containing all file metadata

        Returns:
            bool: True if storage was successful in either backend
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return False

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.store_metadata(metadata)  # type: ignore
                if result:
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    logger.debug(f"Stored metadata for {metadata.file_id} in Elasticsearch")
                    return True
                else:
                    # Store returned False, record as failure
                    if self.circuit_breaker:
                        self.circuit_breaker.record_failure()
                    logger.warning(
                        f"Elasticsearch store returned False for {metadata.file_id}, "
                        "falling back to local"
                    )
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(
                    f"Elasticsearch store failed for {metadata.file_id}: {e}, "
                    "falling back to local"
                )

        # Fall back to local storage
        try:
            result = await self.fallback_storage.store_metadata(metadata)  # type: ignore
            if result:
                logger.debug(f"Stored metadata for {metadata.file_id} in local fallback")
            return result
        except Exception as e:
            logger.error(f"Failed to store metadata in local fallback: {e}")
            return False

    async def get_metadata(self, file_id: str) -> FileMetadata | None:
        """
        Retrieve file metadata with automatic fallback.

        Attempts to retrieve from Elasticsearch if available, falls back to
        local storage on failure or if not found.

        Args:
            file_id: Unique identifier of the file

        Returns:
            FileMetadata if found, None if not found in any backend
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return None

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.get_metadata(file_id)  # type: ignore
                if result is not None:
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    return result
                # Not found in ES, try local fallback
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(
                    f"Elasticsearch get failed for {file_id}: {e}, " "falling back to local"
                )

        # Fall back to local storage
        try:
            return await self.fallback_storage.get_metadata(file_id)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to get metadata from local fallback: {e}")
            return None

    async def update_metadata(self, file_id: str, updates: dict[str, Any]) -> bool:
        """
        Update file metadata with automatic fallback.

        Attempts to update in Elasticsearch if available, falls back to
        local storage on failure.

        Args:
            file_id: Unique identifier of the file
            updates: Dictionary of field names and their new values

        Returns:
            bool: True if update was successful in either backend
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return False

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.update_metadata(file_id, updates)  # type: ignore
                if result:
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    logger.debug(f"Updated metadata for {file_id} in Elasticsearch")
                    return True
                else:
                    # Update returned False (not found or error)
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()  # ES worked, just not found
                    # Try local fallback
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(
                    f"Elasticsearch update failed for {file_id}: {e}, " "falling back to local"
                )

        # Fall back to local storage
        try:
            result = await self.fallback_storage.update_metadata(file_id, updates)  # type: ignore
            if result:
                logger.debug(f"Updated metadata for {file_id} in local fallback")
            return result
        except Exception as e:
            logger.error(f"Failed to update metadata in local fallback: {e}")
            return False

    async def delete_metadata(self, file_id: str) -> bool:
        """
        Delete file metadata with automatic fallback.

        Attempts to delete from Elasticsearch if available, falls back to
        local storage on failure.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if deletion was successful in either backend
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return False

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.delete_metadata(file_id)  # type: ignore
                if result:
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()
                    logger.debug(f"Deleted metadata for {file_id} from Elasticsearch")
                    return True
                else:
                    # Delete returned False (not found)
                    if self.circuit_breaker:
                        self.circuit_breaker.record_success()  # ES worked, just not found
                    # Try local fallback
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(
                    f"Elasticsearch delete failed for {file_id}: {e}, " "falling back to local"
                )

        # Fall back to local storage
        try:
            result = await self.fallback_storage.delete_metadata(file_id)  # type: ignore
            if result:
                logger.debug(f"Deleted metadata for {file_id} from local fallback")
            return result
        except Exception as e:
            logger.error(f"Failed to delete metadata from local fallback: {e}")
            return False

    async def list_metadata(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
        storage_backend: str | None = None,
    ) -> list[FileMetadata]:
        """
        List file metadata with filtering and automatic fallback.

        Attempts to list from Elasticsearch if available, falls back to
        local storage on failure.

        Args:
            user_id: Required filter by user ID
            session_id: Optional filter by session ID
            agent_id: Optional filter by agent ID
            is_generated: Optional filter by whether file was AI-generated
            storage_backend: Optional filter by storage backend

        Returns:
            List of FileMetadata objects matching the filters
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return []

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.list_metadata(  # type: ignore
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    is_generated=is_generated,
                    storage_backend=storage_backend,
                )
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                return result
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(f"Elasticsearch list failed: {e}, falling back to local")

        # Fall back to local storage
        try:
            return await self.fallback_storage.list_metadata(  # type: ignore
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                is_generated=is_generated,
                storage_backend=storage_backend,
            )
        except Exception as e:
            logger.error(f"Failed to list metadata from local fallback: {e}")
            return []

    async def search_metadata(self, query: str) -> list[FileMetadata]:
        """
        Full-text search across metadata with automatic fallback.

        Attempts to search in Elasticsearch if available, falls back to
        local storage on failure.

        Args:
            query: Search query string

        Returns:
            List of FileMetadata objects matching the search query
        """
        if not self._initialized:
            logger.error("MetadataStorageManager not initialized")
            return []

        # Try Elasticsearch if available
        if self._is_es_available():
            try:
                result = await self.primary_storage.search_metadata(query)  # type: ignore
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                return result
            except Exception as e:
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                logger.warning(f"Elasticsearch search failed: {e}, falling back to local")

        # Fall back to local storage
        try:
            return await self.fallback_storage.search_metadata(query)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to search metadata in local fallback: {e}")
            return []

    def get_active_backend_name(self) -> str:
        """
        Get the name of the currently active backend.

        Returns:
            str: 'elasticsearch' or 'local'
        """
        if self._is_es_available():
            return "elasticsearch"
        return "local"

    def get_circuit_breaker_state(self) -> str | None:
        """
        Get the current circuit breaker state.

        Returns:
            str: Circuit breaker state ('closed', 'open', 'half_open') or None if disabled
        """
        if self.circuit_breaker:
            return self.circuit_breaker.get_state().value
        return None

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status information about the manager.

        Returns:
            Dict containing status information including:
            - initialized: Whether the manager is initialized
            - elasticsearch_enabled: Whether ES is configured
            - active_backend: Currently active backend name
            - circuit_breaker_state: Current circuit breaker state
            - circuit_breaker_metrics: Detailed circuit breaker metrics
        """
        status = {
            "initialized": self._initialized,
            "elasticsearch_enabled": self.elasticsearch_enabled,
            "active_backend": self.get_active_backend_name() if self._initialized else None,
            "primary_storage_available": self.primary_storage is not None,
            "fallback_storage_available": self.fallback_storage is not None,
        }

        if self.circuit_breaker:
            status["circuit_breaker_state"] = self.circuit_breaker.get_state().value
            status["circuit_breaker_metrics"] = self.circuit_breaker.get_metrics()
        else:
            status["circuit_breaker_state"] = None
            status["circuit_breaker_metrics"] = None

        return status


# ===== METADATA MIGRATION UTILITY =====


@dataclass
class MigrationReport:
    """Report generated after metadata migration.

    Contains statistics and details about the migration process including
    success/failure counts and any errors encountered.

    Attributes:
        total_entries: Total number of entries found in old format
        successful_migrations: Number of entries successfully migrated
        failed_migrations: Number of entries that failed to migrate
        skipped_entries: Number of entries skipped (already migrated or invalid)
        errors: List of error messages for failed migrations
        warnings: List of warning messages
        backup_path: Path to the backup file (if created)
        migration_time_ms: Total time taken for migration in milliseconds
        started_at: Timestamp when migration started
        completed_at: Timestamp when migration completed
    """

    total_entries: int = 0
    successful_migrations: int = 0
    failed_migrations: int = 0
    skipped_entries: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    backup_path: str | None = None
    migration_time_ms: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "total_entries": self.total_entries,
            "successful_migrations": self.successful_migrations,
            "failed_migrations": self.failed_migrations,
            "skipped_entries": self.skipped_entries,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "backup_path": self.backup_path,
            "migration_time_ms": self.migration_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success_rate": (
                (self.successful_migrations / self.total_entries * 100)
                if self.total_entries > 0
                else 0.0
            ),
        }

    def __str__(self) -> str:
        """Generate human-readable summary of the migration report."""
        lines = [
            "=== Metadata Migration Report ===",
            f"Total entries found: {self.total_entries}",
            f"Successfully migrated: {self.successful_migrations}",
            f"Failed migrations: {self.failed_migrations}",
            f"Skipped entries: {self.skipped_entries}",
        ]

        if self.total_entries > 0:
            success_rate = self.successful_migrations / self.total_entries * 100
            lines.append(f"Success rate: {success_rate:.1f}%")

        if self.backup_path:
            lines.append(f"Backup created at: {self.backup_path}")

        if self.migration_time_ms:
            lines.append(f"Migration time: {self.migration_time_ms:.2f}ms")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                lines.append(f"  - {error}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5 warnings
                lines.append(f"  - {warning}")
            if len(self.warnings) > 5:
                lines.append(f"  ... and {len(self.warnings) - 5} more warnings")

        return "\n".join(lines)


class MetadataMigrationUtility:
    """
    Utility for migrating from old metadata.json format to new individual files.

    This utility handles the migration of file metadata from the legacy single
    metadata.json file format to the new individual JSON files per stored file.
    It provides:

    - Detection of old format metadata.json files
    - Migration of entries to individual {file_id}.json files
    - Automatic backup creation (metadata.json.backup)
    - Error handling for partial failures
    - Detailed migration report generation

    The migration process is designed to be safe and non-destructive:
    - Original metadata.json is backed up before migration
    - Failed entries are logged but don't stop the migration
    - A detailed report is generated after migration

    Example:
        ```python
        from agent_framework.storage.file_storages import (
            MetadataMigrationUtility,
            LocalMetadataStorage
        )

        # Create migration utility
        utility = MetadataMigrationUtility(
            source_path=Path("./file_storage"),
            target_storage=LocalMetadataStorage("./file_storage")
        )

        # Check if migration is needed
        if await utility.detect_old_format():
            # Perform migration
            report = await utility.migrate()
            print(report)
        ```

    Attributes:
        source_path: Path to the directory containing the old metadata.json
        target_storage: MetadataStorageInterface to migrate entries to
    """

    OLD_METADATA_FILENAME = "metadata.json"
    BACKUP_SUFFIX = ".backup"

    def __init__(
        self,
        source_path: Path | str,
        target_storage: MetadataStorageInterface,
    ):
        """
        Initialize the MetadataMigrationUtility.

        Args:
            source_path: Path to the directory containing the old metadata.json file.
                        This is typically the base storage path (e.g., ./file_storage).
            target_storage: MetadataStorageInterface instance to migrate entries to.
                           This should be an initialized storage backend.
        """
        self.source_path = Path(source_path) if isinstance(source_path, str) else source_path
        self.target_storage = target_storage
        self._metadata_json_path = self.source_path / self.OLD_METADATA_FILENAME

    @property
    def metadata_json_path(self) -> Path:
        """Get the path to the old metadata.json file."""
        return self._metadata_json_path

    @property
    def backup_path(self) -> Path:
        """Get the path for the backup file."""
        return self._metadata_json_path.with_suffix(
            self._metadata_json_path.suffix + self.BACKUP_SUFFIX
        )

    async def detect_old_format(self) -> bool:
        """
        Check if an old-format metadata.json file exists.

        Detects the presence of a legacy metadata.json file that needs
        to be migrated to the new individual file format.

        Returns:
            bool: True if old format metadata.json exists, False otherwise
        """
        try:
            exists = self._metadata_json_path.exists()
            if exists:
                logger.info(f"Detected old format metadata.json at {self._metadata_json_path}")
            else:
                logger.debug(f"No old format metadata.json found at {self._metadata_json_path}")
            return exists
        except Exception as e:
            logger.error(f"Error checking for old format metadata.json: {e}")
            return False

    async def _create_backup(self) -> str | None:
        """
        Create a backup of the old metadata.json file.

        Creates a copy of metadata.json as metadata.json.backup before
        migration to ensure data safety.

        Returns:
            str: Path to the backup file if successful, None if failed
        """
        try:
            if not self._metadata_json_path.exists():
                logger.warning("Cannot create backup: metadata.json does not exist")
                return None

            # Read original content
            async with aiofiles.open(self._metadata_json_path, encoding="utf-8") as f:
                content = await f.read()

            # Write to backup file
            async with aiofiles.open(self.backup_path, "w", encoding="utf-8") as f:
                await f.write(content)

            logger.info(f"Created backup at {self.backup_path}")
            return str(self.backup_path)

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    async def _load_old_metadata(self) -> dict[str, Any]:
        """
        Load and parse the old metadata.json file.

        Returns:
            dict: Parsed metadata dictionary, empty dict if file doesn't exist or is invalid
        """
        try:
            if not self._metadata_json_path.exists():
                return {}

            async with aiofiles.open(self._metadata_json_path, encoding="utf-8") as f:
                content = await f.read()

            if not content.strip():
                logger.warning("metadata.json is empty")
                return {}

            data = json.loads(content)

            # Handle different possible formats
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # Convert list to dict keyed by file_id
                return {item.get("file_id", str(i)): item for i, item in enumerate(data)}
            else:
                logger.warning(f"Unexpected metadata.json format: {type(data)}")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata.json: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load metadata.json: {e}")
            return {}

    async def _migrate_entry(
        self, file_id: str, entry_data: dict[str, Any], report: MigrationReport
    ) -> bool:
        """
        Migrate a single metadata entry to the new format.

        Args:
            file_id: The file ID for this entry
            entry_data: The metadata dictionary for this entry
            report: MigrationReport to update with results

        Returns:
            bool: True if migration was successful, False otherwise
        """
        try:
            # Ensure file_id is in the entry data
            if "file_id" not in entry_data:
                entry_data["file_id"] = file_id

            # Validate required fields
            required_fields = ["file_id", "filename", "size_bytes", "user_id"]
            missing_fields = [f for f in required_fields if f not in entry_data]

            if missing_fields:
                error_msg = f"Entry {file_id}: Missing required fields: {missing_fields}"
                logger.warning(error_msg)
                report.warnings.append(error_msg)
                # Try to provide defaults for missing fields
                if "filename" not in entry_data:
                    entry_data["filename"] = f"unknown_{file_id}"
                if "size_bytes" not in entry_data:
                    entry_data["size_bytes"] = 0
                if "user_id" not in entry_data:
                    entry_data["user_id"] = "unknown"

            # Create FileMetadata from entry data
            try:
                metadata = FileMetadata.from_dict(entry_data)
            except ValueError as e:
                error_msg = f"Entry {file_id}: Failed to parse metadata: {e}"
                logger.error(error_msg)
                report.errors.append(error_msg)
                return False

            # Check if entry already exists in target storage
            existing = await self.target_storage.get_metadata(file_id)
            if existing is not None:
                warning_msg = f"Entry {file_id}: Already exists in target storage, skipping"
                logger.debug(warning_msg)
                report.warnings.append(warning_msg)
                report.skipped_entries += 1
                return True  # Not a failure, just skipped

            # Store in target storage
            success = await self.target_storage.store_metadata(metadata)

            if success:
                logger.debug(f"Successfully migrated entry {file_id}")
                return True
            else:
                error_msg = f"Entry {file_id}: Failed to store in target storage"
                logger.error(error_msg)
                report.errors.append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Entry {file_id}: Unexpected error during migration: {e}"
            logger.error(error_msg)
            report.errors.append(error_msg)
            return False

    async def migrate(self, create_backup: bool = True) -> MigrationReport:
        """
        Migrate metadata from old format to new individual files.

        Performs the full migration process:
        1. Creates a backup of metadata.json (if create_backup=True)
        2. Loads and parses the old metadata.json
        3. Migrates each entry to an individual JSON file
        4. Generates a detailed migration report

        The migration continues even if individual entries fail, logging
        errors for later review.

        Args:
            create_backup: Whether to create a backup before migration (default: True)

        Returns:
            MigrationReport: Detailed report of the migration process
        """
        import time

        report = MigrationReport()
        report.started_at = datetime.now()
        start_time = time.time()

        try:
            # Check if old format exists
            if not await self.detect_old_format():
                report.warnings.append("No old format metadata.json found, nothing to migrate")
                report.completed_at = datetime.now()
                report.migration_time_ms = (time.time() - start_time) * 1000
                logger.info("No migration needed: metadata.json not found")
                return report

            # Create backup if requested
            if create_backup:
                backup_path = await self._create_backup()
                if backup_path:
                    report.backup_path = backup_path
                else:
                    report.warnings.append("Failed to create backup, continuing with migration")

            # Load old metadata
            old_metadata = await self._load_old_metadata()
            report.total_entries = len(old_metadata)

            if report.total_entries == 0:
                report.warnings.append("metadata.json is empty or invalid, nothing to migrate")
                report.completed_at = datetime.now()
                report.migration_time_ms = (time.time() - start_time) * 1000
                logger.info("No migration needed: metadata.json is empty")
                return report

            logger.info(f"Starting migration of {report.total_entries} entries")

            # Migrate each entry
            for file_id, entry_data in old_metadata.items():
                success = await self._migrate_entry(file_id, entry_data, report)
                if success and file_id not in [
                    w.split(":")[0].replace("Entry ", "")
                    for w in report.warnings
                    if "Already exists" in w
                ]:
                    report.successful_migrations += 1
                elif not success:
                    report.failed_migrations += 1

            # Finalize report
            report.completed_at = datetime.now()
            report.migration_time_ms = (time.time() - start_time) * 1000

            # Log summary
            logger.info(
                f"Migration completed: {report.successful_migrations}/{report.total_entries} "
                f"successful, {report.failed_migrations} failed, {report.skipped_entries} skipped"
            )

            return report

        except Exception as e:
            error_msg = f"Migration failed with unexpected error: {e}"
            logger.error(error_msg)
            report.errors.append(error_msg)
            report.completed_at = datetime.now()
            report.migration_time_ms = (time.time() - start_time) * 1000
            return report

    async def get_migration_status(self) -> dict[str, Any]:
        """
        Get the current migration status without performing migration.

        Provides information about whether migration is needed and
        the state of the old and new metadata storage.

        Returns:
            dict: Status information including:
                - needs_migration: Whether old format exists
                - old_format_path: Path to old metadata.json
                - old_format_exists: Whether metadata.json exists
                - backup_exists: Whether a backup already exists
                - entry_count: Number of entries in old format (if exists)
        """
        try:
            old_exists = await self.detect_old_format()
            backup_exists = self.backup_path.exists()

            status = {
                "needs_migration": old_exists,
                "old_format_path": str(self._metadata_json_path),
                "old_format_exists": old_exists,
                "backup_exists": backup_exists,
                "backup_path": str(self.backup_path) if backup_exists else None,
                "entry_count": 0,
            }

            if old_exists:
                old_metadata = await self._load_old_metadata()
                status["entry_count"] = len(old_metadata)

            return status

        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {
                "needs_migration": False,
                "error": str(e),
            }


# ===== ABSTRACT STORAGE INTERFACE =====


class FileStorageInterface(ABC):
    """Abstract interface for file storage backends"""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the storage backend"""
        pass

    @abstractmethod
    async def store_file(self, content: bytes, filename: str, metadata: FileMetadata) -> str:
        """Store file and return file_id"""
        pass

    @abstractmethod
    async def retrieve_file(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """Retrieve file content and metadata"""
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        pass

    @abstractmethod
    async def list_files(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
    ) -> list[FileMetadata]:
        """List files with filtering"""
        pass

    @abstractmethod
    async def update_metadata(self, file_id: str, metadata: dict[str, Any]) -> bool:
        """Update file metadata"""
        pass

    @abstractmethod
    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """Get file metadata without content"""
        pass

    @abstractmethod
    async def convert_file_to_markdown(self, file_id: str) -> str | None:
        """Convert file to markdown and return the content"""
        pass

    @abstractmethod
    async def analyze_image(self, file_id: str) -> dict[str, Any] | None:
        """Analyze image content using multimodal capabilities"""
        pass

    @abstractmethod
    async def get_processing_status(self, file_id: str) -> dict[str, Any]:
        """Get comprehensive processing status for a file"""
        pass

    @abstractmethod
    async def store_markdown_version(
        self, original_file_id: str, markdown_content: str
    ) -> str | None:
        """Store markdown version of a file as a separate file"""
        pass

    @abstractmethod
    async def retrieve_markdown_version(
        self, original_file_id: str
    ) -> tuple[str, "FileMetadata"] | None:
        """Retrieve markdown version of a file"""
        pass

    async def get_presigned_url(self, file_id: str, expires_in: int | None = None) -> str:
        """
        Generate a presigned URL for direct file access.

        This method generates a temporary signed URL that allows direct access to the file
        without requiring authentication through the API. The URL expires after the
        specified duration.

        Args:
            file_id: The unique identifier of the file
            expires_in: URL expiration time in seconds. If not specified, uses the
                       default expiration from S3URLConfig (typically 3600 seconds).

        Returns:
            str: Presigned URL string for direct file access

        Raises:
            FileNotFoundError: If file_id does not exist in storage
            NotImplementedError: If the storage backend does not support presigned URLs
        """
        raise NotImplementedError("This storage backend does not support presigned URLs")

    async def get_public_url(self, file_id: str) -> str:
        """
        Generate a public URL for direct file access.

        This method generates a permanent public URL for accessing the file directly.
        This requires the storage bucket to be configured for public access.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: Public URL string for direct file access

        Raises:
            FileNotFoundError: If file_id does not exist in storage
            NotImplementedError: If the storage backend does not support public URLs
        """
        raise NotImplementedError("This storage backend does not support public URLs")


# ===== LOCAL FILE STORAGE IMPLEMENTATION =====


class LocalFileStorage(FileStorageInterface):
    """Local filesystem storage implementation with delegated metadata management"""

    def __init__(
        self,
        base_path: str = "./file_storage",
        metadata_storage_manager: Optional["MetadataStorageManager"] = None,
    ):
        """
        Initialize LocalFileStorage.

        Args:
            base_path: Base directory for file storage
            metadata_storage_manager: Optional MetadataStorageManager for metadata operations.
                                     If not provided, one will be created during initialization.
        """
        self.base_path = Path(base_path)
        self.files_dir = self.base_path / "files"
        self._metadata_storage_manager = metadata_storage_manager
        self._owns_metadata_manager = metadata_storage_manager is None

    async def initialize(self) -> bool:
        """Create storage directories and initialize metadata storage"""
        try:
            # Create directories
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.files_dir.mkdir(exist_ok=True)

            # Initialize metadata storage manager if not provided
            if self._metadata_storage_manager is None:
                # Check if Elasticsearch is enabled
                elasticsearch_enabled = (
                    os.environ.get("ELASTICSEARCH_ENABLED", "").lower() == "true"
                )
                self._metadata_storage_manager = MetadataStorageManager(
                    elasticsearch_enabled=elasticsearch_enabled, local_base_path=str(self.base_path)
                )
                self._owns_metadata_manager = True

            # Initialize the metadata storage manager
            if not await self._metadata_storage_manager.initialize():
                logger.error("Failed to initialize metadata storage manager")
                return False

            logger.info(f"Initialized LocalFileStorage at {self.base_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LocalFileStorage: {e}")
            return False

    @property
    def metadata_storage(self) -> "MetadataStorageManager":
        """Get the metadata storage manager"""
        if self._metadata_storage_manager is None:
            raise RuntimeError("LocalFileStorage not initialized - call initialize() first")
        return self._metadata_storage_manager

    async def store_file(self, content: bytes, filename: str, metadata: FileMetadata) -> str:
        """Store file locally and update metadata with comprehensive error handling"""
        error_handler = ErrorHandler()

        try:
            # Validate inputs
            if not content:
                raise ValidationError(
                    error_type=FileProcessingErrorType.FILE_EMPTY,
                    severity=ErrorSeverity.ERROR,
                    message="Cannot store empty file",
                    user_message=f"File {filename} is empty and cannot be stored",
                )

            if len(content) > 100 * 1024 * 1024:  # 100MB limit
                raise ValidationError(
                    error_type=FileProcessingErrorType.FILE_TOO_LARGE,
                    severity=ErrorSeverity.ERROR,
                    message=f"File {filename} exceeds size limit",
                    user_message=f"File {filename} is too large (max 100MB allowed)",
                )

            # Create storage filename with format: id_original_name.ext
            original_name = Path(filename)
            storage_filename = f"{metadata.file_id}_{original_name.stem}{original_name.suffix}"
            file_path = self.files_dir / storage_filename

            # Check disk space before writing
            try:
                available_space = (
                    os.statvfs(self.base_path).f_bavail * os.statvfs(self.base_path).f_frsize
                )
                if len(content) > available_space:
                    raise StorageError(
                        error_type=FileProcessingErrorType.DISK_SPACE_FULL,
                        severity=ErrorSeverity.ERROR,
                        message="Insufficient disk space",
                        user_message="Not enough storage space available",
                        backend_name="local",
                    )
            except AttributeError:
                # statvfs not available on Windows, skip check
                pass

            # Write file content with error handling
            try:
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
            except PermissionError as e:
                raise StorageError(
                    error_type=FileProcessingErrorType.STORAGE_PERMISSION_DENIED,
                    severity=ErrorSeverity.ERROR,
                    message=f"Permission denied writing to {file_path}",
                    user_message="Storage permission denied - contact administrator",
                    backend_name="local",
                    technical_details=str(e),
                )
            except OSError as e:
                if "No space left" in str(e):
                    raise StorageError(
                        error_type=FileProcessingErrorType.DISK_SPACE_FULL,
                        severity=ErrorSeverity.ERROR,
                        message="Disk space full",
                        user_message="Storage space is full",
                        backend_name="local",
                        technical_details=str(e),
                    )
                else:
                    raise StorageError(
                        error_type=FileProcessingErrorType.STORAGE_WRITE_FAILED,
                        severity=ErrorSeverity.ERROR,
                        message=f"Failed to write file: {str(e)}",
                        user_message="File storage failed due to system error",
                        backend_name="local",
                        technical_details=str(e),
                    )

            # Update metadata with actual size and storage path
            metadata.storage_path = str(file_path)
            metadata.size_bytes = len(content)
            metadata.storage_backend = "local"
            metadata.updated_at = datetime.now()

            # Store metadata using MetadataStorageManager
            try:
                await self.metadata_storage.store_metadata(metadata)
            except Exception as e:
                # File was stored but metadata update failed - this is a warning
                logger.warning(
                    f"File stored but metadata update failed for {metadata.file_id}: {e}"
                )
                # Don't raise here as the file was successfully stored

            logger.debug(f"✅ Stored file {metadata.file_id} ({filename}) locally")
            return metadata.file_id

        except (StorageError, ValidationError):
            # Re-raise our structured errors
            raise
        except Exception as e:
            # Handle unexpected errors
            structured_error = error_handler.handle_exception(
                exception=e,
                operation="file_storage",
                filename=filename,
                context={
                    "file_id": metadata.file_id,
                    "backend": "local",
                    "file_size": len(content) if content else 0,
                },
            )
            logger.error(f"❌ Unexpected error storing file {filename}: {structured_error}")
            raise structured_error

    async def store_markdown_version(
        self, original_file_id: str, markdown_content: str
    ) -> str | None:
        """Store markdown version of a file as a separate file"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                logger.error(f"Original file {original_file_id} not found for markdown storage")
                return None

            # Create new file ID for markdown version
            markdown_file_id = str(uuid.uuid4())

            # Create markdown filename with format: id_original_name.md
            base_name = Path(original_metadata.filename).stem
            markdown_filename = f"{markdown_file_id}_{base_name}.md"

            # Store markdown content as bytes
            markdown_bytes = markdown_content.encode("utf-8")
            markdown_file_path = self.files_dir / markdown_filename

            async with aiofiles.open(markdown_file_path, "wb") as f:
                await f.write(markdown_bytes)

            # Create metadata for markdown file
            markdown_metadata = FileMetadata(
                file_id=markdown_file_id,
                filename=markdown_filename,
                mime_type="text/markdown",
                size_bytes=len(markdown_bytes),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=original_metadata.user_id,
                session_id=original_metadata.session_id,
                agent_id=original_metadata.agent_id,
                is_generated=True,  # Markdown version is generated
                tags=original_metadata.tags + ["markdown-conversion", "auto-generated"],
                custom_metadata={
                    **original_metadata.custom_metadata,
                    "original_file_id": original_file_id,
                    "conversion_source": original_metadata.filename,
                },
                storage_backend="local",
                storage_path=str(markdown_file_path),
                conversion_status="success",
                conversion_timestamp=datetime.now(),
            )

            # Store markdown file metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(markdown_metadata)

            # Update original file metadata to reference markdown version
            await self.metadata_storage.update_metadata(
                original_file_id,
                {
                    "markdown_file_id": markdown_file_id,
                    "markdown_content": markdown_content,
                    "conversion_status": "success",
                    "conversion_timestamp": datetime.now(),
                    "conversion_error": None,
                },
            )

            logger.info(
                f"✅ Stored markdown version of {original_metadata.filename} as separate file {markdown_file_id}"
            )
            return markdown_file_id

        except Exception as e:
            logger.error(f"Failed to store markdown version for file {original_file_id}: {e}")
            return None

    async def retrieve_markdown_version(
        self, original_file_id: str
    ) -> tuple[str, "FileMetadata"] | None:
        """Retrieve markdown version of a file"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                return None

            if not original_metadata.markdown_file_id:
                return None

            # Retrieve markdown file
            markdown_content, markdown_metadata = await self.retrieve_file(
                original_metadata.markdown_file_id
            )
            markdown_text = markdown_content.decode("utf-8")

            return markdown_text, markdown_metadata

        except Exception as e:
            logger.error(f"Failed to retrieve markdown version for file {original_file_id}: {e}")
            return None

    async def retrieve_file(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """Retrieve file content and metadata with comprehensive error handling"""
        error_handler = ErrorHandler()

        try:
            # Validate file_id
            if not file_id or not file_id.strip():
                raise ValidationError(
                    error_type=FileProcessingErrorType.FILENAME_INVALID,
                    severity=ErrorSeverity.ERROR,
                    message="Invalid file ID provided",
                    user_message="File ID is required for retrieval",
                )

            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise StorageError(
                    error_type=FileProcessingErrorType.STORAGE_READ_FAILED,
                    severity=ErrorSeverity.ERROR,
                    message=f"File {file_id} not found in metadata",
                    user_message="File not found in storage system",
                    backend_name="local",
                    context={"file_id": file_id},
                )

            file_path = Path(metadata.storage_path)

            # Check if file exists on disk
            if not file_path.exists():
                raise StorageError(
                    error_type=FileProcessingErrorType.STORAGE_READ_FAILED,
                    severity=ErrorSeverity.ERROR,
                    message=f"File {file_id} not found on disk at {file_path}",
                    user_message="File not found on storage disk - may have been deleted",
                    backend_name="local",
                    context={"file_id": file_id, "expected_path": str(file_path)},
                )

            # Read file content with error handling
            try:
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
            except PermissionError as e:
                raise StorageError(
                    error_type=FileProcessingErrorType.STORAGE_PERMISSION_DENIED,
                    severity=ErrorSeverity.ERROR,
                    message=f"Permission denied reading {file_path}",
                    user_message="Storage permission denied - contact administrator",
                    backend_name="local",
                    technical_details=str(e),
                    context={"file_id": file_id, "file_path": str(file_path)},
                )
            except OSError as e:
                if "corrupted" in str(e).lower() or "invalid" in str(e).lower():
                    raise StorageError(
                        error_type=FileProcessingErrorType.FILE_CORRUPTED,
                        severity=ErrorSeverity.ERROR,
                        message=f"File {file_id} appears to be corrupted",
                        user_message="File is corrupted and cannot be read",
                        backend_name="local",
                        technical_details=str(e),
                        context={"file_id": file_id},
                    )
                else:
                    raise StorageError(
                        error_type=FileProcessingErrorType.STORAGE_READ_FAILED,
                        severity=ErrorSeverity.ERROR,
                        message=f"Failed to read file: {str(e)}",
                        user_message="File read failed due to system error",
                        backend_name="local",
                        technical_details=str(e),
                        context={"file_id": file_id},
                    )

            # Validate content
            if content is None:
                raise StorageError(
                    error_type=FileProcessingErrorType.FILE_CORRUPTED,
                    severity=ErrorSeverity.ERROR,
                    message=f"File {file_id} returned null content",
                    user_message="File appears to be corrupted",
                    backend_name="local",
                    context={"file_id": file_id},
                )

            logger.debug(f"✅ Retrieved file {file_id} from local storage ({len(content)} bytes)")
            return content, metadata

        except (StorageError, ValidationError):
            # Re-raise our structured errors
            raise
        except Exception as e:
            # Handle unexpected errors
            structured_error = error_handler.handle_exception(
                exception=e,
                operation="file_retrieval",
                context={"file_id": file_id, "backend": "local"},
            )
            logger.error(f"❌ Unexpected error retrieving file {file_id}: {structured_error}")
            raise structured_error

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from storage and metadata"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return False

            file_path = Path(metadata.storage_path)

            # Delete file from disk
            if file_path.exists():
                file_path.unlink()

            # Delete metadata using MetadataStorageManager
            await self.metadata_storage.delete_metadata(file_id)

            logger.debug(f"Deleted file {file_id} from local storage")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def list_files(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
    ) -> list[FileMetadata]:
        """List files with filtering using MetadataStorageManager"""
        try:
            logger.info(
                f"🔍 LOCAL STORAGE - Listing files with filters: user_id={user_id}, session_id={session_id}, agent_id={agent_id}, is_generated={is_generated}"
            )

            # Delegate to MetadataStorageManager with storage_backend filter
            files = await self.metadata_storage.list_metadata(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                is_generated=is_generated,
                storage_backend="local",
            )

            logger.info(f"📁 LOCAL STORAGE - Returning {len(files)} files after filtering")
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    async def update_metadata(self, file_id: str, metadata_updates: dict[str, Any]) -> bool:
        """Update file metadata using MetadataStorageManager"""
        try:
            # Delegate to MetadataStorageManager
            result = await self.metadata_storage.update_metadata(file_id, metadata_updates)

            if result:
                logger.debug(f"Updated metadata for file {file_id}")
            else:
                logger.warning(f"Failed to update metadata for file {file_id} - file not found")

            return result

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id}: {e}")
            return False

    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists"""
        # Get metadata from MetadataStorageManager
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            return False

        file_path = Path(metadata.storage_path)
        return file_path.exists()

    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """Get file metadata without content using MetadataStorageManager"""
        logger.info(f"🔍 GET METADATA - Looking for file {file_id}")

        # Delegate to MetadataStorageManager
        metadata = await self.metadata_storage.get_metadata(file_id)

        if metadata is not None:
            logger.info(f"✅ GET METADATA - Found file {file_id}")
        else:
            logger.error(f"❌ GET METADATA - File {file_id} not found")

        return metadata

    async def convert_file_to_markdown(self, file_id: str) -> str | None:
        """Convert file to markdown and return the content"""
        try:
            # Get file content and metadata
            content, metadata = await self.retrieve_file(file_id)

            # Import here to avoid circular import
            from agent_framework.processing.markdown_converter import markdown_converter

            # Convert to markdown
            markdown_content = await markdown_converter.convert_to_markdown(
                content, metadata.filename, metadata.mime_type or ""
            )

            if markdown_content:
                # Update metadata with conversion results using MetadataStorageManager
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "markdown_content": markdown_content,
                        "conversion_status": "success",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": None,
                    },
                )

                logger.info(f"✅ Converted file {file_id} to markdown")
                return markdown_content
            else:
                # Update metadata with failure
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": "Conversion returned empty content",
                    },
                )

                logger.warning(f"❌ Failed to convert file {file_id} to markdown")
                return None

        except Exception as e:
            logger.error(f"❌ Error converting file {file_id} to markdown: {e}")

            # Update metadata with error using MetadataStorageManager
            try:
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": str(e),
                    },
                )
            except Exception:
                pass  # Ignore errors updating metadata on failure

            return None

    async def analyze_image(self, file_id: str) -> dict[str, Any] | None:
        """Analyze image content using multimodal capabilities"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                logger.warning(f"File {file_id} not found for image analysis")
                return None

            # Check if file has visual content
            if not metadata.has_visual_content and not (
                metadata.mime_type and metadata.mime_type.startswith("image/")
            ):
                logger.warning(f"File {file_id} does not contain visual content")
                return None

            # For now, return a placeholder result indicating analysis capability
            # This will be implemented in later tasks with actual multimodal processing
            analysis_result = {
                "status": "not_implemented",
                "message": "Image analysis capability will be implemented in task 4",
                "file_id": file_id,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "has_visual_content": metadata.has_visual_content,
            }

            # Update metadata with analysis attempt using MetadataStorageManager
            await self.metadata_storage.update_metadata(
                file_id, {"multimodal_processing_status": "not_implemented"}
            )

            logger.debug(f"Image analysis placeholder for file {file_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in image analysis for file {file_id}: {e}")
            return None

    async def get_processing_status(self, file_id: str) -> dict[str, Any]:
        """Get comprehensive processing status for a file using MetadataStorageManager"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return {"file_id": file_id, "exists": False, "error": "File not found"}

            # Compile comprehensive processing status
            status = {
                "file_id": file_id,
                "exists": True,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "size_bytes": metadata.size_bytes,
                "storage_backend": metadata.storage_backend,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                # Conversion status
                "conversion_status": metadata.conversion_status,
                "conversion_timestamp": (
                    metadata.conversion_timestamp.isoformat()
                    if metadata.conversion_timestamp
                    else None
                ),
                "conversion_error": metadata.conversion_error,
                "has_markdown_version": metadata.markdown_file_id is not None,
                "markdown_file_id": metadata.markdown_file_id,
                # Multimodal processing status
                "has_visual_content": metadata.has_visual_content,
                "multimodal_processing_status": metadata.multimodal_processing_status,
                "image_analysis_available": metadata.image_analysis_result is not None,
                # Processing errors and warnings
                "processing_errors": metadata.processing_errors,
                "processing_warnings": metadata.processing_warnings,
                "total_processing_time_ms": metadata.total_processing_time_ms,
                # AI generation info
                "is_generated": metadata.is_generated,
                "generation_model": metadata.generation_model,
                "generation_prompt": metadata.generation_prompt,
                "generation_parameters": metadata.generation_parameters,
                # Tags and metadata
                "tags": metadata.tags,
                "custom_metadata": metadata.custom_metadata,
            }

            logger.debug(f"Retrieved processing status for file {file_id}")
            return status

        except Exception as e:
            logger.error(f"Error getting processing status for file {file_id}: {e}")
            return {"file_id": file_id, "exists": False, "error": str(e)}


# ===== S3 FILE STORAGE IMPLEMENTATION =====

# S3 availability flag
S3_AVAILABLE = False
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    S3_AVAILABLE = True
except ImportError:
    logger.warning("S3 storage not available: boto3 not installed. Install with 'uv add boto3'")


class S3FileStorage(FileStorageInterface):
    """AWS S3 storage implementation with delegated metadata management"""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        prefix: str = "agent-files/",
        metadata_storage_manager: Optional["MetadataStorageManager"] = None,
        url_config: S3URLConfig | None = None,
    ):
        """
        Initialize S3FileStorage.

        Args:
            bucket: S3 bucket name
            region: AWS region
            prefix: Key prefix for stored files
            metadata_storage_manager: Optional MetadataStorageManager for metadata operations.
                                     If not provided, one will be created during initialization.
            url_config: Optional S3URLConfig for URL generation settings.
                       If not provided, one will be created from environment variables.
        """
        if not S3_AVAILABLE:
            raise ImportError("S3 storage requires boto3. Install with 'uv add boto3'")

        self.bucket = bucket
        self.region = region
        self.prefix = prefix
        self.s3_client = None
        self._metadata_storage_manager = metadata_storage_manager
        self._owns_metadata_manager = metadata_storage_manager is None
        self.url_config = url_config or S3URLConfig.from_env()

    async def initialize(self) -> bool:
        """Initialize S3 client and verify bucket access"""
        try:
            self.s3_client = boto3.client("s3", region_name=self.region)

            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.bucket)

            # Initialize metadata storage manager if not provided
            if self._metadata_storage_manager is None:
                # Check if Elasticsearch is enabled
                elasticsearch_enabled = (
                    os.environ.get("ELASTICSEARCH_ENABLED", "").lower() == "true"
                )
                self._metadata_storage_manager = MetadataStorageManager(
                    elasticsearch_enabled=elasticsearch_enabled,
                    local_base_path="./file_storage",  # Default local path for fallback
                )
                self._owns_metadata_manager = True

            # Initialize the metadata storage manager
            if not await self._metadata_storage_manager.initialize():
                logger.error("Failed to initialize metadata storage manager")
                return False

            logger.info(f"Initialized S3FileStorage for bucket {self.bucket}")
            return True

        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to initialize S3 storage: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 storage: {e}")
            return False

    @property
    def metadata_storage(self) -> "MetadataStorageManager":
        """Get the metadata storage manager"""
        if self._metadata_storage_manager is None:
            raise RuntimeError("S3FileStorage not initialized - call initialize() first")
        return self._metadata_storage_manager

    async def store_file(self, content: bytes, filename: str, metadata: FileMetadata) -> str:
        """Store file in S3"""
        try:
            # Create storage filename with format: id_original_name.ext
            original_name = Path(filename)
            storage_filename = f"{metadata.file_id}_{original_name.stem}{original_name.suffix}"
            key = f"{self.prefix}{storage_filename}"

            # S3 metadata can only contain ASCII characters
            # URL-encode the filename for S3 metadata, keep original in our metadata
            from urllib.parse import quote
            safe_filename = quote(filename, safe='')  # URL-encode all non-ASCII chars
            
            # Store file in S3 with metadata
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=metadata.mime_type or "application/octet-stream",
                Metadata={
                    "filename": safe_filename,  # URL-encoded for S3 compatibility
                    "mime_type": metadata.mime_type or "",
                    "user_id": metadata.user_id,
                    "session_id": metadata.session_id or "",
                    "agent_id": metadata.agent_id or "",
                    "is_generated": str(metadata.is_generated),
                    "created_at": metadata.created_at.isoformat(),
                    "file_id": metadata.file_id,
                },
            )

            # Update metadata
            metadata.storage_path = key
            metadata.size_bytes = len(content)
            metadata.storage_backend = "s3"
            metadata.updated_at = datetime.now()

            # Store metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(metadata)

            logger.debug(f"Stored file {metadata.file_id} ({filename}) in S3")
            return metadata.file_id

        except Exception as e:
            logger.error(f"Failed to store file {metadata.file_id} in S3: {e}")
            raise

    async def store_markdown_version(
        self, original_file_id: str, markdown_content: str
    ) -> str | None:
        """Store markdown version of a file as a separate file in S3"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                logger.error(f"Original file {original_file_id} not found for markdown storage")
                return None

            # Create new file ID for markdown version
            markdown_file_id = str(uuid.uuid4())

            # Create markdown filename with format: id_original_name.md
            base_name = Path(original_metadata.filename).stem
            markdown_filename = f"{markdown_file_id}_{base_name}.md"

            # Store markdown content as bytes
            markdown_bytes = markdown_content.encode("utf-8")
            markdown_key = f"{self.prefix}{markdown_filename}"

            # Store markdown file in S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=markdown_key,
                Body=markdown_bytes,
                ContentType="text/markdown",
                Metadata={
                    "filename": markdown_filename,
                    "mime_type": "text/markdown",
                    "user_id": original_metadata.user_id,
                    "session_id": original_metadata.session_id or "",
                    "agent_id": original_metadata.agent_id or "",
                    "is_generated": "True",
                    "created_at": datetime.now().isoformat(),
                    "file_id": markdown_file_id,
                    "original_file_id": original_file_id,
                },
            )

            # Create metadata for markdown file
            from datetime import datetime

            markdown_metadata = FileMetadata(
                file_id=markdown_file_id,
                filename=markdown_filename,
                mime_type="text/markdown",
                size_bytes=len(markdown_bytes),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=original_metadata.user_id,
                session_id=original_metadata.session_id,
                agent_id=original_metadata.agent_id,
                is_generated=True,  # Markdown version is generated
                tags=original_metadata.tags + ["markdown-conversion", "auto-generated"],
                custom_metadata={
                    **original_metadata.custom_metadata,
                    "original_file_id": original_file_id,
                    "conversion_source": original_metadata.filename,
                },
                storage_backend="s3",
                storage_path=markdown_key,
                conversion_status="success",
                conversion_timestamp=datetime.now(),
            )

            # Store markdown file metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(markdown_metadata)

            # Update original file metadata to reference markdown version
            await self.metadata_storage.update_metadata(
                original_file_id,
                {
                    "markdown_file_id": markdown_file_id,
                    "markdown_content": markdown_content,
                    "conversion_status": "success",
                    "conversion_timestamp": datetime.now(),
                    "conversion_error": None,
                },
            )

            logger.info(
                f"✅ Stored markdown version of {original_metadata.filename} as separate file {markdown_file_id} in S3"
            )
            return markdown_file_id

        except Exception as e:
            logger.error(f"Failed to store markdown version for file {original_file_id} in S3: {e}")
            return None

    async def retrieve_markdown_version(
        self, original_file_id: str
    ) -> tuple[str, "FileMetadata"] | None:
        """Retrieve markdown version of a file from S3"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                return None

            if not original_metadata.markdown_file_id:
                return None

            # Retrieve markdown file
            markdown_content, markdown_metadata = await self.retrieve_file(
                original_metadata.markdown_file_id
            )
            markdown_text = markdown_content.decode("utf-8")

            return markdown_text, markdown_metadata

        except Exception as e:
            logger.error(
                f"Failed to retrieve markdown version for file {original_file_id} from S3: {e}"
            )
            return None

    async def retrieve_file(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """Retrieve file content and metadata from S3"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")

            # Get file from S3
            response = self.s3_client.get_object(Bucket=self.bucket, Key=metadata.storage_path)

            content = response["Body"].read()

            logger.debug(f"Retrieved file {file_id} from S3")
            return content, metadata

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File {file_id} not found in S3")
            else:
                logger.error(f"Failed to retrieve file {file_id} from S3: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to retrieve file {file_id} from S3: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from S3 and metadata"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return False

            # Delete file from S3
            self.s3_client.delete_object(Bucket=self.bucket, Key=metadata.storage_path)

            # Delete metadata using MetadataStorageManager
            await self.metadata_storage.delete_metadata(file_id)

            logger.debug(f"Deleted file {file_id} from S3")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id} from S3: {e}")
            return False

    async def list_files(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
    ) -> list[FileMetadata]:
        """List files with filtering using MetadataStorageManager"""
        try:
            # Delegate to MetadataStorageManager with storage_backend filter
            files = await self.metadata_storage.list_metadata(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                is_generated=is_generated,
                storage_backend="s3",
            )
            return files

        except Exception as e:
            logger.error(f"Failed to list files from S3: {e}")
            return []

    async def update_metadata(self, file_id: str, metadata_updates: dict[str, Any]) -> bool:
        """Update file metadata using MetadataStorageManager"""
        try:
            # Delegate to MetadataStorageManager
            result = await self.metadata_storage.update_metadata(file_id, metadata_updates)

            if result:
                logger.debug(f"Updated metadata for file {file_id} in S3")

            return result

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id} in S3: {e}")
            return False

    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists in S3"""
        # Get metadata from MetadataStorageManager
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=metadata.storage_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"Error checking file existence in S3: {e}")
                return False

    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """Get file metadata without content using MetadataStorageManager"""
        return await self.metadata_storage.get_metadata(file_id)

    async def convert_file_to_markdown(self, file_id: str) -> str | None:
        """Convert file to markdown and return the content"""
        try:
            # Get file content and metadata
            content, metadata = await self.retrieve_file(file_id)

            # Import here to avoid circular import
            from agent_framework.processing.markdown_converter import markdown_converter

            # Convert to markdown
            markdown_content = await markdown_converter.convert_to_markdown(
                content, metadata.filename, metadata.mime_type or ""
            )

            if markdown_content:
                # Update metadata with conversion results using MetadataStorageManager
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "markdown_content": markdown_content,
                        "conversion_status": "success",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": None,
                    },
                )

                logger.info(f"✅ Converted file {file_id} to markdown")
                return markdown_content
            else:
                # Update metadata with failure
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": "Conversion returned empty content",
                    },
                )

                logger.warning(f"❌ Failed to convert file {file_id} to markdown")
                return None

        except Exception as e:
            logger.error(f"❌ Error converting file {file_id} to markdown: {e}")

            # Update metadata with error using MetadataStorageManager
            try:
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": str(e),
                    },
                )
            except Exception:
                pass  # Ignore errors updating metadata on failure

            return None

    async def analyze_image(self, file_id: str) -> dict[str, Any] | None:
        """Analyze image content using multimodal capabilities"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                logger.warning(f"File {file_id} not found for image analysis")
                return None

            # Check if file has visual content
            if not metadata.has_visual_content and not (
                metadata.mime_type and metadata.mime_type.startswith("image/")
            ):
                logger.warning(f"File {file_id} does not contain visual content")
                return None

            # For now, return a placeholder result indicating analysis capability
            # This will be implemented in later tasks with actual multimodal processing
            analysis_result = {
                "status": "not_implemented",
                "message": "Image analysis capability will be implemented in task 4",
                "file_id": file_id,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "has_visual_content": metadata.has_visual_content,
            }

            # Update metadata with analysis attempt using MetadataStorageManager
            await self.metadata_storage.update_metadata(
                file_id, {"multimodal_processing_status": "not_implemented"}
            )

            logger.debug(f"Image analysis placeholder for file {file_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in image analysis for file {file_id}: {e}")
            return None

    async def get_processing_status(self, file_id: str) -> dict[str, Any]:
        """Get comprehensive processing status for a file using MetadataStorageManager"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return {"file_id": file_id, "exists": False, "error": "File not found"}

            # Compile comprehensive processing status
            status = {
                "file_id": file_id,
                "exists": True,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "size_bytes": metadata.size_bytes,
                "storage_backend": metadata.storage_backend,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                # Conversion status
                "conversion_status": metadata.conversion_status,
                "conversion_timestamp": (
                    metadata.conversion_timestamp.isoformat()
                    if metadata.conversion_timestamp
                    else None
                ),
                "conversion_error": metadata.conversion_error,
                "has_markdown_version": metadata.markdown_file_id is not None,
                "markdown_file_id": metadata.markdown_file_id,
                # Multimodal processing status
                "has_visual_content": metadata.has_visual_content,
                "multimodal_processing_status": metadata.multimodal_processing_status,
                "image_analysis_available": metadata.image_analysis_result is not None,
                # Processing errors and warnings
                "processing_errors": metadata.processing_errors,
                "processing_warnings": metadata.processing_warnings,
                "total_processing_time_ms": metadata.total_processing_time_ms,
                # AI generation info
                "is_generated": metadata.is_generated,
                "generation_model": metadata.generation_model,
                "generation_prompt": metadata.generation_prompt,
                "generation_parameters": metadata.generation_parameters,
                # Tags and metadata
                "tags": metadata.tags,
                "custom_metadata": metadata.custom_metadata,
            }

            logger.debug(f"Retrieved processing status for file {file_id}")
            return status

        except Exception as e:
            logger.error(f"Error getting processing status for file {file_id}: {e}")
            return {"file_id": file_id, "exists": False, "error": str(e)}

    async def get_presigned_url(self, file_id: str, expires_in: int | None = None) -> str:
        """
        Generate a presigned S3 URL for direct file access.

        This method generates a temporary signed URL that allows direct access to the file
        without requiring authentication through the API. The URL expires after the
        specified duration.

        Args:
            file_id: The unique identifier of the file
            expires_in: URL expiration time in seconds. If not specified, uses the
                       default expiration from S3URLConfig (typically 3600 seconds).

        Returns:
            str: Presigned URL string for direct file access

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        logger.info(f"🔍 get_presigned_url called for file_id={file_id}")
        
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            logger.error(f"🔍 get_presigned_url: File {file_id} not found in metadata")
            raise FileNotFoundError(f"File {file_id} not found")

        logger.info(f"🔍 get_presigned_url: Found metadata, storage_path={metadata.storage_path}")

        expiration = expires_in or self.url_config.default_expiration
        expiration = min(expiration, self.url_config.max_expiration)

        if expiration > self.url_config.max_expiration:
            logger.debug(
                f"Requested expiration {expires_in}s exceeds max {self.url_config.max_expiration}s, "
                f"using max value"
            )

        logger.info(f"🔍 get_presigned_url: Calling s3_client.generate_presigned_url with bucket={self.bucket}, key={metadata.storage_path}, expiration={expiration}")
        
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": metadata.storage_path},
                ExpiresIn=expiration,
            )
            logger.info(f"🔍 get_presigned_url: SUCCESS! Generated URL: {url[:100]}...")
            return url
        except Exception as e:
            logger.error(f"🔍 get_presigned_url: FAILED to generate presigned URL: {type(e).__name__}: {e}")
            raise

    async def get_public_url(self, file_id: str) -> str:
        """
        Generate a public S3 URL for direct file access.

        This method generates a permanent public URL for accessing the file directly.
        This requires the S3 bucket to be configured for public access.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: Public URL string in format https://{bucket}.s3.{region}.amazonaws.com/{key}

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File {file_id} not found")

        url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{metadata.storage_path}"

        logger.debug(f"Generated public URL for file {file_id}")
        return url

    async def get_download_url(self, file_id: str) -> str:
        """
        Get download URL for forcing file download.

        Returns the appropriate URL format based on the S3_URL_MODE configuration:
        - API mode: Returns {API_BASE_URL}/files/{file_id}/download (forces download)
        - PRESIGNED mode: Returns a presigned S3 URL with temporary access
        - PUBLIC mode: Returns a public S3 URL (requires public bucket)

        For displaying images inline (in chat), use get_view_url() instead.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: Download URL in the format determined by S3_URL_MODE

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        logger.info(f"🔍 S3FileStorage.get_download_url called for {file_id}, url_mode={self.url_config.url_mode}")
        if self.url_config.url_mode == S3URLMode.PRESIGNED:
            return await self.get_presigned_url(file_id)
        elif self.url_config.url_mode == S3URLMode.PUBLIC:
            return await self.get_public_url(file_id)
        else:
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")
            base_url = self.url_config.api_base_url
            return f"{base_url}/files/{file_id}/download"

    async def get_view_url(self, file_id: str) -> str:
        """
        Get URL for viewing file inline in browser (for images in chat, etc.)

        Returns the appropriate URL format based on the S3_URL_MODE configuration:
        - API mode: Returns {API_BASE_URL}/files/{file_id}/view (displays inline)
        - PRESIGNED mode: Returns a presigned S3 URL (browsers display inline by default)
        - PUBLIC mode: Returns a public S3 URL (browsers display inline by default)

        Use this for displaying generated images (charts, diagrams) in chat.
        For forcing file download, use get_download_url() instead.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: View URL for inline display

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        logger.info(f"👁️ S3FileStorage.get_view_url called for {file_id}, url_mode={self.url_config.url_mode}")
        if self.url_config.url_mode == S3URLMode.PRESIGNED:
            return await self.get_presigned_url(file_id)
        elif self.url_config.url_mode == S3URLMode.PUBLIC:
            return await self.get_public_url(file_id)
        else:
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")
            base_url = self.url_config.api_base_url
            return f"{base_url}/files/{file_id}/view"


# ===== MINIO FILE STORAGE IMPLEMENTATION =====

# MinIO availability flag
MINIO_AVAILABLE = False
try:
    from minio import Minio
    from minio.error import S3Error

    MINIO_AVAILABLE = True
except ImportError:
    logger.warning("MinIO storage not available: minio not installed. Install with 'uv add minio'")


class MinIOFileStorage(FileStorageInterface):
    """MinIO storage implementation with delegated metadata management"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = True,
        prefix: str = "agent-files/",
        metadata_storage_manager: Optional["MetadataStorageManager"] = None,
        url_config: S3URLConfig | None = None,
    ):
        """
        Initialize MinIOFileStorage.

        Args:
            endpoint: MinIO server endpoint
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket: MinIO bucket name
            secure: Whether to use HTTPS
            prefix: Key prefix for stored files
            metadata_storage_manager: Optional MetadataStorageManager for metadata operations.
                                     If not provided, one will be created during initialization.
            url_config: Optional S3URLConfig for URL generation settings.
                       If not provided, one will be created from environment variables.
        """
        if not MINIO_AVAILABLE:
            raise ImportError("MinIO storage requires minio package. Install with 'uv add minio'")

        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.prefix = prefix
        self.client = None
        self._metadata_storage_manager = metadata_storage_manager
        self._owns_metadata_manager = metadata_storage_manager is None
        self.url_config = url_config or S3URLConfig.from_env()

    async def initialize(self) -> bool:
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )

            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket {self.bucket}")

            # Initialize metadata storage manager if not provided
            if self._metadata_storage_manager is None:
                # Check if Elasticsearch is enabled
                elasticsearch_enabled = (
                    os.environ.get("ELASTICSEARCH_ENABLED", "").lower() == "true"
                )
                self._metadata_storage_manager = MetadataStorageManager(
                    elasticsearch_enabled=elasticsearch_enabled,
                    local_base_path="./file_storage",  # Default local path for fallback
                )
                self._owns_metadata_manager = True

            # Initialize the metadata storage manager
            if not await self._metadata_storage_manager.initialize():
                logger.error("Failed to initialize metadata storage manager")
                return False

            logger.info(f"Initialized MinIOFileStorage for bucket {self.bucket} on {self.endpoint}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MinIO storage: {e}")
            return False

    @property
    def metadata_storage(self) -> "MetadataStorageManager":
        """Get the metadata storage manager"""
        if self._metadata_storage_manager is None:
            raise RuntimeError("MinIOFileStorage not initialized - call initialize() first")
        return self._metadata_storage_manager

    async def store_file(self, content: bytes, filename: str, metadata: FileMetadata) -> str:
        """Store file in MinIO"""
        try:
            # Create storage filename with format: id_original_name.ext
            original_name = Path(filename)
            storage_filename = f"{metadata.file_id}_{original_name.stem}{original_name.suffix}"
            key = f"{self.prefix}{storage_filename}"

            # MinIO metadata can only contain ASCII characters
            # URL-encode the filename for MinIO metadata, keep original in our metadata
            from urllib.parse import quote
            safe_filename = quote(filename, safe='')  # URL-encode all non-ASCII chars
            
            # Prepare metadata for MinIO
            minio_metadata = {
                "filename": safe_filename,  # URL-encoded for MinIO compatibility
                "mime-type": metadata.mime_type or "application/octet-stream",
                "user-id": metadata.user_id,
                "session-id": metadata.session_id or "",
                "agent-id": metadata.agent_id or "",
                "is-generated": str(metadata.is_generated),
                "created-at": metadata.created_at.isoformat(),
                "file-id": metadata.file_id,
            }

            # Store file in MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=BytesIO(content),
                length=len(content),
                content_type=metadata.mime_type or "application/octet-stream",
                metadata=minio_metadata,
            )

            # Update metadata
            metadata.storage_path = key
            metadata.size_bytes = len(content)
            metadata.storage_backend = "minio"
            metadata.updated_at = datetime.now()

            # Store metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(metadata)

            logger.debug(f"Stored file {metadata.file_id} ({filename}) in MinIO")
            return metadata.file_id

        except Exception as e:
            logger.error(f"Failed to store file {metadata.file_id} in MinIO: {e}")
            raise

    async def retrieve_file(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """Retrieve file content and metadata from MinIO"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")

            # Get file from MinIO
            response = self.client.get_object(
                bucket_name=self.bucket, object_name=metadata.storage_path
            )

            content = response.read()
            response.close()
            response.release_conn()

            logger.debug(f"Retrieved file {file_id} from MinIO")
            return content, metadata

        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"File {file_id} not found in MinIO")
            else:
                logger.error(f"Failed to retrieve file {file_id} from MinIO: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to retrieve file {file_id} from MinIO: {e}")
            raise

    async def store_markdown_version(
        self, original_file_id: str, markdown_content: str
    ) -> str | None:
        """Store markdown version of a file as a separate file in MinIO"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                logger.error(f"Original file {original_file_id} not found for markdown storage")
                return None

            # Create new file ID for markdown version
            markdown_file_id = str(uuid.uuid4())

            # Create markdown filename with format: id_original_name.md
            base_name = Path(original_metadata.filename).stem
            markdown_filename = f"{markdown_file_id}_{base_name}.md"

            # Store markdown content as bytes
            markdown_bytes = markdown_content.encode("utf-8")
            markdown_key = f"{self.prefix}{markdown_filename}"

            # Prepare metadata for MinIO
            minio_metadata = {
                "filename": markdown_filename,
                "mime-type": "text/markdown",
                "user-id": original_metadata.user_id,
                "session-id": original_metadata.session_id or "",
                "agent-id": original_metadata.agent_id or "",
                "is-generated": "True",
                "created-at": datetime.now().isoformat(),
                "file-id": markdown_file_id,
                "original-file-id": original_file_id,
            }

            # Store markdown file in MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=markdown_key,
                data=BytesIO(markdown_bytes),
                length=len(markdown_bytes),
                content_type="text/markdown",
                metadata=minio_metadata,
            )

            # Create metadata for markdown file
            from datetime import datetime

            markdown_metadata = FileMetadata(
                file_id=markdown_file_id,
                filename=markdown_filename,
                mime_type="text/markdown",
                size_bytes=len(markdown_bytes),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=original_metadata.user_id,
                session_id=original_metadata.session_id,
                agent_id=original_metadata.agent_id,
                is_generated=True,  # Markdown version is generated
                tags=original_metadata.tags + ["markdown-conversion", "auto-generated"],
                custom_metadata={
                    **original_metadata.custom_metadata,
                    "original_file_id": original_file_id,
                    "conversion_source": original_metadata.filename,
                },
                storage_backend="minio",
                storage_path=markdown_key,
                conversion_status="success",
                conversion_timestamp=datetime.now(),
            )

            # Store markdown file metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(markdown_metadata)

            # Update original file metadata to reference markdown version
            await self.metadata_storage.update_metadata(
                original_file_id,
                {
                    "markdown_file_id": markdown_file_id,
                    "markdown_content": markdown_content,
                    "conversion_status": "success",
                    "conversion_timestamp": datetime.now(),
                    "conversion_error": None,
                },
            )

            logger.info(
                f"✅ Stored markdown version of {original_metadata.filename} as separate file {markdown_file_id} in MinIO"
            )
            return markdown_file_id

        except Exception as e:
            logger.error(
                f"Failed to store markdown version for file {original_file_id} in MinIO: {e}"
            )
            return None

    async def retrieve_markdown_version(
        self, original_file_id: str
    ) -> tuple[str, "FileMetadata"] | None:
        """Retrieve markdown version of a file from MinIO"""
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                return None

            if not original_metadata.markdown_file_id:
                return None

            # Retrieve markdown file
            markdown_content, markdown_metadata = await self.retrieve_file(
                original_metadata.markdown_file_id
            )
            markdown_text = markdown_content.decode("utf-8")

            return markdown_text, markdown_metadata

        except Exception as e:
            logger.error(
                f"Failed to retrieve markdown version for file {original_file_id} from MinIO: {e}"
            )
            return None

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from MinIO and metadata"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return False

            # Delete file from MinIO
            self.client.remove_object(bucket_name=self.bucket, object_name=metadata.storage_path)

            # Delete metadata using MetadataStorageManager
            await self.metadata_storage.delete_metadata(file_id)

            logger.debug(f"Deleted file {file_id} from MinIO")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id} from MinIO: {e}")
            return False

    async def list_files(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
    ) -> list[FileMetadata]:
        """List files with filtering using MetadataStorageManager"""
        try:
            # Delegate to MetadataStorageManager with storage_backend filter
            files = await self.metadata_storage.list_metadata(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                is_generated=is_generated,
                storage_backend="minio",
            )
            return files

        except Exception as e:
            logger.error(f"Failed to list files from MinIO: {e}")
            return []

    async def update_metadata(self, file_id: str, metadata_updates: dict[str, Any]) -> bool:
        """Update file metadata using MetadataStorageManager"""
        try:
            # Delegate to MetadataStorageManager
            result = await self.metadata_storage.update_metadata(file_id, metadata_updates)

            if result:
                logger.debug(f"Updated metadata for file {file_id} in MinIO")

            return result

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id} in MinIO: {e}")
            return False

    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists in MinIO"""
        # Get metadata from MetadataStorageManager
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            return False

        try:
            self.client.stat_object(bucket_name=self.bucket, object_name=metadata.storage_path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                logger.error(f"Error checking file existence in MinIO: {e}")
                return False

    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """Get file metadata without content using MetadataStorageManager"""
        return await self.metadata_storage.get_metadata(file_id)

    async def convert_file_to_markdown(self, file_id: str) -> str | None:
        """Convert file to markdown and return the content"""
        try:
            # Get file content and metadata
            content, metadata = await self.retrieve_file(file_id)

            # Import here to avoid circular import
            from agent_framework.processing.markdown_converter import markdown_converter

            # Convert to markdown
            markdown_content = await markdown_converter.convert_to_markdown(
                content, metadata.filename, metadata.mime_type or ""
            )

            if markdown_content:
                # Update metadata with conversion results using MetadataStorageManager
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "markdown_content": markdown_content,
                        "conversion_status": "success",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": None,
                    },
                )

                logger.info(f"✅ Converted file {file_id} to markdown")
                return markdown_content
            else:
                # Update metadata with failure
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": "Conversion returned empty content",
                    },
                )

                logger.warning(f"❌ Failed to convert file {file_id} to markdown")
                return None

        except Exception as e:
            logger.error(f"❌ Error converting file {file_id} to markdown: {e}")

            # Update metadata with error using MetadataStorageManager
            try:
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": str(e),
                    },
                )
            except Exception:
                pass  # Ignore errors updating metadata on failure

            return None

    async def analyze_image(self, file_id: str) -> dict[str, Any] | None:
        """Analyze image content using multimodal capabilities"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                logger.warning(f"File {file_id} not found for image analysis")
                return None

            # Check if file has visual content
            if not metadata.has_visual_content and not (
                metadata.mime_type and metadata.mime_type.startswith("image/")
            ):
                logger.warning(f"File {file_id} does not contain visual content")
                return None

            # For now, return a placeholder result indicating analysis capability
            # This will be implemented in later tasks with actual multimodal processing
            analysis_result = {
                "status": "not_implemented",
                "message": "Image analysis capability will be implemented in task 4",
                "file_id": file_id,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "has_visual_content": metadata.has_visual_content,
            }

            # Update metadata with analysis attempt using MetadataStorageManager
            await self.metadata_storage.update_metadata(
                file_id, {"multimodal_processing_status": "not_implemented"}
            )

            logger.debug(f"Image analysis placeholder for file {file_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in image analysis for file {file_id}: {e}")
            return None

    async def get_processing_status(self, file_id: str) -> dict[str, Any]:
        """Get comprehensive processing status for a file using MetadataStorageManager"""
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return {"file_id": file_id, "exists": False, "error": "File not found"}

            # Compile comprehensive processing status
            status = {
                "file_id": file_id,
                "exists": True,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "size_bytes": metadata.size_bytes,
                "storage_backend": metadata.storage_backend,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                # Conversion status
                "conversion_status": metadata.conversion_status,
                "conversion_timestamp": (
                    metadata.conversion_timestamp.isoformat()
                    if metadata.conversion_timestamp
                    else None
                ),
                "conversion_error": metadata.conversion_error,
                "has_markdown_version": metadata.markdown_file_id is not None,
                "markdown_file_id": metadata.markdown_file_id,
                # Multimodal processing status
                "has_visual_content": metadata.has_visual_content,
                "multimodal_processing_status": metadata.multimodal_processing_status,
                "image_analysis_available": metadata.image_analysis_result is not None,
                # Processing errors and warnings
                "processing_errors": metadata.processing_errors,
                "processing_warnings": metadata.processing_warnings,
                "total_processing_time_ms": metadata.total_processing_time_ms,
                # AI generation info
                "is_generated": metadata.is_generated,
                "generation_model": metadata.generation_model,
                "generation_prompt": metadata.generation_prompt,
                "generation_parameters": metadata.generation_parameters,
                # Tags and metadata
                "tags": metadata.tags,
                "custom_metadata": metadata.custom_metadata,
            }

            logger.debug(f"Retrieved processing status for file {file_id}")
            return status

        except Exception as e:
            logger.error(f"Error getting processing status for file {file_id}: {e}")
            return {"file_id": file_id, "exists": False, "error": str(e)}

    async def get_presigned_url(self, file_id: str, expires_in: int | None = None) -> str:
        """
        Generate a presigned MinIO URL for direct file access.

        This method generates a temporary signed URL that allows direct access to the file
        without requiring authentication through the API. The URL expires after the
        specified duration. Uses the configured MinIO endpoint.

        Args:
            file_id: The unique identifier of the file
            expires_in: URL expiration time in seconds. If not specified, uses the
                       default expiration from S3URLConfig (typically 3600 seconds).

        Returns:
            str: Presigned URL string for direct file access using the MinIO endpoint

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        from datetime import timedelta

        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File {file_id} not found")

        expiration = expires_in or self.url_config.default_expiration
        expiration = min(expiration, self.url_config.max_expiration)

        if expires_in is not None and expires_in > self.url_config.max_expiration:
            logger.debug(
                f"Requested expiration {expires_in}s exceeds max {self.url_config.max_expiration}s, "
                f"using max value"
            )

        url = self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=metadata.storage_path,
            expires=timedelta(seconds=expiration),
        )

        logger.debug(f"Generated presigned URL for file {file_id} with expiration {expiration}s")
        return url

    async def get_public_url(self, file_id: str) -> str:
        """
        Generate a public MinIO URL for direct file access.

        This method generates a permanent public URL for accessing the file directly.
        This requires the MinIO bucket to be configured for public access.
        Uses the configured MinIO endpoint.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: Public URL string using the configured MinIO endpoint

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File {file_id} not found")

        protocol = "https" if self.secure else "http"
        url = f"{protocol}://{self.endpoint}/{self.bucket}/{metadata.storage_path}"

        logger.debug(f"Generated public URL for file {file_id}")
        return url

    async def get_download_url(self, file_id: str) -> str:
        """
        Get download URL for forcing file download.

        Returns the appropriate URL format based on the S3_URL_MODE configuration:
        - API mode: Returns {API_BASE_URL}/files/{file_id}/download (forces download)
        - PRESIGNED mode: Returns a presigned MinIO URL with temporary access
        - PUBLIC mode: Returns a public MinIO URL (requires public bucket)

        For displaying images inline (in chat), use get_view_url() instead.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: Download URL in the format determined by S3_URL_MODE

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        if self.url_config.url_mode == S3URLMode.PRESIGNED:
            return await self.get_presigned_url(file_id)
        elif self.url_config.url_mode == S3URLMode.PUBLIC:
            return await self.get_public_url(file_id)
        else:
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")
            base_url = self.url_config.api_base_url
            return f"{base_url}/files/{file_id}/download"

    async def get_view_url(self, file_id: str) -> str:
        """
        Get URL for viewing file inline in browser (for images in chat, etc.)

        Returns the appropriate URL format based on the S3_URL_MODE configuration:
        - API mode: Returns {API_BASE_URL}/files/{file_id}/view (displays inline)
        - PRESIGNED mode: Returns a presigned MinIO URL (browsers display inline by default)
        - PUBLIC mode: Returns a public MinIO URL (browsers display inline by default)

        Use this for displaying generated images (charts, diagrams) in chat.
        For forcing file download, use get_download_url() instead.

        Args:
            file_id: The unique identifier of the file

        Returns:
            str: View URL for inline display

        Raises:
            FileNotFoundError: If file_id does not exist in storage
        """
        if self.url_config.url_mode == S3URLMode.PRESIGNED:
            return await self.get_presigned_url(file_id)
        elif self.url_config.url_mode == S3URLMode.PUBLIC:
            return await self.get_public_url(file_id)
        else:
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")
            base_url = self.url_config.api_base_url
            return f"{base_url}/files/{file_id}/view"


# ===== GCP FILE STORAGE IMPLEMENTATION =====

# GCP availability flag
GCP_AVAILABLE = False
try:
    from google.api_core.exceptions import GoogleAPIError
    from google.cloud import storage as gcs_storage
    from google.cloud.exceptions import NotFound as GCSNotFound

    GCP_AVAILABLE = True
except ImportError:
    logger.warning(
        "GCP storage not available: google-cloud-storage not installed. "
        "Install with 'uv add google-cloud-storage'"
    )


class GCPFileStorage(FileStorageInterface):
    """
    Google Cloud Storage file storage implementation with delegated metadata management.

    This implementation stores files in Google Cloud Storage buckets and delegates
    metadata operations to the MetadataStorageManager for consistent metadata handling
    across all storage backends.

    Attributes:
        bucket_name: Name of the GCS bucket
        project_id: GCP project ID (optional, uses default if not provided)
        credentials_path: Path to service account credentials JSON file (optional)
        prefix: Key prefix for stored files
        client: GCS client instance
        bucket: GCS bucket instance
        metadata_storage: MetadataStorageManager for metadata operations

    Example:
        ```python
        from agent_framework.storage.file_storages import GCPFileStorage

        # Initialize with explicit credentials
        storage = GCPFileStorage(
            bucket="my-bucket",
            project_id="my-project",
            credentials_path="/path/to/credentials.json",
            prefix="agent-files/"
        )

        # Or use default credentials (from environment)
        storage = GCPFileStorage(bucket="my-bucket")

        await storage.initialize()
        ```
    """

    def __init__(
        self,
        bucket: str,
        project_id: str | None = None,
        credentials_path: str | None = None,
        prefix: str = "agent-files/",
        metadata_storage_manager: Optional["MetadataStorageManager"] = None,
    ):
        """
        Initialize GCPFileStorage.

        Args:
            bucket: GCS bucket name
            project_id: GCP project ID (optional, uses default if not provided)
            credentials_path: Path to service account credentials JSON file (optional).
                            If not provided, uses Application Default Credentials.
            prefix: Key prefix for stored files (default: "agent-files/")
            metadata_storage_manager: Optional MetadataStorageManager for metadata operations.
                                     If not provided, one will be created during initialization.

        Raises:
            ImportError: If google-cloud-storage package is not installed
        """
        if not GCP_AVAILABLE:
            raise ImportError(
                "GCP storage requires google-cloud-storage package. "
                "Install with 'uv add google-cloud-storage'"
            )

        self.bucket_name = bucket
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.prefix = prefix
        self.client: Any | None = None
        self.bucket: Any | None = None
        self._metadata_storage_manager = metadata_storage_manager
        self._owns_metadata_manager = metadata_storage_manager is None

    async def initialize(self) -> bool:
        """
        Initialize GCP client and verify bucket access.

        Creates the GCS client using either explicit credentials or Application
        Default Credentials. Verifies that the bucket exists and is accessible.
        Also initializes the MetadataStorageManager if not provided.

        Returns:
            bool: True if initialization was successful, False otherwise

        Note:
            If credentials_path is not provided, the client will use Application
            Default Credentials (ADC). This includes:
            - GOOGLE_APPLICATION_CREDENTIALS environment variable
            - Default service account on GCP compute resources
            - gcloud CLI credentials
        """
        try:
            # Create GCS client
            if self.credentials_path:
                # Use explicit credentials file
                self.client = gcs_storage.Client.from_service_account_json(
                    self.credentials_path, project=self.project_id
                )
                logger.debug(f"Created GCS client with credentials from {self.credentials_path}")
            else:
                # Use Application Default Credentials
                self.client = gcs_storage.Client(project=self.project_id)
                logger.debug("Created GCS client with Application Default Credentials")

            # Get bucket reference and verify it exists
            try:
                self.bucket = self.client.get_bucket(self.bucket_name)
                logger.debug(f"Verified access to GCS bucket: {self.bucket_name}")
            except GCSNotFound:
                logger.error(
                    f"GCS bucket '{self.bucket_name}' not found. "
                    "Please create the bucket or check the bucket name."
                )
                return False
            except GoogleAPIError as e:
                logger.error(f"Failed to access GCS bucket '{self.bucket_name}': {e}")
                return False

            # Initialize metadata storage manager if not provided
            if self._metadata_storage_manager is None:
                # Check if Elasticsearch is enabled
                elasticsearch_enabled = (
                    os.environ.get("ELASTICSEARCH_ENABLED", "").lower() == "true"
                )
                self._metadata_storage_manager = MetadataStorageManager(
                    elasticsearch_enabled=elasticsearch_enabled,
                    local_base_path="./file_storage",  # Default local path for fallback
                )
                self._owns_metadata_manager = True

            # Initialize the metadata storage manager
            if not await self._metadata_storage_manager.initialize():
                logger.error("Failed to initialize metadata storage manager")
                return False

            logger.info(
                f"Initialized GCPFileStorage for bucket {self.bucket_name} "
                f"(project: {self.project_id or 'default'})"
            )
            return True

        except Exception as e:
            error_msg = str(e)
            if "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
                logger.error(
                    f"GCP authentication failed: {e}. "
                    "Please check your credentials configuration. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS environment variable or "
                    "provide credentials_path parameter."
                )
            else:
                logger.error(f"Failed to initialize GCP storage: {e}")
            return False

    @property
    def metadata_storage(self) -> "MetadataStorageManager":
        """
        Get the metadata storage manager.

        Returns:
            MetadataStorageManager: The metadata storage manager instance

        Raises:
            RuntimeError: If GCPFileStorage has not been initialized
        """
        if self._metadata_storage_manager is None:
            raise RuntimeError("GCPFileStorage not initialized - call initialize() first")
        return self._metadata_storage_manager

    async def store_file(self, content: bytes, filename: str, metadata: FileMetadata) -> str:
        """
        Store file in GCP Cloud Storage.

        Uploads the file content to GCS and stores metadata using the
        MetadataStorageManager. The file is stored with a key format of
        {prefix}{file_id}_{original_filename}.

        Args:
            content: File content as bytes
            filename: Original filename
            metadata: FileMetadata object with file information

        Returns:
            str: The file_id of the stored file

        Raises:
            RuntimeError: If storage is not initialized
            GoogleAPIError: If GCS upload fails
        """
        try:
            if self.bucket is None:
                raise RuntimeError("GCPFileStorage not initialized")

            # Create storage filename with format: id_original_name.ext
            original_name = Path(filename)
            storage_filename = f"{metadata.file_id}_{original_name.stem}{original_name.suffix}"
            key = f"{self.prefix}{storage_filename}"

            # Create blob and upload
            blob = self.bucket.blob(key)

            # Set content type
            blob.content_type = metadata.mime_type or "application/octet-stream"

            # Set custom metadata on the blob
            blob.metadata = {
                "filename": filename,
                "mime_type": metadata.mime_type or "",
                "user_id": metadata.user_id,
                "session_id": metadata.session_id or "",
                "agent_id": metadata.agent_id or "",
                "is_generated": str(metadata.is_generated),
                "created_at": metadata.created_at.isoformat(),
                "file_id": metadata.file_id,
            }

            # Upload content
            blob.upload_from_string(content, content_type=blob.content_type)

            # Update metadata
            metadata.storage_path = key
            metadata.size_bytes = len(content)
            metadata.storage_backend = "gcp"
            metadata.updated_at = datetime.now()

            # Store metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(metadata)

            logger.debug(f"Stored file {metadata.file_id} ({filename}) in GCS")
            return metadata.file_id

        except GoogleAPIError as e:
            logger.error(f"Failed to store file {metadata.file_id} in GCS: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error storing file {metadata.file_id} in GCS: {e}")
            raise

    async def store_markdown_version(
        self, original_file_id: str, markdown_content: str
    ) -> str | None:
        """
        Store markdown version of a file as a separate file in GCS.

        Creates a new file containing the markdown conversion of the original
        file and links them through metadata.

        Args:
            original_file_id: ID of the original file
            markdown_content: Markdown content to store

        Returns:
            str: File ID of the markdown version, or None if failed
        """
        try:
            if self.bucket is None:
                raise RuntimeError("GCPFileStorage not initialized")

            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                logger.error(f"Original file {original_file_id} not found for markdown storage")
                return None

            # Create new file ID for markdown version
            markdown_file_id = str(uuid.uuid4())

            # Create markdown filename with format: id_original_name.md
            base_name = Path(original_metadata.filename).stem
            markdown_filename = f"{markdown_file_id}_{base_name}.md"

            # Store markdown content as bytes
            markdown_bytes = markdown_content.encode("utf-8")
            markdown_key = f"{self.prefix}{markdown_filename}"

            # Create blob and upload
            blob = self.bucket.blob(markdown_key)
            blob.content_type = "text/markdown"
            blob.metadata = {
                "filename": markdown_filename,
                "mime_type": "text/markdown",
                "user_id": original_metadata.user_id,
                "session_id": original_metadata.session_id or "",
                "agent_id": original_metadata.agent_id or "",
                "is_generated": "True",
                "created_at": datetime.now().isoformat(),
                "file_id": markdown_file_id,
                "original_file_id": original_file_id,
            }

            blob.upload_from_string(markdown_bytes, content_type="text/markdown")

            # Create metadata for markdown file
            markdown_metadata = FileMetadata(
                file_id=markdown_file_id,
                filename=markdown_filename,
                mime_type="text/markdown",
                size_bytes=len(markdown_bytes),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=original_metadata.user_id,
                session_id=original_metadata.session_id,
                agent_id=original_metadata.agent_id,
                is_generated=True,  # Markdown version is generated
                tags=original_metadata.tags + ["markdown-conversion", "auto-generated"],
                custom_metadata={
                    **original_metadata.custom_metadata,
                    "original_file_id": original_file_id,
                    "conversion_source": original_metadata.filename,
                },
                storage_backend="gcp",
                storage_path=markdown_key,
                conversion_status="success",
                conversion_timestamp=datetime.now(),
            )

            # Store markdown file metadata using MetadataStorageManager
            await self.metadata_storage.store_metadata(markdown_metadata)

            # Update original file metadata to reference markdown version
            await self.metadata_storage.update_metadata(
                original_file_id,
                {
                    "markdown_file_id": markdown_file_id,
                    "markdown_content": markdown_content,
                    "conversion_status": "success",
                    "conversion_timestamp": datetime.now(),
                    "conversion_error": None,
                },
            )

            logger.info(
                f"✅ Stored markdown version of {original_metadata.filename} "
                f"as separate file {markdown_file_id} in GCS"
            )
            return markdown_file_id

        except Exception as e:
            logger.error(
                f"Failed to store markdown version for file {original_file_id} in GCS: {e}"
            )
            return None

    async def retrieve_markdown_version(
        self, original_file_id: str
    ) -> tuple[str, "FileMetadata"] | None:
        """
        Retrieve markdown version of a file from GCS.

        Args:
            original_file_id: ID of the original file

        Returns:
            Tuple of (markdown_content, metadata) or None if not found
        """
        try:
            # Get original metadata from MetadataStorageManager
            original_metadata = await self.metadata_storage.get_metadata(original_file_id)
            if original_metadata is None:
                return None

            if not original_metadata.markdown_file_id:
                return None

            # Retrieve markdown file
            markdown_content, markdown_metadata = await self.retrieve_file(
                original_metadata.markdown_file_id
            )
            markdown_text = markdown_content.decode("utf-8")

            return markdown_text, markdown_metadata

        except Exception as e:
            logger.error(
                f"Failed to retrieve markdown version for file {original_file_id} from GCS: {e}"
            )
            return None

    async def retrieve_file(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """
        Retrieve file content and metadata from GCS.

        Args:
            file_id: Unique identifier of the file

        Returns:
            Tuple of (content_bytes, metadata)

        Raises:
            FileNotFoundError: If file is not found
            RuntimeError: If storage is not initialized
        """
        try:
            if self.bucket is None:
                raise RuntimeError("GCPFileStorage not initialized")

            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                raise FileNotFoundError(f"File {file_id} not found")

            # Get blob from GCS
            blob = self.bucket.blob(metadata.storage_path)

            # Download content
            try:
                content = blob.download_as_bytes()
            except GCSNotFound:
                raise FileNotFoundError(f"File {file_id} not found in GCS")

            logger.debug(f"Retrieved file {file_id} from GCS")
            return content, metadata

        except FileNotFoundError:
            raise
        except GoogleAPIError as e:
            logger.error(f"Failed to retrieve file {file_id} from GCS: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving file {file_id} from GCS: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from GCS and metadata.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if self.bucket is None:
                raise RuntimeError("GCPFileStorage not initialized")

            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return False

            # Delete file from GCS
            blob = self.bucket.blob(metadata.storage_path)
            try:
                blob.delete()
            except GCSNotFound:
                logger.warning(f"File {file_id} not found in GCS, removing metadata only")

            # Delete metadata using MetadataStorageManager
            await self.metadata_storage.delete_metadata(file_id)

            logger.debug(f"Deleted file {file_id} from GCS")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id} from GCS: {e}")
            return False

    async def list_files(
        self,
        user_id: str,
        session_id: str | None = None,
        agent_id: str | None = None,
        is_generated: bool | None = None,
    ) -> list[FileMetadata]:
        """
        List files with filtering using MetadataStorageManager.

        Delegates to MetadataStorageManager with storage_backend="gcp" filter.

        Args:
            user_id: Required filter by user ID
            session_id: Optional filter by session ID
            agent_id: Optional filter by agent ID
            is_generated: Optional filter by whether file was AI-generated

        Returns:
            List of FileMetadata objects matching the filters
        """
        try:
            # Delegate to MetadataStorageManager with storage_backend filter
            files = await self.metadata_storage.list_metadata(
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                is_generated=is_generated,
                storage_backend="gcp",
            )
            return files

        except Exception as e:
            logger.error(f"Failed to list files from GCS: {e}")
            return []

    async def update_metadata(self, file_id: str, metadata_updates: dict[str, Any]) -> bool:
        """
        Update file metadata using MetadataStorageManager.

        Args:
            file_id: Unique identifier of the file
            metadata_updates: Dictionary of field names and their new values

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Delegate to MetadataStorageManager
            result = await self.metadata_storage.update_metadata(file_id, metadata_updates)

            if result:
                logger.debug(f"Updated metadata for file {file_id} in GCS")

            return result

        except Exception as e:
            logger.error(f"Failed to update metadata for file {file_id} in GCS: {e}")
            return False

    async def file_exists(self, file_id: str) -> bool:
        """
        Check if file exists in GCS.

        Args:
            file_id: Unique identifier of the file

        Returns:
            bool: True if file exists, False otherwise
        """
        if self.bucket is None:
            return False

        # Get metadata from MetadataStorageManager
        metadata = await self.metadata_storage.get_metadata(file_id)
        if metadata is None:
            return False

        try:
            blob = self.bucket.blob(metadata.storage_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence in GCS: {e}")
            return False

    async def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """
        Get file metadata without content using MetadataStorageManager.

        Args:
            file_id: Unique identifier of the file

        Returns:
            FileMetadata if found, None otherwise
        """
        return await self.metadata_storage.get_metadata(file_id)

    async def convert_file_to_markdown(self, file_id: str) -> str | None:
        """
        Convert file to markdown and return the content.

        Retrieves the file, converts it to markdown using the markdown converter,
        and updates the metadata with conversion results.

        Args:
            file_id: Unique identifier of the file

        Returns:
            Markdown content string or None if conversion failed
        """
        try:
            # Get file content and metadata
            content, metadata = await self.retrieve_file(file_id)

            # Import here to avoid circular import
            from agent_framework.processing.markdown_converter import markdown_converter

            # Convert to markdown
            markdown_content = await markdown_converter.convert_to_markdown(
                content, metadata.filename, metadata.mime_type or ""
            )

            if markdown_content:
                # Update metadata with conversion results using MetadataStorageManager
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "markdown_content": markdown_content,
                        "conversion_status": "success",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": None,
                    },
                )

                logger.info(f"✅ Converted file {file_id} to markdown")
                return markdown_content
            else:
                # Update metadata with failure
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": "Conversion returned empty content",
                    },
                )

                logger.warning(f"❌ Failed to convert file {file_id} to markdown")
                return None

        except Exception as e:
            logger.error(f"❌ Error converting file {file_id} to markdown: {e}")

            # Update metadata with error using MetadataStorageManager
            try:
                await self.metadata_storage.update_metadata(
                    file_id,
                    {
                        "conversion_status": "failed",
                        "conversion_timestamp": datetime.now(),
                        "conversion_error": str(e),
                    },
                )
            except Exception:
                pass  # Ignore errors updating metadata on failure

            return None

    async def analyze_image(self, file_id: str) -> dict[str, Any] | None:
        """
        Analyze image content using multimodal capabilities.

        Args:
            file_id: Unique identifier of the file

        Returns:
            Analysis result dictionary or None if analysis failed
        """
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                logger.warning(f"File {file_id} not found for image analysis")
                return None

            # Check if file has visual content
            if not metadata.has_visual_content and not (
                metadata.mime_type and metadata.mime_type.startswith("image/")
            ):
                logger.warning(f"File {file_id} does not contain visual content")
                return None

            # For now, return a placeholder result indicating analysis capability
            # This will be implemented in later tasks with actual multimodal processing
            analysis_result = {
                "status": "not_implemented",
                "message": "Image analysis capability will be implemented in task 4",
                "file_id": file_id,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "has_visual_content": metadata.has_visual_content,
            }

            # Update metadata with analysis attempt using MetadataStorageManager
            await self.metadata_storage.update_metadata(
                file_id, {"multimodal_processing_status": "not_implemented"}
            )

            logger.debug(f"Image analysis placeholder for file {file_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in image analysis for file {file_id}: {e}")
            return None

    async def get_processing_status(self, file_id: str) -> dict[str, Any]:
        """
        Get comprehensive processing status for a file using MetadataStorageManager.

        Args:
            file_id: Unique identifier of the file

        Returns:
            Dictionary containing processing status information
        """
        try:
            # Get metadata from MetadataStorageManager
            metadata = await self.metadata_storage.get_metadata(file_id)
            if metadata is None:
                return {"file_id": file_id, "exists": False, "error": "File not found"}

            # Compile comprehensive processing status
            status = {
                "file_id": file_id,
                "exists": True,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "size_bytes": metadata.size_bytes,
                "storage_backend": metadata.storage_backend,
                "created_at": metadata.created_at.isoformat(),
                "updated_at": metadata.updated_at.isoformat(),
                # Conversion status
                "conversion_status": metadata.conversion_status,
                "conversion_timestamp": (
                    metadata.conversion_timestamp.isoformat()
                    if metadata.conversion_timestamp
                    else None
                ),
                "conversion_error": metadata.conversion_error,
                "has_markdown_version": metadata.markdown_file_id is not None,
                "markdown_file_id": metadata.markdown_file_id,
                # Multimodal processing status
                "has_visual_content": metadata.has_visual_content,
                "multimodal_processing_status": metadata.multimodal_processing_status,
                "image_analysis_available": metadata.image_analysis_result is not None,
                # Processing errors and warnings
                "processing_errors": metadata.processing_errors,
                "processing_warnings": metadata.processing_warnings,
                "total_processing_time_ms": metadata.total_processing_time_ms,
                # AI generation info
                "is_generated": metadata.is_generated,
                "generation_model": metadata.generation_model,
                "generation_prompt": metadata.generation_prompt,
                "generation_parameters": metadata.generation_parameters,
                # Tags and metadata
                "tags": metadata.tags,
                "custom_metadata": metadata.custom_metadata,
            }

            logger.debug(f"Retrieved processing status for file {file_id}")
            return status

        except Exception as e:
            logger.error(f"Error getting processing status for file {file_id}: {e}")
            return {"file_id": file_id, "exists": False, "error": str(e)}
