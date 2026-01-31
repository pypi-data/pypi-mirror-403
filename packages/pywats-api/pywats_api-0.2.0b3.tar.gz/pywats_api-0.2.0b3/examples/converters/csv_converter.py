"""
Example File Converter V2 - Using UUTReport Model

Demonstrates how to create a FileConverter using the PyWATS UUTReport API.

This example converts CSV test result files into WATS reports using the
proper API pattern with:
- api.report.create_uut_report()
- uut.get_root_sequence_call()
- root.add_numeric_step()
- step.add_measurement()

This is the recommended approach for all new converters.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# PyWATS Report Model API Imports
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
    ConversionStatus,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)


class CsvConverter(FileConverter):
    """
    Example converter that processes CSV test result files using UUTReport model.
    
    Expected CSV format:
        serial_number,part_number,result,test_name,measured_value,unit,pass,low_limit,high_limit
        SN001,PN-123,PASSED,Voltage Test,12.5,V,TRUE,10.0,15.0
        SN001,PN-123,PASSED,Current Test,1.2,A,TRUE,0.5,2.0
    
    This converter demonstrates the CORRECT pattern for building WATS reports:
    
    1. Create UUTReport with header information
    2. Get root sequence using get_root_sequence_call()
    3. Add steps using factory methods:
       - add_numeric_step() for numeric measurements
       - add_boolean_step() for pass/fail tests
       - add_string_step() for string values
    4. Return the UUTReport object (NOT a dictionary!)
    
    Usage:
        converter = CsvConverter()
        source = ConverterSource.from_file(Path("test_results.csv"))
        
        validation = converter.validate(source, context)
        if validation.can_convert:
            result = converter.convert(source, context)
            # result.report is a UUTReport instance
    """
    
    # =========================================================================
    # Converter Identity
    # =========================================================================
    
    @property
    def name(self) -> str:
        return "CSV Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts CSV test result files into WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        """Match CSV files with specific naming convention"""
        return ["*_results.csv", "test_*.csv", "*.csv"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """Define configurable arguments for this converter"""
        return {
            "processCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=10,
                description="Process/operation type code",
            ),
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Part revision number",
            ),
            "stationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="CSV Station",
                description="Station name",
            ),
            "location": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Production",
                description="Station location",
            ),
            "purpose": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Functional Test",
                description="Test purpose",
            ),
            "failOnError": ArgumentDefinition(
                arg_type=ArgumentType.BOOLEAN,
                default=True,
                description="Fail entire conversion on any row error",
            ),
        }
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate the CSV file and extract preview information.
        
        Returns a ValidationResult with confidence score based on how
        well the file matches expected format.
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        # Check file extension
        if source.path.suffix.lower() != '.csv':
            return ValidationResult.no_match("Not a CSV file")
        
        try:
            # Read first few rows to validate format
            with open(source.path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check required columns
                if reader.fieldnames is None:
                    return ValidationResult.no_match("Could not read CSV headers")
                
                required_columns = {'serial_number', 'part_number', 'result'}
                optional_columns = {'test_name', 'measured_value', 'unit', 'pass', 'low_limit', 'high_limit'}
                
                available = set(col.lower() for col in reader.fieldnames)
                missing = required_columns - available
                
                if missing:
                    return ValidationResult.pattern_match(
                        message=f"CSV file but missing required columns: {missing}"
                    )
                
                # Read first data row to extract preview info
                try:
                    first_row = next(reader)
                    serial = first_row.get('serial_number', '')
                    part = first_row.get('part_number', '')
                    overall_result = first_row.get('result', '')
                    
                    # High confidence if we found all data
                    has_optional = optional_columns.issubset(available)
                    confidence = 0.95 if has_optional else 0.75
                    
                    return ValidationResult.good_match(
                        confidence=confidence,
                        message="Valid CSV test file",
                        detected_serial_number=serial,
                        detected_part_number=part,
                        detected_result=overall_result,
                    )
                    
                except StopIteration:
                    return ValidationResult.pattern_match(
                        message="CSV file has headers but no data rows"
                    )
                    
        except csv.Error as e:
            return ValidationResult.no_match(f"Invalid CSV format: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    # =========================================================================
    # Conversion
    # =========================================================================
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """
        Convert the CSV file to a WATS UUTReport.
        
        Uses the PyWATS UUTReport model API to build the report properly.
        
        Args:
            source: The file source to convert
            context: Conversion context with configuration
        
        Returns:
            ConverterResult with UUTReport object or error
        """
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        # Get arguments from context
        process_code = context.get_argument("processCode", 10)
        part_revision = context.get_argument("partRevision", "1.0")
        station_name = context.get_argument("stationName", "CSV Station")
        location = context.get_argument("location", "Production")
        purpose = context.get_argument("purpose", "Functional Test")
        fail_on_error = context.get_argument("failOnError", True)
        
        try:
            with open(source.path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return ConverterResult.failed_result(error="CSV file has no data rows")
            
            # Extract header information from first row
            first_row = rows[0]
            serial_number = first_row.get('serial_number', 'UNKNOWN')
            part_number = first_row.get('part_number', 'UNKNOWN')
            overall_result = first_row.get('result', 'UNKNOWN').upper()
            
            # ═══════════════════════════════════════════════════════════════════
            # Step 1: Create UUTReport using the API
            # ═══════════════════════════════════════════════════════════════════
            report = UUTReport(
                pn=part_number,
                sn=serial_number,
                rev=part_revision,
                process_code=int(process_code),
                station_name=station_name,
                location=location,
                purpose=purpose,
                result="P" if overall_result == "PASSED" else "F",
                start=datetime.now().astimezone(),
            )
            
            # Add misc info about source file
            report.add_misc_info(description="Source File", value=source.path.name)
            report.add_misc_info(description="Converter", value=f"{self.name} v{self.version}")
            
            # ═══════════════════════════════════════════════════════════════════
            # Step 2: Get root sequence and configure it
            # ═══════════════════════════════════════════════════════════════════
            root = report.get_root_sequence_call()
            root.name = source.path.stem  # Use filename as sequence name
            root.sequence.version = self.version
            root.sequence.file_name = source.path.name
            
            # ═══════════════════════════════════════════════════════════════════
            # Step 3: Add test steps from CSV rows
            # ═══════════════════════════════════════════════════════════════════
            for i, row in enumerate(rows, 1):
                step_added = self._add_step_from_row(root, row, i)
                if not step_added and fail_on_error:
                    return ConverterResult.failed_result(
                        error=f"Error in row {i}: invalid data format"
                    )
            
            # ═══════════════════════════════════════════════════════════════════
            # Step 4: Return the UUTReport (not a dict!)
            # ═══════════════════════════════════════════════════════════════════
            return ConverterResult.success_result(
                report=report,  # UUTReport instance, NOT dict!
                post_action=PostProcessAction.MOVE,
            )
            
        except Exception as e:
            return ConverterResult.failed_result(
                error=f"Conversion error: {e}",
                warnings=[f"File: {source.path}"]
            )
    
    def _add_step_from_row(
        self,
        sequence: SequenceCall,
        row: Dict[str, str],
        index: int,
    ) -> bool:
        """
        Add a step from a CSV row using the PyWATS API.
        
        Returns True if step was added successfully.
        """
        try:
            test_name = row.get('test_name', f'Test_{index}')
            measured = row.get('measured_value', '')
            unit = row.get('unit', '')
            passed_str = row.get('pass', 'TRUE').upper()
            passed = passed_str == 'TRUE'
            
            # Parse limits if available
            low_limit_str = row.get('low_limit', '')
            high_limit_str = row.get('high_limit', '')
            
            low_limit: Optional[float] = None
            high_limit: Optional[float] = None
            
            if low_limit_str:
                try:
                    low_limit = float(low_limit_str)
                except ValueError:
                    pass
            
            if high_limit_str:
                try:
                    high_limit = float(high_limit_str)
                except ValueError:
                    pass
            
            # Determine step type and create accordingly
            if measured:
                try:
                    value = float(measured)
                    
                    # Determine comparison operator based on available limits
                    if low_limit is not None and high_limit is not None:
                        # Have both limits - use GELE (Greater Equal, Less Equal)
                        sequence.add_numeric_step(
                            name=test_name,
                            value=value,
                            unit=unit,
                            low_limit=low_limit,
                            high_limit=high_limit,
                            comp_op=CompOp.GELE,
                            status="P" if passed else "F",
                        )
                    elif low_limit is not None:
                        # Only low limit - use GE (Greater Equal)
                        sequence.add_numeric_step(
                            name=test_name,
                            value=value,
                            unit=unit,
                            low_limit=low_limit,
                            comp_op=CompOp.GE,
                            status="P" if passed else "F",
                        )
                    elif high_limit is not None:
                        # Only high limit - use LE (Less Equal)
                        sequence.add_numeric_step(
                            name=test_name,
                            value=value,
                            unit=unit,
                            high_limit=high_limit,
                            comp_op=CompOp.LE,
                            status="P" if passed else "F",
                        )
                    else:
                        # No limits - use LOG (just log the value)
                        sequence.add_numeric_step(
                            name=test_name,
                            value=value,
                            unit=unit,
                            comp_op=CompOp.LOG,
                            status="P" if passed else "F",
                        )
                except ValueError:
                    # Not a number - add as string step
                    sequence.add_string_step(
                        name=test_name,
                        value=measured,
                        status="P" if passed else "F",
                    )
            else:
                # No measured value - add as boolean pass/fail step
                sequence.add_boolean_step(
                    name=test_name,
                    value=passed,
                    status="P" if passed else "F",
                )
            
            return True
            
        except Exception:
            return False
    
    # =========================================================================
    # Lifecycle Hooks (Optional)
    # =========================================================================
    
    def on_load(self, context: ConverterContext) -> None:
        """Called when converter is loaded"""
        print(f"[{self.name}] Converter loaded")
    
    def on_success(
        self,
        source: ConverterSource,
        result: ConverterResult,
        context: ConverterContext
    ) -> None:
        """Called after successful conversion"""
        print(f"[{self.name}] Successfully converted: {source.primary_name}")
    
    def on_failure(
        self,
        source: ConverterSource,
        result: ConverterResult,
        context: ConverterContext
    ) -> None:
        """Called after failed conversion"""
        print(f"[{self.name}] Failed to convert: {source.primary_name}")
        print(f"  Error: {result.error}")


# ═══════════════════════════════════════════════════════════════════════════════
# Test/Demo Code
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Test the converter with a sample file"""
    
    # Create a sample CSV file with limits
    sample_csv = Path("sample_test_results.csv")
    sample_csv.write_text(
        "serial_number,part_number,result,test_name,measured_value,unit,pass,low_limit,high_limit\n"
        "SN001,PN-123,PASSED,Voltage Test,12.5,V,TRUE,10.0,15.0\n"
        "SN001,PN-123,PASSED,Current Test,1.2,A,TRUE,0.5,2.0\n"
        "SN001,PN-123,PASSED,Resistance Test,100,Ohm,TRUE,90,110\n"
        "SN001,PN-123,PASSED,Power On Self Test,,,TRUE,,\n"
    )
    
    try:
        converter = CsvConverter()
        source = ConverterSource.from_file(sample_csv)
        context = ConverterContext(station_name="TEST-STATION-01")
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, "
              f"confidence={validation.confidence:.2f}")
        print(f"  Detected: SN={validation.detected_serial_number}, "
              f"PN={validation.detected_part_number}")
        
        # Convert if valid
        if validation.can_convert:
            result = converter.convert(source, context)
            print(f"\nConversion: status={result.status.value}")
            
            if result.status == ConversionStatus.SUCCESS:
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
                    step_type = step.step_type if hasattr(step, 'step_type') else 'Unknown'
                    print(f"  └─ {step_type}: {step.name} [{step.status}]")
                
                # Show JSON (truncated)
                print(f"\n=== JSON Output (truncated) ===")
                json_output = report.model_dump_json(by_alias=True, indent=2, exclude_none=True)
                print(json_output[:1500] + "..." if len(json_output) > 1500 else json_output)
    
    finally:
        if sample_csv.exists():
            sample_csv.unlink()


if __name__ == "__main__":
    main()
