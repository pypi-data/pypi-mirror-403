"""
pyWATS Client Service

Background service for WATS Client operations.
Runs independently of GUI, provides IPC for remote control.

Architecture: Async-first
- AsyncClientService: The implementation (uses asyncio)
- ClientService: Sync entry point (runs asyncio.run internally)

Usage (sync - simple):
    from pywats_client.service import ClientService
    service = ClientService(instance_id="default")
    service.start()  # Blocks until stopped

Usage (async - full control):
    from pywats_client.service import AsyncClientService
    service = AsyncClientService(instance_id="default")
    await service.run()
"""

# Sync entry point
from .client_service import ClientService, ServiceStatus

# Async implementation
from .async_client_service import (
    AsyncClientService,
    AsyncServiceStatus,
    run_async_service,
    run_async_service_with_qt,
)
from .async_converter_pool import (
    AsyncConverterPool,
    AsyncConversionItem,
    AsyncConversionItemState,
)
from .async_pending_queue import (
    AsyncPendingQueue,
    AsyncPendingQueueState,
)

# Async IPC (pure Python, no Qt dependency)
from .async_ipc_server import AsyncIPCServer
from .async_ipc_client import (
    AsyncIPCClient,
    ServiceStatus as IPCServiceStatus,
    InstanceInfo,
    discover_services_async,
    ServiceDiscoveryAsync,
)

# Aliases for cleaner imports (async is the default)
ConverterPool = AsyncConverterPool
PendingQueue = AsyncPendingQueue

__all__ = [
    # Sync entry point
    'ClientService',
    'ServiceStatus',
    # Async implementation
    'AsyncClientService',
    'AsyncServiceStatus',
    'AsyncConverterPool',
    'AsyncConversionItem',
    'AsyncConversionItemState',
    'AsyncPendingQueue',
    'AsyncPendingQueueState',
    # Async IPC (pure Python)
    'AsyncIPCServer',
    'AsyncIPCClient',
    'IPCServiceStatus',
    'InstanceInfo',
    'discover_services_async',
    'ServiceDiscoveryAsync',
    # Aliases
    'ConverterPool',
    'PendingQueue',
    # Entry points
    'run_async_service',
    'run_async_service_with_qt',
]
