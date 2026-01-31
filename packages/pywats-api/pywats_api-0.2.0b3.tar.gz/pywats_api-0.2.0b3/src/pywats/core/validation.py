"""Validation utilities for pyWATS.

This module provides validation for report headers (serial numbers, part numbers)
following WATS documentation guidelines.

Key Concepts:
    - "Soft" validation: Raises warnings/exceptions that can be bypassed
    - Problematic characters are blocked by default to prevent issues
    - Bypass is explicit (not accidental) via context manager or flag

Usage:
    # Default: Raises ReportHeaderValidationError on problematic chars
    report = UUTReport(pn="PART-001", sn="SN-001")  # OK
    report = UUTReport(pn="PART*001", sn="SN-001")  # Raises error!
    
    # Bypass validation (explicit opt-in)
    with allow_problematic_characters():
        report = UUTReport(pn="PART*001", sn="SN-001")  # OK
    
    # Or use the suppress prefix
    report = UUTReport(pn="SUPPRESS:PART*001", sn="SN-001")  # Value: "PART*001"

Recommendations (from WATS documentation):
    ✅ Allowed: A-Z, a-z, 0-9, hyphen (-), underscore (_), period (.)
    ❌ Problematic: * % ? [] [^] ! / \\
    
References:
    - WATS Standard Text Format documentation
    - WATS Standard XML/JSON Format documentation
"""
from __future__ import annotations

import re
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional

from .exceptions import ValidationError

# Context variable to track if problematic characters are allowed
_allow_problematic_chars: ContextVar[bool] = ContextVar(
    '_allow_problematic_chars', 
    default=False
)

# Prefix to suppress validation for a single value
SUPPRESS_PREFIX = "SUPPRESS:"

# Maximum length for serial number and part number
MAX_LENGTH = 100

# Pattern for allowed characters (alphanumeric + safe symbols)
# Based on WATS documentation: A-Z, a-z, 0-9, -, _, .
ALLOWED_PATTERN = re.compile(r'^[A-Za-z0-9\-_.]+$')

# Problematic characters that cause issues in WATS searches/filters
# Based on WATS documentation
PROBLEMATIC_CHARS = {
    '*': 'Wildcard for any string',
    '%': 'Wildcard for any string',
    '?': 'Wildcard for any single character',
    '[': 'Defines a range or character list',
    ']': 'Defines a range or character list',
    '^': 'Defines negated list (when in [])',
    '!': 'Used in exclusion filtering',
    '/': 'Path delimiter - interferes with parsing',
    '\\': 'Path delimiter - interferes with parsing',
}


class ReportHeaderValidationError(ValidationError):
    """
    Raised when a report header field contains problematic characters.
    
    This is a "soft" error that can be bypassed using:
    - The `allow_problematic_characters()` context manager
    - The `SUPPRESS:` prefix on the value
    
    Attributes:
        field: The field name (e.g., 'sn', 'pn')
        value: The problematic value
        problematic: List of problematic characters found
        recommendations: Suggested alternatives
    """
    
    def __init__(
        self,
        field: str,
        value: str,
        problematic: list[str],
        operation: Optional[str] = None
    ):
        self.field = field
        self.value = value
        self.problematic = problematic
        
        # Build detailed message
        char_descriptions = [
            f"'{c}' ({PROBLEMATIC_CHARS.get(c, 'reserved')})" 
            for c in problematic
        ]
        
        message = (
            f"Report {field} contains problematic characters: {', '.join(char_descriptions)}. "
            f"Value: '{value}'. "
            f"These characters can cause issues with WATS searches and filters. "
            f"To bypass: use allow_problematic_characters() context manager or prefix with 'SUPPRESS:'"
        )
        
        super().__init__(
            message=message,
            field=field,
            value=value,
            operation=operation,
            details={
                "problematic_characters": problematic,
                "bypass_options": [
                    "with allow_problematic_characters(): ...",
                    f"SUPPRESS:{value}"
                ]
            }
        )


class ReportHeaderValidationWarning(UserWarning):
    """
    Warning issued when problematic characters are used with bypass enabled.
    
    Even when bypassing validation, this warning is issued to ensure
    the user is aware of potential issues.
    """
    pass


