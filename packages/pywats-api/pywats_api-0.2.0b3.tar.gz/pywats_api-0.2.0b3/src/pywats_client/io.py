"""
File I/O Utilities for pyWATS Client

Provides file operations for attachments and reports.
All file I/O in pyWATS belongs in pywats_client, not in pywats (API layer).

Design Principle:
    The pywats API (pywats/) is memory-only with NO file operations.
    All file persistence and I/O belongs in pywats_client.
"""

import base64
import mimetypes
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
from dataclasses import dataclass

from pywats.domains.report import Attachment

from .core.file_utils import SafeFileWriter, SafeFileReader

logger = logging.getLogger(__name__)


# Default max attachment size (10 MB)
DEFAULT_MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


@dataclass
class FileInfo:
    """Information about a loaded file."""
    content: bytes
    name: str
    mime_type: str
    size: int


class AttachmentIO:
    """
    File I/O operations for attachments.
    
    This class provides methods to load attachments from files and save
    attachments to files. It bridges the gap between the memory-only
    pywats.Attachment model and the filesystem.
    
    Example:
        >>> from pywats_client.io import AttachmentIO
        >>> 
        >>> # Load from file
        >>> attachment = AttachmentIO.from_file("report.pdf")
        >>> 
        >>> # Load with custom name
        >>> attachment = AttachmentIO.from_file("temp.dat", name="results.bin")
        >>> 
        >>> # Save to file
        >>> AttachmentIO.save(attachment, "output.pdf")
        >>> 
        >>> # Read file info without creating attachment
        >>> info = AttachmentIO.read_file("report.pdf")
        >>> print(f"File: {info.name}, Size: {info.size}, Type: {info.mime_type}")
    """
    
    @staticmethod
    def from_file(
        file_path: Union[str, Path],
        name: Optional[str] = None,
        content_type: Optional[str] = None,
        failure_idx: Optional[int] = None,
        max_size: Optional[int] = None,
        delete_after: bool = False
    ) -> Attachment:
        """
        Create an Attachment from a file.
        
        Args:
            file_path: Path to the file
            name: Custom name (defaults to filename)
            content_type: MIME type (auto-detected if not provided)
            failure_idx: Failure index for UUR attachments (None = report level)
            max_size: Maximum file size in bytes (default: 10 MB)
            delete_after: Delete the file after reading
            
        Returns:
            Attachment instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file exceeds max size
            
        Example:
            >>> attachment = AttachmentIO.from_file("screenshot.png")
            >>> attachment = AttachmentIO.from_file("data.bin", content_type="application/octet-stream")
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check size
        file_size = path.stat().st_size
        max_allowed = max_size or DEFAULT_MAX_ATTACHMENT_SIZE
        if file_size > max_allowed:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum ({max_allowed} bytes)"
            )
        
        # Read content
        content = path.read_bytes()
        
        # Auto-detect MIME type
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"
        
        # Use filename if name not provided
        if not name:
            name = path.name
        
        # Delete if requested
        if delete_after:
            try:
                path.unlink()
                logger.debug(f"Deleted source file: {path}")
            except OSError as e:
                logger.warning(f"Failed to delete source file {path}: {e}")
        
        return Attachment.from_bytes(
            name=name,
            content=content,
            content_type=content_type,
            failure_idx=failure_idx,
            max_size=max_size
        )
    
    @staticmethod
    def read_file(
        file_path: Union[str, Path],
        max_size: Optional[int] = None
    ) -> FileInfo:
        """
        Read a file and return its info without creating an Attachment.
        
        Useful when you need the raw content, name, and MIME type separately.
        
        Args:
            file_path: Path to the file
            max_size: Maximum file size in bytes (default: 10 MB)
            
        Returns:
            FileInfo with content, name, mime_type, and size
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file exceeds max size
            
        Example:
            >>> info = AttachmentIO.read_file("report.pdf")
            >>> report.attach_bytes(info.name, info.content, info.mime_type)
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check size
        file_size = path.stat().st_size
        max_allowed = max_size or DEFAULT_MAX_ATTACHMENT_SIZE
        if file_size > max_allowed:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum ({max_allowed} bytes)"
            )
        
        # Read content
        content = path.read_bytes()
        
        # Auto-detect MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        mime_type = mime_type or "application/octet-stream"
        
        return FileInfo(
            content=content,
            name=path.name,
            mime_type=mime_type,
            size=file_size
        )
    
    @staticmethod
    def save(
        attachment: Attachment,
        file_path: Union[str, Path],
        overwrite: bool = False,
        atomic: bool = True
    ) -> Path:
        """
        Save an Attachment to a file.
        
        Args:
            attachment: Attachment to save
            file_path: Destination file path
            overwrite: Allow overwriting existing files (default: False)
            atomic: Use atomic write (write to temp, then rename)
            
        Returns:
            Path to the saved file
            
        Raises:
            FileExistsError: If file exists and overwrite=False
            ValueError: If attachment has no data
            
        Example:
            >>> AttachmentIO.save(attachment, "output.pdf")
            >>> AttachmentIO.save(attachment, "output.pdf", overwrite=True)
        """
        path = Path(file_path)
        
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {file_path}")
        
        # Get binary content
        content = attachment.get_bytes()
        if not content:
            raise ValueError("Attachment has no data")
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if atomic:
            # Use atomic write from file_utils
            result = SafeFileWriter.write_bytes_atomic(path, content)
            if not result.success:
                raise IOError(f"Failed to save attachment: {result.error}")
        else:
            # Direct write
            path.write_bytes(content)
        
        logger.debug(f"Saved attachment '{attachment.name}' to {path}")
        return path
    
    @staticmethod
    def save_multiple(
        attachments: list[Attachment],
        directory: Union[str, Path],
        overwrite: bool = False
    ) -> list[Path]:
        """
        Save multiple attachments to a directory.
        
        Args:
            attachments: List of Attachments to save
            directory: Destination directory
            overwrite: Allow overwriting existing files
            
        Returns:
            List of paths to saved files
            
        Example:
            >>> paths = AttachmentIO.save_multiple(report.attachments, "output/")
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for attachment in attachments:
            file_path = dir_path / attachment.name
            path = AttachmentIO.save(attachment, file_path, overwrite=overwrite)
            saved_paths.append(path)
        
        return saved_paths


# Convenience functions
def load_attachment(file_path: Union[str, Path], **kwargs) -> Attachment:
    """
    Load an attachment from a file.
    
    Convenience function for AttachmentIO.from_file().
    
    Args:
        file_path: Path to the file
        **kwargs: Additional arguments passed to AttachmentIO.from_file()
        
    Returns:
        Attachment instance
    """
    return AttachmentIO.from_file(file_path, **kwargs)


def save_attachment(attachment: Attachment, file_path: Union[str, Path], **kwargs) -> Path:
    """
    Save an attachment to a file.
    
    Convenience function for AttachmentIO.save().
    
    Args:
        attachment: Attachment to save
        file_path: Destination file path
        **kwargs: Additional arguments passed to AttachmentIO.save()
        
    Returns:
        Path to the saved file
    """
    return AttachmentIO.save(attachment, file_path, **kwargs)


__all__ = [
    "AttachmentIO",
    "FileInfo",
    "load_attachment",
    "save_attachment",
    "DEFAULT_MAX_ATTACHMENT_SIZE",
]
