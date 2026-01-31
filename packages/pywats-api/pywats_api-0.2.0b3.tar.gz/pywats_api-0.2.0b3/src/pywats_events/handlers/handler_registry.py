"""
Handler registry for managing event handlers.

The registry tracks handlers and their event type subscriptions,
enabling efficient routing of events to appropriate handlers.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.handlers.base_handler import BaseHandler
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType


logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Registry for managing event handlers.
    
    Maintains a mapping of event types to handlers and provides
    efficient lookup for event routing.
    
    Example:
        >>> registry = HandlerRegistry()
        >>> registry.register(ReportHandler())
        >>> registry.register(AssetHandler())
        >>> 
        >>> # Get handlers for a specific event type
        >>> handlers = registry.get_handlers(EventType.TEST_RESULT)
        >>> 
        >>> # Get handlers for an event (checks can_handle())
        >>> handlers = registry.get_handlers_for_event(event)
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._handlers: List["BaseHandler"] = []
        self._type_index: Dict["EventType", List["BaseHandler"]] = defaultdict(list)
        self._catch_all_handlers: List["BaseHandler"] = []
    
    def register(self, handler: "BaseHandler") -> None:
        """
        Register a handler.
        
        Args:
            handler: The handler to register
        """
        if handler in self._handlers:
            logger.warning(f"Handler {handler.name} already registered")
            return
        
        self._handlers.append(handler)
        
        # Index by event types
        event_types = handler.event_types
        if not event_types:
            # Empty list = catch-all handler
            self._catch_all_handlers.append(handler)
            logger.debug(f"Registered catch-all handler: {handler.name}")
        else:
            for event_type in event_types:
                self._type_index[event_type].append(handler)
            logger.debug(
                f"Registered handler {handler.name} for types: "
                f"{[et.value for et in event_types]}"
            )
        
        # Sort by priority
        self._sort_handlers()
    
    def unregister(self, handler: "BaseHandler") -> bool:
        """
        Unregister a handler.
        
        Args:
            handler: The handler to unregister
            
        Returns:
            True if handler was found and removed
        """
        if handler not in self._handlers:
            return False
        
        self._handlers.remove(handler)
        
        # Remove from type index
        for event_type in handler.event_types:
            if handler in self._type_index[event_type]:
                self._type_index[event_type].remove(handler)
        
        # Remove from catch-all if present
        if handler in self._catch_all_handlers:
            self._catch_all_handlers.remove(handler)
        
        logger.debug(f"Unregistered handler: {handler.name}")
        return True
    
    def get_handlers(self, event_type: "EventType") -> List["BaseHandler"]:
        """
        Get all handlers registered for an event type.
        
        Args:
            event_type: The event type to look up
            
        Returns:
            List of handlers (sorted by priority)
        """
        # Combine type-specific handlers with catch-all handlers
        handlers = self._type_index.get(event_type, []) + self._catch_all_handlers
        return sorted(handlers, key=lambda h: h.priority)
    
    def get_handlers_for_event(self, event: "Event") -> List["BaseHandler"]:
        """
        Get handlers that can handle a specific event.
        
        This checks each handler's can_handle() method, which may include
        additional filtering beyond just event type.
        
        Args:
            event: The event to find handlers for
            
        Returns:
            List of handlers that can process this event (sorted by priority)
        """
        # Start with handlers for this event type
        potential_handlers = self.get_handlers(event.event_type)
        
        # Filter by can_handle()
        handlers = [h for h in potential_handlers if h.can_handle(event)]
        
        return handlers
    
    def get_all_handlers(self) -> List["BaseHandler"]:
        """
        Get all registered handlers.
        
        Returns:
            List of all handlers (sorted by priority)
        """
        return sorted(self._handlers, key=lambda h: h.priority)
    
    def get_event_types(self) -> Set["EventType"]:
        """
        Get all event types that have registered handlers.
        
        Returns:
            Set of event types with handlers
        """
        return set(self._type_index.keys())
    
    def clear(self) -> None:
        """Remove all handlers from the registry."""
        self._handlers.clear()
        self._type_index.clear()
        self._catch_all_handlers.clear()
        logger.debug("Cleared handler registry")
    
    def _sort_handlers(self) -> None:
        """Sort all handler lists by priority."""
        self._handlers.sort(key=lambda h: h.priority)
        self._catch_all_handlers.sort(key=lambda h: h.priority)
        for handlers in self._type_index.values():
            handlers.sort(key=lambda h: h.priority)
    
    @property
    def handler_count(self) -> int:
        """Number of registered handlers."""
        return len(self._handlers)
    
    def __len__(self) -> int:
        return len(self._handlers)
    
    def __contains__(self, handler: "BaseHandler") -> bool:
        return handler in self._handlers
    
    def __repr__(self) -> str:
        return (
            f"HandlerRegistry(handlers={len(self._handlers)}, "
            f"event_types={len(self._type_index)})"
        )
