"""
Klippel Log Converter - V2 Using UUTReport Model

Converts Klippel test log files to WATS reports using pyWATS UUTReport model.
Port of the C# KlippelLogConverter.

IMPORTANT: This converter uses the pyWATS UUTReport model - NOT raw dictionaries!

This converter handles Klippel test result files with:
- Header file with Key=Value pairs
- Data folder with same name as header file
- TSV files in data folder with test measurements

Header contains start time in format:
Year-Month-WeekNo-JDay-WDay-Day-Hour-Minute-Second-MSec-UTCOffset
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# pyWATS model imports - REQUIRED
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.shared.enums import CompOp
from pywats.domains.report.report_models.uut.step import StepStatus

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


class KlippelConverter(FileConverter):
    """
    Converts Klippel speaker test log files to WATS reports using UUTReport model.
    
    File qualification:
    - Text file with Key=Value format header
    - Contains Cfg_DutStartTime, Cfg_SerialNumber, Ctrl_OverallVerdict
    - Data folder with same name as header file
    - TSV files in data folder with measurements
    
    Data file formats:
    - Single measurements: name, value [, min, max]
    - Frequency data: frq, value [, max [, min]]
    """
    
    @property
    def name(self) -> str:
        return "Klippel Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Klippel speaker test log files to WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt", "*.log"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "partNumber": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="PartNumber1",
                description="Part number for the reports",
            ),
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Part revision for the reports",
            ),
            "sequenceName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="SequenceName1",
                description="Sequence name for the reports",
            ),
            "sequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0.0",
                description="Sequence version for the reports",
            ),
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=700,
                description="Operation type code for Klippel tests",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a Klippel log header file.
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        try:
            header_data = {}
            
            with open(source.path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            header_data[parts[0]] = parts[1]
            
            # Check for required keys
            required_keys = ["Cfg_DutStartTime", "Cfg_SerialNumber", "Ctrl_OverallVerdict"]
            missing_keys = [k for k in required_keys if k not in header_data]
            
            if len(missing_keys) == len(required_keys):
                return ValidationResult.pattern_match(
                    message="File doesn't have expected Klippel header keys"
                )
            
            if missing_keys:
                confidence = 0.6 - (len(missing_keys) * 0.1)
                return ValidationResult(
                    can_convert=True,
                    confidence=max(0.3, confidence),
                    message=f"Partial Klippel header (missing: {', '.join(missing_keys)})",
                    detected_serial_number=header_data.get("Cfg_SerialNumber"),
                )
            
            # Check for data folder
            data_folder = source.path.parent / source.path.stem
            data_files = []
            
            if data_folder.exists() and data_folder.is_dir():
                data_files = list(data_folder.glob("*.txt"))
            
            confidence = 0.8
            if data_files:
                confidence += 0.15
            
            # Parse start time to validate format
            time_str = header_data.get("Cfg_DutStartTime", "")
            time_pattern = r'(?P<Year>\d+)-(?P<Month>\d+)-(?P<WeekNo>-?\d+)-(?P<JDay>-?\d+)-(?P<WDay>\d+)-(?P<Day>\d+)-(?P<Hour>\d+)-(?P<Minute>\d+)-(?P<Second>\d+)-(?P<MSec>\d+)-(?P<UTCOffset>\d+)'
            
            if re.match(time_pattern, time_str):
                confidence = min(0.95, confidence + 0.05)
            
            return ValidationResult(
                can_convert=True,
                confidence=confidence,
                message=f"Valid Klippel log ({len(data_files)} data files)",
                detected_serial_number=header_data.get("Cfg_SerialNumber"),
            )
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert Klippel log file to UUTReport"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            # Read header file
            header_data = {}
            
            with open(source.path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            header_data[parts[0]] = parts[1]
            
            # Get parameters
            part_number = context.get_argument("partNumber", "PartNumber1")
            part_revision = context.get_argument("partRevision", "1.0")
            sequence_name = context.get_argument("sequenceName", "SequenceName1")
            sequence_version = context.get_argument("sequenceVersion", "1.0.0")
            operation_code = context.get_argument("operationTypeCode", 700)
            
            # Get serial number and operator
            serial_number = header_data.get("Cfg_SerialNumber", "UNKNOWN")
            user_name = header_data.get("Cfg_UserName", "")
            
            # Parse start time
            start_time = self._parse_start_time(header_data)
            
            # Determine overall result
            overall_verdict = header_data.get("Ctrl_OverallVerdict", "0")
            # Code: -1=Void, 0=Fail, 1=Pass, 2=Warning, 3=Noise, 4=Invalid
            result = "P" if overall_verdict == "1" else "F"
            
            # ========================================
            # BUILD REPORT USING UUTReport MODEL
            # ========================================
            
            report = UUTReport(
                pn=part_number,
                sn=serial_number,
                rev=part_revision,
                process_code=operation_code,
                station_name="Klippel",
                location="Production",  # Required field
                purpose="Functional Test",  # Required field
                result=result,
                start=start_time or datetime.now(),
            )
            
            # Set operator via info if available
            # Note: operator field may need to be set on the info object
            
            # Add misc info using factory method
            if source.path:
                report.add_misc_info(description="FileName", value=source.path.name)
            
            if "Cfg_LoginMode" in header_data:
                report.add_misc_info(description="Cfg_LoginMode", value=header_data["Cfg_LoginMode"])
            if "Cfg_Speaker" in header_data:
                report.add_misc_info(description="Cfg_Speaker", value=header_data["Cfg_Speaker"])
            if user_name:
                report.add_misc_info(description="Operator", value=user_name)
            
            # Get root sequence
            root = report.get_root_sequence_call()
            root.name = sequence_name
            root.sequence.version = sequence_version
            
            # Read data files from data folder
            data_folder = source.path.parent / source.path.stem
            
            if data_folder.exists() and data_folder.is_dir():
                self._process_data_files(data_folder, root)
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _parse_start_time(self, header_data: Dict[str, str]) -> Optional[datetime]:
        """Parse Klippel start time format"""
        time_str = header_data.get("Cfg_DutStartTime", "")
        time_pattern = r'(?P<Year>\d+)-(?P<Month>\d+)-(?P<WeekNo>-?\d+)-(?P<JDay>-?\d+)-(?P<WDay>\d+)-(?P<Day>\d+)-(?P<Hour>\d+)-(?P<Minute>\d+)-(?P<Second>\d+)-(?P<MSec>\d+)-(?P<UTCOffset>\d+)'
        time_match = re.match(time_pattern, time_str)
        
        if time_match:
            try:
                return datetime(
                    int(time_match.group("Year")),
                    int(time_match.group("Month")),
                    int(time_match.group("Day")),
                    int(time_match.group("Hour")),
                    int(time_match.group("Minute")),
                    int(time_match.group("Second")),
                    int(time_match.group("MSec")) * 1000  # Convert ms to microseconds
                )
            except ValueError:
                pass
        return None
    
    def _process_data_files(self, data_folder: Path, root: SequenceCall) -> None:
        """Process all data files in the data folder"""
        data_files = sorted(data_folder.glob("*.txt"))
        current_sequence_name = ""
        current_sequence: SequenceCall = root  # Start with root as default
        
        for data_file in data_files:
            seq_name = self._get_sequence_name(data_file)
            
            # Group by sequence (first part of filename before hyphen)
            if seq_name != current_sequence_name:
                current_sequence_name = seq_name
                new_sequence = root.add_sequence_call(
                    name=seq_name,
                    file_name=f"{seq_name}.seq",
                    version="1.0"
                )
                # Type assertion: add_sequence_call always returns a SequenceCall
                assert isinstance(new_sequence, SequenceCall)
                current_sequence = new_sequence
            
            self._read_data_file(data_file, current_sequence)
    
    def _get_sequence_name(self, file_path: Path) -> str:
        """Get sequence name from filename (part before hyphen)"""
        filename_parts = file_path.stem.split('-')
        return filename_parts[0] if filename_parts else file_path.stem
    
    def _read_data_file(self, file_path: Path, sequence: SequenceCall) -> None:
        """Read a data file and add steps to sequence"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            if not lines:
                return
            
            # Parse header
            headers = lines[0].strip().split('\t')
            
            if headers[0] == "name":
                self._process_single_measurements(lines[1:], sequence)
            elif headers[0] == "frq":
                self._process_frequency_data(lines[1:], headers, sequence)
                
        except Exception as e:
            print(f"Warning: Error reading data file {file_path}: {e}")
    
    def _process_single_measurements(self, lines: List[str], sequence: SequenceCall) -> None:
        """Process single measurement lines"""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if not parts:
                continue
            
            step_name = parts[0]
            values = self._read_doubles(line)
            
            if not values:
                continue
            
            # Determine status and limits (using "P" for passed, "F" for failed)
            status = "P"
            kwargs: Dict[str, Any] = {
                "name": step_name,
                "value": values[0],
                "unit": "",
                "status": status,
            }
            
            if len(values) == 3:
                # values[0] = measured, values[1] = min, values[2] = max
                kwargs["comp_op"] = CompOp.GELE
                kwargs["low_limit"] = values[1]
                kwargs["high_limit"] = values[2]
                
                if not (values[1] <= values[0] <= values[2]):
                    kwargs["status"] = "F"
            else:
                kwargs["comp_op"] = CompOp.LOG
            
            sequence.add_numeric_step(**kwargs)
    
    def _process_frequency_data(self, lines: List[str], headers: List[str], sequence: SequenceCall) -> None:
        """Process frequency data lines with chart"""
        x_values: List[float] = []
        y_values: List[float] = []
        min_values: List[float] = []
        max_values: List[float] = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            values = self._read_doubles(line)
            
            if len(values) >= 2:
                x_values.append(values[0])
                y_values.append(values[1])
                
                if len(values) >= 4:
                    max_values.append(values[2])
                    min_values.append(values[3])
                elif len(values) == 3:
                    max_values.append(values[2])
        
        if not y_values:
            return
        
        y_name = headers[1] if len(headers) > 1 else "Y"
        
        # Create multi-numeric step with statistics (using "P" for passed, "F" for failed)
        multi_step = sequence.add_multi_numeric_step(
            name=y_name,
            status="P",
        )
        
        # Add measurements: avg, min, max
        avg_value = sum(y_values) / len(y_values)
        multi_step.add_measurement(
            name="avg",
            value=avg_value,
            unit="Hz",
            comp_op=CompOp.LOG,
            status="P",
        )
        
        if min_values:
            multi_step.add_measurement(
                name="min",
                value=min(y_values),
                unit="Hz",
                comp_op=CompOp.LOG,
                status="P",
            )
        
        if max_values:
            multi_step.add_measurement(
                name="max",
                value=max(y_values),
                unit="Hz",
                comp_op=CompOp.LOG,
                status="P",
            )
        
        # Check for out-of-bounds
        error_count = 0
        for i in range(len(y_values)):
            if max_values and i < len(max_values) and y_values[i] > max_values[i]:
                error_count += 1
            if min_values and i < len(min_values) and y_values[i] < min_values[i]:
                error_count += 1
        
        # Add out-of-bounds check step
        oob_status = "P" if error_count == 0 else "F"
        sequence.add_numeric_step(
            name="OutOfBounds",
            value=float(error_count),
            unit="#",
            comp_op=CompOp.EQ,
            high_limit=0.0,
            status=oob_status,
        )
        
        if error_count > 0:
            multi_step.status = StepStatus.Failed
        
        # TODO: Add chart support when available in the API
        # For now, chart data would need to be added via the chart step factory method
    
    def _read_doubles(self, line: str) -> List[float]:
        """Parse doubles from tab-separated line"""
        elements = line.split('\t')
        values: List[float] = []
        
        for element in elements:
            try:
                value = float(element)
                values.append(value)
            except ValueError:
                continue
        
        return values


