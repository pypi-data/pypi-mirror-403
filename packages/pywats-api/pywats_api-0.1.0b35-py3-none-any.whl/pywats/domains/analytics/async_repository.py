"""Async Analytics repository - data access layer.

All async API interactions for statistics, KPIs, yield analysis, and dashboard data.
Maps to the WATS /api/App/* endpoints (backend naming).

Uses Routes class from pywats.core.routes for centralized endpoint management.

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

from ...core.routes import Routes

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from .models import (
    YieldData,
    ProcessInfo,
    LevelInfo,
    ProductGroup,
    StepAnalysisRow,
    TopFailedStep,
    RepairStatistics,
    RepairHistoryRecord,
    MeasurementData,
    AggregatedMeasurement,
    OeeAnalysisResult,
    # Internal models
    UnitFlowNode,
    UnitFlowLink,
    UnitFlowUnit,
    UnitFlowFilter,
    UnitFlowResult,
    MeasurementListItem,
    StepStatusItem,
)
from ..report.models import WATSFilter, ReportHeader


class AsyncAnalyticsRepository:
    """
    Async Analytics/Statistics data access layer.

    Handles all async WATS API interactions for statistics, KPIs, and yield analysis.
    Maps to /api/App/* endpoints on the backend.
    
    Includes internal API methods for Unit Flow and measurement filtering.
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        error_handler: Optional["ErrorHandler"] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize with async HTTP client.

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
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make an internal API GET request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = await self._http_client.get(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None

    async def _internal_post(
        self, 
        endpoint: str, 
        data: Any = None, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make an internal API POST request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = await self._http_client.post(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None

    # =========================================================================
    # System Info
    # =========================================================================

    async def get_version(self) -> Optional[str]:
        """
        Get server/api version.

        GET /api/App/Version

        Returns:
            Version string (e.g., "24.1.0") or None
        """
        response = await self._http_client.get(Routes.App.VERSION)
        data = self._error_handler.handle_response(
            response, operation="get_version", allow_empty=True
        )
        return str(data) if data else None

    async def get_processes(
        self,
        include_test_operations: Optional[bool] = None,
        include_repair_operations: Optional[bool] = None,
        include_wip_operations: Optional[bool] = None,
        include_inactive_processes: Optional[bool] = None,
    ) -> List[ProcessInfo]:
        """
        Get processes with optional filtering.

        GET /api/App/Processes

        Args:
            include_test_operations: Include processes marked as IsTestOperation
            include_repair_operations: Include processes marked as IsRepairOperation
            include_wip_operations: Include processes marked as IsWipOperation
            include_inactive_processes: Include inactive processes

        Returns:
            List of ProcessInfo objects
        """
        params: Dict[str, Any] = {}
        if include_test_operations is not None:
            params["includeTestOperations"] = include_test_operations
        if include_repair_operations is not None:
            params["includeRepairOperations"] = include_repair_operations
        if include_wip_operations is not None:
            params["includeWipOperations"] = include_wip_operations
        if include_inactive_processes is not None:
            params["includeInactiveProcesses"] = include_inactive_processes

        response = await self._http_client.get(
            Routes.App.PROCESSES, params=params if params else None
        )
        result = self._error_handler.handle_response(
            response, operation="get_processes", allow_empty=True
        )
        if result:
            return [ProcessInfo.model_validate(item) for item in result]
        return []

    async def get_levels(self) -> List[LevelInfo]:
        """
        Get all production levels.

        GET /api/App/Levels

        Returns:
            List of LevelInfo objects
        """
        response = await self._http_client.get(Routes.App.LEVELS)
        result = self._error_handler.handle_response(
            response, operation="get_levels", allow_empty=True
        )
        if result:
            return [LevelInfo.model_validate(item) for item in result]
        return []

    async def get_product_groups(
        self,
        include_filters: Optional[bool] = None
    ) -> List[ProductGroup]:
        """
        Get all product groups.

        GET /api/App/ProductGroups

        Args:
            include_filters: Include or exclude product group filters

        Returns:
            List of ProductGroup objects
        """
        params: Dict[str, Any] = {}
        if include_filters is not None:
            params["includeFilters"] = include_filters

        response = await self._http_client.get(
            Routes.App.PRODUCT_GROUPS, params=params if params else None
        )
        result = self._error_handler.handle_response(
            response, operation="get_product_groups", allow_empty=True
        )
        if result:
            return [ProductGroup.model_validate(item) for item in result]
        return []

    # =========================================================================
    # Yield Statistics
    # =========================================================================

    async def get_dynamic_yield(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Yield by custom dimensions (PREVIEW).

        POST /api/App/DynamicYield

        Args:
            filter_data: WATSFilter object or dict with dimensions and filters

        Returns:
            List of YieldData objects ordered as specified in dimensions
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data) if filter_data else {}

        if ("periodCount" in data or "dateGrouping" in data) and "includeCurrentPeriod" not in data:
            data["includeCurrentPeriod"] = True

        params: Optional[Dict[str, Any]] = None
        if isinstance(data, dict) and data.get("dimensions"):
            dimensions = data.get("dimensions")
            params = {"dimensions": dimensions}
            if len(data.keys()) == 1:
                data = {}

        if not data:
            data = {}

        response = await self._http_client.post(
            Routes.App.DYNAMIC_YIELD, data=data, params=params
        )
        result = self._error_handler.handle_response(
            response, operation="get_dynamic_yield", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    async def get_volume_yield(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Volume/Yield list.

        GET/POST /api/App/VolumeYield

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = await self._http_client.post(Routes.App.VOLUME_YIELD, data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = await self._http_client.get(
                Routes.App.VOLUME_YIELD, params=params if params else None
            )
        result = self._error_handler.handle_response(
            response, operation="get_volume_yield", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    async def get_high_volume(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        High Volume list.

        GET/POST /api/App/HighVolume

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = await self._http_client.post(Routes.App.HIGH_VOLUME, data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = await self._http_client.get(
                Routes.App.HIGH_VOLUME, params=params if params else None
            )
        result = self._error_handler.handle_response(
            response, operation="get_high_volume", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    async def get_high_volume_by_product_group(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Yield by product group sorted by volume.

        POST /api/App/HighVolumeByProductGroup

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of YieldData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(
            Routes.App.HIGH_VOLUME_BY_GROUP, data=data
        )
        result = self._error_handler.handle_response(
            response, operation="get_high_volume_by_product_group", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    async def get_worst_yield(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Worst Yield list.

        GET/POST /api/App/WorstYield

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = await self._http_client.post(Routes.App.WORST_YIELD, data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = await self._http_client.get(
                Routes.App.WORST_YIELD, params=params if params else None
            )
        result = self._error_handler.handle_response(
            response, operation="get_worst_yield", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    async def get_worst_yield_by_product_group(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Yield by product group sorted by lowest yield.

        POST /api/App/WorstYieldByProductGroup

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of YieldData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(
            Routes.App.WORST_YIELD_BY_GROUP, data=data
        )
        result = self._error_handler.handle_response(
            response, operation="get_worst_yield_by_product_group", allow_empty=True
        )
        if result:
            return [YieldData.model_validate(item) for item in result]
        return []

    # =========================================================================
    # Repair Statistics
    # =========================================================================

    async def get_dynamic_repair(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[RepairStatistics]:
        """
        Calculate repair statistics by custom dimensions (PREVIEW).

        POST /api/App/DynamicRepair

        Args:
            filter_data: WATSFilter object or dict with dimensions and filters

        Returns:
            List of RepairStatistics objects ordered as specified in dimensions
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data) if filter_data else {}

        if ("periodCount" in data or "dateGrouping" in data) and "includeCurrentPeriod" not in data:
            data["includeCurrentPeriod"] = True

        params: Optional[Dict[str, Any]] = None
        if isinstance(data, dict) and data.get("dimensions"):
            dimensions = data.get("dimensions")
            params = {"dimensions": dimensions}
            if len(data.keys()) == 1:
                data = {}

        if not data:
            data = {}

        response = await self._http_client.post(
            Routes.App.DYNAMIC_REPAIR, data=data, params=params
        )
        result = self._error_handler.handle_response(
            response, operation="get_dynamic_repair", allow_empty=True
        )
        if result:
            items = result if isinstance(result, list) else [result]
            return [RepairStatistics.model_validate(item) for item in items]
        return []

    async def get_related_repair_history(
        self, part_number: str, revision: str
    ) -> List[RepairHistoryRecord]:
        """
        Get list of repaired failures related to the part number and revision.

        GET /api/App/RelatedRepairHistory

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of RepairHistoryRecord objects
        """
        params: Dict[str, Any] = {
            "partNumber": part_number,
            "revision": revision,
        }
        response = await self._http_client.get(
            Routes.App.RELATED_REPAIR_HISTORY, params=params
        )
        result = self._error_handler.handle_response(
            response, operation="get_related_repair_history", allow_empty=True
        )
        if result:
            items = result if isinstance(result, list) else [result]
            return [RepairHistoryRecord.model_validate(item) for item in items]
        return []

    # =========================================================================
    # Failure Analysis
    # =========================================================================

    async def get_top_failed(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[TopFailedStep]:
        """
        Get the top failed steps.

        GET/POST /api/App/TopFailed

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            top_count: Maximum number of results (GET only)

        Returns:
            List of TopFailedStep objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = await self._http_client.post(Routes.App.TOP_FAILED, data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            if part_number:
                params["partNumber"] = part_number
            if revision:
                params["revision"] = revision
            if top_count is not None:
                params["topCount"] = top_count
            response = await self._http_client.get(
                Routes.App.TOP_FAILED, params=params if params else None
            )
        result = self._error_handler.handle_response(
            response, operation="get_top_failed", allow_empty=True
        )
        if result:
            items = result if isinstance(result, list) else [result]
            return [TopFailedStep.model_validate(item) for item in items]
        return []

    async def get_test_step_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[StepAnalysisRow]:
        """
        Get step and measurement statistics (PREVIEW).

        POST /api/App/TestStepAnalysis

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of StepAnalysisRow rows
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(Routes.App.TEST_STEP_ANALYSIS, data=data)
        result = self._error_handler.handle_response(
            response, operation="get_test_step_analysis", allow_empty=True
        )
        if result:
            raw_items: List[Any]
            if isinstance(result, list):
                raw_items = result
            else:
                raw_items = [result]
            return [StepAnalysisRow.model_validate(item) for item in raw_items]
        return []

    # =========================================================================
    # Measurements
    # =========================================================================

    @staticmethod
    def _normalize_measurement_path(path: str) -> str:
        """Convert user-friendly path format to API format."""
        if not path:
            return path
        if "¶" in path:
            return path
        if "::" in path:
            step_path, measurement_name = path.rsplit("::", 1)
            step_path = step_path.replace("/", "¶")
            return f"{step_path}¶¶{measurement_name}"
        return path.replace("/", "¶")

    async def get_measurements(
        self, 
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[MeasurementData]:
        """
        Get numeric measurements by measurement path (PREVIEW).

        POST /api/App/Measurements

        Args:
            filter_data: WATSFilter object or dict with filters
            measurement_paths: Measurement path(s) as query parameter

        Returns:
            List of MeasurementData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        params: Dict[str, str] = {}
        
        if "measurement_path" in data:
            measurement_paths = measurement_paths or data.pop("measurement_path")
        if "measurementPath" in data:
            measurement_paths = measurement_paths or data.pop("measurementPath")
            
        if measurement_paths:
            params["measurementPaths"] = self._normalize_measurement_path(measurement_paths)
        
        response = await self._http_client.post(
            Routes.App.MEASUREMENTS, 
            data=data,
            params=params if params else None
        )
        result = self._error_handler.handle_response(
            response, operation="get_measurements", allow_empty=True
        )
        if result:
            all_measurements = []
            items = result if isinstance(result, list) else [result]
            for item in items:
                if isinstance(item, dict) and "measurements" in item:
                    for m in item.get("measurements", []):
                        all_measurements.append(MeasurementData.model_validate(m))
                else:
                    all_measurements.append(MeasurementData.model_validate(item))
            return all_measurements
        return []

    async def get_aggregated_measurements(
        self, 
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[AggregatedMeasurement]:
        """
        Get aggregated numeric measurements by measurement path.

        POST /api/App/AggregatedMeasurements

        Args:
            filter_data: WATSFilter object or dict with filters
            measurement_paths: Measurement path(s) as query parameter

        Returns:
            List of AggregatedMeasurement objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        params: Dict[str, str] = {}
        
        if "measurement_path" in data:
            measurement_paths = measurement_paths or data.pop("measurement_path")
        if "measurementPath" in data:
            measurement_paths = measurement_paths or data.pop("measurementPath")
            
        if measurement_paths:
            params["measurementPaths"] = self._normalize_measurement_path(measurement_paths)
            
        response = await self._http_client.post(
            Routes.App.AGGREGATED_MEASUREMENTS, 
            data=data,
            params=params if params else None
        )
        result = self._error_handler.handle_response(
            response, operation="get_aggregated_measurements", allow_empty=True
        )
        if result:
            all_measurements = []
            items = result if isinstance(result, list) else [result]
            for item in items:
                if isinstance(item, dict) and "measurements" in item:
                    for m in item.get("measurements", []):
                        all_measurements.append(AggregatedMeasurement.model_validate(m))
                else:
                    all_measurements.append(AggregatedMeasurement.model_validate(item))
            return all_measurements
        return []

    # =========================================================================
    # OEE (Overall Equipment Effectiveness)
    # =========================================================================

    async def get_oee_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> Optional[OeeAnalysisResult]:
        """
        Overall Equipment Effectiveness - analysis.

        POST /api/App/OeeAnalysis

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            OeeAnalysisResult object or None
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(Routes.App.OEE_ANALYSIS, data=data)
        result = self._error_handler.handle_response(
            response, operation="get_oee_analysis", allow_empty=True
        )
        if result:
            return OeeAnalysisResult.model_validate(result)
        return None

    # =========================================================================
    # Serial Number and Unit History
    # =========================================================================

    async def get_serial_number_history(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Serial Number History.

        POST /api/App/SerialNumberHistory

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(Routes.App.SERIAL_NUMBER_HISTORY, data=data)
        result = self._error_handler.handle_response(
            response, operation="get_serial_number_history", allow_empty=True
        )
        if result:
            return [ReportHeader.model_validate(item) for item in result]
        return []

    async def get_uut_reports(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        serial_number: Optional[str] = None,
        status: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Returns UUT report header info.

        GET/POST /api/App/UutReport

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            serial_number: Filter by serial number (GET only)
            status: Filter by status (GET only)
            top_count: Maximum results (GET only)

        Returns:
            List of ReportHeader objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = await self._http_client.post(Routes.App.UUT_REPORT, data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            if part_number:
                params["partNumber"] = part_number
            if revision:
                params["revision"] = revision
            if serial_number:
                params["serialNumber"] = serial_number
            if status:
                params["status"] = status
            if top_count is not None:
                params["topCount"] = top_count
            response = await self._http_client.get(
                Routes.App.UUT_REPORT, params=params if params else None
            )
        result = self._error_handler.handle_response(
            response, operation="get_uut_reports", allow_empty=True
        )
        if result:
            return [ReportHeader.model_validate(item) for item in result]
        return []

    async def get_uur_reports(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Returns UUR report header info.

        POST /api/App/UurReport

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = await self._http_client.post(Routes.App.UUR_REPORT, data=data)
        result = self._error_handler.handle_response(
            response, operation="get_uur_reports", allow_empty=True
        )
        if result:
            return [ReportHeader.model_validate(item) for item in result]
        return []

    # =========================================================================
    # Unit Flow Endpoints (Internal API)
    # =========================================================================

    async def query_unit_flow(
        self, 
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query unit flow data with filters.
        
        POST /api/internal/UnitFlow
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This is the main endpoint for unit flow queries. Returns nodes
        and links representing how units flow through production.
        
        Args:
            filter_data: UnitFlowFilter or dict with filter parameters
            
        Returns:
            Raw response data containing nodes and links, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW, data=data)

    async def get_unit_flow_links(self) -> List[UnitFlowLink]:
        """
        Get all unit flow links.
        
        GET /api/internal/UnitFlow/Links
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns the links (edges) between nodes in the unit flow diagram.
        
        Returns:
            List of UnitFlowLink objects
        """
        data = await self._internal_get(Routes.Analytics.Internal.UNIT_FLOW_LINKS)
        if data and isinstance(data, list):
            return [UnitFlowLink.model_validate(item) for item in data]
        return []

    async def get_unit_flow_nodes(self) -> List[UnitFlowNode]:
        """
        Get all unit flow nodes.
        
        GET /api/internal/UnitFlow/Nodes
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns the nodes (operations/processes) in the unit flow diagram.
        
        Returns:
            List of UnitFlowNode objects
        """
        data = await self._internal_get(Routes.Analytics.Internal.UNIT_FLOW_NODES)
        if data and isinstance(data, list):
            return [UnitFlowNode.model_validate(item) for item in data]
        return []

    async def query_unit_flow_by_serial_numbers(
        self, 
        serial_numbers: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query unit flow for specific serial numbers.
        
        POST /api/internal/UnitFlow/SN
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Traces the production flow path for specific units.
        
        Args:
            serial_numbers: List of serial numbers to query
            filter_data: Additional filter parameters
            
        Returns:
            Raw response data containing flow information, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        data["serialNumbers"] = serial_numbers
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW_SN, data=data)

    async def set_unit_flow_split_by(
        self, 
        split_by: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Set the split-by dimension for unit flow analysis.
        
        POST /api/internal/UnitFlow/SplitBy
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Splits the flow diagram by a specific dimension (e.g., station, location).
        
        Args:
            split_by: Dimension to split by (e.g., "stationName", "location")
            filter_data: Additional filter parameters
            
        Returns:
            Raw response data with split flow, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        data["splitBy"] = split_by
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW_SPLIT_BY, data=data)

    async def set_unit_flow_order(
        self, 
        unit_order: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Set the unit ordering for flow analysis.
        
        POST /api/internal/UnitFlow/UnitOrder
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Controls how units are ordered in the flow visualization.
        
        Args:
            unit_order: Order specification (e.g., "startTime", "serialNumber")
            filter_data: Additional filter parameters
            
        Returns:
            Raw response data with ordered flow, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        data["unitOrder"] = unit_order
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW_UNIT_ORDER, data=data)

    async def get_unit_flow_units(self) -> List[UnitFlowUnit]:
        """
        Get individual units from the unit flow.
        
        GET /api/internal/UnitFlow/Units
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns the list of individual units that have traversed the flow.
        
        Returns:
            List of UnitFlowUnit objects
        """
        data = await self._internal_get(Routes.Analytics.Internal.UNIT_FLOW_UNITS)
        if data and isinstance(data, list):
            return [UnitFlowUnit.model_validate(item) for item in data]
        return []

    async def set_unit_flow_visibility(
        self,
        show_list: Optional[List[str]] = None,
        hide_list: Optional[List[str]] = None,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Control visibility of operations in the unit flow.
        
        POST /api/internal/UnitFlow (with showList/hideList)
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Show or hide specific operations/nodes in the flow diagram.
        
        Args:
            show_list: List of operation IDs/names to show
            hide_list: List of operation IDs/names to hide
            filter_data: Additional filter parameters
            
        Returns:
            Raw response data with updated visibility, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        if show_list is not None:
            data["showList"] = show_list
        if hide_list is not None:
            data["hideList"] = hide_list
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW, data=data)

    async def expand_unit_flow_operations(
        self,
        expand: bool = True,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Expand or collapse operations in the unit flow.
        
        POST /api/internal/UnitFlow (with expandOperations)
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Controls whether operations are shown expanded or collapsed.
        
        Args:
            expand: True to expand, False to collapse
            filter_data: Additional filter parameters
            
        Returns:
            Raw response data with updated expansion, or None
        """
        if filter_data is None:
            data = {}
        elif isinstance(filter_data, UnitFlowFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        data["expandOperations"] = expand
        
        return await self._internal_post(Routes.Analytics.Internal.UNIT_FLOW, data=data)

    # =========================================================================
    # Step/Measurement Filter Endpoints (Internal API)
    # =========================================================================

    async def get_measurement_list_simple(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """
        Get measurement list using simple query parameters.
        
        GET /api/internal/App/MeasurementList
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Simple version that queries measurements by product group, level,
        and time range with step/sequence filters.
        
        Args:
            product_group_id: Product group ID (required)
            level_id: Level ID (required)
            days: Number of days to query (required)
            step_filters: XML string defining step filters (required)
            sequence_filters: XML string defining sequence filters (required)
            
        Returns:
            List of MeasurementListItem objects.
        """
        params = {
            "productGroupId": product_group_id,
            "levelId": level_id,
            "days": days,
            "stepFilters": step_filters,
            "sequenceFilters": sequence_filters,
        }
        
        data = await self._internal_get(Routes.Analytics.Internal.MEASUREMENT_LIST, params=params)
        
        if data and isinstance(data, list):
            return [MeasurementListItem.model_validate(item) for item in data]
        return []

    async def get_measurement_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """
        Get measurement list with full filter support.
        
        POST /api/internal/App/MeasurementList
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Advanced version that allows full filter customization with
        step and sequence filters.
        
        Args:
            filter_data: Filter parameters (partNumber, testOperation, etc.)
            step_filters: XML string defining step filters (required)
            sequence_filters: XML string defining sequence filters (required)
            
        Returns:
            List of MeasurementListItem objects with measurement details.
        """
        params = {
            "stepFilters": step_filters,
            "sequenceFilters": sequence_filters,
        }
        
        data = await self._internal_post(
            Routes.Analytics.Internal.MEASUREMENT_LIST,
            data=filter_data,
            params=params
        )
        
        if data and isinstance(data, list):
            return [MeasurementListItem.model_validate(item) for item in data]
        return []

    async def get_step_status_list_simple(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """
        Get step status list using simple query parameters.
        
        GET /api/internal/App/StepStatusList
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Simple version that queries step statuses by product group, level,
        and time range with step/sequence filters.
        
        Args:
            product_group_id: Product group ID (required)
            level_id: Level ID (required)
            days: Number of days to query (required)
            step_filters: XML string defining step filters (required)
            sequence_filters: XML string defining sequence filters (required)
            
        Returns:
            List of StepStatusItem objects.
        """
        params = {
            "productGroupId": product_group_id,
            "levelId": level_id,
            "days": days,
            "stepFilters": step_filters,
            "sequenceFilters": sequence_filters,
        }
        
        data = await self._internal_get(Routes.Analytics.Internal.STEP_STATUS_LIST, params=params)
        
        if data and isinstance(data, list):
            return [StepStatusItem.model_validate(item) for item in data]
        return []

    async def get_step_status_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """
        Get step status list with full filter support.
        
        POST /api/internal/App/StepStatusList
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Advanced version that allows full filter customization with
        step and sequence filters.
        
        Args:
            filter_data: Filter parameters (partNumber, status, etc.)
            step_filters: XML string defining step filters (required)
            sequence_filters: XML string defining sequence filters (required)
            
        Returns:
            List of StepStatusItem objects with step status details.
        """
        params = {
            "stepFilters": step_filters,
            "sequenceFilters": sequence_filters,
        }
        
        data = await self._internal_post(
            Routes.Analytics.Internal.STEP_STATUS_LIST,
            data=filter_data,
            params=params
        )
        
        if data and isinstance(data, list):
            return [StepStatusItem.model_validate(item) for item in data]
        return []

    async def get_top_failed_simple(
        self,
        part_number: str,
        process_code: str,
        product_group_id: str,
        level_id: str,
        days: int,
        count: int = 10
    ) -> List[TopFailedStep]:
        """
        Get top failed steps using simple query parameters.
        
        GET /api/internal/App/TopFailed
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Simple version that queries top failed steps by part number, process code,
        product group, level, and time range.
        
        Args:
            part_number: Part number of reports (required)
            process_code: Process code of reports (required)
            product_group_id: Product group ID (required)
            level_id: Level ID (required)
            days: Number of days to query (required)
            count: Number of items to return (default 10)
            
        Returns:
            List of TopFailedStep objects with failure statistics.
        """
        params = {
            "partNumber": part_number,
            "processCode": process_code,
            "productGroupId": product_group_id,
            "levelId": level_id,
            "days": days,
            "count": count,
        }
        
        data = await self._internal_get(Routes.Analytics.Internal.TOP_FAILED, params=params)
        
        if data and isinstance(data, list):
            return [TopFailedStep.model_validate(item) for item in data]
        return []

    async def get_top_failed_advanced(
        self,
        filter_data: Dict[str, Any],
        top_count: Optional[int] = None
    ) -> List[TopFailedStep]:
        """
        Get top failed steps with full filter support (advanced version).
        
        POST /api/internal/App/TopFailed
        
        This advanced version allows full filter customization beyond what
        the standard get_top_failed() method supports. Use this when you need
        to specify complex filter combinations.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            filter_data: Filter parameters dictionary. Supported keys include:
                - partNumber: Filter by product part number
                - testOperation: Filter by test operation
                - startDate/endDate: Date range filters
                - productGroup: Filter by product group
                - Additional custom filter parameters
            top_count: Optional override for maximum results (topCount)
            
        Returns:
            List of TopFailedStep objects with failure statistics.
            
        Example:
            >>> steps = await repo.get_top_failed_advanced(
            ...     {"partNumber": "ABC-123", "testOperation": "FCT"},
            ...     top_count=10
            ... )
        """
        if top_count is not None:
            filter_data = dict(filter_data)
            filter_data["topCount"] = top_count
        
        data = await self._internal_post(Routes.Analytics.Internal.TOP_FAILED, data=filter_data)
        
        if data and isinstance(data, list):
            return [TopFailedStep.model_validate(item) for item in data]
        return []
