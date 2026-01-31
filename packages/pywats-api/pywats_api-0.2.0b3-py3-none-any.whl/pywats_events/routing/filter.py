"""
Event filtering for selective event processing.
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType


logger = logging.getLogger(__name__)


class EventFilter:
    """
    Composable filter for events.
    
    Allows building complex filter conditions using a fluent interface.
    
    Example:
        >>> filter = (EventFilter()
        ...     .by_type(EventType.TEST_RESULT)
        ...     .by_source("cfx")
        ...     .where(lambda e: e.payload.get("result") == "fail")
        ... )
        >>> 
        >>> if filter.matches(event):
        ...     process_failed_test(event)
    """
    
    def __init__(self):
        """Initialize empty filter (matches everything)."""
        self._predicates: List[Callable[["Event"], bool]] = []
    
    def by_type(self, *event_types: "EventType") -> "EventFilter":
        """
        Filter by event type.
        
        Args:
            event_types: Event types to include
            
        Returns:
            Self for chaining
        """
        type_set = set(event_types)
        self._predicates.append(lambda e: e.event_type in type_set)
        return self
    
    def exclude_type(self, *event_types: "EventType") -> "EventFilter":
        """
        Exclude event types.
        
        Args:
            event_types: Event types to exclude
            
        Returns:
            Self for chaining
        """
        type_set = set(event_types)
        self._predicates.append(lambda e: e.event_type not in type_set)
        return self
    
    def by_source(self, *sources: str) -> "EventFilter":
        """
        Filter by event source.
        
        Args:
            sources: Source names to include
            
        Returns:
            Self for chaining
        """
        source_set = set(sources)
        self._predicates.append(lambda e: e.source in source_set)
        return self
    
    def exclude_source(self, *sources: str) -> "EventFilter":
        """
        Exclude event sources.
        
        Args:
            sources: Source names to exclude
            
        Returns:
            Self for chaining
        """
        source_set = set(sources)
        self._predicates.append(lambda e: e.source not in source_set)
        return self
    
    def where(self, predicate: Callable[["Event"], bool]) -> "EventFilter":
        """
        Add custom filter condition.
        
        Args:
            predicate: Function(event) -> bool
            
        Returns:
            Self for chaining
        """
        self._predicates.append(predicate)
        return self
    
    def has_payload_key(self, key: str) -> "EventFilter":
        """
        Filter for events with specific payload key.
        
        Args:
            key: Payload key that must exist
            
        Returns:
            Self for chaining
        """
        self._predicates.append(lambda e: key in e.payload)
        return self
    
    def payload_equals(self, key: str, value: any) -> "EventFilter":
        """
        Filter for events with specific payload value.
        
        Args:
            key: Payload key
            value: Expected value
            
        Returns:
            Self for chaining
        """
        self._predicates.append(lambda e: e.payload.get(key) == value)
        return self
    
    def payload_in(self, key: str, values: List[any]) -> "EventFilter":
        """
        Filter for events with payload value in list.
        
        Args:
            key: Payload key
            values: List of acceptable values
            
        Returns:
            Self for chaining
        """
        value_set = set(values)
        self._predicates.append(lambda e: e.payload.get(key) in value_set)
        return self
    
    def matches(self, event: "Event") -> bool:
        """
        Check if an event matches all filter conditions.
        
        Args:
            event: Event to check
            
        Returns:
            True if event matches all conditions
        """
        if not self._predicates:
            return True
        
        for predicate in self._predicates:
            try:
                if not predicate(event):
                    return False
            except Exception as e:
                logger.warning(f"Filter predicate error: {e}")
                return False
        
        return True
    
    def __call__(self, event: "Event") -> bool:
        """Allow filter to be used as a callable."""
        return self.matches(event)
    
    def __and__(self, other: "EventFilter") -> "EventFilter":
        """Combine filters with AND logic."""
        combined = EventFilter()
        combined._predicates = self._predicates + other._predicates
        return combined
    
    def __or__(self, other: "EventFilter") -> "EventFilter":
        """Combine filters with OR logic."""
        combined = EventFilter()
        combined._predicates = [
            lambda e, f1=self, f2=other: f1.matches(e) or f2.matches(e)
        ]
        return combined
    
    def __invert__(self) -> "EventFilter":
        """Negate filter."""
        negated = EventFilter()
        negated._predicates = [lambda e, f=self: not f.matches(e)]
        return negated
    
    def __repr__(self) -> str:
        return f"EventFilter(conditions={len(self._predicates)})"
