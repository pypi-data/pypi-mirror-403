"""
Example: pyWATS Async Service Application

This example shows how to use the pyWATS Client async service architecture
to build a service application with:
- AsyncClientService (background processing with asyncio)
- IPC communication via AsyncIPCClient
- File monitoring
- Graceful shutdown
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from pywats_client.service import AsyncClientService, ServiceStatus
from pywats_client.service.async_ipc_client import AsyncIPCClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceApplication:
    """
    Service application using the pyWATS AsyncClientService.
    
    This demonstrates:
    1. Starting the async background service
    2. Communicating with it via IPC
    3. Monitoring status and controlling the service
    
    The AsyncClientService can run as:
    - A Windows Service
    - A systemd service
    - A standalone daemon
    - A foreground console application
    
    The async architecture provides:
    - Non-blocking I/O with AsyncWATS
    - Concurrent uploads (5 simultaneous via AsyncPendingQueue)
    - Concurrent conversions (10 simultaneous via AsyncConverterPool)
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize service application.
        
        Args:
            instance_id: Instance ID for multi-station support
        """
        self.instance_id = instance_id
        self.service: Optional[AsyncClientService] = None
        self._running = False

    async def start(self) -> None:
        """Start the async service"""
        if self._running:
            logger.warning("Service already running")
            return
        
        logger.info(f"Starting async service application [instance: {self.instance_id}]")
        
        # Create and start the AsyncClientService
        self.service = AsyncClientService()
        self._running = True
        
        try:
            # Run blocks until service stops
            await self.service.run()
        except asyncio.CancelledError:
            logger.info("Service cancelled")
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            self._running = False
    
    async def stop(self) -> None:
        """Stop the service gracefully"""
        if not self._running:
            return
        
        logger.info("Stopping async service application...")
        
        if self.service:
            await self.service.stop()
        
        self._running = False
        logger.info("Service application stopped")
    
    def get_status(self) -> dict:
        """Get service status"""
        if not self.service:
            return {"status": "not_started"}
        
        return {
            "status": self.service.status.value,
            "running": self._running,
            "instance_id": self.instance_id,
        }


class IPCControlExample:
    """
    Example of controlling a running service via IPC.
    
    This shows how to communicate with an already-running AsyncClientService
    from another process (e.g., GUI, CLI, or web interface).
    
    Uses AsyncIPCClient which is pure asyncio (no Qt dependency).
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize IPC controller.
        
        Args:
            instance_id: Instance ID of the service to control
        """
        self.instance_id = instance_id
        self.client: Optional[AsyncIPCClient] = None
    
    async def connect(self) -> bool:
        """Connect to a running service"""
        try:
            self.client = AsyncIPCClient(self.instance_id)
            connected = await self.client.connect()
            if connected:
                logger.info(f"Connected to service [instance: {self.instance_id}]")
            return connected
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the service"""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def get_status(self) -> Optional[dict]:
        """Get status from the running service"""
        if not self.client:
            return None
        
        try:
            status = await self.client.get_status()
            return {
                'status': status.status,
                'api_status': status.api_status,
                'pending_count': status.pending_count,
                'instance_id': status.instance_id
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return None
    
    async def request_shutdown(self) -> bool:
        """Request the service to shut down"""
        if not self.client:
            return False
        
        try:
            await self.client.stop_service()
            return True
        except Exception as e:
            logger.error(f"Failed to request shutdown: {e}")
            return False


# ============================================================================
# Entry Points
# ============================================================================

def run_service():
    """Run the async service in foreground"""
    service = ServiceApplication(instance_id="default")
    asyncio.run(service.start())


async def control_service_async():
    """Example of controlling a running service via IPC (async)"""
    controller = IPCControlExample(instance_id="default")
    
    if await controller.connect():
        # Get status
        status = await controller.get_status()
        if status:
            print(f"Service status: {status}")
        
        # Disconnect
        await controller.disconnect()


def control_service():
    """Example of controlling a running service via IPC"""
    asyncio.run(control_service_async())


def main():
    """Main entry point - run the async service"""
    run_service()


if __name__ == "__main__":
    main()
