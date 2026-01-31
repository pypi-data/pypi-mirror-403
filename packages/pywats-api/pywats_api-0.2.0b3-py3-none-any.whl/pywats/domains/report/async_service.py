"""Async Report service - business logic layer.

Async version of the report service for non-blocking operations.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union, Callable, Protocol, overload
from uuid import UUID, uuid4
import logging

from .models import WATSFilter, ReportHeader
from .report_models import UUTReport, UURReport
from .report_models.uut.uut_info import UUTInfo
from .report_models.uur.uur_info import UURInfo
from .report_models.uur.uur_sub_unit import UURSubUnit
from .async_repository import AsyncReportRepository
from .enums import ReportType
from .filter_builders import (
    build_serial_filter,
    build_part_number_filter,
    build_date_range_filter,
    build_subunit_part_filter,
    build_subunit_serial_filter,
)
from .query_helpers import is_uut_report_type, get_expand_fields
from ...shared.stats import QueueProcessingResult

logger = logging.getLogger(__name__)

# Default for recent_headers (days to look back)
DEFAULT_RECENT_DAYS = 7


class StationInfo(Protocol):
    """Protocol for station information provider."""
    name: str
    location: str
    purpose: str


class AsyncReportService:
    """
    Async Report business logic.

    Provides high-level async operations for managing test reports,
    including factory methods for creating UUT and UUR reports.
    """

    def __init__(
        self,
        repository: AsyncReportRepository,
        station_provider: Optional[Callable[[], StationInfo]] = None
    ) -> None:
        """
        Initialize with async repository.

        Args:
            repository: AsyncReportRepository for data access
            station_provider: Optional callable that returns station info
        """
        self._repository = repository
        self._station_provider = station_provider

    # =========================================================================
    # Factory Methods (Sync - no repository calls)
    # =========================================================================

    def create_uut_report(
        self,
        operator: str,
        part_number: str,
        revision: str,
        serial_number: str,
        operation_type: int,
        *,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> UUTReport:
        """
        Create a new UUT (Unit Under Test) report.

        This is a factory method that creates a report pre-populated with
        station information from the station_provider if available.

        Args:
            operator: Operator name
            part_number: Product part number
            revision: Product revision
            serial_number: Unit serial number
            operation_type: Process/operation code (e.g., 100 for FCT)
            station_name: Override station name
            location: Override location
            purpose: Override purpose
            start_time: Test start time (default: now)

        Returns:
            UUTReport ready to populate with test steps

        Example:
            >>> report = service.create_uut_report(
            ...     operator="John",
            ...     part_number="PCBA-001",
            ...     revision="A",
            ...     serial_number="SN-12345",
            ...     operation_type=100
            ... )
            >>> root = report.get_root_sequence_call()
            >>> root.add_numeric_test("Voltage", 5.0, 4.5, 5.5)
        """
        # Resolve station info
        effective_station_name = station_name
        effective_location = location
        effective_purpose = purpose

        if self._station_provider:
            station = self._station_provider()
            effective_station_name = station_name or station.name
            effective_location = location or station.location
            effective_purpose = purpose or station.purpose

        report = UUTReport(
            pn=part_number,
            sn=serial_number,
            rev=revision,
            process_code=operation_type,
            station_name=effective_station_name or "Unknown",
            location=effective_location or "Unknown",
            purpose=effective_purpose or "Unknown",
            result="P",  # Default to pass, will be updated
            start=start_time or datetime.now().astimezone(),
        )

        report.info = UUTInfo(operator=operator)

        return report

    def _resolve_station(
        self,
        station: Optional[StationInfo] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> tuple:
        """Resolve station information from various sources."""
        resolved_name = station_name
        resolved_location = location
        resolved_purpose = purpose

        # Try station object if provided
        if station:
            resolved_name = resolved_name or station.name
            resolved_location = resolved_location or station.location
            resolved_purpose = resolved_purpose or station.purpose

        # Try station provider
        if self._station_provider:
            provider_station = self._station_provider()
            resolved_name = resolved_name or provider_station.name
            resolved_location = resolved_location or provider_station.location
            resolved_purpose = resolved_purpose or provider_station.purpose

        # Defaults
        resolved_name = resolved_name or "Unknown"
        resolved_location = resolved_location or "Unknown"
        resolved_purpose = resolved_purpose or "Development"

        return resolved_name, resolved_location, resolved_purpose

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: UUTReport,
        test_operation_code_pos: None = None,
        *,
        repair_process_code: int = 500,
        operator: Optional[str] = None,
        station: Optional[StationInfo] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: UUID,
        test_operation_code_pos: None = None,
        *,
        part_number: str,
        serial_number: str,
        test_operation_code: int,
        repair_process_code: int = 500,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional[StationInfo] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: str,
        test_operation_code_pos: int,
        *,
        serial_number: str,
        repair_process_code: int = 500,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional[StationInfo] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    def create_uur_report(
        self,
        uut_or_guid_or_pn: Union[UUTReport, UUID, str, None] = None,
        test_operation_code_pos: Optional[int] = None,
        *,
        # Common optional parameters
        operator: Optional[str] = None,
        part_number: Optional[str] = None,
        serial_number: Optional[str] = None,
        revision: str = "A",
        # Dual process codes (key UUR architectural feature)
        repair_process_code: int = 500,
        test_operation_code: Optional[int] = None,
        station: Optional[StationInfo] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None,
        comment: Optional[str] = None,
        # Alternative parameter names
        process_code: Optional[int] = None,
        operation_type: Optional[int] = None,
    ) -> UURReport:
        """
        Create a new UUR (Unit Under Repair) report.

        UUR reports require TWO process codes:

        1. **repair_process_code**: The type of repair operation (default: 500)
           - Must be a valid repair operation (isRepairOperation=true)
           - Common values: 500 (Repair), 510 (RMA Repair)
           - This becomes the top-level report process_code

        2. **test_operation_code**: The original test operation that failed
           - Must be a valid test operation (isTestOperation=true)
           - Common values: 100 (End of line test), 50 (PCBA test), etc.
           - Automatically extracted from UUTReport if provided
           - Stored in uur_info.test_operation_code

        Supports multiple calling patterns:

        1. From UUTReport object (recommended):
           ```python
           uur = api.report.create_uur_report(
               failed_uut,
               repair_process_code=500,
               operator="RepairTech"
           )
           ```

        2. From UUT GUID (when you have the ID but not the full report):
           ```python
           uur = api.report.create_uur_report(
               uut_guid,
               part_number="PN-123",
               serial_number="SN-001",
               test_operation_code=100,
               repair_process_code=500
           )
           ```

        3. From part number and test operation code:
           ```python
           uur = api.report.create_uur_report(
               "PN-123", 100,  # part_number, test_operation_code
               serial_number="SN-001",
               repair_process_code=500
           )
           ```

        Args:
            uut_or_guid_or_pn: UUTReport object, UUID of referenced UUT, or part number
            test_operation_code_pos: Test operation code (positional, for pattern 3)
            operator: Name of the repair operator
            part_number: Part number (when not using UUTReport)
            serial_number: Serial number (when not using UUTReport)
            revision: Revision of the unit (default "A")
            repair_process_code: Repair operation type (default 500=Repair)
            test_operation_code: Original test operation that failed
            station_name: Optional station name
            location: Optional location
            purpose: Optional purpose (default "Repair")
            comment: Optional comment for the repair
            process_code: Alias for test_operation_code
            operation_type: Alias for test_operation_code

        Returns:
            A new UURReport object ready for adding repair info and submission
        """
        # Resolve parameters based on calling pattern
        ref_uut_guid: Optional[UUID] = None
        pn: str = ""
        sn: str = ""
        rev: str = revision
        test_op_code: Optional[int] = None

        # Pattern 1: UUTReport object
        if isinstance(uut_or_guid_or_pn, UUTReport):
            uut = uut_or_guid_or_pn
            ref_uut_guid = uut.id
            pn = uut.pn
            sn = uut.sn
            rev = uut.rev or revision
            # Extract test operation code from the UUT
            test_op_code = test_operation_code or uut.process_code
            # Use UUT's station/location as defaults if not specified
            station_name = station_name or uut.station_name
            location = location or uut.location

        # Pattern 2: UUID
        elif isinstance(uut_or_guid_or_pn, UUID):
            ref_uut_guid = uut_or_guid_or_pn
            if not part_number:
                raise ValueError("part_number is required when creating UUR from UUID")
            if not serial_number:
                raise ValueError("serial_number is required when creating UUR from UUID")
            pn = part_number
            sn = serial_number
            rev = revision
            # Resolve test operation code from various sources (use 'is not None' to allow 0)
            test_op_code = (
                test_operation_code if test_operation_code is not None else
                test_operation_code_pos if test_operation_code_pos is not None else
                process_code if process_code is not None else
                operation_type
            )
            if test_op_code is None:
                raise ValueError("test_operation_code is required when creating UUR from UUID")

        # Pattern 3: part_number string with test_operation_code
        elif isinstance(uut_or_guid_or_pn, str):
            pn = uut_or_guid_or_pn
            # Resolve test operation code (use 'is not None' to allow 0)
            test_op_code = (
                test_operation_code_pos if test_operation_code_pos is not None else
                test_operation_code if test_operation_code is not None else
                process_code if process_code is not None else
                operation_type
            )
            if test_op_code is None:
                raise ValueError("test_operation_code is required when creating UUR from part_number")
            if not serial_number:
                raise ValueError("serial_number is required when creating UUR from part_number")
            sn = serial_number
            rev = revision

        # Fallback: use keyword arguments
        else:
            if part_number:
                pn = part_number
            if serial_number:
                sn = serial_number
            test_op_code = test_operation_code or process_code or operation_type

        if not pn:
            raise ValueError("part_number is required")
        if not sn:
            raise ValueError("serial_number is required")

        # Resolve station information
        resolved_station_name, resolved_location, resolved_purpose = self._resolve_station(
            station, station_name, location, purpose
        )
        # Default purpose for UUR is "Repair"
        if resolved_purpose == "Development":
            resolved_purpose = "Repair"

        # Get current timestamp for timing fields
        now = datetime.now().astimezone()

        # Create UURInfo with dual process code architecture
        # Note: API requires processCode, confirmDate, finalizeDate, execTime in uur object
        # refUUT can be null (for standalone repairs without a failed UUT reference)
        uur_info = UURInfo(
            operator=operator or "Unknown",  # Required field from ReportInfo
            ref_uut=ref_uut_guid,  # Can be None for standalone repairs
            comment=comment,
            # Set the test operation code (what failed)
            test_operation_code=test_op_code,
            process_code=test_op_code,  # API requires this in uur object
            # Required timing fields
            confirm_date=now,
            finalize_date=now,
            exec_time=0.0,  # Time spent on repair (seconds)
        )

        # Create report with repair process code at top level
        report = UURReport(
            id=uuid4(),
            type="R",
            pn=pn,
            sn=sn,
            rev=rev,
            process_code=repair_process_code,  # Repair operation (500, 510, etc.)
            station_name=resolved_station_name,
            location=resolved_location,
            purpose=resolved_purpose,
            start=datetime.now().astimezone(),
            uur_info=uur_info
        )

        # Copy sub_units from UUT if creating from UUTReport
        if isinstance(uut_or_guid_or_pn, UUTReport):
            uut = uut_or_guid_or_pn
            self._copy_sub_units_to_uur(uut, report)

        return report

    def _copy_sub_units_to_uur(self, uut: UUTReport, uur: UURReport) -> None:
        """Copy sub-units from UUT to UUR report."""
        if not uut.sub_units:
            return

        uur.sub_units = []
        for sub in uut.sub_units:
            uur_sub = UURSubUnit(
                pn=sub.pn,
                rev=sub.rev,
                sn=sub.sn,
                part_type=getattr(sub, 'part_type', None),
                idx=getattr(sub, 'idx', 0),
                parent_idx=getattr(sub, 'parent_idx', None),
                position=getattr(sub, 'position', None),
            )
            uur.sub_units.append(uur_sub)

    def create_uur_from_uut(
        self,
        uut_report: UUTReport,
        operator: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport:
        """
        Create a UUR report linked to a UUT report.

        This is a convenience method that creates a repair report referencing
        the given UUT report, copying relevant metadata.

        Args:
            uut_report: The UUT report to create repair for
            operator: Operator performing the repair
            comment: Initial comment for the repair

        Returns:
            UURReport linked to the UUT
        """
        return self.create_uur_report(
            uut_report,
            operator=operator,
            comment=comment
        )

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def query_headers(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
        skip: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Query report headers (unified endpoint for UUT and UUR).

        Args:
            report_type: ReportType.UUT or ReportType.UUR (or "uut"/"uur" strings)
            expand: Fields to expand (subUnits, miscInfo, assets, attachments)
            odata_filter: OData filter string (e.g., "serialNumber eq '12345'")
            top: Maximum results ($top)
            orderby: Sort order ($orderby, e.g., "start desc")
            skip: Number to skip ($skip)

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> # Query UUT headers for a serial number
            >>> headers = await service.query_headers(
            ...     report_type=ReportType.UUT,
            ...     odata_filter="serialNumber eq '12345'"
            ... )
            >>> 
            >>> # Query UUR (repair) headers
            >>> repairs = await service.query_headers(
            ...     report_type=ReportType.UUR,
            ...     top=10
            ... )
        """
        return await self._repository.query_headers(
            report_type=report_type,
            expand=expand,
            odata_filter=odata_filter,
            top=top,
            orderby=orderby,
            skip=skip
        )

    async def query_uut_headers(
        self,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """
        Query UUT report headers.

        Args:
            expand: Fields to expand (subUnits, miscInfo, assets, attachments)
            odata_filter: OData filter string (e.g., "serialNumber eq '12345'")
            top: Maximum results ($top)
            orderby: Sort order ($orderby, e.g., "start desc")

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> headers = await service.query_uut_headers(
            ...     odata_filter="serialNumber eq '12345'",
            ...     top=10
            ... )
        """
        return await self._repository.query_headers(
            ReportType.UUT, expand=expand,
            odata_filter=odata_filter, top=top, orderby=orderby
        )

    async def query_uur_headers(
        self,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """
        Query UUR (repair) report headers.

        Args:
            expand: Fields to expand (uurSubUnits, uurMiscInfo, uurAttachments)
            odata_filter: OData filter string (e.g., "serialNumber eq '12345'")
            top: Maximum results ($top)
            orderby: Sort order ($orderby, e.g., "start desc")

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> repairs = await service.query_uur_headers(
            ...     odata_filter="serialNumber eq '12345'",
            ...     top=10
            ... )
        """
        return await self._repository.query_headers(
            ReportType.UUR, expand=expand,
            odata_filter=odata_filter, top=top, orderby=orderby
        )

    async def get_report(
        self,
        report_id: str,
        detail_level: Optional[int] = None
    ) -> Optional[Union[UUTReport, UURReport]]:
        """
        Get a report by ID.

        Args:
            report_id: Report ID (GUID)
            detail_level: Level of detail (0-7)

        Returns:
            UUTReport or UURReport, or None
        """
        if not report_id or not report_id.strip():
            raise ValueError("report_id is required")
        return await self._repository.get_wsjf(report_id, detail_level=detail_level)

    async def submit_report(
        self,
        report: Union[UUTReport, UURReport, Dict[str, Any]],
    ) -> Optional[str]:
        """
        Submit a test report.

        Args:
            report: UUTReport, UURReport, or dict

        Returns:
            Report ID if successful

        Note:
            For offline/queue functionality, use pywats_client.ClientService
            which provides file-based queuing with retry logic.

        Example:
            >>> report_id = await service.submit_report(report)
            >>> print(f"Submitted: {report_id}")
        """
        result = await self._repository.post_wsjf(report)
        if result:
            # Extract identifying info for logging
            if isinstance(report, dict):
                pn = report.get('part_number') or report.get('pn') or report.get('partNumber', 'unknown')
                sn = report.get('serial_number') or report.get('sn') or report.get('serialNumber', 'unknown')
            else:
                pn = getattr(report, 'part_number', None) or getattr(report, 'pn', None) or 'unknown'
                sn = getattr(report, 'serial_number', None) or getattr(report, 'sn', None) or 'unknown'
            logger.info(f"REPORT_SUBMITTED: id={result} (pn={pn}, sn={sn})")
        return result

    # =========================================================================
    # Attachments
    # =========================================================================

    async def get_attachment(
        self,
        attachment_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get attachment content.

        Args:
            attachment_id: Attachment ID
            step_id: Step ID

        Returns:
            Attachment content as bytes
        """
        return await self._repository.get_attachment(attachment_id, step_id)

    async def get_all_attachments(self, report_id: str) -> Optional[bytes]:
        """
        Get all attachments for a report as zip.

        Args:
            report_id: Report ID

        Returns:
            Zip file content as bytes
        """
        return await self._repository.get_attachments_as_zip(report_id)

    # =========================================================================
    # Certificate
    # =========================================================================

    async def get_certificate(self, report_id: str) -> Optional[bytes]:
        """
        Get certificate for a report.

        Args:
            report_id: Report ID

        Returns:
            Certificate content as bytes
        """
        return await self._repository.get_certificate(report_id)

    # =========================================================================
    # Additional Query Methods
    # =========================================================================

    async def query_headers_with_subunits(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers with sub-units expanded.

        Args:
            report_type: ReportType.UUT or ReportType.UUR
            odata_filter: OData filter string
            top: Maximum results
            orderby: Sort order

        Returns:
            List of ReportHeader objects with sub-units
        """
        is_uut = is_uut_report_type(report_type)
        expand_fields = get_expand_fields(is_uut, include_subunits=True)

        return await self._repository.query_headers(
            report_type, expand=expand_fields,
            odata_filter=odata_filter, top=top, orderby=orderby
        )

    async def query_headers_by_subunit_part_number(
        self,
        subunit_part_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers filtering by sub-unit part number.

        Uses OData filter to find parent units containing specific sub-units.

        Args:
            subunit_part_number: Part number of sub-unit to filter by
            report_type: ReportType.UUT or ReportType.UUR
            top: Maximum results

        Returns:
            List of ReportHeader objects with sub-units expanded
        """
        is_uut = is_uut_report_type(report_type)
        odata_filter = build_subunit_part_filter(subunit_part_number, is_uut)
        expand_fields = get_expand_fields(is_uut, include_subunits=True)

        return await self._repository.query_headers(
            report_type, expand=expand_fields,
            odata_filter=odata_filter, top=top
        )

    async def query_headers_by_subunit_serial(
        self,
        subunit_serial_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers filtering by sub-unit serial number.

        Args:
            subunit_serial_number: Serial number of sub-unit to filter by
            report_type: ReportType.UUT or ReportType.UUR
            top: Maximum results

        Returns:
            List of ReportHeader objects with sub-units expanded
        """
        is_uut = is_uut_report_type(report_type)
        odata_filter = build_subunit_serial_filter(subunit_serial_number, is_uut)
        expand_fields = get_expand_fields(is_uut, include_subunits=True)

        return await self._repository.query_headers(
            report_type, expand=expand_fields,
            odata_filter=odata_filter, top=top
        )

    async def query_headers_by_misc_info(
        self,
        description: str,
        string_value: str,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Query report headers by misc info.

        Args:
            description: Misc info description
            string_value: Misc info string value
            top: Number of records to return

        Returns:
            List of ReportHeader objects
        """
        return await self._repository.query_headers_by_misc_info(
            description, string_value, top
        )

    # =========================================================================
    # Query Helpers
    # =========================================================================

    async def get_headers_by_serial(
        self,
        serial_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by serial number.

        Args:
            serial_number: Serial number to search
            report_type: ReportType.UUT or ReportType.UUR
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        odata_filter = build_serial_filter(serial_number)
        return await self._repository.query_headers(
            report_type, odata_filter=odata_filter, top=top
        )

    async def get_headers_by_part_number(
        self,
        part_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by part number.

        Args:
            part_number: Part number to search
            report_type: ReportType.UUT or ReportType.UUR
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        odata_filter = build_part_number_filter(part_number)
        return await self._repository.query_headers(
            report_type, odata_filter=odata_filter, top=top
        )

    async def get_headers_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: Union[ReportType, str] = ReportType.UUT
    ) -> List[ReportHeader]:
        """
        Get report headers by date range.

        Args:
            start_date: Start date
            end_date: End date
            report_type: ReportType.UUT or ReportType.UUR

        Returns:
            List of ReportHeader
        """
        odata_filter = build_date_range_filter(start_date, end_date)
        return await self._repository.query_headers(
            report_type, odata_filter=odata_filter
        )

    async def get_recent_headers(
        self,
        days: int = DEFAULT_RECENT_DAYS,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get headers from the last N days.

        Args:
            days: Number of days back (default: DEFAULT_RECENT_DAYS = 7)
            report_type: ReportType.UUT or ReportType.UUR
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        odata_filter = build_date_range_filter(start_date, end_date)
        return await self._repository.query_headers(
            report_type, odata_filter=odata_filter, top=top
        )

    async def get_todays_headers(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get today's report headers.

        Args:
            report_type: ReportType.UUT or ReportType.UUR
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        odata_filter = build_date_range_filter(today, tomorrow)
        return await self._repository.query_headers(
            report_type, odata_filter=odata_filter, top=top
        )

    # =========================================================================
    # Submit Alias
    # =========================================================================

    async def submit(
        self,
        report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Submit a new report (alias for submit_report).

        Args:
            report: Report to submit (UUTReport, UURReport or dict)

        Returns:
            Report ID if successful, None otherwise
        """
        return await self.submit_report(report)

    # =========================================================================
    # WSXF (XML Format) Operations
    # =========================================================================

    async def get_report_xml(
        self,
        report_id: str,
        include_attachments: Optional[bool] = None,
        include_chartdata: Optional[bool] = None,
        include_indexes: Optional[bool] = None,
    ) -> Optional[bytes]:
        """
        Get a report as XML (WSXF format).

        Args:
            report_id: Report ID (GUID)
            include_attachments: Include attachment data. Default True.
                                Set False to reduce payload.
            include_chartdata: Include chart/plot data. Default True.
                              Set False to reduce payload.
            include_indexes: Include index information. Default False.

        Returns:
            XML content as bytes or None
        """
        return await self._repository.get_wsxf(
            report_id,
            include_attachments=include_attachments,
            include_chartdata=include_chartdata,
            include_indexes=include_indexes,
        )

    async def submit_report_xml(self, xml_content: str) -> Optional[str]:
        """
        Submit a report in XML format.

        Args:
            xml_content: Report as XML string

        Returns:
            Report ID if successful, None otherwise
        """
        result = await self._repository.post_wsxf(xml_content)
        if result:
            logger.info(f"REPORT_SUBMITTED_XML: id={result}")
        return result
