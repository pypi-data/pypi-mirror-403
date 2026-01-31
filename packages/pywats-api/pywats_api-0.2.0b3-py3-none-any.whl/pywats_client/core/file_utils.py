"""
Centralized File Utilities

Provides safe, atomic file operations for the pyWATS Client.
All file I/O in pywats_client should use these utilities.

Features:
- Atomic writes (write to temp, then rename)
- Safe reads with corruption recovery
- Optional file locking for multi-process safety
- Consistent error handling

Design Principle:
    The pywats API (pywats/) should be memory-only with NO file operations.
    All file persistence belongs in pywats_client and should use this module.
"""

import json
import os
import time
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar, Callable
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Platform-specific file locking
if os.name == 'nt':
    # Windows
    import msvcrt
    
    def _lock_file(f, exclusive: bool = True) -> bool:
        """Acquire file lock on Windows."""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK if exclusive else msvcrt.LK_NBRLCK, 1)
            return True
        except (IOError, OSError):
            return False
    
    def _unlock_file(f) -> None:
        """Release file lock on Windows."""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except (IOError, OSError):
            pass
else:
    # Unix/Linux/Mac
    import fcntl
    
    def _lock_file(f, exclusive: bool = True) -> bool:
        """Acquire file lock on Unix."""
        try:
            flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(f.fileno(), flags | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False
    
    def _unlock_file(f) -> None:
        """Release file lock on Unix."""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (IOError, OSError):
            pass


class FileOperation(Enum):
    """Types of file operations for logging/tracking."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    RENAME = "rename"
    COPY = "copy"


@dataclass
class FileOperationResult:
    """Result of a file operation."""
    success: bool
    path: Path
    operation: FileOperation
    error: Optional[str] = None
    backup_path: Optional[Path] = None


class SafeFileWriter:
    """
    Provides atomic file writing operations.
    
    Writes to a temporary file first, then atomically renames to the target.
    This ensures that the target file is never in a corrupted state.
    
    Example:
        >>> SafeFileWriter.write_text_atomic(Path("config.json"), '{"key": "value"}')
        >>> SafeFileWriter.write_json_atomic(Path("data.json"), {"key": "value"})
    """
    
    @staticmethod
    def write_text_atomic(
        path: Path,
        content: str,
        encoding: str = 'utf-8',
        backup: bool = False,
    ) -> FileOperationResult:
        """
        Write text to file atomically.
        
        Args:
            path: Target file path
            content: Text content to write
            encoding: File encoding (default: utf-8)
            backup: Create .bak backup before overwriting
            
        Returns:
            FileOperationResult with success status
        """
        path = Path(path)
        temp_path = None
        backup_path = None
        
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file in same directory (for atomic rename)
            fd, temp_path_str = tempfile.mkstemp(
                suffix='.tmp',
                prefix=path.stem + '_',
                dir=path.parent
            )
            temp_path = Path(temp_path_str)
            
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is on disk
            
            # Create backup if requested and file exists
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.bak')
                if backup_path.exists():
                    backup_path.unlink()
                path.rename(backup_path)
            
            # Atomic rename (atomic on POSIX, nearly atomic on Windows)
            temp_path.replace(path)
            
            logger.debug(f"Atomically wrote {len(content)} bytes to {path}")
            return FileOperationResult(
                success=True,
                path=path,
                operation=FileOperation.WRITE,
                backup_path=backup_path
            )
            
        except Exception as ex:
            # Cleanup temp file on failure
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            
            # Restore from backup if we created one
            if backup_path and backup_path.exists() and not path.exists():
                try:
                    backup_path.rename(path)
                except:
                    pass
            
            logger.error(f"Failed to write {path}: {ex}")
            return FileOperationResult(
                success=False,
                path=path,
                operation=FileOperation.WRITE,
                error=str(ex)
            )
    
    @staticmethod
    def write_json_atomic(
        path: Path,
        data: Dict[str, Any],
        indent: int = 2,
        backup: bool = False,
    ) -> FileOperationResult:
        """
        Write JSON data to file atomically.
        
        Args:
            path: Target file path
            data: Dictionary to serialize as JSON
            indent: JSON indentation (default: 2)
            backup: Create .bak backup before overwriting
            
        Returns:
            FileOperationResult with success status
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return SafeFileWriter.write_text_atomic(path, content, backup=backup)
        except (TypeError, ValueError) as ex:
            logger.error(f"Failed to serialize JSON for {path}: {ex}")
            return FileOperationResult(
                success=False,
                path=Path(path),
                operation=FileOperation.WRITE,
                error=f"JSON serialization error: {ex}"
            )
    
    @staticmethod
    def write_bytes_atomic(
        path: Path,
        content: bytes,
        backup: bool = False,
    ) -> FileOperationResult:
        """
        Write bytes to file atomically.
        
        Args:
            path: Target file path
            content: Bytes content to write
            backup: Create .bak backup before overwriting
            
        Returns:
            FileOperationResult with success status
        """
        path = Path(path)
        temp_path = None
        backup_path = None
        
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file
            fd, temp_path_str = tempfile.mkstemp(
                suffix='.tmp',
                prefix=path.stem + '_',
                dir=path.parent
            )
            temp_path = Path(temp_path_str)
            
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            
            # Create backup if requested
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.bak')
                if backup_path.exists():
                    backup_path.unlink()
                path.rename(backup_path)
            
            # Atomic rename
            temp_path.replace(path)
            
            logger.debug(f"Atomically wrote {len(content)} bytes to {path}")
            return FileOperationResult(
                success=True,
                path=path,
                operation=FileOperation.WRITE,
                backup_path=backup_path
            )
            
        except Exception as ex:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            
            if backup_path and backup_path.exists() and not path.exists():
                try:
                    backup_path.rename(path)
                except:
                    pass
            
            logger.error(f"Failed to write {path}: {ex}")
            return FileOperationResult(
                success=False,
                path=path,
                operation=FileOperation.WRITE,
                error=str(ex)
            )


class SafeFileReader:
    """
    Provides safe file reading operations with recovery capabilities.
    
    Example:
        >>> text = SafeFileReader.read_text_safe(Path("config.json"))
        >>> data = SafeFileReader.read_json_safe(Path("data.json"), default={})
    """
    
    @staticmethod
    def read_text_safe(
        path: Path,
        default: Optional[str] = None,
        encoding: str = 'utf-8',
        try_backup: bool = True,
    ) -> Optional[str]:
        """
        Read text from file with fallback to backup.
        
        Args:
            path: File path to read
            default: Default value if file doesn't exist or is corrupt
            encoding: File encoding (default: utf-8)
            try_backup: Try .bak file if main file fails
            
        Returns:
            File content or default value
        """
        path = Path(path)
        
        # Try main file
        if path.exists():
            try:
                return path.read_text(encoding=encoding)
            except Exception as ex:
                logger.warning(f"Failed to read {path}: {ex}")
        
        # Try backup file
        if try_backup:
            backup_path = path.with_suffix(path.suffix + '.bak')
            if backup_path.exists():
                try:
                    logger.info(f"Recovering from backup: {backup_path}")
                    content = backup_path.read_text(encoding=encoding)
                    # Restore backup to main file
                    SafeFileWriter.write_text_atomic(path, content)
                    return content
                except Exception as ex:
                    logger.warning(f"Failed to read backup {backup_path}: {ex}")
        
        return default
    
    @staticmethod
    def read_json_safe(
        path: Path,
        default: Optional[Dict[str, Any]] = None,
        try_backup: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Read JSON from file with fallback to backup.
        
        Args:
            path: File path to read
            default: Default value if file doesn't exist or is corrupt
            try_backup: Try .bak file if main file fails
            
        Returns:
            Parsed JSON dictionary or default value
        """
        content = SafeFileReader.read_text_safe(path, default=None, try_backup=try_backup)
        
        if content is None:
            return default
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as ex:
            logger.warning(f"JSON parse error in {path}: {ex}")
            
            # Try backup if we haven't already
            if try_backup:
                backup_path = Path(path).with_suffix(Path(path).suffix + '.bak')
                if backup_path.exists():
                    try:
                        backup_content = backup_path.read_text()
                        data = json.loads(backup_content)
                        logger.info(f"Recovered JSON from backup: {backup_path}")
                        # Restore backup to main file
                        SafeFileWriter.write_text_atomic(path, backup_content)
                        return data
                    except:
                        pass
            
            return default
    
    @staticmethod
    def read_bytes_safe(
        path: Path,
        default: Optional[bytes] = None,
        try_backup: bool = True,
    ) -> Optional[bytes]:
        """
        Read bytes from file with fallback to backup.
        
        Args:
            path: File path to read
            default: Default value if file doesn't exist
            try_backup: Try .bak file if main file fails
            
        Returns:
            File content as bytes or default value
        """
        path = Path(path)
        
        if path.exists():
            try:
                return path.read_bytes()
            except Exception as ex:
                logger.warning(f"Failed to read {path}: {ex}")
        
        if try_backup:
            backup_path = path.with_suffix(path.suffix + '.bak')
            if backup_path.exists():
                try:
                    logger.info(f"Recovering from backup: {backup_path}")
                    return backup_path.read_bytes()
                except Exception as ex:
                    logger.warning(f"Failed to read backup {backup_path}: {ex}")
        
        return default


@contextmanager
def locked_file(
    path: Path,
    mode: str = 'r',
    encoding: Optional[str] = 'utf-8',
    timeout: float = 5.0,
    exclusive: bool = True,
):
    """
    Context manager for file operations with locking.
    
    Args:
        path: File path
        mode: File mode ('r', 'w', 'rb', 'wb', etc.)
        encoding: File encoding (None for binary modes)
        timeout: Lock timeout in seconds
        exclusive: Use exclusive lock (default) or shared lock
        
    Yields:
        File handle with lock held
        
    Example:
        >>> with locked_file(Path("data.json"), 'r') as f:
        ...     data = json.load(f)
    
    Raises:
        TimeoutError: If lock cannot be acquired within timeout
        FileNotFoundError: If file doesn't exist (for read modes)
    """
    path = Path(path)
    
    # Determine binary mode
    is_binary = 'b' in mode
    if is_binary:
        encoding = None
    
    # Open file
    f = open(path, mode, encoding=encoding)
    
    try:
        # Try to acquire lock with timeout
        start_time = time.time()
        while not _lock_file(f, exclusive=exclusive):
            if time.time() - start_time > timeout:
                f.close()
                raise TimeoutError(f"Could not acquire lock on {path} within {timeout}s")
            time.sleep(0.1)
        
        yield f
        
    finally:
        _unlock_file(f)
        f.close()


def safe_delete(path: Path, missing_ok: bool = True) -> FileOperationResult:
    """
    Safely delete a file.
    
    Args:
        path: File path to delete
        missing_ok: Don't raise error if file doesn't exist
        
    Returns:
        FileOperationResult with success status
    """
    path = Path(path)
    
    try:
        if path.exists():
            path.unlink()
            logger.debug(f"Deleted {path}")
        elif not missing_ok:
            return FileOperationResult(
                success=False,
                path=path,
                operation=FileOperation.DELETE,
                error="File not found"
            )
        
        return FileOperationResult(
            success=True,
            path=path,
            operation=FileOperation.DELETE
        )
        
    except Exception as ex:
        logger.error(f"Failed to delete {path}: {ex}")
        return FileOperationResult(
            success=False,
            path=path,
            operation=FileOperation.DELETE,
            error=str(ex)
        )


def safe_rename(
    src: Path,
    dst: Path,
    overwrite: bool = False,
) -> FileOperationResult:
    """
    Safely rename/move a file.
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Overwrite destination if exists
        
    Returns:
        FileOperationResult with success status
    """
    src = Path(src)
    dst = Path(dst)
    
    try:
        if not src.exists():
            return FileOperationResult(
                success=False,
                path=src,
                operation=FileOperation.RENAME,
                error="Source file not found"
            )
        
        if dst.exists() and not overwrite:
            return FileOperationResult(
                success=False,
                path=dst,
                operation=FileOperation.RENAME,
                error="Destination already exists"
            )
        
        # Ensure destination directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Use replace for atomic operation
        src.replace(dst)
        
        logger.debug(f"Renamed {src} -> {dst}")
        return FileOperationResult(
            success=True,
            path=dst,
            operation=FileOperation.RENAME
        )
        
    except Exception as ex:
        logger.error(f"Failed to rename {src} -> {dst}: {ex}")
        return FileOperationResult(
            success=False,
            path=src,
            operation=FileOperation.RENAME,
            error=str(ex)
        )


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        True if directory exists or was created
    """
    path = Path(path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as ex:
        logger.error(f"Failed to create directory {path}: {ex}")
        return False


# Convenience aliases
write_text = SafeFileWriter.write_text_atomic
write_json = SafeFileWriter.write_json_atomic
write_bytes = SafeFileWriter.write_bytes_atomic
read_text = SafeFileReader.read_text_safe
read_json = SafeFileReader.read_json_safe
read_bytes = SafeFileReader.read_bytes_safe
