"""
ATML (IEEE 1671/1636.1) Test Results Converter

Converts IEEE ATML (Automatic Test Markup Language) test result files into WATS reports.
Supports ATML versions 2.02, 5.00, and 6.01, including the TestStand WATS AddOn extensions.

IEEE Standards:
    - IEEE 1671: ATML Framework
    - IEEE 1636.1: Test Results Schema

ATML Versions and Namespaces:
    - ATML 2.02: urn:IEEE-1636.1:2006:TestResults
    - ATML 5.00: urn:IEEE-1636.1:2011:TestResults  
    - ATML 6.01: urn:IEEE-1636.1:2013:TestResults

TestStand WATS AddOn Extension:
    The NI TestStand WATS AddOn adds custom namespace with WATS-specific data:
    - www.ni.com/TestStand/ATMLTestResults/1.0 (ATML 2.02)
    - www.ni.com/TestStand/ATMLTestResults/2.0 (ATML 5.00)
    - www.ni.com/TestStand/ATMLTestResults/3.0 (ATML 6.01)
    
    Extensions include:
    - TSStepProperties: StepType, StepGroup, BlockLevel, Index, TotalTime, ModuleTime
    - TSResultSetProperties: BatchSerialNumber, TestSocketIndex
    - TSLimitProperties: ThresholdType (percentage/ppm/delta), RawLimits

Element Mapping:
    - <tr:TestGroup> -> SequenceCall (with recursive processing)
    - <tr:SessionAction> -> GenericStep (with StepType icon mapping)
    - <tr:Test stepType="PassFailTest"> -> PassFailStep
    - <tr:Test stepType="StringValueTest"> -> StringValueStep  
    - <tr:Test stepType="NumericLimitTest"> -> NumericLimitStep
    - <tr:Test stepType="NI_MultipleNumericLimitTest"> -> Multiple NumericLimitSteps
"""

import re
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
import xml.etree.ElementTree as ET

# pyWATS model imports
from pywats.domains.report.report_models import (
    UUTReport, 
    StepStatus, 
    ReportStatus, 
    SequenceCall,
)
from pywats.domains.report.report_models.uut.steps import CompOp

# Converter infrastructure
from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.context import ConverterContext
from pywats_client.converters.models import (
    ConverterSource,
    ConverterResult,
    ValidationResult,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)


class StepGroup(str, Enum):
    """Step group types for ATML conversion."""
    MAIN = "Main"
    SETUP = "Setup"
    CLEANUP = "Cleanup"


class ATMLVersion(Enum):
    """Supported ATML versions."""
    V2_02 = "2.02"
    V5_00 = "5.00"
    V6_01 = "6.01"
    UNKNOWN = "unknown"


# ATML namespace mappings by version
ATML_NAMESPACES = {
    ATMLVersion.V2_02: {
        "tr": "urn:IEEE-1636.1:2006:TestResults",
        "c": "urn:IEEE-1671:2006:Common",
        "ts": "www.ni.com/TestStand/ATMLTestResults/1.0",
        "trc": "urn:IEEE-1636.1:2006:TestResultsCollection",
    },
    ATMLVersion.V5_00: {
        "tr": "urn:IEEE-1636.1:2011:TestResults",
        "c": "urn:IEEE-1671:2009:Common",
        "ts": "www.ni.com/TestStand/ATMLTestResults/2.0",
        "trc": "urn:IEEE-1636.1:2011:TestResultsCollection",
    },
    ATMLVersion.V6_01: {
        "tr": "urn:IEEE-1636.1:2013:TestResults",
        "c": "urn:IEEE-1671:2010:Common",
        "ts": "www.ni.com/TestStand/ATMLTestResults/3.0",
        "trc": "urn:IEEE-1636.1:2013:TestResultsCollection",
    },
}


# TestStand icon type to step type mapping
ICON_TYPE_MAP = {
    "Label": 0,
    "Action": 1,
    "Goto": 2,
    "NI_FTPFiles": 3,
    "NI_Flow_If": 4,
    "NI_Flow_ElseIf": 5,
    "NI_Flow_Else": 6,
    "NI_Flow_End": 7,
    "NI_Flow_For": 8,
    "NI_Flow_ForEach": 9,
    "NI_Flow_Break": 10,
    "NI_Flow_Continue": 11,
    "NI_Flow_DoWhile": 12,
    "NI_Flow_While": 13,
    "NI_Flow_Select": 14,
    "NI_Flow_Case": 15,
    "NI_Lock": 16,
    "NI_Rendezvous": 17,
    "NI_Queue": 18,
    "NI_Notification": 19,
    "NI_Wait": 20,
    "NI_Batch_Sync": 21,
    "NI_AutoSchedule": 22,
    "NI_UseResource": 23,
    "NI_ThreadPriority": 24,
    "NI_Semaphore": 25,
    "NI_BatchSpec": 26,
    "NI_OpenDatabase": 27,
    "NI_OpenSQLStatement": 28,
    "NI_CloseSQLStatement": 29,
    "NI_CloseDatabase": 30,
    "NI_DataOperation": 31,
    "NI_IVIDmm": 32,
    "NI_IVIScope": 33,
    "NI_IVIFgen": 34,
    "NI_IVIPowerSupply": 35,
    "NI_Switch": 36,
    "NI_IVITools": 37,
    "NI_LV_CheckSystemStatus": 38,
    "NI_LV_RunVIAsynchronously": 39,
}


