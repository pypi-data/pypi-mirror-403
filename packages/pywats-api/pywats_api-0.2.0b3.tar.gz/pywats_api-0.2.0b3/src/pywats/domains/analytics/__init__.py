"""Analytics domain module.

Provides statistics, KPIs, yield analysis, and dashboard data services.

BACKEND API MAPPING
-------------------
This module maps to the WATS backend '/api/App/*' endpoints.
We chose 'analytics' as the Python module name because it better describes
the functionality (yield analysis, KPIs, statistics, OEE) while 'App' is the
server's controller name.

All API calls in this module target /api/App/* endpoints:
- GET/POST /api/App/DynamicYield
- GET/POST /api/App/DynamicRepair  
- GET/POST /api/App/TopFailed
- GET/POST /api/App/TestStepAnalysis
- etc.

Internal API endpoints (uses internal APIs which may change):
- POST /api/internal/UnitFlow
- GET /api/internal/UnitFlow/Links
- GET /api/internal/UnitFlow/Nodes
- POST /api/internal/UnitFlow/SN
- POST /api/internal/UnitFlow/SplitBy
- POST /api/internal/UnitFlow/UnitOrder
- GET /api/internal/UnitFlow/Units
- GET/POST /api/internal/App/MeasurementList
- GET/POST /api/internal/App/StepStatusList

Type-Safe Enums:
----------------
- Dimension: Grouping dimensions for dynamic queries (PART_NUMBER, STATION_NAME, etc.)
- KPI: Key Performance Indicators (UNIT_COUNT, FPY, etc.)
- RepairDimension: Repair-specific dimensions (REPAIR_CODE, COMPONENT_REF, etc.)
- RepairKPI: Repair-specific KPIs (REPAIR_COUNT, REPAIR_REPORT_COUNT)
- DimensionBuilder: Fluent builder for constructing dimension queries
"""
from .enums import (
    YieldDataType, 
    ProcessType,
    # Dimension query enums
    Dimension,
    RepairDimension,
    KPI,
    RepairKPI,
    DimensionBuilder,
    # Alarm type enum
    AlarmType,
)
from .models import (
    YieldData,
    ProcessInfo,
    LevelInfo,
    ProductGroup,
    StepAnalysisRow,
    # New typed models
    TopFailedStep,
    RepairStatistics,
    RepairHistoryRecord,
    MeasurementData,
    AggregatedMeasurement,
    OeeAnalysisResult,
    # Unit Flow models (internal API)
    UnitFlowNode,
    UnitFlowLink,
    UnitFlowUnit,
    UnitFlowFilter,
    UnitFlowResult,
    # Step/Measurement filter models (internal API)
    StepStatusItem,
    MeasurementListItem,
    # Alarm models (internal API)
    AlarmLog,
)

# Async implementations (primary API)
from .async_repository import AsyncAnalyticsRepository
from .async_service import AsyncAnalyticsService

__all__ = [
    # Enums
    "YieldDataType",
    "ProcessType",
    # Dimension query enums and builder
    "Dimension",
    "RepairDimension",
    "KPI",
    "RepairKPI",
    "DimensionBuilder",
    # Alarm type enum
    "AlarmType",
    # Models
    "YieldData",
    "ProcessInfo",
    "LevelInfo",
    "ProductGroup",
    "StepAnalysisRow",
    # Typed models
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
    # Alarm models (internal API)
    "AlarmLog",
    # Async implementations
    "AsyncAnalyticsRepository",
    "AsyncAnalyticsService",
]
