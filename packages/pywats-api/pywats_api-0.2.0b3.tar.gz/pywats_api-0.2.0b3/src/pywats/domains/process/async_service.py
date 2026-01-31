"""Async Process service - business logic layer.

Uses the WATS API for process operations with enhanced TTL caching.

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import asyncio
import logging

from .async_repository import AsyncProcessRepository
from .models import ProcessInfo, RepairOperationConfig, RepairCategory
from ...core.cache import AsyncTTLCache
from ...shared.stats import CacheStats

logger = logging.getLogger(__name__)


class AsyncProcessService:
    """
    Async Process business logic layer with enhanced TTL caching.
    
    Uses AsyncTTLCache for automatic cache expiration and management.
    Cache reduces server calls for static data like operation types.
    
    Example:
        # Get a test operation by code
        process = await api.process.get_test_operation(100)
        
        # Get a test operation by name
        process = await api.process.get_test_operation("End of line test")
        
        # Get a repair operation
        repair = await api.process.get_repair_operation(500)
        
        # Force cache refresh
        await api.process.refresh()
        
        # View cache statistics
        print(api.process.cache_stats)
    """
    
    # Default cache refresh interval (5 minutes = 300 seconds)
    DEFAULT_CACHE_TTL = 300
    
    # Default process codes (WATS convention)
    DEFAULT_TEST_PROCESS_CODE = 100
    DEFAULT_REPAIR_PROCESS_CODE = 500
    
    def __init__(
        self, 
        repository: AsyncProcessRepository,
        cache_ttl: float = DEFAULT_CACHE_TTL,
        max_cache_size: int = 10000
    ) -> None:
        """
        Initialize service with repository and enhanced caching.
        
        Args:
            repository: AsyncProcessRepository instance
            cache_ttl: Cache time-to-live in seconds (default: 300)
            max_cache_size: Maximum cache entries (default: 10000)
        """
        self._repository = repository
        self._cache_ttl = cache_ttl
        
        # Enhanced TTL cache (replaces simple in-memory list)
        self._cache = AsyncTTLCache[List[ProcessInfo]](
            default_ttl=cache_ttl,
            max_size=max_cache_size,
            auto_cleanup=True,
            cleanup_interval=60.0  # Cleanup every minute
        )
        
        self._lock = asyncio.Lock()
        self._cache_started = False

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def _ensure_cache_started(self) -> None:
        """Ensure background cache cleanup is running."""
        if not self._cache_started:
            async with self._lock:
                if not self._cache_started:
                    await self._cache.start_cleanup()
                    self._cache_started = True

    @property
    def cache_ttl(self) -> float:
        """Get the cache TTL in seconds."""
        return self._cache_ttl
    
    @property
    def refresh_interval(self) -> float:
        """Get the cache refresh interval in seconds (alias for cache_ttl)."""
        return self._cache_ttl
    
    @refresh_interval.setter
    def refresh_interval(self, value: float) -> None:
        """Set the cache refresh interval in seconds."""
        self._cache_ttl = value
        self._cache._default_ttl = value
    
    @property
    def last_refresh(self) -> Optional[datetime]:
        """Get the timestamp of the last cache refresh."""
        # Check if processes are cached and get their entry time
        entry = self._cache._cache.get("processes")
        if entry:
            return entry.cached_at
        return None

    @property
    def cache_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats with hit/miss counts and rates
            
        Example:
            >>> stats = service.cache_stats
            >>> print(f"Hit rate: {stats.hit_rate:.1f}%")
        """
        internal_stats = self._cache.stats
        return CacheStats(
            hits=internal_stats.hits,
            misses=internal_stats.misses,
            size=self._cache.size,
            max_size=None  # TTL cache doesn't have max size
        )

    async def refresh(self) -> None:
        """
        Force refresh the process cache from the server.
        
        Thread-safe operation that fetches fresh data from the API
        and updates the cache.
        """
        await self._ensure_cache_started()
        
        processes = await self._repository.get_processes()
        await self._cache.set_async('processes', processes)
        
        logger.info(f"Process cache refreshed ({len(processes)} processes)")

    async def _get_cached_processes(self) -> List[ProcessInfo]:
        """Get processes from cache or fetch if not cached."""
        await self._ensure_cache_started()
        
        # Try to get from cache
        processes = await self._cache.get_async('processes')
        
        if processes is None:
            # Cache miss - fetch from server
            logger.debug("Process cache miss - fetching from server")
            await self.refresh()
            processes = await self._cache.get_async('processes')
        
        return processes if processes is not None else []

    async def clear_cache(self) -> None:
        """Clear the process cache."""
        await self._cache.clear_async()
        logger.info("Process cache cleared")
    async def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes (cached with TTL).
        
        Returns:
            List of ProcessInfo objects
        """
        processes = await self._get_cached_processes()
        return list(processes)  # Return copy to prevent modification

    async def get_test_operations(self) -> List[ProcessInfo]:
        """
        Get all test operations (isTestOperation=true).
        
        Returns:
            List of test operation ProcessInfo objects
        """
        processes = await self.get_processes()
        return [p for p in processes if p.is_test_operation]

    async def get_repair_operations(self) -> List[ProcessInfo]:
        """
        Get all repair operations (isRepairOperation=true).
        
        Returns:
            List of repair operation ProcessInfo objects
        """
        processes = await self.get_processes()
        return [p for p in processes if p.is_repair_operation]

    async def get_wip_operations(self) -> List[ProcessInfo]:
        """
        Get all WIP operations (isWipOperation=true).
        
        Returns:
            List of WIP operation ProcessInfo objects
        """
        processes = await self.get_processes()
        return [p for p in processes if p.is_wip_operation]

    # =========================================================================
    # Process Lookup (Read-Only)
    # =========================================================================

    async def get_process_by_code(self, code: int) -> Optional[ProcessInfo]:
        """
        Get a process by its code.
        
        Args:
            code: Process code (e.g., 100, 500)
            
        Returns:
            ProcessInfo or None if not found
        """
        processes = await self.get_processes()
        for p in processes:
            if p.code == code:
                return p
        return None

    async def get_process_by_name(self, name: str) -> Optional[ProcessInfo]:
        """
        Get a process by its name (case-insensitive).
        
        Args:
            name: Process name
            
        Returns:
            ProcessInfo or None if not found
        """
        name_lower = name.lower()
        processes = await self.get_processes()
        for p in processes:
            if p.name and p.name.lower() == name_lower:
                return p
        return None

    async def get_test_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """
        Get a test operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo or None if not found
        """
        if isinstance(identifier, int):
            process = await self.get_process_by_code(identifier)
        else:
            process = await self.get_process_by_name(identifier)
        
        if process and process.is_test_operation:
            return process
        return None

    async def get_repair_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """
        Get a repair operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo or None if not found
        """
        if isinstance(identifier, int):
            process = await self.get_process_by_code(identifier)
        else:
            process = await self.get_process_by_name(identifier)
        
        if process and process.is_repair_operation:
            return process
        return None

    async def get_wip_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """
        Get a WIP operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo or None if not found
        """
        if isinstance(identifier, int):
            process = await self.get_process_by_code(identifier)
        else:
            process = await self.get_process_by_name(identifier)
        
        if process and process.is_wip_operation:
            return process
        return None

    async def get_process(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """
        Get any process by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo or None if not found
        """
        if isinstance(identifier, int):
            return await self.get_process_by_code(identifier)
        else:
            return await self.get_process_by_name(identifier)

    # =========================================================================
    # Validation Methods
    # =========================================================================

    async def is_valid_test_operation(self, code: int) -> bool:
        """
        Check if a code is a valid test operation.
        
        Args:
            code: Process code to validate
            
        Returns:
            True if it's a valid test operation code
        """
        process = await self.get_process_by_code(code)
        return process is not None and process.is_test_operation

    async def is_valid_repair_operation(self, code: int) -> bool:
        """
        Check if a code is a valid repair operation.
        
        Args:
            code: Process code to validate
            
        Returns:
            True if it's a valid repair operation code
        """
        process = await self.get_process_by_code(code)
        return process is not None and process.is_repair_operation

    async def is_valid_wip_operation(self, code: int) -> bool:
        """
        Check if a code is a valid WIP operation.
        
        Args:
            code: Process code to validate
            
        Returns:
            True if it's a valid WIP operation code
        """
        process = await self.get_process_by_code(code)
        return process is not None and process.is_wip_operation

    async def get_default_test_code(self) -> int:
        """
        Get the default test operation code.
        
        First checks if code 100 exists, otherwise returns the first
        available test operation code.
        
        Returns:
            Default test operation code (typically 100)
        """
        # Try standard code first
        if await self.is_valid_test_operation(self.DEFAULT_TEST_PROCESS_CODE):
            return self.DEFAULT_TEST_PROCESS_CODE
        
        # Fallback to first available test operation
        test_ops = await self.get_test_operations()
        if test_ops:
            return test_ops[0].code
        
        return self.DEFAULT_TEST_PROCESS_CODE  # Return default even if not found

    async def get_default_repair_code(self) -> int:
        """
        Get the default repair operation code.
        
        First checks if code 500 exists, otherwise returns the first
        available repair operation code.
        
        Returns:
            Default repair operation code (typically 500)
        """
        # Try standard code first
        if await self.is_valid_repair_operation(self.DEFAULT_REPAIR_PROCESS_CODE):
            return self.DEFAULT_REPAIR_PROCESS_CODE
        
        # Fallback to first available repair operation
        repair_ops = await self.get_repair_operations()
        if repair_ops:
            return repair_ops[0].code
        
        return self.DEFAULT_REPAIR_PROCESS_CODE  # Return default even if not found

    async def get_fail_codes(
        self, 
        repair_code: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Get fail codes for a repair operation.
        
        Args:
            repair_code: Repair operation code (default: 500)
            
        Returns:
            List of fail code dictionaries with category, code, description, guid
        """
        configs = await self.get_repair_operation_configs()
        if repair_code in configs:
            return [
                {
                    "category": fc.category,
                    "code": fc.code,
                    "description": fc.code,  # code and description are the same
                    "guid": str(fc.guid),
                    "category_guid": str(fc.category_guid)
                }
                for fc in configs[repair_code].failure_codes
            ]
        return []

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_default_test_operation(self) -> Optional[ProcessInfo]:
        """
        Get the default test operation (code 100).
        
        Returns:
            ProcessInfo for code 100 or None
        """
        return await self.get_test_operation(self.DEFAULT_TEST_PROCESS_CODE)

    async def get_default_repair_operation(self) -> Optional[ProcessInfo]:
        """
        Get the default repair operation (code 500).
        
        Returns:
            ProcessInfo for code 500 or None
        """
        return await self.get_repair_operation(self.DEFAULT_REPAIR_PROCESS_CODE)

    async def process_exists(self, code: int) -> bool:
        """
        Check if a process with the given code exists.
        
        Args:
            code: Process code
            
        Returns:
            True if process exists
        """
        return await self.get_process_by_code(code) is not None

    async def list_process_codes(self) -> List[int]:
        """
        Get a list of all process codes.
        
        Returns:
            List of process codes
        """
        processes = await self.get_processes()
        return [p.code for p in processes if p.code is not None]

    async def list_process_names(self) -> List[str]:
        """
        Get a list of all process names.
        
        Returns:
            List of process names
        """
        processes = await self.get_processes()
        return [p.name for p in processes if p.name]

    # =========================================================================
    # Internal API - Detailed Process Operations
    # =========================================================================

    async def get_processes_detailed(self) -> List[ProcessInfo]:
        """
        Get all processes with detailed information from internal API.
        
        Returns processes with additional fields not available in public API,
        including configuration details and extended metadata.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            List of ProcessInfo objects with full details
            
        See Also:
            get_processes: Standard process retrieval from public API
        """
        return await self._repository.get_processes_detailed()

    async def get_process_detailed(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        Get a specific process by ID with detailed information.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            process_id: The process GUID
            
        Returns:
            ProcessInfo or None if not found
            
        See Also:
            get_process: Standard process retrieval from public API
        """
        return await self._repository.get_process(process_id)

    # =========================================================================
    # Internal API - Repair Operations
    # =========================================================================

    async def get_repair_operation_configs(self) -> Dict[int, RepairOperationConfig]:
        """
        Get all repair operation configurations.
        
        Returns a dictionary keyed by process code (e.g., 500, 510).
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            Dict mapping process code to RepairOperationConfig
        """
        return await self._repository.get_repair_operations()

    async def get_repair_operation_config(
        self, 
        process_id: UUID, 
        process_code: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific repair operation configuration.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            process_id: The process GUID
            process_code: Optional process code filter
            
        Returns:
            Repair operation config dict or None
        """
        return await self._repository.get_repair_operation(process_id, process_code)

    async def get_repair_categories(
        self, 
        process_code: Optional[int] = None
    ) -> List[RepairCategory]:
        """
        Get repair categories for a repair operation.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            process_code: Specific process code, or None for default (500)
            
        Returns:
            List of RepairCategory objects
        """
        code = process_code or self.DEFAULT_REPAIR_PROCESS_CODE
        configs = await self.get_repair_operation_configs()
        
        if code in configs:
            return configs[code].repair_categories
        return []

    async def get_repair_codes(
        self, 
        process_code: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """
        Get repair codes for a repair operation from internal API.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            process_code: Specific process code, or None for default (500)
            category: Filter by repair category name
            
        Returns:
            List of repair code strings
        """
        categories = await self.get_repair_categories(process_code)
        
        codes = []
        for cat in categories:
            if category is None or cat.name == category:
                codes.extend(cat.repair_codes)
        return codes
