"""Batch execution utilities for concurrent operations.

This module provides utilities for executing multiple operations concurrently
with configurable concurrency limits and comprehensive error handling.

Usage:
    from pywats.core.batch import batch_execute, BatchConfig

    # Execute multiple operations concurrently
    results = batch_execute(
        keys=["PN-001", "PN-002", "PN-003"],
        operation=lambda pn: api.product.get_product(pn),
        max_workers=10,
    )
    
    # Process results
    for key, result in zip(keys, results):
        if result.is_success:
            print(f"{key}: {result.value.description}")
        else:
            print(f"{key}: FAILED - {result.message}")

Key Features:
- Concurrent execution using ThreadPoolExecutor
- Configurable concurrency limits (default: 10)
- Results preserve input order
- Individual failures don't break the batch
- Progress callback support
- Type-safe Result[T] return type
"""
from typing import TypeVar, Callable, List, Optional, Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pywats.shared.result import Success, Failure, Result
import logging

T = TypeVar("T")
K = TypeVar("K")

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch operations.
    
    Attributes:
        max_workers: Maximum concurrent operations (default: 10)
        fail_fast: Stop on first error if True (default: False)
        timeout: Timeout per operation in seconds (default: None)
        
    Example:
        >>> config = BatchConfig(max_workers=5, fail_fast=True)
        >>> results = batch_execute(keys, operation, config=config)
    """
    max_workers: int = 10
    fail_fast: bool = False
    timeout: Optional[float] = None
    
    def __post_init__(self):
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_workers > 100:
            logger.warning(
                f"High concurrency ({self.max_workers}) may cause rate limiting. "
                "Consider using max_workers <= 20."
            )


def batch_execute(
    keys: List[K],
    operation: Callable[[K], T],
    max_workers: int = 10,
    on_progress: Optional[Callable[[int, int], None]] = None,
    config: Optional[BatchConfig] = None,
) -> List[Result[T]]:
    """Execute batch operations concurrently with error handling.
    
    Executes the given operation for each key concurrently using a thread pool.
    Results are returned in the same order as the input keys.
    
    Args:
        keys: List of input keys to process
        operation: Function to call for each key, returns T
        max_workers: Maximum concurrent operations (default: 10, overridden by config)
        on_progress: Optional callback (completed, total) for progress tracking
        config: Optional BatchConfig for advanced settings
        
    Returns:
        List of Result[T] in same order as input keys.
        Each result is either Success(value) or Failure(error_code, message).
        
    Example:
        >>> def get_product(part_number: str) -> Product:
        ...     return api.product.get_product(part_number)
        ...
        >>> results = batch_execute(
        ...     keys=["PN-001", "PN-002", "PN-003"],
        ...     operation=get_product,
        ...     max_workers=5,
        ... )
        >>> 
        >>> for pn, result in zip(["PN-001", "PN-002", "PN-003"], results):
        ...     if result.is_success:
        ...         print(f"{pn}: {result.value.description}")
        ...     else:
        ...         print(f"{pn}: Error - {result.message}")
        
    Note:
        - Results preserve input order
        - Individual failures don't stop other operations (unless fail_fast=True)
        - Use config.fail_fast=True to stop on first error
    """
    if not keys:
        return []
    
    # Use config if provided, otherwise use max_workers parameter
    effective_config = config or BatchConfig(max_workers=max_workers)
    workers = effective_config.max_workers
    
    # Pre-allocate results list to maintain order
    results: List[Optional[Result[T]]] = [None] * len(keys)
    completed_count = 0
    first_error: Optional[Exception] = None
    
    def execute_one(index: int, key: K) -> tuple[int, Result[T]]:
        """Execute operation for a single key and return indexed result."""
        try:
            value = operation(key)
            if value is None:
                return index, Failure(
                    error_code="NOT_FOUND",
                    message=f"Operation returned None for key: {key}",
                    details={"key": str(key), "index": index}
                )
            return index, Success(value=value)
        except Exception as e:
            return index, Failure(
                error_code=_classify_exception(e),
                message=str(e),
                details={
                    "key": str(key),
                    "index": index,
                    "exception_type": type(e).__name__
                }
            )
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(execute_one, i, key): i
            for i, key in enumerate(keys)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            try:
                index, result = future.result(timeout=effective_config.timeout)
                results[index] = result
                
                # Update progress
                completed_count += 1
                if on_progress:
                    on_progress(completed_count, len(keys))
                
                # Check fail_fast
                if effective_config.fail_fast and result.is_failure:
                    first_error = Exception(result.message)
                    # Cancel remaining futures
                    for f in future_to_index:
                        f.cancel()
                    break
                    
            except Exception as e:
                # Handle timeout or other execution errors
                idx = future_to_index[future]
                results[idx] = Failure(
                    error_code="OPERATION_FAILED",
                    message=f"Execution error: {e}",
                    details={"index": idx, "exception_type": type(e).__name__}
                )
                completed_count += 1
                if on_progress:
                    on_progress(completed_count, len(keys))
    
    # Fill any remaining None slots (from cancelled futures) with failures
    for i, result in enumerate(results):
        if result is None:
            results[i] = Failure(
                error_code="OPERATION_FAILED",
                message="Operation was cancelled (fail_fast triggered)",
                details={"key": str(keys[i]), "index": i}
            )
    
    logger.debug(
        f"Batch completed: {sum(1 for r in results if r.is_success)}/{len(keys)} succeeded"
    )
    
    return results


def batch_execute_with_retry(
    keys: List[K],
    operation: Callable[[K], T],
    max_workers: int = 10,
    max_retries: int = 3,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[Result[T]]:
    """Execute batch operations with automatic retry for failed items.
    
    First attempts all operations. Then retries failed operations up to
    max_retries times with exponential backoff.
    
    Args:
        keys: List of input keys to process
        operation: Function to call for each key
        max_workers: Maximum concurrent operations
        max_retries: Maximum retry attempts for failed items
        on_progress: Optional progress callback
        
    Returns:
        List of Result[T] in same order as input keys
        
    Example:
        >>> results = batch_execute_with_retry(
        ...     keys=part_numbers,
        ...     operation=api.product.get_product,
        ...     max_retries=3,
        ... )
    """
    import time
    
    results = batch_execute(keys, operation, max_workers, on_progress)
    
    for attempt in range(max_retries):
        # Find failed indices
        failed_indices = [
            i for i, r in enumerate(results) 
            if r.is_failure and _is_retryable(r)
        ]
        
        if not failed_indices:
            break
        
        # Exponential backoff
        delay = 0.5 * (2 ** attempt)
        logger.info(
            f"Retry attempt {attempt + 1}/{max_retries}: "
            f"{len(failed_indices)} items, waiting {delay}s"
        )
        time.sleep(delay)
        
        # Retry failed items
        failed_keys = [keys[i] for i in failed_indices]
        retry_results = batch_execute(failed_keys, operation, max_workers)
        
        # Update results
        for idx, retry_result in zip(failed_indices, retry_results):
            results[idx] = retry_result
    
    return results


def collect_successes(results: List[Result[T]]) -> List[T]:
    """Extract successful values from batch results.
    
    Args:
        results: List of Result[T] from batch_execute
        
    Returns:
        List of successful values (failures are excluded)
        
    Example:
        >>> results = batch_execute(keys, operation)
        >>> products = collect_successes(results)
        >>> print(f"Got {len(products)} products")
    """
    return [r.value for r in results if r.is_success]


def collect_failures(results: List[Result[T]]) -> List[Failure]:
    """Extract failures from batch results.
    
    Args:
        results: List of Result[T] from batch_execute
        
    Returns:
        List of Failure objects
        
    Example:
        >>> results = batch_execute(keys, operation)
        >>> failures = collect_failures(results)
        >>> for f in failures:
        ...     print(f"Error: {f.error_code} - {f.message}")
    """
    return [r for r in results if r.is_failure]


def partition_results(
    results: List[Result[T]]
) -> tuple[List[T], List[Failure]]:
    """Partition results into successes and failures.
    
    Args:
        results: List of Result[T] from batch_execute
        
    Returns:
        Tuple of (successes, failures)
        
    Example:
        >>> results = batch_execute(keys, operation)
        >>> successes, failures = partition_results(results)
        >>> print(f"Success: {len(successes)}, Failed: {len(failures)}")
    """
    return collect_successes(results), collect_failures(results)


def _classify_exception(exc: Exception) -> str:
    """Classify an exception into an error code."""
    exc_type = type(exc).__name__
    
    # Map common exceptions to error codes
    mapping = {
        "ConnectionError": "CONNECTION_ERROR",
        "Timeout": "TIMEOUT",
        "TimeoutError": "TIMEOUT",
        "HTTPError": "API_ERROR",
        "ValidationError": "INVALID_INPUT",
        "ValueError": "INVALID_INPUT",
        "KeyError": "NOT_FOUND",
        "NotFoundError": "NOT_FOUND",
        "AuthenticationError": "UNAUTHORIZED",
        "AuthorizationError": "FORBIDDEN",
    }
    
    return mapping.get(exc_type, "OPERATION_FAILED")


def _is_retryable(failure: Failure) -> bool:
    """Determine if a failure is retryable."""
    retryable_codes = {
        "CONNECTION_ERROR",
        "TIMEOUT",
        "API_ERROR",
        "OPERATION_FAILED",
    }
    return failure.error_code in retryable_codes


__all__ = [
    "batch_execute",
    "batch_execute_with_retry",
    "BatchConfig",
    "collect_successes",
    "collect_failures",
    "partition_results",
]
