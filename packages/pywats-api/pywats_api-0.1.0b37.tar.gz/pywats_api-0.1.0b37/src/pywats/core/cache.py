"""
Enhanced caching utilities for pyWATS API.

Provides configurable TTL-based caching for static/semi-static data like:
- Operation types
- Processes
- Levels
- Product definitions
- Asset types

This reduces server calls and improves performance.
"""
from typing import TypeVar, Generic, Optional, Callable, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import RLock
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Single cache entry with TTL tracking."""
    value: T
    cached_at: datetime
    ttl_seconds: float
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.ttl_seconds == 0:
            return False  # Never expires
        age = (datetime.now() - self.cached_at).total_seconds()
        return age > self.ttl_seconds
    
    @property
    def age_seconds(self) -> float:
        """Get age of this entry in seconds."""
        return (datetime.now() - self.cached_at).total_seconds()


@dataclass
class CacheStats:
    """Cache statistics for monitoring and optimization."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    refreshes: int = 0
    total_size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def __str__(self) -> str:
        return (
            f"CacheStats(hits={self.hits}, misses={self.misses}, "
            f"hit_rate={self.hit_rate:.2%}, evictions={self.evictions}, "
            f"refreshes={self.refreshes})"
        )


class TTLCache(Generic[T]):
    """
    Thread-safe TTL (Time-To-Live) cache with automatic expiration.
    
    Features:
    - Configurable TTL per entry
    - Automatic expiration cleanup
    - LRU eviction when max size reached
    - Cache statistics tracking
    - Thread-safe operations
    
    Example:
        >>> cache = TTLCache[Product](default_ttl=3600, max_size=1000)
        >>> cache.set("PART-001", product, ttl=7200)
        >>> product = cache.get("PART-001")
        >>> cache.clear()
    """
    
    def __init__(
        self,
        default_ttl: float = 3600.0,
        max_size: int = 1000,
        auto_cleanup: bool = True,
        cleanup_interval: float = 300.0
    ):
        """
        Initialize TTL cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            max_size: Maximum cache size (0 = unlimited)
            auto_cleanup: Automatically clean expired entries (default: True)
            cleanup_interval: Cleanup check interval in seconds (default: 5 min)
        """
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._auto_cleanup = auto_cleanup
        self._cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._lock = RLock()
        self._stats = CacheStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._last_cleanup = datetime.now()
    
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found or expired
            
        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return default
            
            if entry.is_expired:
                # Expired - remove and return default
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return default
            
            # Cache hit
            entry.hits += 1
            self._stats.hits += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        """
        with self._lock:
            # Check size limit
            if self._max_size > 0 and key not in self._cache:
                if len(self._cache) >= self._max_size:
                    # Evict least recently used (oldest)
                    self._evict_lru()
            
            effective_ttl = ttl if ttl is not None else self._default_ttl
            
            self._cache[key] = CacheEntry(
                value=value,
                cached_at=datetime.now(),
                ttl_seconds=effective_ttl
            )
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats.evictions += 1
            
            self._last_cleanup = datetime.now()
            return len(expired_keys)
    
    def _evict_lru(self) -> None:
        """Evict least recently used (oldest) entry."""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].cached_at
        )
        
        del self._cache[oldest_key]
        self._stats.evictions += 1
    
    @property
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                refreshes=self._stats.refreshes
            )
    
    def keys(self) -> list[str]:
        """Get all cache keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                self._stats.evictions += 1
                return False
            return True
    
    def __len__(self) -> int:
        """Get cache size."""
        return self.size
    
    def __repr__(self) -> str:
        return (
            f"TTLCache(size={self.size}, max_size={self._max_size}, "
            f"ttl={self._default_ttl}s, stats={self.stats})"
        )


class AsyncTTLCache(TTLCache[T]):
    """
    Async-safe TTL cache with async cleanup task.
    
    Extends TTLCache with async locking and automatic background cleanup.
    
    Example:
        >>> cache = AsyncTTLCache[Product](default_ttl=3600)
        >>> await cache.start_cleanup()  # Start background cleanup
        >>> await cache.set_async("KEY", value)
        >>> value = await cache.get_async("KEY")
        >>> await cache.stop_cleanup()  # Stop background cleanup
    """
    
    def __init__(
        self,
        default_ttl: float = 3600.0,
        max_size: int = 1000,
        auto_cleanup: bool = True,
        cleanup_interval: float = 300.0
    ):
        super().__init__(default_ttl, max_size, auto_cleanup, cleanup_interval)
        self._async_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def get_async(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Async version of get()."""
        async with self._async_lock:
            return self.get(key, default)
    
    async def set_async(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None
    ) -> None:
        """Async version of set()."""
        async with self._async_lock:
            self.set(key, value, ttl)
    
    async def delete_async(self, key: str) -> bool:
        """Async version of delete()."""
        async with self._async_lock:
            return self.delete(key)
    
    async def clear_async(self) -> None:
        """Async version of clear()."""
        async with self._async_lock:
            self.clear()
    
    async def cleanup_expired_async(self) -> int:
        """Async version of cleanup_expired()."""
        async with self._async_lock:
            return self.cleanup_expired()
    
    async def start_cleanup(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running")
            return
        
        if not self._auto_cleanup:
            logger.info("Auto cleanup disabled - not starting task")
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"Started async cache cleanup (interval={self._cleanup_interval}s)"
        )
    
    async def stop_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task is None:
            return
        
        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass
        
        self._cleanup_task = None
        logger.info("Stopped async cache cleanup")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                removed = await self.cleanup_expired_async()
                if removed > 0:
                    logger.debug(f"Cache cleanup removed {removed} expired entries")
            except asyncio.CancelledError:
                logger.debug("Cache cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    async def __aenter__(self) -> "AsyncTTLCache[T]":
        """Context manager entry - start cleanup."""
        await self.start_cleanup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stop cleanup."""
        await self.stop_cleanup()


def cached_function(
    cache: TTLCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[float] = None
):
    """
    Decorator to cache function results.
    
    Args:
        cache: TTLCache instance to use
        key_func: Function to generate cache key from args/kwargs
        ttl: Time-to-live override
    
    Example:
        >>> product_cache = TTLCache[Product](default_ttl=3600)
        >>>
        >>> @cached_function(product_cache, key_func=lambda pn: f"product:{pn}")
        >>> def get_product(part_number: str) -> Product:
        ...     return fetch_from_server(part_number)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args
                cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        wrapper.__wrapped__ = func
        return wrapper
    return decorator


async def cached_async_function(
    cache: AsyncTTLCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[float] = None
):
    """
    Decorator to cache async function results.
    
    Args:
        cache: AsyncTTLCache instance to use
        key_func: Function to generate cache key from args/kwargs
        ttl: Time-to-live override
    
    Example:
        >>> product_cache = AsyncTTLCache[Product](default_ttl=3600)
        >>>
        >>> @cached_async_function(product_cache, key_func=lambda pn: f"product:{pn}")
        >>> async def get_product(part_number: str) -> Product:
        ...     return await fetch_from_server(part_number)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args
                cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            result = await cache.get_async(cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set_async(cache_key, result, ttl=ttl)
            return result
        
        wrapper.__wrapped__ = func
        return wrapper
    return decorator
