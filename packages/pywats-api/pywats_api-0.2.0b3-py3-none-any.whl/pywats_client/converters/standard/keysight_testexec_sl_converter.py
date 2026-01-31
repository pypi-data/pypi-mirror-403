"""
Keysight TestExec SL XML Converter

Converts Keysight TestExec SL (formerly Agilent) functional test result files
into WATS reports using pyWATS UUTReport model.

TestExec SL is a functional test executive widely used for PCB/PCBA functional testing.
It outputs XML result files with test sequences, measurements, and pass/fail results.

Expected XML structure (composite from various TestExec SL versions):
<?xml version="1.0" encoding="UTF-8"?>
<TestResults xmlns="...">
  <Header>
    <ProgramName>TestProgram</ProgramName>
    <StationID>STATION01</StationID>
    <Operator>JohnDoe</Operator>
    <StartTime>2024-01-01T10:00:00</StartTime>
    <EndTime>2024-01-01T10:05:00</EndTime>
  </Header>
  <UUT>
    <SerialNumber>SN12345</SerialNumber>
    <PartNumber>PN67890</PartNumber>
    <Revision>A</Revision>
  </UUT>
  <TestSequence>
    <Test name="VoltageMeasurement" status="pass">
      <Measurement>
        <Name>VCC</Name>
        <Value>5.02</Value>
        <Units>V</Units>
        <LowLimit>4.9</LowLimit>
        <HighLimit>5.1</HighLimit>
      </Measurement>
    </Test>
    <TestGroup name="PowerTests">
      <Test name="CurrentDraw" status="pass">
        <Measurement>...</Measurement>
      </Test>
    </TestGroup>
  </TestSequence>
  <Summary>
    <Status>Pass</Status>
    <Duration>300.5</Duration>
    <TotalTests>42</TotalTests>
    <PassedTests>42</PassedTests>
    <FailedTests>0</FailedTests>
  </Summary>
</TestResults>

Alternative XML structures supported:
- <TestExecResults> as root (older versions)
- <Results> as root (some configurations)
- Various namespace configurations

Reference:
- Keysight TestExec SL Application Note: 5990-4367EN
- Keysight TestExec SL User Manual
"""

import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# pyWATS model imports - REQUIRED
from pywats.domains.report.report_models import UUTReport, StepStatus, ReportStatus, SequenceCall
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


