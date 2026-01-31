"""
═══════════════════════════════════════════════════════════════════════════════
 PyWATS CONVERTER TEMPLATE - Reference Implementation
═══════════════════════════════════════════════════════════════════════════════

This template demonstrates the CORRECT way to build WATS reports using the
PyWATS UUTReport model API. All converters MUST follow this pattern.

╔═══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  CRITICAL RULE: NO DICTIONARIES FOR REPORT BUILDING!                      ║
║                                                                               ║
║  All converters MUST use the PyWATS UUTReport model with its factory methods. ║
║  If the API is missing a feature, that's an API problem to fix.               ║
║  NO WORKAROUNDS - NO RAW DICTS!                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

CONVERTER ARCHITECTURE OVERVIEW:
--------------------------------
1. FileConverter - Base class providing common functionality
2. ConverterSource - Represents the file(s) being converted  
3. ConverterContext - Provides runtime context (arguments, folders, etc.)
4. ConverterResult - Return value containing UUTReport or error info
5. ValidationResult - Return value from validate() with confidence score

REPORT BUILDING FLOW:
--------------------
1. Create UUTReport with header information (pn, sn, rev, process_code, etc.)
2. Get root sequence: root = report.get_root_sequence_call()
3. Add sub-sequences: seq = root.add_sequence_call(name="GroupName", ...)
4. Add test steps: seq.add_numeric_step(...), seq.add_boolean_step(...), etc.
5. Return ConverterResult.success_result(report=report, ...)

FILE FORMAT (Mock Example):
---------------------------
This template converter processes a mock "Simple Test Format" (.stf) file:

    # Header
    SERIAL: SN12345
    PART: PN-ABC-001
    REVISION: 1.0
    STATION: TestStation01
    OPERATOR: JohnDoe
    START: 2024-01-15T10:30:00
    
    # Test Results (tab-separated)
    # GroupName<TAB>TestName<TAB>Type<TAB>Value<TAB>Unit<TAB>LowLimit<TAB>HighLimit<TAB>Status
    Power Tests	VCC Voltage	NUMERIC	5.02	V	4.5	5.5	PASS
    Power Tests	VDD Voltage	NUMERIC	3.31	V	3.0	3.6	PASS
    Power Tests	Power OK	BOOLEAN	-	-	-	-	PASS
    Calibration	Serial Read	STRING	ABC123	-	-	-	PASS
    Calibration	Offset	MULTI_NUMERIC	1.2,1.3,1.1	mV	0.5	2.0	PASS
    
    # Footer
    RESULT: PASS
    END: 2024-01-15T10:35:00

Author: PyWATS Development Team
Version: 1.0.0
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# REQUIRED IMPORTS - PyWATS Report Model API
# ═══════════════════════════════════════════════════════════════════════════════

# Core report model - This is the main class for building test reports
from pywats.domains.report.report_models import UUTReport

# UUT-specific info (operator, fixture, etc.)
from pywats.domains.report.report_models.uut.uut_info import UUTInfo

# Sequence call - Container for test steps, provides factory methods
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall

# Comparison operators for limit checking
from pywats.shared.enums import CompOp

# Optional: Import step status enum for type hints
from pywats.domains.report.report_models.uut.step import StepStatus

# Misc info for additional metadata
from pywats.domains.report.report_models.misc_info import MiscInfo

# Sub-units for tracking components within the UUT
from pywats.domains.report.report_models.sub_unit import SubUnit

# Chart types for waveform/graph data
from pywats.domains.report.report_models.chart import Chart, ChartSeries, ChartType

# Generic step for flow control steps (if, for, while, etc.)
from pywats.domains.report.report_models.uut.steps.generic_step import FlowType

# ═══════════════════════════════════════════════════════════════════════════════
# REQUIRED IMPORTS - Converter Infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

# Base class for file-based converters
from pywats_client.converters.file_converter import FileConverter

# Context provides arguments, folders, and runtime info
from pywats_client.converters.context import ConverterContext

# Models for converter input/output
from pywats_client.converters.models import (
    ConverterSource,      # Input: file path and metadata
    ConverterResult,      # Output: UUTReport or error
    ValidationResult,     # Output from validate()
    PostProcessAction,    # What to do with file after conversion
    ArgumentDefinition,   # Define configurable arguments
    ArgumentType,         # Argument type enum
)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARISON OPERATOR REFERENCE
# ═══════════════════════════════════════════════════════════════════════════════
#
# CompOp Enum Values (from pywats.domains.report.report_models.uut.steps.comp_operator):
#
#   CompOp.LOG   - Log only (no limits applied)
#   CompOp.EQ    - Equal to limit
#   CompOp.NE    - Not equal to limit  
#   CompOp.LT    - Less than high_limit
#   CompOp.LE    - Less than or equal to high_limit
#   CompOp.GT    - Greater than low_limit
#   CompOp.GE    - Greater than or equal to low_limit
#   CompOp.GELE  - Between limits inclusive (>= low_limit AND <= high_limit) - MOST COMMON
#   CompOp.GTLT  - Between limits exclusive (> low_limit AND < high_limit)
#   CompOp.GELT  - >= low_limit AND < high_limit
#   CompOp.GTLE  - > low_limit AND <= high_limit
#
# ═══════════════════════════════════════════════════════════════════════════════


class ConverterTemplate(FileConverter):
    """
    Template converter demonstrating proper PyWATS report building patterns.
    
    This converter processes mock ".stf" (Simple Test Format) files and
    demonstrates ALL available step types and API patterns.
    
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ AVAILABLE STEP FACTORY METHODS (on SequenceCall):                           │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ add_sequence_call()      - Add nested sequence/group                        │
    │ add_numeric_step()       - Single numeric measurement with limits           │
    │ add_multi_numeric_step() - Multiple measurements in one step               │
    │ add_boolean_step()       - Pass/fail without value                          │
    │ add_string_step()        - String value comparison                          │
    │ add_multi_string_step()  - Multiple string measurements                     │
    │ add_multi_boolean_step() - Multiple boolean measurements                    │
    │ add_chart_step()         - XY chart/waveform data                           │
    │ add_generic_step()       - Flow control steps (if/for/while/action)         │
    └─────────────────────────────────────────────────────────────────────────────┘
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: CONVERTER IDENTITY
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def name(self) -> str:
        """Human-readable name shown in UI and logs"""
        return "Converter Template (Reference Implementation)"
    
    @property
    def version(self) -> str:
        """Semantic version of this converter"""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Detailed description for documentation"""
        return (
            "Reference implementation demonstrating proper PyWATS report building. "
            "Processes Simple Test Format (.stf) files."
        )
    
    @property
    def file_patterns(self) -> List[str]:
        """
        Glob patterns for files this converter handles.
        The file monitor uses these to determine which converter to try.
        """
        return ["*.stf", "test_*.txt"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """
        Define configurable arguments for this converter.
        These can be set in the client configuration and accessed via context.
        
        Available ArgumentTypes:
        - STRING: Text value
        - INTEGER: Whole number
        - FLOAT: Decimal number  
        - BOOLEAN: True/False
        - ENUM: Selection from predefined values
        - PATH: File or directory path
        """
        return {
            "processCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=10,
                description="WATS process/operation code for this test type",
            ),
            "stationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="TemplateStation",
                description="Station name to use if not specified in file",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Production",
                description="Station location (e.g., Production, Lab, Engineering)",
            ),
            "purpose": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Functional Test",
                description="Test purpose description",
            ),
            "defaultOperator": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="operator",
                description="Default operator name if not in file",
            ),
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file can be converted and extract preview information.
        
        This method is called BEFORE convert() to:
        1. Determine if this converter can handle the file (confidence score)
        2. Extract preview information (serial number, part number, result)
        3. Avoid expensive conversion attempts on incompatible files
        
        Confidence Levels:
        - 0.95+: Perfect match, highly confident
        - 0.7-0.9: Good match with most expected fields
        - 0.4-0.7: Possible match, some fields found  
        - 0.1-0.4: Weak match, might work
        - 0.0: Cannot convert this file
        
        Returns:
            ValidationResult with can_convert, confidence, and detected fields
        """
        # Check file exists
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        # Check extension (optional but improves performance)
        valid_extensions = {'.stf', '.txt'}
        if source.path.suffix.lower() not in valid_extensions:
            return ValidationResult.no_match(f"Unsupported extension: {source.path.suffix}")
        
        try:
            # Read file and validate structure
            content = source.path.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            # Look for expected header fields
            has_serial = any(line.startswith('SERIAL:') for line in lines)
            has_part = any(line.startswith('PART:') for line in lines)
            has_result = any(line.startswith('RESULT:') for line in lines)
            has_tests = any('\t' in line and line.split('\t')[0] not in 
                          {'SERIAL:', 'PART:', 'RESULT:', '#'} for line in lines)
            
            if not (has_serial or has_part):
                return ValidationResult.pattern_match(
                    message="File matches pattern but missing header fields"
                )
            
            # Extract preview information
            serial_number = self._extract_field(lines, 'SERIAL:')
            part_number = self._extract_field(lines, 'PART:')
            result_str = self._extract_field(lines, 'RESULT:')
            
            # Calculate confidence
            confidence = 0.3  # Base confidence for matching extension
            if has_serial:
                confidence += 0.2
            if has_part:
                confidence += 0.2
            if has_result:
                confidence += 0.15
            if has_tests:
                confidence += 0.15
            
            return ValidationResult(
                can_convert=True,
                confidence=min(0.95, confidence),
                message=f"Valid STF file with {sum([has_serial, has_part, has_result, has_tests])}/4 expected sections",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result="Passed" if result_str == "PASS" else "Failed" if result_str == "FAIL" else result_str,
            )
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def _extract_field(self, lines: List[str], prefix: str) -> str:
        """Helper to extract a field value from header lines"""
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return ""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: CONVERSION (Main Implementation)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert the source file to a WATS UUTReport.
        
        ┌─────────────────────────────────────────────────────────────────────────┐
        │ CONVERSION WORKFLOW:                                                    │
        │                                                                         │
        │ 1. Parse file content and extract header information                    │
        │ 2. Create UUTReport with header data                                    │
        │ 3. Get root sequence: root = report.get_root_sequence_call()            │
        │ 4. Add test groups as sub-sequences                                     │
        │ 5. Add test steps using factory methods                                 │
        │ 6. Return ConverterResult.success_result(report=report)                 │
        └─────────────────────────────────────────────────────────────────────────┘
        
        Returns:
            ConverterResult containing UUTReport on success, error info on failure
        """
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            # ═══════════════════════════════════════════════════════════════════
            # STEP 1: Parse file content
            # ═══════════════════════════════════════════════════════════════════
            content = source.path.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            
            # Extract header fields
            serial_number = self._extract_field(lines, 'SERIAL:') or "UNKNOWN"
            part_number = self._extract_field(lines, 'PART:') or "UNKNOWN"
            revision = self._extract_field(lines, 'REVISION:') or "1.0"
            station_name = self._extract_field(lines, 'STATION:') or context.get_argument("stationName", "TemplateStation")
            operator = self._extract_field(lines, 'OPERATOR:') or context.get_argument("defaultOperator", "operator")
            result_str = self._extract_field(lines, 'RESULT:') or "FAIL"
            
            # Parse timestamps
            start_str = self._extract_field(lines, 'START:')
            end_str = self._extract_field(lines, 'END:')
            start_time = self._parse_datetime(start_str) or datetime.now().astimezone()
            end_time = self._parse_datetime(end_str)
            
            # Get arguments from context
            process_code = context.get_argument("processCode", 10)
            location = context.get_argument("location", "Production")
            purpose = context.get_argument("purpose", "Functional Test")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2: Create UUTReport
            # ═══════════════════════════════════════════════════════════════════
            #
            # UUTReport Constructor Parameters:
            #   pn: str           - Part number (required)
            #   sn: str           - Serial number (required)
            #   rev: str          - Revision (required)
            #   process_code: int - Operation/process code (required)
            #   station_name: str - Station/machine name (required)
            #   location: str     - Physical location (required)
            #   purpose: str      - Test purpose description (required)
            #   result: str       - "P"=Pass, "F"=Fail, "E"=Error (default "P")
            #   start: datetime   - Test start time with timezone (auto-set if None)
            #
            report = UUTReport(
                pn=part_number,
                sn=serial_number,
                rev=revision,
                process_code=process_code,
                station_name=station_name,
                location=location,
                purpose=purpose,
                result="P" if result_str == "PASS" else "F",
                start=start_time,
            )
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2b: Set additional UUT info (operator, fixture, etc.)
            # ═══════════════════════════════════════════════════════════════════
            report.info = UUTInfo(operator=operator)
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2c: Add misc info (key-value metadata)
            # ═══════════════════════════════════════════════════════════════════
            report.add_misc_info(description="Source File", value=source.path.name)
            report.add_misc_info(description="Converter", value=f"{self.name} v{self.version}")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 2d: Add sub-units (optional - for tracking components)
            # ═══════════════════════════════════════════════════════════════════
            # Example: report.add_sub_unit(part_type="PCB", sn="PCB-001", pn="PCB-123", rev="A")
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 3: Get root sequence call
            # ═══════════════════════════════════════════════════════════════════
            #
            # The root sequence is the top-level container for all test steps.
            # Every UUTReport has exactly one root sequence.
            #
            root = report.get_root_sequence_call()
            root.name = f"{purpose} - {part_number}"
            root.sequence.version = self.version
            root.sequence.file_name = source.path.name
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 4: Build test hierarchy from file content
            # ═══════════════════════════════════════════════════════════════════
            self._build_test_hierarchy(lines, root)
            
            # ═══════════════════════════════════════════════════════════════════
            # STEP 5: Return successful result
            # ═══════════════════════════════════════════════════════════════════
            #
            # PostProcessAction options:
            #   MOVE   - Move file to success folder (recommended)
            #   DELETE - Delete file after conversion
            #   KEEP   - Leave file in place
            #   ZIP    - Compress file after conversion
            #
            return ConverterResult.success_result(
                report=report,  # UUTReport instance - NOT a dictionary!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(
                error=f"Conversion failed: {e}",
                warnings=[f"File: {source.path}"]
            )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: TEST HIERARCHY BUILDING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_test_hierarchy(self, lines: List[str], root: SequenceCall) -> None:
        """
        Build test step hierarchy from parsed file lines.
        
        This demonstrates organizing tests into groups (sequences) and
        adding different step types.
        """
        # Track current group/sequence
        current_group: Optional[SequenceCall] = None
        current_group_name: Optional[str] = None
        
        for line in lines:
            # Skip header lines and comments
            if ':' in line.split('\t')[0] or line.startswith('#') or not line.strip():
                continue
            
            # Parse tab-separated test data
            parts = line.split('\t')
            if len(parts) < 8:
                continue
            
            group_name, test_name, test_type, value, unit, low_limit, high_limit, status = parts[:8]
            
            # Create new group sequence if needed
            if group_name != current_group_name:
                current_group = root.add_sequence_call(
                    name=group_name,
                    file_name=f"{group_name.replace(' ', '_')}.seq",
                    version="1.0"
                )
                current_group_name = group_name
            
            # Add step based on type
            self._add_step(
                sequence=current_group,
                test_name=test_name,
                test_type=test_type,
                value=value,
                unit=unit,
                low_limit=low_limit,
                high_limit=high_limit,
                status=status,
            )
    
    def _add_step(
        self,
        sequence: SequenceCall,
        test_name: str,
        test_type: str,
        value: str,
        unit: str,
        low_limit: str,
        high_limit: str,
        status: str,
    ) -> None:
        """
        Add a test step to the sequence based on test type.
        
        ┌─────────────────────────────────────────────────────────────────────────┐
        │ STEP TYPE REFERENCE:                                                    │
        ├─────────────────────────────────────────────────────────────────────────┤
        │ NUMERIC        - Single numeric measurement with optional limits        │
        │ MULTI_NUMERIC  - Multiple measurements in one step                      │
        │ BOOLEAN        - Pass/fail without a measured value                     │
        │ STRING         - String value comparison                                │
        │ MULTI_STRING   - Multiple string measurements                           │
        │ CHART          - XY waveform/graph data                                 │
        │ ACTION         - Generic action step (no measurement)                   │
        └─────────────────────────────────────────────────────────────────────────┘
        """
        step_status = "P" if status == "PASS" else "F"
        
        # ═══════════════════════════════════════════════════════════════════════
        # NUMERIC STEP - Single measurement with limits
        # ═══════════════════════════════════════════════════════════════════════
        if test_type == "NUMERIC":
            # Parse numeric values
            numeric_value = float(value) if value and value != "-" else 0.0
            low = float(low_limit) if low_limit and low_limit != "-" else None
            high = float(high_limit) if high_limit and high_limit != "-" else None
            
            # Determine comparison operator
            comp_op = CompOp.LOG  # Default: no limits
            if low is not None and high is not None:
                comp_op = CompOp.GELE  # >= low AND <= high
            elif low is not None:
                comp_op = CompOp.GE    # >= low
            elif high is not None:
                comp_op = CompOp.LE    # <= high
            
            sequence.add_numeric_step(
                name=test_name,
                value=numeric_value,
                unit=unit if unit != "-" else "",
                comp_op=comp_op,
                low_limit=low,
                high_limit=high,
                status=step_status,
                # Optional parameters:
                # id="step_001",           # Custom step ID
                # group="M",               # Step group (M=Main, S=Setup, C=Cleanup)
                # error_code=123,          # Error code on failure
                # error_message="...",     # Error message on failure
                # reportText="...",        # Additional text for report
                # tot_time=1.5,            # Step execution time in seconds
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # MULTI-NUMERIC STEP - Multiple measurements in one step
        # ═══════════════════════════════════════════════════════════════════════
        elif test_type == "MULTI_NUMERIC":
            # Parse comma-separated values
            values = [float(v.strip()) for v in value.split(',') if v.strip()]
            low = float(low_limit) if low_limit and low_limit != "-" else None
            high = float(high_limit) if high_limit and high_limit != "-" else None
            
            # Create multi-numeric step
            multi_step = sequence.add_multi_numeric_step(
                name=test_name,
                status=step_status,
            )
            
            # Add individual measurements
            for i, val in enumerate(values):
                meas_status = "P" if (low is None or val >= low) and (high is None or val <= high) else "F"
                multi_step.add_measurement(
                    name=f"Reading {i+1}",
                    value=val,
                    unit=unit if unit != "-" else "",
                    status=meas_status,
                    comp_op=CompOp.GELE if (low is not None and high is not None) else CompOp.LOG,
                    low_limit=low,
                    high_limit=high,
                )
        
        # ═══════════════════════════════════════════════════════════════════════
        # BOOLEAN STEP - Pass/fail without measured value
        # ═══════════════════════════════════════════════════════════════════════
        elif test_type == "BOOLEAN":
            sequence.add_boolean_step(
                name=test_name,
                status=step_status,
                # Optional parameters:
                # report_text="Check completed successfully",
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # STRING STEP - String value comparison
        # ═══════════════════════════════════════════════════════════════════════
        elif test_type == "STRING":
            sequence.add_string_step(
                name=test_name,
                value=value,
                status=step_status,
                comp_op=CompOp.LOG,  # or CompOp.EQ for exact match
                # limit="expected_value",  # For comparison
                # report_text="...",       # Long text goes here
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # CHART STEP - XY Waveform data
        # ═══════════════════════════════════════════════════════════════════════
        elif test_type == "CHART":
            # Example: Create chart with sample data
            series_data = ChartSeries(
                name="Signal",
                x_data=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                y_data=[0.0, 0.5, 1.0, 0.5, 0.0, -0.5],
            )
            
            sequence.add_chart_step(
                name=test_name,
                chart_type=ChartType.XY,  # or LINE, BAR, etc.
                status=step_status,
                label="Waveform Capture",
                x_label="Time",
                x_unit="s",
                y_label="Voltage",
                y_unit="V",
                series=[series_data],
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # ACTION/GENERIC STEP - Flow control or action without measurement
        # ═══════════════════════════════════════════════════════════════════════
        elif test_type == "ACTION":
            sequence.add_generic_step(
                step_type=FlowType.Action,
                name=test_name,
                status=step_status,
            )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _parse_datetime(self, dt_string: str) -> Optional[datetime]:
        """Parse datetime string, return None on failure"""
        if not dt_string:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_string, fmt)
                return dt.astimezone()  # Make timezone-aware
            except ValueError:
                continue
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6: LIFECYCLE HOOKS (Optional)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def on_load(self, context: ConverterContext) -> None:
        """Called when converter is first loaded. Use for initialization."""
        pass
    
    def on_success(
        self, 
        source: ConverterSource, 
        result: ConverterResult, 
        context: ConverterContext
    ) -> None:
        """Called after successful conversion. Use for logging or notifications."""
        pass
    
    def on_failure(
        self, 
        source: ConverterSource, 
        result: ConverterResult, 
        context: ConverterContext
    ) -> None:
        """Called after failed conversion. Use for error handling."""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL EXAMPLE/TEST
# ═══════════════════════════════════════════════════════════════════════════════

def create_sample_file() -> Path:
    """Create a sample .stf file for testing"""
    sample_content = """# Sample Test Format File
