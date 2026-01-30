"""OData query parameter helpers for Report queries.

This module provides functions for building OData query parameters
used in report API calls. Extracted from async_service.py for improved
testability and reusability.

Example:
    >>> from pywats.domains.report.query_helpers import (
    ...     build_query_params,
    ...     get_expand_fields,
    ...     is_uut_report_type
    ... )
    >>> 
    >>> # Build query parameters
    >>> params = build_query_params(
    ...     odata_filter="serialNumber eq 'SN-001'",
    ...     top=10,
    ...     orderby="start desc"
    ... )
    >>> # Result: {"$filter": "...", "$top": 10, "$orderby": "start desc"}
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from .enums import ReportType


def is_uut_report_type(report_type: Union[ReportType, str]) -> bool:
    """
    Check if report type is UUT.

    Args:
        report_type: ReportType enum or string ("uut"/"uur")

    Returns:
        True if UUT, False if UUR

    Example:
        >>> is_uut_report_type(ReportType.UUT)
        True
        >>> is_uut_report_type("uur")
        False
    """
    if isinstance(report_type, str):
        return report_type.lower() == "uut"
    return report_type == ReportType.UUT


def get_expand_fields(
    is_uut: bool,
    include_subunits: bool = False,
    include_misc_info: bool = False,
    include_assets: bool = False,
    include_attachments: bool = False,
) -> List[str]:
    """
    Get appropriate expand field names based on report type.

    UUT and UUR reports have different field names for sub-units,
    misc info, assets, and attachments.

    Args:
        is_uut: True for UUT reports, False for UUR
        include_subunits: Include sub-units expansion
        include_misc_info: Include misc info expansion
        include_assets: Include assets expansion
        include_attachments: Include attachments expansion

    Returns:
        List of expand field names

    Example:
        >>> get_expand_fields(is_uut=True, include_subunits=True)
        ['subUnits']
        >>> get_expand_fields(is_uut=False, include_subunits=True)
        ['uurSubUnits']
    """
    fields: List[str] = []
    
    if include_subunits:
        fields.append("subUnits" if is_uut else "uurSubUnits")
    
    if include_misc_info:
        fields.append("miscInfo" if is_uut else "uurMiscInfo")
    
    if include_assets:
        fields.append("assets" if is_uut else "uurAssets")
    
    if include_attachments:
        fields.append("attachments" if is_uut else "uurAttachments")
    
    return fields


def build_expand_clause(expand: Optional[List[str]]) -> Optional[str]:
    """
    Build OData $expand clause from list of fields.

    Args:
        expand: List of field names to expand

    Returns:
        Comma-separated expand string, or None if no fields

    Example:
        >>> build_expand_clause(["subUnits", "miscInfo"])
        "subUnits,miscInfo"
        >>> build_expand_clause(None)
        None
    """
    if not expand:
        return None
    return ",".join(expand)


def build_orderby_clause(
    orderby: Optional[str] = None,
    default: str = "start desc"
) -> str:
    """
    Build OData $orderby clause with optional default.

    Args:
        orderby: Sort order string (e.g., "start desc", "partNumber asc")
        default: Default sort order if none specified

    Returns:
        Order by string

    Example:
        >>> build_orderby_clause("partNumber asc")
        "partNumber asc"
        >>> build_orderby_clause(None, default="start desc")
        "start desc"
    """
    return orderby or default


def build_query_params(
    odata_filter: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    orderby: Optional[str] = None,
    expand: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    count: bool = False,
) -> Dict[str, Any]:
    """
    Build complete OData query parameters dictionary.

    This creates a dictionary suitable for passing to HTTP request params.
    Only includes parameters that have values.

    Args:
        odata_filter: OData filter string
        top: Maximum number of results ($top)
        skip: Number of results to skip ($skip)
        orderby: Sort order ($orderby)
        expand: Fields to expand ($expand)
        select: Fields to select ($select)
        count: Include total count ($count)

    Returns:
        Dictionary of query parameters (OData keys prefixed with $)

    Example:
        >>> build_query_params(
        ...     odata_filter="serialNumber eq 'SN-001'",
        ...     top=10,
        ...     orderby="start desc",
        ...     expand=["subUnits"]
        ... )
        {
            "$filter": "serialNumber eq 'SN-001'",
            "$top": 10,
            "$orderby": "start desc",
            "$expand": "subUnits"
        }
    """
    params: Dict[str, Any] = {}
    
    if odata_filter:
        params["$filter"] = odata_filter
    
    if top is not None:
        params["$top"] = top
    
    if skip is not None:
        params["$skip"] = skip
    
    if orderby:
        params["$orderby"] = orderby
    
    if expand:
        params["$expand"] = build_expand_clause(expand)
    
    if select:
        params["$select"] = ",".join(select)
    
    if count:
        params["$count"] = "true"
    
    return params


def format_datetime_for_odata(dt: 'datetime') -> str:
    """
    Format datetime for OData filter.

    Args:
        dt: datetime object (should have timezone info for accuracy)

    Returns:
        ISO 8601 formatted string suitable for OData

    Example:
        >>> from datetime import datetime
        >>> dt = datetime(2026, 1, 26, 14, 30, 0)
        >>> format_datetime_for_odata(dt)
        "2026-01-26T14:30:00Z"
    """
    from datetime import datetime as dt_class
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_default_query_params(
    report_type: Union[ReportType, str] = ReportType.UUT,
    include_subunits: bool = False,
    top: int = 100,
    orderby: str = "start desc"
) -> Dict[str, Any]:
    """
    Get sensible default query parameters for report queries.

    Args:
        report_type: Report type (UUT or UUR)
        include_subunits: Whether to expand sub-units
        top: Default page size
        orderby: Default sort order

    Returns:
        Query parameters dictionary

    Example:
        >>> get_default_query_params(ReportType.UUT, include_subunits=True)
        {"$top": 100, "$orderby": "start desc", "$expand": "subUnits"}
    """
    is_uut = is_uut_report_type(report_type)
    
    expand = None
    if include_subunits:
        expand = get_expand_fields(is_uut, include_subunits=True)
    
    return build_query_params(
        top=top,
        orderby=orderby,
        expand=expand
    )