# Test code
if __name__ == "__main__":
    import json
    import tempfile
    import shutil
    
    # Create sample Klippel log structure
    temp_dir = tempfile.mkdtemp()
    
    # Create header file
    header_content = """Cfg_UserName=TestOperator
Cfg_LoginMode=Local
Cfg_SerialNumber=KLP12345
Cfg_Speaker=Speaker-A1
Cfg_DutStartTime=2024-1-3-15-3-15-10-30-45-123-120
Ctrl_OverallVerdict=1
"""
    
    header_path = Path(temp_dir) / "TestLog.txt"
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    # Create data folder
    data_folder = Path(temp_dir) / "TestLog"
    data_folder.mkdir()
    
    # Create data file with single measurements
    single_data = """name\tvalue\tmin\tmax
Impedance\t8.5\t7.5\t9.5
Sensitivity\t92.3\t90.0\t95.0
"""
    with open(data_folder / "Electrical-Measurements.txt", 'w') as f:
        f.write(single_data)
    
    # Create data file with frequency data
    freq_data = """frq\tresponse\tmax\tmin
100\t85.0\t90.0\t80.0
200\t88.0\t92.0\t82.0
500\t90.5\t95.0\t85.0
1000\t92.0\t97.0\t87.0
"""
    with open(data_folder / "FrequencyResponse-FR.txt", 'w') as f:
        f.write(freq_data)
    
    try:
        converter = KlippelConverter()
        source = ConverterSource.from_file(header_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Detected SN: {validation.detected_serial_number}")
        
        # Convert
        result = converter.convert(source, context)
        print(f"\nConversion status: {result.status.value}")
        
        if result.report and isinstance(result.report, UUTReport):
            report = result.report
            print(f"\nGenerated UUTReport:")
            print(f"  Part Number: {report.pn}")
            print(f"  Serial Number: {report.sn}")
            print(f"  Result: {report.result}")
            
            # Serialize to JSON
            report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
            print("\nSerialized Report:")
            print(json.dumps(report_dict, indent=2))
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
