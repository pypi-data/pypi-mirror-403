"""
Queue Module for pyWATS Client

Provides persistent queue implementations that extend the pure API queues.

Architecture:
    ┌───────────────────────────────────────────────────┐
    │  pywats.queue (Pure API - NO file I/O)            │
    │  ├── MemoryQueue - In-memory only, thread-safe    │
    │  ├── BaseQueue - Abstract base class              │
    │  └── QueueItem - Queue item data class            │
    └────────────────────┬──────────────────────────────┘
                         │ extends
    ┌────────────────────▼──────────────────────────────┐
    │  pywats_client.queue (File Persistence)           │
    │  └── PersistentQueue - File-backed queue          │
    │      - Uses atomic writes (file_utils)            │
    │      - Crash recovery                             │
    │      - WSJF format storage                        │
    └───────────────────────────────────────────────────┘

Usage:
    >>> from pywats_client.queue import PersistentQueue
    >>> 
    >>> queue = PersistentQueue(queue_dir="C:/WATS/Queue")
    >>> 
    >>> # Add report to queue
    >>> item = queue.add(report_data)
    >>> 
    >>> # Process items
    >>> for item in queue.list_pending():
    ...     item.mark_processing()
    ...     queue.update(item)
    ...     try:
    ...         api.report.submit(item.data)
    ...         item.mark_completed()
    ...     except Exception as e:
    ...         item.mark_failed(str(e))
    ...     queue.update(item)

For in-memory only (no persistence), use pywats.queue.MemoryQueue.
"""

from .persistent_queue import PersistentQueue

# Re-export base classes from pywats.queue for convenience
from pywats.queue import (
    MemoryQueue,
    BaseQueue,
    QueueItem,
    QueueItemStatus,
    QueueHooks,
    # Format converters
    WSJFConverter,
    convert_to_wsjf,
)

__all__ = [
    # Persistent queue (file-backed)
    "PersistentQueue",
    # Base classes from pywats
    "MemoryQueue",
    "BaseQueue",
    "QueueItem",
    "QueueItemStatus",
    "QueueHooks",
    # Format converters
    "WSJFConverter",
    "convert_to_wsjf",
]
