"""Pagination utilities for iterating over large result sets.

This module provides utilities for automatic pagination, allowing users to
iterate over large datasets without manually handling page boundaries.

Usage:
    from pywats.core.pagination import paginate, PaginationConfig

    # Iterate over all SCIM users
    for user in paginate(
        fetch_page=lambda start, count: api.scim.get_users(start_index=start, count=count),
        get_items=lambda response: response.resources,
        get_total=lambda response: response.total_results,
        page_size=100,
    ):
        print(user.display_name)

Key Features:
- Memory-efficient iteration (doesn't load all pages at once)
- Automatic page boundary handling
- Early termination support (break works)
- Configurable page sizes
- Progress tracking support
"""
from typing import TypeVar, Callable, Iterator, Optional, Any, List, Generic
from dataclasses import dataclass
import logging

T = TypeVar("T")
R = TypeVar("R")  # Response type

logger = logging.getLogger(__name__)


@dataclass
class PaginationConfig:
    """Configuration for pagination behavior.
    
    Attributes:
        page_size: Number of items per page (default: 100)
        max_items: Maximum total items to retrieve (default: None = unlimited)
        start_index: Starting index for pagination (default: 1 for SCIM, 0 for others)
        
    Example:
        >>> config = PaginationConfig(page_size=50, max_items=1000)
    """
    page_size: int = 100
    max_items: Optional[int] = None
    start_index: int = 1  # SCIM uses 1-based indexing
    
    def __post_init__(self):
        if self.page_size < 1:
            raise ValueError("page_size must be at least 1")
        if self.page_size > 1000:
            logger.warning(
                f"Large page_size ({self.page_size}) may cause slow responses. "
                "Consider using page_size <= 200."
            )


@dataclass 
class PaginationState:
    """Tracks the current state of pagination.
    
    Attributes:
        current_index: Current position in the result set
        items_retrieved: Total items retrieved so far
        total_items: Total items available (if known)
        pages_retrieved: Number of pages retrieved
        is_complete: Whether pagination has completed
    """
    current_index: int = 0
    items_retrieved: int = 0
    total_items: Optional[int] = None
    pages_retrieved: int = 0
    is_complete: bool = False


def paginate(
    fetch_page: Callable[[int, int], R],
    get_items: Callable[[R], List[T]],
    get_total: Optional[Callable[[R], int]] = None,
    page_size: int = 100,
    start_index: int = 1,
    max_items: Optional[int] = None,
    on_page: Optional[Callable[[int, int, Optional[int]], None]] = None,
) -> Iterator[T]:
    """Iterate over paginated results with automatic page fetching.
    
    This generator fetches pages on-demand and yields individual items,
    handling page boundaries transparently.
    
    Args:
        fetch_page: Function that fetches a page, takes (start_index, count)
        get_items: Function to extract items from a page response
        get_total: Optional function to get total count from response
        page_size: Number of items per page (default: 100)
        start_index: Starting index (default: 1 for SCIM-style)
        max_items: Maximum items to retrieve (default: unlimited)
        on_page: Optional callback (page_num, items_so_far, total)
        
    Yields:
        Individual items from each page
        
    Example:
        >>> # Iterate over SCIM users
        >>> for user in paginate(
        ...     fetch_page=lambda s, c: scim_service.get_users(start_index=s, count=c),
        ...     get_items=lambda r: r.resources,
        ...     get_total=lambda r: r.total_results,
        ...     page_size=100,
        ... ):
        ...     print(user.display_name)
        ...     if user.active:
        ...         break  # Early termination works!
        
    Note:
        - Memory-efficient: only one page loaded at a time
        - Supports early termination with break
        - Works with any paginated API that supports start/count
    """
    current_index = start_index
    items_retrieved = 0
    total_items: Optional[int] = None
    page_number = 0
    
    while True:
        # Check max_items limit
        if max_items is not None and items_retrieved >= max_items:
            logger.debug(f"Reached max_items limit ({max_items})")
            break
        
        # Adjust page size for last page if max_items set
        effective_page_size = page_size
        if max_items is not None:
            remaining = max_items - items_retrieved
            effective_page_size = min(page_size, remaining)
        
        # Fetch page
        try:
            response = fetch_page(current_index, effective_page_size)
        except Exception as e:
            logger.error(f"Error fetching page at index {current_index}: {e}")
            raise
        
        # Extract items
        items = get_items(response)
        if not items:
            logger.debug(f"Empty page at index {current_index}, stopping")
            break
        
        # Get total if available
        if get_total is not None and total_items is None:
            try:
                total_items = get_total(response)
            except Exception:
                pass  # Total not available
        
        page_number += 1
        
        # Progress callback
        if on_page:
            on_page(page_number, items_retrieved + len(items), total_items)
        
        # Yield items
        for item in items:
            yield item
            items_retrieved += 1
            
            # Check max_items after each item
            if max_items is not None and items_retrieved >= max_items:
                return
        
        # Check if we've reached the end
        if len(items) < effective_page_size:
            logger.debug(
                f"Partial page ({len(items)} < {effective_page_size}), stopping"
            )
            break
        
        if total_items is not None and items_retrieved >= total_items:
            logger.debug(f"Reached total_items ({total_items}), stopping")
            break
        
        # Move to next page
        current_index += len(items)
    
    logger.debug(
        f"Pagination complete: {items_retrieved} items in {page_number} pages"
    )


