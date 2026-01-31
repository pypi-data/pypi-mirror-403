"""
Event router for directing events to appropriate handlers.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType
    from pywats_events.handlers.base_handler import BaseHandler


logger = logging.getLogger(__name__)


class RoutingRule:
    """
    A rule for routing events.
    
    Rules can match on event type, source, payload content, etc.
    """
    
    def __init__(
        self,
        name: str,
        predicate: Callable[["Event"], bool],
        priority: int = 100,
    ):
        """
        Initialize routing rule.
        
        Args:
            name: Rule name for logging
            predicate: Function(event) -> bool, returns True if rule matches
            priority: Rule priority (lower = checked first)
        """
        self.name = name
        self.predicate = predicate
        self.priority = priority
    
    def matches(self, event: "Event") -> bool:
        """Check if rule matches an event."""
        try:
            return self.predicate(event)
        except Exception as e:
            logger.warning(f"Rule {self.name} predicate error: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"RoutingRule(name={self.name}, priority={self.priority})"


class EventRouter:
    """
    Router for directing events based on rules.
    
    Allows complex routing logic beyond simple type-based routing.
    
    Example:
        >>> router = EventRouter()
        >>> 
        >>> # Route high-priority events to fast handler
        >>> router.add_rule(
        ...     RoutingRule(
        ...         name="high_priority",
        ...         predicate=lambda e: e.payload.get("priority") == "high",
        ...         priority=10
        ...     ),
        ...     handler=fast_handler
        ... )
        >>> 
        >>> # Route by source
        >>> router.add_rule(
        ...     RoutingRule(
        ...         name="cfx_source",
        ...         predicate=lambda e: e.source == "cfx"
        ...     ),
        ...     handler=cfx_handler
        ... )
    """
    
    def __init__(self):
        """Initialize router."""
        self._rules: List[tuple[RoutingRule, "BaseHandler"]] = []
        self._default_handler: Optional["BaseHandler"] = None
        self._logger = logging.getLogger(__name__)
    
    def add_rule(
        self,
        rule: RoutingRule,
        handler: "BaseHandler"
    ) -> "EventRouter":
        """
        Add a routing rule.
        
        Args:
            rule: The routing rule
            handler: Handler to route to when rule matches
            
        Returns:
            Self for chaining
        """
        self._rules.append((rule, handler))
        self._rules.sort(key=lambda x: x[0].priority)
        return self
    
    def set_default_handler(self, handler: "BaseHandler") -> "EventRouter":
        """
        Set default handler for unmatched events.
        
        Args:
            handler: Default handler
            
        Returns:
            Self for chaining
        """
        self._default_handler = handler
        return self
    
    def route(self, event: "Event") -> Optional["BaseHandler"]:
        """
        Find the handler for an event.
        
        Args:
            event: Event to route
            
        Returns:
            Handler to use, or None if no match
        """
        for rule, handler in self._rules:
            if rule.matches(event):
                self._logger.debug(f"Event {event.id[:8]} matched rule: {rule.name}")
                return handler
        
        if self._default_handler:
            self._logger.debug(f"Event {event.id[:8]} using default handler")
            return self._default_handler
        
        return None
    
    def get_all_handlers(self, event: "Event") -> List["BaseHandler"]:
        """
        Get all handlers that match an event.
        
        Unlike route(), this returns ALL matching handlers.
        
        Args:
            event: Event to check
            
        Returns:
            List of matching handlers
        """
        handlers = []
        for rule, handler in self._rules:
            if rule.matches(event):
                handlers.append(handler)
        return handlers
    
    def clear(self) -> None:
        """Remove all routing rules."""
        self._rules.clear()
        self._default_handler = None
    
    @property
    def rule_count(self) -> int:
        """Number of routing rules."""
        return len(self._rules)
    
    def __repr__(self) -> str:
        return f"EventRouter(rules={len(self._rules)})"


def by_type(*event_types: "EventType") -> Callable[["Event"], bool]:
    """
    Create predicate that matches event types.
    
    Args:
        event_types: Event types to match
        
    Returns:
        Predicate function
    """
    type_set = set(event_types)
    return lambda event: event.event_type in type_set


def by_source(*sources: str) -> Callable[["Event"], bool]:
    """
    Create predicate that matches event sources.
    
    Args:
        sources: Source names to match
        
    Returns:
        Predicate function
    """
    source_set = set(sources)
    return lambda event: event.source in source_set


def by_payload(key: str, value: any) -> Callable[["Event"], bool]:
    """
    Create predicate that matches payload content.
    
    Args:
        key: Payload key to check
        value: Expected value
        
    Returns:
        Predicate function
    """
    return lambda event: event.payload.get(key) == value


def by_payload_exists(key: str) -> Callable[["Event"], bool]:
    """
    Create predicate that checks if payload key exists.
    
    Args:
        key: Payload key to check
        
    Returns:
        Predicate function
    """
    return lambda event: key in event.payload
