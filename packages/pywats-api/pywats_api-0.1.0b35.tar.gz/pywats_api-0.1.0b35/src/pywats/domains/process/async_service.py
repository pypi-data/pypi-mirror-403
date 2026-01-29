"""Async Process service - business logic layer.

Uses the WATS API for process operations with in-memory caching.

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import asyncio

from .async_repository import AsyncProcessRepository
from .models import ProcessInfo, RepairOperationConfig, RepairCategory


class AsyncProcessService:
    """
    Async Process business logic layer with caching.
    
    Maintains an in-memory cache of processes that refreshes at a 
    configurable interval. Provides read-only access to processes
    with lookup methods by name or code.
    
    Example:
        # Get a test operation by code
        process = await api.process.get_test_operation(100)
        
        # Get a test operation by name
        process = await api.process.get_test_operation("End of line test")
        
        # Get a repair operation
        repair = await api.process.get_repair_operation(500)
        
        # Force cache refresh
        await api.process.refresh()
    """
    
    # Default cache refresh interval (5 minutes)
    DEFAULT_REFRESH_INTERVAL = 300
    
    # Default process codes (WATS convention)
    DEFAULT_TEST_PROCESS_CODE = 100
    DEFAULT_REPAIR_PROCESS_CODE = 500
    
    def __init__(
        self, 
        repository: AsyncProcessRepository,
        refresh_interval: int = DEFAULT_REFRESH_INTERVAL
    ):
        """
        Initialize service with repository and caching.
        
        Args:
            repository: AsyncProcessRepository instance
            refresh_interval: Cache refresh interval in seconds (default: 300)
        """
        self._repository = repository
        self._refresh_interval = refresh_interval
        
        # Cache state
        self._cache: List[ProcessInfo] = []
        self._last_refresh: Optional[datetime] = None
        self._lock = asyncio.Lock()

    # =========================================================================
    # Cache Management
    # =========================================================================

    @property
    def refresh_interval(self) -> int:
        """Get the cache refresh interval in seconds."""
        return self._refresh_interval

    @refresh_interval.setter
    def refresh_interval(self, value: int) -> None:
        """Set the cache refresh interval in seconds."""
        if value < 0:
            raise ValueError("Refresh interval must be non-negative")
        self._refresh_interval = value

    async def refresh(self) -> None:
        """
        Force refresh the process cache from the server.
        
        Thread-safe operation that fetches fresh data from the API.
        """
        async with self._lock:
            self._cache = await self._repository.get_processes()
            self._last_refresh = datetime.now()

    async def _ensure_cache(self) -> None:
        """Ensure cache is populated and not stale."""
        needs_refresh = False
        
        async with self._lock:
            if not self._cache or self._last_refresh is None:
                needs_refresh = True
            elif self._refresh_interval > 0:
                age = datetime.now() - self._last_refresh
                if age > timedelta(seconds=self._refresh_interval):
                    needs_refresh = True
        
        if needs_refresh:
            await self.refresh()

    @property
    def last_refresh(self) -> Optional[datetime]:
        """Get the timestamp of the last cache refresh."""
        return self._last_refresh

    # =========================================================================
    # Process Listing (Read-Only)
    # =========================================================================

    async def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes (cached).
        
        Returns:
            List of ProcessInfo objects
        """
        await self._ensure_cache()
        return list(self._cache)  # Return copy to prevent modification

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
            List of fail code dictionaries
        """
        configs = await self.get_repair_operations()
        if repair_code in configs:
            return [
                {"code": fc.code, "name": fc.name, "description": fc.description}
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
