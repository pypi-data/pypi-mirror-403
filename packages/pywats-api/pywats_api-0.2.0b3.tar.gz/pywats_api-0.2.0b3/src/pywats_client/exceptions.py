"""
Custom Exceptions for pyWATS Client

This module defines exception types specific to the pyWATS Client application,
including converter errors, queue errors, service errors, and configuration errors.

Each exception includes troubleshooting hints to help users resolve issues.

Usage:
    from pywats_client.exceptions import (
        ConverterError,
        FileFormatError,
        QueueError,
        ServiceInstallError,
    )
    
    # Raise with context for helpful error messages
    raise ConverterError(
        "Failed to parse CSV file",
        converter_name="CSVConverter",
        file_path="/path/to/file.csv"
    )
"""

from typing import Optional, Dict, Any, List
from pathlib import Path


# =============================================================================
# Troubleshooting Hints
# =============================================================================

TROUBLESHOOTING_HINTS: Dict[str, List[str]] = {
    "converter": [
        "Check the file format matches the converter's expected format",
        "Verify the file is not corrupted (try opening it manually)",
        "Check converter configuration in the GUI or config file",
        "Review the converter log for detailed error messages",
        "Try a different converter if multiple are available",
    ],
    "file_format": [
        "Verify the file extension matches the content type",
        "Check for encoding issues (UTF-8 vs UTF-16 vs ANSI)",
        "Ensure required columns/fields are present",
        "Look for special characters that might cause parsing issues",
        "Try opening the file in a text editor to inspect content",
    ],
    "file_access": [
        "Check file permissions (read access required)",
        "Ensure the file is not open in another application",
        "Verify the path is correct and the file exists",
        "Check if antivirus is blocking file access",
        "On network drives, verify connectivity",
    ],
    "queue": [
        "Check available disk space in the queue directory",
        "Verify write permissions on the queue folder",
        "Review queue statistics: pywats-client status",
        "Clear stuck items: move .processing files back to .pending",
        "Check for file system errors with disk diagnostics",
    ],
    "queue_full": [
        "Process pending items before adding more",
        "Increase max_queue_size in configuration",
        "Check if the upload service is running",
        "Verify network connectivity to WATS server",
        "Consider enabling auto-cleanup of completed items",
    ],
    "queue_corrupted": [
        "Backup the queue directory before recovery",
        "Run: pywats-client queue repair",
        "Remove corrupted .wsjf files and retry",
        "Check for disk errors that may have caused corruption",
        "Consider clearing the queue and re-importing files",
    ],
    "offline": [
        "Check network connectivity to WATS server",
        "Verify server URL in configuration",
        "Reports are queued locally and will upload when online",
        "Run: pywats-client status to see queue status",
        "Test connection: pywats-client test-connection",
    ],
    "service_install": [
        "Run with administrator/root privileges",
        "Check if a previous installation exists",
        "On Windows: verify pywin32 is installed (pip install pywin32)",
        "On Linux: check systemd status (systemctl status pywats-client)",
        "Review system logs for installation errors",
    ],
    "service_start": [
        "Check service status: pywats-client status",
        "Verify configuration file is valid JSON",
        "Check if another instance is already running",
        "Review logs: pywats-client logs",
        "On Linux with SELinux: check for AVC denials",
    ],
    "service_permission": [
        "On Windows: run as Administrator",
        "On Linux: use sudo or run as service user",
        "Check file permissions on config and data directories",
        "Verify the service account has network access",
        "On SELinux: install the pywats policy module",
    ],
    "config_file": [
        "Verify the config file is valid JSON (use a JSON validator)",
        "Check for missing required fields",
        "Ensure file path is correct",
        "Look for typos in configuration keys",
        "Try creating a fresh config: pywats-client config init",
    ],
    "config_missing": [
        "Run: pywats-client config init to create default config",
        "Check the expected config location: ~/.pywats_client/config.json",
        "Set custom path with: --config /path/to/config.json",
        "Environment variables can override config file settings",
        "Copy a template config from documentation",
    ],
}


