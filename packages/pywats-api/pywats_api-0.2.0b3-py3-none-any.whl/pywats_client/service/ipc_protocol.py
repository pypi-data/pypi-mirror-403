"""
IPC Protocol Definition

Defines the protocol version, message types, and schemas for
communication between the pyWATS service and GUI/clients.

Protocol Version History:
- 1.0: Initial implicit version (pre-versioning)
- 2.0: Explicit versioning, authentication, rate limiting
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import json


# =============================================================================
# Protocol Version
# =============================================================================

PROTOCOL_VERSION = "2.0"
PROTOCOL_VERSION_MAJOR = 2
PROTOCOL_VERSION_MINOR = 0

# Minimum supported client version (for server compatibility checking)
MIN_CLIENT_VERSION = "2.0"

# Minimum supported server version (for client compatibility checking)
MIN_SERVER_VERSION = "2.0"


def parse_version(version_str: str) -> tuple[int, int]:
    """Parse version string into (major, minor) tuple."""
    try:
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return (major, minor)
    except (ValueError, IndexError):
        return (0, 0)


def is_version_compatible(version: str, min_version: str) -> bool:
    """
    Check if a version is compatible with minimum required version.
    
    Args:
        version: Version to check
        min_version: Minimum required version
        
    Returns:
        True if version >= min_version
    """
    v_major, v_minor = parse_version(version)
    min_major, min_minor = parse_version(min_version)
    
    if v_major > min_major:
        return True
    if v_major < min_major:
        return False
    return v_minor >= min_minor


# =============================================================================
# Message Types
# =============================================================================

class MessageType(str, Enum):
    """IPC message types"""
    # Connection management
    HELLO = "hello"           # Initial handshake from server
    CONNECT = "connect"       # Client connection request
    DISCONNECT = "disconnect" # Client disconnect notification
    
    # Authentication
    AUTH = "auth"             # Authentication request
    AUTH_RESPONSE = "auth_response"  # Authentication result
    
    # Service commands
    PING = "ping"             # Connection test
    GET_STATUS = "get_status" # Get service status
    GET_CONFIG = "get_config" # Get configuration
    SET_CONFIG = "set_config" # Update configuration
    
    # Queue operations
    GET_QUEUE = "get_queue"   # Get queue status
    CLEAR_QUEUE = "clear_queue"  # Clear queue
    
    # Converter operations
    GET_CONVERTERS = "get_converters"  # List converters
    START_CONVERTER = "start_converter"  # Start a converter
    STOP_CONVERTER = "stop_converter"    # Stop a converter
    
    # Service control
    START_SERVICE = "start_service"  # Start the service
    STOP_SERVICE = "stop_service"    # Stop the service
    RESTART_SERVICE = "restart_service"  # Restart service
    
    # Sync operations
    SYNC_NOW = "sync_now"     # Trigger immediate sync
    
    # Error
    ERROR = "error"           # Error response


# =============================================================================
# Message Schemas
# =============================================================================

@dataclass
class IPCMessage:
    """Base IPC message structure"""
    command: str
    request_id: str = ""
    protocol_version: str = PROTOCOL_VERSION
    args: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPCMessage":
        return cls(
            command=data.get("command", ""),
            request_id=data.get("request_id", ""),
            protocol_version=data.get("protocol_version", "1.0"),
            args=data.get("args", {})
        )
    
    @classmethod
    def from_json(cls, data: str) -> "IPCMessage":
        return cls.from_dict(json.loads(data))


@dataclass
class IPCResponse:
    """IPC response structure"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: str = ""
    protocol_version: str = PROTOCOL_VERSION
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPCResponse":
        return cls(
            success=data.get("success", False),
            data=data.get("data"),
            error=data.get("error"),
            request_id=data.get("request_id", ""),
            protocol_version=data.get("protocol_version", "1.0")
        )
    
    @classmethod
    def success_response(
        cls,
        data: Any = None,
        request_id: str = ""
    ) -> "IPCResponse":
        """Create a success response"""
        return cls(
            success=True,
            data=data,
            error=None,
            request_id=request_id
        )
    
    @classmethod
    def error_response(
        cls,
        error: str,
        request_id: str = ""
    ) -> "IPCResponse":
        """Create an error response"""
        return cls(
            success=False,
            data=None,
            error=error,
            request_id=request_id
        )


