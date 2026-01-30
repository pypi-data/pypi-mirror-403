"""Shared enums used across pyWATS domains.

These enums provide type-safe values for common parameters across the API,
eliminating magic strings and enabling IDE autocomplete.

Usage:
    from pywats import StatusFilter, RunFilter, StepType
    
    filter = WATSFilter(status=StatusFilter.FAILED, run=RunFilter.FIRST)
"""
from enum import Enum, IntEnum


class StatusFilter(str, Enum):
    """
    Status filter values for querying reports.
    
    Used for filtering reports by test outcome in WATSFilter and analytics queries.
    Inherits from str so it serializes correctly to the API.
    
    Note: This is different from ReportStatus which uses single-letter codes
    for WSJF format. StatusFilter uses the full string values expected by 
    query endpoints.
    
    Example:
        >>> filter = WATSFilter(status=StatusFilter.PASSED)
        >>> # Or with string (backward compatible)
        >>> filter = WATSFilter(status="Passed")
    """
    PASSED = "Passed"
    """Test passed successfully."""
    
    FAILED = "Failed"
    """Test failed with a failure condition."""
    
    ERROR = "Error"
    """Test encountered an error (not pass/fail)."""
    
    TERMINATED = "Terminated"
    """Test was terminated before completion."""
    
    DONE = "Done"
    """Test completed (neutral status, no pass/fail)."""
    
    SKIPPED = "Skipped"
    """Test was skipped."""


class RunFilter(IntEnum):
    """
    Run filter for step/measurement analysis.
    
    Specifies which run(s) to include when analyzing multi-run test data.
    
    Example:
        >>> filter = WATSFilter(run=RunFilter.FIRST)
        >>> filter = WATSFilter(run=RunFilter.ALL)
    """
    FIRST = 1
    """Only first run (first attempt)."""
    
    SECOND = 2
    """Only second run (first retest)."""
    
    THIRD = 3
    """Only third run (second retest)."""
    
    LAST = -1
    """Only last/final run for each unit."""
    
    ALL = -2
    """All runs (include retests)."""


class StepType(str, Enum):
    """
    Test step types in WATS.
    
    Used to categorize and filter steps by their function.
    These match the WATS backend step type values.
    
    Example:
        >>> # Filter for measurement steps only
        >>> [s for s in steps if s.step_type == StepType.NUMERIC_LIMIT]
    """
    # Sequence/Group steps
    SEQUENCE_CALL = "SequenceCall"
    """Call to another sequence/routine."""
    
    # Measurement steps
    NUMERIC_LIMIT = "NumericLimit"
    """Numeric measurement with limits (pass/fail based on value)."""
    
    STRING_VALUE = "StringValue"
    """String value measurement (match or comparison)."""
    
    PASS_FAIL = "PassFail"
    """Simple pass/fail step (boolean result)."""
    
    MULTIPLE_NUMERIC = "MultipleNumericLimit"
    """Multiple numeric measurements in one step."""
    
    # Action steps
    ACTION = "Action"
    """Action step (do something, no measurement)."""
    
    MESSAGE_POPUP = "MessagePopup"
    """Display a message to operator."""
    
    CALL_EXECUTABLE = "CallExecutable"
    """Call external executable/script."""
    
    # Flow control
    LABEL = "Label"
    """Label for goto/flow control."""
    
    GOTO = "Goto"
    """Goto/jump to label."""
    
    FLOW_CONTROL = "FlowControl"
    """Flow control step (if/else/loop)."""
    
    STATEMENT = "Statement"
    """Code statement/expression."""
    
    # Property steps
    PROPERTY_LOADER = "PropertyLoader"
    """Load property from storage."""
    
    # Generic
    GENERIC = "Generic"
    """Generic step type."""
    
    # Unknown/other
    UNKNOWN = "Unknown"
    """Unknown step type (for forward compatibility)."""


