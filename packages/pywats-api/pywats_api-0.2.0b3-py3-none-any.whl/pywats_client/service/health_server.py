"""
HTTP Health Server for pyWATS Client

Provides a lightweight HTTP health check endpoint for:
- Docker HEALTHCHECK directives
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems

Endpoints:
    GET /health         - Basic health check (200 OK or 503 Service Unavailable)
    GET /health/live    - Liveness probe (is the process alive?)
    GET /health/ready   - Readiness probe (is the service ready to accept work?)
    GET /health/details - Detailed health information (JSON)

Usage:
    from pywats_client.service.health_server import HealthServer
    
    # Create and start health server
    health_server = HealthServer(port=8080)
    health_server.set_service_reference(client_service)
    health_server.start()
    
    # In Docker/Kubernetes:
    # HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
"""

import json
import logging
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health check result container"""
    
    def __init__(
        self,
        healthy: bool,
        status: str = "unknown",
        details: Optional[Dict[str, Any]] = None
    ):
        self.healthy = healthy
        self.status = status
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "status": self.status,
            "timestamp": self.timestamp,
            "details": self.details
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class HealthRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoints"""
    
    # Reference to health server (set by HTTPServer subclass)
    health_server: Optional['HealthServer'] = None
    
    def log_message(self, format: str, *args) -> None:
        """Override to use our logger instead of stderr"""
        logger.debug(f"Health check: {args[0]}")
    
    def do_GET(self) -> None:
        """Handle GET requests"""
        if self.path == "/health" or self.path == "/":
            self._handle_health()
        elif self.path == "/health/live":
            self._handle_liveness()
        elif self.path == "/health/ready":
            self._handle_readiness()
        elif self.path == "/health/details":
            self._handle_details()
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _handle_health(self) -> None:
        """Basic health check - returns 200 if service is running"""
        status = self._get_health_status()
        if status.healthy:
            self._send_response(200, {"status": "ok"})
        else:
            self._send_response(503, {"status": "unhealthy", "reason": status.status})
    
    def _handle_liveness(self) -> None:
        """
        Liveness probe - is the process alive?
        
        Always returns 200 if the HTTP server is responding.
        Kubernetes uses this to know if the container should be restarted.
        """
        self._send_response(200, {"status": "alive"})
    
    def _handle_readiness(self) -> None:
        """
        Readiness probe - is the service ready to accept work?
        
        Returns 200 only if the service is fully initialized and connected.
        Kubernetes uses this to know if traffic should be routed to this pod.
        """
        status = self._get_health_status()
        ready = status.healthy and status.details.get("api_connected", False)
        
        if ready:
            self._send_response(200, {"status": "ready"})
        else:
            self._send_response(503, {
                "status": "not ready",
                "reason": status.details.get("reason", status.status)
            })
    
    def _handle_details(self) -> None:
        """Detailed health information"""
        status = self._get_health_status()
        self._send_response(
            200 if status.healthy else 503,
            status.to_dict()
        )
    
    def _get_health_status(self) -> HealthStatus:
        """Get current health status from the health server"""
        if self.health_server and self.health_server.health_check:
            return self.health_server.health_check()
        return HealthStatus(healthy=True, status="unknown", details={"note": "No health check configured"})
    
    def _send_response(self, code: int, data: dict) -> None:
        """Send JSON response"""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


class HealthHTTPServer(HTTPServer):
    """HTTPServer subclass that passes health_server reference to handlers"""
    
    def __init__(self, server_address, RequestHandlerClass, health_server: 'HealthServer'):
        self.health_server = health_server
        super().__init__(server_address, RequestHandlerClass)
    
    def finish_request(self, request, client_address):
        """Override to set health_server on handler"""
        self.RequestHandlerClass.health_server = self.health_server
        super().finish_request(request, client_address)


