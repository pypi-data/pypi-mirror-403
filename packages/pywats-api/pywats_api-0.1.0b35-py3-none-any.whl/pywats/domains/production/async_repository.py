"""Async Production repository - data access layer.

Async version of the production repository for non-blocking API calls.
Includes both public and internal API methods.
Uses Routes class for centralized endpoint management.

⚠️ INTERNAL API methods are marked and may change without notice.
"""
from typing import Optional, List, Dict, Any, Union, Sequence, TYPE_CHECKING
from datetime import datetime
import logging

from ...core.routes import Routes

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)

logger = logging.getLogger(__name__)


class AsyncProductionRepository:
    """
    Async Production data access layer.

    Handles all async WATS API interactions for production management.
    Includes both public API methods and internal API methods (marked with ⚠️).
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        base_url: str = "",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with async HTTP client.

        Args:
            http_client: AsyncHttpClient for making async HTTP requests
            base_url: Base URL (needed for internal API Referer header)
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        self._base_url = base_url.rstrip('/') if base_url else ""
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Internal API Helpers
    # =========================================================================

    async def _internal_get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        operation: str = "internal_get"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API GET request with Referer header.
        """
        response = await self._http_client.get(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        operation: str = "internal_post"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API POST request with Referer header.
        """
        response = await self._http_client.post(
            endpoint,
            params=params,
            data=data,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_put(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        operation: str = "internal_put"
    ) -> Any:
        """
        ⚠️ INTERNAL: Make an internal API PUT request with Referer header.
        """
        response = await self._http_client.put(
            endpoint,
            params=params,
            data=data,
            headers={"Referer": self._base_url}
        )
        return self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )

    async def _internal_delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        operation: str = "internal_delete"
    ) -> bool:
        """
        ⚠️ INTERNAL: Make an internal API DELETE request with Referer header.
        """
        response = await self._http_client.delete(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        self._error_handler.handle_response(
            response, operation=operation, allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Unit CRUD
    # =========================================================================

    async def get_unit(
        self, serial_number: str, part_number: str
    ) -> Optional[Unit]:
        """
        Get unit information.

        GET /api/Production/Unit/{serialNumber}/{partNumber}
        """
        response = await self._http_client.get(
            Routes.Production.unit(serial_number, part_number)
        )
        data = self._error_handler.handle_response(
            response, operation="get_unit", allow_empty=True
        )
        if data:
            return Unit.model_validate(data)
        return None

    async def save_units(
        self, units: Sequence[Union[Unit, Dict[str, Any]]]
    ) -> List[Unit]:
        """
        Add or update units by serial number.

        PUT /api/Production/Units
        """
        payload = [
            u.model_dump(by_alias=True, exclude_none=True)
            if isinstance(u, Unit) else u
            for u in units
        ]
        response = await self._http_client.put(Routes.Production.UNITS, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_units", allow_empty=True
        )
        if data:
            if isinstance(data, list):
                return [Unit.model_validate(item) for item in data]
            elif isinstance(data, dict):
                if data.get('errorCount', 0) == 0:
                    return [u if isinstance(u, Unit) else Unit.model_validate(u) for u in units]
                else:
                    from ...core.exceptions import PyWATSError
                    raise PyWATSError(f"Failed to save units: {data}")
        return []

    # =========================================================================
    # Unit Verification
    # =========================================================================

    async def get_unit_verification(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerification]:
        """
        Verifies the unit and returns its grade.

        GET /api/Production/UnitVerification
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number
        }
        if revision:
            params["revision"] = revision
        response = await self._http_client.get(
            Routes.Production.UNIT_VERIFICATION, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="get_unit_verification", allow_empty=True
        )
        if data:
            return UnitVerification.model_validate(data)
        return None

    async def get_unit_verification_grade(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerificationGrade]:
        """
        Get complete verification grade for a unit.

        GET /api/Production/UnitVerification
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number
        }
        if revision:
            params["revision"] = revision
        response = await self._http_client.get(
            Routes.Production.UNIT_VERIFICATION, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="get_unit_verification_grade", allow_empty=True
        )
        if data:
            return UnitVerificationGrade.model_validate(data)
        return None

    # =========================================================================
    # Serial Number Types
    # =========================================================================

    async def get_serial_number_types(self) -> List[SerialNumberType]:
        """
        Get serial number types.

        GET /api/Production/SerialNumbers/Types
        """
        response = await self._http_client.get(Routes.Production.SERIAL_NUMBER_TYPES)
        data = self._error_handler.handle_response(
            response, operation="get_serial_number_types", allow_empty=True
        )
        if data and isinstance(data, list):
            return [SerialNumberType.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Unit Phases
    # =========================================================================

    async def get_unit_phases(self) -> List[UnitPhase]:
        """
        Get all available unit phases.

        ⚠️ INTERNAL API - Uses internal MES endpoint.
        
        GET /api/internal/Mes/GetUnitPhases
        
        Unit phases define production workflow states (e.g., "Under Production",
        "Finalized", "Scrapped", etc.).
        
        Returns:
            List of UnitPhase objects
        """
        data = await self._internal_get(
            Routes.Production.Internal.GET_UNIT_PHASES,
            operation="get_unit_phases"
        )
        if data and isinstance(data, list):
            return [UnitPhase.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Unit History
    # =========================================================================

    async def get_unit_changes(
        self,
        serial_number: Optional[str] = None,
        part_number: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[UnitChange]:
        """
        Get unit change records.

        GET /api/Production/Units/Changes

        Args:
            serial_number: Optional serial number filter
            part_number: Optional part number filter
            top: Number of records to return
            skip: Number of records to skip

        Returns:
            List of UnitChange objects
        """
        params: Dict[str, Any] = {}
        if serial_number:
            params["serialNumber"] = serial_number
        if part_number:
            params["partNumber"] = part_number
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip
        response = await self._http_client.get(
            Routes.Production.UNITS_CHANGES,
            params=params if params else None
        )
        data = self._error_handler.handle_response(
            response, operation="get_unit_changes", allow_empty=True
        )
        if data and isinstance(data, list):
            return [UnitChange.model_validate(item) for item in data]
        return []

    async def delete_unit_change(self, change_id: str) -> bool:
        """
        Delete a unit change record.

        DELETE /api/Production/Units/Changes/{id}

        Args:
            change_id: The change record ID

        Returns:
            True if successful
        """
        response = await self._http_client.delete(
            Routes.Production.unit_change(str(change_id))
        )
        self._error_handler.handle_response(
            response, operation="delete_unit_change", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Unit Phase and Process
    # =========================================================================

    async def set_unit_phase(
        self,
        serial_number: str,
        part_number: str,
        phase: Union[int, str],
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's phase.

        PUT /api/Production/SetUnitPhase

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            phase: The phase ID (int) or phase name (str)
            comment: Optional comment

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "phase": phase
        }
        if comment:
            params["comment"] = comment
        response = await self._http_client.put(
            Routes.Production.SET_UNIT_PHASE, params=params
        )
        self._error_handler.handle_response(
            response, operation="set_unit_phase", allow_empty=True
        )
        return response.is_success

    async def set_unit_process(
        self,
        serial_number: str,
        part_number: str,
        process_code: Optional[int] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's process.

        PUT /api/Production/SetUnitProcess

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            process_code: The process code
            comment: Optional comment

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number
        }
        if process_code is not None:
            params["processCode"] = process_code
        if comment:
            params["comment"] = comment
        response = await self._http_client.put(
            Routes.Production.SET_UNIT_PROCESS, params=params
        )
        self._error_handler.handle_response(
            response, operation="set_unit_process", allow_empty=True
        )
        return response.is_success

    # =========================================================================
    # Child Units (Assembly) - Public API
    # =========================================================================

    async def add_child_unit(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Create a parent/child relation between two units.

        POST /api/Production/AddChildUnit

        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {
            "parentSerialNumber": parent_serial,
            "parentPartNumber": parent_part,
            "childSerialNumber": child_serial,
            "childPartNumber": child_part
        }
        response = await self._http_client.post(
            Routes.Production.ADD_CHILD_UNIT, params=params
        )
        self._error_handler.handle_response(
            response, operation="add_child_unit", allow_empty=True
        )
        return response.is_success

    async def remove_child_unit(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Remove the parent/child relation between two units.

        POST /api/Production/RemoveChildUnit

        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {
            "parentSerialNumber": parent_serial,
            "parentPartNumber": parent_part,
            "childSerialNumber": child_serial,
            "childPartNumber": child_part
        }
        response = await self._http_client.post(
            Routes.Production.REMOVE_CHILD_UNIT, params=params
        )
        self._error_handler.handle_response(
            response, operation="remove_child_unit", allow_empty=True
        )
        return response.is_success

    async def check_child_units(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify child units according to box build.

        GET /api/Production/CheckChildUnits

        Args:
            serial_number: Parent serial number
            part_number: Parent part number
            revision: Parent revision

        Returns:
            Child unit check results or None
        """
        from typing import cast
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "revision": revision
        }
        response = await self._http_client.get(
            Routes.Production.CHECK_CHILD_UNITS, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="check_child_units", allow_empty=True
        )
        if data:
            return cast(Dict[str, Any], data)
        return None

    # =========================================================================
    # Serial Numbers - Public API
    # =========================================================================

    async def take_serial_numbers(
        self,
        type_name: str,
        count: int = 1,
        reference_sn: Optional[str] = None,
        reference_pn: Optional[str] = None,
        station_name: Optional[str] = None
    ) -> List[str]:
        """
        Take free serial numbers.

        POST /api/Production/SerialNumbers/Take

        Args:
            type_name: Serial number type name
            count: Number of serial numbers to take (quantity)
            reference_sn: Optional reference serial number
            reference_pn: Optional reference part number
            station_name: Optional station name

        Returns:
            List of allocated serial numbers
        """
        import re

        params: Dict[str, Any] = {
            "serialNumberType": type_name,
            "quantity": count
        }
        if reference_sn:
            params["refSN"] = reference_sn
        if reference_pn:
            params["refPN"] = reference_pn
        if station_name:
            params["stationName"] = station_name
        response = await self._http_client.post(
            Routes.Production.SERIAL_NUMBERS_TAKE, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="take_serial_numbers", allow_empty=True
        )
        if data:
            # Handle XML response - extract serial numbers from <SN id="..."/> tags
            if isinstance(data, str) and "<SerialNumbers" in data:
                # Parse XML to extract serial number IDs
                sn_ids = re.findall(r'<SN id="([^"]+)"', data)
                return sn_ids
            elif isinstance(data, list):
                return data
            else:
                return [data] if data else []
        return []

    async def get_serial_numbers_by_range(
        self,
        type_name: str,
        from_serial: str,
        to_serial: str
    ) -> List[Dict[str, Any]]:
        """
        Get serial numbers in a range.

        GET /api/Production/SerialNumbers/ByRange

        Args:
            type_name: Serial number type name
            from_serial: Start of range
            to_serial: End of range

        Returns:
            List of serial number records
        """
        params: Dict[str, Any] = {
            "typeName": type_name,
            "from": from_serial,
            "to": to_serial
        }
        response = await self._http_client.get(
            Routes.Production.SERIAL_NUMBERS_BY_RANGE, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="get_serial_numbers_by_range", allow_empty=True
        )
        if data:
            return data if isinstance(data, list) else []
        return []

    async def get_serial_numbers_by_reference(
        self,
        type_name: str,
        reference_serial: Optional[str] = None,
        reference_part: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get serial numbers by reference.

        GET /api/Production/SerialNumbers/ByReference

        Args:
            type_name: Serial number type name
            reference_serial: Reference serial number
            reference_part: Reference part number

        Returns:
            List of serial number records
        """
        params: Dict[str, Any] = {"typeName": type_name}
        if reference_serial:
            params["referenceSerialNumber"] = reference_serial
        if reference_part:
            params["referencePartNumber"] = reference_part
        response = await self._http_client.get(
            Routes.Production.SERIAL_NUMBERS_BY_REFERENCE, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="get_serial_numbers_by_reference", allow_empty=True
        )
        if data:
            return data if isinstance(data, list) else []
        return []

    async def upload_serial_numbers(
        self,
        file_content: bytes,
        content_type: str = "text/csv"
    ) -> bool:
        """
        Upload serial numbers file (XML or CSV).

        PUT /api/Production/SerialNumbers

        Args:
            file_content: File content as bytes
            content_type: MIME type

        Returns:
            True if successful
        """
        headers = {"Content-Type": content_type}
        response = await self._http_client.put(
            Routes.Production.SERIAL_NUMBERS,
            data=file_content,
            headers=headers
        )
        self._error_handler.handle_response(
            response, operation="upload_serial_numbers", allow_empty=True
        )
        return response.is_success

    async def export_serial_numbers(
        self,
        type_name: str,
        state: Optional[str] = None,
        format: str = "csv"
    ) -> Optional[bytes]:
        """
        Export serial numbers as file.

        GET /api/Production/SerialNumbers

        Args:
            type_name: Serial number type name
            state: Optional state filter
            format: Output format (csv or xml)

        Returns:
            File content as bytes or None
        """
        params: Dict[str, Any] = {"typeName": type_name}
        if state:
            params["state"] = state
        if format:
            params["format"] = format
        response = await self._http_client.get(
            Routes.Production.SERIAL_NUMBERS, params=params
        )
        self._error_handler.handle_response(
            response, operation="export_serial_numbers", allow_empty=True
        )
        if response.is_success:
            return response.raw
        return None

    # =========================================================================
    # Batches
    # =========================================================================

    async def get_batches(
        self,
        part_number: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> List[ProductionBatch]:
        """
        Get production batches.

        GET /api/Production/Batches
        """
        params: Dict[str, Any] = {}
        if part_number:
            params["partNumber"] = part_number
        if batch_id:
            params["batchId"] = batch_id
        
        response = await self._http_client.get(Routes.Production.BATCHES, params=params or None)
        data = self._error_handler.handle_response(
            response, operation="get_batches", allow_empty=True
        )
        if data and isinstance(data, list):
            return [ProductionBatch.model_validate(item) for item in data]
        return []

    async def save_batch(
        self, batch: Union[ProductionBatch, Dict[str, Any]]
    ) -> Optional[ProductionBatch]:
        """
        Create or update a production batch.

        PUT /api/Production/Batch
        """
        payload = (
            batch.model_dump(by_alias=True, exclude_none=True)
            if isinstance(batch, ProductionBatch) else batch
        )
        response = await self._http_client.put(Routes.Production.BATCH, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_batch", allow_empty=True
        )
        if data:
            return ProductionBatch.model_validate(data)
        return None

    async def save_batches(
        self, batches: Sequence[Union[ProductionBatch, Dict[str, Any]]]
    ) -> List[ProductionBatch]:
        """
        Add or update batches (bulk).

        PUT /api/Production/Batches

        Args:
            batches: List of ProductionBatch objects or data dictionaries

        Returns:
            List of saved ProductionBatch objects
        """
        payload = [
            b.model_dump(by_alias=True, exclude_none=True)
            if isinstance(b, ProductionBatch) else b
            for b in batches
        ]
        response = await self._http_client.put(Routes.Production.BATCHES, data=payload)
        data = self._error_handler.handle_response(
            response, operation="save_batches", allow_empty=True
        )
        if data:
            return [ProductionBatch.model_validate(item) for item in data]
        return []

    # =========================================================================
    # ⚠️ INTERNAL API - Connection Check
    # =========================================================================

    async def is_connected(self) -> bool:
        """
        ⚠️ INTERNAL: Check if Production module is connected.
        
        GET /api/internal/Production/isConnected
        """
        result = await self._internal_get(
            Routes.Production.Internal.IS_CONNECTED,
            operation="is_connected"
        )
        return result is not None

    # =========================================================================
    # ⚠️ INTERNAL API - Unit Phases (MES)
    # =========================================================================

    async def get_unit_phases_mes(self) -> List[UnitPhase]:
        """
        Get all available unit phases from MES (Manufacturing Execution System).

        GET /api/internal/Mes/GetUnitPhases
        
        This method retrieves unit phases from the MES internal endpoint,
        which may return different or more detailed data than the standard
        get_unit_phases() method that uses the public Production API.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Returns:
            List of UnitPhase objects from MES
            
        See Also:
            get_unit_phases(): Standard method using public API
        """
        data = await self._internal_get(
            Routes.Production.Internal.GET_UNIT_PHASES,
            operation="get_unit_phases_mes"
        )
        if data:
            return [UnitPhase.model_validate(item) for item in data]
        return []

    # =========================================================================
    # ⚠️ INTERNAL API - Sites
    # =========================================================================

    async def get_sites(self) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get all production sites.
        
        GET /api/internal/Production/GetSites
        """
        data = await self._internal_get(
            Routes.Production.Internal.GET_SITES,
            operation="get_sites"
        )
        if data and isinstance(data, list):
            return data
        return []

    # =========================================================================
    # ⚠️ INTERNAL API - Unit Operations
    # =========================================================================

    async def get_unit_by_serial(
        self,
        serial_number: str,
        part_number: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a unit by serial number with optional part number filter.
        
        GET /api/internal/Production/GetUnit
        
        Unlike the standard get_unit() method which requires both serial_number
        and part_number, this method allows lookup by serial number alone.
        Useful when the part number is unknown or when searching across products.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: The unit serial number (required)
            part_number: Optional product part number filter
            
        Returns:
            Unit data dictionary or None if not found
            
        See Also:
            get_unit(): Standard method requiring both serial and part number
        """
        params: Dict[str, Any] = {"serialNumber": serial_number}
        if part_number:
            params["partNumber"] = part_number
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT, 
            params,
            operation="get_unit_by_serial"
        )

    async def get_unit_info(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get unit information.
        
        GET /api/internal/Production/GetUnitInfo
        """
        params = {"serialNumber": serial_number, "partNumber": part_number}
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT_INFO, 
            params,
            operation="get_unit_info"
        )

    async def get_unit_hierarchy(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get the complete unit hierarchy.
        
        GET /api/internal/Production/GetUnitHierarchy
        """
        params = {"serialNumber": serial_number, "partNumber": part_number}
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT_HIERARCHY, 
            params,
            operation="get_unit_hierarchy"
        )

    async def get_unit_state_history(
        self,
        serial_number: str,
        part_number: str
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get the unit state change history.
        
        GET /api/internal/Production/GetUnitStateHistory
        """
        params = {"serialNumber": serial_number, "partNumber": part_number}
        data = await self._internal_get(
            Routes.Production.Internal.GET_UNIT_STATE_HISTORY, 
            params,
            operation="get_unit_state_history"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def get_unit_phase(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current phase of a specific unit.
        
        GET /api/internal/Production/GetUnitPhase
        
        Returns the current manufacturing phase for a specific unit,
        such as 'Assembly', 'Testing', 'Shipped', etc.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: The unit serial number
            part_number: The product part number
            
        Returns:
            Phase data dictionary with current phase info, or None
            
        See Also:
            get_unit_phases(): Get all available phases (not unit-specific)
        """
        params = {"serialNumber": serial_number, "partNumber": part_number}
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT_PHASE, 
            params,
            operation="get_unit_phase"
        )

    async def get_unit_process(
        self,
        serial_number: str,
        part_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current process of a specific unit.
        
        GET /api/internal/Production/GetUnitProcess
        
        Returns the current manufacturing process assigned to a unit,
        indicating what operation/step the unit is currently at.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: The unit serial number
            part_number: The product part number
            
        Returns:
            Process data dictionary with current process info, or None
        """
        params = {"serialNumber": serial_number, "partNumber": part_number}
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT_PROCESS, 
            params,
            operation="get_unit_process"
        )

    async def get_unit_contents(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get unit contents (BOM/components).
        
        GET /api/internal/Production/GetUnitContents
        """
        params = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "revision": revision
        }
        return await self._internal_get(
            Routes.Production.Internal.GET_UNIT_CONTENTS, 
            params,
            operation="get_unit_contents"
        )

    async def create_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: str,
        batch_number: Optional[str] = None,
        unit_phase: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new unit in the production system.
        
        POST /api/internal/Production/CreateUnit
        
        Creates a new production unit with the specified serial number,
        part number, and revision. Optionally assigns a batch and initial phase.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: Unique serial number for the unit
            part_number: Product part number
            revision: Product revision
            batch_number: Optional batch/lot number to assign
            unit_phase: Optional initial unit phase ID
            
        Returns:
            Created unit data dictionary, or None on failure
            
        Example:
            >>> unit = await repo.create_unit(
            ...     serial_number="SN-001",
            ...     part_number="PROD-A",
            ...     revision="1.0",
            ...     batch_number="BATCH-2024-01"
            ... )
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "revision": revision
        }
        if batch_number:
            params["batchNumber"] = batch_number
        if unit_phase is not None:
            params["unitPhase"] = unit_phase
        return await self._internal_post(
            Routes.Production.Internal.CREATE_UNIT, 
            params=params,
            operation="create_unit"
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Child Unit Operations
    # =========================================================================

    async def add_child_unit_validated(
        self,
        serial_number: str,
        part_number: str,
        child_serial_number: str,
        child_part_number: str,
        check_part_number: str,
        check_revision: str,
        culture_code: str = "en-US",
        check_phase: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a child unit with validation against box build template.
        
        POST /api/internal/Production/AddChildUnit
        
        This is an advanced version of add_child_unit() that performs
        validation against the box build template to ensure the child
        unit matches expected part number and revision requirements.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: Parent unit serial number
            part_number: Parent unit part number
            child_serial_number: Child unit serial number to add
            child_part_number: Child unit part number
            check_part_number: Expected part number for validation
            check_revision: Expected revision for validation
            culture_code: Locale for error messages (default: "en-US")
            check_phase: Whether to validate phase compatibility
            
        Returns:
            Result data dictionary with validation outcome, or None
            
        See Also:
            add_child_unit(): Simple version without validation
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "childSerialNumber": child_serial_number,
            "childPartNumber": child_part_number,
            "checkPartNumber": check_part_number,
            "checkRevision": check_revision,
            "cultureCode": culture_code
        }
        if check_phase is not None:
            params["checkPhase"] = check_phase
        return await self._internal_post(
            Routes.Production.Internal.ADD_CHILD_UNIT, 
            params=params,
            operation="add_child_unit_validated"
        )

    async def remove_child_unit_localized(
        self,
        serial_number: str,
        part_number: str,
        child_serial_number: str,
        child_part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Remove a child unit with localized error messages.
        
        POST /api/internal/Production/RemoveChildUnit
        
        This version supports culture_code for localized error messages,
        useful for multi-language production environments.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            serial_number: Parent unit serial number
            part_number: Parent unit part number
            child_serial_number: Child unit serial number to remove
            child_part_number: Child unit part number
            culture_code: Optional locale code (e.g., "en-US", "de-DE")
            
        Returns:
            Result data dictionary, or None
            
        See Also:
            remove_child_unit(): Simple version without localization
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number,
            "childSerialNumber": child_serial_number,
            "childPartNumber": child_part_number
        }
        if culture_code:
            params["cultureCode"] = culture_code
        return await self._internal_post(
            Routes.Production.Internal.REMOVE_CHILD_UNIT, 
            params=params,
            operation="remove_child_unit_localized"
        )

    async def remove_all_child_units(
        self,
        serial_number: str,
        part_number: str,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Remove all child units from a parent unit.
        
        POST /api/internal/Production/RemoveAllChildUnits
        """
        params: Dict[str, Any] = {
            "serialNumber": serial_number,
            "partNumber": part_number
        }
        if culture_code:
            params["cultureCode"] = culture_code
        return await self._internal_post(
            Routes.Production.Internal.REMOVE_ALL_CHILD_UNITS, 
            params=params,
            operation="remove_all_child_units"
        )

    async def validate_child_units(
        self,
        parent_serial_number: str,
        parent_part_number: str,
        culture_code: str = "en-US"
    ) -> Optional[Dict[str, Any]]:
        """
        Validate child units against box build requirements.
        
        GET /api/internal/Production/CheckChildUnits
        
        Performs validation of all child units attached to a parent unit,
        checking against box build template requirements. Returns detailed
        validation results with localized messages.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            parent_serial_number: Parent unit serial number
            parent_part_number: Parent unit part number
            culture_code: Locale for validation messages (default: "en-US")
            
        Returns:
            Validation results dictionary including:
            - Compliance status
            - Missing/extra child units
            - Validation messages in specified locale
            
        See Also:
            check_child_units(): Simple version using public API with revision param
        """
        params = {
            "ParentSerialNumber": parent_serial_number,
            "ParentPartNumber": parent_part_number,
            "CultureCode": culture_code
        }
        return await self._internal_get(
            Routes.Production.Internal.CHECK_CHILD_UNITS, 
            params,
            operation="validate_child_units"
        )

    # =========================================================================
    # ⚠️ INTERNAL API - Serial Number Management
    # =========================================================================

    async def find_serial_numbers(
        self,
        serial_number_type: str,
        start_address: str,
        end_address: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Find all serial numbers in a range.
        
        GET /api/internal/Production/SerialNumbers
        """
        params: Dict[str, Any] = {
            "serialNumberType": serial_number_type,
            "startAddress": start_address,
            "endAddress": end_address
        }
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
        data = await self._internal_get(
            Routes.Production.Internal.SERIAL_NUMBERS, 
            params,
            operation="find_serial_numbers"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def get_serial_number_count(
        self,
        serial_number_type: str,
        start_address: Optional[str] = None,
        end_address: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Optional[int]:
        """
        ⚠️ INTERNAL: Get count of serial numbers in a range.
        
        GET /api/internal/Production/SerialNumbers/Count
        """
        params: Dict[str, Any] = {"serialNumberType": serial_number_type}
        if start_address:
            params["startAddress"] = start_address
        if end_address:
            params["endAddress"] = end_address
        if from_date:
            params["fromDate"] = from_date.isoformat()
        if to_date:
            params["toDate"] = to_date.isoformat()
        return await self._internal_get(
            Routes.Production.Internal.SERIAL_NUMBERS_COUNT, 
            params,
            operation="get_serial_number_count"
        )

    async def free_serial_numbers(
        self,
        ranges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Free reserved serial numbers in specified ranges.
        
        PUT /api/internal/Production/SerialNumbers/Free
        """
        return await self._internal_put(
            Routes.Production.Internal.SERIAL_NUMBERS_FREE,
            data=ranges,
            operation="free_serial_numbers"
        )

    async def delete_free_serial_numbers(
        self,
        ranges: List[Dict[str, Any]]
    ) -> bool:
        """
        ⚠️ INTERNAL: Delete free serial numbers in specified ranges.
        
        DELETE /api/internal/Production/SerialNumbers/Free
        """
        return await self._internal_delete(
            Routes.Production.Internal.SERIAL_NUMBERS_FREE,
            data=ranges,
            operation="delete_free_serial_numbers"
        )

    async def get_serial_number_ranges(
        self,
        serial_number_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get current serial number ranges.
        
        GET /api/internal/Production/SerialNumbers/Ranges
        """
        params: Dict[str, Any] = {}
        if serial_number_type:
            params["serialNumberType"] = serial_number_type
        data = await self._internal_get(
            Routes.Production.Internal.SERIAL_NUMBERS_RANGES,
            params if params else None,
            operation="get_serial_number_ranges"
        )
        if data and isinstance(data, list):
            return data
        return []

    async def get_serial_number_statistics(
        self,
        serial_number_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ INTERNAL: Get statistics for serial numbers.
        
        GET /api/internal/Production/SerialNumbers/Statistics
        """
        params: Dict[str, Any] = {}
        if serial_number_type:
            params["serialNumberType"] = serial_number_type
        return await self._internal_get(
            Routes.Production.Internal.SERIAL_NUMBERS_STATISTICS,
            params if params else None,
            operation="get_serial_number_statistics"
        )