class CompOp(str, Enum):
    """
    Comparison operators for numeric limit steps.
    
    Defines how a measured value is compared against limits.
    Inherits from (str, Enum) for JSON serialization compatibility.
    
    Also available as CompOperator alias for backward compatibility.
    
    Example:
        >>> from pywats.shared.enums import CompOp
        >>> # Or use the alias:
        >>> from pywats.shared.enums import CompOperator
        >>> 
        >>> if step.comp_op == CompOp.GELE:
        ...     print("Value must be between limits (inclusive)")
    """
    # None limit compOp
    LOG = "LOG"
    """No limit - just log the value."""

    # Single limit compOp (lowLimit required, highLimit not supported)
    EQ = "EQ"
    """Equal to (==)."""
    
    EQT = "EQT"
    """Equal or Tolerant."""
    
    NE = "NE"
    """Not equal to (!=)."""
    
    LT = "LT"
    """Less than (<)."""
    
    LE = "LE"
    """Less than or equal (<=)."""
    
    GT = "GT"
    """Greater than (>)."""
    
    GE = "GE"
    """Greater than or equal (>=)."""
    
    CASESENSIT = "CASESENSIT"
    """Case-sensitive string comparison."""
    
    IGNORECASE = "IGNORECASE"
    """Case-insensitive string comparison."""

    # Dual limit compOp (both lowLimit and highLimit required)
    # Range comparisons (AND - value must be within range)
    GTLT = "GTLT"
    """Between exclusive (> low AND < high)."""
    
    GTLE = "GTLE"
    """Between (> low AND <= high)."""
    
    GELT = "GELT"
    """Between (>= low AND < high)."""
    
    GELE = "GELE"
    """Between inclusive (>= low AND <= high)."""

    # Outside range comparisons (OR - value must be outside range)
    LTGT = "LTGT"
    """Outside range (< low OR > high)."""
    
    LTGE = "LTGE"
    """Outside or equal (< low OR >= high)."""
    
    LEGT = "LEGT"
    """Outside or equal (<= low OR > high)."""
    
    LEGE = "LEGE"
    """Outside or equal (<= low OR >= high)."""

    def __str__(self) -> str:
        """Return the value for serialization."""
        return self.value

    def __repr__(self) -> str:
        """Return representation."""
        return f"CompOp.{self.name}"

    def get_limits_requirement(self) -> tuple[bool, bool]:
        """
        Returns a tuple indicating whether lowLimit and highLimit are required.
        
        Returns:
            (low_required, high_required) tuple
        """
        if self == CompOp.LOG:
            return (False, False)
        elif self in {
            CompOp.EQ, CompOp.EQT, CompOp.NE, CompOp.LT, CompOp.LE, 
            CompOp.GT, CompOp.GE, CompOp.CASESENSIT, CompOp.IGNORECASE
        }:
            return (True, False)
        else:
            return (True, True)

    def validate_limits(self, low_limit: float | None, high_limit: float | None) -> bool:
        """Validate that limits match requirements for this operator."""
        low_required, high_required = self.get_limits_requirement()
        
        if not low_required and not high_required:
            return True
        if low_required and low_limit is None:
            return False
        if high_required and high_limit is None:
            return False
        return True

    def evaluate(
        self, 
        value: float | int, 
        low_limit: float | int | None = None, 
        high_limit: float | int | None = None
    ) -> bool:
        """
        Evaluate whether a measurement value passes the comparison.
        
        Args:
            value: The measured value to evaluate
            low_limit: The low limit
            high_limit: The high limit (for dual-limit operators)
            
        Returns:
            True if the measurement passes, False if it fails
        """
        if self == CompOp.LOG:
            return True
        if self in {CompOp.CASESENSIT, CompOp.IGNORECASE, CompOp.EQT}:
            return True  # String comparisons not supported
        
        # Single-limit comparisons
        if self == CompOp.EQ:
            return value == low_limit if low_limit is not None else True
        elif self == CompOp.NE:
            return value != low_limit if low_limit is not None else True
        elif self == CompOp.GT:
            return value > low_limit if low_limit is not None else True
        elif self == CompOp.LT:
            return value < low_limit if low_limit is not None else True
        elif self == CompOp.GE:
            return value >= low_limit if low_limit is not None else True
        elif self == CompOp.LE:
            return value <= low_limit if low_limit is not None else True
        
        # Dual-limit AND comparisons
        if low_limit is None or high_limit is None:
            return True
        if self == CompOp.GTLT:
            return value > low_limit and value < high_limit
        elif self == CompOp.GELE:
            return value >= low_limit and value <= high_limit
        elif self == CompOp.GELT:
            return value >= low_limit and value < high_limit
        elif self == CompOp.GTLE:
            return value > low_limit and value <= high_limit
        
        # Dual-limit OR comparisons
        elif self == CompOp.LTGT:
            return value < low_limit or value > high_limit
        elif self == CompOp.LEGE:
            return value <= low_limit or value >= high_limit
        elif self == CompOp.LEGT:
            return value <= low_limit or value > high_limit
        elif self == CompOp.LTGE:
            return value < low_limit or value >= high_limit
        
        return True


# Backward compatibility alias
CompOperator = CompOp


class SortDirection(str, Enum):
    """
    Sort direction for dimension queries.
    
    Used with DimensionBuilder to specify ordering.
    
    Example:
        >>> builder = DimensionBuilder()
        >>> builder.add(KPI.UNIT_COUNT, SortDirection.DESC)
    """
    ASC = "asc"
    """Ascending order (smallest first)."""
    
    DESC = "desc"
    """Descending order (largest first)."""
