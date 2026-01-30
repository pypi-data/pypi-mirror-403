# ReportBuilder - Simple Report Building for pyWATS

## Overview

The **ReportBuilder** is a forgiving, LLM-friendly tool for creating WATS test reports with minimal complexity. It's designed for:

- **Converter scripts** that parse test data from various formats
- **LLM-generated code** that needs to build reports without deep understanding
- **Quick prototyping** where you don't want to think about report structure
- **Situations with messy data** that needs graceful handling

## Philosophy

- **If it can be inferred, it will be** - Step types, comparison operators, and statuses are automatically determined
- **If it's missing, use sensible defaults** - You only specify what you have
- **Never fail on missing metadata** - Do the best with what's provided
- **Support both flat and hierarchical structures** - Automatically organize by groups

## Quick Start

### Simple Example

```python
from pywats.tools import ReportBuilder

# Create builder
builder = ReportBuilder(
    part_number="MODULE-100",
    serial_number="MOD-2025-001"
)

# Add steps - it figures out the types
builder.add_step("Voltage Test", 5.02, unit="V", low_limit=4.5, high_limit=5.5)
builder.add_step("Power OK", True)
builder.add_step("Serial Read", "ABC123")

# Build and submit
report = builder.build()
api.report.submit_report(report)
```

### One-Liner with quick_report()

```python
from pywats.tools import quick_report

steps = [
    {"name": "Voltage", "value": 5.0, "unit": "V", "low_limit": 4.5, "high_limit": 5.5},
    {"name": "Current", "value": 1.2, "unit": "A"},
    {"name": "Status", "value": True}
]

report = quick_report("PN-001", "SN-001", steps)
api.report.submit_report(report)
```

## Key Features

### 1. Automatic Type Inference

The builder automatically determines the correct step type based on your data:

```python
builder.add_step("Boolean Test", True)           # → Boolean step
builder.add_step("Numeric Test", 5.0)           # → Numeric step
builder.add_step("String Test", "ABC")          # → String step
builder.add_step("Multi-Numeric", [1, 2, 3])    # → Multi-numeric step
```

### 2. Smart Status Calculation

Status is automatically calculated from limits unless you override it:

```python
# Auto-calculated as "P" (in range)
builder.add_step("Test1", 5.0, low_limit=4.0, high_limit=6.0)

# Auto-calculated as "F" (out of range)
builder.add_step("Test2", 10.0, low_limit=4.0, high_limit=6.0)

# Manual override
builder.add_step("Test3", 5.0, status="F")  # Force fail
```

### 3. Flexible Data Handling

Works with messy, real-world data:

```python
# Limits as strings (auto-converted)
builder.add_step("Test", "5.02", low_limit="4.5", high_limit="5.5")

# Various status formats
builder.add_step("Test1", 5.0, status="PASS")
builder.add_step("Test2", 5.0, status="P")
builder.add_step("Test3", 5.0, status="Passed")
builder.add_step("Test4", 5.0, status=True)

# Boolean from string
builder.add_step("Test", "TRUE")  # Converts to boolean
```

### 4. Automatic Grouping/Sequences

Create hierarchical reports by specifying groups:

```python
builder = ReportBuilder("PN-001", "SN-001")

# Power tests group
builder.add_step("VCC", 3.3, unit="V", group="Power Tests")
builder.add_step("VDD", 1.8, unit="V", group="Power Tests")

# Communication tests group
builder.add_step("UART", True, group="Communication")
builder.add_step("I2C", True, group="Communication")

# Build creates sequences automatically
report = builder.build()
```

Result:
```
MainSequence
├── Power Tests (sequence)
│   ├── VCC
│   └── VDD
└── Communication (sequence)
    ├── UART
    └── I2C
```

## API Reference

### ReportBuilder

```python
class ReportBuilder:
    def __init__(
        self,
        part_number: str,
        serial_number: str,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional[str] = None,
        location: Optional[str] = None,
        process_code: int = 10,
        result: Optional[str] = None,
        start_time: Optional[datetime] = None,
        purpose: Optional[str] = None
    )
```

