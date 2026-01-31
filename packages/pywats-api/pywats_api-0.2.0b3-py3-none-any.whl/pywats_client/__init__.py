"""
pyWATS Client - Cross-platform client application for WATS

Features:
- Background service for report processing
- Converter framework for file-to-report conversion
- Qt-based GUI for configuration and monitoring
- CLI interface for headless configuration and control
- Multi-instance support
- Service/daemon mode support (systemd, Windows Service, launchd)

Installation:
    pip install pywats-api[client]

Usage:
- GUI Mode:      python -m pywats_client gui
- Service Mode:  python -m pywats_client service
- Install:       python -m pywats_client install-service
"""

__version__ = "0.2.0b1"

# Core configuration
from .core.config import ClientConfig, get_default_config_path

# Exceptions (user-facing errors with troubleshooting hints)
from .exceptions import (
    ClientError,
    # Converter errors
    ConverterError,
    FileFormatError,
    FileAccessError,
    ConverterConfigError,
    # Queue errors
    QueueError,
    QueueFullError,
    QueueCorruptedError,
    OfflineError,
    # Service errors
    ServiceInstallError,
    ServiceStartError,
    ServicePermissionError,
    # Configuration errors
    ConfigurationError,
    ConfigurationMissingError,
)

# Service layer (async-first architecture)
from .service.client_service import ClientService, ServiceStatus
from .service.async_client_service import AsyncClientService, AsyncServiceStatus
from .service.async_converter_pool import AsyncConverterPool, AsyncConversionItem
from .service.async_pending_queue import AsyncPendingQueue, AsyncPendingQueueState

# Async IPC (pure Python, no Qt dependency)
from .service.async_ipc_server import AsyncIPCServer
from .service.async_ipc_client import (
    AsyncIPCClient,
    InstanceInfo,
    discover_services_async,
    ServiceDiscoveryAsync,
)

# Aliases for cleaner imports
ConverterPool = AsyncConverterPool
PendingQueue = AsyncPendingQueue

# Converters
from .converters.base import (
    ConverterBase,
    ConverterResult,
    ConverterArguments,
    ConversionStatus,
    PostProcessAction,
    FileInfo,
    CSVConverter,
)

# Control interfaces
from .control.cli import ConfigCLI, cli_main

# File I/O utilities
from .io import (
    AttachmentIO,
    FileInfo as AttachmentFileInfo,
    load_attachment,
    save_attachment,
)

__all__ = [
    # Version
    "__version__",
    
    # Core configuration
    "ClientConfig",
    "get_default_config_path",
    
    # Service layer (async-first)
    "ClientService",
    "ServiceStatus",
    "AsyncClientService",
    "AsyncServiceStatus",
    "AsyncConverterPool",
    "AsyncConversionItem",
    "AsyncPendingQueue",
    "AsyncPendingQueueState",
    # Aliases
    "ConverterPool",
    "PendingQueue",
    
    # IPC (async - pure Python, no Qt)
    "AsyncIPCServer",
    "AsyncIPCClient",
    "InstanceInfo",
    "discover_services_async",
    "ServiceDiscoveryAsync",
    
    # Converters
    "ConverterBase",
    "ConverterResult",
    "ConverterArguments",
    "ConversionStatus",
    "PostProcessAction",
    "FileInfo",
    "CSVConverter",
    
    # CLI
    "ConfigCLI",
    "cli_main",
    
    # File I/O
    "AttachmentIO",
    "AttachmentFileInfo",
    "load_attachment",
    "save_attachment",
    
    # Exceptions
    "ClientError",
    "ConverterError",
    "FileFormatError",
    "FileAccessError",
    "ConverterConfigError",
    "QueueError",
    "QueueFullError",
    "QueueCorruptedError",
    "OfflineError",
    "ServiceInstallError",
    "ServiceStartError",
    "ServicePermissionError",
    "ConfigurationError",
    "ConfigurationMissingError",
]
