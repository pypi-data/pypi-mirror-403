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


class CompOperator(str, Enum):
    """
    Comparison operators for numeric limit steps.
    
    Defines how a measured value is compared against limits.
    
    Example:
        >>> # Check if step uses greater-than comparison
        >>> if step.comp_operator == CompOperator.GT:
        ...     print("Must be greater than limit")
    """
    # Standard comparisons
    EQ = "EQ"
    """Equal to (==)."""
    
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
    
    # Range comparisons
    GELE = "GELE"
    """Between inclusive (>= low AND <= high)."""
    
    GTLT = "GTLT"
    """Between exclusive (> low AND < high)."""
    
    GELT = "GELT"
    """Between (>= low AND < high)."""
    
    GTLE = "GTLE"
    """Between (> low AND <= high)."""
    
    # Outside range
    LTGT = "LTGT"
    """Outside range (< low OR > high)."""
    
    LEGE = "LEGE"
    """Outside or equal (<= low OR >= high)."""
    
    # Case variations (some backends use these)
    LOG = "LOG"
    """Logarithmic comparison (special)."""
    
    CASESENSITIVE = "CaseSensitiveStringCompare"
    """Case-sensitive string comparison."""
    
    CASEINSENSITIVE = "CaseInsensitiveStringCompare"
    """Case-insensitive string comparison."""


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
