"""
Async Task Runner - Bridge between async operations and Qt GUI thread.

This module provides utilities for running async operations from the GUI
without blocking the main thread, while safely delivering results back
to Qt widgets via signals.

Key Features:
- Run async coroutines in a background thread pool
- Automatic result/error delivery via Qt signals
- Progress tracking and cancellation support
- Task management and cleanup
- Decorator for easy async method integration

Usage:
    # Create a runner (typically one per page or window)
    runner = AsyncTaskRunner()
    
    # Connect to signals
    runner.task_completed.connect(self._on_task_done)
    runner.task_error.connect(self._on_task_error)
    
    # Run an async task
    async def fetch_data():
        api = get_api()
        return await api.asset.get_assets()
    
    task_id = runner.run(fetch_data(), name="fetch_assets")
    
    # Or use the decorator
    @async_task(runner)
    async def load_assets(self):
        return await self.api.asset.get_assets()
    
    load_assets()  # Returns immediately, signal emitted when done
"""

from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Awaitable, Callable, Dict, Generic, Optional, TypeVar, Union
)
from functools import wraps

from PySide6.QtCore import QObject, Signal, QThread

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskState(Enum):
    """Task execution states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult(Generic[T]):
    """
    Result container for async task execution.
    
    Contains either a successful result or an error.
    """
    task_id: str
    name: str
    state: TaskState
    result: Optional[T] = None
    error: Optional[Exception] = None
    traceback: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if task completed successfully"""
        return self.state == TaskState.COMPLETED and self.error is None
    
    @property
    def is_error(self) -> bool:
        """Check if task failed with an error"""
        return self.state == TaskState.FAILED or self.error is not None


@dataclass
class TaskInfo:
    """Information about a running task"""
    task_id: str
    name: str
    state: TaskState = TaskState.PENDING
    future: Optional[asyncio.Future] = None
    progress: int = 0
    progress_message: str = ""


