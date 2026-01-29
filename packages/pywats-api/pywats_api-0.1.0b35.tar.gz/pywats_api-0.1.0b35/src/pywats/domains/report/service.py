"""Report service - thin sync wrapper around AsyncReportService.

This module provides synchronous access to AsyncReportService methods.
All business logic is maintained in async_service.py (source of truth).
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Callable
from uuid import UUID

from .async_service import AsyncReportService, StationInfo
from .async_repository import AsyncReportRepository
from .models import WATSFilter, ReportHeader
from .report_models import UUTReport, UURReport
from .enums import ReportType
from ...core.sync_runner import run_sync


class ReportService:
    """
    Synchronous wrapper for AsyncReportService.

    Provides sync access to all async report service operations.
    All business logic is in AsyncReportService.
    """

    def __init__(
        self,
        async_service: AsyncReportService = None,
        *,
        repository: AsyncReportRepository = None,
        station_provider: Optional[Callable[[], StationInfo]] = None
    ):
        """
        Initialize with AsyncReportService or repository.

        Args:
            async_service: AsyncReportService instance to wrap
            repository: (Deprecated) Repository instance for backward compatibility
            station_provider: Optional callable that returns station info
        """
        if repository is not None:
            # Backward compatibility: create async service from repository
            self._async_service = AsyncReportService(repository, station_provider)
            self._repository = repository  # Keep reference for tests
        elif async_service is not None:
            self._async_service = async_service
            self._repository = async_service._repository  # Expose underlying repo
        else:
            raise ValueError("Either async_service or repository must be provided")

    @classmethod
    def from_repository(
        cls,
        repository: AsyncReportRepository,
        station_provider: Optional[Callable[[], StationInfo]] = None
    ) -> "ReportService":
        """
        Create ReportService from an AsyncReportRepository.

        Args:
            repository: AsyncReportRepository instance
            station_provider: Optional callable that returns station info

        Returns:
            ReportService wrapping an AsyncReportService
        """
        async_service = AsyncReportService(repository, station_provider)
        return cls(async_service)

    # =========================================================================
    # Factory Methods (Sync - no repository calls, call directly)
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
        """Create a new UUT (Unit Under Test) report."""
        return self._async_service.create_uut_report(
            operator=operator,
            part_number=part_number,
            revision=revision,
            serial_number=serial_number,
            operation_type=operation_type,
            station_name=station_name,
            location=location,
            purpose=purpose,
            start_time=start_time,
        )

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
        # Legacy parameters (for backward compatibility)
        process_code: Optional[int] = None,
        operation_type: Optional[int] = None,
    ) -> UURReport:
        """Create a new UUR (Unit Under Repair) report."""
        return self._async_service.create_uur_report(
            uut_or_guid_or_pn=uut_or_guid_or_pn,
            test_operation_code_pos=test_operation_code_pos,
            operator=operator,
            part_number=part_number,
            serial_number=serial_number,
            revision=revision,
            repair_process_code=repair_process_code,
            test_operation_code=test_operation_code,
            station=station,
            station_name=station_name,
            location=location,
            purpose=purpose,
            comment=comment,
            process_code=process_code,
            operation_type=operation_type,
        )

    def create_uur_from_uut(
        self,
        uut_report: UUTReport,
        operator: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport:
        """Create a UUR report linked to a UUT report."""
        return self._async_service.create_uur_from_uut(
            uut_report=uut_report,
            operator=operator,
            comment=comment,
        )

    # =========================================================================
    # Query Operations
    # =========================================================================

    def query_headers(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
        skip: Optional[int] = None
    ) -> List[ReportHeader]:
        """Query report headers (unified endpoint for UUT and UUR)."""
        return run_sync(self._async_service.query_headers(
            report_type=report_type,
            expand=expand,
            odata_filter=odata_filter,
            top=top,
            orderby=orderby,
            skip=skip,
        ))

    def query_uut_headers(
        self,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """Query UUT report headers."""
        return run_sync(self._async_service.query_uut_headers(
            expand=expand,
            odata_filter=odata_filter,
            top=top,
            orderby=orderby,
        ))

    def query_uur_headers(
        self,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """Query UUR (repair) report headers."""
        return run_sync(self._async_service.query_uur_headers(
            expand=expand,
            odata_filter=odata_filter,
            top=top,
            orderby=orderby,
        ))

    def get_report(
        self,
        report_id: str,
        detail_level: Optional[int] = None
    ) -> Optional[Union[UUTReport, UURReport]]:
        """Get a report by ID."""
        return run_sync(self._async_service.get_report(
            report_id=report_id,
            detail_level=detail_level,
        ))

    def submit_report(
        self,
        report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """Submit a test report."""
        return run_sync(self._async_service.submit_report(report))

    # =========================================================================
    # Attachments
    # =========================================================================

    def get_attachment(
        self,
        attachment_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Get attachment content."""
        return run_sync(self._async_service.get_attachment(
            attachment_id=attachment_id,
            step_id=step_id,
        ))

    def get_all_attachments(self, report_id: str) -> Optional[bytes]:
        """Get all attachments for a report as zip."""
        return run_sync(self._async_service.get_all_attachments(report_id))

    # =========================================================================
    # Certificate
    # =========================================================================

    def get_certificate(self, report_id: str) -> Optional[bytes]:
        """Get certificate for a report."""
        return run_sync(self._async_service.get_certificate(report_id))

    # =========================================================================
    # Additional Query Methods
    # =========================================================================

    def query_headers_with_subunits(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """Query report headers with sub-units expanded."""
        return run_sync(self._async_service.query_headers_with_subunits(
            report_type=report_type,
            odata_filter=odata_filter,
            top=top,
            orderby=orderby,
        ))

    def query_headers_by_subunit_part_number(
        self,
        subunit_part_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """Query report headers filtering by sub-unit part number."""
        return run_sync(self._async_service.query_headers_by_subunit_part_number(
            subunit_part_number=subunit_part_number,
            report_type=report_type,
            top=top,
        ))

    def query_headers_by_subunit_serial(
        self,
        subunit_serial_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """Query report headers filtering by sub-unit serial number."""
        return run_sync(self._async_service.query_headers_by_subunit_serial(
            subunit_serial_number=subunit_serial_number,
            report_type=report_type,
            top=top,
        ))

    def query_headers_by_misc_info(
        self,
        description: str,
        string_value: str,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """Query report headers by misc info."""
        return run_sync(self._async_service.query_headers_by_misc_info(
            description=description,
            string_value=string_value,
            top=top,
        ))

    # =========================================================================
    # Query Helpers
    # =========================================================================

    def get_headers_by_serial(
        self,
        serial_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """Get report headers by serial number."""
        return run_sync(self._async_service.get_headers_by_serial(
            serial_number=serial_number,
            report_type=report_type,
            top=top,
        ))

    def get_headers_by_part_number(
        self,
        part_number: str,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """Get report headers by part number."""
        return run_sync(self._async_service.get_headers_by_part_number(
            part_number=part_number,
            report_type=report_type,
            top=top,
        ))

    def get_headers_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: Union[ReportType, str] = ReportType.UUT
    ) -> List[ReportHeader]:
        """Get report headers by date range."""
        return run_sync(self._async_service.get_headers_by_date_range(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
        ))

    def get_recent_headers(
        self,
        days: int = 7,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """Get headers from the last N days."""
        return run_sync(self._async_service.get_recent_headers(
            days=days,
            report_type=report_type,
            top=top,
        ))

    def get_todays_headers(
        self,
        report_type: Union[ReportType, str] = ReportType.UUT,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """Get today's report headers."""
        return run_sync(self._async_service.get_todays_headers(
            report_type=report_type,
            top=top,
        ))

    # =========================================================================
    # Submit Alias
    # =========================================================================

    def submit(
        self,
        report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """Submit a new report (alias for submit_report)."""
        return run_sync(self._async_service.submit(report))

    # =========================================================================
    # WSXF (XML Format) Operations
    # =========================================================================

    def get_report_xml(
        self,
        report_id: str,
        include_attachments: Optional[bool] = None,
        include_chartdata: Optional[bool] = None,
        include_indexes: Optional[bool] = None,
    ) -> Optional[bytes]:
        """Get a report as XML (WSXF format)."""
        return run_sync(self._async_service.get_report_xml(
            report_id=report_id,
            include_attachments=include_attachments,
            include_chartdata=include_chartdata,
            include_indexes=include_indexes,
        ))

    def submit_report_xml(self, xml_content: str) -> Optional[str]:
        """Submit a report in XML format."""
        return run_sync(self._async_service.submit_report_xml(xml_content))
