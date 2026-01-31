"""
XJ Log Converter V2 (XJTAG JTAG Tester) - Using UUTReport Model

Converts XJTAG log ZIP files to WATS reports using the pyWATS UUTReport API.

This is the refactored version that uses proper API calls instead of dictionaries.

Port of the C# XJLogConverter.

File Format:
    ZIP archive containing:
    - Info.xml with test run count
    - Run N.xml files with individual test results

Each run contains testgroup elements with testfunction elements.
"""

import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# pyWATS Report Model API Imports
# ═══════════════════════════════════════════════════════════════════════════════
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.uut_info import UUTInfo
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.shared.enums import CompOp

# ═══════════════════════════════════════════════════════════════════════════════
# Converter Infrastructure Imports
# ═══════════════════════════════════════════════════════════════════════════════
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


class XJTAGConverter(FileConverter):
    """
    Converts XJTAG log ZIP files to WATS reports using the UUTReport model.
    
    This converter demonstrates the proper API-based pattern for:
    1. Creating UUTReport with header info
    2. Building test hierarchy with sequences and boolean steps
    3. Handling multiple reports from a single source file
    
    File qualification:
    - ZIP file containing Info.xml
    - Info.xml has LogFileInfo/TestRunCount element
    - Run N.xml files with testrun elements
    """
    
    @property
    def name(self) -> str:
        return "XJTAG Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts XJTAG log ZIP files to WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.zip", "*.xjlog"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "partNumber": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="PN",
                description="Part number for the reports",
            ),
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Part revision for the reports",
            ),
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=210,
                description="Operation type code for JTAG tests",
            ),
            "sequenceName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="JTAGSeq1",
                description="Sequence name for the reports",
            ),
            "sequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0.0",
                description="Sequence version for the reports",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Production",
                description="Station location",
            ),
            "purpose": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="JTAG Boundary Scan",
                description="Test purpose",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is an XJTAG log ZIP file.
        
        Checks:
        - File is a valid ZIP archive
        - Contains Info.xml
        - Info.xml has LogFileInfo structure with TestRunCount
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        try:
            with zipfile.ZipFile(source.path, 'r') as zf:
                # Check for Info.xml
                namelist = zf.namelist()
                
                if "Info.xml" not in namelist:
                    return ValidationResult.pattern_match(
                        message="ZIP file doesn't contain Info.xml"
                    )
                
                # Read and parse Info.xml
                with zf.open("Info.xml") as info_file:
                    try:
                        info_xml = ET.parse(info_file)
                        root = info_xml.getroot()
                        
                        # Check for LogFileInfo element
                        log_info = root.find("LogFileInfo") if root.tag != "LogFileInfo" else root
                        if log_info is None and root.tag == "LogFileInfo":
                            log_info = root
                        elif log_info is None:
                            return ValidationResult.pattern_match(
                                message="Info.xml doesn't have LogFileInfo element"
                            )
                        
                        # Get test run count
                        run_count_elem = log_info.find("TestRunCount")
                        if run_count_elem is None or not run_count_elem.text:
                            return ValidationResult.pattern_match(
                                message="Info.xml doesn't have TestRunCount element"
                            )
                        
                        run_count = int(run_count_elem.text)
                        
                        # Verify Run N.xml files exist and try to get serial from first
                        runs_found = 0
                        serial_number = None
                        
                        for i in range(1, run_count + 1):
                            run_filename = f"Run {i}.xml"
                            if run_filename in namelist:
                                runs_found += 1
                                # Try to extract serial from first run
                                if serial_number is None:
                                    try:
                                        with zf.open(run_filename) as run_file:
                                            run_xml = ET.parse(run_file)
                                            serial_elem = run_xml.find(".//serial")
                                            if serial_elem is not None and serial_elem.text:
                                                serial_number = serial_elem.text
                                    except:
                                        pass
                        
                        if runs_found == 0:
                            return ValidationResult.pattern_match(
                                message="ZIP file has no Run N.xml files"
                            )
                        
                        confidence = 0.9 if runs_found == run_count else 0.7
                        
                        return ValidationResult(
                            can_convert=True,
                            confidence=confidence,
                            message=f"Valid XJTAG log with {run_count} test runs ({runs_found} found)",
                            detected_serial_number=serial_number,
                        )
                        
                    except ET.ParseError:
                        return ValidationResult.no_match("Info.xml is not valid XML")
                        
        except zipfile.BadZipFile:
            return ValidationResult.no_match("File is not a valid ZIP archive")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert XJTAG log ZIP file to WATS UUTReport(s).
        
        Uses the pyWATS UUTReport model API to build reports properly.
        
        Note: This may generate multiple reports (one per test run).
        The primary report is returned.
        """
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            reports: List[UUTReport] = []
            
            with zipfile.ZipFile(source.path, 'r') as zf:
                # Read Info.xml to get test run count
                with zf.open("Info.xml") as info_file:
                    info_xml = ET.parse(info_file)
                    root = info_xml.getroot()
                    
                    log_info = root.find("LogFileInfo") if root.tag != "LogFileInfo" else root
                    if log_info is None and root.tag == "LogFileInfo":
                        log_info = root
                    
                    if log_info is None:
                        return ConverterResult.failed_result(
                            error="Info.xml structure is invalid"
                        )
                    
                    run_count_elem = log_info.find("TestRunCount")
                    if run_count_elem is None or not run_count_elem.text:
                        return ConverterResult.failed_result(
                            error="Cannot find TestRunCount in Info.xml"
                        )
                    
                    run_count = int(run_count_elem.text)
                
                # Process each test run
                for i in range(1, run_count + 1):
                    run_filename = f"Run {i}.xml"
                    if run_filename not in zf.namelist():
                        continue
                    
                    with zf.open(run_filename) as run_file:
                        try:
                            run_xml = ET.parse(run_file)
                            report = self._build_report(run_xml, source.path, context)
                            if report:
                                reports.append(report)
                        except ET.ParseError as e:
                            # Log warning but continue with other runs
                            pass
            
            if not reports:
                return ConverterResult.failed_result(
                    error="No valid test runs found in ZIP file"
                )
            
            # Return the first report as primary
            # Additional reports should be submitted via context in production
            return ConverterResult.success_result(
                report=reports[0],  # UUTReport instance, NOT dict!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _build_report(
        self, 
        xml: ET.ElementTree, 
        file_path: Path,
        context: ConverterContext
    ) -> Optional[UUTReport]:
        """
        Build a UUTReport from a Run N.xml document using the pyWATS API.
        """
        test_run = xml.getroot()
        if test_run.tag != "testrun":
            return None
        
        test_run_info = test_run.find("testruninfo")
        if test_run_info is None:
            return None
        
        # Get parameters from context
        part_number = context.get_argument("partNumber", "PN")
        part_revision = context.get_argument("partRevision", "1.0")
        operation_code = context.get_argument("operationTypeCode", 210)
        sequence_name = context.get_argument("sequenceName", "JTAGSeq1")
        sequence_version = context.get_argument("sequenceVersion", "1.0.0")
        location = context.get_argument("location", "Production")
        purpose = context.get_argument("purpose", "JTAG Boundary Scan")
        
        # Get serial number
        serial_elem = test_run_info.find("serial")
        serial_number = serial_elem.text if serial_elem is not None and serial_elem.text else "UNKNOWN"
        
        # Get user/operator
        user_elem = test_run_info.find("user")
        operator = user_elem.text if user_elem is not None and user_elem.text else "operator"
        
        # Get station name from xjlink-name
        station_elem = test_run_info.find("xjlink-name")
        station_name = station_elem.text if station_elem is not None and station_elem.text else "XJTAG-Station"
        
        # Parse start datetime
        start_time = datetime.now().astimezone()
        datetime_attr = test_run.get("datetime")
        if datetime_attr:
            try:
                start_time = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Determine overall result
        result_elem = test_run_info.find("result")
        result = "P"
        if result_elem is not None and result_elem.text:
            result = "P" if result_elem.text == "Passed" else "F"
        
        # ═══════════════════════════════════════════════════════════════════════
        # Create UUTReport using the API
        # ═══════════════════════════════════════════════════════════════════════
        report = UUTReport(
            pn=part_number,
            sn=serial_number,
            rev=part_revision,
            process_code=int(operation_code),
            station_name=station_name,
            location=location,
            purpose=purpose,
            result=result,
            start=start_time,
        )
        
        # Set UUT info with operator
        report.info = UUTInfo(operator=operator)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Add misc info
        # ═══════════════════════════════════════════════════════════════════════
        report.add_misc_info(description="Source File", value=file_path.name)
        report.add_misc_info(description="Converter", value=f"{self.name} v{self.version}")
        
        # Add XJTAG-specific info
        xjlink_serial = test_run_info.find("xjlink-serial")
        if xjlink_serial is not None and xjlink_serial.text:
            report.add_misc_info(description="XJLink Serial", value=xjlink_serial.text)
        
        xjtag_version = test_run_info.find("xjtag-version")
        if xjtag_version is not None and xjtag_version.text:
            report.add_misc_info(description="XJTAG Version", value=xjtag_version.text)
        
        # Add comment from project-description
        desc_elem = test_run_info.find("project-description")
        if desc_elem is not None and desc_elem.text:
            report.add_misc_info(description="Project Description", value=desc_elem.text)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Get root sequence and set properties
        # ═══════════════════════════════════════════════════════════════════════
        root = report.get_root_sequence_call()
        root.name = sequence_name
        root.sequence.version = sequence_version
        root.sequence.file_name = file_path.name
        
        # Get execution time
        time_elem = test_run_info.find("time-taken")
        if time_elem is not None and time_elem.text:
            try:
                exec_time_ms = float(time_elem.text)
                root.tot_time = exec_time_ms / 1000.0
            except ValueError:
                pass
        
        # ═══════════════════════════════════════════════════════════════════════
        # Build test hierarchy from testgroups
        # ═══════════════════════════════════════════════════════════════════════
        self._build_test_hierarchy(test_run, root)
        
        return report
    
    def _build_test_hierarchy(self, test_run: ET.Element, root: SequenceCall) -> None:
        """
        Build test step hierarchy from testgroup elements.
        
        Creates a sequence for each testgroup and boolean steps for testfunctions.
        """
        for test_group in test_run.findall("testgroup"):
            group_name = test_group.get("name", "TestGroup")
            
            # Create sequence for this test group
            group_seq = root.add_sequence_call(
                name=group_name,
                file_name=f"{group_name.replace(' ', '_')}.seq",
                version="1.0"
            )
            
            # Process test functions
            for test_function in test_group.findall("testfunction"):
                self._add_test_function(group_seq, test_function)
    
    def _add_test_function(self, sequence: SequenceCall, test_function: ET.Element) -> None:
        """
        Add a test function as a boolean step using the pyWATS API.
        
        XJTAG test functions are pass/fail tests, so we use add_boolean_step().
        """
        func_name = test_function.get("name", "TestFunction")
        
        result_elem = test_function.find("result")
        if result_elem is None:
            return
        
        result_value = result_elem.get("value", "")
        passed = result_value == "Passed"
        step_status = "P" if passed else "F"
        
        # Get report text from text-output
        report_text = None
        text_output = test_function.find("text-output")
        if text_output is not None and text_output.text:
            report_text = text_output.text
        
        # Get step execution time
        tot_time = None
        time_elem = test_function.find("time-taken")
        if time_elem is not None and time_elem.text:
            try:
                tot_time = float(time_elem.text) / 1000.0  # Convert ms to seconds
            except ValueError:
                pass
        
        # Add boolean step using API
        sequence.add_boolean_step(
            name=func_name,
            status=step_status,
            report_text=report_text,
            tot_time=tot_time,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Test/Demo Code
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import tempfile
    import os
    
    # Create a sample XJTAG log ZIP file
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / "test_log.zip"
    
    info_xml = """<?xml version="1.0"?>
