"""
CFX Sample Messages.

Realistic sample IPC-CFX messages based on the official CFX SDK examples.
Use these for testing, development, and understanding the message formats.
"""

from .test_samples import (
    UNITS_TESTED_ICT,
    UNITS_TESTED_FCT,
    UNITS_TESTED_MULTI_MEASUREMENT,
    UNITS_INSPECTED_AOI,
    UNITS_INSPECTED_SPI,
)

from .production_samples import (
    WORK_STARTED_SAMPLE,
    WORK_COMPLETED_PASSED,
    WORK_COMPLETED_FAILED,
    UNITS_ARRIVED_SAMPLE,
    UNITS_DEPARTED_SAMPLE,
    UNITS_DISQUALIFIED_SAMPLE,
)

from .material_samples import (
    MATERIALS_INSTALLED_SMT,
    MATERIALS_INSTALLED_THROUGH_HOLE,
    MATERIALS_LOADED_FEEDER,
)

from .resource_samples import (
    FAULT_OCCURRED_TEMPERATURE,
    FAULT_OCCURRED_FEEDER,
    FAULT_CLEARED_SAMPLE,
    STATION_STATE_CHANGED_SAMPLES,
)

from .generator import CFXSampleGenerator

__all__ = [
    # Test samples
    "UNITS_TESTED_ICT",
    "UNITS_TESTED_FCT", 
    "UNITS_TESTED_MULTI_MEASUREMENT",
    "UNITS_INSPECTED_AOI",
    "UNITS_INSPECTED_SPI",
    # Production samples
    "WORK_STARTED_SAMPLE",
    "WORK_COMPLETED_PASSED",
    "WORK_COMPLETED_FAILED",
    "UNITS_ARRIVED_SAMPLE",
    "UNITS_DEPARTED_SAMPLE",
    "UNITS_DISQUALIFIED_SAMPLE",
    # Material samples
    "MATERIALS_INSTALLED_SMT",
    "MATERIALS_INSTALLED_THROUGH_HOLE",
    "MATERIALS_LOADED_FEEDER",
    # Resource samples
    "FAULT_OCCURRED_TEMPERATURE",
    "FAULT_OCCURRED_FEEDER",
    "FAULT_CLEARED_SAMPLE",
    "STATION_STATE_CHANGED_SAMPLES",
    # Generator
    "CFXSampleGenerator",
]