SERIAL: SN-TEST-001
PART: PN-DEMO-123
REVISION: 2.0
STATION: DemoStation
OPERATOR: TestOperator
START: 2024-01-15T10:30:00

# Test Results (tab-separated)
Power Tests	VCC Voltage	NUMERIC	5.02	V	4.5	5.5	PASS
Power Tests	VDD Voltage	NUMERIC	3.31	V	3.0	3.6	PASS
Power Tests	Power Good	BOOLEAN	-	-	-	-	PASS
Calibration	Serial Read	STRING	ABC123XYZ	-	-	-	PASS
Calibration	Offset Values	MULTI_NUMERIC	1.2,1.3,1.1,1.25	mV	0.5	2.0	PASS
Verification	Final Check	BOOLEAN	-	-	-	-	PASS

RESULT: PASS
END: 2024-01-15T10:35:00
"""
    sample_path = Path("sample_test.stf")
    sample_path.write_text(sample_content, encoding='utf-8')
    return sample_path


def main():
    """
    Demonstrate converter usage and report generation.
    
    This function shows how to:
    1. Create a converter instance
    2. Validate a source file
    3. Convert to UUTReport
    4. Inspect the generated report
    """
    import json
    
    print("=" * 80)
    print("PyWATS Converter Template - Demo")
    print("=" * 80)
    
    # Create sample file
    sample_path = create_sample_file()
    print(f"\nCreated sample file: {sample_path}")
    
    try:
        # Initialize converter and context
        converter = ConverterTemplate()
        context = ConverterContext(station_name="DemoStation")
        source = ConverterSource.from_file(sample_path)
        
        # Step 1: Validate
        print("\n--- VALIDATION ---")
        validation = converter.validate(source, context)
        print(f"Can convert: {validation.can_convert}")
        print(f"Confidence: {validation.confidence:.2f}")
        print(f"Detected SN: {validation.detected_serial_number}")
        print(f"Detected PN: {validation.detected_part_number}")
        print(f"Detected Result: {validation.detected_result}")
        
        if not validation.can_convert:
            print("Cannot convert file!")
            return
        
        # Step 2: Convert
        print("\n--- CONVERSION ---")
        result = converter.convert(source, context)
        print(f"Status: {result.status}")
        
        if result.report:
            # Step 3: Inspect report
            print("\n--- GENERATED REPORT ---")
            report = result.report
            print(f"Part Number: {report.pn}")
            print(f"Serial Number: {report.sn}")
            print(f"Revision: {report.rev}")
            print(f"Result: {'PASSED' if report.result == 'P' else 'FAILED'}")
            print(f"Station: {report.station_name}")
            
            # Show step hierarchy
            print("\n--- TEST HIERARCHY ---")
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
            
            # Show JSON output (what would be sent to server)
            print("\n--- JSON OUTPUT (truncated) ---")
            json_output = report.model_dump_json(by_alias=True, indent=2, exclude_none=True)
            # Show first 2000 chars
            if len(json_output) > 2000:
                print(json_output[:2000] + "\n... (truncated)")
            else:
                print(json_output)
        else:
            print(f"Error: {result.error}")
    
    finally:
        # Cleanup
        if sample_path.exists():
            sample_path.unlink()
            print(f"\nCleaned up: {sample_path}")


if __name__ == "__main__":
    main()
