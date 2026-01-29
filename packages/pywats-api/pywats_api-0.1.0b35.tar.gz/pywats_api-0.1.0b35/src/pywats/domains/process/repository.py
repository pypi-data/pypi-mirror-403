"""Process repository - sync wrapper around async implementation.

This module provides a synchronous interface by wrapping the async repository.
The async_repository.py is the source of truth for all business logic.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ...core import HttpClient
    from ...core.exceptions import ErrorHandler

from ...core.sync_runner import run_sync
from ...core.async_client import AsyncHttpClient
from .async_repository import AsyncProcessRepository
from .models import ProcessInfo, RepairOperationConfig


class ProcessRepository:
    """
    Process data access layer (sync wrapper).

    This is a thin wrapper around AsyncProcessRepository that provides
    a synchronous interface. All business logic lives in the async version.
    """

    def __init__(
        self, 
        http_client: "HttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with HTTP client.

        Args:
            http_client: HttpClient for making HTTP requests
            error_handler: Optional ErrorHandler for error handling
        """
        self._async_http = AsyncHttpClient(
            base_url=http_client.base_url,
            token=http_client.token,
            timeout=http_client.timeout,
            verify_ssl=http_client.verify_ssl,
            rate_limiter=http_client.rate_limiter,
            retry_config=http_client.retry_config,
        )
        self._async = AsyncProcessRepository(
            self._async_http, 
            error_handler, 
            base_url=http_client.base_url
        )

    # =========================================================================
    # Public API - Process Operations
    # =========================================================================

    def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes from the public API.
        
        GET /api/App/Processes
        
        Returns:
            List of ProcessInfo objects
        """
        return run_sync(self._async.get_processes())

    # =========================================================================
    # Internal API - Detailed Process Operations
    # =========================================================================

    def get_processes_detailed(self) -> List[ProcessInfo]:
        """
        Get all processes with detailed information from internal API.
        
        GET /api/internal/Process/GetProcesses
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            List of ProcessInfo objects with full details
        """
        return run_sync(self._async.get_processes_detailed())

    def get_process(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        Get a specific process by ID from internal API.
        
        GET /api/internal/Process/GetProcess/{id}
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            process_id: The process GUID
            
        Returns:
            ProcessInfo or None if not found
        """
        return run_sync(self._async.get_process(process_id))

    # =========================================================================
    # Internal API - Repair Operations
    # =========================================================================

    def get_repair_operations(self) -> Dict[int, RepairOperationConfig]:
        """
        Get all repair operation configurations.
        
        GET /api/internal/Process/GetRepairOperations
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            Dict mapping process code to RepairOperationConfig
        """
        return run_sync(self._async.get_repair_operations())

    def get_repair_operation(
        self, 
        process_id: UUID, 
        process_code: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific repair operation configuration.
        
        GET /api/internal/Process/GetRepairOperation/{id}
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            process_id: The process GUID
            process_code: Optional process code filter
            
        Returns:
            Repair operation config dict or None
        """
        return run_sync(self._async.get_repair_operation(process_id, process_code))
