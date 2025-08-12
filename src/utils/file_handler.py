"""
File handling utilities for document upload and validation.

This module provides secure file validation, storage, and processing utilities
with content-based validation and size limits.
"""

import os
import uuid
# import magic  # Commented out - requires system libmagic
import asyncio
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
import logging

from .config import settings

logger = logging.getLogger(__name__)


class FileValidator:
    """
    File validation utility with security checks.

    Provides content-based file validation, size checking, and secure
    file handling for PDF documents.
    """

    def __init__(self):
        """Initialize file validator with configuration."""
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_mime_types = {"application/pdf"}
        self.allowed_extensions = {".pdf"}

    async def validate_pdf_file(self, file: UploadFile) -> Tuple[bytes, str]:
        """
        Validate uploaded PDF file.

        Args:
            file: FastAPI UploadFile object.

        Returns:
            Tuple[bytes, str]: File content and validated filename.

        Raises:
            HTTPException: If validation fails.
        """
        try:
            # Check filename extension
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")

            filename_lower = file.filename.lower()
            if not any(filename_lower.endswith(ext) for ext in self.allowed_extensions):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only PDF files are allowed. Got: {file.filename}",
                )

            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer

            # Check file size
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB",
                )

            if len(content) < 100:  # Minimum viable PDF size
                raise HTTPException(
                    status_code=400, detail="File too small to be a valid PDF"
                )

            # Content-based validation using PDF header check
            if not content.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=400, detail="Invalid PDF file - missing PDF header"
                )

            logger.info(
                f"File validation successful: {file.filename} ({len(content)} bytes)"
            )
            return content, file.filename

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise HTTPException(
                status_code=500, detail=f"File validation failed: {str(e)}"
            )


class FileStorage:
    """
    Secure file storage utility.

    Handles temporary file storage and cleanup with unique identifiers.
    """

    def __init__(self):
        """Initialize file storage with configuration."""
        self.upload_dir = settings.UPLOAD_DIR
        self.results_dir = settings.RESULTS_DIR

        # Ensure directories exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate unique filename while preserving extension.

        Args:
            original_filename: Original file name.

        Returns:
            str: Unique filename.
        """
        _, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"

    async def save_upload(self, content: bytes, filename: str) -> str:
        """
        Save uploaded file temporarily.

        Args:
            content: File content bytes.
            filename: Original filename.

        Returns:
            str: Unique file identifier.
        """
        try:
            unique_filename = self.generate_unique_filename(filename)
            file_path = os.path.join(self.upload_dir, unique_filename)

            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self._write_file_sync(file_path, content)
            )

            logger.info(f"File saved: {unique_filename}")
            return unique_filename

        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise Exception(f"Failed to save file: {str(e)}")

    def _write_file_sync(self, file_path: str, content: bytes) -> None:
        """
        Write file synchronously (for executor).

        Args:
            file_path: Path to write file.
            content: File content.
        """
        with open(file_path, "wb") as f:
            f.write(content)

    async def cleanup_upload(self, filename: str) -> None:
        """
        Clean up temporary uploaded file.

        Args:
            filename: Unique filename to clean up.
        """
        try:
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.exists(file_path):
                await asyncio.get_event_loop().run_in_executor(
                    None, os.remove, file_path
                )
                logger.info(f"Cleaned up file: {filename}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {filename}: {e}")

    def get_upload_stats(self) -> dict:
        """
        Get upload directory statistics.

        Returns:
            dict: Upload directory stats.
        """
        try:
            files = os.listdir(self.upload_dir)
            total_size = 0

            for filename in files:
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)

            return {
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
            }
        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
            return {"total_files": 0, "total_size_bytes": 0, "total_size_mb": 0}


class ResultStorage:
    """
    Result storage utility for classification results.

    Handles persistent storage of classification results as JSON files.
    """

    def __init__(self):
        """Initialize result storage."""
        self.results_dir = settings.RESULTS_DIR
        os.makedirs(self.results_dir, exist_ok=True)

    async def save_result(self, task_id: str, result: dict) -> None:
        """
        Save classification result.

        Args:
            task_id: Unique task identifier.
            result: Classification result dictionary.
        """
        try:

            result_file = os.path.join(self.results_dir, f"{task_id}.json")

            # Write result file asynchronously
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._write_result_sync(result_file, result)
            )

            logger.info(f"Result saved: {task_id}")

        except Exception as e:
            logger.error(f"Error saving result {task_id}: {e}")
            raise

    def _write_result_sync(self, file_path: str, result: dict) -> None:
        """
        Write result file synchronously.

        Args:
            file_path: Path to result file.
            result: Result data.
        """
        import json

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    async def get_result(self, task_id: str) -> Optional[dict]:
        """
        Get classification result by task ID.

        Args:
            task_id: Task identifier.

        Returns:
            Optional[dict]: Classification result or None if not found.
        """
        try:
            result_file = os.path.join(self.results_dir, f"{task_id}.json")

            if not os.path.exists(result_file):
                return None

            # Read result file asynchronously
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._read_result_sync(result_file)
            )

        except Exception as e:
            logger.error(f"Error reading result {task_id}: {e}")
            return None

    def _read_result_sync(self, file_path: str) -> dict:
        """
        Read result file synchronously.

        Args:
            file_path: Path to result file.

        Returns:
            dict: Result data.
        """
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