def get_troubleshooting_hints(error_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Get formatted troubleshooting hints for an error type.
    
    Args:
        error_type: Type of error (converter, queue, service_install, etc.)
        context: Optional context to customize hints
        
    Returns:
        Formatted troubleshooting hints string
    """
    hints = TROUBLESHOOTING_HINTS.get(error_type, [])
    if not hints:
        return ""
    
    # Replace placeholders with context values
    if context:
        formatted_hints = []
        for hint in hints:
            try:
                formatted_hints.append(hint.format(**context))
            except KeyError:
                formatted_hints.append(hint)
        hints = formatted_hints
    
    lines = ["\nPossible causes and solutions:"]
    for i, hint in enumerate(hints, 1):
        lines.append(f"  {i}. {hint}")
    lines.append("\nFor detailed diagnostics, run: pywats-client diagnose")
    
    return "\n".join(lines)


# =============================================================================
# Base Exception
# =============================================================================

class ClientError(Exception):
    """Base exception for all pyWATS Client errors."""
    
    error_type: str = "general"
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        show_hints: bool = True
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.show_hints = show_hints
        self._hints: Optional[str] = None
        
        if show_hints:
            self._hints = get_troubleshooting_hints(self.error_type, self.details)
    
    def __str__(self) -> str:
        parts = [self.message]
        
        if self.details:
            # Format details nicely
            detail_items = [f"{k}={v}" for k, v in self.details.items() if v is not None]
            if detail_items:
                parts.append(f"[{', '.join(detail_items)}]")
        
        if self._hints:
            parts.append(self._hints)
        
        return "\n".join(parts)
    
    @property
    def short_message(self) -> str:
        """Get the error message without hints"""
        return self.message


# =============================================================================
# Converter Exceptions
# =============================================================================

class ConverterError(ClientError):
    """
    Raised when a converter fails to process a file.
    
    This is the general converter error. For more specific errors,
    use FileFormatError, FileAccessError, or ConverterConfigError.
    """
    
    error_type = "converter"
    
    def __init__(
        self,
        message: str,
        converter_name: Optional[str] = None,
        file_path: Optional[str] = None,
        cause: Optional[Exception] = None
    ) -> None:
        self.converter_name = converter_name
        self.file_path = file_path
        self.cause = cause
        
        details = {}
        if converter_name:
            details["converter"] = converter_name
        if file_path:
            details["file"] = str(file_path)
        if cause:
            details["cause"] = str(cause)
        
        super().__init__(message, details)


class FileFormatError(ClientError):
    """
    Raised when a file has an invalid or unexpected format.
    
    Common causes:
    - Wrong file extension for content
    - Encoding issues (UTF-8 vs ANSI)
    - Missing required columns/fields
    - Corrupted file content
    """
    
    error_type = "file_format"
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        expected_format: Optional[str] = None,
        actual_format: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> None:
        self.file_path = file_path
        self.expected_format = expected_format
        self.actual_format = actual_format
        self.line_number = line_number
        
        details = {}
        if file_path:
            details["file"] = str(file_path)
        if expected_format:
            details["expected"] = expected_format
        if actual_format:
            details["actual"] = actual_format
        if line_number:
            details["line"] = line_number
        
        super().__init__(message, details)


class FileAccessError(ClientError):
    """
    Raised when a file cannot be accessed.
    
    Common causes:
    - File doesn't exist
    - Insufficient permissions
    - File is locked by another process
    - Network drive disconnected
    """
    
    error_type = "file_access"
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None
    ) -> None:
        self.file_path = file_path
        self.operation = operation
        
        details = {}
        if file_path:
            details["file"] = str(file_path)
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)


class ConverterConfigError(ClientError):
    """
    Raised when converter configuration is invalid.
    """
    
    error_type = "config_file"
    
    def __init__(
        self,
        message: str,
        converter_name: Optional[str] = None,
        setting: Optional[str] = None,
        value: Optional[Any] = None
    ) -> None:
        self.converter_name = converter_name
        self.setting = setting
        self.value = value
        
        details = {}
        if converter_name:
            details["converter"] = converter_name
        if setting:
            details["setting"] = setting
        if value is not None:
            details["value"] = str(value)[:100]
        
        super().__init__(message, details)


# =============================================================================
# Queue Exceptions
# =============================================================================

class QueueError(ClientError):
    """
    Raised when a queue operation fails.
    
    This is the general queue error. For more specific errors,
    use QueueFullError, QueueCorruptedError, or OfflineError.
    """
    
    error_type = "queue"
    
    def __init__(
        self,
        message: str,
        queue_path: Optional[str] = None,
        item_id: Optional[str] = None,
        operation: Optional[str] = None
    ) -> None:
        self.queue_path = queue_path
        self.item_id = item_id
        self.operation = operation
        
        details = {}
        if queue_path:
            details["queue_path"] = str(queue_path)
        if item_id:
            details["item_id"] = item_id
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)


class QueueFullError(ClientError):
    """
    Raised when the queue has reached its maximum capacity.
    
    Solutions:
    - Wait for pending items to be processed
    - Increase queue size limit
    - Check if upload service is running
    """
    
    error_type = "queue_full"
    
    def __init__(
        self,
        message: str = "Queue is full",
        current_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> None:
        self.current_size = current_size
        self.max_size = max_size
        
        details = {}
        if current_size is not None:
            details["current_size"] = current_size
        if max_size is not None:
            details["max_size"] = max_size
        
        super().__init__(message, details)


class QueueCorruptedError(ClientError):
    """
    Raised when queue data is corrupted.
    
    This can happen due to:
    - Disk errors
    - Process crash during write
    - Manual file editing
    """
    
    error_type = "queue_corrupted"
    
    def __init__(
        self,
        message: str,
        queue_path: Optional[str] = None,
        corrupted_file: Optional[str] = None
    ) -> None:
        self.queue_path = queue_path
        self.corrupted_file = corrupted_file
        
        details = {}
        if queue_path:
            details["queue_path"] = str(queue_path)
        if corrupted_file:
            details["corrupted_file"] = str(corrupted_file)
        
        super().__init__(message, details)


class OfflineError(ClientError):
    """
    Raised when an operation requires connectivity but the system is offline.
    
    Note: Most operations will queue locally when offline.
    This error is only raised for operations that require immediate connectivity.
    """
    
    error_type = "offline"
    
    def __init__(
        self,
        message: str = "Operation requires network connectivity",
        server_url: Optional[str] = None,
        queued: bool = False
    ) -> None:
        self.server_url = server_url
        self.queued = queued
        
        details = {}
        if server_url:
            details["server_url"] = server_url
        if queued:
            details["queued"] = "yes (will retry when online)"
        
        super().__init__(message, details)


# =============================================================================
# Service Exceptions
# =============================================================================

class ServiceInstallError(ClientError):
    """
    Raised when service installation fails.
    
    Common causes:
    - Insufficient privileges (not admin/root)
    - Missing dependencies (pywin32 on Windows)
    - Previous installation not fully removed
    """
    
    error_type = "service_install"
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        platform: Optional[str] = None,
        cause: Optional[Exception] = None
    ) -> None:
        self.service_name = service_name
        self.platform = platform
        self.cause = cause
        
        details = {}
        if service_name:
            details["service"] = service_name
        if platform:
            details["platform"] = platform
        if cause:
            details["cause"] = str(cause)
        
        super().__init__(message, details)


class ServiceStartError(ClientError):
    """
    Raised when the service fails to start.
    
    Common causes:
    - Configuration error
    - Another instance already running
    - Port already in use
    - Insufficient permissions
    """
    
    error_type = "service_start"
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        self.service_name = service_name
        self.reason = reason
        
        details = {}
        if service_name:
            details["service"] = service_name
        if reason:
            details["reason"] = reason
        
        super().__init__(message, details)


class ServicePermissionError(ClientError):
    """
    Raised when a service operation requires elevated privileges.
    """
    
    error_type = "service_permission"
    
    def __init__(
        self,
        message: str = "This operation requires administrator privileges",
        operation: Optional[str] = None
    ) -> None:
        self.operation = operation
        
        details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigurationError(ClientError):
    """
    Raised when configuration is invalid.
    """
    
    error_type = "config_file"
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        key: Optional[str] = None,
        value: Optional[Any] = None
    ) -> None:
        self.config_file = config_file
        self.key = key
        self.value = value
        
        details = {}
        if config_file:
            details["config_file"] = str(config_file)
        if key:
            details["key"] = key
        if value is not None:
            details["value"] = str(value)[:100]
        
        super().__init__(message, details)


class ConfigurationMissingError(ClientError):
    """
    Raised when required configuration file is missing.
    """
    
    error_type = "config_missing"
    
    def __init__(
        self,
        message: str = "Configuration file not found",
        config_file: Optional[str] = None,
        expected_location: Optional[str] = None
    ) -> None:
        self.config_file = config_file
        self.expected_location = expected_location
        
        details = {}
        if config_file:
            details["config_file"] = str(config_file)
        if expected_location:
            details["expected_location"] = str(expected_location)
        
        super().__init__(message, details)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Base
    "ClientError",
    # Converter
    "ConverterError",
    "FileFormatError",
    "FileAccessError",
    "ConverterConfigError",
    # Queue
    "QueueError",
    "QueueFullError",
    "QueueCorruptedError",
    "OfflineError",
    # Service
    "ServiceInstallError",
    "ServiceStartError",
    "ServicePermissionError",
    # Configuration
    "ConfigurationError",
    "ConfigurationMissingError",
]
