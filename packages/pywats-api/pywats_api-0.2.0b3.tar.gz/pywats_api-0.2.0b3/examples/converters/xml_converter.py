"""
XML Format Converter V2 (DBAudio Format) - Using UUTReport Model

Converts XML test result files into WATS reports using the pyWATS UUTReport API.

This is the refactored version that uses proper API calls instead of dictionaries.

Port of the C# XMLFormatConverter (DBAudio format).

Expected XML structure:
<test>
    <header>
        <tester>OperatorName</tester>
        <article_number>PartNumber</article_number>
        <sernum>SerialNumber</sernum>
        <test_file>TestFileName</test_file>
        <test_existed>true|false</test_existed>
    </header>
    <meas>
        <name>MeasurementName</name>
        <val>12.5</val>
        <unit>V</unit>
        <in_range>true|false</in_range>
    </meas>
    <curve>
        <name>CurveName</name>
        <unit_x>Hz</unit_x>
        <unit_y>dB</unit_y>
        <points>
            <point><val_x>100</val_x><val_y>-3.2</val_y></point>
            ...
        </points>
    </curve>
</test>
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# pyWATS Report Model API Imports
# ═══════════════════════════════════════════════════════════════════════════════
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.uut_info import UUTInfo
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.shared.enums import CompOp
from pywats.domains.report.report_models.chart import Chart, ChartSeries, ChartType

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


class XMLConverter(FileConverter):
    """
    Converts XML test result files (DBAudio format) to WATS reports using UUTReport model.
    
    This converter demonstrates the proper API-based pattern for:
    1. Creating UUTReport with header info
    2. Adding numeric steps for measurements
    3. Adding chart steps for curve data
    
    File qualification:
    - File extension must be .xml
    - Root element must be 'test'
    - Must contain 'header' element with tester, article_number, sernum
    """
    
    @property
    def name(self) -> str:
        return "XML Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts XML test result files (DBAudio format) into WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Part revision number",
            ),
            "sequenceFileVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="NA",
                description="Sequence file version",
            ),
            "stationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="XMLConverter",
                description="Station name override",
            ),
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=55,
                description="Operation type code",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Production",
                description="Station location",
            ),
            "purpose": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Audio Test",
                description="Test purpose",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a properly formatted XML test file.
        
        Confidence levels:
        - 0.95: Has root 'test' element with header containing all expected fields
        - 0.75: Has 'test' root with partial header
        - 0.4: Valid XML with 'test' root but no header
        - 0.3: Valid XML but different structure
        - 0.0: Not valid XML
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        if source.path.suffix.lower() != '.xml':
            return ValidationResult.no_match("Not an XML file")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Check for 'test' root element
            if root.tag != 'test':
                return ValidationResult.pattern_match(
                    message=f"XML file but root is '{root.tag}', not 'test'"
                )
            
            # Check for header element
            header = root.find('header')
            if header is None:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.4,
                    message="XML test file but missing header element"
                )
            
            # Extract header fields
            tester = self._get_text(header, 'tester')
            article_number = self._get_text(header, 'article_number')
            sernum = self._get_text(header, 'sernum')
            test_file = self._get_text(header, 'test_file')
            test_existed = self._get_text(header, 'test_existed')
            
            # Count found fields
            expected_fields = ['tester', 'article_number', 'sernum', 'test_file']
            found_count = sum(1 for f in expected_fields if self._get_text(header, f))
            
            # Check for measurements or curves
            has_meas = root.find('meas') is not None
            has_curve = root.find('curve') is not None
            
            confidence = 0.4 + (found_count / len(expected_fields)) * 0.4
            if has_meas or has_curve:
                confidence += 0.15
            
            result_str = "Failed" if test_existed == "false" else "Passed"
            
            return ValidationResult(
                can_convert=True,
                confidence=min(0.95, confidence),
                message=f"Valid DBAudio XML ({found_count}/{len(expected_fields)} header fields)",
                detected_serial_number=sernum,
                detected_part_number=article_number,
                detected_result=result_str,
            )
            
        except ET.ParseError as e:
            return ValidationResult.no_match(f"Invalid XML: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert XML test file to WATS UUTReport.
        
        Uses the pyWATS UUTReport model API to build the report properly.
        """
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            xml_test = tree.getroot()
            
            # Get arguments
            part_revision = context.get_argument("partRevision", "1.0")
            seq_version = context.get_argument("sequenceFileVersion", "NA")
            station_name = context.get_argument("stationName", "XMLConverter")
            operation_code = context.get_argument("operationTypeCode", 55)
            location = context.get_argument("location", "Production")
            purpose = context.get_argument("purpose", "Audio Test")
            
            # Read header
            header = xml_test.find('header')
            if header is None:
                return ConverterResult.failed_result(error="Missing header element")
            
            operator = self._get_text(header, 'tester', 'operator')
            part_number = self._get_text(header, 'article_number', 'UNKNOWN')
            serial_number = self._get_text(header, 'sernum', 'UNKNOWN')
            test_file = self._get_text(header, 'test_file', 'AudioTest')
            test_existed = self._get_text(header, 'test_existed', 'true')
            
            # Determine result
            result = "F" if test_existed == "false" else "P"
            
            # Use file modification time as start time
            start_time = datetime.now().astimezone()
            if source.path.exists():
                mtime = source.path.stat().st_mtime
                start_time = datetime.fromtimestamp(mtime).astimezone()
            
            # ═══════════════════════════════════════════════════════════════════
            # Create UUTReport using the API
            # ═══════════════════════════════════════════════════════════════════
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
            
            # Add misc info
            report.add_misc_info(description="Source File", value=source.path.name)
            report.add_misc_info(description="Converter", value=f"{self.name} v{self.version}")
            
            # ═══════════════════════════════════════════════════════════════════
            # Get root sequence and set properties
            # ═══════════════════════════════════════════════════════════════════
            root = report.get_root_sequence_call()
            root.name = test_file or "Audio Test"
            root.sequence.version = seq_version
            root.sequence.file_name = source.path.name
            
            # ═══════════════════════════════════════════════════════════════════
            # Build test hierarchy from measurements and curves
            # ═══════════════════════════════════════════════════════════════════
            self._build_test_hierarchy(xml_test, root)
            
            return ConverterResult.success_result(
                report=report,  # UUTReport instance, NOT dict!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _build_test_hierarchy(self, xml_test: ET.Element, root: SequenceCall) -> None:
        """
        Read all meas and curve elements and add them to the root sequence.
        """
        # Group measurements into a sequence
        meas_elements = xml_test.findall('meas')
        if meas_elements:
            meas_seq = root.add_sequence_call(
                name="Measurements",
                file_name="measurements.seq",
                version="1.0"
            )
            for meas in meas_elements:
                self._add_measurement(meas_seq, meas)
        
        # Group curves into a sequence
        curve_elements = xml_test.findall('curve')
        if curve_elements:
            curve_seq = root.add_sequence_call(
                name="Curves",
                file_name="curves.seq",
                version="1.0"
            )
            for curve in curve_elements:
                self._add_curve(curve_seq, curve)
    
    def _add_measurement(self, sequence: SequenceCall, meas_elem: ET.Element) -> None:
        """
        Add a measurement as a numeric step using the pyWATS API.
        """
        name = self._get_text(meas_elem, 'name', 'Measurement')
        val_str = self._get_text(meas_elem, 'val', '0')
        unit = self._get_text(meas_elem, 'unit', '')
        in_range = self._get_text(meas_elem, 'in_range', 'true')
        
        try:
            value = float(val_str)
        except (ValueError, TypeError):
            value = 0.0
        
        step_status = "P" if in_range == "true" else "F"
        
        # Add numeric step using API (LOG mode since we don't have limits)
        sequence.add_numeric_step(
            name=name,
            value=value,
            unit=unit,
            comp_op=CompOp.LOG,  # No limits in this format
            status=step_status,
        )
    
    def _add_curve(self, sequence: SequenceCall, curve_elem: ET.Element) -> None:
        """
        Add a curve as a chart step with statistics using the pyWATS API.
        
        Creates a chart step with the curve data and adds a multi-numeric
        step with statistics (Avg, Min, Max).
        """
        name = self._get_text(curve_elem, 'name', 'Curve')
        unit_x = self._get_text(curve_elem, 'unit_x', 'X')
        unit_y = self._get_text(curve_elem, 'unit_y', 'Y')
        
        # Read points
        x_values: List[float] = []
        y_values: List[float] = []
        
        points_elem = curve_elem.find('points')
        if points_elem is not None:
            for point in points_elem.findall('point'):
                try:
                    x = float(self._get_text(point, 'val_x', '0'))
                    y = float(self._get_text(point, 'val_y', '0'))
                    x_values.append(x)
                    y_values.append(y)
                except (ValueError, TypeError):
                    continue
        
        if not y_values:
            return
        
        # Calculate statistics
        avg_y = sum(y_values) / len(y_values)
        min_y = min(y_values)
        max_y = max(y_values)
        
        # Create chart series
        series_data = ChartSeries(
            name=name,
            x_data=x_values,
            y_data=y_values,
        )
        
        # Add chart step using API
        sequence.add_chart_step(
            name=f"{name} Chart",
            chart_type=ChartType.XY,
            status="P",
            label=name,
            x_label="X",
            x_unit=unit_x,
            y_label="Y",
            y_unit=unit_y,
            series=[series_data],
        )
        
        # Add multi-numeric step with statistics
        stats_step = sequence.add_multi_numeric_step(
            name=f"{name} Statistics",
            status="P",
        )
        
        stats_step.add_measurement(
            name="Average",
            value=avg_y,
            unit=unit_y,
            status="P",
            comp_op=CompOp.LOG,
        )
        stats_step.add_measurement(
            name="Minimum",
            value=min_y,
            unit=unit_y,
            status="P",
            comp_op=CompOp.LOG,
        )
        stats_step.add_measurement(
            name="Maximum",
            value=max_y,
            unit=unit_y,
            status="P",
            comp_op=CompOp.LOG,
        )
    
    def _get_text(self, parent: ET.Element, tag: str, default: str = '') -> str:
        """Safely get text content of a child element"""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# Test/Demo Code
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import tempfile
    
    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<test>
    <header>
        <tester>JohnDoe</tester>
        <article_number>PN-12345</article_number>
        <sernum>SN-00001</sernum>
        <test_file>AudioTest_v1</test_file>
        <test_existed>true</test_existed>
    </header>
    <meas>
        <name>Output Voltage</name>
        <val>12.45</val>
        <unit>V</unit>
        <in_range>true</in_range>
    </meas>
    <meas>
        <name>Current Draw</name>
        <val>1.52</val>
        <unit>A</unit>
        <in_range>true</in_range>
    </meas>
    <curve>
        <name>Frequency Response</name>
        <unit_x>Hz</unit_x>
        <unit_y>dB</unit_y>
        <points>
            <point><val_x>100</val_x><val_y>-2.1</val_y></point>
            <point><val_x>1000</val_x><val_y>0.0</val_y></point>
            <point><val_x>10000</val_x><val_y>-1.5</val_y></point>
            <point><val_x>20000</val_x><val_y>-3.2</val_y></point>
        </points>
    </curve>
</test>"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(sample_xml)
        temp_path = Path(f.name)
    
    try:
        converter = XMLConverter()
        source = ConverterSource.from_file(temp_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Detected: SN={validation.detected_serial_number}, PN={validation.detected_part_number}")
        
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
        temp_path.unlink()
