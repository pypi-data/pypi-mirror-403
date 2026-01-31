"""OData query helpers for safe filter construction.

This module provides utilities for building safe OData filter expressions,
protecting against injection attacks when constructing queries from user input.

Usage:
------
    from pywats.shared.odata import escape_string, build_filter
    
    # Safe string escaping
    safe_value = escape_string(user_input)
    filter_expr = f"partNumber eq '{safe_value}'"
    
    # Using the filter builder
    filter_expr = build_filter(
        ("partNumber", "eq", part_number),
        ("status", "eq", "Passed"),
    )
    
    # With date handling
    from datetime import date
    filter_expr = build_filter(
        ("start", "ge", date(2024, 1, 1)),
        ("start", "lt", date(2024, 2, 1)),
    )

Security Notes:
---------------
- Always use escape_string() when embedding user input in OData filters
- The build_filter() function automatically escapes all string values
- Never use f-strings with raw user input in OData expressions
"""
from datetime import date, datetime
from typing import Any, List, Tuple, Union, Optional
import re

__all__ = [
    "escape_string",
    "escape_guid",
    "format_value",
    "build_filter",
    "ODataFilterBuilder",
]


def escape_string(value: str) -> str:
    """Escape a string for safe use in OData filter expressions.
    
    OData uses single quotes for string literals. This function escapes
    single quotes by doubling them, preventing injection attacks.
    
    Args:
        value: The string value to escape
        
    Returns:
        The escaped string (without surrounding quotes)
        
    Example:
        >>> escape_string("O'Brien")
        "O''Brien"
        >>> escape_string("normal")
        "normal"
    """
    if not isinstance(value, str):
        value = str(value)
    # OData escapes single quotes by doubling them
    return value.replace("'", "''")


def escape_guid(value: str) -> str:
    """Validate and format a GUID for OData.
    
    Args:
        value: A GUID string (with or without dashes)
        
    Returns:
        The GUID formatted for OData (lowercase, with dashes)
        
    Raises:
        ValueError: If the value is not a valid GUID format
        
    Example:
        >>> escape_guid("550e8400-e29b-41d4-a716-446655440000")
        "550e8400-e29b-41d4-a716-446655440000"
    """
    # Remove any existing dashes and validate hex characters
    clean = value.replace("-", "").lower()
    if len(clean) != 32 or not all(c in "0123456789abcdef" for c in clean):
        raise ValueError(f"Invalid GUID format: {value}")
    
    # Format with dashes
    return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"


