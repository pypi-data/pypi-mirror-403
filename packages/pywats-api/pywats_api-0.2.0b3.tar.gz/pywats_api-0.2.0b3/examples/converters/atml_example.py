"""
ATML Converter Example

This example demonstrates using the ATMLConverter to convert IEEE ATML
(Automatic Test Markup Language) test result files to WATS reports.

ATML is an IEEE standard (IEEE 1671/1636.1) for test information interchange.
The pyWATS ATMLConverter supports:
- ATML 2.02 (IEEE 1636.1:2006)
- ATML 5.00 (IEEE 1636.1:2011)
- ATML 6.01 (IEEE 1636.1:2013)
- TestStand WATS AddOn extensions

The TestStand WATS AddOn (available from NI TestStand) adds custom XML
elements that include WATS-specific information like:
- TSStepProperties: StepType, StepGroup, BlockLevel, TotalTime, ModuleTime
- TSResultSetProperties: BatchSerialNumber, TestSocketIndex
- TSLimitProperties: ThresholdType, RawLimits
"""

from pathlib import Path
from pywats_client.converters.standard import ATMLConverter
from pywats_client.converters.context import ConverterContext
from pywats_client.converters.models import ConverterSource


def convert_atml_file(atml_file: Path) -> None:
    """
    Convert an ATML file to a WATS report.
    
    Args:
        atml_file: Path to the ATML XML file
    """
    # Create the converter
    converter = ATMLConverter()
    
    # Create source and context
    source = ConverterSource(path=atml_file)
    context = ConverterContext(
        arguments={
            # Default values if not in file
            "operationTypeCode": "10",
            "partRevision": "1.0",
            "sequenceVersion": "1.0",
        }
    )
    
    # Validate the file first
    validation = converter.validate(source, context)
    print(f"Validation result: {validation.can_convert}")
    print(f"  Confidence: {validation.confidence}")
    print(f"  Message: {validation.message}")
    
    if validation.detected_serial_number:
        print(f"  Detected Serial: {validation.detected_serial_number}")
    if validation.detected_part_number:
        print(f"  Detected Part#: {validation.detected_part_number}")
    if validation.detected_result:
        print(f"  Detected Result: {validation.detected_result}")
    
    if not validation.can_convert:
        print("File cannot be converted")
        return
    
    # Convert the file
    result = converter.convert(source, context)
    
    if result.is_success:
        print(f"\nConversion successful!")
        print(f"  ATML Version: {result.metadata.get('atml_version', 'unknown')}")
        print(f"  Reports created: {result.metadata.get('reports_created', 1)}")
        
        # Access the report(s)
        if isinstance(result.report, list):
            for i, report in enumerate(result.report):
                print_report_summary(report, i + 1)
        else:
            print_report_summary(result.report, 1)
    else:
        print(f"Conversion failed: {result.error}")


def print_report_summary(report, index: int = 1) -> None:
    """Print a summary of the converted report."""
    print(f"\n--- Report {index} ---")
    print(f"  Operator: {report.operator}")
    print(f"  Part Number: {report.part_number}")
    print(f"  Part Revision: {report.part_revision}")
    print(f"  Serial Number: {report.serial_number}")
    print(f"  Sequence: {report.sequence_name}")
    print(f"  Station: {report.station_name}")
    print(f"  Status: {report.status}")
    
    if hasattr(report, 'start_time') and report.start_time:
        print(f"  Start Time: {report.start_time}")
    if hasattr(report, 'execution_time') and report.execution_time:
        print(f"  Execution Time: {report.execution_time:.3f}s")
    
    # Count steps
    step_count = count_steps(report)
    print(f"  Total Steps: {step_count}")


def count_steps(report) -> int:
    """Recursively count all steps in a report."""
    count = 0
    if hasattr(report, 'steps') and report.steps:
        count += len(report.steps)
        for step in report.steps:
            if hasattr(step, 'steps') and step.steps:
                count += count_steps_recursive(step)
    return count


def count_steps_recursive(parent) -> int:
    """Recursively count steps in a step container."""
    count = len(parent.steps) if hasattr(parent, 'steps') and parent.steps else 0
    for step in (parent.steps if hasattr(parent, 'steps') and parent.steps else []):
        if hasattr(step, 'steps') and step.steps:
            count += count_steps_recursive(step)
    return count


# Example ATML element mapping
ATML_ELEMENT_MAPPING = """
ATML Element Mapping to WATS:

ATML Element              | WATS Step Type
--------------------------|------------------------
<tr:TestGroup>            | SequenceCall
<tr:SessionAction>        | GenericStep (with icon)
<tr:Test PassFailTest>    | PassFailStep
<tr:Test StringValueTest> | StringValueStep
<tr:Test NumericLimitTest>| NumericLimitStep

TestStand StepTypes in SessionAction:
- Label, Action, Goto
- NI_Flow_If, NI_Flow_Else, NI_Flow_For, NI_Flow_While, etc.
- NI_Wait, NI_Lock, NI_Batch_Sync
- NI_OpenDatabase, NI_CloseDatabase, NI_DataOperation
- And 30+ more...
"""


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python atml_example.py <atml_file.xml>")
        print("\nSupported ATML versions:")
        print("  - ATML 2.02 (IEEE 1636.1:2006)")
        print("  - ATML 5.00 (IEEE 1636.1:2011)")
        print("  - ATML 6.01 (IEEE 1636.1:2013)")
        print("\nTestStand WATS AddOn extensions are automatically detected.")
        print(ATML_ELEMENT_MAPPING)
        sys.exit(1)
    
    atml_path = Path(sys.argv[1])
    if not atml_path.exists():
        print(f"Error: File not found: {atml_path}")
        sys.exit(1)
    
    convert_atml_file(atml_path)