<LogFileInfo>
    <TestRunCount>1</TestRunCount>
</LogFileInfo>
"""
    
    run1_xml = """<?xml version="1.0"?>
<testrun datetime="2024-01-15T10:30:45Z">
    <testruninfo>
        <user>TestOperator</user>
        <serial>SN12345</serial>
        <project-description>Test Project</project-description>
        <xjlink-name>XJTAG-Station-1</xjlink-name>
        <xjlink-serial>XJ001</xjlink-serial>
        <xjtag-version>3.0</xjtag-version>
        <time-taken>5000</time-taken>
        <result>Passed</result>
    </testruninfo>
    <testgroup name="ConnectionTests">
        <testfunction name="JTAG_Chain">
            <result value="Passed"/>
            <text-output>Chain OK: 5 devices found</text-output>
            <time-taken>150</time-taken>
        </testfunction>
        <testfunction name="BSDL_Verify">
            <result value="Passed"/>
            <text-output>All BSDL files verified</text-output>
            <time-taken>250</time-taken>
        </testfunction>
    </testgroup>
    <testgroup name="MemoryTests">
        <testfunction name="RAM_Test">
            <result value="Passed"/>
            <text-output>Memory test passed</text-output>
            <time-taken>1200</time-taken>
        </testfunction>
    </testgroup>
