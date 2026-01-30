"""
Shared Statistics Models

Type-safe models for statistics and processing results returned by queues,
caches, and batch operations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


@dataclass
class QueueProcessingResult:
    """
    Result of processing a queue of reports.
    
    Returned by queue.process_all() and service.process_queue().
    
    Attributes:
        success: Number of reports successfully submitted
        failed: Number of reports that failed to submit
        skipped: Number of reports skipped (e.g., already processed)
        errors: List of error messages for failed reports
        
    Example:
        >>> result = queue.process_all()
        >>> print(f"Processed: {result.success} success, {result.failed} failed")
        >>> if result.errors:
        ...     for error in result.errors:
        ...         print(f"  Error: {error}")
    """
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        """Total number of reports processed."""
        return self.success + self.failed + self.skipped
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return (self.success / self.total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "success": self.success,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "total": self.total,
        }


@dataclass
class QueueStats:
    """
    Statistics about a queue's current state.
    
    Returned by queue.get_stats().
    
    Attributes:
        pending: Number of items waiting to be processed
        processing: Number of items currently being processed
        completed: Number of items successfully completed
        failed: Number of items that failed
        
    Example:
        >>> stats = queue.get_stats()
        >>> print(f"Queue: {stats.pending} pending, {stats.processing} processing")
    """
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    
    @property
    def total(self) -> int:
        """Total number of items in queue."""
        return self.pending + self.processing + self.completed + self.failed
    
    @property
    def active(self) -> int:
        """Number of items not yet completed (pending + processing)."""
        return self.pending + self.processing
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for backward compatibility."""
        return {
            "pending": self.pending,
            "processing": self.processing,
            "completed": self.completed,
            "failed": self.failed,
            "total": self.total,
        }


@dataclass
class CacheStats:
    """
    Statistics about a cache's current state.
    
    Returned by cache_stats property.
    
    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        size: Current number of items in cache
        max_size: Maximum cache capacity
        
    Example:
        >>> stats = service.cache_stats
        >>> print(f"Cache hit rate: {stats.hit_rate:.1f}%")
    """
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: Optional[int] = None
    
    @property
    def total_requests(self) -> int:
        """Total number of cache lookups."""
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        """Hit rate as percentage (0-100)."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    @property
    def utilization(self) -> Optional[float]:
        """Cache utilization as percentage (0-100), or None if unbounded."""
        if self.max_size is None or self.max_size == 0:
            return None
        return (self.size / self.max_size) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
        }


@dataclass  
class BatchResult:
    """
    Result of a batch operation.
    
    Returned by batch submit operations.
    
    Attributes:
        total: Total number of items in batch
        success: Number of items successfully processed
        failed: Number of items that failed
        results: Individual results per item
        errors: Error messages keyed by item index
        
    Example:
        >>> result = api.report.submit_batch(reports)
        >>> print(f"Batch: {result.success}/{result.total} succeeded")
    """
    total: int = 0
    success: int = 0
    failed: int = 0
    results: List[Any] = field(default_factory=list)
    errors: Dict[int, str] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return (self.success / self.total) * 100
    
    @property
    def all_succeeded(self) -> bool:
        """True if all items succeeded."""
        return self.failed == 0 and self.total > 0
