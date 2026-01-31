"""pyWATS Models

Report models for UUT/UUR format.
These are re-exported from the domains.report.report_models module.
Domain-specific models are in their respective domains.
"""

# UUT/UUR Report models (WSJF format - full report structure)
# Re-exported from domains.report.report_models for convenient imports
from ..domains.report.report_models import (
    # Base classes
    WATSBase, Report, ReportStatus,
    ReportInfo, MiscInfo, AdditionalData, BinaryData,
    Asset as ReportAsset, AssetStats, Chart, ChartSeries, ChartType,
    SubUnit, Attachment as ReportAttachment, DeserializationContext,
    # UUT Report
    UUTReport, UUTInfo, Step, StepStatus,
    # UUR Report
    UURReport, UURInfo, SubRepair
)

# Comparison operator (convenient import without deep path)
from pywats.shared.enums import CompOp

__all__ = [
    # UUT/UUR Report models (WSJF format)
    "WATSBase",
    "Report",
    "ReportStatus",
    "ReportInfo",
    "MiscInfo",
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
    "UUTReport",
    "UUTInfo",
    "Step",
    "StepStatus",
    "UURReport",
    "UURInfo",
    "SubRepair",
    # Comparison operator
    "CompOp",
]

