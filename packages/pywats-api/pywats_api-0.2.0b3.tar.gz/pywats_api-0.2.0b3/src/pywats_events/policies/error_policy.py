"""
Error handling policy with dead letter queue and circuit breaker.

Handles events that have exhausted their retry attempts or encountered
unrecoverable errors.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pywats_events.models.event import Event


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking all events
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class DeadLetterEntry:
    """
    Entry in the dead letter queue.
    
    Attributes:
        event: The failed event
        error: The exception that caused the failure
        timestamp: When the failure occurred
        handler_name: Name of the handler that failed
        retry_count: Number of retries attempted
    """
    event: "Event"
    error: Exception
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    handler_name: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event.id,
            "event_type": str(self.event.event_type),
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "timestamp": self.timestamp.isoformat(),
            "handler_name": self.handler_name,
            "retry_count": self.retry_count,
        }


class DeadLetterQueue:
    """
    Dead letter queue for events that failed processing.
    
    Stores failed events for later inspection, replay, or manual handling.
    
    Example:
        >>> dlq = DeadLetterQueue(max_size=1000)
        >>> dlq.add(event, error)
        >>> 
        >>> # Inspect failed events
        >>> for entry in dlq.get_entries():
        ...     print(f"Failed: {entry.event_id} - {entry.error}")
        >>> 
        >>> # Replay events
        >>> while entry := dlq.pop():
        ...     await bus.publish(entry.event)
    """
    
    def __init__(
        self,
        max_size: int = 10000,
        on_add: Optional[Callable[[DeadLetterEntry], None]] = None,
    ):
        """
        Initialize dead letter queue.
        
        Args:
            max_size: Maximum entries to store (oldest removed when exceeded)
            on_add: Callback when entry is added
        """
        self._max_size = max_size
        self._on_add = on_add
        self._entries: Deque[DeadLetterEntry] = deque(maxlen=max_size)
        self._logger = logging.getLogger(__name__)
    
    @property
    def size(self) -> int:
        """Number of entries in the queue."""
        return len(self._entries)
    
    @property
    def is_empty(self) -> bool:
        """Whether the queue is empty."""
        return len(self._entries) == 0
    
    def add(
        self,
        event: "Event",
        error: Exception,
        handler_name: Optional[str] = None,
    ) -> DeadLetterEntry:
        """
        Add a failed event to the dead letter queue.
        
        Args:
            event: The failed event
            error: The exception that caused the failure
            handler_name: Name of the handler that failed
            
        Returns:
            The created dead letter entry
        """
        entry = DeadLetterEntry(
            event=event,
            error=error,
            handler_name=handler_name,
            retry_count=event.metadata.retry_count,
        )
        
        self._entries.append(entry)
        self._logger.warning(
            f"Event {event.id[:8]} added to dead letter queue: {error}"
        )
        
        if self._on_add:
            try:
                self._on_add(entry)
            except Exception as e:
                self._logger.error(f"DLQ callback error: {e}")
        
        return entry
    
    def pop(self) -> Optional[DeadLetterEntry]:
        """
        Remove and return the oldest entry.
        
        Returns:
            The oldest entry, or None if empty
        """
        if self._entries:
            return self._entries.popleft()
        return None
    
    def peek(self) -> Optional[DeadLetterEntry]:
        """
        Return the oldest entry without removing it.
        
        Returns:
            The oldest entry, or None if empty
        """
        if self._entries:
            return self._entries[0]
        return None
    
    def get_entries(
        self,
        limit: Optional[int] = None,
        event_type: Optional[str] = None,
    ) -> List[DeadLetterEntry]:
        """
        Get entries from the queue.
        
        Args:
            limit: Maximum entries to return
            event_type: Filter by event type
            
        Returns:
            List of entries (newest first)
        """
        entries = list(reversed(self._entries))
        
        if event_type:
            entries = [
                e for e in entries 
                if str(e.event.event_type) == event_type
            ]
        
        if limit:
            entries = entries[:limit]
        
        return entries
    
    def clear(self) -> int:
        """
        Clear all entries from the queue.
        
        Returns:
            Number of entries removed
        """
        count = len(self._entries)
        self._entries.clear()
        self._logger.info(f"Cleared {count} entries from dead letter queue")
        return count
    
    def __len__(self) -> int:
        return len(self._entries)


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Tracks failure rates and can "trip" to prevent further attempts
    when a handler is consistently failing.
    
    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Blocking all requests, waiting for reset timeout
        - HALF_OPEN: Allowing limited requests to test recovery
    
    Example:
        >>> breaker = CircuitBreaker(
        ...     failure_threshold=5,
        ...     reset_timeout=30.0
        ... )
        >>> 
        >>> if breaker.can_proceed():
        ...     try:
        ...         await handler.handle(event)
        ...         breaker.record_success()
        ...     except Exception as e:
        ...         breaker.record_failure()
        ...         raise
        ... else:
        ...     # Circuit is open, skip this handler
        ...     pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        reset_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes in half-open before closing
            reset_timeout: Seconds before trying half-open from open
            half_open_max_calls: Max calls allowed in half-open state
        """
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._reset_timeout = reset_timeout
        self._half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        
        self._logger = logging.getLogger(__name__)
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        self._update_state()
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Whether circuit is in closed (normal) state."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Whether circuit is open (blocking)."""
        return self.state == CircuitState.OPEN
    
    def can_proceed(self) -> bool:
        """
        Check if a request can proceed.
        
        Returns:
            True if request should proceed, False if blocked
        """
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.OPEN:
            return False
        
        # HALF_OPEN: allow limited calls
        if self._half_open_calls < self._half_open_max_calls:
            self._half_open_calls += 1
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record a successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._logger.debug(
                f"Circuit breaker success in half-open: {self._success_count}/{self._success_threshold}"
            )
            if self._success_count >= self._success_threshold:
                self._close()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        
        if self._state == CircuitState.HALF_OPEN:
            self._logger.warning("Circuit breaker failure in half-open, re-opening")
            self._open()
        elif self._state == CircuitState.CLOSED:
            self._logger.debug(
                f"Circuit breaker failure: {self._failure_count}/{self._failure_threshold}"
            )
            if self._failure_count >= self._failure_threshold:
                self._open()
    
    def reset(self) -> None:
        """Reset circuit to closed state."""
        self._close()
        self._logger.info("Circuit breaker manually reset")
    
    def _update_state(self) -> None:
        """Update state based on timeout."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._reset_timeout:
                self._half_open()
    
    def _open(self) -> None:
        """Transition to open state."""
        self._state = CircuitState.OPEN
        self._logger.warning("Circuit breaker OPENED")
    
    def _close(self) -> None:
        """Transition to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._logger.info("Circuit breaker CLOSED")
    
    def _half_open(self) -> None:
        """Transition to half-open state."""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._half_open_calls = 0
        self._logger.info("Circuit breaker HALF-OPEN")
    
    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(state={self._state.value}, "
            f"failures={self._failure_count}/{self._failure_threshold})"
        )


