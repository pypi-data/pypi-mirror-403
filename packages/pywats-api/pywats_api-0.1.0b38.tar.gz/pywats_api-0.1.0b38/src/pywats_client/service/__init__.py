"""
pyWATS Client Service

Background service for WATS Client operations.
Runs independently of GUI, provides IPC for remote control.
"""

from .client_service import ClientService
from .converter_pool import ConverterPool, ConversionItem
from .pending_watcher import PendingWatcher

__all__ = [
    'ClientService',
    'ConverterPool',
    'ConversionItem',
    'PendingWatcher',
]
