"""
JSON Format Converter (v2 - Using UUTReport Model)

Converts JSON test result files into WATS reports using the pyWATS UUTReport model.
This version demonstrates the proper way to build reports using factory methods.

Port of the C# JSONFormatConverter.

Expected JSON structure:
{
    "processName": "OperationType",
    "pn": "PartNumber",
    "sn": "SerialNumber",
    "rev": "Revision",
    "result": "P" or "F",
    "startUTC": "2024-01-01T00:00:00Z",
    "miscInfos": [{"description": "...", "text": "..."}],
    "subUnits": [{"partType": "...", "pn": "...", "sn": "...", "rev": "..."}],
    "testGroups": {
        "GroupName": {
            "TestName": {
                "Type": "number|string|Boolean|array",
                "value": ...,
                "status": "P|F|S|E|D",
                "compOp": "LOG|EQ|NE|...",
                "lowlimit": ...,
                "highlimit": ...,
                "unit": "..."
            }
        }
    }
}
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# pyWATS imports for UUT model
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.uut_info import UUTInfo
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.shared.enums import CompOp
from pywats.domains.report.report_models.misc_info import MiscInfo
from pywats.domains.report.report_models.sub_unit import SubUnit

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


class JSONConverter(FileConverter):
    """
    Converts JSON test result files to WATS reports using UUTReport model.
    
    This converter demonstrates the proper pattern for building reports:
    1. Create UUTReport with header info
    2. Get root sequence via report.get_root_sequence_call()
    3. Add sub-sequences via root.add_sequence_call()
    4. Add test steps via sequence.add_numeric_step(), add_boolean_step(), etc.
    
    File qualification:
    - File extension must be .json
    - Must contain 'processName', 'pn', 'sn' fields
    - Must contain 'testGroups' object
    """
    
    # Mapping from JSON compOp strings to CompOp enum
    COMP_OP_MAP = {
        "LOG": CompOp.LOG,
        "EQ": CompOp.EQ,
        "NE": CompOp.NE,
        "LT": CompOp.LT,
        "LE": CompOp.LE,
        "GT": CompOp.GT,
        "GE": CompOp.GE,
        "GELE": CompOp.GELE,
        "GTLT": CompOp.GTLT,
        "GELT": CompOp.GELT,
        "GTLE": CompOp.GTLE,
    }
    
    @property
    def name(self) -> str:
        return "JSON Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts JSON test result files into WATS reports (uses UUTReport model)"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.json"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operator": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="oper",
                description="Default operator name",
            ),
            "stationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="JSONConverter",
                description="Station name for the report",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="",
                description="Station location",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a properly formatted JSON test file.
        
        Confidence levels:
        - 0.95: Has all expected fields (processName, pn, sn, testGroups)
        - 0.7: Valid JSON with some expected fields
        - 0.3: Valid JSON file but doesn't match expected structure
        - 0.0: Not a valid JSON file
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        if source.path.suffix.lower() != '.json':
            return ValidationResult.no_match("Not a JSON file")
        
        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return ValidationResult.pattern_match(
                    message="JSON file but root is not an object"
                )
            
            # Check for required fields
            required_fields = {'processName', 'pn', 'sn', 'testGroups'}
            found_fields = required_fields.intersection(data.keys())
            
            if len(found_fields) == 0:
                return ValidationResult.pattern_match(
                    message="JSON file but no expected test fields found"
                )
            
            # Check for testGroups structure
            has_test_groups = 'testGroups' in data and isinstance(data['testGroups'], dict)
            
            # Extract preview info
            serial_number = data.get('sn', '')
            part_number = data.get('pn', '')
            result = data.get('result', '')
            process = data.get('processName', '')
            
            # Calculate confidence
            confidence = 0.3 + (len(found_fields) / len(required_fields)) * 0.5
            if has_test_groups and len(data.get('testGroups', {})) > 0:
                confidence += 0.15
            
            return ValidationResult(
                can_convert=True,
                confidence=min(0.95, confidence),
                message=f"Valid JSON test file ({len(found_fields)}/{len(required_fields)} fields)",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result="Passed" if result == "P" else "Failed" if result == "F" else result,
                detected_process=process,
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult.no_match(f"Invalid JSON: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert JSON test file to WATS report using UUTReport model"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get arguments
            operator = context.get_argument("operator", "oper")
            station_name = context.get_argument("stationName", "JSONConverter")
            location = context.get_argument("location", "")
            
            # Parse start time
            start_time = datetime.now().astimezone()
            if "startUTC" in data:
                try:
                    start_time = datetime.fromisoformat(
                        data["startUTC"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass
            
            # Parse process code (try to extract numeric, fallback to string hash)
            process_name = data.get("processName", "10")
            try:
                process_code = int(process_name)
            except ValueError:
                # Use a deterministic hash for string process names
                process_code = abs(hash(process_name)) % 1000
            
            # Create UUTReport using the model
            report = UUTReport(
                pn=data.get("pn", "UNKNOWN"),
                sn=data.get("sn", "UNKNOWN"),
                rev=data.get("rev", "1.0"),
                process_code=process_code,
                station_name=station_name,
                location=location,
                purpose=process_name,  # Store original process name as purpose
                result="P" if data.get("result", "F") == "P" else "F",
                start=start_time,
            )
            
            # Set UUT info
            report.info = UUTInfo(operator=operator)
            
            # Add misc infos
            for info in data.get("miscInfos", []):
                if isinstance(info, dict):
                    desc = info.get("description", "")
                    text = info.get("text", "")
                    if desc or text:
                        misc = MiscInfo(description=desc, string_value=text)
                        if report.misc_infos is None:
                            report.misc_infos = []
                        report.misc_infos.append(misc)
            
            # Add sub-units
            for unit in data.get("subUnits", []):
                if isinstance(unit, dict):
                    sub = SubUnit(
                        part_type=unit.get("partType", ""),
                        pn=unit.get("pn", ""),
                        sn=unit.get("sn", ""),
                        rev=unit.get("rev", ""),
                    )
                    if report.sub_units is None:
                        report.sub_units = []
                    report.sub_units.append(sub)
            
            # Get root sequence and build test hierarchy
            root = report.get_root_sequence_call()
            root.name = f"{process_name} Tests"
            
            # Process test groups
            self._build_test_hierarchy(data, root)
            
            return ConverterResult.success_result(
                report=report,  # Now passing UUTReport instead of dict!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _build_test_hierarchy(
        self,
        data: Dict[str, Any],
        root: SequenceCall
    ) -> None:
        """Build test step hierarchy from testGroups"""
        test_groups = data.get("testGroups", {})
        
        for group_name, group_tests in test_groups.items():
            if not isinstance(group_tests, dict):
                continue
            
            # Create sequence for this group
            group_seq = root.add_sequence_call(
                name=group_name,
                file_name=f"{group_name}.seq",
                version="1.0.0"
            )
            
            for test_name, test_data in group_tests.items():
                if test_name == "totTime":
                    # Group total time - set on sequence
                    if isinstance(test_data, (int, float)):
                        group_seq.tot_time = float(test_data)
                    continue
                
                if not isinstance(test_data, dict):
                    continue
                
                self._add_step(group_seq, test_name, test_data)
    
    def _add_step(
        self,
        sequence: SequenceCall,
        test_name: str,
        test_data: Dict[str, Any]
    ) -> None:
        """Add a test step to the sequence based on test type"""
        test_type = test_data.get("Type", "")
        status = self._map_status(test_data.get("status", "D"))
        comp_op_str = test_data.get("compOp", "LOG")
        comp_op = self.COMP_OP_MAP.get(comp_op_str, CompOp.LOG)
        
        if test_type == "number":
            # Single numeric measurement
            value = test_data.get("value")
            if value is None:
                return
            
            # Build kwargs conditionally
            step_kwargs: Dict[str, Any] = {
                "name": test_name,
                "value": float(value),
                "unit": test_data.get("unit", ""),
                "comp_op": comp_op,
                "status": status,
            }
            if test_data.get("lowlimit") is not None:
                step_kwargs["low_limit"] = float(test_data["lowlimit"])
            if test_data.get("highlimit") is not None:
                step_kwargs["high_limit"] = float(test_data["highlimit"])
            
            sequence.add_numeric_step(**step_kwargs)
        
        elif test_type == "string":
            # String value test
            value = str(test_data.get("value", ""))
            
            # For long strings, store in reportText
            if len(value) >= 100:
                sequence.add_string_step(
                    name=test_name,
                    value="(see report text)",
                    status=status,
                    report_text=value,
                )
            else:
                sequence.add_string_step(
                    name=test_name,
                    value=value,
                    status=status,
                )
        
        elif test_type == "Boolean":
            # Pass/Fail test
            sequence.add_boolean_step(
                name=test_name,
                status=status,
            )
        
        elif test_type == "array":
            # Multiple numeric measurements
            array_values = test_data.get("value", [])
            unit = test_data.get("unit", "")
            low = test_data.get("lowlimit")
            high = test_data.get("highlimit")
            
            # Create multi-numeric step
            multi_step = sequence.add_multi_numeric_step(
                name=test_name,
                status=status,
            )
            
            # Add each measurement
            for i, val in enumerate(array_values):
                # Build kwargs conditionally to avoid passing None where not expected
                meas_kwargs: Dict[str, Any] = {
                    "name": f"[{i}]",
                    "value": float(val),
                    "unit": unit,
                    "status": status,
                    "comp_op": comp_op,
                }
                if low is not None:
                    meas_kwargs["low_limit"] = float(low)
                if high is not None:
                    meas_kwargs["high_limit"] = float(high)
                multi_step.add_measurement(**meas_kwargs)
    
    def _map_status(self, status: str) -> str:
        """Map JSON status code to WATS status code"""
        status_map = {
            "P": "P",      # Passed
            "true": "P",   # Passed
            "F": "F",      # Failed
            "false": "F",  # Failed
            "S": "S",      # Skipped
            "E": "E",      # Error
            "D": "D",      # Done
        }
        return status_map.get(status, "D")


# Test code
if __name__ == "__main__":
    import tempfile
    
    # Create sample JSON
    sample_data = {
        "processName": "FUNC_TEST",
        "pn": "PN-12345",
        "sn": "SN-00001",
        "rev": "1.0",
        "result": "P",
        "startUTC": "2024-01-15T10:30:00Z",
        "miscInfos": [
            {"description": "Operator", "text": "John Doe"},
            {"description": "Fixture", "text": "FIX-001"}
        ],
        "subUnits": [
            {"partType": "PCB", "pn": "PCB-001", "sn": "PCB-SN-001", "rev": "A"}
        ],
        "testGroups": {
            "PowerTests": {
                "totTime": 1.5,
                "VoltageTest": {
                    "Type": "number",
                    "value": 12.1,
                    "status": "P",
                    "compOp": "GELE",
                    "lowlimit": 11.5,
                    "highlimit": 12.5,
                    "unit": "V"
                },
                "CurrentTest": {
                    "Type": "number",
                    "value": 1.2,
                    "status": "P",
                    "compOp": "LOG",
                    "unit": "A"
                }
            },
            "FunctionalTests": {
                "BootTest": {
                    "Type": "Boolean",
                    "value": True,
                    "status": "P"
                },
                "FirmwareVersion": {
                    "Type": "string",
                    "value": "v2.1.0",
                    "status": "D"
                },
                "MultiChannelReadings": {
                    "Type": "array",
                    "value": [1.01, 1.02, 0.99, 1.00],
                    "status": "P",
                    "compOp": "GELE",
                    "lowlimit": 0.95,
                    "highlimit": 1.05,
                    "unit": "V"
                }
            }
        }
    }
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f, indent=2)
        temp_path = Path(f.name)
    
    try:
        converter = JSONConverter()
        source = ConverterSource.from_file(temp_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Detected: SN={validation.detected_serial_number}, PN={validation.detected_part_number}")
        
        # Convert
        result = converter.convert(source, context)
        print(f"\nConversion status: {result.status.value}")
        
        if result.report and isinstance(result.report, UUTReport):
            # result.report is now a UUTReport object!
            report: UUTReport = result.report  # type: ignore[assignment]
            print(f"\nGenerated UUTReport:")
            print(f"  Part Number: {report.pn}")
            print(f"  Serial Number: {report.sn}")
            print(f"  Revision: {report.rev}")
            print(f"  Result: {report.result}")
            print(f"  Station: {report.station_name}")
            
            # Show the step hierarchy
            root = report.get_root_sequence_call()
            print(f"\nTest Hierarchy:")
            print(f"  Root: {root.name}")
            if root.steps:
                for seq in root.steps:
                    print(f"    Sequence: {seq.name}")
                    if isinstance(seq, SequenceCall) and seq.steps:  # type: ignore[union-attr]
                        for step in seq.steps:
                            print(f"      Step: {step.name} ({type(step).__name__})")
            
            # Serialize to JSON (for comparison)
            print("\n\nSerialized Report (WSJF format):")
            report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
            print(json.dumps(report_dict, indent=2))
            
    finally:
        temp_path.unlink()
