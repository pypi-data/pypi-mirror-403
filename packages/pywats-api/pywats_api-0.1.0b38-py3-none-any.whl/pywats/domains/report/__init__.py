"""Report domain.

Provides services and repository for test reports (UUT/UUR).

For creating test reports, see the TestUUT factory class:
    from pywats.tools.test_uut import TestUUT
"""
# Report models (UUT/UUR report structure)
from .report_models import (
    UUTReport,
    UURReport,
    Report,
    MiscInfo,
    Step,
    StepStatus,
    WATSBase,
    ReportInfo,
    AdditionalData,
    BinaryData,
    Asset as ReportAsset,
    AssetStats,
    Chart,
    ChartSeries,
    ChartType,
    SubUnit,
    Attachment as ReportAttachment,
    DeserializationContext,
)
from .report_models.uut.steps.sequence_call import SequenceCall, StepList

# Import query-related models
from .enums import DateGrouping, ImportMode, ReportType
from .models import WATSFilter, ReportHeader, Attachment

# Filter and query helpers (Phase 1 & 2 refactoring)
from .filter_builders import (
    build_serial_filter,
    build_part_number_filter,
    build_date_range_filter,
    build_recent_filter,
    build_today_filter,
    build_subunit_part_filter,
    build_subunit_serial_filter,
    build_header_filter,
    combine_filters,
)
from .query_helpers import (
    is_uut_report_type,
    get_expand_fields,
    build_expand_clause,
    build_orderby_clause,
    build_query_params,
    get_default_query_params,
)

# Async implementations (primary API)
from .async_repository import AsyncReportRepository
from .async_service import AsyncReportService

# Backward-compatible aliases
ReportRepository = AsyncReportRepository
ReportService = AsyncReportService

__all__ = [
    # Report Models (UUT/UUR)
    "UUTReport",
    "UURReport",
    "Report",
    "SequenceCall",
    "StepList",
    "Step",
    "StepStatus",
    "MiscInfo",
    "WATSBase",
    "ReportInfo",
    "AdditionalData",
    "BinaryData",
    "ReportAsset",
    "AssetStats",
    "Chart",
    "ChartSeries",
    "ChartType",
    "SubUnit",
    "ReportAttachment",
    "DeserializationContext",
    # Enums
    "DateGrouping",
    "ImportMode",
    "ReportType",
    # Query models
    "WATSFilter",
    "ReportHeader",
    "Attachment",
    # Filter builders (Phase 1)
    "build_serial_filter",
    "build_part_number_filter",
    "build_date_range_filter",
    "build_recent_filter",
    "build_today_filter",
    "build_subunit_part_filter",
    "build_subunit_serial_filter",
    "build_header_filter",
    "combine_filters",
    # Query helpers (Phase 2)
    "is_uut_report_type",
    "get_expand_fields",
    "build_expand_clause",
    "build_orderby_clause",
    "build_query_params",
    "get_default_query_params",
    # Async implementations (primary API)
    "AsyncReportRepository",
    "AsyncReportService",
    # Backward-compatible aliases
    "ReportRepository",
    "ReportService",
]
