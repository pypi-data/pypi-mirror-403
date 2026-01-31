"""
Queue Management for pyWATS

Provides queue implementations for report submission:

Memory Queue (Pure API - No File I/O):
    - MemoryQueue: Thread-safe in-memory queue
    - QueueItem: Data class for queue items
    - BaseQueue: Abstract base for custom implementations
    - QueueItemStatus: Unified status enum (from pywats.shared.enums)

For file-based persistence, use pywats_client:
    - pywats_client.queue.PersistentQueue for file-based queue operations

Design Principles:
    The pywats API is "memory-only" with NO file operations.
    All file I/O belongs in pywats_client.
"""

# Unified status enum (canonical source: pywats.shared.enums)
from ..shared.enums import QueueItemStatus

# Pure memory queue (NO file operations)
from .memory_queue import (
    MemoryQueue,
    BaseQueue,
    QueueItem,
    QueueHooks,
)

# Format converters (in-memory transformations)
from .formats import WSJFConverter, convert_to_wsjf, convert_from_wsxf, convert_from_wstf

__all__ = [
    # Unified status enum
    "QueueItemStatus",
    # Pure memory queue (recommended)
    "MemoryQueue",
    "BaseQueue",
    "QueueItem",
    "QueueHooks",
    # Format converters
    "WSJFConverter",
    "convert_to_wsjf",
    "convert_from_wsxf",
    "convert_from_wstf",
]

