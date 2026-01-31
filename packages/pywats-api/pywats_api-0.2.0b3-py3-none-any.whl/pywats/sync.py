"""
Synchronous wrapper utilities for async pyWATS services.

This module provides the SyncServiceWrapper class used internally by pyWATS
to wrap async services for synchronous usage.

Note: For most use cases, use the main pyWATS class instead of these utilities:
    from pywats import pyWATS
    api = pyWATS(base_url="...", token="...")
"""
import asyncio
from typing import Any, TypeVar, Coroutine
from functools import wraps
import inspect

T = TypeVar('T')


def _run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine synchronously, creating an event loop if needed."""
    try:
        asyncio.get_running_loop()
        # If there's already a running loop, we can't use run_until_complete
        # This would happen in Jupyter notebooks or async contexts
        raise RuntimeError(
            "Cannot use sync API from within an async context. "
            "Use the async API directly instead."
        )
    except RuntimeError:
        # No running loop - this is the normal case for sync usage
        pass
    
    # Create a new event loop for this call
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class SyncServiceWrapper:
    """
    Generic synchronous wrapper for async services.
    
    Automatically wraps all async methods of the underlying service
    to run synchronously using _run_sync.
    """
    
    def __init__(self, async_service: Any):
        """
        Initialize with an async service instance.
        
        Args:
            async_service: Any async service with async methods
        """
        self._async = async_service
    
    def __getattr__(self, name: str) -> Any:
        """
        Dynamically wrap async methods as sync methods.
        
        Args:
            name: Attribute name to access
            
        Returns:
            Wrapped sync method or original attribute
        """
        attr = getattr(self._async, name)
        
        # If it's a coroutine function (async method), wrap it
        if inspect.iscoroutinefunction(attr):
            @wraps(attr)
            def sync_wrapper(*args, **kwargs):
                return _run_sync(attr(*args, **kwargs))
            return sync_wrapper
        
        # Otherwise return as-is (properties, regular methods, etc.)
        return attr


# Note: SyncWATS class was removed - use pyWATS instead which provides the same
# functionality with additional features like auto-discovery and settings management