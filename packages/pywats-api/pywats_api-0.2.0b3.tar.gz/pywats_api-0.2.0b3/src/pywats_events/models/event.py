"""
Core Event and EventMetadata classes for the pyWATS event system.

Events are the fundamental unit of communication in the event system.
They are protocol-agnostic and can originate from any transport adapter
(CFX, MQTT, webhook, file watcher, etc.).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event_types import EventType


@dataclass
class EventMetadata:
    """
    Metadata for event tracing, correlation, and debugging.
    
    This information travels with the event through the system and enables:
    - Distributed tracing across services
    - Correlation of related events
    - Debugging and audit trails
    - Performance monitoring
    
    Attributes:
        event_id: Unique identifier for this event instance
        correlation_id: ID linking related events (e.g., request/response)
        causation_id: ID of the event that caused this event
        timestamp: When the event was created (UTC)
        source: Origin of the event (transport name, service name)
        source_topic: Original topic/channel (e.g., CFX topic, MQTT topic)
        retry_count: Number of times this event has been retried
        trace_id: Distributed trace ID for observability
        span_id: Span ID within the trace
        custom: Additional custom metadata
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"
    source_topic: Optional[str] = None
    retry_count: int = 0
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def increment_retry(self) -> "EventMetadata":
        """Create a copy with incremented retry count."""
        return EventMetadata(
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            timestamp=self.timestamp,
            source=self.source,
            source_topic=self.source_topic,
            retry_count=self.retry_count + 1,
            trace_id=self.trace_id,
            span_id=self.span_id,
            custom=self.custom.copy(),
        )
    
    def with_causation(self, causing_event: "Event") -> "EventMetadata":
        """Create metadata linking to a causing event."""
        return EventMetadata(
            event_id=str(uuid.uuid4()),
            correlation_id=self.correlation_id or causing_event.metadata.event_id,
            causation_id=causing_event.metadata.event_id,
            timestamp=datetime.now(timezone.utc),
            source=self.source,
            trace_id=self.trace_id or causing_event.metadata.trace_id,
            span_id=str(uuid.uuid4())[:8],
            custom=self.custom.copy(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "source_topic": self.source_topic,
            "retry_count": self.retry_count,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "custom": self.custom,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventMetadata":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)
            
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            timestamp=timestamp,
            source=data.get("source", "unknown"),
            source_topic=data.get("source_topic"),
            retry_count=data.get("retry_count", 0),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            custom=data.get("custom", {}),
        )


@dataclass
class Event:
    """
    Core event class for the pyWATS event system.
    
    Events are protocol-agnostic containers for data flowing through the system.
    They carry:
    - A type indicating what kind of event this is
    - A payload containing the actual data
    - Metadata for tracing and debugging
    
    Example:
        >>> from pywats_events.models import Event, EventType
        >>> 
        >>> event = Event(
        ...     event_type=EventType.TEST_RESULT,
        ...     payload={
        ...         "unit_id": "SN12345",
        ...         "result": "pass",
        ...         "tests": [...]
        ...     },
        ...     source="cfx"
        ... )
    
    Attributes:
        event_type: The type of event (from EventType enum)
        payload: The event data (type depends on event_type)
        metadata: Tracing and debugging metadata
    """
    
    event_type: "EventType"
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def __post_init__(self):
        """Ensure metadata has source if provided at event level."""
        # If source was provided in metadata, keep it
        pass
    
    @classmethod
    def create(
        cls,
        event_type: "EventType",
        payload: Dict[str, Any],
        source: str = "unknown",
        correlation_id: Optional[str] = None,
        **metadata_kwargs
    ) -> "Event":
        """
        Factory method to create an event with common options.
        
        Args:
            event_type: The type of event
            payload: Event data
            source: Origin of the event (e.g., "cfx", "mqtt", "webhook")
            correlation_id: ID to correlate related events
            **metadata_kwargs: Additional metadata fields
            
        Returns:
            New Event instance
        """
        metadata = EventMetadata(
            source=source,
            correlation_id=correlation_id,
            **metadata_kwargs
        )
        return cls(event_type=event_type, payload=payload, metadata=metadata)
    
    def with_retry(self) -> "Event":
        """Create a copy of this event with incremented retry count."""
        return Event(
            event_type=self.event_type,
            payload=self.payload.copy(),
            metadata=self.metadata.increment_retry(),
        )
    
    def derive(
        self,
        event_type: "EventType",
        payload: Dict[str, Any],
        source: Optional[str] = None
    ) -> "Event":
        """
        Create a derived event that maintains correlation with this event.
        
        Useful when one event triggers the creation of another.
        
        Args:
            event_type: Type for the new event
            payload: Payload for the new event
            source: Source for the new event (defaults to same source)
            
        Returns:
            New Event linked to this one via correlation/causation IDs
        """
        new_metadata = self.metadata.with_causation(self)
        if source:
            new_metadata.source = source
        return Event(
            event_type=event_type,
            payload=payload,
            metadata=new_metadata,
        )
    
    @property
    def id(self) -> str:
        """Shortcut to event_id in metadata."""
        return self.metadata.event_id
    
    @property
    def event_id(self) -> str:
        """Alias for id property (for compatibility)."""
        return self.metadata.event_id
    
    @property
    def source(self) -> str:
        """Shortcut to source in metadata."""
        return self.metadata.source
    
    @property
    def timestamp(self) -> datetime:
        """Shortcut to timestamp in metadata."""
        return self.metadata.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": str(self.event_type),
            "payload": self.payload,
            "metadata": self.metadata.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create event from dictionary.
        
        Note: Requires EventType to be imported and the event_type
        string to be a valid EventType value.
        """
        from pywats_events.models.event_types import EventType
        
        event_type_str = data.get("event_type", "custom")
        try:
            event_type = EventType.from_string(event_type_str)
        except ValueError:
            event_type = EventType.CUSTOM
            
        return cls(
            event_type=event_type,
            payload=data.get("payload", {}),
            metadata=EventMetadata.from_dict(data.get("metadata", {})),
        )
    
    def __repr__(self) -> str:
        return (
            f"Event(type={self.event_type.value}, "
            f"id={self.id[:8]}..., "
            f"source={self.source})"
        )