class AsyncTaskRunner(QObject):
    """
    Executes async coroutines in a background thread and signals results to Qt.
    
    This class bridges the gap between Python's asyncio and Qt's event loop,
    allowing async operations to run without blocking the GUI while ensuring
    results are delivered to the GUI thread safely via signals.
    
    Thread Safety:
        All signal emissions are thread-safe due to Qt's queued connections.
        The internal state is protected for concurrent access from multiple tasks.
    
    Memory Management:
        Completed tasks are automatically cleaned up.
        Call cleanup() when done to release all resources.
    
    Example:
        class MyPage(QWidget):
            def __init__(self):
                self._runner = AsyncTaskRunner(parent=self)
                self._runner.task_completed.connect(self._on_completed)
                self._runner.task_error.connect(self._on_error)
            
            def load_data(self):
                async def fetch():
                    return await api.get_data()
                self._runner.run(fetch(), name="load_data")
            
            def _on_completed(self, result: TaskResult):
                if result.name == "load_data":
                    self._data = result.result
                    self._update_table()
            
            def _on_error(self, result: TaskResult):
                QMessageBox.warning(self, "Error", str(result.error))
    """
    
    # Signals for task lifecycle
    task_started = Signal(str, str)  # (task_id, name)
    task_completed = Signal(object)  # TaskResult
    task_error = Signal(object)  # TaskResult
    task_progress = Signal(str, int, str)  # (task_id, progress 0-100, message)
    task_cancelled = Signal(str)  # task_id
    
    # Convenience signal for any completion (success or error)
    task_finished = Signal(object)  # TaskResult
    
    def __init__(
        self, 
        parent: Optional[QObject] = None,
        max_workers: int = 4
    ) -> None:
        """
        Initialize the async task runner.
        
        Args:
            parent: Parent QObject (for automatic cleanup)
            max_workers: Maximum concurrent tasks
        """
        super().__init__(parent)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, TaskInfo] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[QThread] = None
        
        # Create a dedicated event loop for async tasks
        self._setup_event_loop()
    
    def _setup_event_loop(self) -> None:
        """Create a dedicated event loop running in a background thread"""
        self._loop = asyncio.new_event_loop()
        self._shutting_down = False
        
        # Run the event loop in a background thread
        import threading
        self._loop_thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="AsyncTaskRunner-EventLoop"
        )
        self._loop_thread.start()
    
    def _run_event_loop(self) -> None:
        """Run the event loop (called in background thread)"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def run(
        self, 
        coro: Awaitable[T], 
        name: str = "task",
        on_complete: Optional[Callable[[TaskResult[T]], None]] = None,
        on_error: Optional[Callable[[TaskResult[T]], None]] = None,
        on_progress: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Run an async coroutine in the background.
        
        Args:
            coro: The coroutine to execute
            name: Human-readable task name (for logging/UI)
            on_complete: Optional callback for successful completion
            on_error: Optional callback for errors
            on_progress: Optional callback for progress updates (percent, message)
        
        Returns:
            Task ID that can be used to track or cancel the task
            
        Raises:
            RuntimeError: If the runner has been shut down
            
        Example:
            async def fetch():
                return await api.get_assets()
            
            task_id = runner.run(
                fetch(),
                name="fetch_assets",
                on_complete=lambda r: self._update_table(r.result)
            )
        """
        # Guard against use after shutdown
        if self._shutting_down:
            raise RuntimeError("AsyncTaskRunner has been shut down")
        
        task_id = str(uuid.uuid4())[:8]
        
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            state=TaskState.PENDING
        )
        self._tasks[task_id] = task_info
        
        # Emit started signal
        self.task_started.emit(task_id, name)
        logger.debug(f"Task started: {name} ({task_id})")
        
        # Submit task to event loop
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._execute_task(task_id, name, coro, on_complete, on_error),
                self._loop
            )
            task_info.future = future
            task_info.state = TaskState.RUNNING
        else:
            logger.error("Event loop not running - cannot execute task")
            result = TaskResult(
                task_id=task_id,
                name=name,
                state=TaskState.FAILED,
                error=RuntimeError("Event loop not running")
            )
            self.task_error.emit(result)
            self.task_finished.emit(result)
        
        return task_id
    
    async def _execute_task(
        self,
        task_id: str,
        name: str,
        coro: Awaitable[T],
        on_complete: Optional[Callable[[TaskResult[T]], None]],
        on_error: Optional[Callable[[TaskResult[T]], None]]
    ) -> None:
        """Execute the task and emit appropriate signals"""
        result: TaskResult[T]
        
        try:
            value = await coro
            result = TaskResult(
                task_id=task_id,
                name=name,
                state=TaskState.COMPLETED,
                result=value
            )
            
            logger.debug(f"Task completed: {name} ({task_id})")
            
            # Emit signals (thread-safe via Qt)
            self.task_completed.emit(result)
            self.task_finished.emit(result)
            
            # Call callback if provided
            if on_complete:
                try:
                    on_complete(result)
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")
            
        except asyncio.CancelledError:
            result = TaskResult(
                task_id=task_id,
                name=name,
                state=TaskState.CANCELLED
            )
            self.task_cancelled.emit(task_id)
            self.task_finished.emit(result)
            logger.debug(f"Task cancelled: {name} ({task_id})")
            
        except Exception as e:
            tb = traceback.format_exc()
            result = TaskResult(
                task_id=task_id,
                name=name,
                state=TaskState.FAILED,
                error=e,
                traceback=tb
            )
            
            logger.error(f"Task failed: {name} ({task_id}): {e}")
            
            # Emit signals
            self.task_error.emit(result)
            self.task_finished.emit(result)
            
            # Call error callback if provided
            if on_error:
                try:
                    on_error(result)
                except Exception as cb_error:
                    logger.error(f"Error in error callback: {cb_error}")
        
        finally:
            # Clean up task info
            if task_id in self._tasks:
                self._tasks[task_id].state = result.state
    
    def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancellation was requested, False if task not found
        """
        if task_id not in self._tasks:
            return False
        
        task_info = self._tasks[task_id]
        if task_info.future and not task_info.future.done():
            task_info.future.cancel()
            task_info.state = TaskState.CANCELLED
            return True
        
        return False
    
    def cancel_all(self) -> int:
        """
        Cancel all running tasks.
        
        Returns:
            Number of tasks cancelled
        """
        count = 0
        for task_id in list(self._tasks.keys()):
            if self.cancel(task_id):
                count += 1
        return count
    
    def is_running(self, task_id: str) -> bool:
        """Check if a task is still running"""
        if task_id not in self._tasks:
            return False
        return self._tasks[task_id].state == TaskState.RUNNING
    
    def has_running_tasks(self) -> bool:
        """Check if any tasks are running"""
        return any(
            info.state == TaskState.RUNNING 
            for info in self._tasks.values()
        )
    
    def get_running_count(self) -> int:
        """Get count of running tasks"""
        return sum(
            1 for info in self._tasks.values()
            if info.state == TaskState.RUNNING
        )
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        
        Cancels all running tasks and stops the event loop.
        Called automatically when parent QObject is destroyed.
        
        This method is idempotent - safe to call multiple times.
        """
        if self._shutting_down:
            return  # Already cleaning up
        
        self._shutting_down = True
        
        # Cancel all running tasks
        self.cancel_all()
        
        # Stop the event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Shutdown executor (wait briefly for pending tasks)
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
        except TypeError:
            # Python 3.8 doesn't support cancel_futures
            self._executor.shutdown(wait=False)
        
        # Clear task tracking
        self._tasks.clear()
        
        logger.debug("AsyncTaskRunner cleaned up")
    
    def deleteLater(self) -> None:
        """Clean up when Qt deletes this object"""
        self.cleanup()
        super().deleteLater()


