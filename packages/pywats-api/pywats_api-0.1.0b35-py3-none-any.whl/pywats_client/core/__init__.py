"""
Core module initialization
"""

from .config import ClientConfig, get_default_config_path
from .client import WATSClient
from .instance_manager import InstanceManager
from .event_bus import EventBus, event_bus, AppEvent
from .app_facade import AppFacade
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
    "WATSClient",
    "InstanceManager",
    "EventBus",
    "event_bus",
    "AppEvent",
    "AppFacade",
    # Async utilities
    "AsyncTaskRunner",
    "TaskResult",
    "TaskState",
    "TaskInfo",
    "AsyncContextMixin",
    "async_task",
]
