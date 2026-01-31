# Converter Examples

This folder contains example converters demonstrating how to build custom converters for the PyWATS client.

## Reference Implementation

- **[converter_template.py](converter_template.py)** - Comprehensive reference implementation with detailed comments explaining the correct patterns for building WATS reports using the UUTReport model API.

## Format Examples

- **[csv_converter.py](csv_converter.py)** - CSV file converter example
- **[json_converter.py](json_converter.py)** - JSON file converter example  
- **[xml_converter.py](xml_converter.py)** - XML file converter example
- **[simple_builder_converter.py](simple_builder_converter.py)** - Simplified report building example

## Built-in Converters

For production use, these converters are included with the client package:

**WATS Standard Formats:**
- `WATSStandardTextConverter` - Tab-delimited text format
- `WATSStandardJsonConverter` - WATS JSON format (WSJF)
- `WATSStandardXMLConverter` - WATS XML format (WSXF/WRML)

**Test Equipment:**
- `SeicaXMLConverter` - Seica Flying Probe
- `TeradyneICTConverter` - Teradyne i3070 ICT
- `TeradyneSpectrumICTConverter` - Teradyne Spectrum ICT
- `KlippelConverter` - Klippel audio/acoustic test
- `SPEAConverter` - SPEA automated test equipment
- `XJTAGConverter` - XJTAG boundary scan

**Special:**
- `AIConverter` - Auto-selection converter that detects file type

## Creating Custom Converters

```python
from pywats_client.converters import FileConverter, ConverterResult, PostProcessAction
from pywats.domains.report.report_models import UUTReport

class MyConverter(FileConverter):
    @property
    def name(self) -> str:
        return "My Custom Converter"
    
    @property
    def file_patterns(self) -> list:
        return ["*.myext"]
    
    def convert(self, source, context) -> ConverterResult:
        # Parse the file
        with open(source.path, 'r') as f:
            data = f.read()
        
        # Build report using UUTReport model
        report = UUTReport(
            part_number="PN-001",
            serial_number="SN-001",
            operation_code="TEST",
            result="P"
        )
        
        # Add test steps
        root = report.get_root_sequence_call()
        root.add_numeric_limit_step(
            name="Voltage",
            value=3.3,
            low_limit=3.0,
            high_limit=3.6,
            unit="V"
        )
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE
        )
```

## See Also

- [LLM Converter Guide](../../docs/guides/llm-converter-guide.md) - Quick reference for implementing converters
- [Client Service Guide](../../docs/installation/client.md) - Installing and configuring converters