def _str_to_double(s: str) -> float:
    """
    Convert string to double, handling special values.
    
    Supports:
    - Standard numbers
    - Hex numbers (0x prefix)
    - Infinity variations (+inf, -inf, infinity, etc.)
    - NaN/IND values
    """
    if not s or not s.strip():
        return float('nan')
    
    s = s.strip()
    
    # Handle hex numbers
    if s.lower().startswith("0x"):
        try:
            return float(int(s, 16))
        except ValueError:
            raise ValueError(f"Invalid hex number: {s}")
    
    # Try normal float parsing
    try:
        return float(s)
    except ValueError:
        pass
    
    # Handle special values
    s_lower = s.lower()
    if s_lower in ("infinity", "inf", "+infinity", "+inf", "positiveinfinity"):
        return float('inf')
    elif s_lower in ("-infinity", "-inf", "negativeinfinity"):
        return float('-inf')
    elif s_lower in ("nan", "ind"):
        return float('nan')
    else:
        raise ValueError(f"Invalid double number: {s}")


def _get_step_status(outcome_value: str, qualifier: Optional[str] = None) -> StepStatus:
    """Convert ATML outcome to WATS StepStatus."""
    value = outcome_value.replace("NotStarted", "Skipped")
    
    if value in ("UserDefined", "Aborted") and qualifier:
        value = qualifier
    
    status_map = {
        "Passed": StepStatus.PASSED,
        "Failed": StepStatus.FAILED,
        "Done": StepStatus.DONE,
        "Skipped": StepStatus.SKIPPED,
        "Error": StepStatus.ERROR,
        "Terminated": StepStatus.TERMINATED,
        "Running": StepStatus.RUNNING,
    }
    
    return status_map.get(value, StepStatus.DONE)


def _get_report_status(outcome_value: str, qualifier: Optional[str] = None) -> ReportStatus:
    """Convert ATML outcome to WATS ReportStatus."""
    step_status = _get_step_status(outcome_value, qualifier)
    
    status_map = {
        StepStatus.PASSED: ReportStatus.PASSED,
        StepStatus.FAILED: ReportStatus.FAILED,
        StepStatus.DONE: ReportStatus.DONE,
        StepStatus.SKIPPED: ReportStatus.SKIPPED,
        StepStatus.ERROR: ReportStatus.ERROR,
        StepStatus.TERMINATED: ReportStatus.TERMINATED,
    }
    
    return status_map.get(step_status, ReportStatus.DONE)


def _get_comp_op(comparators: List[str]) -> CompOp:
    """Convert ATML comparator pair to WATS CompOp."""
    # Join comparators if it's a pair
    comp_str = "".join(comparators)
    
    comp_map = {
        "GELE": CompOp.GELE,
        "GELT": CompOp.GELT,
        "GTLE": CompOp.GTLE,
        "GTLT": CompOp.GTLT,
        "GE": CompOp.GE,
        "GT": CompOp.GT,
        "LE": CompOp.LE,
        "LT": CompOp.LT,
        "EQ": CompOp.EQ,
        "NE": CompOp.NE,
        "LOG": CompOp.LOG,
        "CASESENSIT": CompOp.CASESENSIT,
        "IGNORECASE": CompOp.IGNORECASE,
    }
    
    return comp_map.get(comp_str, CompOp.GELE)


def _get_step_group(group_value: str) -> StepGroup:
    """Convert ATML step group to WATS StepGroup."""
    group_map = {
        "Main": StepGroup.MAIN,
        "Setup": StepGroup.SETUP,
        "Cleanup": StepGroup.CLEANUP,
    }
    return group_map.get(group_value, StepGroup.MAIN)


