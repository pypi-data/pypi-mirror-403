"""
pyWATS - Python API for WATS

A clean, object-oriented Python library for interacting with the WATS server.

Usage (Synchronous - for scripts):
    from pywats import pyWATS
    
    api = pyWATS(base_url="https://your-wats-server.com", token="your-token")
    
    # Access modules
    products = api.product.get_products()
    product = api.product.get_product("PART-001")
    
    # Use query models
    from pywats.domains.report import WATSFilter
    filter = WATSFilter(part_number="PART-001")
    headers = api.report.query_uut_headers(filter)
    
    # Use report models (WSJF format)
    from pywats.models import UUTReport, UURReport
    report = UUTReport(pn="PART-001", sn="SN-12345", rev="A", ...)

Usage (Asynchronous - for GUI/async applications):
    import asyncio
    from pywats import AsyncWATS
    
    async def main():
        async with AsyncWATS(base_url="...", token="...") as api:
            products = await api.product.get_products()
            print(products)
    
    asyncio.run(main())
"""

from .pywats import pyWATS
from .async_wats import AsyncWATS
from .sync import SyncWATS
from .exceptions import (
    PyWATSError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConnectionError
)
from .core.logging import enable_debug_logging
from .core.station import Station, StationRegistry, StationConfig, Purpose
from .core.throttle import configure_throttling, RateLimiter
from .core.retry import RetryConfig, RetryExhaustedError
from .core.validation import (
    allow_problematic_characters,
    ReportHeaderValidationError,
    ReportHeaderValidationWarning,
)

# Optional queue module (imported only when needed)
# from .queue import SimpleQueue, convert_to_wsjf, convert_from_wsxf, convert_from_wstf

# Import commonly used models from domains for convenience
from .domains.product import Product, ProductRevision, ProductGroup, ProductView
from .domains.product.enums import ProductState
from .domains.asset import Asset, AssetType, AssetLog
from .domains.asset.enums import AssetState, AssetLogType
from .domains.production import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade
)
from .domains.rootcause import (
    Ticket, TicketStatus, TicketPriority, TicketView,
    TicketUpdate, TicketUpdateType, TicketAttachment
)
from .domains.scim import (
    ScimToken, ScimUser, ScimUserName, ScimUserEmail,
    ScimPatchRequest, ScimPatchOperation, ScimListResponse
)
from .domains.report import WATSFilter, ReportHeader, Attachment
from .domains.analytics import (
    YieldData, ProcessInfo, LevelInfo,
    # New typed models for analytics
    TopFailedStep, RepairStatistics, RepairHistoryRecord,
    MeasurementData, AggregatedMeasurement, OeeAnalysisResult,
    # Unit Flow models (internal API)
    UnitFlowNode, UnitFlowLink, UnitFlowUnit, UnitFlowFilter, UnitFlowResult,
    # Step/Measurement filter models (internal API)
    StepStatusItem, MeasurementListItem,
    # Dimension query enums and builder
    Dimension, RepairDimension, KPI, RepairKPI, DimensionBuilder,
)

# Common models from shared
from .shared import Setting, PyWATSModel

# Result types for structured error handling (LLM/Agent-friendly)
from .shared import Result, Success, Failure, ErrorCode, failure_from_exception

# Type-safe enums and path utilities for query building
from .shared import (
    StatusFilter, RunFilter, StepType, CompOp, CompOperator, SortDirection,
    StepPath, MeasurementPath, normalize_path, display_path, normalize_paths,
)
from .domains.report.enums import DateGrouping

# Discovery helpers for API exploration (LLM/Agent-friendly)
from .shared import discover

__version__ = "0.1.0b38"
__wats_server_version__ = "2025.3.9.824"  # Minimum required WATS server version
__all__ = [
    # Main classes
    "pyWATS",
    "AsyncWATS",
    "SyncWATS",
    # Station concept
    "Station",
    "StationRegistry",
    "StationConfig",
    "Purpose",
    # Rate limiting
    "configure_throttling",
    "RateLimiter",
    # Retry configuration
    "RetryConfig",
    "RetryExhaustedError",
    # Validation (report header fields)
    "allow_problematic_characters",
    "ReportHeaderValidationError",
    "ReportHeaderValidationWarning",
    # Logging utilities
    "enable_debug_logging",
    # Exceptions
    "PyWATSError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ConnectionError",
    # Product models
    "Product",
    "ProductRevision",
    "ProductView",
    "ProductState",
    "ProductGroup",
    # Asset models
    "Asset",
    "AssetType",
    "AssetLog",
    "AssetState",
    "AssetLogType",
    # Production models
    "Unit",
    "UnitChange",
    "ProductionBatch",
    "SerialNumberType",
    "UnitVerification",
    "UnitVerificationGrade",
    # RootCause (Ticketing) models
    "Ticket",
    "TicketStatus",
    "TicketPriority",
    "TicketView",
    "TicketUpdate",
    "TicketUpdateType",
    "TicketAttachment",
    # Query/filter models
    "ReportHeader",
    "WATSFilter",
    "Attachment",
    "YieldData",
    "ProcessInfo",
    "LevelInfo",
    # Analytics typed models
    "TopFailedStep",
    "RepairStatistics",
    "RepairHistoryRecord",
    "MeasurementData",
    "AggregatedMeasurement",
    "OeeAnalysisResult",
    # Unit Flow models (internal API)
    "UnitFlowNode",
    "UnitFlowLink",
    "UnitFlowUnit",
    "UnitFlowFilter",
    "UnitFlowResult",
    # Step/Measurement filter models (internal API)
    "StepStatusItem",
    "MeasurementListItem",
    # Analytics dimension/KPI enums
    "Dimension",
    "RepairDimension",
    "KPI",
    "RepairKPI",
    "DimensionBuilder",
    # SCIM models (user provisioning)
    "ScimToken",
    "ScimUser",
    "ScimUserName",
    "ScimUserEmail",
    "ScimPatchRequest",
    "ScimPatchOperation",
    "ScimListResponse",
    # Common models
    "Setting",
    "PyWATSModel",
    # Result types for structured error handling
    "Result",
    "Success",
    "Failure",
    "ErrorCode",
    "failure_from_exception",
    # Type-safe query enums
    "StatusFilter",
    "RunFilter",
    "StepType",
    "CompOperator",
    "SortDirection",
    "DateGrouping",
    # Path utilities (seamless / <-> ¶ conversion)
    "StepPath",
    "MeasurementPath",
    "normalize_path",
    "display_path",
    "normalize_paths",
    # Discovery helpers
    "discover",
    # Comparison operator for limits
    "CompOp",
]
