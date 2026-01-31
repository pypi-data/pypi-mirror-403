"""
Distributed tracing support for event system.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event


logger = logging.getLogger(__name__)


# Context variable for current trace
_current_trace: ContextVar[Optional["TraceContext"]] = ContextVar(
    "current_trace", default=None
)


@dataclass
class Span:
    """
    A span in a distributed trace.
    
    Represents a unit of work within a trace.
    """
    span_id: str
    name: str
    trace_id: str
    parent_span_id: Optional[str] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    status: str = "ok"
    attributes: Dict[str, Any] = None
    events: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)
        if self.attributes is None:
            self.attributes = {}
        if self.events is None:
            self.events = []
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Span duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })
    
    def end(self, status: str = "ok") -> None:
        """End the span."""
        self.end_time = datetime.now(timezone.utc)
        self.status = status
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for export."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


class TraceContext:
    """
    Context for a distributed trace.
    
    Manages the current trace and span stack.
    """
    
    def __init__(self, trace_id: Optional[str] = None):
        """Initialize trace context."""
        self.trace_id = trace_id or str(uuid.uuid4())
        self._spans: List[Span] = []
        self._current_span: Optional[Span] = None
    
    @property
    def current_span(self) -> Optional[Span]:
        """Get current active span."""
        return self._current_span
    
    @property
    def all_spans(self) -> List[Span]:
        """Get all spans in the trace."""
        return self._spans.copy()
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
        """
        Start a new span.
        
        Args:
            name: Span name
            attributes: Initial attributes
            
        Returns:
            New span
        """
        parent_span_id = self._current_span.span_id if self._current_span else None
        
        span = Span(
            span_id=str(uuid.uuid4())[:16],
            name=name,
            trace_id=self.trace_id,
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        
        self._spans.append(span)
        self._current_span = span
        return span
    
    def end_span(self, status: str = "ok") -> Optional[Span]:
        """
        End the current span.
        
        Args:
            status: Final status
            
        Returns:
            Ended span
        """
        if self._current_span:
            self._current_span.end(status)
            ended = self._current_span
            
            # Pop to parent span
            if len(self._spans) > 1:
                # Find parent
                parent_id = ended.parent_span_id
                if parent_id:
                    for span in reversed(self._spans):
                        if span.span_id == parent_id:
                            self._current_span = span
                            break
                else:
                    self._current_span = None
            else:
                self._current_span = None
            
            return ended
        return None
    
    def to_dict(self) -> Dict:
        """Convert trace to dictionary for export."""
        return {
            "trace_id": self.trace_id,
            "spans": [s.to_dict() for s in self._spans],
        }


class EventTracer:
    """
    Event tracer for distributed tracing.
    
    Provides tracing capabilities for event processing.
    
    Example:
        >>> tracer = EventTracer()
        >>> 
        >>> with tracer.trace_event(event) as span:
        ...     span.set_attribute("handler", "ReportHandler")
        ...     result = await handler.handle(event)
        ...     span.set_attribute("result", "success")
    """
    
    def __init__(self, service_name: str = "pywats_events"):
        """
        Initialize tracer.
        
        Args:
            service_name: Name of the service for traces
        """
        self._service_name = service_name
        self._exporters: List[callable] = []
        self._logger = logging.getLogger(__name__)
    
    @staticmethod
    def get_current_trace() -> Optional[TraceContext]:
        """Get the current trace context."""
        return _current_trace.get()
    
    @staticmethod
    def set_current_trace(context: Optional[TraceContext]) -> None:
        """Set the current trace context."""
        _current_trace.set(context)
    
    def add_exporter(self, exporter: callable) -> None:
        """
        Add a trace exporter.
        
        Args:
            exporter: Function(trace_dict) to export traces
        """
        self._exporters.append(exporter)
    
    @contextmanager
    def trace(self, name: str, trace_id: Optional[str] = None) -> Generator[TraceContext, None, None]:
        """
        Create a new trace context.
        
        Args:
            name: Trace name
            trace_id: Optional existing trace ID
            
        Yields:
            Trace context
        """
        context = TraceContext(trace_id=trace_id)
        token = _current_trace.set(context)
        
        try:
            context.start_span(name, {"service": self._service_name})
            yield context
            context.end_span("ok")
        except Exception as e:
            if context.current_span:
                context.current_span.set_attribute("error", str(e))
                context.end_span("error")
            raise
        finally:
            _current_trace.reset(token)
            self._export(context)
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Generator[Span, None, None]:
        """
        Create a new span in the current trace.
        
        Args:
            name: Span name
            attributes: Span attributes
            
        Yields:
            Span
        """
        context = _current_trace.get()
        
        if context is None:
            # No active trace, create minimal context
            context = TraceContext()
            token = _current_trace.set(context)
            own_context = True
        else:
            token = None
            own_context = False
        
        try:
            span = context.start_span(name, attributes)
            yield span
            context.end_span("ok")
        except Exception as e:
            span.set_attribute("error", str(e))
            context.end_span("error")
            raise
        finally:
            if own_context and token:
                _current_trace.reset(token)
    
    @contextmanager
    def trace_event(self, event: "Event") -> Generator[Span, None, None]:
        """
        Trace event processing.
        
        Uses event metadata for trace/span IDs if available.
        
        Args:
            event: Event being processed
            
        Yields:
            Span for event processing
        """
        trace_id = event.metadata.trace_id or str(uuid.uuid4())
        
        with self.trace(f"event:{event.event_type.value}", trace_id=trace_id) as context:
            span = context.current_span
            if span:
                span.set_attribute("event.id", event.id)
                span.set_attribute("event.type", str(event.event_type))
                span.set_attribute("event.source", event.source)
                if event.metadata.correlation_id:
                    span.set_attribute("correlation_id", event.metadata.correlation_id)
            yield span
    
    def _export(self, context: TraceContext) -> None:
        """Export trace to all exporters."""
        trace_dict = context.to_dict()
        
        for exporter in self._exporters:
            try:
                exporter(trace_dict)
            except Exception as e:
                self._logger.error(f"Trace export error: {e}")
    
    def __repr__(self) -> str:
        return f"EventTracer(service={self._service_name})"


def log_exporter(trace: Dict) -> None:
    """Simple exporter that logs traces."""
    logger.info(f"Trace {trace['trace_id']}: {len(trace['spans'])} spans")
    for span in trace['spans']:
        logger.debug(
            f"  Span {span['name']}: {span['duration_ms']:.2f}ms "
            f"({span['status']})"
        )
