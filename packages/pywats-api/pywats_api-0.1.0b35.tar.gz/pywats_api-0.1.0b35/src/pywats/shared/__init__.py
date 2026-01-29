"""Shared components for pyWATS.

Contains base models, common types, validators, enums, and discovery helpers used across domains.

For LLM/Agent Integration:
--------------------------
- Use `discover` module to explore available fields, methods, and valid values
- Use `Result`, `Success`, `Failure` for structured error handling
- All models use snake_case field names (not camelCase aliases)

Type-Safe Enums:
----------------
- StatusFilter: Query filter for report status (PASSED, FAILED, ERROR, etc.)
- RunFilter: Step analysis run selection (FIRST, LAST, ALL)
- StepType: Test step types (NUMERIC_LIMIT, PASS_FAIL, etc.)
- CompOperator: Comparison operators for limits (GELE, GT, LT, etc.)
- SortDirection: Sort direction for dimension queries (ASC, DESC)

Path Utilities:
---------------
- StepPath: Handle step paths with seamless / ↔ ¶ conversion
- MeasurementPath: Handle measurement paths with seamless / ↔ ¶ conversion
- normalize_path: Convert display path (/) to API path (¶)
- display_path: Convert API path (¶) to display path (/)
"""
from .base_model import PyWATSModel
from .common_types import Setting, ChangeType
from .result import Result, Success, Failure, ErrorCode, failure_from_exception
from .enums import StatusFilter, RunFilter, StepType, CompOperator, SortDirection
from .paths import StepPath, MeasurementPath, normalize_path, display_path, normalize_paths
from . import discovery as discover

__all__ = [
    # Base model
    "PyWATSModel",
    # Common types
    "Setting",
    "ChangeType",
    # Result types for structured error handling
    "Result",
    "Success",
    "Failure",
    "ErrorCode",
    "failure_from_exception",
    # Type-safe enums
    "StatusFilter",
    "RunFilter",
    "StepType",
    "CompOperator",
    "SortDirection",
    # Path utilities
    "StepPath",
    "MeasurementPath",
    "normalize_path",
    "display_path",
    "normalize_paths",
    # Discovery module for API exploration
    "discover",
]