class ATMLConverter(FileConverter):
    """
    Converts IEEE ATML test result files to WATS reports.
    
    Supports:
    - ATML 2.02 (IEEE 1636.1:2006)
    - ATML 5.00 (IEEE 1636.1:2011)
    - ATML 6.01 (IEEE 1636.1:2013)
    - TestStand WATS AddOn extensions
    
    File qualification:
    - File extension must be .xml
    - Root element must be TestResultsCollection or TestResults
    - Must contain IEEE-1636.1 namespace
    """
    
    def __init__(self):
        super().__init__()
        self._version: ATMLVersion = ATMLVersion.UNKNOWN
        self._ns: Dict[str, str] = {}
        self._root: Optional[ET.Element] = None
    
    @property
    def name(self) -> str:
        return "ATML Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return (
            "Converts IEEE ATML (IEEE 1671/1636.1) test result files into WATS reports. "
            "Supports ATML 2.02, 5.00, and 6.01 including TestStand WATS AddOn extensions."
        )
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml", "*.atml"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="10",
                description="Default operation type code if not in file",
            ),
            "partNumber": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="",
                description="Default part number if not in file",
            ),
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Default part revision if not in file",
            ),
            "sequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Default sequence version if not in file",
            ),
            "operator": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="",
                description="Default operator if not in file",
            ),
        }
    
    def _detect_version(self, root: ET.Element) -> ATMLVersion:
        """Detect ATML version from XML namespaces."""
        # Get namespaces from root element
        root_tag = root.tag
        
        # Check namespace in tag
        if "IEEE-1636.1:2013" in root_tag:
            return ATMLVersion.V6_01
        elif "IEEE-1636.1:2011" in root_tag:
            return ATMLVersion.V5_00
        elif "IEEE-1636.1:2006" in root_tag:
            return ATMLVersion.V2_02
        
        # Check xmlns attributes
        for attr, value in root.attrib.items():
            if "IEEE-1636.1:2013" in value:
                return ATMLVersion.V6_01
            elif "IEEE-1636.1:2011" in value:
                return ATMLVersion.V5_00
            elif "IEEE-1636.1:2006" in value:
                return ATMLVersion.V2_02
        
        return ATMLVersion.UNKNOWN
    
    def _setup_namespaces(self, version: ATMLVersion) -> Dict[str, str]:
        """Get namespace dict for the detected ATML version."""
        if version in ATML_NAMESPACES:
            return ATML_NAMESPACES[version]
        
        # Fallback to 6.01 namespaces as default
        return ATML_NAMESPACES[ATMLVersion.V6_01]
    
    def _find(self, element: ET.Element, path: str) -> Optional[ET.Element]:
        """Find element with namespace-aware path."""
        # Replace namespace prefixes with actual URIs
        xpath = path
        for prefix, uri in self._ns.items():
            xpath = xpath.replace(f"{prefix}:", f"{{{uri}}}")
        return element.find(xpath)
    
    def _findall(self, element: ET.Element, path: str) -> List[ET.Element]:
        """Find all elements with namespace-aware path."""
        xpath = path
        for prefix, uri in self._ns.items():
            xpath = xpath.replace(f"{prefix}:", f"{{{uri}}}")
        return element.findall(xpath)
    
    def _get_attr(self, element: ET.Element, attr: str, default: str = "") -> str:
        """Get attribute value with default."""
        return element.get(attr, default) if element is not None else default
    
    def _get_text(self, element: Optional[ET.Element], default: str = "") -> str:
        """Get element text with default."""
        return element.text if element is not None and element.text else default
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """Validate that the file is a properly formatted ATML file."""
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix not in ('.xml', '.atml'):
            return ValidationResult.no_match("Not an XML/ATML file")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Detect ATML version
            version = self._detect_version(root)
            if version == ATMLVersion.UNKNOWN:
                # Check if it might still be ATML by looking for common elements
                root_tag_local = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                if root_tag_local not in ('TestResultsCollection', 'TestResults'):
                    return ValidationResult.no_match(
                        f"XML file but root is '{root_tag_local}', not ATML"
                    )
                # Might be ATML without standard namespace
                version = ATMLVersion.V6_01  # Assume latest
            
            self._version = version
            self._ns = self._setup_namespaces(version)
            self._root = root
            
            # Find TestResults element
            test_results = self._find(root, "trc:TestResults")
            if test_results is None:
                # Try direct TestResults root
                root_tag_local = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                if root_tag_local == "TestResults":
                    test_results = root
                else:
                    return ValidationResult(
                        can_convert=True,
                        confidence=0.3,
                        message=f"ATML {version.value} but cannot find TestResults element"
                    )
            
            # Extract preview info
            serial_number = ""
            part_number = ""
            result_str = "Unknown"
            
            # Try to get UUT info
            uut = self._find(test_results, "tr:UUT")
            if uut is not None:
                serial_el = self._find(uut, "c:SerialNumber")
                serial_number = self._get_text(serial_el)
                
                definition = self._find(uut, "c:Definition")
                if definition is not None:
                    ident = self._find(definition, "c:Identification")
                    if ident is not None:
                        id_numbers = self._find(ident, "c:IdentificationNumbers")
                        if id_numbers is not None:
                            id_num = self._find(id_numbers, "c:IdentificationNumber")
                            part_number = self._get_attr(id_num, "number")
            
            # Get outcome
            result_set = self._find(test_results, "tr:ResultSet")
            if result_set is not None:
                outcome = self._find(result_set, "tr:Outcome")
                if outcome is not None:
                    outcome_value = self._get_attr(outcome, "value")
                    result_str = "Passed" if outcome_value == "Passed" else "Failed"
            
            return ValidationResult(
                can_convert=True,
                confidence=0.9,
                message=f"Valid ATML {version.value} file",
                detected_serial_number=serial_number or None,
                detected_part_number=part_number or None,
                detected_result=result_str,
            )
            
        except ET.ParseError as e:
            return ValidationResult.no_match(f"Invalid XML: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert ATML test file to WATS UUTReport."""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Detect version and setup namespaces
            self._version = self._detect_version(root)
            if self._version == ATMLVersion.UNKNOWN:
                self._version = ATMLVersion.V6_01  # Default to latest
            
            self._ns = self._setup_namespaces(self._version)
            self._root = root
            
            # Get arguments
            default_op_code = context.get_argument("operationTypeCode", "10")
            default_part = context.get_argument("partNumber", "")
            default_revision = context.get_argument("partRevision", "1.0")
            default_seq_version = context.get_argument("sequenceVersion", "1.0")
            default_operator = context.get_argument("operator", "")
            
            # Find TestResults element(s)
            test_results_list = self._findall(root, "trc:TestResults")
            if not test_results_list:
                # Try direct TestResults root
                root_tag_local = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                if root_tag_local == "TestResults":
                    test_results_list = [root]
                else:
                    return ConverterResult.failed_result(
                        error="No TestResults element found in ATML file"
                    )
            
            reports = []
            
            for test_results in test_results_list:
                report = self._create_report_from_test_results(
                    test_results,
                    default_op_code,
                    default_part,
                    default_revision,
                    default_seq_version,
                    default_operator,
                )
                if report:
                    reports.append(report)
            
            if not reports:
                return ConverterResult.failed_result(
                    error="Failed to create any reports from ATML file"
                )
            
            # Return single report or list
            if len(reports) == 1:
                return ConverterResult.success_result(
                    report=reports[0],
                    post_action=PostProcessAction.MOVE,
                    metadata={
                        "atml_version": self._version.value,
                        "reports_created": 1,
                    }
                )
            else:
                return ConverterResult.success_result(
                    report=reports,
                    post_action=PostProcessAction.MOVE,
                    metadata={
                        "atml_version": self._version.value,
                        "reports_created": len(reports),
                    }
                )
        
        except ET.ParseError as e:
            return ConverterResult.failed_result(error=f"XML parse error: {e}")
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _create_report_from_test_results(
        self,
        test_results: ET.Element,
        default_op_code: str,
        default_part: str,
        default_revision: str,
        default_seq_version: str,
        default_operator: str,
    ) -> Optional[UUTReport]:
        """Create a UUTReport from a TestResults element."""
        
        # Extract UUT information
        uut = self._find(test_results, "tr:UUT")
        if uut is None:
            return None
        
        # Get serial number
        serial_el = self._find(uut, "c:SerialNumber")
        serial_number = self._get_text(serial_el, "NA")
        
        # Get part number from UUT Definition
        part_number = default_part
        part_revision = default_revision
        
        definition = self._find(uut, "c:Definition")
        if definition is not None:
            ident = self._find(definition, "c:Identification")
            if ident is not None:
                id_numbers = self._find(ident, "c:IdentificationNumbers")
                if id_numbers is not None:
                    id_num = self._find(id_numbers, "c:IdentificationNumber")
                    if id_num is not None:
                        part_number = self._get_attr(id_num, "number", default_part)
        
        # Get operator from Personnel
        personnel = self._find(test_results, "tr:Personnel")
        operator = default_operator
        if personnel is not None:
            sys_operator = self._find(personnel, "tr:SystemOperator")
            if sys_operator is not None:
                operator = self._get_attr(sys_operator, "name") or self._get_attr(sys_operator, "ID", default_operator)
        
        # Get sequence name from ResultSet
        result_set = self._find(test_results, "tr:ResultSet")
        if result_set is None:
            return None
        
        sequence_name = self._get_attr(result_set, "name", "Unknown")
        
        # Parse dates
        start_str = self._get_attr(result_set, "startDateTime")
        end_str = self._get_attr(result_set, "endDateTime")
        
        start_time = self._parse_datetime(start_str)
        end_time = self._parse_datetime(end_str)
        
        # Get station name
        test_station = self._find(test_results, "tr:TestStation")
        station_name = "Unknown"
        if test_station is not None:
            serial_el = self._find(test_station, "c:SerialNumber")
            station_name = self._get_text(serial_el, "Unknown")
        
        # Get overall outcome
        outcome = self._find(result_set, "tr:Outcome")
        outcome_value = self._get_attr(outcome, "value", "Done")
        outcome_qualifier = self._get_attr(outcome, "qualifier")
        report_status = _get_report_status(outcome_value, outcome_qualifier)
        
        # Create the report
        report = UUTReport(
            operator=operator,
            part_number=part_number,
            part_revision=part_revision,
            serial_number=serial_number,
            operation_type_code=default_op_code,
            sequence_name=sequence_name,
            sequence_version=default_seq_version,
        )
        
        report.start_time = start_time
        if start_time and end_time:
            report.execution_time = (end_time - start_time).total_seconds()
        
        report.station_name = station_name
        report.status = report_status
        
        # Process additional data from UUT Definition Extension
        self._process_additional_data(definition, report)
        
        # Process all child elements (steps)
        self._process_elements(result_set, report, report)
        
        # Check for batch serial number in ResultSet Extension
        self._process_result_set_extension(result_set, report)
        
        return report
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse ATML datetime string."""
        if not dt_str:
            return None
        
        # Try various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                # Handle variable fractional seconds
                if '.' in dt_str:
                    # Normalize to 6 decimal places
                    parts = dt_str.split('.')
                    if len(parts) == 2:
                        frac = parts[1][:6].ljust(6, '0')
                        dt_str = f"{parts[0]}.{frac}"
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _process_additional_data(self, definition: Optional[ET.Element], report: UUTReport) -> None:
        """Process AdditionalData from UUT Definition Extension."""
        if definition is None:
            return
        
        extension = self._find(definition, "c:Extension")
        if extension is None:
            return
        
        ts_collection = self._find(extension, "ts:TSCollection")
        if ts_collection is None:
            return
        
        # Find AdditionalData item
        for item in ts_collection:
            name_attr = item.get("name", "")
            if name_attr == "AdditionalData":
                collection = self._find(item, "c:Collection")
                if collection is not None:
                    for addit in collection:
                        self._add_additional_data_item(addit, report)
    
    def _add_additional_data_item(self, item: ET.Element, report: UUTReport) -> None:
        """Add a single additional data item to the report."""
        name = item.get("name", "").strip()
        if not name:
            return
        
        # Check for nested collection (e.g., Manufacturer.Name)
        nested_collection = self._find(item, "c:Collection")
        if nested_collection is not None:
            nested_item = self._find(nested_collection, "c:Item")
            if nested_item is not None:
                nested_name = nested_item.get("name", "").strip()
                if nested_name:
                    name = f"{name}.{nested_name}"
        
        value = (item.text or "").strip()
        
        if name and value:
            report.add_misc_info(name, value)
    
    def _process_result_set_extension(self, result_set: ET.Element, report: UUTReport) -> None:
        """Process ResultSet Extension for batch info."""
        extension = self._find(result_set, "tr:Extension")
        if extension is None:
            return
        
        ts_props = self._find(extension, "ts:TSResultSetProperties")
        if ts_props is None:
            return
        
        # Get batch serial number
        batch_serial = self._find(ts_props, "ts:BatchSerialNumber")
        if batch_serial is not None:
            batch_sn = self._get_text(batch_serial)
            if batch_sn:
                report.batch_serial_number = batch_sn
        
        # Get test socket index
        socket_index = self._find(ts_props, "ts:TestSocketIndex")
        if socket_index is not None:
            socket_val = socket_index.get("value")
            if socket_val:
                try:
                    report.test_socket_index = int(socket_val)
                except ValueError:
                    pass
    
    def _process_elements(
        self,
        parent: ET.Element,
        report: UUTReport,
        current_parent: Union[UUTReport, SequenceCall],
    ) -> None:
        """
        Recursively process child elements (TestGroup, SessionAction, Test).
        """
        for child in parent:
            # Get local tag name (without namespace)
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag == "TestGroup":
                self._process_test_group(child, report, current_parent)
            elif tag == "SessionAction":
                self._process_session_action(child, report, current_parent)
            elif tag == "Test":
                self._process_test(child, report, current_parent)
    
    def _process_test_group(
        self,
        element: ET.Element,
        report: UUTReport,
        current_parent: Union[UUTReport, SequenceCall],
    ) -> None:
        """Process a TestGroup element -> SequenceCall."""
        name = element.get("name", "Unknown")
        caller_name = element.get("callerName", name)
        
        # Get step properties from Extension
        step_group = StepGroup.MAIN
        step_time = None
        module_time = None
        status = StepStatus.DONE
        
        extension = self._find(element, "tr:Extension")
        if extension is not None:
            ts_props = self._find(extension, "ts:TSStepProperties")
            if ts_props is not None:
                group_el = self._find(ts_props, "ts:StepGroup")
                if group_el is not None:
                    step_group = _get_step_group(self._get_text(group_el, "Main"))
                
                time_el = self._find(ts_props, "ts:TotalTime")
                if time_el is not None:
                    try:
                        step_time = float(time_el.get("value", "0"))
                    except ValueError:
                        pass
                
                mod_time_el = self._find(ts_props, "ts:ModuleTime")
                if mod_time_el is not None:
                    try:
                        module_time = float(mod_time_el.get("value", "0"))
                    except ValueError:
                        pass
        
        # Get outcome
        outcome = self._find(element, "tr:Outcome")
        if outcome is not None:
            outcome_value = self._get_attr(outcome, "value", "Done")
            outcome_qualifier = self._get_attr(outcome, "qualifier")
            status = _get_step_status(outcome_value, outcome_qualifier)
        
        # Create sequence call
        seq_call = current_parent.add_sequence_call(caller_name, name)
        seq_call.status = status
        seq_call.step_group = step_group
        
        if step_time is not None:
            seq_call.total_time = step_time
        if module_time is not None:
            seq_call.module_time = module_time
        
        # Recursively process children
        self._process_elements(element, report, seq_call)
    
    def _process_session_action(
        self,
        element: ET.Element,
        report: UUTReport,
        current_parent: Union[UUTReport, SequenceCall],
    ) -> None:
        """Process a SessionAction element -> GenericStep."""
        name = element.get("name", "Unknown")
        
        # Get step properties
        step_type = "Action"
        step_group = StepGroup.MAIN
        step_time = None
        status = StepStatus.DONE
        
        extension = self._find(element, "tr:Extension")
        if extension is not None:
            ts_props = self._find(extension, "ts:TSStepProperties")
            if ts_props is not None:
                type_el = self._find(ts_props, "ts:StepType")
                if type_el is not None:
                    step_type = self._get_text(type_el, "Action")
                
                group_el = self._find(ts_props, "ts:StepGroup")
                if group_el is not None:
                    step_group = _get_step_group(self._get_text(group_el, "Main"))
                
                time_el = self._find(ts_props, "ts:TotalTime")
                if time_el is not None:
                    try:
                        step_time = float(time_el.get("value", "0"))
                    except ValueError:
                        pass
        
        # Get outcome from ActionOutcome
        action_outcome = self._find(element, "tr:ActionOutcome")
        if action_outcome is not None:
            outcome_value = self._get_attr(action_outcome, "value", "Done")
            outcome_qualifier = self._get_attr(action_outcome, "qualifier")
            status = _get_step_status(outcome_value, outcome_qualifier)
        
        # Create generic step
        step = current_parent.add_step(name, "")
        step.status = status
        step.step_group = step_group
        step.step_type = step_type
        
        if step_time is not None:
            step.total_time = step_time
    
    def _process_test(
        self,
        element: ET.Element,
        report: UUTReport,
        current_parent: Union[UUTReport, SequenceCall],
    ) -> None:
        """Process a Test element -> various step types."""
        name = element.get("name", "Unknown")
        
        # Determine step type from Extension
        step_type = "NumericLimitTest"  # Default
        step_group = StepGroup.MAIN
        step_time = None
        status = StepStatus.DONE
        
        extension = self._find(element, "tr:Extension")
        if extension is not None:
            ts_props = self._find(extension, "ts:TSStepProperties")
            if ts_props is not None:
                type_el = self._find(ts_props, "ts:StepType")
                if type_el is not None:
                    step_type = self._get_text(type_el, "NumericLimitTest")
                
                group_el = self._find(ts_props, "ts:StepGroup")
                if group_el is not None:
                    step_group = _get_step_group(self._get_text(group_el, "Main"))
                
                time_el = self._find(ts_props, "ts:TotalTime")
                if time_el is not None:
                    try:
                        step_time = float(time_el.get("value", "0"))
                    except ValueError:
                        pass
        
        # Get outcome
        outcome = self._find(element, "tr:Outcome")
        if outcome is not None:
            outcome_value = self._get_attr(outcome, "value", "Done")
            outcome_qualifier = self._get_attr(outcome, "qualifier")
            status = _get_step_status(outcome_value, outcome_qualifier)
        
        # Process based on step type
        if step_type == "PassFailTest":
            self._add_pass_fail_step(element, current_parent, name, status, step_group, step_time)
        elif step_type == "StringValueTest":
            self._add_string_value_step(element, current_parent, name, status, step_group, step_time)
        elif step_type in ("NumericLimitTest", "NI_MultipleNumericLimitTest"):
            self._add_numeric_limit_step(element, current_parent, name, status, step_group, step_time, step_type)
        else:
            # Default to pass/fail for unknown types
            self._add_pass_fail_step(element, current_parent, name, status, step_group, step_time)
    
    def _add_pass_fail_step(
        self,
        element: ET.Element,
        parent: Union[UUTReport, SequenceCall],
        name: str,
        status: StepStatus,
        step_group: StepGroup,
        step_time: Optional[float],
    ) -> None:
        """Add a PassFailStep."""
        step = parent.add_pass_fail_step(name)
        step.status = status
        step.step_group = step_group
        if step_time is not None:
            step.total_time = step_time
    
    def _add_string_value_step(
        self,
        element: ET.Element,
        parent: Union[UUTReport, SequenceCall],
        name: str,
        status: StepStatus,
        step_group: StepGroup,
        step_time: Optional[float],
    ) -> None:
        """Add a StringValueStep."""
        # Get test result data
        test_result = self._find(element, "tr:TestResult")
        value = ""
        limit = ""
        comp_op = CompOp.LOG
        
        if test_result is not None:
            # Get measured value
            test_data = self._find(test_result, "tr:TestData")
            if test_data is not None:
                datum = self._find(test_data, "c:Datum")
                if datum is not None:
                    value_el = self._find(datum, "c:Value")
                    value = self._get_text(value_el)
            
            # Get limits
            test_limits = self._find(test_result, "tr:TestLimits")
            if test_limits is not None:
                limit, comp_op = self._get_string_limits(test_limits)
        
        step = parent.add_string_value_step(name, value, limit, comp_op)
        step.status = status
        step.step_group = step_group
        if step_time is not None:
            step.total_time = step_time
    
    def _add_numeric_limit_step(
        self,
        element: ET.Element,
        parent: Union[UUTReport, SequenceCall],
        name: str,
        status: StepStatus,
        step_group: StepGroup,
        step_time: Optional[float],
        step_type: str,
    ) -> None:
        """Add NumericLimitStep(s)."""
        # Get all test results
        test_results = self._findall(element, "tr:TestResult")
        
        if not test_results:
            # No test results, just add a basic step
            step = parent.add_numeric_limit_step(name, float('nan'))
            step.status = status
            step.step_group = step_group
            if step_time is not None:
                step.total_time = step_time
            return
        
        is_first = True
        for test_result in test_results:
            # Get measurement name
            result_name = test_result.get("name", "")
            full_name = f"{name}.{result_name}" if result_name else name
            
            # Get measured value
            value = float('nan')
            unit = ""
            
            test_data = self._find(test_result, "tr:TestData")
            if test_data is not None:
                datum = self._find(test_data, "c:Datum")
                if datum is not None:
                    value_str = datum.get("value", "")
                    if value_str:
                        try:
                            value = _str_to_double(value_str)
                        except ValueError:
                            pass
                    unit = datum.get("nonStandardUnit", "") or datum.get("unit", "")
            
            # Get limits
            low = float('nan')
            high = float('nan')
            comp_op = CompOp.LOG
            
            test_limits = self._find(test_result, "tr:TestLimits")
            if test_limits is not None:
                low, high, comp_op = self._get_numeric_limits(test_limits)
            
            # Create the step
            step = parent.add_numeric_limit_step(
                full_name,
                value,
                low_limit=low if not math.isnan(low) else None,
                high_limit=high if not math.isnan(high) else None,
                comp=comp_op,
                unit=unit if unit else None,
            )
            
            # Only set status/timing on first measurement
            if is_first:
                step.status = status
                step.step_group = step_group
                if step_time is not None:
                    step.total_time = step_time
                is_first = False
    
    def _get_numeric_limits(self, test_limits: ET.Element) -> Tuple[float, float, CompOp]:
        """Extract numeric limits from TestLimits element."""
        low = float('nan')
        high = float('nan')
        comp_op = CompOp.GELE
        
        limits = self._find(test_limits, "tr:Limits")
        if limits is None:
            return low, high, comp_op
        
        # Check for LimitPair
        limit_pair = self._find(limits, "c:LimitPair")
        if limit_pair is not None:
            limit_elements = self._findall(limit_pair, "c:Limit")
            if len(limit_elements) >= 2:
                comp1 = limit_elements[0].get("comparator", "GE")
                comp2 = limit_elements[1].get("comparator", "LE")
                comp_op = _get_comp_op([comp1, comp2])
                
                datum1 = self._find(limit_elements[0], "c:Datum")
                datum2 = self._find(limit_elements[1], "c:Datum")
                
                if datum1 is not None:
                    low = _str_to_double(datum1.get("value", ""))
                if datum2 is not None:
                    high = _str_to_double(datum2.get("value", ""))
            
            return low, high, comp_op
        
        # Check for SingleLimit
        single_limit = self._find(limits, "c:SingleLimit")
        if single_limit is not None:
            comp_str = single_limit.get("comparator", "GE")
            comp_op = _get_comp_op([comp_str])
            
            datum = self._find(single_limit, "c:Datum")
            if datum is not None:
                low = _str_to_double(datum.get("value", ""))
            
            return low, high, comp_op
        
        # Check for Expected (with possible threshold processing)
        expected = self._find(limits, "c:Expected")
        if expected is not None:
            # Check for TSLimitProperties with threshold
            extension = self._find(limits, "c:Extension")
            if extension is not None:
                ts_limit_props = self._find(extension, "ts:TSLimitProperties")
                if ts_limit_props is not None:
                    threshold_type = self._find(ts_limit_props, "ts:ThresholdType")
                    if threshold_type is not None:
                        raw_limits = self._find(ts_limit_props, "ts:RawLimits")
                        if raw_limits is not None:
                            return self._process_threshold_limits(
                                threshold_type, raw_limits
                            )
            
            # Simple expected value
            comp_str = expected.get("comparator", "EQ")
            comp_op = _get_comp_op([comp_str])
            
            datum = self._find(expected, "c:Datum")
            if datum is not None:
                low = _str_to_double(datum.get("value", ""))
            
            return low, high, comp_op
        
        return low, high, comp_op
    
    def _process_threshold_limits(
        self,
        threshold_type: ET.Element,
        raw_limits: ET.Element,
    ) -> Tuple[float, float, CompOp]:
        """Process threshold-based limits (percentage, ppm, delta)."""
        threshold_str = self._get_text(threshold_type, "").lower()
        
        nominal_el = self._find(raw_limits, "ts:Nominal")
        low_el = self._find(raw_limits, "ts:Low")
        high_el = self._find(raw_limits, "ts:High")
        
        nominal = _str_to_double(nominal_el.get("value", "0") if nominal_el is not None else "0")
        threshold_low = _str_to_double(low_el.get("value", "nan") if low_el is not None else "nan")
        threshold_high = _str_to_double(high_el.get("value", "nan") if high_el is not None else "nan")
        
        low = float('nan')
        high = float('nan')
        
        if threshold_str == "percentage":
            if not math.isnan(threshold_low):
                low = nominal - (abs(nominal) * threshold_low / 100)
            if not math.isnan(threshold_high):
                high = nominal + (abs(nominal) * threshold_high / 100)
        elif threshold_str == "ppm":
            if not math.isnan(threshold_low):
                low = nominal - (abs(nominal) * threshold_low / 1000000)
            if not math.isnan(threshold_high):
                high = nominal + (abs(nominal) * threshold_high / 1000000)
        elif threshold_str == "delta":
            if not math.isnan(threshold_low):
                low = nominal - threshold_low
            if not math.isnan(threshold_high):
                high = nominal + threshold_high
        
        return low, high, CompOp.GELE
    
    def _get_string_limits(self, test_limits: ET.Element) -> Tuple[str, CompOp]:
        """Extract string limits from TestLimits element."""
        limit = ""
        comp_op = CompOp.LOG
        
        limits = self._find(test_limits, "tr:Limits")
        if limits is None:
            return limit, comp_op
        
        expected = self._find(limits, "c:Expected")
        if expected is not None:
            comp_str = expected.get("comparator", "EQ")
            
            if comp_str == "CIEQ":
                comp_op = CompOp.IGNORECASE
            else:
                comp_op = CompOp.CASESENSIT
            
            datum = self._find(expected, "c:Datum")
            if datum is not None:
                value_el = self._find(datum, "c:Value")
                limit = self._get_text(value_el)
        
        return limit, comp_op