@contextmanager
def allow_problematic_characters():
    """
    Context manager to bypass report header validation.
    
    Use this when you intentionally need to use characters that would
    normally be blocked. A warning will still be issued.
    
    Example:
        with allow_problematic_characters():
            report = UUTReport(
                pn="PART/001",  # Normally blocked
                sn="SN*001",    # Normally blocked
                ...
            )
    """
    token = _allow_problematic_chars.set(True)
    try:
        yield
    finally:
        _allow_problematic_chars.reset(token)


def is_problematic_chars_allowed() -> bool:
    """Check if problematic characters are currently allowed."""
    return _allow_problematic_chars.get()


def find_problematic_characters(value: str) -> list[str]:
    """
    Find all problematic characters in a value.
    
    Args:
        value: The string to check
        
    Returns:
        List of problematic characters found (empty if none)
    """
    found = []
    for char in PROBLEMATIC_CHARS:
        if char in value:
            found.append(char)
    return found


def validate_report_header_field(
    value: str,
    field_name: str,
    *,
    allow_bypass: bool = True,
    operation: Optional[str] = None
) -> str:
    """
    Validate a report header field (serial number, part number, etc.).
    
    This function performs "soft" validation - it blocks problematic characters
    by default but allows them to be bypassed explicitly.
    
    Args:
        value: The field value to validate
        field_name: Name of the field (for error messages)
        allow_bypass: Whether to check for bypass conditions (default True)
        operation: Optional operation name for error context
        
    Returns:
        The validated value (with SUPPRESS: prefix stripped if present)
        
    Raises:
        ReportHeaderValidationError: If problematic characters found and not bypassed
    """
    if not value:
        return value
    
    # Check for SUPPRESS: prefix
    if allow_bypass and value.startswith(SUPPRESS_PREFIX):
        actual_value = value[len(SUPPRESS_PREFIX):]
        problematic = find_problematic_characters(actual_value)
        if problematic:
            warnings.warn(
                f"Using problematic characters in {field_name}: "
                f"{', '.join(repr(c) for c in problematic)}. "
                f"This may cause issues with WATS searches/filters.",
                ReportHeaderValidationWarning,
                stacklevel=3
            )
        return actual_value
    
    # Check for context manager bypass
    if allow_bypass and is_problematic_chars_allowed():
        problematic = find_problematic_characters(value)
        if problematic:
            warnings.warn(
                f"Using problematic characters in {field_name}: "
                f"{', '.join(repr(c) for c in problematic)}. "
                f"This may cause issues with WATS searches/filters.",
                ReportHeaderValidationWarning,
                stacklevel=3
            )
        return value
    
    # Validate
    problematic = find_problematic_characters(value)
    if problematic:
        raise ReportHeaderValidationError(
            field=field_name,
            value=value,
            problematic=problematic,
            operation=operation
        )
    
    return value


def validate_serial_number(value: str, *, allow_bypass: bool = True) -> str:
    """
    Validate a serial number field.
    
    Args:
        value: Serial number to validate
        allow_bypass: Whether to allow bypass via context manager or prefix
        
    Returns:
        Validated serial number
        
    Raises:
        ReportHeaderValidationError: If invalid and not bypassed
    """
    return validate_report_header_field(
        value, 
        "serial_number",
        allow_bypass=allow_bypass,
        operation="validate_serial_number"
    )


def validate_part_number(value: str, *, allow_bypass: bool = True) -> str:
    """
    Validate a part number field.
    
    Args:
        value: Part number to validate
        allow_bypass: Whether to allow bypass via context manager or prefix
        
    Returns:
        Validated part number
        
    Raises:
        ReportHeaderValidationError: If invalid and not bypassed
    """
    return validate_report_header_field(
        value,
        "part_number", 
        allow_bypass=allow_bypass,
        operation="validate_part_number"
    )


def validate_batch_serial_number(value: str, *, allow_bypass: bool = True) -> str:
    """
    Validate a batch serial number field.
    
    Args:
        value: Batch serial number to validate
        allow_bypass: Whether to allow bypass via context manager or prefix
        
    Returns:
        Validated batch serial number
        
    Raises:
        ReportHeaderValidationError: If invalid and not bypassed
    """
    return validate_report_header_field(
        value,
        "batch_serial_number",
        allow_bypass=allow_bypass,
        operation="validate_batch_serial_number"
    )
