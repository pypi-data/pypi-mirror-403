"""
Request batching utilities for bulk operations.

Provides batching support to reduce network round-trips when performing
bulk operations like:
- Querying multiple reports
- Submitting multiple units
- Fetching multiple products

This improves performance by combining multiple requests into fewer calls.
"""
from typing import TypeVar, Generic, List, Callable, Awaitable, Optional, Dict, Any
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    max_batch_size: int = 100
    max_wait_time: float = 0.1  # seconds
    max_concurrent_batches: int = 5


@dataclass
class BatchItem(Generic[T, R]):
    """Single item in a batch request."""
    item: T
    future: asyncio.Future[R] = field(default_factory=asyncio.Future)
    timestamp: datetime = field(default_factory=datetime.now)


class RequestBatcher(Generic[T, R]):
    """
    Batch multiple individual requests into bulk operations.
    
    Collects requests over a short time window and processes them
    as a single bulk operation, reducing network overhead.
    
    Example:
        >>> # Create batcher for product lookups
        >>> async def bulk_get_products(part_numbers: List[str]) -> List[Product]:
        ...     return await api.product.get_products_batch(part_numbers)
        >>>
        >>> batcher = RequestBatcher(
        ...     bulk_func=bulk_get_products,
        ...     config=BatchConfig(max_batch_size=50, max_wait_time=0.1)
        ... )
        >>>
        >>> # Start batcher
        >>> await batcher.start()
        >>>
        >>> # Individual requests get automatically batched
        >>> product1 = await batcher.add("PART-001")
        >>> product2 = await batcher.add("PART-002")
        >>> # Both requests processed in same bulk call
        >>>
        >>> await batcher.stop()
    """
    
    def __init__(
        self,
        bulk_func: Callable[[List[T]], Awaitable[List[R]]],
        config: Optional[BatchConfig] = None
    ):
        """
        Initialize request batcher.
        
        Args:
            bulk_func: Async function that processes a batch of items
                       and returns results in the same order
            config: Batch configuration (default: BatchConfig())
        """
        self._bulk_func = bulk_func
        self._config = config or BatchConfig()
        
        self._pending: List[BatchItem[T, R]] = []
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        self._stats = {
            'total_items': 0,
            'total_batches': 0,
            'total_wait_time': 0.0,
            'max_batch_size': 0
        }
    
    async def start(self) -> None:
        """Start the batch processor."""
        if self._running:
            logger.warning("Batcher already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Request batcher started")
    
    async def stop(self) -> None:
        """Stop the batch processor and flush pending items."""
        if not self._running:
            return
        
        # Process any remaining items
        await self._flush()
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Request batcher stopped. Stats: {self._stats}")
    
    async def add(self, item: T) -> R:
        """
        Add item to batch queue and wait for result.
        
        Args:
            item: Item to add to batch
            
        Returns:
            Result from bulk processing
        """
        if not self._running:
            raise RuntimeError("Batcher not started. Call start() first.")
        
        batch_item = BatchItem[T, R](item=item)
        
        async with self._lock:
            self._pending.append(batch_item)
            self._stats['total_items'] += 1
        
        # Wait for result
        return await batch_item.future
    
    async def _flush(self) -> None:
        """Process all pending items immediately."""
        async with self._lock:
            if not self._pending:
                return
            
            batch = self._pending
            self._pending = []
        
        await self._process_batch(batch)
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                # Wait for max_wait_time
                await asyncio.sleep(self._config.max_wait_time)
                
                # Check if we should process
                should_process = False
                async with self._lock:
                    if self._pending:
                        # Process if we have max batch size or waited long enough
                        if len(self._pending) >= self._config.max_batch_size:
                            should_process = True
                        elif self._pending:
                            oldest = self._pending[0].timestamp
                            age = (datetime.now() - oldest).total_seconds()
                            if age >= self._config.max_wait_time:
                                should_process = True
                
                if should_process:
                    await self._flush()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
    
    async def _process_batch(self, batch: List[BatchItem[T, R]]) -> None:
        """
        Process a batch of items.
        
        Args:
            batch: List of batch items to process
        """
        if not batch:
            return
        
        batch_size = len(batch)
        items = [b.item for b in batch]
        
        try:
            # Call bulk function
            results = await self._bulk_func(items)
            
            # Validate results
            if len(results) != len(items):
                raise ValueError(
                    f"Bulk function returned {len(results)} results "
                    f"but expected {len(items)}"
                )
            
            # Set results on futures
            for batch_item, result in zip(batch, results):
                if not batch_item.future.done():
                    batch_item.future.set_result(result)
            
            # Update stats
            self._stats['total_batches'] += 1
            self._stats['max_batch_size'] = max(
                self._stats['max_batch_size'],
                batch_size
            )
            
            logger.debug(f"Processed batch of {batch_size} items")
            
        except Exception as e:
            # Set exception on all futures
            for batch_item in batch:
                if not batch_item.future.done():
                    batch_item.future.set_exception(e)
            
            logger.error(f"Error processing batch: {e}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get batcher statistics."""
        return dict(self._stats)
    
    async def __aenter__(self) -> "RequestBatcher[T, R]":
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.stop()


class ChunkedBatcher(Generic[T, R]):
    """
    Process large lists in chunks to avoid overwhelming the server.
    
    Unlike RequestBatcher which batches over time, ChunkedBatcher
    splits a known list into manageable chunks.
    
    Example:
        >>> async def process_chunk(items: List[str]) -> List[Product]:
        ...     return await api.product.get_products_batch(items)
        >>>
        >>> batcher = ChunkedBatcher(
        ...     process_func=process_chunk,
        ...     chunk_size=50,
        ...     max_concurrent=5
        ... )
        >>>
        >>> # Process 1000 items in chunks of 50
        >>> results = await batcher.process_all(part_numbers_1000)
    """
    
    def __init__(
        self,
        process_func: Callable[[List[T]], Awaitable[List[R]]],
        chunk_size: int = 100,
        max_concurrent: int = 5
    ):
        """
        Initialize chunked batcher.
        
        Args:
            process_func: Function to process one chunk
            chunk_size: Size of each chunk (default: 100)
            max_concurrent: Max concurrent chunk operations (default: 5)
        """
        self._process_func = process_func
        self._chunk_size = chunk_size
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _process_chunk(self, chunk: List[T]) -> List[R]:
        """Process one chunk with semaphore limiting."""
        async with self._semaphore:
            return await self._process_func(chunk)
    
    async def process_all(self, items: List[T]) -> List[R]:
        """
        Process all items in chunks.
        
        Args:
            items: List of items to process
            
        Returns:
            List of results (same order as input)
        """
        if not items:
            return []
        
        # Split into chunks
        chunks = [
            items[i:i + self._chunk_size]
            for i in range(0, len(items), self._chunk_size)
        ]
        
        logger.debug(
            f"Processing {len(items)} items in {len(chunks)} chunks "
            f"(size={self._chunk_size})"
        )
        
        # Process all chunks concurrently (with semaphore limit)
        tasks = [self._process_chunk(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks)
        
        # Flatten results
        results: List[R] = []
        for chunk_result in chunk_results:
            results.extend(chunk_result)
        
        return results


async def batch_map(
    items: List[T],
    func: Callable[[T], Awaitable[R]],
    batch_size: int = 100,
    max_concurrent: int = 10
) -> List[R]:
    """
    Map an async function over a list with batching and concurrency control.
    
    Similar to asyncio.gather but with batching and concurrency limits.
    
    Args:
        items: Items to process
        func: Async function to apply to each item
        batch_size: Process in batches of this size
        max_concurrent: Max concurrent operations
        
    Returns:
        List of results (same order as input)
        
    Example:
        >>> async def fetch_product(pn: str) -> Product:
        ...     return await api.product.get_product(pn)
        >>>
        >>> # Process 1000 products with controlled concurrency
        >>> products = await batch_map(
        ...     part_numbers,
        ...     fetch_product,
        ...     batch_size=50,
        ...     max_concurrent=10
        ... )
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_func(item: T) -> R:
        async with semaphore:
            return await func(item)
    
    # Process in chunks to avoid creating too many tasks at once
    results: List[R] = []
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        tasks = [bounded_func(item) for item in chunk]
        chunk_results = await asyncio.gather(*tasks)
        results.extend(chunk_results)
    
    return results
