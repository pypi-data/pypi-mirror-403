"""
Core module initialization
"""

from .config import ClientConfig, get_default_config_path
from .config_manager import ConfigManager, load_client_settings
from .instance_manager import InstanceManager, InstanceLock
from .event_bus import EventBus, event_bus, AppEvent
from .connection_config import ConnectionConfig, ConnectionState
from .file_utils import (
    SafeFileWriter, 
    SafeFileReader, 
    FileOperation,
    FileOperationResult,
    locked_file,
    safe_delete,
    safe_rename,
    ensure_directory,
)
from .async_runner import (
    AsyncTaskRunner,
    TaskResult,
    TaskState,
    TaskInfo,
    AsyncContextMixin,
    async_task,
)

__all__ = [
    "ClientConfig",
    "get_default_config_path",
    # API settings manager (file-based persistence)
    "ConfigManager",
    "load_client_settings",
    # Instance management
    "InstanceManager",
    "InstanceLock",
    # Event system
    "EventBus",
    "event_bus",
    "AppEvent",
    # Connection
    "ConnectionConfig",
    "ConnectionState",
    # File utilities
    "SafeFileWriter",
    "SafeFileReader",
    "FileOperation",
    "FileOperationResult",
    "locked_file",
    "safe_delete",
    "safe_rename",
    "ensure_directory",
    # Async utilities
    "AsyncTaskRunner",
    "TaskResult",
    "TaskState",
    "TaskInfo",
    "AsyncContextMixin",
    "async_task",
]