class ErrorPolicy:
    """
    Error handling policy for failed events.
    
    Combines dead letter queue, circuit breaker, and custom error handling.
    
    Example:
        >>> policy = ErrorPolicy()
        >>> policy.on_failure(lambda event, error: alert(event, error))
        >>> 
        >>> try:
        ...     await handler.handle(event)
        ... except Exception as e:
        ...     policy.handle_failure(event, e)
    """
    
    def __init__(
        self,
        dead_letter_queue: Optional[DeadLetterQueue] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize error policy.
        
        Args:
            dead_letter_queue: DLQ for failed events
            circuit_breaker: Circuit breaker for failure protection
        """
        self._dlq = dead_letter_queue or DeadLetterQueue()
        self._circuit_breaker = circuit_breaker
        self._failure_callbacks: List[Callable[["Event", Exception], None]] = []
        self._logger = logging.getLogger(__name__)
    
    @property
    def dead_letter_queue(self) -> DeadLetterQueue:
        """Access to the dead letter queue."""
        return self._dlq
    
    @property
    def circuit_breaker(self) -> Optional[CircuitBreaker]:
        """Access to the circuit breaker."""
        return self._circuit_breaker
    
    def on_failure(
        self,
        callback: Callable[["Event", Exception], None]
    ) -> "ErrorPolicy":
        """
        Add a failure callback.
        
        Args:
            callback: Function(event, error) called on failure
            
        Returns:
            Self for chaining
        """
        self._failure_callbacks.append(callback)
        return self
    
    def handle_failure(
        self,
        event: "Event",
        error: Exception,
        handler_name: Optional[str] = None,
    ) -> None:
        """
        Handle a failed event (synchronous).
        
        Args:
            event: The failed event
            error: The exception that occurred
            handler_name: Name of the failing handler
        """
        self._logger.error(
            f"Event {event.id[:8]} failed permanently: {error}"
        )
        
        # Add to dead letter queue
        self._dlq.add(event, error, handler_name)
        
        # Update circuit breaker
        if self._circuit_breaker:
            self._circuit_breaker.record_failure()
        
        # Notify callbacks
        for callback in self._failure_callbacks:
            try:
                callback(event, error)
            except Exception as cb_error:
                self._logger.error(f"Failure callback error: {cb_error}")
    
    async def handle_failure_async(
        self,
        event: "Event",
        error: Exception,
        handler_name: Optional[str] = None,
    ) -> None:
        """
        Handle a failed event (asynchronous).
        
        Args:
            event: The failed event
            error: The exception that occurred
            handler_name: Name of the failing handler
        """
        self._logger.error(
            f"Event {event.id[:8]} failed permanently: {error}"
        )
        
        # Add to dead letter queue
        self._dlq.add(event, error, handler_name)
        
        # Update circuit breaker
        if self._circuit_breaker:
            self._circuit_breaker.record_failure()
        
        # Notify callbacks
        for callback in self._failure_callbacks:
            try:
                result = callback(event, error)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as cb_error:
                self._logger.error(f"Failure callback error: {cb_error}")
    
    def can_process(self) -> bool:
        """
        Check if processing should proceed.
        
        Returns:
            True if circuit breaker allows processing
        """
        if self._circuit_breaker:
            return self._circuit_breaker.can_proceed()
        return True
    
    def record_success(self) -> None:
        """Record a successful operation."""
        if self._circuit_breaker:
            self._circuit_breaker.record_success()
    
    def __repr__(self) -> str:
        return (
            f"ErrorPolicy(dlq_size={len(self._dlq)}, "
            f"circuit={self._circuit_breaker})"
        )
