"""Synchronous runner for async coroutines.

Provides utilities to run async code from synchronous contexts.
This enables the async-first pattern where async implementations
are the source of truth, and sync methods are thin wrappers.

Usage:
    from pywats.core.sync_runner import run_sync
    
    class SyncRepository:
        def __init__(self, async_repo: AsyncRepository):
            self._async = async_repo
        
        def get_item(self, id: str) -> Item:
            return run_sync(self._async.get_item(id))
"""
import asyncio
from typing import TypeVar, Coroutine, Any
from functools import wraps

T = TypeVar('T')


def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine synchronously.
    
    Handles both cases:
    - No event loop running: creates one with asyncio.run()
    - Event loop running: runs in a thread pool to avoid blocking
    
    Args:
        coro: The coroutine to execute
        
    Returns:
        The result of the coroutine
        
    Example:
        async def fetch_data():
            return await some_async_call()
        
        # Can be called from sync code:
        data = run_sync(fetch_data())
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - use asyncio.run()
        return asyncio.run(coro)
    else:
        # Already in async context - run in thread pool
        # This avoids blocking the event loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()


def sync_wrapper(async_method):
    """
    Decorator to create a sync wrapper for an async method.
    
    Usage:
        class SyncService:
            def __init__(self, async_service):
                self._async = async_service
            
            @sync_wrapper
            async def get_item(self, id: str):
                return await self._async.get_item(id)
    
    Note: The decorated method should call the async version.
    """
    @wraps(async_method)
    def wrapper(*args, **kwargs):
        return run_sync(async_method(*args, **kwargs))
    return wrapper


class SyncWrapper:
    """
    Base class for creating sync wrappers around async classes.
    
    Subclasses should set _async_class and implement __init__
    to create the async instance.
    
    Example:
        class SyncProductRepository(SyncWrapper):
            _async_class = AsyncProductRepository
            
            def __init__(self, http_client, ...):
                # Create sync HTTP client wrapper if needed
                async_client = AsyncHttpClient(...)
                self._async = AsyncProductRepository(async_client, ...)
    """
    _async: Any  # The wrapped async instance
    
    def _run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run an async method synchronously."""
        return run_sync(coro)
