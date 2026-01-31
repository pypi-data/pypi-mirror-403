"""Unified file upload abstraction for different LLM providers."""

import os
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional

from google import genai
from google.genai.types import File

from mfcli.utils.config import get_config
from mfcli.utils.logger import get_logger

logger = get_logger(__name__)


class FileUploadProvider(str, Enum):
    """Supported file upload providers."""
    GEMINI = "gemini"
    OPENAI = "openai"


class BaseFileUploader(ABC):
    """Base class for file upload implementations."""

    @abstractmethod
    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> dict:
        """
        Upload a file to the provider's file storage.
        
        Args:
            file_path: Path to the local file to upload
            display_name: Optional display name for the file
            
        Returns:
            Dictionary containing file metadata including URI/ID for accessing the file
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from the provider's storage.
        
        Args:
            file_id: The ID/URI of the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_file_info(self, file_id: str) -> dict:
        """
        Get information about an uploaded file.
        
        Args:
            file_id: The ID/URI of the file
            
        Returns:
            Dictionary containing file metadata
        """
        pass


class GeminiFileUploader(BaseFileUploader):
    """File uploader implementation for Google Gemini."""

    def __init__(self):
        """Initialize the Gemini file uploader."""
        config = get_config()
        self.client = genai.Client(api_key=config.google_api_key)
        logger.info("Initialized Gemini file uploader")

    @staticmethod
    def _file_access_check(file_path: str):
        file_path_obj = Path(file_path)

        # Validate file exists and is readable
        if not file_path_obj.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not os.access(file_path_obj, os.R_OK):
            raise ValueError(f"File is not readable: {file_path}")

    def upload(self, file_path: str) -> File:
        """
        Upload a file to Gemini Files API and return File object.

        Args:
            file_path: Path to the local file to upload

        Returns:
            Gemini types File object.

        Raises:
            ValueError: If file doesn't exist or is not readable
            Exception: If upload fails
        """
        self._file_access_check(file_path)
        return self.client.files.upload(file=file_path)

    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> dict:
        """
        Upload a file to Gemini Files API.
        
        Args:
            file_path: Path to the local file to upload
            display_name: Optional display name for the file
            
        Returns:
            Dictionary with file metadata including 'uri', 'name', 'mime_type', 'size_bytes'
            
        Raises:
            ValueError: If file doesn't exist or is not readable
            Exception: If upload fails
        """

        self._file_access_check(file_path)

        file_path_obj = Path(file_path)

        # Use filename as display name if not provided
        if display_name is None:
            display_name = file_path_obj.name

        try:
            logger.info(f"Uploading file to Gemini: {file_path}")

            # Upload the file
            uploaded_file = self.client.files.upload(
                file=str(file_path_obj),
                config={'display_name': display_name}
            )

            # Extract metadata
            result = {
                'uri': uploaded_file.uri,
                'name': uploaded_file.name,
                'display_name': uploaded_file.display_name,
                'mime_type': uploaded_file.mime_type,
                'size_bytes': uploaded_file.size_bytes,
                'state': uploaded_file.state.name,
                'provider': FileUploadProvider.GEMINI.value
            }

            logger.info(f"Successfully uploaded file: {result['name']}")
            return result

        except Exception as e:
            logger.error(f"Failed to upload file to Gemini: {e}")
            raise Exception(f"Failed to upload file to Gemini: {str(e)}")

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Gemini Files API.
        
        Args:
            file_id: The name/ID of the file (e.g., 'files/abc123')
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            logger.info(f"Deleting file from Gemini: {file_id}")
            self.client.files.delete(name=file_id)
            logger.info(f"Successfully deleted file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Gemini: {e}")
            return False

    def get_file_info(self, file_id: str) -> dict:
        """
        Get information about an uploaded file.
        
        Args:
            file_id: The name/ID of the file (e.g., 'files/abc123')
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            logger.info(f"Getting file info from Gemini: {file_id}")
            file_info = self.client.files.get(name=file_id)

            result = {
                'uri': file_info.uri,
                'name': file_info.name,
                'display_name': file_info.display_name,
                'mime_type': file_info.mime_type,
                'size_bytes': file_info.size_bytes,
                'state': file_info.state.name,
                'provider': FileUploadProvider.GEMINI.value
            }

            return result

        except Exception as e:
            logger.error(f"Failed to get file info from Gemini: {e}")
            raise Exception(f"Failed to get file info: {str(e)}")


class OpenAIFileUploader(BaseFileUploader):
    """File uploader implementation for OpenAI (placeholder for future implementation)."""

    def __init__(self):
        """Initialize the OpenAI file uploader."""
        config = get_config()
        # This will be implemented when OpenAI support is added
        logger.info("OpenAI file uploader - not yet implemented")
        raise NotImplementedError("OpenAI file upload support coming soon")

    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> dict:
        """Upload a file to OpenAI."""
        raise NotImplementedError("OpenAI file upload not yet implemented")

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from OpenAI."""
        raise NotImplementedError("OpenAI file deletion not yet implemented")

    def get_file_info(self, file_id: str) -> dict:
        """Get file info from OpenAI."""
        raise NotImplementedError("OpenAI file info not yet implemented")


class FileUploadManager:
    """Manager class to handle file uploads across different providers."""

    def __init__(self, provider: FileUploadProvider = FileUploadProvider.GEMINI):
        """
        Initialize the file upload manager.
        
        Args:
            provider: The file upload provider to use (default: GEMINI)
        """
        self.provider = provider
        self.uploader = self._get_uploader(provider)

    def _get_uploader(self, provider: FileUploadProvider) -> BaseFileUploader:
        """Get the appropriate uploader for the specified provider."""
        if provider == FileUploadProvider.GEMINI:
            return GeminiFileUploader()
        elif provider == FileUploadProvider.OPENAI:
            return OpenAIFileUploader()
        else:
            raise ValueError(f"Unsupported file upload provider: {provider}")

    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> dict:
        """
        Upload a file using the configured provider.
        
        Args:
            file_path: Path to the local file to upload
            display_name: Optional display name for the file
            
        Returns:
            Dictionary with file metadata
        """
        return self.uploader.upload_file(file_path, display_name)

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file using the configured provider.
        
        Args:
            file_id: The ID/URI of the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        return self.uploader.delete_file(file_id)

    def get_file_info(self, file_id: str) -> dict:
        """
        Get file information using the configured provider.
        
        Args:
            file_id: The ID/URI of the file
            
        Returns:
            Dictionary containing file metadata
        """
        return self.uploader.get_file_info(file_id)


def get_file_upload_manager(provider: FileUploadProvider = FileUploadProvider.GEMINI) -> FileUploadManager:
    """
    Factory function to get a file upload manager instance.
    
    Args:
        provider: The file upload provider to use (default: GEMINI)
        
    Returns:
        FileUploadManager instance
    """
    return FileUploadManager(provider)
