"""Analytics service - thin sync wrapper around AsyncAnalyticsService.

This module provides synchronous access to AsyncAnalyticsService methods.
All business logic is maintained in async_service.py (source of truth).
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .async_service import AsyncAnalyticsService
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
    UnitFlowNode,
    UnitFlowLink,
    UnitFlowUnit,
    UnitFlowFilter,
    UnitFlowResult,
    MeasurementListItem,
    StepStatusItem,
)
from ..report.models import WATSFilter, ReportHeader
from ...shared.paths import StepPath
from ...core.sync_runner import run_sync


class AnalyticsService:
    """
    Synchronous wrapper for AsyncAnalyticsService.

    Provides sync access to all async analytics service operations.
    All business logic is in AsyncAnalyticsService.
    """

    def __init__(self, async_service: AsyncAnalyticsService = None, *, repository=None) -> None:
        """
        Initialize with AsyncAnalyticsService or repository.

        Args:
            async_service: AsyncAnalyticsService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncAnalyticsService(repository)
            self._repository = repository
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(cls, repository: AsyncAnalyticsRepository) -> "AnalyticsService":
        """Create AnalyticsService from an AsyncAnalyticsRepository."""
        async_service = AsyncAnalyticsService(repository)
        return cls(async_service)

    # =========================================================================
    # System Info
    # =========================================================================

    def get_version(self) -> Optional[str]:
        """Get WATS API version information.

        Returns:
            Version string or None if not available.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_version())

    def get_processes(
        self,
        include_test_operations: Optional[bool] = None,
        include_repair_operations: Optional[bool] = None,
        include_wip_operations: Optional[bool] = None,
        include_inactive_processes: Optional[bool] = None,
    ) -> List[ProcessInfo]:
        """Get all defined test processes/operations.

        Args:
            include_test_operations: Include test operations (default: True).
            include_repair_operations: Include repair operations.
            include_wip_operations: Include WIP operations.
            include_inactive_processes: Include inactive processes.

        Returns:
            List of ProcessInfo objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_processes(
            include_test_operations=include_test_operations,
            include_repair_operations=include_repair_operations,
            include_wip_operations=include_wip_operations,
            include_inactive_processes=include_inactive_processes,
        ))

    def get_levels(self) -> List[LevelInfo]:
        """Get all production levels.

        Returns:
            List of LevelInfo objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_levels())

    def get_product_groups(
        self,
        include_filters: Optional[bool] = None
    ) -> List[ProductGroup]:
        """Get all product groups.

        Args:
            include_filters: Whether to include filter definitions.

        Returns:
            List of ProductGroup objects.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_product_groups(include_filters=include_filters))

    # =========================================================================
    # Yield Statistics
    # =========================================================================

    def get_dynamic_yield(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """Get dynamic yield statistics by custom dimensions (PREVIEW).

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            List of YieldData with statistics by requested dimensions.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid or missing required fields.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_dynamic_yield(filter_data))

    def get_yield_summary(
        self,
        part_number: str,
        revision: Optional[str] = None,
        days: int = 30,
    ) -> List[YieldData]:
        """Get yield summary for a product over a time period.

        Args:
            part_number: Product part number.
            revision: Optional revision filter.
            days: Number of days to look back (default: 30).

        Returns:
            List of YieldData for the product.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If part_number is empty.
            NotFoundError: If product not found.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_yield_summary(
            part_number=part_number,
            revision=revision,
            days=days,
        ))

    def get_station_yield(
        self,
        station_name: str,
        days: int = 7,
    ) -> List[YieldData]:
        """Get yield statistics for a specific test station.

        Args:
            station_name: Name of the test station.
            days: Number of days to look back (default: 7).

        Returns:
            List of YieldData for the station.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If station_name is empty.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_station_yield(
            station_name=station_name,
            days=days,
        ))

    def get_dynamic_repair(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[RepairStatistics]:
        """Get dynamic repair statistics by custom dimensions (PREVIEW).

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            List of RepairStatistics with repair data by dimensions.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_dynamic_repair(filter_data))

    def get_volume_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """Get volume/yield statistics.

        Args:
            filter_data: Optional WATSFilter for custom filtering.
            product_group: Filter by product group name.
            level: Filter by production level.

        Returns:
            List of YieldData with volume statistics.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_volume_yield(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
        ))

    def get_worst_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """Get worst yield statistics (products with lowest yield).

        Args:
            filter_data: Optional WATSFilter for custom filtering.
            product_group: Filter by product group name.
            level: Filter by production level.

        Returns:
            List of YieldData sorted by worst yield.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_worst_yield(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
        ))

    def get_worst_yield_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """Get worst yield statistics grouped by product group.

        Args:
            filter_data: WATSFilter with query parameters.

        Returns:
            List of YieldData grouped by product group.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_worst_yield_by_product_group(filter_data))

    # =========================================================================
    # High Volume Analysis
    # =========================================================================

    def get_high_volume(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """Get high volume product list (products with most units tested).

        Args:
            filter_data: Optional WATSFilter for custom filtering.
            product_group: Filter by product group name.
            level: Filter by production level.

        Returns:
            List of YieldData sorted by volume (highest first).

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_high_volume(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
        ))

    def get_high_volume_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """Get yield statistics grouped by product group, sorted by volume.

        Args:
            filter_data: WATSFilter with query parameters.

        Returns:
            List of YieldData grouped by product group, sorted by volume.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_high_volume_by_product_group(filter_data))

    # =========================================================================
    # Failure Analysis
    # =========================================================================

    def get_top_failed(
        self,
        filter_data: Optional[WATSFilter] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[TopFailedStep]:
        """Get top failed test steps.

        Args:
            filter_data: Optional WATSFilter for custom filtering.
            product_group: Filter by product group name.
            level: Filter by production level.
            part_number: Filter by product part number.
            revision: Filter by revision.
            top_count: Maximum number of results to return.

        Returns:
            List of TopFailedStep sorted by failure count.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_top_failed(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            top_count=top_count,
        ))

    def get_related_repair_history(
        self, part_number: str, revision: str
    ) -> List[RepairHistoryRecord]:
        """Get list of repaired failures related to the part number and revision.

        Args:
            part_number: Product part number.
            revision: Product revision.

        Returns:
            List of RepairHistoryRecord with repair data.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If part_number or revision is empty.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_related_repair_history(part_number, revision))

    def get_test_step_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[StepAnalysisRow]:
        """Get step and measurement statistics (PREVIEW).

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            List of StepAnalysisRow with step statistics.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_test_step_analysis(filter_data))

    def get_test_step_analysis_for_operation(
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

        Args:
            part_number: Product part number.
            test_operation: Test operation name or code.
            revision: Optional revision filter.
            days: Number of days to look back (default: 30).
            run: Run number (default: 1).
            max_count: Maximum records to return (default: 10000).

        Returns:
            List of StepAnalysisRow with step statistics.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If part_number or test_operation is empty.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_test_step_analysis_for_operation(
            part_number=part_number,
            test_operation=test_operation,
            revision=revision,
            days=days,
            run=run,
            max_count=max_count,
        ))

    # =========================================================================
    # Measurements
    # =========================================================================

    def get_measurements(
        self,
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[MeasurementData]:
        """Get numeric measurements by measurement path (PREVIEW).

        Args:
            filter_data: WATSFilter or dict with query parameters.
            measurement_paths: Optional measurement path filter.

        Returns:
            List of MeasurementData with numeric values.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_measurements(
            filter_data,
            measurement_paths=measurement_paths,
        ))

    def get_aggregated_measurements(
        self,
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[AggregatedMeasurement]:
        """Get aggregated numeric measurements by measurement path.

        Args:
            filter_data: WATSFilter or dict with query parameters.
            measurement_paths: Optional measurement path filter.

        Returns:
            List of AggregatedMeasurement with statistics (avg, min, max, etc.).

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_aggregated_measurements(
            filter_data,
            measurement_paths=measurement_paths,
        ))

    # =========================================================================
    # OEE (Overall Equipment Effectiveness)
    # =========================================================================

    def get_oee_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> Optional[OeeAnalysisResult]:
        """Overall Equipment Effectiveness - analysis.

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            OeeAnalysisResult with availability, performance, quality, and OEE.
            OEE = (availability * performance * quality) / 10000.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_oee_analysis(filter_data))

    # =========================================================================
    # Serial Number and Unit History
    # =========================================================================

    def get_serial_number_history(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """Serial Number History.

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            List of ReportHeader for the serial number history.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_serial_number_history(filter_data))

    def get_uut_reports(
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
        """Returns UUT report header info.

        Args:
            filter_data: Optional WATSFilter for custom filtering.
            product_group: Filter by product group name.
            level: Filter by production level.
            part_number: Filter by product part number.
            revision: Filter by revision.
            serial_number: Filter by serial number.
            status: Filter by status (Passed/Failed).
            top_count: Maximum number of results.

        Returns:
            List of ReportHeader for matching UUT reports.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_uut_reports(
            filter_data=filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            serial_number=serial_number,
            status=status,
            top_count=top_count,
        ))

    def get_uur_reports(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """Returns UUR report header info.

        Args:
            filter_data: WATSFilter or dict with query parameters.

        Returns:
            List of ReportHeader for matching UUR (repair) reports.

        Raises:
            AuthenticationError: If API token is invalid or expired.
            ValidationError: If filter_data is invalid.
            APIError: If the server returns an error response.
            PyWATSError: For other unexpected errors.
        """
        return run_sync(self._async_service.get_uur_reports(filter_data))

    # =========================================================================
    # Unit Flow Methods (⚠️ INTERNAL API)
    # =========================================================================

    def get_unit_flow(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Get complete unit flow data with nodes and links. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_unit_flow(filter_data))

    def get_flow_links(self) -> List[UnitFlowLink]:
        """Get all links from the current unit flow state. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_flow_links())

    def get_flow_nodes(self) -> List[UnitFlowNode]:
        """Get all nodes from the current unit flow state. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_flow_nodes())

    def trace_serial_numbers(
        self,
        serial_numbers: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Optional[UnitFlowResult]:
        """Trace the production flow for specific serial numbers. ⚠️ INTERNAL"""
        return run_sync(self._async_service.trace_serial_numbers(
            serial_numbers=serial_numbers,
            filter_data=filter_data,
        ))

    def get_flow_units(self) -> List[UnitFlowUnit]:
        """Get all individual units from the unit flow. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_flow_units())

    def split_flow_by(
        self,
        dimension: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Split the unit flow by a specific dimension. ⚠️ INTERNAL"""
        return run_sync(self._async_service.split_flow_by(
            dimension=dimension,
            filter_data=filter_data,
        ))

    def set_unit_order(
        self,
        order_by: str,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Set how units are ordered in the flow visualization. ⚠️ INTERNAL"""
        return run_sync(self._async_service.set_unit_order(
            order_by=order_by,
            filter_data=filter_data,
        ))

    def set_unit_flow_visibility(
        self,
        show_operations: Optional[List[str]] = None,
        hide_operations: Optional[List[str]] = None,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Control visibility of operations in the unit flow. ⚠️ INTERNAL"""
        return run_sync(self._async_service.set_unit_flow_visibility(
            show_operations=show_operations,
            hide_operations=hide_operations,
            filter_data=filter_data,
        ))

    def show_operations(
        self,
        operation_ids: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Show specific operations in the unit flow diagram. ⚠️ INTERNAL"""
        return run_sync(self._async_service.show_operations(
            operation_ids=operation_ids,
            filter_data=filter_data,
        ))

    def hide_operations(
        self,
        operation_ids: List[str],
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Hide specific operations from the unit flow diagram. ⚠️ INTERNAL"""
        return run_sync(self._async_service.hide_operations(
            operation_ids=operation_ids,
            filter_data=filter_data,
        ))

    def expand_operations(
        self,
        expand: bool = True,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> UnitFlowResult:
        """Expand or collapse operations in the unit flow. ⚠️ INTERNAL"""
        return run_sync(self._async_service.expand_operations(
            expand=expand,
            filter_data=filter_data,
        ))

    def get_bottlenecks(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None,
        min_yield_threshold: float = 95.0
    ) -> List[UnitFlowNode]:
        """Find production bottlenecks (nodes with yield below threshold). ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_bottlenecks(
            filter_data=filter_data,
            min_yield_threshold=min_yield_threshold,
        ))

    def get_flow_summary(
        self,
        filter_data: Optional[Union[UnitFlowFilter, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get a summary of the unit flow statistics. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_flow_summary(filter_data))

    # =========================================================================
    # Step/Measurement Filter Methods (⚠️ INTERNAL API)
    # =========================================================================

    def get_measurement_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """Get measurement list with step/sequence filters. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_measurement_list(
            filter_data=filter_data,
            step_filters=step_filters,
            sequence_filters=sequence_filters,
        ))

    def get_measurement_list_by_product(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[MeasurementListItem]:
        """Get measurement list using simple parameters. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_measurement_list_by_product(
            product_group_id=product_group_id,
            level_id=level_id,
            days=days,
            step_filters=step_filters,
            sequence_filters=sequence_filters,
        ))

    def get_step_status_list(
        self,
        filter_data: Dict[str, Any],
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """Get step status list with step/sequence filters. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_step_status_list(
            filter_data=filter_data,
            step_filters=step_filters,
            sequence_filters=sequence_filters,
        ))

    def get_step_status_list_by_product(
        self,
        product_group_id: str,
        level_id: str,
        days: int,
        step_filters: str,
        sequence_filters: str
    ) -> List[StepStatusItem]:
        """Get step status list using simple parameters. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_step_status_list_by_product(
            product_group_id=product_group_id,
            level_id=level_id,
            days=days,
            step_filters=step_filters,
            sequence_filters=sequence_filters,
        ))

    def get_top_failed_internal(
        self,
        filter_data: Dict[str, Any],
        top_count: Optional[int] = None
    ) -> List[TopFailedStep]:
        """Get top failed steps with advanced filter support. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_top_failed_internal(
            filter_data=filter_data,
            top_count=top_count,
        ))

    def get_top_failed_by_product(
        self,
        part_number: str,
        process_code: str,
        product_group_id: str,
        level_id: str,
        days: int,
        count: int = 10
    ) -> List[TopFailedStep]:
        """Get top failed steps using simple parameters. ⚠️ INTERNAL"""
        return run_sync(self._async_service.get_top_failed_by_product(
            part_number=part_number,
            process_code=process_code,
            product_group_id=product_group_id,
            level_id=level_id,
            days=days,
            count=count,
        ))

