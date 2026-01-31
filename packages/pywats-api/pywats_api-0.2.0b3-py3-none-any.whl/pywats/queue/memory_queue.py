"""
Memory Queue for pyWATS API

Pure in-memory queue implementation with NO file operations.
This is the base queue that can be extended for persistence.

Design Principles:
    - NO file I/O - completely in-memory
    - Thread-safe for concurrent access
    - Async-compatible
    - Extensible via subclassing for persistence

For file-based persistence, use PersistentQueue from pywats_client.
"""

import logging
import asyncio
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Callable, Iterator
from dataclasses import dataclass, field
from collections import deque
import uuid

from ..shared.stats import QueueStats
from ..shared.enums import QueueItemStatus

logger = logging.getLogger(__name__)


# Re-export QueueItemStatus for convenient imports from this module
__all__ = ["QueueItemStatus", "QueueItem", "BaseQueue", "MemoryQueue", "QueueHooks"]


@dataclass
class QueueItem:
    """
    Represents an item in the queue.
    
    This is a pure data class with no file operations.
    The 'data' field holds the actual payload (report dict, pydantic model, etc.)
    """
    id: str
    data: Any  # The actual payload (report data)
    status: QueueItemStatus = QueueItemStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        data: Any,
        item_id: Optional[str] = None,
        max_attempts: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "QueueItem":
        """
        Create a new queue item.
        
        Args:
            data: The payload data (report, dict, etc.)
            item_id: Optional custom ID (auto-generated if not provided)
            max_attempts: Maximum retry attempts
            metadata: Optional metadata dictionary
            
        Returns:
            New QueueItem instance
        """
        return cls(
            id=item_id or str(uuid.uuid4()),
            data=data,
            max_attempts=max_attempts,
            metadata=metadata or {},
        )
    
    def mark_processing(self) -> None:
        """Mark item as currently being processed."""
        self.status = QueueItemStatus.PROCESSING
        self.updated_at = datetime.now()
        self.attempts += 1
    
    def mark_completed(self) -> None:
        """Mark item as successfully processed."""
        self.status = QueueItemStatus.COMPLETED
        self.updated_at = datetime.now()
        self.last_error = None
    
    def mark_failed(self, error: str) -> None:
        """Mark item as failed."""
        self.status = QueueItemStatus.FAILED
        self.updated_at = datetime.now()
        self.last_error = error
    
    def mark_suspended(self, reason: Optional[str] = None) -> None:
        """Mark item as suspended for later retry."""
        self.status = QueueItemStatus.SUSPENDED
        self.updated_at = datetime.now()
        if reason:
            self.last_error = reason
    
    def reset_to_pending(self) -> None:
        """Reset item back to pending status."""
        self.status = QueueItemStatus.PENDING
        self.updated_at = datetime.now()
    
    @property
    def can_retry(self) -> bool:
        """Check if item can be retried."""
        return self.attempts < self.max_attempts
    
    @property
    def is_pending(self) -> bool:
        return self.status == QueueItemStatus.PENDING
    
    @property
    def is_processing(self) -> bool:
        return self.status == QueueItemStatus.PROCESSING
    
    @property
    def is_completed(self) -> bool:
        return self.status == QueueItemStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        return self.status == QueueItemStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "last_error": self.last_error,
            "metadata": self.metadata,
            # Note: 'data' not included - it may be large/complex
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any], data: Any = None) -> "QueueItem":
        """Deserialize from dictionary."""
        return cls(
            id=d["id"],
            data=data,
            status=QueueItemStatus(d["status"]),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            attempts=d.get("attempts", 0),
            max_attempts=d.get("max_attempts", 3),
            last_error=d.get("last_error"),
            metadata=d.get("metadata", {}),
        )


