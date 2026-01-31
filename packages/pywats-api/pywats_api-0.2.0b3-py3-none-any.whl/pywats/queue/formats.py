"""
WATS Report Format Converters

Supports conversion between various WATS report formats:
- WSJF: WATS JSON Format (standard, used for queueing)
- WSXF: WATS XML Format (older server format)
- WSTF: WATS TestStand Format (TestStand-specific XML)
- ATML: Automatic Test Markup Language (IEEE standard)

All operations are memory-only (string/dict transformations).
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Union


class WSJFConverter:
    """Converter for WSJF (WATS JSON Format)."""
    
    @staticmethod
    def to_wsjf(report_data: Union[Dict[str, Any], object]) -> str:
        """
        Convert report data to WSJF (JSON string).
        
        Args:
            report_data: Report dictionary or pydantic model
            
        Returns:
            JSON string in WSJF format
        """
        # If it's a pydantic model, serialize it
        if hasattr(report_data, 'model_dump_json'):
            return report_data.model_dump_json(by_alias=True, exclude_none=True)
        elif hasattr(report_data, 'dict'):
            # Pydantic v1
            return json.dumps(report_data.dict(by_alias=True, exclude_none=True))
        else:
            # Plain dictionary
            return json.dumps(report_data)
    
    @staticmethod
    def from_wsjf(wsjf_data: str) -> Dict[str, Any]:
        """
        Parse WSJF (JSON string) to dictionary.
        
        Args:
            wsjf_data: JSON string in WSJF format
            
        Returns:
            Report dictionary
        """
        return json.loads(wsjf_data)


def convert_to_wsjf(report_data: Union[Dict[str, Any], object]) -> str:
    """
    Convert any report data to WSJF format.
    
    Args:
        report_data: Report dictionary or pydantic model
        
    Returns:
        JSON string in WSJF format
        
    Example:
        >>> from pywats import pyWATS
        >>> api = pyWATS(...)
        >>> report = api.report.create_uut_report(...)
        >>> wsjf = convert_to_wsjf(report)
        >>> # Save to file or submit
    """
    return WSJFConverter.to_wsjf(report_data)


def convert_from_wsxf(wsxf_data: str) -> Dict[str, Any]:
    """
    Convert WSXF (XML) format to WSJF (JSON).
    
    Args:
        wsxf_data: XML string in WSXF format
        
    Returns:
        Report dictionary in WSJF-compatible format
        
    Note:
        This is a basic converter. For production use, implement
        a custom converter in pywats_client.converters
    """
    # Parse XML
    root = ET.fromstring(wsxf_data)
    
    # Basic structure extraction
    report = {}
    
    # Extract basic fields (simplified - expand as needed)
    for child in root:
        tag = child.tag.replace('{http://www.wats.com/XmlFormats/2009/Report}', '')
        if len(child) == 0:  # Leaf node
            report[tag] = child.text
        # Handle nested elements as needed
    
    return report


def convert_from_wstf(wstf_data: str) -> Dict[str, Any]:
    """
    Convert WSTF (TestStand XML) format to WSJF (JSON).
    
    Args:
        wstf_data: XML string in WSTF format
        
    Returns:
        Report dictionary in WSJF-compatible format
        
    Note:
        This is a basic converter. For production use, implement
        a custom converter in pywats_client.converters
    """
    # Parse TestStand XML
    root = ET.fromstring(wstf_data)
    
    # Basic structure extraction
    report = {}
    
    # Extract TestStand-specific fields
    # This is simplified - actual implementation would need
    # to handle TestStand's complex sequence structure
    
    return report


def convert_from_atml(atml_data: str) -> Dict[str, Any]:
    """
    Convert ATML (Automatic Test Markup Language) to WSJF (JSON).
    
    Args:
        atml_data: XML string in ATML format
        
    Returns:
        Report dictionary in WSJF-compatible format
        
    Note:
        ATML is an IEEE standard (IEEE 1671/1636.1). This function provides
        basic format detection. For full ATML conversion with support for
        ATML 2.02, 5.00, 6.01, and TestStand WATS AddOn extensions, use
        the ATMLConverter from pywats_client.converters.standard:
        
            from pywats_client.converters.standard import ATMLConverter
        
        The ATMLConverter properly handles:
        - All ATML versions (2.02, 5.00, 6.01)
        - TestStand WATS AddOn custom namespaces
        - TSStepProperties (StepType, StepGroup, TotalTime, etc.)
        - TSResultSetProperties (BatchSerialNumber, TestSocketIndex)
        - All limit types (LimitPair, SingleLimit, Expected with thresholds)
        - Complex step hierarchies (TestGroup, SessionAction, Test)
    """
    # Parse ATML XML to verify structure
    root = ET.fromstring(atml_data)
    
    # Detect version from namespace
    version = "unknown"
    root_tag = root.tag
    if "IEEE-1636.1:2013" in root_tag:
        version = "6.01"
    elif "IEEE-1636.1:2011" in root_tag:
        version = "5.00"
    elif "IEEE-1636.1:2006" in root_tag:
        version = "2.02"
    else:
        # Check xmlns attributes
        for attr, value in root.attrib.items():
            if "IEEE-1636.1:2013" in value:
                version = "6.01"
                break
            elif "IEEE-1636.1:2011" in value:
                version = "5.00"
                break
            elif "IEEE-1636.1:2006" in value:
                version = "2.02"
                break
    
    # Return basic structure with detection info
    # Full conversion should use ATMLConverter class
    return {
        "_format": "atml",
        "_version": version,
        "_note": "Use ATMLConverter from pywats_client.converters.standard for full conversion",
    }


def detect_format(data: str) -> str:
    """
    Detect the format of report data.
    
    Args:
        data: Report data as string
        
    Returns:
        Format name: 'wsjf', 'wsxf', 'wstf', 'atml', or 'unknown'
    """
    data_stripped = data.strip()
    
    # Check if JSON (WSJF)
    if data_stripped.startswith('{') or data_stripped.startswith('['):
        try:
            json.loads(data_stripped)
            return 'wsjf'
        except:
            pass
    
    # Check if XML
    if data_stripped.startswith('<'):
        try:
            root = ET.fromstring(data_stripped)
            
            # Check namespace/root tag for format
            if 'wats.com' in (root.tag or ''):
                return 'wsxf'
            elif 'TestStand' in (root.tag or ''):
                return 'wstf'
            elif 'ATML' in (root.tag or '') or '1636' in (root.tag or '') or '1671' in (root.tag or ''):
                return 'atml'
            # Check xmlns for IEEE ATML namespaces
            for attr, value in root.attrib.items():
                if 'IEEE-1636' in value or 'IEEE-1671' in value:
                    return 'atml'
            return 'xml'
        except:
            pass
    
    return 'unknown'


def convert_to_wsjf_auto(data: str) -> str:
    """
    Auto-detect format and convert to WSJF.
    
    Args:
        data: Report data in any supported format
        
    Returns:
        JSON string in WSJF format
        
    Raises:
        ValueError: If format is not supported
    """
    format_type = detect_format(data)
    
    if format_type == 'wsjf':
        return data  # Already in WSJF
    elif format_type == 'wsxf':
        report_dict = convert_from_wsxf(data)
        return json.dumps(report_dict)
    elif format_type == 'wstf':
        report_dict = convert_from_wstf(data)
        return json.dumps(report_dict)
    elif format_type == 'atml':
        report_dict = convert_from_atml(data)
        return json.dumps(report_dict)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
