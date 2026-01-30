"""Analytics domain enumerations.

Enumerations for statistics, KPI, yield analysis, and dimension queries.

These provide type-safe alternatives to magic strings for analytics queries.

Usage:
    from pywats import Dimension, KPI, DimensionBuilder
    
    # Build a dimension query with type safety
    dims = DimensionBuilder()\\
        .add(KPI.UNIT_COUNT, desc=True)\\
        .add(Dimension.PART_NUMBER)\\
        .add(Dimension.PERIOD)\\
        .build()
    
    filter = WATSFilter(dimensions=dims, period_count=30)
"""
from enum import Enum, IntEnum
from typing import List, Optional, Union

from ...shared.enums import SortDirection


class YieldDataType(IntEnum):
    """Types of yield data calculations."""
    FIRST_PASS = 1
    """First pass yield (passed on first attempt)."""
    
    FINAL = 2
    """Final yield (eventually passed after repairs)."""
    
    ROLLED = 3
    """Rolled throughput yield."""


class ProcessType(IntEnum):
    """Process/operation categories."""
    TEST = 1
    """Test operation."""
    
    REPAIR = 2
    """Repair operation."""
    
    CALIBRATION = 3
    """Calibration operation."""


class Dimension(str, Enum):
    """
    Dimension fields for dynamic yield/repair queries.
    
    Dimensions define the grouping/breakdown of statistics.
    Use with DimensionBuilder for type-safe query construction.
    
    Example:
        >>> from pywats import Dimension, DimensionBuilder
        >>> dims = DimensionBuilder().add(Dimension.PART_NUMBER).add(Dimension.PERIOD).build()
        'partNumber;period'
    """
    # Product dimensions
    PART_NUMBER = "partNumber"
    """Product part number."""
    
    PRODUCT_NAME = "productName"
    """Product name."""
    
    PRODUCT_GROUP = "productGroup"
    """Product group."""
    
    REVISION = "revision"
    """Product revision."""
    
    # Location/station dimensions
    STATION_NAME = "stationName"
    """Test station name."""
    
    LOCATION = "location"
    """Physical location."""
    
    PURPOSE = "purpose"
    """Station purpose."""
    
    # Operation dimensions
    TEST_OPERATION = "testOperation"
    """Test operation name."""
    
    PROCESS_CODE = "processCode"
    """Process code number."""
    
    # Time dimensions
    PERIOD = "period"
    """Time period (requires dateGrouping)."""
    
    # Software dimensions
    SW_FILENAME = "swFilename"
    """Test software filename."""
    
    SW_VERSION = "swVersion"
    """Test software version."""
    
    # Production dimensions
    LEVEL = "level"
    """Production level (PCBA, Module, etc.)."""
    
    BATCH_NUMBER = "batchNumber"
    """Production batch number."""
    
    OPERATOR = "operator"
    """Operator name."""
    
    FIXTURE_ID = "fixtureId"
    """Test fixture ID."""
    
    SOCKET_INDEX = "socketIndex"
    """Socket index on fixture."""
    
    # Failure dimensions
    ERROR_CODE = "errorCode"
    """Error code."""
    
    STEP_CAUSED_UUT_FAILURE = "stepCausedUutFailure"
    """Step that caused UUT failure."""
    
    STEP_PATH_CAUSED_UUT_FAILURE = "stepPathCausedUutFailure"
    """Path of step that caused failure."""
    
    # Misc dimensions
    MISC_INFO_DESCRIPTION = "miscInfoDescription"
    """Misc info description field."""
    
    MISC_INFO_STRING = "miscInfoString"
    """Misc info string field."""
    
    # Asset dimensions
    ASSET_SERIAL_NUMBER = "assetSerialNumber"
    """Asset serial number."""
    
    ASSET_NAME = "assetName"
    """Asset name."""
    
    # Unit type
    UNIT_TYPE = "unitType"
    """Unit type classification."""


