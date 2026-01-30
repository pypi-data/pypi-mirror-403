"""Process service - thin sync wrapper around AsyncProcessService.

This module provides synchronous access to AsyncProcessService methods.
All business logic is maintained in async_service.py (source of truth).

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from uuid import UUID

from .async_service import AsyncProcessService
from .async_repository import AsyncProcessRepository
from .models import ProcessInfo, RepairOperationConfig, RepairCategory
from ...core.sync_runner import run_sync


class ProcessService:
    """
    Synchronous wrapper for AsyncProcessService.

    Provides sync access to all async process service operations.
    All business logic is in AsyncProcessService.
    """

    # Default process codes (WATS convention)
    DEFAULT_TEST_PROCESS_CODE = 100
    DEFAULT_REPAIR_PROCESS_CODE = 500

    def __init__(self, async_service: AsyncProcessService = None, *, repository=None) -> None:
        """
        Initialize with AsyncProcessService or repository.

        Args:
            async_service: AsyncProcessService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncProcessService(repository)
            self._repository = repository  # Keep reference for tests
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository  # Expose underlying repo
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncProcessRepository) -> "ProcessService":
        """
        Create ProcessService from an AsyncProcessRepository.

        Args:
            repository: AsyncProcessRepository instance

        Returns:
            ProcessService wrapping an AsyncProcessService
        """
        async_service = AsyncProcessService(repository)
        return cls(async_service)

    # =========================================================================
    # Cache Management
    # =========================================================================

    @property
    def refresh_interval(self) -> int:
        """Get the cache refresh interval in seconds."""
        return self._async_service.refresh_interval

    @refresh_interval.setter
    def refresh_interval(self, value: int) -> None:
        """Set the cache refresh interval in seconds."""
        self._async_service.refresh_interval = value

    def refresh(self) -> None:
        """Force refresh the process cache from the server.
        
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        run_sync(self._async_service.refresh())

    @property
    def last_refresh(self) -> Optional[datetime]:
        """Get the timestamp of the last cache refresh."""
        return self._async_service.last_refresh

    # =========================================================================
    # Process Listing (Read-Only)
    # =========================================================================

    def get_processes(self) -> List[ProcessInfo]:
        """Get all processes (cached).
        
        Returns:
            List of all ProcessInfo objects
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_processes())

    def get_test_operations(self) -> List[ProcessInfo]:
        """Get all test operations (isTestOperation=true).
        
        Returns:
            List of ProcessInfo objects where isTestOperation=true
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_test_operations())

    def get_repair_operations(self) -> List[ProcessInfo]:
        """Get all repair operations (isRepairOperation=true).
        
        Returns:
            List of ProcessInfo objects where isRepairOperation=true
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_operations())

    def get_wip_operations(self) -> List[ProcessInfo]:
        """Get all WIP operations (isWipOperation=true).
        
        Returns:
            List of ProcessInfo objects where isWipOperation=true
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_wip_operations())

    # =========================================================================
    # Process Lookup (Read-Only)
    # =========================================================================

    def get_process_by_code(self, code: int) -> Optional[ProcessInfo]:
        """Get a process by its code.
        
        Args:
            code: The process code to lookup
            
        Returns:
            ProcessInfo if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_process_by_code(code))

    def get_process_by_name(self, name: str) -> Optional[ProcessInfo]:
        """Get a process by its name (case-insensitive).
        
        Args:
            name: The process name to lookup (case-insensitive)
            
        Returns:
            ProcessInfo if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_process_by_name(name))

    def get_test_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """Get a test operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo if found and is a test operation, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_test_operation(identifier))

    def get_repair_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """Get a repair operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo if found and is a repair operation, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_operation(identifier))

    def get_wip_operation(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """Get a WIP operation by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo if found and is a WIP operation, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_wip_operation(identifier))

    def get_process(
        self, 
        identifier: Union[int, str]
    ) -> Optional[ProcessInfo]:
        """Get any process by code or name.
        
        Args:
            identifier: Process code (int) or name (str)
            
        Returns:
            ProcessInfo if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_process(identifier))

    # =========================================================================
    # Validation Methods
    # =========================================================================

    def is_valid_test_operation(self, code: int) -> bool:
        """Check if a code is a valid test operation.
        
        Args:
            code: The process code to check
            
        Returns:
            True if code exists and is a test operation, False otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.is_valid_test_operation(code))

    def is_valid_repair_operation(self, code: int) -> bool:
        """Check if a code is a valid repair operation.
        
        Args:
            code: The process code to check
            
        Returns:
            True if code exists and is a repair operation, False otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.is_valid_repair_operation(code))

    def is_valid_wip_operation(self, code: int) -> bool:
        """Check if a code is a valid WIP operation.
        
        Args:
            code: The process code to check
            
        Returns:
            True if code exists and is a WIP operation, False otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.is_valid_wip_operation(code))

    def get_default_test_code(self) -> int:
        """Get the default test operation code (typically 100).
        
        Returns:
            Default test operation code
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_default_test_code())

    def get_default_repair_code(self) -> int:
        """Get the default repair operation code (typically 500).
        
        Returns:
            Default repair operation code
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_default_repair_code())

    def get_fail_codes(
        self, 
        repair_code: int = 500
    ) -> List[Dict[str, Any]]:
        """Get fail codes for a repair operation.
        
        Args:
            repair_code: The repair operation code (default: 500)
            
        Returns:
            List of fail code dictionaries with code and description
            
        Raises:
            AuthenticationError: If API authentication fails
            NotFoundError: If repair operation code does not exist
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_fail_codes(repair_code))

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def get_default_test_operation(self) -> Optional[ProcessInfo]:
        """Get the default test operation (code 100).
        
        Returns:
            ProcessInfo for default test operation if it exists, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_default_test_operation())

    def get_default_repair_operation(self) -> Optional[ProcessInfo]:
        """Get the default repair operation (code 500).
        
        Returns:
            ProcessInfo for default repair operation if it exists, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_default_repair_operation())

    def process_exists(self, code: int) -> bool:
        """Check if a process with the given code exists.
        
        Args:
            code: The process code to check
            
        Returns:
            True if process exists, False otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.process_exists(code))

    def list_process_codes(self) -> List[int]:
        """Get a list of all process codes.
        
        Returns:
            List of all process codes
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.list_process_codes())

    def list_process_names(self) -> List[str]:
        """Get a list of all process names.
        
        Returns:
            List of all process names
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.list_process_names())

    # =========================================================================
    # Internal API - Detailed Process Operations
    # =========================================================================

    def get_processes_detailed(self) -> List[ProcessInfo]:
        """
        ⚠️ INTERNAL API - Get all processes with detailed information.
        
        Returns processes with additional fields not available in public API.
        
        Returns:
            List of ProcessInfo with extended details
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_processes_detailed())

    def get_process_detailed(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        ⚠️ INTERNAL API - Get a specific process by ID with detailed information.
        
        Args:
            process_id: The UUID of the process
            
        Returns:
            ProcessInfo with extended details if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_process_detailed(process_id))

    # =========================================================================
    # Internal API - Repair Operations
    # =========================================================================

    def get_repair_operation_configs(self) -> Dict[int, RepairOperationConfig]:
        """
        ⚠️ INTERNAL API - Get all repair operation configurations.
        
        Returns a dictionary keyed by process code (e.g., 500, 510).
        
        Returns:
            Dictionary mapping process codes to RepairOperationConfig objects
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_operation_configs())
        return run_sync(self._async_service.get_repair_operation_configs())

    def get_repair_operation_config(
        self, 
        process_id: UUID, 
        process_code: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL API - Get a specific repair operation configuration.
        
        Args:
            process_id: The UUID of the repair operation
            process_code: Optional process code for additional filtering
            
        Returns:
            Configuration dictionary if found, None otherwise
            
        Raises:
            AuthenticationError: If API authentication fails
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_operation_config(process_id, process_code))

    def get_repair_categories(
        self, 
        process_code: Optional[int] = None
    ) -> List[RepairCategory]:
        """
        ⚠️ INTERNAL API - Get repair categories for a repair operation.
        
        Args:
            process_code: Optional repair operation code (default: 500)
            
        Returns:
            List of RepairCategory objects
            
        Raises:
            AuthenticationError: If API authentication fails
            NotFoundError: If repair operation code does not exist
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_categories(process_code))

    def get_repair_codes(
        self, 
        process_code: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """
        ⚠️ INTERNAL API - Get repair codes for a repair operation.
        
        Args:
            process_code: Optional repair operation code (default: 500)
            category: Optional category to filter repair codes
            
        Returns:
            List of repair code strings
            
        Raises:
            AuthenticationError: If API authentication fails
            NotFoundError: If repair operation code or category does not exist
            APIError: If the server request fails or endpoint changes
            PyWATSError: For other API-related errors
        """
        return run_sync(self._async_service.get_repair_codes(process_code, category))