class KeysightTestExecSLConverter(FileConverter):
    """
    Converts Keysight TestExec SL XML test result files to WATS reports.
    
    Supports multiple XML structures from different TestExec SL versions:
    - TestResults (current)
    - TestExecResults (legacy)
    - Results (alternative)
    
    File qualification:
    - File extension must be .xml
    - Root element must be TestResults, TestExecResults, or Results
    - Must contain Header/UUT/TestSequence or equivalent elements
    """
    
    # Possible root elements for TestExec SL files
    ROOT_ELEMENTS = {'testresults', 'testexecresults', 'results', 'testexecsl'}
    
    # Common namespaces used in TestExec SL XML files
    NAMESPACES = {
        '': '',  # No namespace
        'keysight': 'http://www.keysight.com/testexec',
        'agilent': 'http://www.agilent.com/testexec',
    }
    
    @property
    def name(self) -> str:
        return "Keysight TestExec SL Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Keysight TestExec SL functional test XML files to WATS reports"
    
    @property
    def author(self) -> str:
        return "pyWATS Team"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml", "*.txsl"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=20,
                description="Operation type code for WATS (default: 20 = Functional Test)",
            ),
            "defaultStation": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="TestExec SL",
                description="Default station name if not found in XML",
            ),
            "includePassedMeasurements": ArgumentDefinition(
                arg_type=ArgumentType.BOOLEAN,
                default=True,
                description="Include measurements from passed tests",
            ),
            "treatMissingLimitsAsPassFail": ArgumentDefinition(
                arg_type=ArgumentType.BOOLEAN,
                default=True,
                description="Treat tests without limits as pass/fail steps",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """Validate that the file is a properly formatted TestExec SL XML file."""
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix not in ('.xml', '.txsl'):
            return ValidationResult.no_match("Not an XML file")
        
        try:
            # Parse with namespace handling
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Get root tag without namespace
            root_tag = self._strip_namespace(root.tag).lower()
            
            if root_tag not in self.ROOT_ELEMENTS:
                return ValidationResult.no_match(
                    f"XML root element '{root_tag}' not recognized as TestExec SL format"
                )
            
            # Extract namespace from root
            ns = self._get_namespace(root)
            
            # Look for key elements that indicate TestExec SL format
            header = self._find_element(root, ['Header', 'TestHeader', 'FileHeader'], ns)
            uut = self._find_element(root, ['UUT', 'Unit', 'DUT', 'Device'], ns)
            tests = self._find_element(root, ['TestSequence', 'Tests', 'TestResults', 'Sequence'], ns)
            
            confidence = 0.3  # Base confidence for matching root element
            part_number = None
            serial_number = None
            result_str = None
            
            if header is not None:
                confidence += 0.2
            
            if uut is not None:
                confidence += 0.2
                # Try to extract UUT info
                serial_number = self._get_text(uut, ['SerialNumber', 'Serial', 'SN', 'UnitSerial'], ns)
                part_number = self._get_text(uut, ['PartNumber', 'Part', 'PN', 'ProductNumber'], ns)
            
            if tests is not None:
                confidence += 0.2
                # Count tests to verify structure
                test_count = len(tests.findall('.//*'))
                if test_count > 0:
                    confidence += 0.1
            
            # Try to get overall result
            summary = self._find_element(root, ['Summary', 'Result', 'TestSummary'], ns)
            if summary is not None:
                status_text = self._get_text(summary, ['Status', 'Result', 'Outcome'], ns)
                if status_text:
                    result_str = "Passed" if status_text.lower() in ('pass', 'passed', 'p', 'true', '1') else "Failed"
            
            return ValidationResult(
                can_convert=True,
                confidence=min(confidence, 0.95),
                message=f"Valid Keysight TestExec SL XML",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result=result_str,
            )
            
        except ET.ParseError as e:
            return ValidationResult.no_match(f"Invalid XML: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert TestExec SL XML test file to WATS UUTReport"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            ns = self._get_namespace(root)
            
            # Get configuration
            operation_code = context.get_argument("operationTypeCode", 20)
            default_station = context.get_argument("defaultStation", "TestExec SL")
            include_passed = context.get_argument("includePassedMeasurements", True)
            missing_limits_as_pf = context.get_argument("treatMissingLimitsAsPassFail", True)
            
            # Extract header information
            header_info = self._extract_header(root, ns)
            
            # Extract UUT information
            uut_info = self._extract_uut(root, ns)
            
            # Extract summary
            summary_info = self._extract_summary(root, ns)
            
            # Validate required fields
            if not uut_info.get('serial_number'):
                # Try to use filename as serial number
                uut_info['serial_number'] = source.path.stem
            
            if not uut_info.get('part_number'):
                uut_info['part_number'] = header_info.get('program_name', 'Unknown')
            
            # Determine overall result
            overall_result = self._determine_result(summary_info, root, ns)
            
            # Parse timestamps
            start_time, end_time = self._parse_timestamps(header_info, summary_info)
            
            # ========================================
            # BUILD REPORT USING UUTReport MODEL
            # ========================================
            
            report = UUTReport(
                pn=uut_info.get('part_number', 'Unknown'),
                sn=uut_info.get('serial_number', 'Unknown'),
                rev=uut_info.get('revision', '1'),
                process_code=operation_code,
                station_name=header_info.get('station_id') or default_station,
                location=header_info.get('location', 'Production'),
                purpose="Functional Test",
                result="P" if overall_result else "F",
                start=start_time,
            )
            
            # Add misc info
            if header_info.get('operator'):
                report.add_misc_info(description="Operator", value=header_info['operator'])
            if header_info.get('program_name'):
                report.add_misc_info(description="Test Program", value=header_info['program_name'])
            if summary_info.get('total_tests'):
                report.add_misc_info(description="Total Tests", value=str(summary_info['total_tests']))
            if summary_info.get('duration'):
                report.add_misc_info(description="Test Duration (s)", value=str(summary_info['duration']))
            
            # Get root sequence
            root_sequence = report.get_root_sequence_call()
            root_sequence.name = header_info.get('program_name', 'MainSequence')
            if header_info.get('program_version'):
                root_sequence.sequence.version = header_info['program_version']
            
            # Process test sequence
            self._process_test_sequence(
                root=root,
                ns=ns,
                parent_sequence=root_sequence,
                include_passed=include_passed,
                missing_limits_as_pf=missing_limits_as_pf
            )
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    # =========================================================================
    # Helper Methods - Namespace handling
    # =========================================================================
    
    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace prefix from an XML tag"""
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag
    
    def _get_namespace(self, element: ET.Element) -> str:
        """Extract namespace from element tag"""
        if element.tag.startswith('{'):
            return element.tag.split('}')[0] + '}'
        return ''
    
    def _find_element(
        self, 
        parent: ET.Element, 
        names: List[str], 
        ns: str
    ) -> Optional[ET.Element]:
        """Find first matching element from a list of possible names"""
        for name in names:
            # Try with namespace
            elem = parent.find(f'{ns}{name}')
            if elem is not None:
                return elem
            # Try without namespace
            elem = parent.find(name)
            if elem is not None:
                return elem
            # Try case-insensitive search
            for child in parent:
                if self._strip_namespace(child.tag).lower() == name.lower():
                    return child
        return None
    
    def _find_all_elements(
        self, 
        parent: ET.Element, 
        names: List[str], 
        ns: str
    ) -> List[ET.Element]:
        """Find all matching elements from a list of possible names"""
        results = []
        for name in names:
            results.extend(parent.findall(f'{ns}{name}'))
            results.extend(parent.findall(name))
        return results
    
    def _get_text(
        self, 
        parent: ET.Element, 
        names: List[str], 
        ns: str
    ) -> Optional[str]:
        """Get text content from first matching element"""
        elem = self._find_element(parent, names, ns)
        if elem is not None and elem.text:
            return elem.text.strip()
        # Also check attributes
        for name in names:
            attr_name = name.lower()
            if attr_name in parent.attrib:
                return parent.attrib[attr_name]
            # Try original case
            if name in parent.attrib:
                return parent.attrib[name]
        return None
    
    # =========================================================================
    # Helper Methods - Data extraction
    # =========================================================================
    
    def _extract_header(self, root: ET.Element, ns: str) -> Dict[str, Any]:
        """Extract header information from XML"""
        info = {}
        
        header = self._find_element(root, ['Header', 'TestHeader', 'FileHeader'], ns)
        if header is None:
            header = root  # Some formats put header info at root level
        
        info['program_name'] = self._get_text(header, 
            ['ProgramName', 'TestProgram', 'SequenceName', 'Name'], ns)
        info['program_version'] = self._get_text(header, 
            ['ProgramVersion', 'Version', 'SequenceVersion'], ns)
        info['station_id'] = self._get_text(header, 
            ['StationID', 'Station', 'StationName', 'TestStation'], ns)
        info['operator'] = self._get_text(header, 
            ['Operator', 'OperatorID', 'User', 'Technician'], ns)
        info['location'] = self._get_text(header, 
            ['Location', 'Site', 'Facility'], ns)
        info['start_time'] = self._get_text(header, 
            ['StartTime', 'Start', 'TestStart', 'BeginTime'], ns)
        info['end_time'] = self._get_text(header, 
            ['EndTime', 'End', 'TestEnd', 'FinishTime'], ns)
        
        return info
    
    def _extract_uut(self, root: ET.Element, ns: str) -> Dict[str, Any]:
        """Extract UUT information from XML"""
        info = {}
        
        uut = self._find_element(root, ['UUT', 'Unit', 'DUT', 'Device', 'Product'], ns)
        if uut is None:
            uut = root
        
        info['serial_number'] = self._get_text(uut, 
            ['SerialNumber', 'Serial', 'SN', 'UnitSerial', 'UnitID'], ns)
        info['part_number'] = self._get_text(uut, 
            ['PartNumber', 'Part', 'PN', 'ProductNumber', 'Model'], ns)
        info['revision'] = self._get_text(uut, 
            ['Revision', 'Rev', 'Version', 'HWRevision'], ns)
        info['batch'] = self._get_text(uut, 
            ['Batch', 'Lot', 'BatchNumber', 'LotNumber'], ns)
        
        return info
    
    def _extract_summary(self, root: ET.Element, ns: str) -> Dict[str, Any]:
        """Extract summary information from XML"""
        info = {}
        
        summary = self._find_element(root, ['Summary', 'TestSummary', 'Results'], ns)
        if summary is None:
            summary = root
        
        info['status'] = self._get_text(summary, 
            ['Status', 'Result', 'Outcome', 'FinalResult'], ns)
        
        # Parse numeric values
        duration_str = self._get_text(summary, 
            ['Duration', 'TestTime', 'ExecutionTime', 'TotalTime'], ns)
        if duration_str:
            try:
                info['duration'] = float(re.sub(r'[^\d.]', '', duration_str))
            except ValueError:
                pass
        
        total_str = self._get_text(summary, 
            ['TotalTests', 'Total', 'TestCount'], ns)
        if total_str:
            try:
                info['total_tests'] = int(re.sub(r'[^\d]', '', total_str))
            except ValueError:
                pass
        
        passed_str = self._get_text(summary, 
            ['PassedTests', 'Passed', 'PassCount'], ns)
        if passed_str:
            try:
                info['passed_tests'] = int(re.sub(r'[^\d]', '', passed_str))
            except ValueError:
                pass
        
        failed_str = self._get_text(summary, 
            ['FailedTests', 'Failed', 'FailCount'], ns)
        if failed_str:
            try:
                info['failed_tests'] = int(re.sub(r'[^\d]', '', failed_str))
            except ValueError:
                pass
        
        return info
    
    def _determine_result(self, summary: Dict[str, Any], root: ET.Element, ns: str) -> bool:
        """Determine overall pass/fail result"""
        # Check summary status
        status = summary.get('status', '').lower()
        if status in ('pass', 'passed', 'p', 'true', '1', 'ok', 'success'):
            return True
        if status in ('fail', 'failed', 'f', 'false', '0', 'error', 'ng'):
            return False
        
        # Check failed count
        if summary.get('failed_tests', 0) > 0:
            return False
        
        # Check if all tests passed
        total = summary.get('total_tests', 0)
        passed = summary.get('passed_tests', 0)
        if total > 0 and total == passed:
            return True
        
        # Check root element attributes
        root_status = root.attrib.get('status', '').lower()
        if root_status in ('pass', 'passed', 'p', 'true', '1'):
            return True
        if root_status in ('fail', 'failed', 'f', 'false', '0'):
            return False
        
        # Default to passed if no indication of failure
        return True
    
    def _parse_timestamps(
        self, 
        header: Dict[str, Any], 
        summary: Dict[str, Any]
    ) -> Tuple[datetime, Optional[datetime]]:
        """Parse start and end timestamps"""
        start_time = datetime.now()
        end_time = None
        
        # Common timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y%m%d%H%M%S",
        ]
        
        start_str = header.get('start_time')
        if start_str:
            for fmt in formats:
                try:
                    start_time = datetime.strptime(start_str[:len(fmt)+5], fmt)
                    break
                except ValueError:
                    continue
        
        end_str = header.get('end_time')
        if end_str:
            for fmt in formats:
                try:
                    end_time = datetime.strptime(end_str[:len(fmt)+5], fmt)
                    break
                except ValueError:
                    continue
        
        return start_time, end_time
    
    # =========================================================================
    # Helper Methods - Test processing
    # =========================================================================
    
    def _process_test_sequence(
        self,
        root: ET.Element,
        ns: str,
        parent_sequence: SequenceCall,
        include_passed: bool,
        missing_limits_as_pf: bool
    ) -> None:
        """Process the test sequence section of the XML"""
        
        # Find test sequence container
        test_container = self._find_element(
            root, 
            ['TestSequence', 'Tests', 'TestResults', 'Sequence', 'Steps'], 
            ns
        )
        
        if test_container is None:
            test_container = root
        
        # Process all child elements
        for child in test_container:
            tag = self._strip_namespace(child.tag).lower()
            
            if tag in ('test', 'teststep', 'step', 'measurement'):
                self._process_test_element(
                    child, ns, parent_sequence, include_passed, missing_limits_as_pf
                )
            elif tag in ('testgroup', 'group', 'sequence', 'subsection'):
                self._process_test_group(
                    child, ns, parent_sequence, include_passed, missing_limits_as_pf
                )
    
    def _process_test_group(
        self,
        group_elem: ET.Element,
        ns: str,
        parent_sequence: SequenceCall,
        include_passed: bool,
        missing_limits_as_pf: bool
    ) -> None:
        """Process a test group element"""
        
        # Get group name
        group_name = (
            group_elem.attrib.get('name') or 
            group_elem.attrib.get('Name') or
            self._get_text(group_elem, ['Name', 'GroupName', 'Title'], ns) or
            'TestGroup'
        )
        
        # Create sequence for group
        group_sequence = parent_sequence.add_sequence_call(
            name=group_name,
            file_name=f"{group_name}.seq"
        )
        assert isinstance(group_sequence, SequenceCall)
        
        # Process children
        for child in group_elem:
            tag = self._strip_namespace(child.tag).lower()
            
            if tag in ('test', 'teststep', 'step', 'measurement'):
                self._process_test_element(
                    child, ns, group_sequence, include_passed, missing_limits_as_pf
                )
            elif tag in ('testgroup', 'group', 'sequence', 'subsection'):
                self._process_test_group(
                    child, ns, group_sequence, include_passed, missing_limits_as_pf
                )
    
    def _process_test_element(
        self,
        test_elem: ET.Element,
        ns: str,
        parent_sequence: SequenceCall,
        include_passed: bool,
        missing_limits_as_pf: bool
    ) -> None:
        """Process a single test element"""
        
        # Get test name
        test_name = (
            test_elem.attrib.get('name') or 
            test_elem.attrib.get('Name') or
            self._get_text(test_elem, ['Name', 'TestName', 'StepName'], ns) or
            'Test'
        )
        
        # Get status
        status_str = (
            test_elem.attrib.get('status') or 
            test_elem.attrib.get('Status') or
            test_elem.attrib.get('result') or
            self._get_text(test_elem, ['Status', 'Result', 'Outcome'], ns) or
            'pass'
        ).lower()
        
        is_passed = status_str in ('pass', 'passed', 'p', 'true', '1', 'ok')
        
        # Skip passed tests if not including them
        if is_passed and not include_passed:
            return
        
        # Look for measurement data
        measurement = self._find_element(
            test_elem, 
            ['Measurement', 'Measurements', 'Data', 'Value'], 
            ns
        )
        
        # If test element itself has measurement attributes
        if measurement is None:
            measurement = test_elem
        
        # Extract measurement values
        value_str = self._get_text(measurement, ['Value', 'MeasuredValue', 'Result', 'Data'], ns)
        unit = self._get_text(measurement, ['Units', 'Unit', 'MeasurementUnit'], ns) or '?'
        low_limit_str = self._get_text(measurement, ['LowLimit', 'LowerLimit', 'Min', 'LL'], ns)
        high_limit_str = self._get_text(measurement, ['HighLimit', 'UpperLimit', 'Max', 'HL', 'UL'], ns)
        
        # Parse numeric values
        value = self._parse_float(value_str)
        low_limit = self._parse_float(low_limit_str)
        high_limit = self._parse_float(high_limit_str)
        
        # Get step status
        step_status = "P" if is_passed else "F"
        
        # Determine step type based on available data
        has_value = value is not None
        has_limits = low_limit is not None or high_limit is not None
        
        if has_value and has_limits:
            # Numeric limit step
            comp_op = self._determine_comp_op(low_limit, high_limit)
            parent_sequence.add_numeric_step(
                name=test_name,
                value=value,
                unit=unit,
                comp_op=comp_op,
                low_limit=low_limit,
                high_limit=high_limit,
                status=step_status,
            )
        elif has_value and not has_limits:
            if missing_limits_as_pf:
                # Treat as pass/fail
                parent_sequence.add_pass_fail_step(
                    name=test_name,
                    status=step_status,
                )
            else:
                # Numeric step without limits (log value)
                parent_sequence.add_numeric_step(
                    name=test_name,
                    value=value,
                    unit=unit,
                    comp_op=CompOp.LOG,
                    status=step_status,
                )
        else:
            # Pass/fail step (no numeric value)
            parent_sequence.add_pass_fail_step(
                name=test_name,
                status=step_status,
            )
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse a string to float, handling various formats"""
        if value is None:
            return None
        try:
            # Remove non-numeric characters except . - e E
            cleaned = re.sub(r'[^\d.\-eE+]', '', value)
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _determine_comp_op(
        self, 
        low_limit: Optional[float], 
        high_limit: Optional[float]
    ) -> CompOp:
        """Determine comparison operator based on limits"""
        if low_limit is not None and high_limit is not None:
            return CompOp.GELE  # Between limits
        elif low_limit is not None:
            return CompOp.GE    # Greater than or equal
        elif high_limit is not None:
            return CompOp.LE    # Less than or equal
        else:
            return CompOp.LOG   # Log only


# Test code
if __name__ == "__main__":
    import json
    
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<TestResults>
  <Header>
    <ProgramName>FunctionalTest_v2.1</ProgramName>
    <StationID>FCT-STATION-01</StationID>
    <Operator>JohnDoe</Operator>
    <StartTime>2024-01-15T10:30:00</StartTime>
    <EndTime>2024-01-15T10:35:00</EndTime>
  </Header>
  <UUT>
    <SerialNumber>SN123456789</SerialNumber>
    <PartNumber>PCBA-1234</PartNumber>
    <Revision>A2</Revision>
  </UUT>
  <TestSequence>
    <Test name="Power_On" status="pass">
      <Measurement>
        <Name>InitialCurrent</Name>
        <Value>0.125</Value>
        <Units>A</Units>
        <LowLimit>0.05</LowLimit>
        <HighLimit>0.25</HighLimit>
      </Measurement>
    </Test>
    <TestGroup name="VoltageTests">
      <Test name="VCC_Measurement" status="pass">
        <Measurement>
          <Value>5.02</Value>
          <Units>V</Units>
          <LowLimit>4.9</LowLimit>
          <HighLimit>5.1</HighLimit>
        </Measurement>
      </Test>
      <Test name="VDD_Measurement" status="pass">
        <Measurement>
          <Value>3.31</Value>
          <Units>V</Units>
          <LowLimit>3.2</LowLimit>
          <HighLimit>3.4</HighLimit>
        </Measurement>
      </Test>
    </TestGroup>
    <TestGroup name="CommunicationTests">
      <Test name="UART_Loopback" status="pass"/>
      <Test name="SPI_Flash_Test" status="pass"/>
      <Test name="I2C_EEPROM_Test" status="fail"/>
    </TestGroup>
  </TestSequence>
  <Summary>
    <Status>Fail</Status>
    <Duration>285.3</Duration>
    <TotalTests>6</TotalTests>
    <PassedTests>5</PassedTests>
    <FailedTests>1</FailedTests>
  </Summary>
</TestResults>"""
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(sample_xml)
        temp_path = Path(f.name)
    
    try:
        converter = KeysightTestExecSLConverter()
        source = ConverterSource.from_file(temp_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Message: {validation.message}")
        print(f"  Detected: SN={validation.detected_serial_number}, PN={validation.detected_part_number}")
        print(f"  Result: {validation.detected_result}")
        
        # Convert
        result = converter.convert(source, context)
        print(f"\nConversion status: {result.status.value}")
        
        if result.report and isinstance(result.report, UUTReport):
            report = result.report
            print(f"\nGenerated UUTReport:")
            print(f"  Part Number: {report.pn}")
            print(f"  Serial Number: {report.sn}")
            print(f"  Revision: {report.rev}")
            print(f"  Result: {report.result}")
            print(f"  Station: {report.station_name}")
            
            # Serialize to JSON
            report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
            print("\nSerialized Report (summary):")
            print(f"  Root steps: {len(report_dict.get('root', {}).get('steps', []))}")
            
            # Full JSON output
            print("\n" + "="*60)
            print("Full Report JSON:")
            print("="*60)
            print(json.dumps(report_dict, indent=2))
    finally:
        temp_path.unlink()