class RepairDimension(str, Enum):
    """
    Additional dimensions specific to repair statistics.
    
    Use with DimensionBuilder for DynamicRepair queries.
    
    Example:
        >>> dims = DimensionBuilder()\\
        ...     .add(RepairDimension.REPAIR_CODE)\\
        ...     .add(RepairDimension.COMPONENT_REF)\\
        ...     .build()
    """
    REPAIR_OPERATION = "repairOperation"
    """Repair operation name."""
    
    REPAIR_CODE = "repairCode"
    """Repair action code."""
    
    REPAIR_CATEGORY = "repairCategory"
    """Repair category."""
    
    REPAIR_TYPE = "repairType"
    """Repair type."""
    
    # Component dimensions
    COMPONENT_REF = "componentRef"
    """Component reference designator."""
    
    COMPONENT_NUMBER = "componentNumber"
    """Component part number."""
    
    COMPONENT_REVISION = "componentRevision"
    """Component revision."""
    
    COMPONENT_VENDOR = "componentVendor"
    """Component vendor."""
    
    COMPONENT_DESCRIPTION = "componentDescription"
    """Component description."""
    
    # Related test dimensions
    FUNCTION_BLOCK = "functionBlock"
    """Function block."""
    
    REFERENCED_STEP = "referencedStep"
    """Referenced test step."""
    
    REFERENCED_STEP_PATH = "referencedStepPath"
    """Path of referenced test step."""
    
    # Test context for repair
    TEST_PERIOD = "testPeriod"
    """Test period."""
    
    TEST_LEVEL = "testLevel"
    """Test level."""
    
    TEST_STATION_NAME = "testStationName"
    """Test station name."""
    
    TEST_LOCATION = "testLocation"
    """Test location."""
    
    TEST_PURPOSE = "testPurpose"
    """Test purpose."""
    
    TEST_OPERATOR = "testOperator"
    """Test operator."""


class KPI(str, Enum):
    """
    Key Performance Indicators for yield/repair queries.
    
    KPIs are numeric metrics that can be returned and sorted.
    Use with DimensionBuilder for sorting (asc/desc).
    
    Example:
        >>> dims = DimensionBuilder()\\
        ...     .add(KPI.UNIT_COUNT, desc=True)\\  # Sort by volume descending
        ...     .add(KPI.FPY)\\
        ...     .build()
    """
    # Volume KPIs
    UNIT_COUNT = "unitCount"
    """Total unit count."""
    
    # Pass counts
    FP_COUNT = "fpCount"
    """First pass count."""
    
    SP_COUNT = "spCount"
    """Second pass count."""
    
    TP_COUNT = "tpCount"
    """Third pass count."""
    
    LP_COUNT = "lpCount"
    """Last pass count."""
    
    # Fail counts
    FP_FAIL_COUNT = "fpFailCount"
    """First pass fail count."""
    
    SP_FAIL_COUNT = "spFailCount"
    """Second pass fail count."""
    
    TP_FAIL_COUNT = "tpFailCount"
    """Third pass fail count."""
    
    LP_FAIL_COUNT = "lpFailCount"
    """Last pass fail count."""
    
    # Yield percentages
    FPY = "fpy"
    """First pass yield (%)."""
    
    SPY = "spy"
    """Second pass yield (%)."""
    
    TPY = "tpy"
    """Third pass yield (%)."""
    
    LPY = "lpy"
    """Last pass yield (%)."""
    
    # PPM metrics
    PPM_FPY = "ppmFpy"
    """First pass yield in PPM."""
    
    PPM_SPY = "ppmSpy"
    """Second pass yield in PPM."""
    
    PPM_TPY = "ppmTpy"
    """Third pass yield in PPM."""
    
    PPM_LPY = "ppmLpy"
    """Last pass yield in PPM."""
    
    PPM_TEST_YIELD = "ppmTestYield"
    """Test yield in PPM."""
    
    # Other yield metrics
    TEST_YIELD_COUNT = "testYieldCount"
    """Test yield count."""
    
    TEST_REPORT_COUNT = "testReportCount"
    """Test report count."""
    
    TEST_YIELD = "testYield"
    """Test yield percentage."""
    
    RETEST_COUNT = "retestCount"
    """Retest count."""
    
    # Timestamps
    FIRST_UTC = "firstUtc"
    """First occurrence timestamp."""
    
    LAST_UTC = "lastUtc"
    """Last occurrence timestamp."""


class RepairKPI(str, Enum):
    """
    KPIs specific to repair statistics.
    
    Example:
        >>> dims = DimensionBuilder()\\
        ...     .add(RepairKPI.REPAIR_COUNT, desc=True)\\
        ...     .build()
    """
    REPAIR_REPORT_COUNT = "repairReportCount"
    """Number of repair reports."""
    
    REPAIR_COUNT = "repairCount"
    """Total repair count."""


