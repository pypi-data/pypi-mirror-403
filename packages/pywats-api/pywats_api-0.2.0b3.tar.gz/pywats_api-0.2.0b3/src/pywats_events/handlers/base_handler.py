"""
Base handler abstract class for the pyWATS event system.

Handlers process events and implement business logic. They are protocol-agnostic
and can receive events from any transport (CFX, MQTT, webhook, etc.).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType


logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Abstract base class for event handlers.
    
    Handlers process events from the event bus. They declare which event types
    they handle and implement the processing logic.
    
    Example:
        >>> class ReportHandler(BaseHandler):
        ...     @property
        ...     def event_types(self) -> List[EventType]:
        ...         return [EventType.TEST_RESULT, EventType.INSPECTION_RESULT]
        ...     
        ...     async def handle(self, event: Event) -> Optional[Any]:
        ...         # Process test results, create UUTReport, submit to WATS
        ...         report = self._build_report(event.payload)
        ...         await self.report_service.submit(report)
        ...         return report
    
    Attributes:
        name: Handler name for logging/debugging (defaults to class name)
        priority: Handler priority (lower = higher priority, default 100)
        enabled: Whether this handler is enabled
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True
    ):
        """
        Initialize the handler.
        
        Args:
            name: Handler name (defaults to class name)
            priority: Execution priority (lower = earlier)
            enabled: Whether handler is enabled
        """
        self._name = name or self.__class__.__name__
        self._priority = priority
        self._enabled = enabled
        self._logger = logging.getLogger(f"{__name__}.{self._name}")
    
    @property
    def name(self) -> str:
        """Handler name for logging and debugging."""
        return self._name
    
    @property
    def priority(self) -> int:
        """Handler priority (lower = higher priority)."""
        return self._priority
    
    @property
    def enabled(self) -> bool:
        """Whether this handler is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable this handler."""
        self._enabled = value
    
    @property
    @abstractmethod
    def event_types(self) -> List["EventType"]:
        """
        List of event types this handler processes.
        
        The handler will only receive events matching these types.
        Return an empty list to receive all events (not recommended).
        
        Returns:
            List of EventType values this handler handles
        """
        pass
    
    @abstractmethod
    async def handle(self, event: "Event") -> Optional[Any]:
        """
        Process an event.
        
        This method is called when an event matching one of the handler's
        event_types is published to the event bus.
        
        Args:
            event: The event to process
            
        Returns:
            Optional result from processing (handler-specific)
            
        Raises:
            Any exception will be caught by the event bus and handled
            according to the error policy (retry, dead letter, etc.)
        """
        pass
    
    def can_handle(self, event: "Event") -> bool:
        """
        Check if this handler can process the given event.
        
        By default, checks if the event type is in event_types.
        Override for custom filtering logic.
        
        Args:
            event: The event to check
            
        Returns:
            True if this handler should process the event
        """
        if not self._enabled:
            return False
        if not self.event_types:  # Empty list = handle all
            return True
        return event.event_type in self.event_types
    
    async def on_start(self) -> None:
        """
        Called when the event bus starts.
        
        Override to perform initialization (open connections, etc.)
        """
        self._logger.debug(f"Handler {self.name} starting")
    
    async def on_stop(self) -> None:
        """
        Called when the event bus stops.
        
        Override to perform cleanup (close connections, etc.)
        """
        self._logger.debug(f"Handler {self.name} stopping")
    
    async def on_error(self, event: "Event", error: Exception) -> None:
        """
        Called when handle() raises an exception.
        
        Override to perform custom error handling (logging, alerting, etc.)
        The error will still be propagated to the event bus error policy.
        
        Args:
            event: The event that caused the error
            error: The exception that was raised
        """
        self._logger.error(
            f"Handler {self.name} error processing event {event.id}: {error}",
            exc_info=True
        )
    
    def __repr__(self) -> str:
        types = [et.value for et in self.event_types]
        return f"{self.__class__.__name__}(name={self.name}, types={types}, enabled={self.enabled})"


class SyncHandler(BaseHandler):
    """
    Base class for synchronous handlers.
    
    Use this when your handler logic doesn't need async I/O.
    The sync handle_sync() method will be wrapped for async execution.
    """
    
    @abstractmethod
    def handle_sync(self, event: "Event") -> Optional[Any]:
        """
        Process an event synchronously.
        
        Args:
            event: The event to process
            
        Returns:
            Optional result from processing
        """
        pass
    
    async def handle(self, event: "Event") -> Optional[Any]:
        """Wrap sync handler for async execution."""
        return self.handle_sync(event)


class FilteringHandler(BaseHandler):
    """
    Handler with built-in event filtering capabilities.
    
    Extends BaseHandler with filter functions that can be chained.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True
    ):
        super().__init__(name, priority, enabled)
        self._filters: List[callable] = []
    
    def add_filter(self, filter_func: callable) -> "FilteringHandler":
        """
        Add a filter function.
        
        Args:
            filter_func: Function(event) -> bool, returns True to process
            
        Returns:
            Self for chaining
        """
        self._filters.append(filter_func)
        return self
    
    def can_handle(self, event: "Event") -> bool:
        """Check base conditions and all filters."""
        if not super().can_handle(event):
            return False
        return all(f(event) for f in self._filters)
