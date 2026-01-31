"""
File access tools for retrieving file paths and URLs.

These tools help bridge the gap between file storage and other tools
that need to access stored files (like PDF generation with images).
"""

import logging
from typing import Callable
from pathlib import Path

from .base import AgentTool, ToolDependencyError

logger = logging.getLogger(__name__)


class GetFilePathTool(AgentTool):
    """Tool for getting an accessible path or URL for a stored file."""
    
    def get_tool_function(self) -> Callable:
        """Return the get file path function."""
        
        async def get_file_path(file_id: str) -> str:
            """
            Get an accessible path or URL for a stored file.
            
            For local storage: Returns the absolute file path
            For S3/MinIO: Returns a presigned URL for direct access
            
            This is useful when you need to reference a file in HTML/PDF generation.
            
            Args:
                file_id: The file ID returned from file storage operations
            
            Returns:
                Either an absolute file path or a presigned URL that can be used in HTML
            
            Example usage:
                1. Create a chart image and get file_id
                2. Use this tool to get the path/URL
                3. Use the path in HTML: <img src="file:///path/to/image.png">
                   or URL: <img src="https://bucket.s3.amazonaws.com/...">
            """
            self._ensure_initialized()
            
            # Check file storage availability
            if not self.file_storage:
                raise ToolDependencyError(
                    "File storage is required but was not provided. "
                    "Ensure file_storage is set via set_context()."
                )
            
            try:
                # Get file metadata
                metadata = await self.file_storage.get_file_metadata(file_id)
                
                if not metadata:
                    return f"Error: File with ID '{file_id}' not found in storage"
                
                # Check storage backend type
                backend_name = metadata.storage_backend
                
                if backend_name == "local":
                    # For local storage, return absolute path
                    storage_path = metadata.storage_path
                    
                    # Verify file exists
                    file_path = Path(storage_path)
                    if not file_path.exists():
                        return f"Error: File exists in metadata but not on disk: {storage_path}"
                    
                    # Return absolute path with file:// protocol for HTML
                    absolute_path = file_path.resolve()
                    logger.info(f"Retrieved local file path for {file_id}: {absolute_path}")
                    return f"file://{absolute_path}"
                
                else:
                    # For S3/MinIO, get a download URL (presigned or public)
                    logger.info(f"🔍 GetFilePathTool: S3/MinIO backend '{backend_name}' detected for {file_id}")
                    if hasattr(self.file_storage, 'get_download_url'):
                        logger.info(f"🔍 GetFilePathTool: Calling get_download_url({file_id})")
                        download_url = await self.file_storage.get_download_url(file_id)
                        logger.info(f"🔍 GetFilePathTool: get_download_url returned: {download_url[:100] if download_url else 'None'}...")
                        return download_url
                    else:
                        error_msg = f"Storage backend '{backend_name}' does not support get_download_url"
                        logger.error(error_msg)
                        return f"Error: {error_msg}"
                
            except Exception as e:
                error_msg = f"Failed to get file path: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return f"Error: {str(e)}"
        
        return get_file_path


__all__ = [
    "GetFilePathTool",
]