</testrun>
"""
    
    try:
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("Info.xml", info_xml)
            zf.writestr("Run 1.xml", run1_xml)
        
        converter = XJTAGConverter()
        source = ConverterSource.from_file(zip_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Message: {validation.message}")
        print(f"  Detected SN: {validation.detected_serial_number}")
        
        # Convert
        result = converter.convert(source, context)
        print(f"\nConversion status: {result.status.value}")
        
        if result.report:
            report = result.report
            print(f"\n=== Generated UUTReport ===")
            print(f"Part Number: {report.pn}")
            print(f"Serial Number: {report.sn}")
            print(f"Result: {'PASSED' if report.result == 'P' else 'FAILED'}")
            print(f"Station: {report.station_name}")
            
            # Show hierarchy
            print(f"\n=== Test Hierarchy ===")
            root = report.get_root_sequence_call()
            print(f"Root: {root.name}")
            for step in root.steps:
                if hasattr(step, 'steps'):  # It's a sequence
                    print(f"  └─ Sequence: {step.name}")
                    for child in step.steps:
                        step_type = child.step_type if hasattr(child, 'step_type') else 'Unknown'
                        print(f"      └─ {step_type}: {child.name} [{child.status}]")
                else:
                    print(f"  └─ {step.step_type}: {step.name} [{step.status}]")
            
            # Show JSON (truncated)
            print(f"\n=== JSON Output (truncated) ===")
            json_output = report.model_dump_json(by_alias=True, indent=2, exclude_none=True)
            print(json_output[:1500] + "..." if len(json_output) > 1500 else json_output)
            
    finally:
        zip_path.unlink()
        os.rmdir(temp_dir)
