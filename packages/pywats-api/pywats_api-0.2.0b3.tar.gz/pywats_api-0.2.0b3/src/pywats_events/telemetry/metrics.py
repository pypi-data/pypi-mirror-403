"""
Metrics collection for event system monitoring.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event
    from pywats_events.models.event_types import EventType


logger = logging.getLogger(__name__)


@dataclass
class EventStats:
    """Statistics for a single event type."""
    event_type: str
    count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    last_seen: Optional[datetime] = None
    
    @property
    def avg_latency_ms(self) -> Optional[float]:
        """Average processing latency."""
        if self.count > 0:
            return self.total_latency_ms / self.count
        return None
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.count > 0:
            return (self.success_count / self.count) * 100
        return 100.0
    
    def record(self, latency_ms: float, success: bool = True) -> None:
        """Record an event processing."""
        self.count += 1
        self.total_latency_ms += latency_ms
        self.last_seen = datetime.now(timezone.utc)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        if self.min_latency_ms is None or latency_ms < self.min_latency_ms:
            self.min_latency_ms = latency_ms
        if self.max_latency_ms is None or latency_ms > self.max_latency_ms:
            self.max_latency_ms = latency_ms
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "count": self.count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class EventMetrics:
    """
    Metrics collector for event system monitoring.
    
    Tracks event counts, latencies, success rates, and other metrics.
    
    Example:
        >>> metrics = EventMetrics()
        >>> bus.on_event(lambda e: metrics.record_start(e))
        >>> 
        >>> # After processing
        >>> metrics.record_end(event, success=True)
        >>> 
        >>> # Get metrics
        >>> print(metrics.get_summary())
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._stats: Dict[str, EventStats] = defaultdict(
            lambda: EventStats(event_type="unknown")
        )
        self._in_progress: Dict[str, float] = {}  # event_id -> start_time
        self._total_events = 0
        self._total_errors = 0
        self._start_time = datetime.now(timezone.utc)
        self._logger = logging.getLogger(__name__)
    
    @property
    def total_events(self) -> int:
        """Total events processed."""
        return self._total_events
    
    @property
    def total_errors(self) -> int:
        """Total processing errors."""
        return self._total_errors
    
    @property
    def uptime_seconds(self) -> float:
        """Time since metrics collection started."""
        return (datetime.now(timezone.utc) - self._start_time).total_seconds()
    
    @property
    def events_per_second(self) -> float:
        """Average events per second."""
        uptime = self.uptime_seconds
        if uptime > 0:
            return self._total_events / uptime
        return 0.0
    
    def record_start(self, event: "Event") -> None:
        """
        Record the start of event processing.
        
        Args:
            event: Event being processed
        """
        self._in_progress[event.id] = time.perf_counter()
    
    def record_end(self, event: "Event", success: bool = True) -> None:
        """
        Record the end of event processing.
        
        Args:
            event: Event that was processed
            success: Whether processing succeeded
        """
        start_time = self._in_progress.pop(event.id, None)
        
        if start_time is not None:
            latency_ms = (time.perf_counter() - start_time) * 1000
        else:
            latency_ms = 0.0
        
        event_type = str(event.event_type)
        if event_type not in self._stats:
            self._stats[event_type] = EventStats(event_type=event_type)
        
        self._stats[event_type].record(latency_ms, success)
        self._total_events += 1
        
        if not success:
            self._total_errors += 1
    
    def record_error(self, event: "Event") -> None:
        """Record a processing error."""
        self.record_end(event, success=False)
    
    def get_stats(self, event_type: str) -> Optional[EventStats]:
        """Get stats for a specific event type."""
        return self._stats.get(event_type)
    
    def get_all_stats(self) -> Dict[str, EventStats]:
        """Get stats for all event types."""
        return dict(self._stats)
    
    def get_summary(self) -> Dict:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        return {
            "total_events": self._total_events,
            "total_errors": self._total_errors,
            "error_rate": (self._total_errors / self._total_events * 100) if self._total_events > 0 else 0,
            "events_per_second": self.events_per_second,
            "uptime_seconds": self.uptime_seconds,
            "in_progress": len(self._in_progress),
            "event_types": len(self._stats),
            "by_type": {k: v.to_dict() for k, v in self._stats.items()},
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._stats.clear()
        self._in_progress.clear()
        self._total_events = 0
        self._total_errors = 0
        self._start_time = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return (
            f"EventMetrics(total={self._total_events}, "
            f"errors={self._total_errors}, "
            f"eps={self.events_per_second:.2f})"
        )
