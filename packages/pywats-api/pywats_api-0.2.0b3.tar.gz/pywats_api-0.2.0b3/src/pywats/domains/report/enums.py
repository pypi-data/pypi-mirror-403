"""Report domain enums."""
from enum import IntEnum, Enum


class DateGrouping(IntEnum):
    """Date grouping options for filters."""
    NONE = -1
    YEAR = 0
    QUARTER = 1
    MONTH = 2
    WEEK = 3
    DAY = 4
    HOUR = 5


class ReportType(str, Enum):
    """
    Report type for querying headers.
    
    - UUT (U): Unit Under Test reports - test results
    - UUR (R): Unit Under Repair reports - repair/rework records
    """
    UUT = "U"
    UUR = "R"
    
    def __str__(self) -> str:
        return self.value


class ImportMode(Enum):
    """
    Import mode for UUT report creation.
    
    Controls automatic behaviors when creating/modifying test data:
    
    - Import: Passive mode - no automatic status calculation or failure propagation.
              Data is stored exactly as provided. Use for importing historical data
              or data from external systems where status has already been determined.
              
    - Active: Active mode - enables automatic behaviors:
              * Default step status is Passed if not explicitly set
              * Measurement auto-status calculation based on comp/limits
              * Failure propagation up the step hierarchy when fail_parent_on_failure=True
    """
    Import = "Import"
    Active = "Active"
