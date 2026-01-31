"""
SPEA Converter V2 (Bitron ICT Format) - Using UUTReport Model

Converts SPEA ICT test result files to WATS reports using the pyWATS UUTReport API.

This is the refactored version that uses proper API calls instead of dictionaries.

Port of the C# SPEAConverter (TextConverterBase).

File Format:
    START header with folder, testplan, product, user, datetime
    LOT line for batch serial number
    SN line for serial number
    ANL/FUNC lines for test measurements
    BOARDRESULT for pass/fail status
    END line with datetime

Component reference prefixes map to component types for grouping.
"""

import re
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
from pywats.domains.report.report_models.uut.steps.generic_step import FlowType

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


class SPEAConverter(FileConverter):
    """
    Converts SPEA ICT test result files to WATS reports using UUTReport model.
    
    This converter demonstrates the proper API-based pattern for building reports:
    1. Create UUTReport with header info
    2. Get root sequence via report.get_root_sequence_call()
    3. Add component-type sequences via root.add_sequence_call()
    4. Add test steps via sequence.add_numeric_step(), add_boolean_step(), etc.
    
    File qualification:
    - Text file with semicolon-delimited data
    - Contains START header line
    - Contains LOT, SN, BOARDRESULT lines
    - Contains ANL or FUNC test lines
    """
    
    # Component type mapping (prefix -> category name)
    COMPONENT_TYPES = {
        "END": "Ignore",
        "RETURN": "Ignore",
        "Start": "Action",
        "Counter": "Action",
        "DISCHARGE": "Action",
        "Close": "Action",
        "Open": "Action",
        "Board": "Action",
        "Components": "Action",
        "End": "Action",
        "Connect": "Action",
        "Sconnect": "Action",
        "Power": "Power",
        "A": "Assembly",
        "AT": "Attenuator or isolator",
        "BR": "Bridge rectifier",
        "BT": "Battery",
        "C": "Capacitor",
        "CS": "Capacitor",
        "CP": "Capacitor",
        "CN": "Capacitor network",
        "CON": "Connector",
        "DSC": "Capacitor",
        "D": "Diode",
        "CR": "Diode",
        "DL": "Delay line",
        "DS": "Display",
        "DZ": "ZenerDiode",
        "F": "Fuse",
        "FB": "Ferrite bead",
        "FD": "Fiducial",
        "FL": "Filter",
        "G": "Generator or oscillator",
        "GL": "Graphical logo",
        "GN": "General network",
        "H": "Hardware",
        "HY": "Circulator or directional coupler",
        "IR": "Infrared diode",
        "ISO": "Isolators",
        "J": "Jack",
        "JP": "Jumper (link)",
        "JSCAN": "JSCAN - ESD check",
        "K": "Relay or contactor",
        "L": "Inductor",
        "LNK": "Link",
        "LS": "Loudspeaker or buzzer",
        "M": "Motor",
        "MK": "Microphone",
        "MP": "Mechanical part",
        "OP": "Opto-isolator",
        "P": "Plug",
        "PS": "Power supply",
        "PTC": "PTC",
        "Q": "Transistor",
        "R": "Resistor",
        "RP": "Resistor",
        "RS": "Resistor",
        "RN": "Resistor network",
        "RT": "Thermistor",
        "RV": "Varistor",
        "S": "Switch",
        "SHO": "Short",
        "SW": "Switch",
        "T": "Transformer",
        "TC": "Thermocouple",
        "TP": "Test point",
        "TUN": "Tuner",
        "U": "Integrated circuit (IC)",
        "V": "Variator",
        "VR": "Voltage regulator",
        "X": "Socket connector",
        "XTAL": "Crystal",
        "Y": "Crystal or oscillator",
        "Z": "Zenerdiode",
    }
    
    @property
    def name(self) -> str:
        return "SPEA Converter (Bitron ICT)"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts SPEA ICT test result files to WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt", "*.log", "*.csv"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=31,
                description="Operation type code for ICT tests",
            ),
            "stationNamePrefix": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="U62P-ICT-0",
                description="Station name prefix",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Production",
                description="Station location",
            ),
            "purpose": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="ICT Test",
                description="Test purpose",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a SPEA ICT test file.
        
        Checks:
        - File starts with START; line
        - Contains LOT; and SN; lines
        - Contains ANL; or FUNC; test lines
        - Contains BOARDRESULT; line
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(8192)  # Read first 8KB
            
            lines = content.split('\n')
            
            has_start = False
            has_lot = False
            has_sn = False
            has_tests = False
            has_result = False
            
            for line in lines:
                line = line.strip()
                if line.startswith("START;"):
                    has_start = True
                elif line.startswith("LOT;"):
                    has_lot = True
                elif line.startswith("SN;"):
                    has_sn = True
                elif line.startswith("ANL;") or line.startswith("FUNC;"):
                    has_tests = True
                elif line.startswith("BOARDRESULT;"):
                    has_result = True
            
            if not has_start:
                return ValidationResult.pattern_match(
                    message="File doesn't start with START; header"
                )
            
            confidence = 0.5
            if has_lot:
                confidence += 0.1
            if has_sn:
                confidence += 0.1
            if has_tests:
                confidence += 0.2
            if has_result:
                confidence += 0.1
            
            # Parse START line for part number
            serial_number = None
            part_number = None
            
            start_pattern = r'^START;(?P<SPEAFolder>[^;]*);(?P<SPEATestplan>[^;]*);(?P<SPEANumber>[^;]*);(?P<Product>[^;]*);(?P<User>[^;]*);(?P<DateTime>.*)'
            for line in lines:
                match = re.match(start_pattern, line.strip())
                if match:
                    part_number = match.group("Product")
                    break
            
            # Get serial number from SN line
            for line in lines:
                if line.strip().startswith("SN;"):
                    serial_number = line.strip()[3:]
                    break
            
            # Get result from BOARDRESULT line
            result_str = None
            for line in lines:
                if line.strip().startswith("BOARDRESULT;"):
                    result_str = line.strip()[12:]
                    break
            
            return ValidationResult(
                can_convert=True,
                confidence=min(0.95, confidence),
                message="Valid SPEA ICT file",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result="Passed" if result_str in ("PASS", "PASSED") else "Failed",
            )
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert SPEA ICT test file to WATS UUTReport.
        
        Uses the pyWATS UUTReport model API to build the report properly.
        """
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            # Read and preprocess file content
            with open(source.path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Preprocess lines (normalize values)
            lines = [self._preprocess_line(line) for line in lines]
            
            # Parse file and build UUTReport
            report = self._build_report(lines, source.path, context)
            
            if not report:
                return ConverterResult.failed_result(error="Failed to parse SPEA file")
            
            return ConverterResult.success_result(
                report=report,  # UUTReport instance, NOT dict!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _preprocess_line(self, line: str) -> str:
        """Preprocess a line to normalize special values"""
        line = line.replace(";-NAN;", ";NaN;")
        line = line.replace(";-1.000000e+10;", ";-inf;")
        line = line.replace(";1.000000e+10;", ";+inf;")
        line = line.replace("BOARDRESULT;NONE", "BOARDRESULT;ERROR")
        line = line.replace("INTERRUPTED", "TERMINATED")
        return line
    
    def _build_report(
        self, 
        lines: List[str], 
        file_path: Path,
        context: ConverterContext
    ) -> Optional[UUTReport]:
        """
        Build UUTReport from SPEA file content using the pyWATS API.
        
        This is the main conversion logic using proper API calls.
        """
        # Get arguments from context
        operation_code = context.get_argument("operationTypeCode", 31)
        station_prefix = context.get_argument("stationNamePrefix", "U62P-ICT-0")
        location = context.get_argument("location", "Production")
        purpose = context.get_argument("purpose", "ICT Test")
        
        # Parsing state
        part_number = "UNKNOWN"
        serial_number = "UNKNOWN"
        batch_serial = ""
        operator = "operator"
        sequence_name = "SPEA ICT"
        station_name = station_prefix
        start_time: Optional[datetime] = None
        end_time: Optional[datetime] = None
        test_socket_index = -1
        result = "P"
        
        # Regex patterns
        start_pattern = re.compile(
            r'^START;(?P<SPEAFolder>[^;]*);(?P<SPEATestplan>[^;]*);(?P<SPEANumber>[^;]*);'
            r'(?P<Product>[^;]*);(?P<User>[^;]*);(?P<DateTime>.*)'
        )
        end_pattern = re.compile(r'^END;(?P<Result>[^;]*);(?P<DateTime>.*)')
        anl_func_pattern = re.compile(
            r'^(?P<Type>ANL|FUNC);(?P<Site>[^;]*);(?P<TaskName>[^;]*);(?P<TaskNumber>[^;]*);'
            r'(?P<TestTask>[^;]*);(?P<Diagnostic>[^;]*);(?P<CompPartNumber>[^;]*);'
            r'(?P<Result>[^;]*);(?P<Measure>[^;]*);(?P<Min>[^;]*);(?P<Max>[^;]*);(?P<Unit>[^;]*)'
        )
        
        # First pass: Extract header information
        for line in lines:
            line = line.strip()
            
            # Parse START line
            match = start_pattern.match(line)
            if match:
                sequence_name = f"{match.group('SPEAFolder')}/{match.group('SPEATestplan')}"
                station_name = f"{station_prefix}{match.group('SPEANumber')}"
                part_number = match.group("Product") or "UNKNOWN"
                operator = match.group("User") or "operator"
                
                # Parse datetime (MM/dd/yyyy;HH:mm:ss)
                dt_str = match.group("DateTime")
                try:
                    start_time = datetime.strptime(dt_str, "%m/%d/%Y;%H:%M:%S")
                except ValueError:
                    try:
                        start_time = datetime.strptime(dt_str, "%d/%m/%Y;%H:%M:%S")
                    except ValueError:
                        start_time = datetime.now()
                continue
            
            # Parse LOT line
            if line.startswith("LOT;"):
                batch_serial = line[4:]
                continue
            
            # Parse SN line
            if line.startswith("SN;"):
                serial_number = line[3:] or "UNKNOWN"
                continue
            
            # Parse BOARDRESULT line
            if line.startswith("BOARDRESULT;"):
                result_str = line[12:]
                if result_str in ("PASS", "PASSED"):
                    result = "P"
                elif result_str == "ERROR":
                    result = "E"
                else:
                    result = "F"
                continue
            
            # Parse END line for execution time
            match = end_pattern.match(line)
            if match:
                dt_str = match.group("DateTime")
                try:
                    end_time = datetime.strptime(dt_str, "%m/%d/%Y;%H:%M:%S")
                except ValueError:
                    try:
                        end_time = datetime.strptime(dt_str, "%d/%m/%Y;%H:%M:%S")
                    except ValueError:
                        pass
                continue
        
        # ═══════════════════════════════════════════════════════════════════════
        # Create UUTReport using the API
        # ═══════════════════════════════════════════════════════════════════════
        if start_time is None:
            start_time = datetime.now()
        
        report = UUTReport(
            pn=part_number,
            sn=serial_number,
            rev="1.0",
            process_code=int(operation_code),
            station_name=station_name,
            location=location,
            purpose=purpose,
            result=result,
            start=start_time.astimezone() if start_time.tzinfo else start_time.astimezone(),
        )
        
        # Set UUT info with operator
        report.info = UUTInfo(operator=operator)
        
        # Add misc info
        report.add_misc_info(description="Source File", value=file_path.name)
        report.add_misc_info(description="Converter", value=f"{self.name} v{self.version}")
        if batch_serial:
            report.add_misc_info(description="Batch Serial", value=batch_serial)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Get root sequence and set properties
        # ═══════════════════════════════════════════════════════════════════════
        root = report.get_root_sequence_call()
        root.name = sequence_name
        root.sequence.version = "1.0.0"
        root.sequence.file_name = file_path.name
        
        # ═══════════════════════════════════════════════════════════════════════
        # Second pass: Build test hierarchy
        # ═══════════════════════════════════════════════════════════════════════
        prev_step_ref = ""
        current_sequence: Optional[SequenceCall] = None
        
        for line in lines:
            line = line.strip()
            
            # Parse ANL or FUNC lines
            match = anl_func_pattern.match(line)
            if not match:
                continue
            
            # Get test socket index from first test
            if test_socket_index == -1:
                try:
                    test_socket_index = int(match.group("Site"))
                except ValueError:
                    pass
            
            comp_ref = match.group("TaskName")
            step_name = match.group("Diagnostic")
            
            # Skip NUL steps
            if step_name.startswith("NUL "):
                continue
            
            # Get component type from reference
            step_ref, found_in_list = self._get_name_from_ref(comp_ref)
            
            if step_ref == "Ignore":
                continue
            
            # Handle sequence changes - group tests by component type
            if not found_in_list or step_ref == "Action":
                # Action steps go directly to root
                current_sequence = root
            elif step_ref != prev_step_ref:
                # Create new sequence for this component type
                current_sequence = root.add_sequence_call(
                    name=step_ref,
                    file_name=f"{step_ref.replace(' ', '_')}.seq",
                    version="1.0"
                )
            
            prev_step_ref = step_ref
            
            # Parse test data
            result_str = match.group("Result")
            step_passed = result_str.startswith("PASS")
            step_status = "P" if step_passed else "F"
            
            measure_str = match.group("Measure")
            min_str = match.group("Min")
            max_str = match.group("Max")
            unit_str = match.group("Unit")
            
            # Add step to current sequence
            self._add_step(
                sequence=current_sequence,
                name=step_name,
                step_ref=step_ref,
                status=step_status,
                measure_str=measure_str,
                min_str=min_str,
                max_str=max_str,
                unit_str=unit_str,
            )
        
        # Calculate execution time if we have both start and end
        if start_time and end_time:
            exec_time = (end_time - start_time).total_seconds()
            root.tot_time = exec_time
        
        return report
    
    def _get_name_from_ref(self, ref_name: str) -> Tuple[str, bool]:
        """Get component type name from reference"""
        match = re.match(r'(?P<Ref>[A-Za-z]+)', ref_name)
        if match:
            ref_type = match.group("Ref")
            if ref_type in self.COMPONENT_TYPES:
                return self.COMPONENT_TYPES[ref_type], True
            return ref_name, False
        return ref_name, False
    
    def _add_step(
        self,
        sequence: SequenceCall,
        name: str,
        step_ref: str,
        status: str,
        measure_str: str,
        min_str: str,
        max_str: str,
        unit_str: str,
    ) -> None:
        """
        Add a test step to the sequence using the pyWATS API.
        
        Determines step type based on measurement data and uses appropriate
        factory method.
        """
        # Action steps - use generic step
        if step_ref == "Action":
            sequence.add_generic_step(
                step_type=FlowType.Action,
                name=name,
                status=status,
            )
            return
        
        # Pass/fail for "Automatic" measurements - use boolean step
        if measure_str == "Automatic":
            sequence.add_boolean_step(
                name=name,
                status=status,
            )
            return
        
        # Parse numeric values
        measure = self._parse_float(measure_str)
        min_val = self._parse_float(min_str)
        max_val = self._parse_float(max_str)
        
        # Pass/fail if all zeros - use boolean step
        if measure == 0 and min_val == 0 and max_val == 0:
            sequence.add_boolean_step(
                name=name,
                status=status,
            )
            return
        
        # Numeric limit step - determine comparison operator
        comp_op = CompOp.GELE  # Default: between limits
        low_limit: Optional[float] = None
        high_limit: Optional[float] = None
        
        if max_val == float('inf'):
            # Only lower limit
            comp_op = CompOp.GE
            low_limit = min_val
        elif min_val == float('-inf'):
            # Only upper limit
            comp_op = CompOp.LE
            high_limit = max_val
        else:
            # Both limits
            comp_op = CompOp.GELE
            low_limit = min_val
            high_limit = max_val
        
        # Handle NaN measurement
        if measure != measure:  # NaN check
            measure = 0.0
        
        # Add numeric step using API
        sequence.add_numeric_step(
            name=name,
            value=measure,
            unit=unit_str if unit_str else "",
            comp_op=comp_op,
            low_limit=low_limit,
            high_limit=high_limit,
            status=status,
        )
    
    def _parse_float(self, value: str) -> float:
        """Parse a float value, handling special cases"""
        value = value.strip()
        
        if not value:
            return 0.0
        
        if value.lower() == "nan":
            return float('nan')
        
        if value == "+inf" or value == "inf":
            return float('inf')
        
        if value == "-inf":
            return float('-inf')
        
        try:
            return float(value)
        except ValueError:
            return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Test/Demo Code
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import json
    import tempfile
    import os
    
    # Create sample SPEA ICT file
    sample_content = """START;TestFolder;TestPlan;001;ProductA;Operator1;01/15/2024;10:30:45
LOT;BATCH001
SN;SN12345
ANL;1;R100;1;1;Resistance Test;R100;PASS;1500;1400;1600;Ohm;TP1;UID001
ANL;1;R101;2;2;Resistance Test;R101;PASS;2200;2100;2300;Ohm;TP2;UID002
ANL;1;C200;3;3;Capacitance Test;C200;FAIL;95;100;120;nF;TP3;UID003
FUNC;1;U1;4;4;IC Test;U1;PASS;Automatic;0;0;;TP4
BOARDRESULT;FAIL
END;FAIL;01/15/2024;10:32:15
"""
    
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / "SPEA_test.txt"
    
    with open(temp_path, 'w') as f:
        f.write(sample_content)
    
    try:
        converter = SPEAConverter()
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
        os.rmdir(temp_dir)
