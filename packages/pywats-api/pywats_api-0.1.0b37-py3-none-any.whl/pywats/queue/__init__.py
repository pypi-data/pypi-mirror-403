"""
Queue Management for pyWATS

Provides queue implementations for report submission:

Memory Queue (Pure API - No File I/O):
    - MemoryQueue: Thread-safe in-memory queue
    - QueueItem: Data class for queue items
    - BaseQueue: Abstract base for custom implementations

File Queue (Legacy - File-Based):
    - SimpleQueue: File-based queue with WSJF format
    - Note: Consider using PersistentQueue from pywats_client instead

For production deployments, use pywats_client.ClientService,
which provides robust file watching, converter framework, and retry logic.

Design Principles:
    The pywats API should be "memory-only" with minimal file operations.
    For file-based persistence, use pywats_client.queue.PersistentQueue.
"""

# Pure memory queue (NO file operations)
from .memory_queue import (
    MemoryQueue,
    BaseQueue,
    QueueItem,
    QueueItemStatus,
    QueueHooks,
)

# File-based queue (has file operations - consider using pywats_client instead)
from .simple_queue import SimpleQueue, QueuedReport, QueueStatus

# Format converters
from .formats import WSJFConverter, convert_to_wsjf, convert_from_wsxf, convert_from_wstf

__all__ = [
    # Pure memory queue (recommended)
    "MemoryQueue",
    "BaseQueue",
    "QueueItem",
    "QueueItemStatus",
    "QueueHooks",
    # File-based queue (legacy)
    "SimpleQueue",
    "QueuedReport",
    "QueueStatus",
    # Format converters
    "WSJFConverter",
    "convert_to_wsjf",
    "convert_from_wsxf",
    "convert_from_wstf",
]

