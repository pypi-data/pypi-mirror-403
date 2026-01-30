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

__version__ = "1.0.0"

# Core configuration
from .core.config import ClientConfig, get_default_config_path

# Service layer (NEW architecture)
from .service.client_service import ClientService, ServiceStatus
from .service.converter_pool import ConverterPool, ConversionItem
from .service.pending_watcher import PendingWatcher
from .service.ipc_client import ServiceIPCClient, ServiceDiscovery, InstanceInfo, discover_services

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

__all__ = [
    # Version
    "__version__",
    
    # Core configuration
    "ClientConfig",
    "get_default_config_path",
    
    # Service layer
    "ClientService",
    "ServiceStatus",
    "ConverterPool",
    "ConversionItem",
    "PendingWatcher",
    
    # IPC
    "ServiceIPCClient",
    "ServiceDiscovery",
    "InstanceInfo",
    "discover_services",
    
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
]