class HealthServer:
    """
    Lightweight HTTP server for health checks.
    
    Designed to be minimal with no external dependencies beyond stdlib.
    Runs in a background thread and provides health endpoints for:
    - Docker HEALTHCHECK
    - Kubernetes probes
    - Load balancer checks
    - Monitoring systems
    
    Example:
        # Create server with custom health check
        server = HealthServer(port=8080)
        server.set_health_check(my_health_function)
        server.start()
        
        # Or with service reference
        server = HealthServer(port=8080)
        server.set_service_reference(client_service)
        server.start()
    """
    
    DEFAULT_PORT = 8080
    
    def __init__(self, port: int = DEFAULT_PORT, host: str = "0.0.0.0"):
        """
        Initialize health server.
        
        Args:
            port: Port to listen on (default: 8080)
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
        """
        self.port = port
        self.host = host
        self._server: Optional[HealthHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        # Health check function
        self.health_check: Optional[Callable[[], HealthStatus]] = None
        
        # Service reference for default health check
        self._service = None
    
    def set_health_check(self, check_func: Callable[[], HealthStatus]) -> None:
        """
        Set custom health check function.
        
        Args:
            check_func: Function that returns HealthStatus
        """
        self.health_check = check_func
    
    def set_service_reference(self, service: 'ClientService') -> None:
        """
        Set reference to ClientService for automatic health checks.
        
        Args:
            service: The ClientService instance to monitor
        """
        self._service = service
        self.health_check = self._default_health_check
    
    def _default_health_check(self) -> HealthStatus:
        """Default health check using ClientService state"""
        if not self._service:
            return HealthStatus(
                healthy=False,
                status="no_service",
                details={"reason": "Service reference not set"}
            )
        
        try:
            # Import ServiceStatus here to avoid circular imports
            from .client_service import ServiceStatus
            
            # Check service status
            service_status = self._service._status
            is_running = service_status == ServiceStatus.RUNNING
            
            # Check API connection
            api_connected = (
                self._service.api is not None and
                hasattr(self._service.api, '_client') and
                self._service.api._client is not None
            )
            
            # Check components
            watcher_running = (
                self._service.pending_watcher is not None and
                getattr(self._service.pending_watcher, '_running', False)
            )
            
            converter_pool_ok = self._service.converter_pool is not None
            
            # Build details
            details = {
                "service_status": service_status.value,
                "api_connected": api_connected,
                "watcher_running": watcher_running,
                "converter_pool_ready": converter_pool_ok,
                "instance_id": self._service.instance_id,
            }
            
            # Add queue stats if available
            if self._service.pending_watcher:
                try:
                    details["pending_count"] = getattr(
                        self._service.pending_watcher, 'pending_count', 0
                    )
                except:
                    pass
            
            # Determine overall health
            healthy = is_running and api_connected
            
            if healthy:
                return HealthStatus(healthy=True, status="healthy", details=details)
            else:
                reason = []
                if not is_running:
                    reason.append(f"service not running ({service_status.value})")
                if not api_connected:
                    reason.append("API not connected")
                details["reason"] = ", ".join(reason)
                return HealthStatus(healthy=False, status="unhealthy", details=details)
                
        except Exception as e:
            logger.exception("Health check failed")
            return HealthStatus(
                healthy=False,
                status="error",
                details={"error": str(e)}
            )
    
    def start(self) -> bool:
        """
        Start the health server in a background thread.
        
        Returns:
            True if started successfully
        """
        if self._running:
            logger.warning("Health server already running")
            return True
        
        try:
            # Check if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((self.host if self.host != "0.0.0.0" else "127.0.0.1", self.port))
                if result == 0:
                    logger.warning(f"Port {self.port} already in use, health server not started")
                    return False
        except:
            pass  # Port check failed, try to start anyway
        
        try:
            self._server = HealthHTTPServer(
                (self.host, self.port),
                HealthRequestHandler,
                self
            )
            self._server.socket.settimeout(1)  # Allow periodic checks
            
            self._thread = threading.Thread(
                target=self._serve,
                daemon=True,
                name="HealthServer"
            )
            self._running = True
            self._thread.start()
            
            logger.info(f"Health server started on http://{self.host}:{self.port}/health")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
            return False
    
    def _serve(self) -> None:
        """Server thread main loop"""
        while self._running:
            try:
                self._server.handle_request()
            except Exception as e:
                if self._running:  # Only log if not shutting down
                    logger.debug(f"Health server request error: {e}")
    
    def stop(self) -> None:
        """Stop the health server"""
        self._running = False
        
        if self._server:
            try:
                self._server.shutdown()
            except:
                pass
            self._server = None
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        
        logger.info("Health server stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if server is running"""
        return self._running and self._thread is not None and self._thread.is_alive()


# Convenience function for quick health server setup
def create_health_server(
    service: Optional['ClientService'] = None,
    port: int = HealthServer.DEFAULT_PORT,
    custom_check: Optional[Callable[[], HealthStatus]] = None
) -> HealthServer:
    """
    Create and configure a health server.
    
    Args:
        service: Optional ClientService reference
        port: Port to listen on
        custom_check: Optional custom health check function
        
    Returns:
        Configured HealthServer instance (not started)
    """
    server = HealthServer(port=port)
    
    if custom_check:
        server.set_health_check(custom_check)
    elif service:
        server.set_service_reference(service)
    
    return server
