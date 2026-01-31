"""Custom exceptions for pyWATS.

This module defines all exception types used throughout the pyWATS library.
Each exception includes troubleshooting hints to help users resolve issues.
"""
from typing import Optional, Dict, Any, List


# =============================================================================
# Troubleshooting Hints
# =============================================================================

TROUBLESHOOTING_HINTS: Dict[str, List[str]] = {
    "connection": [
        "Verify the server URL is correct (check for typos)",
        "Test connectivity: curl {url}/api/version",
        "Check if a proxy is required: set HTTP_PROXY/HTTPS_PROXY",
        "Verify firewall allows outbound HTTPS (port 443)",
        "Check if the server is reachable from this network",
    ],
    "authentication": [
        "Verify the API token is correct and not expired",
        "Ensure the token is base64-encoded (format: username:token)",
        "Check if the user account is active in WATS",
        "Verify the user has API access permissions",
        "Try regenerating the API token in WATS settings",
    ],
    "timeout": [
        "Increase timeout: pyWATS(timeout=60.0)",
        "Check network latency to the server",
        "Large responses may need longer timeouts",
        "Consider using async API for long operations",
        "Check if server is under heavy load",
    ],
    "server_error": [
        "Check WATS server logs for details",
        "Verify WATS server version is 2025.3.9.824 or later",
        "The server may be overloaded or restarting",
        "Contact WATS support if issue persists",
    ],
    "not_found": [
        "Verify the resource ID or identifier is correct",
        "Check if the resource exists in WATS",
        "Ensure you have permission to access this resource",
        "The resource may have been deleted",
    ],
    "validation": [
        "Check the field value matches expected format",
        "Review API documentation for valid values",
        "Some fields have character limits or patterns",
        "Dates should be in ISO 8601 format",
    ],
    "configuration": [
        "Check config file syntax (valid JSON)",
        "Verify all required fields are present",
        "Environment variables override config file",
        "Run: pywats-client diagnose for full check",
    ],
    "service": [
        "Check service status: systemctl status pywats-client",
        "View logs: journalctl -u pywats-client -f",
        "Verify permissions on config and data directories",
        "On RHEL: check SELinux with: ausearch -m AVC -ts recent",
    ],
}


def get_troubleshooting_hints(error_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Get formatted troubleshooting hints for an error type.
    
    Args:
        error_type: Type of error (connection, authentication, etc.)
        context: Optional context to customize hints (e.g., URL)
        
    Returns:
        Formatted troubleshooting hints string
    """
    hints = TROUBLESHOOTING_HINTS.get(error_type, [])
    if not hints:
        return ""
    
    # Replace placeholders with context values
    if context:
        hints = [hint.format(**context) if '{' in hint else hint for hint in hints]
    
    lines = ["\nPossible causes and solutions:"]
    for i, hint in enumerate(hints, 1):
        lines.append(f"  {i}. {hint}")
    lines.append("\nFor detailed diagnostics, run: pywats-client diagnose")
    
    return "\n".join(lines)


# =============================================================================
# Base Exception
# =============================================================================

class PyWATSError(Exception):
    """Base exception for all pyWATS errors."""
    
    # Override in subclasses
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
            parts.append(f"Details: {self.details}")
        
        if self._hints:
            parts.append(self._hints)
        
        return "\n".join(parts)
    
    @property
    def short_message(self) -> str:
        """Get the error message without hints"""
        return self.message


# =============================================================================
# Specific Exceptions
# =============================================================================

class AuthenticationError(PyWATSError):
    """Raised when authentication fails."""
    
    error_type = "authentication"
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message,
            details or {},
            show_hints=True
        )


class NotFoundError(PyWATSError):
    """Raised when a requested resource is not found."""
    
    error_type = "not_found"
    
    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None
    ) -> None:
        self.resource_type = resource_type
        self.identifier = identifier
        msg = message or f"{resource_type} '{identifier}' not found"
        super().__init__(
            msg,
            {"resource_type": resource_type, "identifier": identifier}
        )


class ValidationError(PyWATSError):
    """Raised when data validation fails."""
    
    error_type = "validation"
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ) -> None:
        self.field = field
        self.value = value
        details: Dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate long values
        super().__init__(message, details)


class ServerError(PyWATSError):
    """Raised when the server returns an error."""
    
    error_type = "server_error"
    
    def __init__(
        self,
        status_code: int,
        message: str,
        response_body: Optional[str] = None
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        
        # Provide specific guidance based on status code
        status_hints = {
            500: "Internal server error - check WATS server logs",
            502: "Bad gateway - server may be restarting",
            503: "Service unavailable - server overloaded or maintenance",
            504: "Gateway timeout - request took too long",
        }
        
        hint = status_hints.get(status_code, "")
        full_message = f"Server error ({status_code}): {message}"
        if hint:
            full_message += f" - {hint}"
        
        super().__init__(
            full_message,
            {"status_code": status_code, "response_body": response_body[:500] if response_body else None}
        )


class ConnectionError(PyWATSError):
    """Raised when connection to the server fails."""
    
    error_type = "connection"
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None
    ) -> None:
        details = {}
        if url:
            details["url"] = url
        super().__init__(message, details)


class TimeoutError(PyWATSError):
    """Raised when a request times out."""
    
    error_type = "timeout"
    
    def __init__(
        self,
        message: str = "Request timed out",
        timeout: Optional[float] = None,
        endpoint: Optional[str] = None
    ) -> None:
        details = {}
        if timeout:
            details["timeout_seconds"] = timeout
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(message, details)


class ConfigurationError(PyWATSError):
    """Raised when configuration is invalid."""
    
    error_type = "configuration"
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        missing_field: Optional[str] = None
    ) -> None:
        details = {}
        if config_file:
            details["config_file"] = config_file
        if missing_field:
            details["missing_field"] = missing_field
        super().__init__(message, details)


class ServiceError(PyWATSError):
    """Raised when service operation fails."""
    
    error_type = "service"
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None
    ) -> None:
        details = {}
        if service_name:
            details["service_name"] = service_name
        if operation:
            details["operation"] = operation
        super().__init__(message, details)

