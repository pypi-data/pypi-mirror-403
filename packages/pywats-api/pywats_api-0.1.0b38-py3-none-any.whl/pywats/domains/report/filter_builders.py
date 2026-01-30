"""OData filter building utilities for Report queries.

This module provides functions for building OData filter strings
used in report header queries. Extracted from async_service.py
for improved testability and reusability.

Example:
    >>> from pywats.domains.report.filter_builders import (
    ...     build_serial_filter,
    ...     build_date_range_filter,
    ...     combine_filters
    ... )
    >>> 
    >>> # Build individual filters
    >>> serial_filter = build_serial_filter("SN-12345")
    >>> date_filter = build_date_range_filter(start_date, end_date)
    >>> 
    >>> # Combine multiple filters
    >>> combined = combine_filters([serial_filter, date_filter])
    >>> # Result: "serialNumber eq 'SN-12345' and start ge 2026-01-01T00:00:00Z and start le 2026-01-31T23:59:59Z"
"""
from datetime import datetime, timedelta
from typing import Optional, List


def build_serial_filter(serial_number: str) -> str:
    """
    Build OData filter for serial number.

    Args:
        serial_number: Serial number to filter by

    Returns:
        OData filter string

    Example:
        >>> build_serial_filter("SN-12345")
        "serialNumber eq 'SN-12345'"
    """
    return f"serialNumber eq '{serial_number}'"


def build_part_number_filter(part_number: str) -> str:
    """
    Build OData filter for part number.

    Args:
        part_number: Part number to filter by

    Returns:
        OData filter string

    Example:
        >>> build_part_number_filter("PN-001")
        "partNumber eq 'PN-001'"
    """
    return f"partNumber eq '{part_number}'"


def build_date_range_filter(
    start_date: datetime,
    end_date: datetime,
    field_name: str = "start"
) -> str:
    """
    Build OData filter for date range.

    Args:
        start_date: Start of date range
        end_date: End of date range
        field_name: Date field to filter on (default: "start")

    Returns:
        OData filter string

    Example:
        >>> from datetime import datetime
        >>> start = datetime(2026, 1, 1)
        >>> end = datetime(2026, 1, 31, 23, 59, 59)
        >>> build_date_range_filter(start, end)
        "start ge 2026-01-01T00:00:00Z and start le 2026-01-31T23:59:59Z"
    """
    start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{field_name} ge {start_str} and {field_name} le {end_str}"


def build_recent_filter(
    days: int = 7,
    field_name: str = "start"
) -> str:
    """
    Build OData filter for recent reports (last N days).

    Args:
        days: Number of days back to include
        field_name: Date field to filter on (default: "start")

    Returns:
        OData filter string

    Example:
        >>> # Get reports from last 7 days
        >>> build_recent_filter(7)
        "start ge 2026-01-19T... and start le 2026-01-26T..."
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return build_date_range_filter(start_date, end_date, field_name)


def build_today_filter(field_name: str = "start") -> str:
    """
    Build OData filter for today's reports.

    Args:
        field_name: Date field to filter on (default: "start")

    Returns:
        OData filter string
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    return build_date_range_filter(today, tomorrow, field_name)


def build_subunit_part_filter(
    subunit_part_number: str,
    is_uut: bool = True
) -> str:
    """
    Build OData filter for sub-unit part number.

    Args:
        subunit_part_number: Part number of sub-unit to filter by
        is_uut: True for UUT reports, False for UUR reports

    Returns:
        OData filter string with 'any' clause

    Example:
        >>> build_subunit_part_filter("SUB-001", is_uut=True)
        "subUnits/any(s: s/partNumber eq 'SUB-001')"
        >>> build_subunit_part_filter("SUB-001", is_uut=False)
        "uurSubUnits/any(s: s/partNumber eq 'SUB-001')"
    """
    collection = "subUnits" if is_uut else "uurSubUnits"
    return f"{collection}/any(s: s/partNumber eq '{subunit_part_number}')"


def build_subunit_serial_filter(
    subunit_serial_number: str,
    is_uut: bool = True
) -> str:
    """
    Build OData filter for sub-unit serial number.

    Args:
        subunit_serial_number: Serial number of sub-unit to filter by
        is_uut: True for UUT reports, False for UUR reports

    Returns:
        OData filter string with 'any' clause

    Example:
        >>> build_subunit_serial_filter("SN-SUB-001", is_uut=True)
        "subUnits/any(s: s/serialNumber eq 'SN-SUB-001')"
    """
    collection = "subUnits" if is_uut else "uurSubUnits"
    return f"{collection}/any(s: s/serialNumber eq '{subunit_serial_number}')"


def combine_filters(filters: List[Optional[str]], operator: str = "and") -> Optional[str]:
    """
    Combine multiple OData filters with a logical operator.

    Args:
        filters: List of filter strings (None values are ignored)
        operator: Logical operator ("and" or "or")

    Returns:
        Combined filter string, or None if no filters provided

    Example:
        >>> filters = [
        ...     build_serial_filter("SN-001"),
        ...     build_part_number_filter("PN-001"),
        ...     None  # Ignored
        ... ]
        >>> combine_filters(filters)
        "serialNumber eq 'SN-001' and partNumber eq 'PN-001'"
    """
    # Filter out None and empty strings
    valid_filters = [f for f in filters if f]
    
    if not valid_filters:
        return None
    
    if len(valid_filters) == 1:
        return valid_filters[0]
    
    return f" {operator} ".join(valid_filters)


def build_header_filter(
    part_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Optional[str]:
    """
    Build a combined filter for common report header queries.

    This is a convenience function that combines multiple common filters.

    Args:
        part_number: Part number to filter by
        serial_number: Serial number to filter by
        start_date: Start of date range
        end_date: End of date range

    Returns:
        Combined OData filter string, or None if no filters provided

    Example:
        >>> build_header_filter(
        ...     part_number="PN-001",
        ...     serial_number="SN-12345"
        ... )
        "partNumber eq 'PN-001' and serialNumber eq 'SN-12345'"
    """
    filters: List[Optional[str]] = []
    
    if part_number:
        filters.append(build_part_number_filter(part_number))
    
    if serial_number:
        filters.append(build_serial_filter(serial_number))
    
    if start_date and end_date:
        filters.append(build_date_range_filter(start_date, end_date))
    elif start_date:
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        filters.append(f"start ge {start_str}")
    elif end_date:
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        filters.append(f"start le {end_str}")
    
    return combine_filters(filters)
