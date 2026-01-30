"""
IPC Server for Service Process

Simplified IPC server for GUI communication.
Uses Qt LocalSocket for cross-platform IPC.
"""

import json
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client_service import ClientService

logger = logging.getLogger(__name__)


class IPCServer:
    """
    Simple IPC server for service<->GUI communication.
    
    Runs in service process, handles requests from GUI clients.
    Uses Qt LocalSocket (cross-platform alternative to named pipes/domain sockets).
    """
    
    def __init__(self, instance_id: str, service: 'ClientService') -> None:
        """
        Initialize IPC server.
        
        Args:
            instance_id: Instance identifier
            service: ClientService instance to query
        """
        self.instance_id = instance_id
        self.service = service
        self.socket_name = f"pyWATS_Service_{instance_id}"
        
        self._server = None
        self._clients = []
        self._qt_app = None
    
    def start(self) -> bool:
        """
        Start IPC server.
        
        Note: Requires QCoreApplication to exist in main thread.
        
        Returns:
            True if started successfully
        """
        try:
            from PySide6.QtNetwork import QLocalServer
            from PySide6.QtCore import QCoreApplication
            
            # Verify Qt event loop exists
            if not QCoreApplication.instance():
                logger.error("IPC server requires QCoreApplication in main thread")
                return False
            
            # Remove stale server
            QLocalServer.removeServer(self.socket_name)
            
            # Create server
            self._server = QLocalServer()
            self._server.newConnection.connect(self._on_connection)
            
            if not self._server.listen(self.socket_name):
                logger.error(f"Failed to start IPC server: {self._server.errorString()}")
                return False
            
            logger.info(f"IPC server started: {self.socket_name}")
            return True
            
        except ImportError:
            logger.warning("PySide6 not available, IPC server disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Stop IPC server"""
        if self._server:
            self._server.close()
            logger.info("IPC server stopped")
        
        for client in self._clients:
            client.disconnectFromServer()
        self._clients.clear()
    
    def _on_connection(self):
        """Handle new client connection"""
        if not self._server:
            return
        
        client = self._server.nextPendingConnection()
        if not client:
            return
        
        logger.debug("IPC client connected")
        
        client.readyRead.connect(lambda: self._handle_request(client))
        client.disconnected.connect(lambda: self._on_disconnect(client))
        
        self._clients.append(client)
    
    def _handle_request(self, client):
        """Handle client request"""
        try:
            data = bytes(client.readAll()).decode('utf-8')
            if not data:
                return
            
            request = json.loads(data)
            command = request.get('command')
            
            logger.debug(f"IPC command: {command}")
            
            # Handle commands
            if command == 'get_status':
                response = self.service.get_status_dict()
            
            elif command == 'get_config':
                response = {
                    'config': self.service.config.to_dict()
                }
            
            elif command == 'ping':
                response = {'status': 'ok', 'message': 'pong'}
            
            elif command == 'restart':
                response = {'status': 'ok', 'message': 'Restart not implemented'}
                # TODO: Implement restart
            
            elif command == 'stop':
                response = {'status': 'ok', 'message': 'Stopping service'}
                # Stop service on background thread
                import threading
                threading.Thread(target=self.service.stop, daemon=True).start()
            
            else:
                response = {'error': f'Unknown command: {command}'}
            
            # Send response
            client.write(json.dumps(response).encode('utf-8'))
            client.flush()
            
        except json.JSONDecodeError as e:
            self._send_error(client, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            self._send_error(client, f"Server error: {e}")
    
    def _send_error(self, client, message: str):
        """Send error response"""
        try:
            response = json.dumps({'error': message})
            client.write(response.encode('utf-8'))
            client.flush()
        except Exception as e:
            logger.error(f"Failed to send error: {e}")
    
    def _on_disconnect(self, client):
        """Handle client disconnect"""
        logger.debug("IPC client disconnected")
        if client in self._clients:
            self._clients.remove(client)
        client.deleteLater()
