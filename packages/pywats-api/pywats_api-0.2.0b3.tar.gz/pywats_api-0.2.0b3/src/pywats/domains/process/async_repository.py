"""Async Process repository - data access layer.

Uses the WATS API endpoints for process operations.
All endpoints are defined in pywats.core.routes.Routes.

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from ...core.routes import Routes
from .models import ProcessInfo, RepairOperationConfig


class AsyncProcessRepository:
    """
    Async Process data access layer.
    
    Uses public and internal API endpoints for process operations.
    
    Public API:
    - GET /api/App/Processes
    
    Internal API (⚠️ INTERNAL):
    - GET /api/internal/Process/GetProcesses
    - GET /api/internal/Process/GetProcess/{id}
    - GET /api/internal/Process/GetRepairOperations
    - GET /api/internal/Process/GetRepairOperation/{id}
    """
    
    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        error_handler: Optional["ErrorHandler"] = None,
        base_url: Optional[str] = None
    ) -> None:
        """
        Initialize repository with async HTTP client.
        
        Args:
            http_client: AsyncHttpClient for making async HTTP requests
            error_handler: ErrorHandler for response handling
            base_url: Base URL for Referer header (required for internal API)
        """
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._http_client = http_client
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)
        self._base_url = (base_url or "").rstrip('/')

    # =========================================================================
    # Internal API Helpers
    # =========================================================================

    async def _internal_get(
        self, 
        endpoint: str, 
        operation: str = "internal_get"
    ) -> Any:
        """
        Make an internal API GET request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = await self._http_client.get(
            endpoint,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    # =========================================================================
    # Public API - Process Operations
    # =========================================================================

    async def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes from the public API.
        
        GET /api/App/Processes
        
        Returns:
            List of ProcessInfo objects
        """
        response = await self._http_client.get(Routes.App.PROCESSES)
        data = self._error_handler.handle_response(
            response, operation="get_processes", allow_empty=True
        )
        if data:
            return [ProcessInfo.model_validate(p) for p in data]
        return []

    # =========================================================================
    # Internal API - Process Operations
    # =========================================================================

    async def get_processes_detailed(self) -> List[ProcessInfo]:
        """
        Get all processes with full details from internal API.
        
        GET /api/internal/Process/GetProcesses
        
        This version returns more detailed process information than the
        standard get_processes() method, including:
        - ProcessID (GUID)
        - processIndex
        - state
        - Properties dictionary
        - isTestOperation, isRepairOperation, isWipOperation flags
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            List of ProcessInfo objects with full details
            
        Example:
            >>> processes = await repo.get_processes_detailed()
            >>> for p in processes:
            ...     print(f"{p.name}: test={p.is_test_operation}, repair={p.is_repair_operation}")
        """
        data = await self._internal_get(
            Routes.Process.Internal.GET_PROCESSES,
            operation="get_processes_detailed"
        )
        if data and isinstance(data, list):
            result = []
            for p in data:
                # Map PascalCase to our model
                mapped = {
                    "code": p.get("Code"),
                    "name": p.get("Name"),
                    "description": p.get("Description"),
                    "ProcessID": p.get("ProcessID"),
                    "processIndex": p.get("ProcessIndex"),
                    "state": p.get("State"),
                    "Properties": p.get("Properties"),
                    "isTestOperation": p.get("IsTestOperation", False),
                    "isRepairOperation": p.get("IsRepairOperation", False),
                    "isWipOperation": p.get("IsWIPOperation", False),
                }
                result.append(ProcessInfo.model_validate(mapped))
            return result
        return []

    async def get_process(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        Get a specific process by ID from internal API.
        
        GET /api/internal/Process/GetProcess/{id}
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            process_id: The process GUID
            
        Returns:
            ProcessInfo or None if not found
        """
        data = await self._internal_get(
            Routes.Process.Internal.get_process(str(process_id)),
            operation="get_process_detailed"
        )
        if data:
            mapped = {
                "code": data.get("Code"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "ProcessID": data.get("ProcessID"),
                "processIndex": data.get("ProcessIndex"),
                "state": data.get("State"),
                "Properties": data.get("Properties"),
                "isTestOperation": data.get("IsTestOperation", False),
                "isRepairOperation": data.get("IsRepairOperation", False),
                "isWipOperation": data.get("IsWIPOperation", False),
            }
            return ProcessInfo.model_validate(mapped)
        return None

    # =========================================================================
    # Internal API - Repair Operations
    # =========================================================================

    async def get_repair_operations(self) -> Dict[int, RepairOperationConfig]:
        """
        Get all repair operation configurations.
        
        GET /api/internal/Process/GetRepairOperations
        
        Returns a dictionary mapping process codes (e.g., 500, 510) to their
        repair operation configurations.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            Dict mapping process code (int) to RepairOperationConfig
            
        Example:
            >>> repair_ops = await repo.get_repair_operations()
            >>> for code, config in repair_ops.items():
            ...     print(f"Process {code}: {config}")
        """
        data = await self._internal_get(
            Routes.Process.Internal.GET_REPAIR_OPERATIONS,
            operation="get_repair_operations"
        )
        if data and isinstance(data, dict):
            result = {}
            for code_str, config in data.items():
                try:
                    code = int(code_str)
                    result[code] = RepairOperationConfig.model_validate(config)
                except (ValueError, Exception):
                    continue
            return result
        return {}

    async def get_repair_operation(
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
            Repair operation config dict or None if not found
            
        Example:
            >>> config = await repo.get_repair_operation(process_uuid, process_code=500)
        """
        endpoint = Routes.Process.Internal.get_repair_operation(str(process_id))
        if process_code is not None:
            endpoint += f"?processCode={process_code}"
        return await self._internal_get(endpoint, operation="get_repair_operation")