**Parameters:**
- `part_number` (required): Part number
- `serial_number` (required): Serial number
- `revision`: Revision (default: "A")
- `operator`: Operator name (default: "Converter")
- `station`: Station name
- `location`: Location
- `process_code`: Operation type code (default: 10 = SW Debug)
- `result`: Overall result "P" or "F" (auto-calculated if None)
- `start_time`: Start time (defaults to now)
- `purpose`: Test purpose

### add_step()

```python
def add_step(
    self,
    name: str,
    value: Any = None,
    unit: Optional[str] = None,
    low_limit: Optional[Union[float, str]] = None,
    high_limit: Optional[Union[float, str]] = None,
    status: Optional[str] = None,
    group: Optional[str] = None,
    comp_op: Optional[Union[CompOp, str]] = None,
    **kwargs
) -> "ReportBuilder"
```

**Type Inference:**
- `bool` / `"TRUE"` / `"FALSE"` / `"PASS"` / `"FAIL"` → Boolean step
- `float` / `int` with limits → Numeric limit test
- `float` / `int` without limits → Numeric log
- `str` → String step
- `list[float]` / `list[int]` → Multi-numeric step
- `list[bool]` → Multi-boolean step
- `list[str]` → Multi-string step

**Parameters:**
- `name` (required): Step name
- `value`: Measured value (can be anything)
- `unit`: Unit of measurement (e.g., "V", "A", "°C")
- `low_limit`: Lower limit (for numeric tests)
- `high_limit`: Upper limit (for numeric tests)
- `status`: Status override ("P", "F", "Passed", "Failed", etc.)
- `group`: Group/sequence name (creates hierarchy)
- `comp_op`: Comparison operator (auto-inferred if not specified)
- `**kwargs`: Additional metadata stored for debugging

**Returns:** Self (for method chaining)

### add_step_from_dict()

```python
def add_step_from_dict(
    self,
    data: Dict[str, Any],
    name_key: str = "name",
    value_key: str = "value",
    unit_key: str = "unit",
    low_limit_key: str = "low_limit",
    high_limit_key: str = "high_limit",
    status_key: str = "status",
    group_key: str = "group"
) -> "ReportBuilder"
```

Add a step from a dictionary with flexible key mapping. Automatically tries common variations:
- name: `name`, `Name`, `TestName`, `test_name`, `Step`
- value: `value`, `Value`, `MeasuredValue`, `Result`
- unit: `unit`, `Unit`, `Units`, `UOM`
- low_limit: `low_limit`, `LowLimit`, `Low`, `MinLimit`, `min`
- high_limit: `high_limit`, `HighLimit`, `High`, `MaxLimit`, `max`
- status: `status`, `Status`, `Result`, `Pass`
- group: `group`, `Group`, `Sequence`, `TestGroup`

### add_misc_info()

```python
def add_misc_info(
    self,
    description: str,
    text: str
) -> "ReportBuilder"
```

Add searchable metadata to the report header.

### add_sub_unit()

```python
def add_sub_unit(
    self,
    part_type: str,
    part_number: Optional[str] = None,
    serial_number: Optional[str] = None,
    revision: Optional[str] = None
) -> "ReportBuilder"
```

Add a sub-unit (component) to the report.

### build()

```python
def build(self) -> UUTReport
```

Build the final UUTReport. This method:
1. Creates UUTReport with header info
2. Groups steps by sequence (if groups specified)
3. Adds all steps in correct order
4. Sets overall result based on step statuses
5. Adds misc info and sub-units

**Returns:** UUTReport ready to submit

### quick_report()

```python
def quick_report(
    part_number: str,
    serial_number: str,
    steps: List[Dict[str, Any]],
    **kwargs
) -> UUTReport
```

Create a report from a list of step dictionaries in one call. Perfect for LLM-generated code.