class DimensionBuilder:
    """
    Builder for constructing dimension query strings with type safety.
    
    Provides a fluent API for building dimension strings, avoiding
    typos and enabling IDE autocomplete.
    
    Example:
        >>> from pywats import DimensionBuilder, Dimension, KPI
        >>> 
        >>> # Build a yield query
        >>> dims = DimensionBuilder()\\
        ...     .add(KPI.UNIT_COUNT, desc=True)\\
        ...     .add(Dimension.PART_NUMBER)\\
        ...     .add(Dimension.STATION_NAME)\\
        ...     .add(Dimension.PERIOD)\\
        ...     .build()
        >>> print(dims)
        'unitCount desc;partNumber;stationName;period'
        >>> 
        >>> # Use with WATSFilter
        >>> filter = WATSFilter(dimensions=dims, period_count=30)
    """
    
    def __init__(self) -> None:
        """Create an empty DimensionBuilder."""
        self._parts: List[str] = []
    
    def add(
        self, 
        dimension: Union[Dimension, RepairDimension, KPI, RepairKPI, str],
        direction: Optional[SortDirection] = None,
        *,
        asc: bool = False,
        desc: bool = False
    ) -> "DimensionBuilder":
        """
        Add a dimension or KPI to the query.
        
        Args:
            dimension: The dimension or KPI to add
            direction: Optional sort direction (SortDirection.ASC or DESC)
            asc: Shorthand for direction=SortDirection.ASC
            desc: Shorthand for direction=SortDirection.DESC
            
        Returns:
            self for method chaining
            
        Example:
            >>> builder.add(KPI.UNIT_COUNT, desc=True)
            >>> builder.add(Dimension.PART_NUMBER)
        """
        # Get string value
        value = dimension.value if isinstance(dimension, Enum) else dimension
        
        # Determine sort direction
        if desc:
            direction = SortDirection.DESC
        elif asc:
            direction = SortDirection.ASC
        
        # Build part with optional direction
        if direction:
            self._parts.append(f"{value} {direction.value}")
        else:
            self._parts.append(value)
        
        return self
    
    def add_all(
        self, 
        *dimensions: Union[Dimension, RepairDimension, KPI, RepairKPI, str]
    ) -> "DimensionBuilder":
        """
        Add multiple dimensions without sorting.
        
        Args:
            *dimensions: Dimensions to add
            
        Returns:
            self for method chaining
            
        Example:
            >>> builder.add_all(Dimension.PART_NUMBER, Dimension.PERIOD)
        """
        for dim in dimensions:
            self.add(dim)
        return self
    
    def build(self) -> str:
        """
        Build the dimension string for use in WATSFilter.
        
        Returns:
            Semicolon-separated dimension string
            
        Example:
            >>> dims = DimensionBuilder().add(KPI.FPY).add(Dimension.PERIOD).build()
            'fpy;period'
        """
        return ";".join(self._parts)
    
    def __str__(self) -> str:
        """Convert to string (same as build())."""
        return self.build()
    
    def clear(self) -> "DimensionBuilder":
        """Clear all dimensions and start fresh."""
        self._parts = []
        return self
    
    @classmethod
    def yield_by_product(cls, include_period: bool = True) -> "DimensionBuilder":
        """
        Preset builder for yield analysis by product.
        
        Args:
            include_period: Include period dimension for time series
            
        Returns:
            Pre-configured DimensionBuilder
            
        Example:
            >>> dims = DimensionBuilder.yield_by_product().build()
            'unitCount desc;fpy;partNumber;period'
        """
        builder = cls()
        builder.add(KPI.UNIT_COUNT, desc=True)
        builder.add(KPI.FPY)
        builder.add(Dimension.PART_NUMBER)
        if include_period:
            builder.add(Dimension.PERIOD)
        return builder
    
    @classmethod
    def yield_by_station(cls, include_period: bool = True) -> "DimensionBuilder":
        """
        Preset builder for yield analysis by station.
        
        Returns:
            Pre-configured DimensionBuilder
        """
        builder = cls()
        builder.add(KPI.UNIT_COUNT, desc=True)
        builder.add(KPI.FPY)
        builder.add(Dimension.STATION_NAME)
        if include_period:
            builder.add(Dimension.PERIOD)
        return builder
    
    @classmethod
    def top_failing_products(cls) -> "DimensionBuilder":
        """
        Preset builder for finding worst-yielding products.
        
        Returns:
            Pre-configured DimensionBuilder
        """
        builder = cls()
        builder.add(KPI.FPY, asc=True)  # Lowest yield first
        builder.add(KPI.UNIT_COUNT)
        builder.add(Dimension.PART_NUMBER)
        return builder