@dataclass
class HelloMessage:
    """
    Server hello message sent on connection.
    
    Contains server capabilities and version information.
    """
    protocol_version: str = PROTOCOL_VERSION
    server_version: str = ""  # pyWATS version
    instance_id: str = ""
    requires_auth: bool = False
    capabilities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HelloMessage":
        return cls(
            protocol_version=data.get("protocol_version", "1.0"),
            server_version=data.get("server_version", ""),
            instance_id=data.get("instance_id", ""),
            requires_auth=data.get("requires_auth", False),
            capabilities=data.get("capabilities", [])
        )


@dataclass
class ConnectMessage:
    """Client connect message"""
    protocol_version: str = PROTOCOL_VERSION
    client_version: str = ""  # Client app version
    client_type: str = "gui"  # "gui", "cli", "test"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VersionMismatchError(Exception):
    """Raised when protocol versions are incompatible"""
    client_version: str
    server_version: str
    message: str = ""
    
    def __post_init__(self):
        if not self.message:
            self.message = (
                f"Protocol version mismatch: client={self.client_version}, "
                f"server={self.server_version}. Minimum supported: {MIN_SERVER_VERSION}"
            )
        super().__init__(self.message)


# =============================================================================
# Protocol Constants
# =============================================================================

# Message size limits
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
MAX_HEADER_SIZE = 4  # 4 bytes for length prefix

# Timeout defaults (seconds)
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_REQUEST_TIMEOUT = 30.0
DEFAULT_AUTH_TIMEOUT = 10.0

# Rate limiting defaults
DEFAULT_REQUESTS_PER_MINUTE = 100
DEFAULT_BURST_SIZE = 20


# =============================================================================
# Capability Flags
# =============================================================================

class ServerCapability(str, Enum):
    """Server capability flags advertised in hello message"""
    AUTH = "auth"                 # Authentication supported
    RATE_LIMIT = "rate_limit"    # Rate limiting enabled
    CONVERTERS = "converters"    # Converter management
    QUEUE = "queue"              # Queue management
    CONFIG = "config"            # Config management
    SYNC = "sync"                # Sync operations
    SANDBOX = "sandbox"          # Converter sandboxing


# =============================================================================
# Helper Functions
# =============================================================================

def create_request(
    command: str,
    args: Optional[Dict[str, Any]] = None,
    request_id: str = ""
) -> IPCMessage:
    """
    Create an IPC request message.
    
    Args:
        command: Command name
        args: Optional command arguments
        request_id: Optional request ID for tracking
        
    Returns:
        IPCMessage ready to send
    """
    return IPCMessage(
        command=command,
        args=args or {},
        request_id=request_id
    )


def create_hello(
    instance_id: str,
    server_version: str,
    requires_auth: bool,
    capabilities: Optional[List[str]] = None
) -> HelloMessage:
    """
    Create a server hello message.
    
    Args:
        instance_id: Server instance ID
        server_version: pyWATS version string
        requires_auth: Whether authentication is required
        capabilities: List of server capabilities
        
    Returns:
        HelloMessage ready to send
    """
    return HelloMessage(
        instance_id=instance_id,
        server_version=server_version,
        requires_auth=requires_auth,
        capabilities=capabilities or []
    )


def check_version_compatibility(
    client_version: str,
    server_version: str
) -> tuple[bool, str]:
    """
    Check if client and server versions are compatible.
    
    Args:
        client_version: Client protocol version
        server_version: Server protocol version
        
    Returns:
        Tuple of (is_compatible, error_message)
    """
    # Check if client meets server's minimum requirement
    if not is_version_compatible(client_version, MIN_CLIENT_VERSION):
        return (
            False,
            f"Client version {client_version} is too old. "
            f"Minimum required: {MIN_CLIENT_VERSION}"
        )
    
    # Check if server meets client's minimum requirement
    if not is_version_compatible(server_version, MIN_SERVER_VERSION):
        return (
            False,
            f"Server version {server_version} is too old. "
            f"Minimum required: {MIN_SERVER_VERSION}"
        )
    
    return (True, "")