## Usage Examples

### Example 1: Simple Converter

```python
from pywats.tools import ReportBuilder

def convert_my_format(file_path):
    # Parse your file format
    data = parse_file(file_path)
    
    # Create builder
    builder = ReportBuilder(
        part_number=data["part_number"],
        serial_number=data["serial_number"]
    )
    
    # Add all tests
    for test in data["tests"]:
        builder.add_step(
            name=test["name"],
            value=test["value"],
            unit=test.get("unit"),
            low_limit=test.get("low_limit"),
            high_limit=test.get("high_limit")
        )
    
    # Done!
    return builder.build()
```

### Example 2: From CSV Data

```python
import csv
from pywats.tools import ReportBuilder

def convert_csv(csv_file):
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        
        builder = ReportBuilder("PN-FROM-CSV", "SN-FROM-CSV")
        
        for row in reader:
            builder.add_step_from_dict(
                row,
                name_key="TestName",
                value_key="MeasuredValue",
                unit_key="Unit",
                low_limit_key="LowLimit",
                high_limit_key="HighLimit"
            )
        
        return builder.build()
```

### Example 3: With Metadata

```python
builder = ReportBuilder(
    part_number="ASSEMBLY-500",
    serial_number="ASM-2025-0123",
    operator="Production Line 3",
    station="Final Test"
)

# Add tests
builder.add_step("Visual Inspection", "PASS")
builder.add_step("Voltage", 12.05, unit="V", low_limit=11.5, high_limit=12.5)

# Add metadata
builder.add_misc_info("Batch Number", "BATCH-2025-Q1-042")
builder.add_misc_info("Temperature", "22°C")

# Add components
builder.add_sub_unit(
    part_type="Power Supply",
    part_number="PSU-24V-100W",
    serial_number="PSU-001"
)

report = builder.build()
```

### Example 4: ICT Converter

```python
def convert_ict_data(ict_file):
    data = parse_ict_file(ict_file)
    
    builder = ReportBuilder(
        part_number=data["pn"],
        serial_number=data["sn"],
        operator=data["operator"]
    )
    
    # Group by test type
    for resistance in data["resistances"]:
        builder.add_step(
            name=resistance["designator"],
            value=resistance["measured"],
            unit="Ω",
            low_limit=resistance["min"],
            high_limit=resistance["max"],
            group="Resistance Tests"
        )
    
    for capacitor in data["capacitors"]:
        builder.add_step(
            name=capacitor["designator"],
            value=capacitor["measured"],
            unit="µF",
            low_limit=capacitor["min"],
            high_limit=capacitor["max"],
            group="Capacitance Tests"
        )
    
    return builder.build()
```

## LLM Integration Guide

### For LLM Monitoring/Autocorrection

When monitoring converter code, check for these patterns:

✅ **Good Pattern:**
```python
builder = ReportBuilder(pn, sn)
builder.add_step("Test", value, unit="V", low_limit=4.5, high_limit=5.5)
report = builder.build()
```

❌ **Avoid Direct UUTReport Construction:**
```python
# Too complex for LLMs to get right
report = UUTReport(pn=pn, sn=sn, ...)
root = report.get_root_sequence_call()
root.add_numeric_step(...)  # Easy to mess up parameters
```

### For LLM Implementation of New Converters

**Template for LLMs:**

```python
from pywats.tools import ReportBuilder

def convert_my_format(file_path):
    # 1. Parse file (this is the only custom part)
    data = parse_your_format(file_path)
    
    # 2. Create builder
    builder = ReportBuilder(
        part_number=data["part_number"],
        serial_number=data["serial_number"]
    )
    
    # 3. Add steps (one line per test)
    for test in data["tests"]:
        builder.add_step(
            name=test["name"],
            value=test["value"],
            unit=test.get("unit"),
            low_limit=test.get("low_limit"),
            high_limit=test.get("high_limit"),
            group=test.get("group")  # Optional
        )
    
    # 4. Build and return
    return builder.build()
```