def paginate_all(
    fetch_page: Callable[[int, int], R],
    get_items: Callable[[R], List[T]],
    get_total: Optional[Callable[[R], int]] = None,
    page_size: int = 100,
    start_index: int = 1,
    max_items: Optional[int] = None,
) -> List[T]:
    """Fetch all pages and return as a single list.
    
    Convenience function that collects all paginated results into a list.
    Use with caution for large datasets as all items are loaded into memory.
    
    Args:
        fetch_page: Function that fetches a page
        get_items: Function to extract items from response
        get_total: Optional function to get total count
        page_size: Items per page
        start_index: Starting index
        max_items: Maximum items to retrieve
        
    Returns:
        List of all items
        
    Warning:
        This loads all items into memory. For large datasets,
        use `paginate()` generator instead.
        
    Example:
        >>> all_users = paginate_all(
        ...     fetch_page=lambda s, c: api.scim.get_users(start_index=s, count=c),
        ...     get_items=lambda r: r.resources,
        ...     max_items=1000,  # Limit for safety
        ... )
    """
    return list(paginate(
        fetch_page=fetch_page,
        get_items=get_items,
        get_total=get_total,
        page_size=page_size,
        start_index=start_index,
        max_items=max_items,
    ))


class Paginator(Generic[T, R]):
    """Reusable paginator for a specific API endpoint.
    
    Encapsulates pagination logic for a specific endpoint, making it
    easy to iterate multiple times with different configurations.
    
    Example:
        >>> user_paginator = Paginator(
        ...     fetch_page=lambda s, c: api.scim.get_users(start_index=s, count=c),
        ...     get_items=lambda r: r.resources,
        ...     get_total=lambda r: r.total_results,
        ... )
        >>> 
        >>> # First iteration
        >>> for user in user_paginator.iterate(page_size=50):
        ...     print(user.display_name)
        >>> 
        >>> # Second iteration with different settings
        >>> active_users = list(user_paginator.iterate(max_items=100))
    """
    
    def __init__(
        self,
        fetch_page: Callable[[int, int], R],
        get_items: Callable[[R], List[T]],
        get_total: Optional[Callable[[R], int]] = None,
        start_index: int = 1,
    ):
        """Initialize paginator.
        
        Args:
            fetch_page: Function that fetches a page (start, count) -> Response
            get_items: Function to extract items from response
            get_total: Optional function to get total count from response
            start_index: Starting index (default: 1 for SCIM)
        """
        self._fetch_page = fetch_page
        self._get_items = get_items
        self._get_total = get_total
        self._start_index = start_index
    
    def iterate(
        self,
        page_size: int = 100,
        max_items: Optional[int] = None,
        on_page: Optional[Callable[[int, int, Optional[int]], None]] = None,
    ) -> Iterator[T]:
        """Iterate over all items with pagination.
        
        Args:
            page_size: Items per page
            max_items: Maximum items to retrieve
            on_page: Optional progress callback
            
        Yields:
            Individual items
        """
        return paginate(
            fetch_page=self._fetch_page,
            get_items=self._get_items,
            get_total=self._get_total,
            page_size=page_size,
            start_index=self._start_index,
            max_items=max_items,
            on_page=on_page,
        )
    
    def all(
        self,
        page_size: int = 100,
        max_items: Optional[int] = None,
    ) -> List[T]:
        """Fetch all items into a list.
        
        Args:
            page_size: Items per page
            max_items: Maximum items to retrieve
            
        Returns:
            List of all items
        """
        return list(self.iterate(page_size=page_size, max_items=max_items))
    
    def count(self) -> Optional[int]:
        """Get total count without fetching all items.
        
        Returns:
            Total count if available, None otherwise
        """
        if self._get_total is None:
            return None
        try:
            response = self._fetch_page(self._start_index, 1)
            return self._get_total(response)
        except Exception:
            return None


__all__ = [
    "paginate",
    "paginate_all",
    "Paginator",
    "PaginationConfig",
    "PaginationState",
]