class BaseQueue(ABC):
    """
    Abstract base class for queue implementations.
    
    Defines the interface that all queue implementations must follow.
    Subclasses can add persistence (file, database, etc.) as needed.
    """
    
    @abstractmethod
    def add(self, data: Any, **kwargs) -> QueueItem:
        """Add an item to the queue."""
        pass
    
    @abstractmethod
    def get_next(self) -> Optional[QueueItem]:
        """Get the next pending item for processing."""
        pass
    
    @abstractmethod
    def update(self, item: QueueItem) -> None:
        """Update an item's status in the queue."""
        pass
    
    @abstractmethod
    def remove(self, item_id: str) -> bool:
        """Remove an item from the queue."""
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[QueueItem]:
        """Get an item by ID."""
        pass
    
    @abstractmethod
    def list_by_status(self, status: QueueItemStatus) -> List[QueueItem]:
        """List all items with a specific status."""
        pass
    
    @abstractmethod
    def count_by_status(self, status: QueueItemStatus) -> int:
        """Count items with a specific status."""
        pass
    
    @abstractmethod
    def clear(self, status: Optional[QueueItemStatus] = None) -> int:
        """Clear items from the queue."""
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        """Total number of items in the queue."""
        pass


class MemoryQueue(BaseQueue):
    """
    Thread-safe in-memory queue implementation.
    
    This is a pure memory queue with NO file operations.
    All data is lost when the process exits.
    
    For persistence, use PersistentQueue from pywats_client which
    extends this class with file-based storage.
    
    Example:
        >>> from pywats.queue import MemoryQueue
        >>> 
        >>> queue = MemoryQueue()
        >>> 
        >>> # Add items
        >>> item = queue.add({"pn": "PN001", "sn": "SN001", "result": "Passed"})
        >>> 
        >>> # Process items
        >>> while (item := queue.get_next()) is not None:
        ...     item.mark_processing()
        ...     try:
        ...         # Process the item
        ...         api.report.submit(item.data)
        ...         item.mark_completed()
        ...     except Exception as e:
        ...         item.mark_failed(str(e))
        ...     queue.update(item)
    
    Thread Safety:
        All public methods are thread-safe and can be called from multiple
        threads concurrently. Internal state is protected by a reentrant
        lock (RLock).
        
        Safe Operations:
            - add(), get_next(), update(), remove() - fully thread-safe
            - Iteration via __iter__ - returns snapshot (thread-safe)
            - All query methods (size, count_by_status, etc.) - atomic reads
            
        Important:
            Individual QueueItem objects are NOT thread-safe once retrieved.
            Once you get an item from the queue, protect mutations with
            queue.update() calls to safely persist changes back to the queue.
            
            Example - CORRECT:
                item = queue.get_next()
                item.mark_processing()  # Safe mutation
                queue.update(item)       # Thread-safe update
            
            Example - INCORRECT:
                item = queue.get_next()
                item.status = QueueItemStatus.COMPLETED  # ❌ Not thread-safe
                # Missing queue.update(item)
    
    Cross-Platform Compatibility:
        Uses threading.RLock which is fully supported on all platforms:
        Windows, Linux, macOS, BSD, and other POSIX systems.
    """
    
    def __init__(
        self,
        max_size: Optional[int] = None,
        default_max_attempts: int = 3,
    ) -> None:
        """
        Initialize the memory queue.
        
        Args:
            max_size: Maximum queue size (None = unlimited)
            default_max_attempts: Default retry attempts for new items
        """
        self._items: Dict[str, QueueItem] = {}
        self._order: deque = deque()  # Maintains insertion order for FIFO
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_max_attempts = default_max_attempts
        
        # Event for async waiting
        self._item_added_event = asyncio.Event()
        
        logger.debug(f"Initialized MemoryQueue (max_size={max_size})")
    
    def add(
        self,
        data: Any,
        item_id: Optional[str] = None,
        max_attempts: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueueItem:
        """
        Add an item to the queue.
        
        Args:
            data: The payload data (report dict, pydantic model, etc.)
            item_id: Optional custom ID
            max_attempts: Override default max attempts
            metadata: Optional metadata
            
        Returns:
            The created QueueItem
            
        Raises:
            ValueError: If queue is full (max_size exceeded)
        """
        with self._lock:
            if self._max_size and len(self._items) >= self._max_size:
                raise ValueError(f"Queue is full (max_size={self._max_size})")
            
            item = QueueItem.create(
                data=data,
                item_id=item_id,
                max_attempts=max_attempts or self._default_max_attempts,
                metadata=metadata,
            )
            
            self._items[item.id] = item
            self._order.append(item.id)
            
            # Signal async waiters
            try:
                self._item_added_event.set()
            except:
                pass  # May fail if no event loop
            
            logger.debug(f"Added item {item.id} to queue")
            return item
    
    def get_next(self) -> Optional[QueueItem]:
        """
        Get the next pending item for processing (FIFO order).
        
        Returns:
            Next pending QueueItem or None if queue is empty
        """
        with self._lock:
            for item_id in self._order:
                item = self._items.get(item_id)
                if item and item.status == QueueItemStatus.PENDING:
                    return item
            return None
    
    def get_next_any(self, include_suspended: bool = True) -> Optional[QueueItem]:
        """
        Get the next item that can be processed.
        
        Args:
            include_suspended: Include suspended items that can retry
            
        Returns:
            Next processable QueueItem or None
        """
        with self._lock:
            for item_id in self._order:
                item = self._items.get(item_id)
                if item is None:
                    continue
                
                if item.status == QueueItemStatus.PENDING:
                    return item
                
                if include_suspended and item.status == QueueItemStatus.SUSPENDED:
                    if item.can_retry:
                        return item
            
            return None
    
    def update(self, item: QueueItem) -> None:
        """
        Update an item's status in the queue.
        
        Args:
            item: The QueueItem to update
        """
        with self._lock:
            if item.id in self._items:
                self._items[item.id] = item
                logger.debug(f"Updated item {item.id} to status {item.status.value}")
    
    def remove(self, item_id: str) -> bool:
        """
        Remove an item from the queue.
        
        Args:
            item_id: ID of item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        with self._lock:
            if item_id in self._items:
                del self._items[item_id]
                try:
                    self._order.remove(item_id)
                except ValueError:
                    pass
                logger.debug(f"Removed item {item_id} from queue")
                return True
            return False
    
    def get(self, item_id: str) -> Optional[QueueItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: ID of item to get
            
        Returns:
            QueueItem or None if not found
        """
        with self._lock:
            return self._items.get(item_id)
    
    def list_by_status(self, status: QueueItemStatus) -> List[QueueItem]:
        """
        List all items with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching QueueItems (ordered by creation time)
        """
        with self._lock:
            return [
                item for item_id in self._order
                if (item := self._items.get(item_id)) and item.status == status
            ]
    
    def list_pending(self) -> List[QueueItem]:
        """List all pending items."""
        return self.list_by_status(QueueItemStatus.PENDING)
    
    def list_failed(self) -> List[QueueItem]:
        """List all failed items."""
        return self.list_by_status(QueueItemStatus.FAILED)
    
    def list_completed(self) -> List[QueueItem]:
        """List all completed items."""
        return self.list_by_status(QueueItemStatus.COMPLETED)
    
    def count_by_status(self, status: QueueItemStatus) -> int:
        """
        Count items with a specific status.
        
        Args:
            status: Status to count
            
        Returns:
            Number of items with that status
        """
        with self._lock:
            return sum(1 for item in self._items.values() if item.status == status)
    
    def count_pending(self) -> int:
        """Count pending items."""
        return self.count_by_status(QueueItemStatus.PENDING)
    
    def count_failed(self) -> int:
        """Count failed items."""
        return self.count_by_status(QueueItemStatus.FAILED)
    
    def clear(self, status: Optional[QueueItemStatus] = None) -> int:
        """
        Clear items from the queue.
        
        Args:
            status: Only clear items with this status (None = all items)
            
        Returns:
            Number of items cleared
        """
        with self._lock:
            if status is None:
                count = len(self._items)
                self._items.clear()
                self._order.clear()
                logger.debug(f"Cleared all {count} items from queue")
                return count
            
            to_remove = [
                item_id for item_id, item in self._items.items()
                if item.status == status
            ]
            
            for item_id in to_remove:
                del self._items[item_id]
                try:
                    self._order.remove(item_id)
                except ValueError:
                    pass
            
            logger.debug(f"Cleared {len(to_remove)} {status.value} items from queue")
            return len(to_remove)
    
    def clear_completed(self) -> int:
        """Clear all completed items."""
        return self.clear(QueueItemStatus.COMPLETED)
    
    def clear_failed(self) -> int:
        """Clear all failed items."""
        return self.clear(QueueItemStatus.FAILED)
    
    def retry_failed(self) -> int:
        """
        Reset all failed items back to pending for retry.
        
        Returns:
            Number of items reset
        """
        with self._lock:
            count = 0
            for item in self._items.values():
                if item.status == QueueItemStatus.FAILED and item.can_retry:
                    item.reset_to_pending()
                    count += 1
            logger.debug(f"Reset {count} failed items to pending")
            return count
    
    @property
    def size(self) -> int:
        """Total number of items in the queue."""
        with self._lock:
            return len(self._items)
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.size == 0
    
    def __len__(self) -> int:
        return self.size
    
    def __iter__(self) -> Iterator[QueueItem]:
        """Iterate over all items in order.
        
        Returns an iterator over a snapshot of current items to avoid
        holding the lock during iteration. This makes it safe to iterate
        over the queue while other threads are modifying it.
        
        Example:
            >>> for item in queue:
            ...     print(item.id, item.status)
        
        Thread Safety:
            This method returns a snapshot, so iteration is thread-safe
            and won't block other operations. The snapshot is taken at
            the moment this method is called.
        """
        with self._lock:
            # Create snapshot to avoid holding lock during iteration
            items = [self._items[item_id] for item_id in self._order if item_id in self._items]
        return iter(items)
    
    def get_stats(self) -> QueueStats:
        """
        Get queue statistics.
        
        Returns:
            QueueStats with counts per status
            
        Example:
            >>> stats = queue.get_stats()
            >>> print(f"Pending: {stats.pending}, Processing: {stats.processing}")
        """
        with self._lock:
            stats = QueueStats()
            for item in self._items.values():
                if item.status == QueueItemStatus.PENDING:
                    stats.pending += 1
                elif item.status == QueueItemStatus.PROCESSING:
                    stats.processing += 1
                elif item.status == QueueItemStatus.COMPLETED:
                    stats.completed += 1
                elif item.status == QueueItemStatus.FAILED:
                    stats.failed += 1
            return stats
    
    # Async support
    async def wait_for_item(self, timeout: Optional[float] = None) -> bool:
        """
        Async wait for an item to be added.
        
        Args:
            timeout: Maximum seconds to wait (None = forever)
            
        Returns:
            True if item was added, False if timeout
        """
        self._item_added_event.clear()
        try:
            await asyncio.wait_for(self._item_added_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


# Hooks for extensibility
class QueueHooks:
    """
    Hooks for queue operations.
    
    Subclass to add custom behavior (logging, metrics, persistence, etc.)
    """
    
    def on_item_added(self, item: QueueItem) -> None:
        """Called when an item is added to the queue."""
        pass
    
    def on_item_updated(self, item: QueueItem) -> None:
        """Called when an item is updated."""
        pass
    
    def on_item_removed(self, item_id: str) -> None:
        """Called when an item is removed."""
        pass
    
    def on_item_completed(self, item: QueueItem) -> None:
        """Called when an item is marked as completed."""
        pass
    
    def on_item_failed(self, item: QueueItem) -> None:
        """Called when an item is marked as failed."""
        pass