**LLM should only customize:** The `parse_your_format()` function to extract data from the specific file format.

**Everything else is standard.**

## Advanced Features

### Multi-Value Steps

```python
# Multi-numeric (array of numbers)
builder.add_step(
    "Calibration Points",
    [1.2, 1.3, 1.1, 1.25, 1.15],
    unit="mV",
    low_limit=1.0,
    high_limit=1.5
)

# Multi-boolean (array of pass/fail)
builder.add_step("Pin Tests", [True, True, False, True])

# Multi-string (array of strings)
builder.add_step("Serial Numbers", ["ABC", "DEF", "GHI"])
```

### Custom Comparison Operators

```python
from pywats.domains.report.report_models.uut.steps.comp_operator import CompOp

builder.add_step(
    "Exact Value",
    5.0,
    low_limit=5.0,
    comp_op=CompOp.EQ  # Must equal exactly
)

builder.add_step(
    "Greater Than",
    10.0,
    low_limit=5.0,
    comp_op=CompOp.GT  # Must be > 5.0 (not >=)
)
```

### Failed Reports

```python
builder = ReportBuilder("PN", "SN")

builder.add_step("Test1", 5.0, low_limit=4.0, high_limit=6.0)  # Pass
builder.add_step("Test2", 10.0, low_limit=4.0, high_limit=6.0)  # FAIL

report = builder.build()
# report.result will be "F" because Test2 failed
```

## Comparison with Direct API

### Before (Complex):

```python
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.steps.comp_operator import CompOp

report = UUTReport(
    pn="PN-001",
    sn="SN-001",
    rev="A",
    process_code=10,
    station_name="Station1",
    result="P",
    start=datetime.now()
)

root = report.get_root_sequence_call()

# Need to know exact parameters, types, and comparison operators
root.add_numeric_step(
    name="Voltage",
    value=5.02,
    unit="V",
    comp_op=CompOp.GELE,
    low_limit=4.5,
    high_limit=5.5,
    status="P"
)
```

### After (Simple):

```python
from pywats.tools import ReportBuilder

builder = ReportBuilder("PN-001", "SN-001")

# Just provide data - everything else is inferred
builder.add_step("Voltage", 5.02, unit="V", low_limit=4.5, high_limit=5.5)

report = builder.build()
```

## Best Practices

1. **Use ReportBuilder for converters** - It handles edge cases better than manual construction
2. **Let it infer types** - Don't overthink numeric vs string vs boolean
3. **Use groups for organization** - Makes reports easier to read in WATS
4. **Add misc_info for metadata** - Searchable in WATS
5. **Let status auto-calculate** - Only override if you have explicit pass/fail from source

## Troubleshooting

### Problem: Status always "P" even with failures

**Solution:** Make sure limits are numeric (not strings), or provide explicit status:

```python
# Auto-fails if out of range
builder.add_step("Test", 10.0, low_limit=4.0, high_limit=6.0)

# Or explicit
builder.add_step("Test", 10.0, status="F")
```

### Problem: Wrong step type created

**Solution:** Ensure value is correct Python type:

```python
# Boolean
builder.add_step("Test", True)  # ✓
builder.add_step("Test", "true")  # ✗ (becomes string step)

# Numeric
builder.add_step("Test", 5.0)  # ✓
builder.add_step("Test", "5.0")  # ? (auto-converted, but better to convert yourself)
```

### Problem: Can't find data in dictionary

**Solution:** Use `add_step_from_dict()` with explicit key names:

```python
builder.add_step_from_dict(
    data,
    name_key="TestName",  # Specify exact keys
    value_key="MeasuredValue"
)
```

## See Also

- [Report Module Documentation](../REPORT.md)
- [Converter Template](../../converters/converter_template.py)
- [Simple Converter Example](../../converters/simple_builder_converter.py)
- [Examples](../../examples/report/report_builder_examples.py)