def format_value(value: Any) -> str:
    """Format a Python value as an OData literal.
    
    Handles strings, numbers, booleans, dates, datetimes, and None.
    
    Args:
        value: The Python value to format
        
    Returns:
        The OData-formatted literal string
        
    Example:
        >>> format_value("test")
        "'test'"
        >>> format_value(42)
        "42"
        >>> format_value(True)
        "true"
        >>> format_value(date(2024, 1, 15))
        "2024-01-15"
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f"'{escape_string(value)}'"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    elif isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    else:
        # Fall back to string representation
        return f"'{escape_string(str(value))}'"


def build_filter(*conditions: Tuple[str, str, Any], operator: str = "and") -> str:
    """Build an OData filter expression from conditions.
    
    Each condition is a tuple of (field, operator, value). Values are
    automatically escaped for safe inclusion in the filter.
    
    Args:
        *conditions: Tuples of (field_name, comparison_op, value)
        operator: Logical operator to join conditions ("and" or "or")
        
    Returns:
        The complete OData filter expression
        
    Example:
        >>> build_filter(
        ...     ("partNumber", "eq", "PN-001"),
        ...     ("status", "eq", "Passed"),
        ... )
        "partNumber eq 'PN-001' and status eq 'Passed'"
        
        >>> build_filter(
        ...     ("count", "gt", 10),
        ...     ("count", "lt", 100),
        ... )
        "count gt 10 and count lt 100"
    """
    if not conditions:
        return ""
    
    parts = []
    for field, op, value in conditions:
        formatted = format_value(value)
        parts.append(f"{field} {op} {formatted}")
    
    return f" {operator} ".join(parts)


class ODataFilterBuilder:
    """Fluent builder for constructing OData filter expressions.
    
    Provides a safe, fluent API for building complex OData filters.
    
    Example:
        >>> from pywats.shared.odata import ODataFilterBuilder
        >>> 
        >>> filter_expr = (ODataFilterBuilder()
        ...     .field("partNumber").eq("PN-001")
        ...     .field("status").eq("Passed")
        ...     .field("start").ge(date(2024, 1, 1))
        ...     .build())
        >>> print(filter_expr)
        "partNumber eq 'PN-001' and status eq 'Passed' and start ge 2024-01-01"
        
        >>> # With OR conditions
        >>> filter_expr = (ODataFilterBuilder()
        ...     .field("status").eq("Passed")
        ...     .or_group(
        ...         ODataFilterBuilder()
        ...             .field("partNumber").eq("PN-001")
        ...             .field("partNumber").eq("PN-002")
        ...             .use_or()
        ...     )
        ...     .build())
    """
    
    def __init__(self):
        self._conditions: List[str] = []
        self._operator = "and"
        self._current_field: Optional[str] = None
    
    def field(self, name: str) -> "ODataFilterBuilder":
        """Start a condition for the specified field."""
        self._current_field = name
        return self
    
    def eq(self, value: Any) -> "ODataFilterBuilder":
        """Add an equals condition."""
        return self._add_condition("eq", value)
    
    def ne(self, value: Any) -> "ODataFilterBuilder":
        """Add a not-equals condition."""
        return self._add_condition("ne", value)
    
    def gt(self, value: Any) -> "ODataFilterBuilder":
        """Add a greater-than condition."""
        return self._add_condition("gt", value)
    
    def ge(self, value: Any) -> "ODataFilterBuilder":
        """Add a greater-than-or-equal condition."""
        return self._add_condition("ge", value)
    
    def lt(self, value: Any) -> "ODataFilterBuilder":
        """Add a less-than condition."""
        return self._add_condition("lt", value)
    
    def le(self, value: Any) -> "ODataFilterBuilder":
        """Add a less-than-or-equal condition."""
        return self._add_condition("le", value)
    
    def contains(self, value: str) -> "ODataFilterBuilder":
        """Add a contains condition (substring match)."""
        if self._current_field is None:
            raise ValueError("Must call field() before contains()")
        escaped = escape_string(value)
        self._conditions.append(f"contains({self._current_field}, '{escaped}')")
        self._current_field = None
        return self
    
    def startswith(self, value: str) -> "ODataFilterBuilder":
        """Add a startswith condition."""
        if self._current_field is None:
            raise ValueError("Must call field() before startswith()")
        escaped = escape_string(value)
        self._conditions.append(f"startswith({self._current_field}, '{escaped}')")
        self._current_field = None
        return self
    
    def endswith(self, value: str) -> "ODataFilterBuilder":
        """Add an endswith condition."""
        if self._current_field is None:
            raise ValueError("Must call field() before endswith()")
        escaped = escape_string(value)
        self._conditions.append(f"endswith({self._current_field}, '{escaped}')")
        self._current_field = None
        return self
    
    def is_null(self) -> "ODataFilterBuilder":
        """Add a null check condition."""
        if self._current_field is None:
            raise ValueError("Must call field() before is_null()")
        self._conditions.append(f"{self._current_field} eq null")
        self._current_field = None
        return self
    
    def is_not_null(self) -> "ODataFilterBuilder":
        """Add a not-null check condition."""
        if self._current_field is None:
            raise ValueError("Must call field() before is_not_null()")
        self._conditions.append(f"{self._current_field} ne null")
        self._current_field = None
        return self
    
    def in_list(self, values: List[Any]) -> "ODataFilterBuilder":
        """Add an 'in' condition (value in list).
        
        Note: OData doesn't have a native 'in' operator, so this
        generates multiple OR conditions.
        """
        if self._current_field is None:
            raise ValueError("Must call field() before in_list()")
        if not values:
            # Empty list means no match
            self._conditions.append("false")
        else:
            or_parts = [f"{self._current_field} eq {format_value(v)}" for v in values]
            self._conditions.append(f"({' or '.join(or_parts)})")
        self._current_field = None
        return self
    
    def use_or(self) -> "ODataFilterBuilder":
        """Use OR to join conditions (default is AND)."""
        self._operator = "or"
        return self
    
    def use_and(self) -> "ODataFilterBuilder":
        """Use AND to join conditions (this is the default)."""
        self._operator = "and"
        return self
    
    def or_group(self, builder: "ODataFilterBuilder") -> "ODataFilterBuilder":
        """Add a grouped sub-expression."""
        sub_expr = builder.build()
        if sub_expr:
            self._conditions.append(f"({sub_expr})")
        return self
    
    def raw(self, expression: str) -> "ODataFilterBuilder":
        """Add a raw expression (use with caution - not escaped).
        
        Warning: Only use this for trusted expressions, not user input!
        """
        self._conditions.append(expression)
        return self
    
    def _add_condition(self, op: str, value: Any) -> "ODataFilterBuilder":
        """Add a comparison condition."""
        if self._current_field is None:
            raise ValueError(f"Must call field() before {op}()")
        formatted = format_value(value)
        self._conditions.append(f"{self._current_field} {op} {formatted}")
        self._current_field = None
        return self
    
    def build(self) -> str:
        """Build the final filter expression."""
        if not self._conditions:
            return ""
        return f" {self._operator} ".join(self._conditions)
    
    def __str__(self) -> str:
        """Return the filter expression."""
        return self.build()
