"""Async Analytics service - business logic layer.

All async business operations for statistics, KPIs, yield analysis, and dashboard data.
Maps to the WATS /api/App/* endpoints (backend naming).

Includes internal API methods (marked with ⚠️ INTERNAL) that use undocumented
endpoints. These may change without notice and should be used with caution.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from .async_repository import AsyncAnalyticsRepository
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
from ...shared.paths import normalize_path, normalize_paths, StepPath

logger = logging.getLogger(__name__)


class AsyncAnalyticsService:
    """
    Async Analytics/Statistics business logic layer.

    Provides high-level async operations for yield statistics, KPIs, failure analysis,
    and production analytics. This module wraps the WATS /api/App/* endpoints.
    
    Includes internal API methods for Unit Flow and measurement filtering.
    """

    def __init__(self, repository: AsyncAnalyticsRepository) -> None:
        """
        Initialize with AsyncAnalyticsRepository.

        Args:
            repository: AsyncAnalyticsRepository instance for data access
        """
        self._repository = repository

    # =========================================================================
    # System Info
    # =========================================================================

    async def get_version(self) -> Optional[str]:
        """
        Get WATS API version information.

        Returns:
            Version string (e.g., "24.1.0") or None if not available
        """
        return await self._repository.get_version()

    async def get_processes(
        self,
        include_test_operations: Optional[bool] = None,
        include_repair_operations: Optional[bool] = None,
        include_wip_operations: Optional[bool] = None,
        include_inactive_processes: Optional[bool] = None,
    ) -> List[ProcessInfo]:
        """
        Get all defined test processes/operations.

        Args:
            include_test_operations: Include processes marked as IsTestOperation
            include_repair_operations: Include processes marked as IsRepairOperation
            include_wip_operations: Include processes marked as IsWipOperation
            include_inactive_processes: Include inactive processes

        Returns:
            List of ProcessInfo objects
        """
        return await self._repository.get_processes(
            include_test_operations=include_test_operations,
            include_repair_operations=include_repair_operations,
            include_wip_operations=include_wip_operations,
            include_inactive_processes=include_inactive_processes,
        )

    async def get_levels(self) -> List[LevelInfo]:
        """
        Get all production levels.

        Returns:
            List of LevelInfo objects
        """
        return await self._repository.get_levels()

    async def get_product_groups(
        self,
        include_filters: Optional[bool] = None
    ) -> List[ProductGroup]:
        """
        Get all product groups.

        Args:
            include_filters: Include or exclude product group filters

        Returns:
            List of ProductGroup objects
        """
        return await self._repository.get_product_groups(include_filters=include_filters)

    # =========================================================================
    # Yield Statistics
    # =========================================================================

    async def get_dynamic_yield(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Get dynamic yield statistics by custom dimensions (PREVIEW).

        Args:
            filter_data: WATSFilter with dimensions and filters

        Returns:
            List of YieldData objects
        """
        return await self._repository.get_dynamic_yield(filter_data)

    async def get_yield_summary(
        self,
        part_number: str,
        revision: Optional[str] = None,
        days: int = 30,
    ) -> List[YieldData]:
        """
        Get yield summary for a product over a time period.
        
        Convenience wrapper that creates a WATSFilter internally.
        
        Args:
            part_number: Product part number
            revision: Optional product revision
            days: Number of days to include (default: 30)
            
        Returns:
            List of YieldData objects
        """
        filter_data = WATSFilter(
            part_number=part_number,
            revision=revision,
            period_count=days,
            dimensions="partNumber;period",
        )
        return await self.get_dynamic_yield(filter_data)

    async def get_station_yield(
        self,
        station_name: str,
        days: int = 7,
    ) -> List[YieldData]:
        """
        Get yield statistics for a specific test station.
        
        Convenience wrapper that creates a WATSFilter internally.
        
        Args:
            station_name: Test station name
            days: Number of days to include (default: 7)
            
        Returns:
            List of YieldData objects
        """
        filter_data = WATSFilter(
            station_name=station_name,
            period_count=days,
            dimensions="stationName;period",
        )
        return await self.get_dynamic_yield(filter_data)

    async def get_dynamic_repair(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[RepairStatistics]:
        """
        Get dynamic repair statistics by custom dimensions (PREVIEW).

        Args:
            filter_data: WATSFilter with dimensions and filters

        Returns:
            List of RepairStatistics objects with repair counts and rates
        """
        return await self._repository.get_dynamic_repair(filter_data)

    async def get_volume_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get volume/yield statistics.

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects
        """
        return await self._repository.get_volume_yield(
            filter_data=filter_data, product_group=product_group, level=level
        )

    async def get_worst_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get worst yield statistics (products with lowest yield).

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects sorted by worst yield first
        """
        return await self._repository.get_worst_yield(
            filter_data=filter_data, product_group=product_group, level=level
        )

    async def get_worst_yield_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """
        Get worst yield statistics grouped by product group.

        Args:
            filter_data: WATSFilter with parameters

        Returns:
            List of YieldData objects grouped by product group
        """
        return await self._repository.get_worst_yield_by_product_group(filter_data)

    # =========================================================================
    # High Volume Analysis
    # =========================================================================

    async def get_high_volume(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get high volume product list (products with most units tested).

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects sorted by highest volume first
        """
        return await self._repository.get_high_volume(
            filter_data=filter_data, product_group=product_group, level=level
        )

    async def get_high_volume_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """
        Get yield statistics grouped by product group, sorted by volume.

        Args:
            filter_data: WATSFilter with parameters

        Returns:
            List of YieldData objects grouped by product group
        """
        return await self._repository.get_high_volume_by_product_group(filter_data)

    # =========================================================================
    # Failure Analysis
    # =========================================================================

    async def get_top_failed(
        self,
        filter_data: Optional[WATSFilter] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[TopFailedStep]:
        """
        Get top failed test steps.

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            top_count: Maximum results (GET only)

        Returns:
            List of TopFailedStep objects with failure statistics
        """
        return await self._repository.get_top_failed(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            top_count=top_count,
        )

    async def get_related_repair_history(
        self, part_number: str, revision: str
    ) -> List[RepairHistoryRecord]:
        """
        Get list of repaired failures related to the part number and revision.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of RepairHistoryRecord objects with repair details
        """
        return await self._repository.get_related_repair_history(part_number, revision)

    async def get_test_step_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[StepAnalysisRow]:
        """
        Get step and measurement statistics (PREVIEW).

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of StepAnalysisRow rows
        """
        return await self._repository.get_test_step_analysis(filter_data)

    async def get_test_step_analysis_for_operation(
        self,
        part_number: str,
        test_operation: str,
        *,
        revision: Optional[str] = None,
        days: int = 30,
        run: int = 1,
        max_count: int = 10000,
    ) -> List[StepAnalysisRow]:
        """Convenience wrapper for TestStepAnalysis.

        A simplified interface that automatically creates the filter object
        with sensible defaults for common use cases.

        Args:
            part_number: Product part number (required).
            test_operation: Test operation name (required).
            revision: Product revision (optional).
            days: Number of days to look back from now (default: 30).
            run: Run number to analyze (default: 1 for first run).
            max_count: Maximum number of results (default: 10000).

        Returns:
            List[StepAnalysisRow]: Typed step analysis results.

        Raises:
            ValueError: If part_number or test_operation is empty.

        Example:
            >>> # Simple call with just required parameters
            >>> analysis = await api.analytics.get_test_step_analysis_for_operation(
            ...     part_number="PCBA-001",
            ...     test_operation="FCT"
            ... )
            >>> for row in analysis:
            ...     print(f"{row.step_name}: {row.step_count} tests")
        """
        if not part_number:
            raise ValueError("part_number is required")
        if not test_operation:
            raise ValueError("test_operation is required")

        filter_data = WATSFilter(
            part_number=part_number,
            test_operation=test_operation,
            revision=revision,
            max_count=max_count,
            date_from=datetime.now() - timedelta(days=days),
            run=run,
        )
        return await self.get_test_step_analysis(filter_data)

    # =========================================================================
    # Measurements
    # =========================================================================

    async def get_measurements(
        self,
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[MeasurementData]:
        """
        Get numeric measurements by measurement path (PREVIEW).

        IMPORTANT: Requires partNumber and testOperation filters to avoid timeout.

        Args:
            filter_data: WATSFilter object or dict with filters
            measurement_paths: Measurement path(s) as query parameter

        Returns:
            List of MeasurementData objects with individual measurement values
        """
        return await self._repository.get_measurements(
            filter_data, measurement_paths=measurement_paths
        )

    async def get_aggregated_measurements(
        self,
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[AggregatedMeasurement]:
        """
        Get aggregated numeric measurements by measurement path.

        IMPORTANT: Requires partNumber and testOperation filters to avoid timeout.

        Args:
            filter_data: WATSFilter object or dict with filters
            measurement_paths: Measurement path(s) as query parameter

        Returns:
            List of AggregatedMeasurement objects with statistics
        """
        return await self._repository.get_aggregated_measurements(
            filter_data, measurement_paths=measurement_paths
        )

    # =========================================================================
    # OEE (Overall Equipment Effectiveness)
    # =========================================================================

    async def get_oee_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> Optional[OeeAnalysisResult]:
        """
        Overall Equipment Effectiveness - analysis.

        Args:
            filter_data: WATSFilter object or dict with filters

        Returns:
            OeeAnalysisResult object with OEE metrics
        """
        return await self._repository.get_oee_analysis(filter_data)

    # =========================================================================
    # Serial Number and Unit History
    # =========================================================================

    async def get_serial_number_history(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Serial Number History.

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        return await self._repository.get_serial_number_history(filter_data)

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
        return await self._repository.get_uut_reports(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            serial_number=serial_number,
            status=status,
            top_count=top_count,
        )

    async def get_uur_reports(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Returns UUR report header info.

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        return await self._repository.get_uur_reports(filter_data)

    # =========================================================================
    # Unit Flow Methods (Internal API)
    # =========================================================================

    async def get_unit_flow(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Get complete unit flow data with nodes and links.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        This is the main method for unit flow analysis. Returns a complete
        flow diagram showing how units traverse through production operations.
        
        Args:
            filter_data: UnitFlowFilter or dict with filter criteria.
                Common filters:
                - part_number: Product part number
                - date_from/date_to: Date range
                - station_name: Filter by station
                - include_passed/include_failed: Filter by status
            
        Returns:
            UnitFlowResult with nodes and links
        """
        raw_data = await self._repository.query_unit_flow(filter_data)
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        # Return empty result instead of None to match sync behavior
        return UnitFlowResult(nodes=[], links=[], units=[], total_units=0)

    async def get_flow_links(self) -> List[UnitFlowLink]:
        """
        Get all links from the current unit flow state.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns:
            List of UnitFlowLink objects
        """
        return await self._repository.get_unit_flow_links()

    async def get_flow_nodes(self) -> List[UnitFlowNode]:
        """
        Get all nodes from the current unit flow state.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns:
            List of UnitFlowNode objects
        """
        return await self._repository.get_unit_flow_nodes()

    async def trace_serial_numbers(
        self,
        serial_numbers: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[UnitFlowResult]:
        """
        Trace the production flow for specific serial numbers.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            serial_numbers: List of serial numbers to trace
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult showing the flow path, or None
        """
        raw_data = await self._repository.query_unit_flow_by_serial_numbers(
            serial_numbers, filter_data
        )
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        return None

    async def get_flow_units(self) -> List[UnitFlowUnit]:
        """
        Get all individual units from the unit flow.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Returns:
            List of UnitFlowUnit objects
        """
        return await self._repository.get_unit_flow_units()

    async def split_flow_by(
        self,
        dimension: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Split the unit flow by a specific dimension.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Splits the flow diagram to show parallel paths based on the
        specified dimension (e.g., by station, location, or purpose).
        
        Args:
            dimension: Dimension to split by. Common values:
                - "stationName": Split by test station
                - "location": Split by physical location
                - "purpose": Split by station purpose
                - "processCode": Split by process type
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with split flow view
        """
        raw_data = await self._repository.set_unit_flow_split_by(dimension, filter_data)
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        return UnitFlowResult(nodes=[], links=[], units=[], total_units=0)

    async def set_unit_order(
        self,
        order_by: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Set how units are ordered in the flow visualization.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            order_by: Order specification. Common values:
                - "startTime": Order by when units entered
                - "endTime": Order by when units exited
                - "serialNumber": Order alphabetically by serial
                - "status": Order by pass/fail status
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with reordered units
        """
        raw_data = await self._repository.set_unit_flow_order(order_by, filter_data)
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        return UnitFlowResult(nodes=[], links=[], units=[], total_units=0)

    async def set_unit_flow_visibility(
        self,
        show_operations: Optional[List[str]] = None,
        hide_operations: Optional[List[str]] = None,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Control visibility of operations in the unit flow.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            show_operations: List of operation IDs/names to show
            hide_operations: List of operation IDs/names to hide
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with updated visibility
        """
        raw_data = await self._repository.set_unit_flow_visibility(
            show_list=show_operations,
            hide_list=hide_operations,
            filter_data=filter_data
        )
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        return UnitFlowResult(nodes=[], links=[], units=[], total_units=0)

    async def show_operations(
        self,
        operation_ids: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Show specific operations in the unit flow diagram.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Use this to focus on specific operations of interest.
        
        Args:
            operation_ids: List of operation IDs or names to show
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with updated visibility
        """
        return await self.set_unit_flow_visibility(
            show_operations=operation_ids,
            filter_data=filter_data
        )

    async def hide_operations(
        self,
        operation_ids: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Hide specific operations from the unit flow diagram.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Use this to simplify the view by hiding less relevant operations.
        
        Args:
            operation_ids: List of operation IDs or names to hide
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with updated visibility
        """
        return await self.set_unit_flow_visibility(
            hide_operations=operation_ids,
            filter_data=filter_data
        )

    async def expand_operations(
        self,
        expand: bool = True,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """
        Expand or collapse operations in the unit flow.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        When expanded, shows detailed sub-operations within each process.
        When collapsed, shows an aggregated view.
        
        Args:
            expand: True to expand operations, False to collapse
            filter_data: Additional filter parameters
            
        Returns:
            UnitFlowResult with updated expansion state
        """
        raw_data = await self._repository.expand_unit_flow_operations(expand, filter_data)
        if raw_data:
            return UnitFlowResult.model_validate(raw_data)
        return UnitFlowResult(nodes=[], links=[], units=[], total_units=0)

    async def get_bottlenecks(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None,
        min_yield_threshold: float = 95.0
    ) -> List[UnitFlowNode]:
        """
        Find production bottlenecks (nodes with yield below threshold).
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            filter_data: Filter criteria for the flow
            min_yield_threshold: Minimum acceptable yield (default 95%)
            
        Returns:
            List of UnitFlowNode objects with yield below threshold
        """
        result = await self.get_unit_flow(filter_data)
        
        bottlenecks = []
        for node in result.nodes or []:
            if node.yield_percent is not None and node.yield_percent < min_yield_threshold:
                bottlenecks.append(node)
        
        # Sort by yield (lowest first)
        bottlenecks.sort(key=lambda n: n.yield_percent if n.yield_percent is not None else 100)
        return bottlenecks

    async def get_flow_summary(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of the unit flow statistics.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Provides high-level metrics about the production flow.
        
        Args:
            filter_data: Filter criteria for the flow query
            
        Returns:
            Dictionary with summary statistics including:
            - total_nodes: Number of nodes in the flow
            - total_links: Number of links in the flow
            - total_units: Total number of units processed
            - passed_units: Number of passed units
            - failed_units: Number of failed units
            - avg_yield: Average yield across all nodes
            - min_yield: Minimum yield
            - max_yield: Maximum yield
        """
        result = await self.get_unit_flow(filter_data)
        
        total_units = 0
        passed_units = 0
        failed_units = 0
        yields = []
        
        for node in result.nodes or []:
            if node.unit_count:
                total_units += node.unit_count
            if node.pass_count:
                passed_units += node.pass_count
            if node.fail_count:
                failed_units += node.fail_count
            if node.yield_percent is not None:
                yields.append(node.yield_percent)
        
        return {
            "total_nodes": len(result.nodes or []),
            "total_links": len(result.links or []),
            "total_units": result.total_units or total_units,
            "passed_units": passed_units,
            "failed_units": failed_units,
            "avg_yield": sum(yields) / len(yields) if yields else 0.0,
            "min_yield": min(yields) if yields else 0.0,
            "max_yield": max(yields) if yields else 0.0,
        }

    # =========================================================================
    # Step/Measurement Filter Methods (Internal API)
    # =========================================================================

    async def get_measurement_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """
        Get measurement list with step/sequence filters.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            filter_data: Filter parameters (partNumber, testOperation, etc.)
            step_filters: XML string defining step filters
            sequence_filters: XML string defining sequence filters
            
        Returns:
            List of MeasurementListItem objects
        """
        return await self._repository.get_measurement_list(
            filter_data, step_filters, sequence_filters
        )

    async def get_measurement_list_by_product(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """
        Get measurement list using simple parameters.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            product_group_id: Product group ID
            level_id: Level ID
            days: Number of days to query
            step_filters: XML string defining step filters
            sequence_filters: XML string defining sequence filters
            
        Returns:
            List of MeasurementListItem objects
        """
        return await self._repository.get_measurement_list_simple(
            product_group_id, level_id, days, step_filters, sequence_filters
        )

    async def get_step_status_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """
        Get step status list with step/sequence filters.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            filter_data: Filter parameters (partNumber, status, etc.)
            step_filters: XML string defining step filters
            sequence_filters: XML string defining sequence filters
            
        Returns:
            List of StepStatusItem objects
        """
        return await self._repository.get_step_status_list(
            filter_data, step_filters, sequence_filters
        )

    async def get_step_status_list_by_product(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """
        Get step status list using simple parameters.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            product_group_id: Product group ID
            level_id: Level ID
            days: Number of days to query
            step_filters: XML string defining step filters
            sequence_filters: XML string defining sequence filters
            
        Returns:
            List of StepStatusItem objects
        """
        return await self._repository.get_step_status_list_simple(
            product_group_id, level_id, days, step_filters, sequence_filters
        )

    async def get_top_failed_internal(
        self,
        filter_data: Dict[str, Any],
        top_count: Optional[int] = None
    ) -> List[TopFailedStep]:
        """
        Get top failed steps with advanced filter support.
        
        Uses internal API endpoint for advanced filtering capabilities
        not available through the public API.
        
        Note: Uses internal API endpoint which may change without notice.
        
        Args:
            filter_data: Filter parameters (partNumber, testOperation, etc.)
            top_count: Optional override for maximum results
            
        Returns:
            List of TopFailedStep objects with failure statistics
            
        See Also:
            get_top_failed_simple: Simplified wrapper with named parameters
        """
        return await self._repository.get_top_failed_advanced(filter_data, top_count)

    async def get_top_failed_by_product(
        self,
        part_number: str,
        process_code: str,
        product_group_id: str,
        level_id: str,
        days: int,
        count: int = 10
    ) -> List[TopFailedStep]:
        """
        Get top failed steps using simple parameters.
        
        ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
        
        Args:
            part_number: Part number
            process_code: Process code
            product_group_id: Product group ID
            level_id: Level ID
            days: Number of days to query
            count: Number of items to return (default 10)
            
        Returns:
            List of TopFailedStep objects with failure statistics
        """
        return await self._repository.get_top_failed_simple(
            part_number, process_code, product_group_id, level_id, days, count
        )
