"""
IPC Client for GUI Process

Connects to service process via Qt LocalSocket for status queries and control.
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtCore import QObject

logger = logging.getLogger(__name__)


@dataclass
class InstanceInfo:
    """Information about a discovered service instance"""
    instance_id: str
    socket_name: str
    status: str = "unknown"  # unknown, online, offline
    connection_state: str = "unknown"
    config_file: Optional[str] = None
    uptime: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ServiceIPCClient(QObject):
    """
    IPC client for connecting to service process.
    
    Usage:
        client = ServiceIPCClient("default")
        if client.connect():
            status = client.get_status()
            print(status)
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize IPC client.
        
        Args:
            instance_id: Instance ID to connect to
        """
        super().__init__()
        self.instance_id = instance_id
        self.socket_name = f"pyWATS_Service_{instance_id}"
        self._socket: Optional[QLocalSocket] = None
    
    def connect(self, timeout_ms: int = 500) -> bool:
        """
        Connect to service.
        
        Args:
            timeout_ms: Connection timeout in milliseconds (default: 500ms)
            
        Returns:
            True if connected successfully
        """
        try:
            self._socket = QLocalSocket()
            
            # Connect to server (non-blocking)
            self._socket.connectToServer(self.socket_name)
            
            # Wait for connection with timeout
            if not self._socket.waitForConnected(timeout_ms):
                error = self._socket.errorString()
                # Only log if it's not "file not found" (service not running)
                if "not found" not in error.lower():
                    logger.debug(f"Failed to connect to service: {error}")
                self._socket = None
                return False
            
            logger.debug(f"Connected to service: {self.socket_name}")
            return True
            
        except Exception as e:
            logger.debug(f"Connection error: {e}")
            self._socket = None
            return False
    
    def disconnect(self):
        """Disconnect from service"""
        if self._socket:
            self._socket.disconnectFromServer()
            self._socket = None
    
    def is_connected(self) -> bool:
        """Check if connected to service"""
        return self._socket is not None and self._socket.state() == QLocalSocket.ConnectedState
    
    def _send_command(self, command: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Send command to service and get response.
        
        Args:
            command: Command name
            **kwargs: Additional command parameters
            
        Returns:
            Response dictionary or None if error
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            # Build request
            request = {'command': command, **kwargs}
            data = json.dumps(request).encode('utf-8')
            
            # Send request
            self._socket.write(data)
            self._socket.flush()
            
            # Wait for response
            if not self._socket.waitForReadyRead(5000):
                logger.error(f"Timeout waiting for response to {command}")
                return None
            
            # Read response
            response_data = bytes(self._socket.readAll()).decode('utf-8')
            response = json.loads(response_data)
            
            # Check for error
            if 'error' in response:
                logger.error(f"Service error: {response['error']}")
                return None
            
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending command: {e}", exc_info=True)
            return None
    
    def ping(self) -> bool:
        """
        Ping service to check if alive.
        
        Returns:
            True if service responds
        """
        response = self._send_command('ping')
        return response is not None and response.get('status') == 'ok'
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get service status.
        
        Returns:
            Status dictionary with keys: status, api_status, instance_id, etc.
        """
        return self._send_command('get_status')
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get service configuration.
        
        Returns:
            Configuration dictionary
        """
        response = self._send_command('get_config')
        if response:
            return response.get('config')
        return None
    
    def get_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get service credentials (for API auto-discovery).
        
        Returns:
            Dictionary with 'base_url' and 'token' or None if not configured
        """
        config = self.get_config()
        if config:
            base_url = config.get("service_address", "")
            token = config.get("api_token", "")
            if base_url and token:
                return {"base_url": base_url, "token": token}
        return None
    
    def stop_service(self) -> bool:
        """
        Request service to stop.
        
        Returns:
            True if command sent successfully
        """
        response = self._send_command('stop')
        return response is not None


def discover_services() -> List[str]:
    """
    Discover all running service instances.
    
    Returns:
        List of instance IDs that are running
    """
    # Try common instance IDs
    common_ids = ["default", "station1", "station2", "station3", "station4", "station5", "production", "test"]
    running = []
    
    for instance_id in common_ids:
        client = ServiceIPCClient(instance_id)
        if client.connect(timeout_ms=100):
            running.append(instance_id)
            client.disconnect()
    
    return running


class ServiceDiscovery:
    """
    Discovers running service instances.
    
    Scans for IPC sockets matching pattern and tests connectivity.
    
    Usage:
        discovery = ServiceDiscovery()
        instances = ServiceDiscovery.discover_instances()
        for instance in instances:
            print(f"Found: {instance.instance_id} ({instance.status})")
    """
    
    @staticmethod
    def discover_instances(timeout_ms: int = 500) -> List[InstanceInfo]:
        """
        Discover all running service instances.
        
        Args:
            timeout_ms: Connection timeout per instance
            
        Returns:
            List of discovered instances
        """
        instances = []
        
        # Try common instance IDs
        common_ids = ["default", "station1", "station2", "station3", "station4", "station5", "production", "test"]
        
        for instance_id in common_ids:
            socket_name = f"pyWATS_Service_{instance_id}"
            
            # Try to connect
            client = ServiceIPCClient(instance_id)
            if client.connect(timeout_ms):
                # Get status
                status_data = client.get_status()
                
                if status_data:
                    instance = InstanceInfo(
                        instance_id=instance_id,
                        socket_name=socket_name,
                        status=status_data.get("status", "online"),
                        connection_state=status_data.get("connection_state", "unknown"),
                        config_file=status_data.get("config_file"),
                        uptime=status_data.get("stats", {}).get("uptime")
                    )
                else:
                    instance = InstanceInfo(
                        instance_id=instance_id,
                        socket_name=socket_name,
                        status="online"
                    )
                
                instances.append(instance)
                client.disconnect()
        
        logger.info(f"Discovered {len(instances)} service instance(s)")
        return instances
    
    @staticmethod
    def check_instance_running(instance_id: str, timeout_ms: int = 500) -> bool:
        """
        Check if specific instance is running.
        
        Args:
            instance_id: Instance ID to check
            timeout_ms: Connection timeout
            
        Returns:
            True if instance is running
        """
        client = ServiceIPCClient(instance_id)
        if client.connect(timeout_ms):
            is_alive = client.ping()
            client.disconnect()
            return is_alive
        return False
