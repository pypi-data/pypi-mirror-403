"""
Client Service - Synchronous Entry Point

This module provides a synchronous entry point to the AsyncClientService.
AsyncClientService is the source of truth - this class runs it via asyncio.run().

Architecture: Async-first with sync entry point (Option D).
"""

import asyncio
import logging
import signal
import sys
from typing import Optional, Dict, Any
from enum import Enum

from .async_client_service import AsyncClientService, AsyncServiceStatus

logger = logging.getLogger(__name__)


# ServiceStatus enum (sync alias for AsyncServiceStatus)
class ServiceStatus(Enum):
    """Service status states"""
    STOPPED = "Stopped"
    START_PENDING = "StartPending"
    RUNNING = "Running"
    STOP_PENDING = "StopPending"
    PAUSED = "Paused"
    ERROR = "Error"


# Status mapping between async and sync versions
_STATUS_MAP = {
    AsyncServiceStatus.STOPPED: ServiceStatus.STOPPED,
    AsyncServiceStatus.START_PENDING: ServiceStatus.START_PENDING,
    AsyncServiceStatus.RUNNING: ServiceStatus.RUNNING,
    AsyncServiceStatus.STOP_PENDING: ServiceStatus.STOP_PENDING,
    AsyncServiceStatus.PAUSED: ServiceStatus.PAUSED,
    AsyncServiceStatus.ERROR: ServiceStatus.ERROR,
}


def _run_sync(coro):
    """
    Run an async coroutine synchronously.
    
    Handles both cases:
    - No event loop running: creates one with asyncio.run()
    - Event loop running: runs in a thread pool to avoid blocking
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - use asyncio.run()
        return asyncio.run(coro)
    else:
        # Already in async context - run in thread pool
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()


class ClientService:
    """
    Synchronous wrapper around AsyncClientService.
    
    Provides the same interface as the original ClientService but delegates
    all work to AsyncClientService. This follows the async-first pattern where:
    - AsyncClientService is the single source of truth
    - ClientService is a thin sync wrapper for convenience
    - No code duplication between sync and async versions
    
    Usage:
        service = ClientService(instance_id="default")
        service.start()  # Blocks until stopped
    
    For async usage, use AsyncClientService directly:
        service = AsyncClientService(instance_id="default")
        await service.run()
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize sync service wrapper.
        
        Args:
            instance_id: Instance identifier for multi-instance support
        """
        self._async = AsyncClientService(instance_id)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        logger.info(f"ClientService (sync wrapper) initialized [instance: {instance_id}]")
    
    @property
    def instance_id(self) -> str:
        """Get instance ID"""
        return self._async.instance_id
    
    @property
    def config(self):
        """Get configuration (delegates to async service)"""
        return self._async.config
    
    @property
    def status(self) -> ServiceStatus:
        """Get current service status"""
        return _STATUS_MAP.get(self._async.status, ServiceStatus.STOPPED)
    
    @property
    def api_status(self) -> str:
        """Get API connection status"""
        return self._async.api_status
    
    @property
    def api(self):
        """Get API client (delegates to async service)"""
        return self._async.api
    
    @property
    def converter_pool(self):
        """Get the async converter pool"""
        return self._async._converter_pool
    
    @property
    def pending_queue(self):
        """Get the async pending queue"""
        return self._async._pending_queue
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return self._async.stats
    
    def start(self) -> None:
        """
        Start the service (blocking).
        
        Runs the async service until stopped. This method blocks
        until stop() is called or a signal is received.
        """
        if self._async.status != AsyncServiceStatus.STOPPED:
            logger.warning("Service already running")
            return
        
        logger.info("ClientService starting")
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, stopping service")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the async service (blocks until shutdown)
        try:
            asyncio.run(self._async.run())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            raise
    
    def stop(self) -> None:
        """
        Stop the service gracefully.
        
        Signals the async service to shut down. Safe to call from
        signal handlers or other threads.
        """
        logger.info("Stopping ClientService")
        self._async.request_shutdown()
    
    def get_status_dict(self) -> Dict[str, Any]:
        """
        Get service status as dictionary (for IPC queries).
        
        Returns:
            Dictionary with service status information
        """
        return self._async.get_service_status()


def main(instance_id: str = "default"):
    """
    Service entry point.
    
    Usage:
        python -m pywats_client.service.client_service
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start service
    service = ClientService(instance_id)
    
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
