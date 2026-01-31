"""
Async IPC Client (Pure Python)

Cross-platform IPC client using asyncio streams.
Works with qasync in GUI for non-blocking communication.

Platform support:
- Linux/macOS: Unix domain sockets
- Windows: TCP localhost
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List

from .async_ipc_server import get_socket_address
from ..core.security import load_secret
from .ipc_protocol import (
    PROTOCOL_VERSION,
    HelloMessage,
    is_version_compatible,
    MIN_SERVER_VERSION,
    VersionMismatchError,
)

logger = logging.getLogger(__name__)


@dataclass
class InstanceInfo:
    """Information about a discovered service instance"""
    instance_id: str
    socket_name: str
    connected: bool = False
    status: Optional[Dict[str, Any]] = None


@dataclass
class ServiceStatus:
    """Service status data from IPC"""
    status: str = "Unknown"
    api_status: str = "Unknown"
    pending_count: int = 0
    processing_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    converter_active: int = 0
    converter_pending: int = 0
    uptime_seconds: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceStatus':
        """Create from dict, handling unknown fields gracefully"""
        known_fields = {
            'status', 'api_status', 'pending_count', 'processing_count',
            'completed_count', 'failed_count', 'converter_active',
            'converter_pending', 'uptime_seconds'
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, extra=extra)


class AsyncIPCClient:
    """
    Pure asyncio IPC client for GUI<->service communication.
    
    Non-blocking async client that works with qasync in Qt GUI.
    No Qt dependency - uses standard asyncio streams.
    
    Usage:
        client = AsyncIPCClient(instance_id="default")
        
        if await client.connect():
            status = await client.get_status()
            print(status)
            await client.disconnect()
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize async IPC client.
        
        Args:
            instance_id: Instance ID to connect to
        """
        self.instance_id = instance_id
        self.socket_name = f"pyWATS_Service_{instance_id}"
        
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._authenticated = False
        self._lock = asyncio.Lock()
        
        # Get platform-specific address
        self._is_unix, self._address = get_socket_address(self.socket_name)
        
        # Protocol versioning
        self._protocol_version = PROTOCOL_VERSION
        self._server_hello: Optional[HelloMessage] = None
        self._server_capabilities: List[str] = []
    
    @property
    def connected(self) -> bool:
        """Check if connected to service"""
        return self._connected and self._writer is not None
    
    @property
    def server_version(self) -> Optional[str]:
        """Get server protocol version if connected"""
        return self._server_hello.protocol_version if self._server_hello else None
    
    @property
    def server_capabilities(self) -> List[str]:
        """Get server capabilities"""
        return self._server_capabilities
    
    async def connect(self, timeout: float = 1.0) -> bool:
        """
        Connect to service.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully
            
        Raises:
            VersionMismatchError: If server protocol version is incompatible
        """
        try:
            if self._is_unix:
                # Unix domain socket
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_unix_connection(self._address),
                    timeout=timeout
                )
            else:
                # TCP localhost
                host, port = self._address
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
            
            self._connected = True
            logger.debug(f"Connected to service: {self.socket_name}")
            
            # Receive and validate server hello
            await self._receive_hello(timeout)
            
            # Try to authenticate if server requires it
            await self._authenticate()
            
            return True
            
        except VersionMismatchError:
            # Re-raise version errors
            await self.disconnect()
            raise
        except asyncio.TimeoutError:
            logger.debug(f"Connection timeout: {self.socket_name}")
            return False
        except ConnectionRefusedError:
            logger.debug(f"Connection refused: {self.socket_name}")
            return False
        except FileNotFoundError:
            # Unix socket doesn't exist
            logger.debug(f"Socket not found: {self.socket_name}")
            return False
        except Exception as e:
            logger.debug(f"Connection error: {e}")
            return False
    
    async def _receive_hello(self, timeout: float) -> None:
        """
        Receive and validate server hello message.
        
        Args:
            timeout: Read timeout
            
        Raises:
            VersionMismatchError: If server version is incompatible
        """
        try:
            # Read hello message length
            length_bytes = await asyncio.wait_for(
                self._reader.read(4),
                timeout=timeout
            )
            if len(length_bytes) < 4:
                logger.warning("Failed to receive hello message")
                return
            
            msg_length = int.from_bytes(length_bytes, 'big')
            
            # Read hello message
            data = await asyncio.wait_for(
                self._reader.read(msg_length),
                timeout=timeout
            )
            
            hello_data = json.loads(data.decode('utf-8'))
            self._server_hello = HelloMessage.from_dict(hello_data)
            self._server_capabilities = self._server_hello.capabilities
            
            logger.debug(
                f"Received server hello: protocol={self._server_hello.protocol_version}, "
                f"server={self._server_hello.server_version}, "
                f"auth_required={self._server_hello.requires_auth}"
            )
            
            # Check protocol version compatibility
            if not is_version_compatible(self._server_hello.protocol_version, MIN_SERVER_VERSION):
                raise VersionMismatchError(
                    client_version=self._protocol_version,
                    server_version=self._server_hello.protocol_version
                )
                
        except VersionMismatchError:
            raise
        except asyncio.TimeoutError:
            # Older servers don't send hello - treat as version 1.0
            logger.debug("No hello received (legacy server?)")
            self._server_hello = HelloMessage(protocol_version="1.0")
        except Exception as e:
            logger.warning(f"Error receiving hello: {e}")
            self._server_hello = HelloMessage(protocol_version="1.0")
    
    async def _authenticate(self) -> None:
        """
        Authenticate with server.
        
        Uses hello message to determine if auth is required.
        If authentication fails, doesn't raise - just logs warning.
        Client will discover auth required when making requests.
        """
        try:
            # Check if server requires auth from hello message
            requires_auth = (
                self._server_hello and 
                self._server_hello.requires_auth
            )
            
            if not requires_auth:
                self._authenticated = True
                logger.debug("Server does not require authentication")
                return
            
            # Try to load secret and authenticate
            secret = load_secret(self.instance_id)
            if not secret:
                logger.warning(f"No secret found for instance '{self.instance_id}' - auth will fail")
                return
            
            auth_response = await self.send_command("auth", {"token": secret})
            if auth_response and auth_response.get("success"):
                self._authenticated = True
                logger.info(f"Authenticated successfully with instance '{self.instance_id}'")
            else:
                error = auth_response.get("error", "Unknown error") if auth_response else "No response"
                logger.warning(f"Authentication failed: {error}")
                
        except Exception as e:
            logger.warning(f"Error during authentication: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from service"""
        self._connected = False
        self._authenticated = False
        self._server_hello = None
        self._server_capabilities = []
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
        logger.debug(f"Disconnected from service: {self.socket_name}")
    
    async def send_command(
        self,
        command: str,
        args: Optional[Dict[str, Any]] = None,
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send command and wait for response.
        
        Args:
            command: Command name (e.g., 'get_status', 'ping')
            args: Optional command arguments
            timeout: Response timeout in seconds
            
        Returns:
            Response dict or None on error
        """
        if not self.connected:
            logger.warning("Not connected to service")
            return None
        
        async with self._lock:
            try:
                # Build request with protocol version
                request = {
                    "command": command,
                    "request_id": str(uuid.uuid4()),
                    "protocol_version": self._protocol_version,
                    "args": args or {}
                }
                
                # Encode and send with length prefix
                request_bytes = json.dumps(request).encode('utf-8')
                length_bytes = len(request_bytes).to_bytes(4, 'big')
                
                self._writer.write(length_bytes + request_bytes)
                await self._writer.drain()
                
                # Read response length
                length_data = await asyncio.wait_for(
                    self._reader.read(4),
                    timeout=timeout
                )
                if not length_data or len(length_data) < 4:
                    logger.warning("No response from service")
                    self._connected = False
                    return None
                
                msg_length = int.from_bytes(length_data, 'big')
                
                # Read response body
                response_data = await asyncio.wait_for(
                    self._reader.read(msg_length),
                    timeout=timeout
                )
                
                response = json.loads(response_data.decode('utf-8'))
                return response
                
            except asyncio.TimeoutError:
                logger.warning(f"Command timeout: {command}")
                return None
            except ConnectionResetError:
                logger.warning("Connection reset by service")
                self._connected = False
                return None
            except Exception as e:
                logger.error(f"Error sending command {command}: {e}")
                self._connected = False
                return None
    
    async def ping(self, timeout: float = 1.0) -> bool:
        """
        Ping service to check if alive.
        
        Args:
            timeout: Ping timeout in seconds
            
        Returns:
            True if service responds
        """
        response = await self.send_command("ping", timeout=timeout)
        return response is not None and response.get("success", False)
    
    async def get_status(self) -> Optional[ServiceStatus]:
        """
        Get service status.
        
        Returns:
            ServiceStatus object or None on error
        """
        response = await self.send_command("get_status")
        if response and response.get("success"):
            data = response.get("data", {})
            return ServiceStatus.from_dict(data)
        return None
    
    async def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get service configuration.
        
        Returns:
            Config dict or None on error
        """
        response = await self.send_command("get_config")
        if response and response.get("success"):
            return response.get("data", {})
        return None
    
    async def request_stop(self) -> bool:
        """
        Request service to stop.
        
        Returns:
            True if request was accepted
        """
        response = await self.send_command("stop")
        return response is not None and response.get("success", False)
    
    async def request_restart(self) -> bool:
        """
        Request service to restart.
        
        Returns:
            True if request was accepted
        """
        response = await self.send_command("restart")
        return response is not None and response.get("success", False)


async def discover_services_async(
    instance_ids: Optional[List[str]] = None,
    timeout: float = 0.5
) -> List[InstanceInfo]:
    """
    Discover running service instances.
    
    Args:
        instance_ids: List of instance IDs to check (default: ['default'])
        timeout: Connection timeout per instance
        
    Returns:
        List of InstanceInfo for discovered services
    """
    if instance_ids is None:
        instance_ids = ["default"]
    
    discovered = []
    
    for instance_id in instance_ids:
        client = AsyncIPCClient(instance_id)
        try:
            if await client.connect(timeout=timeout):
                info = InstanceInfo(
                    instance_id=instance_id,
                    socket_name=client.socket_name,
                    connected=True
                )
                
                # Try to get status
                status = await client.get_status()
                if status:
                    info.status = asdict(status)
                
                discovered.append(info)
                await client.disconnect()
        except Exception as e:
            logger.debug(f"Error discovering {instance_id}: {e}")
    
    return discovered


class ServiceDiscoveryAsync:
    """
    Async service discovery helper.
    
    Monitors for service instances and notifies on changes.
    """
    
    def __init__(
        self,
        instance_ids: Optional[List[str]] = None,
        poll_interval: float = 5.0
    ) -> None:
        """
        Initialize async service discovery.
        
        Args:
            instance_ids: Instance IDs to monitor
            poll_interval: Polling interval in seconds
        """
        self.instance_ids = instance_ids or ["default"]
        self.poll_interval = poll_interval
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._discovered: Dict[str, InstanceInfo] = {}
        self._callbacks: List[callable] = []
    
    def add_callback(self, callback: callable) -> None:
        """Add callback for service changes"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: callable) -> None:
        """Remove callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def start(self) -> None:
        """Start discovery monitoring"""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
    
    async def stop(self) -> None:
        """Stop discovery monitoring"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _poll_loop(self) -> None:
        """Polling loop"""
        while self._running:
            try:
                discovered = await discover_services_async(
                    self.instance_ids,
                    timeout=0.5
                )
                
                # Convert to dict
                new_discovered = {i.instance_id: i for i in discovered}
                
                # Check for changes
                if new_discovered != self._discovered:
                    self._discovered = new_discovered
                    for callback in self._callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(list(new_discovered.values()))
                            else:
                                callback(list(new_discovered.values()))
                        except Exception as e:
                            logger.error(f"Discovery callback error: {e}")
                
            except Exception as e:
                logger.error(f"Discovery poll error: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    def get_discovered(self) -> List[InstanceInfo]:
        """Get currently discovered services"""
        return list(self._discovered.values())
