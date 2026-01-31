"""
Asynchronous EventBus implementation.

The AsyncEventBus is designed for high-throughput, non-blocking event processing
using Python's asyncio framework.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType
    from pywats_events.handlers.base_handler import BaseHandler
    from pywats_events.transports.base_transport import BaseTransport
    from pywats_events.policies.retry_policy import RetryPolicy
    from pywats_events.policies.error_policy import ErrorPolicy


logger = logging.getLogger(__name__)


class AsyncEventBus:
    """
    Asynchronous event bus for high-throughput event processing.
    
    Uses asyncio for non-blocking event handling, suitable for
    I/O-bound handlers and high-volume event streams.
    
    Example:
        >>> async def main():
        ...     bus = AsyncEventBus()
        ...     bus.register_handler(MyAsyncHandler())
        ...     await bus.start()
        ...     
        ...     # Publish events
        ...     await bus.publish(event)
        ...     
        ...     # Shutdown
        ...     await bus.stop()
    
    Attributes:
        name: Bus instance name for logging
        max_concurrent: Maximum concurrent handler executions
    """
    
    def __init__(
        self,
        name: str = "default",
        max_concurrent: int = 100,
        retry_policy: Optional["RetryPolicy"] = None,
        error_policy: Optional["ErrorPolicy"] = None,
    ):
        """
        Initialize the async event bus.
        
        Args:
            name: Instance name for logging
            max_concurrent: Maximum concurrent handler executions
            retry_policy: Policy for retrying failed handlers
            error_policy: Policy for handling persistent failures
        """
        self._name = name
        self._max_concurrent = max_concurrent
        self._retry_policy = retry_policy
        self._error_policy = error_policy
        
        # Handler registry
        from pywats_events.handlers.handler_registry import HandlerRegistry
        self._registry = HandlerRegistry()
        
        # Transport adapters
        self._transports: List["BaseTransport"] = []
        
        # Event queue for async processing
        self._queue: asyncio.Queue["Event"] = asyncio.Queue()
        
        # Semaphore for concurrency control
        self._semaphore: Optional[asyncio.Semaphore] = None
        
        # State
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        # Callbacks
        self._on_event_callbacks: List[Callable[["Event"], Any]] = []
        self._on_error_callbacks: List[Callable[["Event", Exception], Any]] = []
        
        self._logger = logging.getLogger(f"{__name__}.{name}")
    
    @property
    def name(self) -> str:
        """Bus instance name."""
        return self._name
    
    @property
    def is_running(self) -> bool:
        """Whether the bus is running."""
        return self._running
    
    @property
    def handler_count(self) -> int:
        """Number of registered handlers."""
        return len(self._registry)
    
    @property
    def transport_count(self) -> int:
        """Number of registered transports."""
        return len(self._transports)
    
    @property
    def queue_size(self) -> int:
        """Current number of events in the queue."""
        return self._queue.qsize()
    
    # =========================================================================
    # Handler Management
    # =========================================================================
    
    def register_handler(self, handler: "BaseHandler") -> None:
        """Register an event handler."""
        self._registry.register(handler)
        self._logger.info(f"Registered handler: {handler.name}")
    
    def unregister_handler(self, handler: "BaseHandler") -> bool:
        """Unregister an event handler."""
        result = self._registry.unregister(handler)
        if result:
            self._logger.info(f"Unregistered handler: {handler.name}")
        return result
    
    def get_handlers(self, event_type: "EventType") -> List["BaseHandler"]:
        """Get handlers for an event type."""
        return self._registry.get_handlers(event_type)
    
    # =========================================================================
    # Transport Management
    # =========================================================================
    
    def register_transport(self, transport: "BaseTransport") -> None:
        """Register a transport adapter."""
        transport.set_async_event_bus(self)
        self._transports.append(transport)
        self._logger.info(f"Registered transport: {transport.name}")
    
    async def start_transport(self, transport: "BaseTransport") -> None:
        """Start a transport adapter asynchronously."""
        if hasattr(transport, 'start_async'):
            await transport.start_async()
        else:
            transport.start()
    
    # =========================================================================
    # Event Publishing
    # =========================================================================
    
    async def publish(self, event: "Event") -> None:
        """
        Publish an event to all registered handlers.
        
        This immediately processes the event without queueing.
        
        Args:
            event: Event to publish
        """
        self._logger.debug(f"Publishing event: {event}")
        
        # Notify callbacks
        for callback in self._on_event_callbacks:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self._logger.error(f"Event callback error: {e}")
        
        # Get matching handlers
        handlers = self._registry.get_handlers_for_event(event)
        
        if not handlers:
            self._logger.debug(f"No handlers for event: {event.event_type}")
            return
        
        # Execute handlers concurrently
        if self._semaphore:
            tasks = [
                self._execute_handler_with_semaphore(handler, event)
                for handler in handlers
            ]
        else:
            tasks = [
                self._execute_handler(handler, event)
                for handler in handlers
            ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish_queued(self, event: "Event") -> None:
        """
        Queue an event for asynchronous processing.
        
        Args:
            event: Event to queue
        """
        await self._queue.put(event)
        self._logger.debug(f"Queued event: {event}")
    
    async def _execute_handler_with_semaphore(
        self,
        handler: "BaseHandler",
        event: "Event"
    ) -> Optional[Any]:
        """Execute handler with concurrency limit."""
        async with self._semaphore:
            return await self._execute_handler(handler, event)
    
    async def _execute_handler(
        self,
        handler: "BaseHandler",
        event: "Event"
    ) -> Optional[Any]:
        """Execute a single handler for an event."""
        try:
            self._logger.debug(
                f"Executing handler {handler.name} for event {event.id[:8]}"
            )
            result = await handler.handle(event)
            return result
            
        except Exception as e:
            self._logger.error(f"Handler {handler.name} failed: {e}")
            
            # Notify error callbacks
            for callback in self._on_error_callbacks:
                try:
                    result = callback(event, e)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as cb_error:
                    self._logger.error(f"Error callback failed: {cb_error}")
            
            # Notify handler
            await handler.on_error(event, e)
            
            # Apply retry policy
            if self._retry_policy and self._retry_policy.should_retry(event, e):
                retry_event = event.with_retry()
                self._logger.info(
                    f"Retrying event {event.id[:8]} "
                    f"(attempt {retry_event.metadata.retry_count})"
                )
                await self.publish_queued(retry_event)
            elif self._error_policy:
                await self._error_policy.handle_failure_async(event, e)
            
            return None
    
    # =========================================================================
    # Lifecycle Management
    # =========================================================================
    
    async def start(self, num_workers: int = 4) -> None:
        """
        Start the async event bus.
        
        Args:
            num_workers: Number of worker tasks to spawn
        """
        if self._running:
            self._logger.warning("Bus already running")
            return
        
        self._logger.info(f"Starting async event bus: {self._name}")
        
        # Initialize semaphore
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        
        # Reinitialize queue (in case of restart)
        self._queue = asyncio.Queue()
        
        self._running = True
        
        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(
                self._worker_loop(),
                name=f"EventBus-{self._name}-Worker-{i}"
            )
            self._worker_tasks.append(task)
        
        # Start handlers
        for handler in self._registry.get_all_handlers():
            await handler.on_start()
        
        # Start transports
        for transport in self._transports:
            await self.start_transport(transport)
        
        self._logger.info(f"Async event bus started: {self._name}")
    
    async def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the async event bus.
        
        Args:
            timeout: Maximum seconds to wait for graceful shutdown
        """
        if not self._running:
            return
        
        self._logger.info(f"Stopping async event bus: {self._name}")
        
        self._running = False
        
        # Stop transports
        for transport in self._transports:
            if hasattr(transport, 'stop_async'):
                await transport.stop_async()
            else:
                transport.stop()
        
        # Stop handlers
        for handler in self._registry.get_all_handlers():
            await handler.on_stop()
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._worker_tasks:
            await asyncio.wait(
                self._worker_tasks,
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED
            )
        
        self._worker_tasks.clear()
        self._logger.info(f"Async event bus stopped: {self._name}")
    
    async def _worker_loop(self) -> None:
        """Worker task loop for processing queued events."""
        self._logger.debug("Worker task started")
        
        while self._running:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=0.1
                )
                await self.publish(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Worker error: {e}")
        
        # Drain remaining events
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                await self.publish(event)
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self._logger.error(f"Drain error: {e}")
        
        self._logger.debug("Worker task stopped")
    
    async def wait_until_empty(self) -> None:
        """Wait until the event queue is empty."""
        await self._queue.join()
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_event(self, callback: Callable[["Event"], Any]) -> None:
        """Register callback for all published events."""
        self._on_event_callbacks.append(callback)
    
    def on_error(self, callback: Callable[["Event", Exception], Any]) -> None:
        """Register callback for handler errors."""
        self._on_error_callbacks.append(callback)
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    async def __aenter__(self) -> "AsyncEventBus":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
    
    def __repr__(self) -> str:
        return (
            f"AsyncEventBus(name={self._name}, "
            f"handlers={len(self._registry)}, "
            f"transports={len(self._transports)}, "
            f"running={self._running})"
        )
