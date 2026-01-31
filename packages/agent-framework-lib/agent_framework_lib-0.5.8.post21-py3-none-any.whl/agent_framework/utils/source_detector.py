"""Source detection for image URLs and file paths.

This module provides automatic detection of storage sources for images,
identifying whether they originate from web URLs, cloud storage (S3, GCP, Azure),
local storage, MinIO, or data URIs.
"""

import os
import re
from enum import Enum

from pydantic import BaseModel


class FileStorageType(Enum):
    """Enumeration of possible storage sources for files."""

    WEB = "web"
    S3 = "s3"
    GCP = "gcp"
    AZURE = "azure"
    LOCAL = "local"
    MINIO = "minio"
    DATA_URI = "data_uri"
    UNKNOWN = "unknown"


class FileStorageInfo(BaseModel):
    """Information about the detected storage source of a file.

    Attributes:
        type: The detected storage type (web, s3, gcp, azure, local, minio, data_uri, unknown)
        detected_from: The pattern or indicator used for detection
        endpoint: Optional custom endpoint URL (for S3/MinIO custom endpoints)
    """

    type: FileStorageType
    detected_from: str
    endpoint: str | None = None

    model_config = {"use_enum_values": True}


class SourceDetector:
    """Detects storage source from image URLs and file paths.

    Analyzes URL patterns to determine if an image originates from web URLs,
    cloud storage (S3, GCP, Azure), local storage, MinIO, or data URIs.

    Attributes:
        custom_s3_endpoints: List of custom S3-compatible endpoints
        custom_minio_endpoints: List of custom MinIO endpoints
    """

    S3_PATTERNS = [
        r"s3\.amazonaws\.com",
        r"s3-[a-z0-9-]+\.amazonaws\.com",
        r"s3\.[a-z0-9-]+\.amazonaws\.com",
    ]

    GCP_PATTERNS = [
        r"storage\.googleapis\.com",
        r"storage\.cloud\.google\.com",
    ]

    AZURE_PATTERNS = [
        r"blob\.core\.windows\.net",
        r"[a-z0-9]+\.blob\.core\.windows\.net",
    ]

    MINIO_PORT_PATTERNS = [
        r":9000(/|$|\?)",
        r":9001(/|$|\?)",
    ]

    def __init__(
        self,
        custom_s3_endpoints: list[str] | None = None,
        custom_minio_endpoints: list[str] | None = None,
    ):
        """Initialize SourceDetector with optional custom endpoints.

        Args:
            custom_s3_endpoints: List of custom S3-compatible endpoints
            custom_minio_endpoints: List of custom MinIO endpoints
        """
        self.custom_s3_endpoints = custom_s3_endpoints or self._load_env_endpoints(
            "CUSTOM_S3_ENDPOINTS"
        )
        self.custom_minio_endpoints = custom_minio_endpoints or self._load_env_endpoints(
            "CUSTOM_MINIO_ENDPOINTS"
        )

    @staticmethod
    def _load_env_endpoints(env_var: str) -> list[str]:
        """Load endpoints from environment variable (comma-separated)."""
        value = os.environ.get(env_var, "")
        if not value:
            return []
        return [ep.strip() for ep in value.split(",") if ep.strip()]

    def detect(self, url: str | None) -> FileStorageInfo:
        """Analyze URL and return storage source information.

        Args:
            url: The URL or path to analyze

        Returns:
            FileStorageInfo with detected type and pattern
        """
        if url is None:
            return FileStorageInfo(
                type=FileStorageType.UNKNOWN,
                detected_from="null_input",
            )

        if not isinstance(url, str) or not url.strip():
            return FileStorageInfo(
                type=FileStorageType.UNKNOWN,
                detected_from="empty_url",
            )

        url = url.strip()

        if result := self._detect_data_uri(url):
            return result

        if result := self._detect_s3(url):
            return result

        if result := self._detect_gcp(url):
            return result

        if result := self._detect_azure(url):
            return result

        if result := self._detect_minio(url):
            return result

        if result := self._detect_local(url):
            return result

        if result := self._detect_web(url):
            return result

        return FileStorageInfo(
            type=FileStorageType.UNKNOWN,
            detected_from="no_pattern_match",
        )

    def _detect_data_uri(self, url: str) -> FileStorageInfo | None:
        """Detect data URI (base64 encoded images)."""
        if url.startswith("data:image/"):
            return FileStorageInfo(
                type=FileStorageType.DATA_URI,
                detected_from="base64_encoded",
            )
        return None

    def _detect_s3(self, url: str) -> FileStorageInfo | None:
        """Detect S3 storage URLs."""
        if url.startswith("s3://"):
            return FileStorageInfo(
                type=FileStorageType.S3,
                detected_from="s3_protocol",
            )

        for pattern in self.S3_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return FileStorageInfo(
                    type=FileStorageType.S3,
                    detected_from=f"pattern:{pattern}",
                )

        for endpoint in self.custom_s3_endpoints:
            if endpoint.lower() in url.lower():
                return FileStorageInfo(
                    type=FileStorageType.S3,
                    detected_from=f"custom_endpoint:{endpoint}",
                    endpoint=endpoint,
                )

        return None

    def _detect_gcp(self, url: str) -> FileStorageInfo | None:
        """Detect GCP storage URLs."""
        if url.startswith("gs://"):
            return FileStorageInfo(
                type=FileStorageType.GCP,
                detected_from="gs_protocol",
            )

        for pattern in self.GCP_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return FileStorageInfo(
                    type=FileStorageType.GCP,
                    detected_from=f"pattern:{pattern}",
                )

        return None

    def _detect_azure(self, url: str) -> FileStorageInfo | None:
        """Detect Azure Blob storage URLs."""
        for pattern in self.AZURE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return FileStorageInfo(
                    type=FileStorageType.AZURE,
                    detected_from=f"pattern:{pattern}",
                )

        return None

    def _detect_minio(self, url: str) -> FileStorageInfo | None:
        """Detect MinIO storage URLs."""
        for endpoint in self.custom_minio_endpoints:
            if endpoint.lower() in url.lower():
                return FileStorageInfo(
                    type=FileStorageType.MINIO,
                    detected_from=f"custom_endpoint:{endpoint}",
                    endpoint=endpoint,
                )

        for pattern in self.MINIO_PORT_PATTERNS:
            if re.search(pattern, url):
                return FileStorageInfo(
                    type=FileStorageType.MINIO,
                    detected_from=f"port_pattern:{pattern}",
                )

        return None

    def _detect_local(self, url: str) -> FileStorageInfo | None:
        """Detect local file paths."""
        if url.startswith("file://"):
            return FileStorageInfo(
                type=FileStorageType.LOCAL,
                detected_from="file_protocol",
            )

        if url.startswith("/"):
            return FileStorageInfo(
                type=FileStorageType.LOCAL,
                detected_from="unix_absolute_path",
            )

        if re.match(r"^[A-Za-z]:\\", url) or re.match(r"^[A-Za-z]:/", url):
            return FileStorageInfo(
                type=FileStorageType.LOCAL,
                detected_from="windows_absolute_path",
            )

        if url.startswith("./") or url.startswith("../"):
            return FileStorageInfo(
                type=FileStorageType.LOCAL,
                detected_from="relative_path",
            )

        return None

    def _detect_web(self, url: str) -> FileStorageInfo | None:
        """Detect generic web URLs (http/https)."""
        if url.startswith("http://") or url.startswith("https://"):
            return FileStorageInfo(
                type=FileStorageType.WEB,
                detected_from="http_protocol",
            )

        return None
