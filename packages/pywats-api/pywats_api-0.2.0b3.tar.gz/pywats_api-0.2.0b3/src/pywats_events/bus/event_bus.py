"""
Synchronous EventBus implementation.

The EventBus is the central hub for event distribution. It manages handler
registration, event publishing, and coordinates with policies for retry
and error handling.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType
    from pywats_events.handlers.base_handler import BaseHandler
    from pywats_events.transports.base_transport import BaseTransport
    from pywats_events.policies.retry_policy import RetryPolicy
    from pywats_events.policies.error_policy import ErrorPolicy


logger = logging.getLogger(__name__)


class EventBus:
    """
    Synchronous event bus for the pyWATS event system.
    
    The EventBus coordinates:
    - Handler registration and lookup
    - Event publishing and distribution
    - Transport adapter management
    - Retry and error policy execution
    
    Example:
        >>> from pywats_events import EventBus, Event, EventType
        >>> 
        >>> bus = EventBus()
        >>> bus.register_handler(MyReportHandler())
        >>> bus.start()
        >>> 
        >>> # Publish events
        >>> event = Event.create(EventType.TEST_RESULT, payload={...})
        >>> bus.publish(event)
        >>> 
        >>> # Shutdown
        >>> bus.stop()
    
    Attributes:
        name: Bus instance name for logging
        max_workers: Max threads for parallel handler execution
    """
    
    def __init__(
        self,
        name: str = "default",
        max_workers: int = 4,
        retry_policy: Optional["RetryPolicy"] = None,
        error_policy: Optional["ErrorPolicy"] = None,
    ):
        """
        Initialize the event bus.
        
        Args:
            name: Instance name for logging
            max_workers: Maximum worker threads
            retry_policy: Policy for retrying failed handlers
            error_policy: Policy for handling persistent failures
        """
        self._name = name
        self._max_workers = max_workers
        self._retry_policy = retry_policy
        self._error_policy = error_policy
        
        # Handler registry
        from pywats_events.handlers.handler_registry import HandlerRegistry
        self._registry = HandlerRegistry()
        
        # Transport adapters
        self._transports: List["BaseTransport"] = []
        
        # Event queue for async processing
        self._queue: Queue["Event"] = Queue()
        
        # Thread pool for handler execution
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # State
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._on_event_callbacks: List[Callable[["Event"], None]] = []
        self._on_error_callbacks: List[Callable[["Event", Exception], None]] = []
        
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
    
    # =========================================================================
    # Handler Management
    # =========================================================================
    
    def register_handler(self, handler: "BaseHandler") -> None:
        """
        Register an event handler.
        
        Args:
            handler: Handler to register
        """
        self._registry.register(handler)
        self._logger.info(f"Registered handler: {handler.name}")
    
    def unregister_handler(self, handler: "BaseHandler") -> bool:
        """
        Unregister an event handler.
        
        Args:
            handler: Handler to unregister
            
        Returns:
            True if handler was found and removed
        """
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
        """
        Register a transport adapter.
        
        Args:
            transport: Transport to register
        """
        transport.set_event_bus(self)
        self._transports.append(transport)
        self._logger.info(f"Registered transport: {transport.name}")
        
        # Start transport if bus is running
        if self._running:
            transport.start()
    
    def unregister_transport(self, transport: "BaseTransport") -> bool:
        """
        Unregister a transport adapter.
        
        Args:
            transport: Transport to unregister
            
        Returns:
            True if transport was found and removed
        """
        if transport not in self._transports:
            return False
        
        if self._running:
            transport.stop()
        
        self._transports.remove(transport)
        self._logger.info(f"Unregistered transport: {transport.name}")
        return True
    
    # =========================================================================
    # Event Publishing
    # =========================================================================
    
    def publish(self, event: "Event") -> None:
        """
        Publish an event to all registered handlers.
        
        This is the synchronous publish method. Events are processed
        immediately in the calling thread.
        
        Args:
            event: Event to publish
        """
        self._logger.debug(f"Publishing event: {event}")
        
        # Notify callbacks
        for callback in self._on_event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Event callback error: {e}")
        
        # Get matching handlers
        handlers = self._registry.get_handlers_for_event(event)
        
        if not handlers:
            self._logger.debug(f"No handlers for event: {event.event_type}")
            return
        
        # Execute handlers
        for handler in handlers:
            self._execute_handler(handler, event)
    
    def publish_async(self, event: "Event") -> None:
        """
        Queue an event for asynchronous processing.
        
        The event will be processed by the worker thread.
        Requires the bus to be started.
        
        Args:
            event: Event to queue
        """
        if not self._running:
            self._logger.warning("Bus not running, publishing synchronously")
            self.publish(event)
            return
        
        self._queue.put(event)
        self._logger.debug(f"Queued event: {event}")
    
    def _execute_handler(self, handler: "BaseHandler", event: "Event") -> Optional[Any]:
        """Execute a single handler for an event."""
        import asyncio
        
        try:
            self._logger.debug(f"Executing handler {handler.name} for event {event.id[:8]}")
            
            # Run async handler
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(handler.handle(event))
            finally:
                loop.close()
            
            return result
            
        except Exception as e:
            self._logger.error(f"Handler {handler.name} failed: {e}")
            
            # Notify error callbacks
            for callback in self._on_error_callbacks:
                try:
                    callback(event, e)
                except Exception as cb_error:
                    self._logger.error(f"Error callback failed: {cb_error}")
            
            # Notify handler
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(handler.on_error(event, e))
            finally:
                loop.close()
            
            # Apply retry policy
            if self._retry_policy and self._retry_policy.should_retry(event, e):
                retry_event = event.with_retry()
                self._logger.info(
                    f"Retrying event {event.id[:8]} "
                    f"(attempt {retry_event.metadata.retry_count})"
                )
                self.publish_async(retry_event)
            elif self._error_policy:
                self._error_policy.handle_failure(event, e)
            
            return None
    
    # =========================================================================
    # Lifecycle Management
    # =========================================================================
    
    def start(self) -> None:
        """
        Start the event bus.
        
        Initializes the thread pool, starts the worker thread,
        and starts all registered transports.
        """
        if self._running:
            self._logger.warning("Bus already running")
            return
        
        self._logger.info(f"Starting event bus: {self._name}")
        
        # Initialize thread pool
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        
        # Start worker thread
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name=f"EventBus-{self._name}-Worker",
            daemon=True
        )
        self._worker_thread.start()
        
        # Start handlers
        import asyncio
        for handler in self._registry.get_all_handlers():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(handler.on_start())
            finally:
                loop.close()
        
        # Start transports
        for transport in self._transports:
            transport.start()
        
        self._logger.info(f"Event bus started: {self._name}")
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the event bus.
        
        Stops all transports, handlers, and the worker thread.
        
        Args:
            timeout: Maximum seconds to wait for graceful shutdown
        """
        if not self._running:
            return
        
        self._logger.info(f"Stopping event bus: {self._name}")
        
        # Signal worker to stop
        self._running = False
        
        # Stop transports
        for transport in self._transports:
            transport.stop()
        
        # Stop handlers
        import asyncio
        for handler in self._registry.get_all_handlers():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(handler.on_stop())
            finally:
                loop.close()
        
        # Wait for worker thread
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
        
        # Shutdown thread pool
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        self._logger.info(f"Event bus stopped: {self._name}")
    
    def _worker_loop(self) -> None:
        """Worker thread loop for processing queued events."""
        self._logger.debug("Worker thread started")
        
        while self._running:
            try:
                # Get event with timeout to allow checking _running flag
                event = self._queue.get(timeout=0.1)
                self.publish(event)
                self._queue.task_done()
            except Empty:
                continue
            except Exception as e:
                self._logger.error(f"Worker error: {e}")
        
        # Drain remaining events
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                self.publish(event)
                self._queue.task_done()
            except Empty:
                break
            except Exception as e:
                self._logger.error(f"Drain error: {e}")
        
        self._logger.debug("Worker thread stopped")
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_event(self, callback: Callable[["Event"], None]) -> None:
        """Register callback for all published events."""
        self._on_event_callbacks.append(callback)
    
    def on_error(self, callback: Callable[["Event", Exception], None]) -> None:
        """Register callback for handler errors."""
        self._on_error_callbacks.append(callback)
    
    # =========================================================================
    # Context Manager
    # =========================================================================
    
    def __enter__(self) -> "EventBus":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def __repr__(self) -> str:
        return (
            f"EventBus(name={self._name}, "
            f"handlers={len(self._registry)}, "
            f"transports={len(self._transports)}, "
            f"running={self._running})"
        )