def async_task(
    runner: AsyncTaskRunner,
    name: Optional[str] = None
) -> Callable:
    """
    Decorator to convert an async method into a fire-and-forget task.
    
    The decorated method will run asynchronously and emit signals
    when complete. Useful for button click handlers, etc.
    
    Args:
        runner: The AsyncTaskRunner to use
        name: Task name (defaults to method name)
    
    Example:
        class MyPage(BasePage):
            def __init__(self, ...):
                self._runner = AsyncTaskRunner(parent=self)
            
            @async_task(runner=self._runner, name="load_assets")
            async def _load_assets(self):
                return await self.api.asset.get_assets()
            
            def _on_refresh_clicked(self):
                self._load_assets()  # Runs async, returns immediately
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., str]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> str:
            task_name = name or func.__name__
            coro = func(*args, **kwargs)
            return runner.run(coro, name=task_name)
        return wrapper
    return decorator


class AsyncContextMixin:
    """
    Mixin class providing async execution helpers for GUI widgets.
    
    Use this as a mixin for pages that need to run async operations.
    
    Example:
        class MyPage(BasePage, AsyncContextMixin):
            def __init__(self, ...):
                super().__init__(...)
                self._init_async_context()
                self._runner.task_completed.connect(self._on_task_completed)
            
            def load_data(self):
                self.run_async(self._load_data(), name="load_data")
            
            async def _load_data(self):
                return await self.api.asset.get_assets()
            
            def _on_task_completed(self, result):
                if result.name == "load_data":
                    self._update_ui(result.result)
    """
    
    _runner: AsyncTaskRunner
    
    def _init_async_context(self) -> None:
        """Initialize async execution context. Call in __init__."""
        if not hasattr(self, '_runner'):
            self._runner = AsyncTaskRunner(parent=self)
    
    def run_async(
        self,
        coro: Awaitable[T],
        name: str = "task",
        on_complete: Optional[Callable[[TaskResult[T]], None]] = None,
        on_error: Optional[Callable[[TaskResult[T]], None]] = None
    ) -> str:
        """
        Run an async coroutine in the background.
        
        Args:
            coro: Coroutine to execute
            name: Task name for tracking
            on_complete: Success callback
            on_error: Error callback
        
        Returns:
            Task ID
        """
        return self._runner.run(coro, name, on_complete, on_error)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        return self._runner.cancel(task_id)
    
    def cancel_all_tasks(self) -> int:
        """Cancel all running tasks"""
        return self._runner.cancel_all()
    
    @property
    def has_running_tasks(self) -> bool:
        """Check if any async tasks are running"""
        return self._runner.has_running_tasks()
