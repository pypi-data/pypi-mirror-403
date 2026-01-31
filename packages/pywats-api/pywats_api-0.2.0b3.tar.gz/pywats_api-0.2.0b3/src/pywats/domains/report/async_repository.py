"""Async Report repository - data access layer.

Async version of the report repository for non-blocking API calls.
Uses Routes for centralized endpoint management.
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
import logging

from ...core.routes import Routes

if TYPE_CHECKING:
    from ...core.async_client import AsyncHttpClient
    from ...core.exceptions import ErrorHandler

from .models import ReportHeader
from .report_models import UUTReport, UURReport
from .enums import ImportMode, ReportType

logger = logging.getLogger(__name__)


class AsyncReportRepository:
    """
    Async Report data access layer.

    Handles all async WATS API interactions for test reports.
    """

    def __init__(
        self, 
        http_client: "AsyncHttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ) -> None:
        """
        Initialize with async HTTP client.

        Args:
            http_client: AsyncHttpClient for making async HTTP requests
            error_handler: Optional ErrorHandler for error handling
        """
        self._http_client = http_client
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)
        self._import_mode: ImportMode = ImportMode.Import

    @property
    def import_mode(self) -> ImportMode:
        """Get the current import mode."""
        return self._import_mode
    
    @import_mode.setter
    def import_mode(self, value: ImportMode) -> None:
        """Set the import mode."""
        if not isinstance(value, ImportMode):
            raise TypeError(f"import_mode must be ImportMode, not {type(value).__name__}")
        self._import_mode = value
        from .import_mode import set_import_mode
        set_import_mode(value)

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
        skip: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers.

        GET /api/Report/Query/Header

        Args:
            report_type: ReportType.UUT ("U") or ReportType.UUR ("R")
            expand: Fields to expand (subUnits, miscInfo, assets, attachments)
            odata_filter: OData filter string (e.g., "serialNumber eq '12345'")
            top: Maximum number of results ($top)
            orderby: Sort order ($orderby, e.g., "start desc")
            skip: Number of results to skip ($skip)

        Returns:
            List of ReportHeader objects
        """
        # Convert ReportType enum to string value
        if isinstance(report_type, ReportType):
            rt_value = report_type.value
        else:
            # Accept string values ("uut"/"uur")
            rt_value = "U" if report_type.lower() == "uut" else "R"
        
        params: Dict[str, Any] = {"reportType": rt_value}
        
        if expand:
            params["$expand"] = ",".join(expand)
        if odata_filter:
            params["$filter"] = odata_filter
        if top is not None:
            params["$top"] = top
        if orderby:
            params["$orderby"] = orderby
        if skip is not None:
            params["$skip"] = skip
            
        response = await self._http_client.get(Routes.Report.QUERY_HEADER, params=params)
        data = self._error_handler.handle_response(
            response, operation="query_headers", allow_empty=True
        )
        if data:
            return [ReportHeader.model_validate(item) for item in data]
        return []

    async def query_headers_by_misc_info(
        self,
        description: str,
        string_value: str,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by misc info search.

        GET /api/Report/Query/HeaderByMiscInfo
        """
        params: Dict[str, Any] = {
            "description": description,
            "stringValue": string_value
        }
        if top:
            params["$top"] = top
        response = await self._http_client.get(
            Routes.Report.QUERY_HEADER_BY_MISC, params=params
        )
        data = self._error_handler.handle_response(
            response, operation="query_headers_by_misc_info", allow_empty=True
        )
        if data:
            return [ReportHeader.model_validate(item) for item in data]
        return []

    # =========================================================================
    # Report WSJF (JSON Format)
    # =========================================================================

    async def post_wsjf(
        self, report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Post a new WSJF report.

        POST /api/Report/WSJF
        """
        if isinstance(report, (UUTReport, UURReport)):
            data = report.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
            
            if isinstance(report, UURReport) and 'uurInfo' in data:
                uur_info = data['uurInfo']
                if 'processCode' not in uur_info:
                    uur_info['processCode'] = report.uur_info.process_code
                if 'refUUT' not in uur_info:
                    uur_info['refUUT'] = report.uur_info.ref_uut
                if 'confirmDate' not in uur_info:
                    uur_info['confirmDate'] = report.uur_info.confirm_date
                if 'finalizeDate' not in uur_info:
                    uur_info['finalizeDate'] = report.uur_info.finalize_date
                if 'execTime' not in uur_info:
                    uur_info['execTime'] = report.uur_info.exec_time
        else:
            data = report
            
        response = await self._http_client.post(Routes.Report.WSJF, data=data)
        
        if not response.is_success:
            error_msg = "Report submission failed"
            if response.data:
                if isinstance(response.data, dict):
                    error_msg = (
                        response.data.get("message") or
                        response.data.get("Message") or
                        response.data.get("error") or
                        str(response.data)
                    )
                elif isinstance(response.data, str):
                    error_msg = response.data
            raise ValueError(f"Report submission failed ({response.status_code}): {error_msg}")
        
        if response.data:
            result_data = response.data
            if isinstance(result_data, list) and len(result_data) > 0:
                result_data = result_data[0]
            if isinstance(result_data, dict):
                return (
                    result_data.get("ID") or
                    result_data.get("id") or
                    result_data.get("uuid")
                )
            return str(result_data)
        return None

    async def get_wsjf(
        self, 
        report_id: str,
        detail_level: Optional[int] = None,
        include_chartdata: Optional[bool] = None,
        include_attachments: Optional[bool] = None,
    ) -> Optional[Union[UUTReport, UURReport]]:
        """
        Get a report in WSJF format.

        GET /api/Report/Wsjf/{id}
        """
        params: Dict[str, Any] = {}
        if detail_level is not None:
            params["detailLevel"] = detail_level
        if include_chartdata is not None:
            params["includeChartdata"] = include_chartdata
        if include_attachments is not None:
            params["includeAttachments"] = include_attachments

        response = await self._http_client.get(
            Routes.Report.wsjf(str(report_id)),
            params=params if params else None
        )
        data = self._error_handler.handle_response(
            response, operation="get_wsjf"
        )
        if data:
            if data.get("uur"):
                return UURReport.model_validate(data)
            return UUTReport.model_validate(data)
        return None

    # =========================================================================
    # Report WSXF (XML Format)
    # =========================================================================

    async def post_wsxf(self, xml_content: str) -> Optional[str]:
        """
        Post a new WSXF (XML) report.

        POST /api/Report/WSXF
        """
        headers = {"Content-Type": "application/xml"}
        response = await self._http_client.post(
            Routes.Report.WSXF,
            data=xml_content,
            headers=headers
        )
        data = self._error_handler.handle_response(
            response, operation="post_wsxf", allow_empty=True
        )
        if data:
            if isinstance(data, dict):
                return data.get("id")
            return str(data)
        return None

    async def get_wsxf(
        self, 
        report_id: str,
        include_attachments: Optional[bool] = None,
        include_chartdata: Optional[bool] = None,
        include_indexes: Optional[bool] = None,
    ) -> Optional[bytes]:
        """
        Get a report in WSXF (XML) format.

        GET /api/Report/Wsxf/{id}
        
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
        params: Dict[str, Any] = {}
        if include_attachments is not None:
            params["includeAttachments"] = include_attachments
        if include_chartdata is not None:
            params["includeChartdata"] = include_chartdata
        if include_indexes is not None:
            params["includeIndexes"] = include_indexes

        response = await self._http_client.get(
            Routes.Report.wsxf(str(report_id)),
            params=params if params else None
        )
        if not response.is_success:
            self._error_handler.handle_response(response, operation="get_wsxf")
            return None
        return response.raw

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

        GET /api/Report/Attachment
        """
        params: Dict[str, Any] = {}
        if attachment_id:
            params["attachmentId"] = attachment_id
        if step_id:
            params["stepId"] = step_id
        response = await self._http_client.get(Routes.Report.ATTACHMENT, params=params)
        if not response.is_success:
            self._error_handler.handle_response(response, operation="get_attachment")
            return None
        return response.raw

    async def get_attachments_as_zip(self, report_id: str) -> Optional[bytes]:
        """
        Get all attachments for a report as zip.

        GET /api/Report/Attachments/{id}
        """
        response = await self._http_client.get(Routes.Report.attachments(str(report_id)))
        if not response.is_success:
            self._error_handler.handle_response(response, operation="get_attachments_as_zip")
            return None
        return response.raw

    # =========================================================================
    # Certificate
    # =========================================================================

    async def get_certificate(self, report_id: str) -> Optional[bytes]:
        """
        Get certificate for a report.

        GET /api/Report/Certificate/{id}
        """
        response = await self._http_client.get(Routes.Report.certificate(str(report_id)))
        if not response.is_success:
            self._error_handler.handle_response(response, operation="get_certificate")
            return None
        return response.raw
