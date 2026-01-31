"""
UUR (Unit Under Repair) report models.

Simplified Pydantic models following UUTReport design pattern.
Failures are stored on sub-units (UURSubUnit.failures), not on the report.
Attachments use the shared Attachment class from report_models.
"""

# Core UUR models
from .uur_report import UURReport
from .uur_info import UURInfo
from .uur_sub_unit import UURSubUnit, UURFailure

# Shared attachment (same as UUT)
from ..attachment import Attachment

# SubRepair model for server deserialization (server returns subRepairs in JSON)
from .sub_repair import SubRepair

__all__ = [
    # Core models
    'UURReport',
    'UURInfo',
    'UURSubUnit',
    'UURFailure',
    'Attachment',
    'SubRepair',
]