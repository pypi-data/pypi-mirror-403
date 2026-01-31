# LLM Quick Reference - ReportBuilder for pyWATS

## For LLMs Implementing Converters

This is your cheat sheet for creating pyWATS converters. **You only need to customize the parsing logic** - everything else is standard.

---

## Standard Converter Template

```python
from pywats.tools import ReportBuilder
from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.models import (
    ConverterSource, ConverterResult, ValidationResult
)

class YourConverter(FileConverter):
    """Your converter description"""
    
    @property
    def name(self) -> str:
        return "Your Converter Name"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.yourext"]
    
    def convert(self, source: ConverterSource, context) -> ConverterResult:
        try:
            # STEP 1: Parse file (ONLY CUSTOM PART)
            data = self._parse_file(source.read_text())
            
            # STEP 2: Create builder (STANDARD)
            builder = ReportBuilder(
                part_number=data["part_number"],
                serial_number=data["serial_number"]
            )
            
            # STEP 3: Add steps (STANDARD)
            for test in data["tests"]:
                builder.add_step(
                    name=test["name"],
                    value=test["value"],
                    unit=test.get("unit"),
                    low_limit=test.get("low_limit"),
                    high_limit=test.get("high_limit"),
                    group=test.get("group")
                )
            
            # STEP 4: Build (STANDARD)
            return ConverterResult.success_result(
                report=builder.build()
            )
        except Exception as e:
            return ConverterResult.error_result(str(e), e)
    
    def _parse_file(self, content: str) -> dict:
        """
        CUSTOMIZE THIS METHOD FOR YOUR FORMAT
        
        Must return:
        {
            "part_number": "PN-001",
            "serial_number": "SN-001",
            "tests": [
                {
                    "name": "Test Name",
                    "value": 5.0,          # Can be: float, int, bool, str, list
                    "unit": "V",           # Optional
                    "low_limit": 4.5,      # Optional
                    "high_limit": 5.5,     # Optional
                    "group": "Power Tests" # Optional (creates sequences)
                },
                ...
            ]
        }
        """
        # YOUR PARSING LOGIC HERE
        pass
```

---

## Quick Add Step Reference

### Basic Patterns

```python
# Numeric test with limits
builder.add_step("Voltage", 5.0, unit="V", low_limit=4.5, high_limit=5.5)

# Numeric test without limits (LOG only)
builder.add_step("Temperature", 25.3, unit="C")

# Boolean test
builder.add_step("Power OK", True)

# String test
builder.add_step("Serial Number", "ABC123")

# Multi-value numeric
builder.add_step("Calibration", [1.2, 1.3, 1.1], unit="mV")

# With grouping (creates sequence)
builder.add_step("VCC", 3.3, unit="V", group="Power Tests")
```

### Type Inference Rules

| Value Type | Result |
|------------|--------|
| `True` or `False` | Boolean step |
| `5.0` or `100` | Numeric step |
| `"ABC"` | String step |
| `[1.0, 2.0, 3.0]` | Multi-numeric step |
| `[True, False]` | Multi-boolean step |
| `["A", "B"]` | Multi-string step |

### Status Calculation

```python
# In range → Pass (auto)
builder.add_step("Test", 5.0, low_limit=4.0, high_limit=6.0)

# Out of range → Fail (auto)
builder.add_step("Test", 10.0, low_limit=4.0, high_limit=6.0)

# Manual override
builder.add_step("Test", 5.0, status="F")  # Force fail
```

---

## Parsing Examples

### CSV Format

```python
def _parse_file(self, content: str) -> dict:
    import csv
    lines = content.strip().split('\n')
    reader = csv.DictReader(lines)
    
    tests = []
    header = {}
    
    for i, row in enumerate(reader):
        if i == 0:  # First row has header info
            header = {
                "part_number": row.get("pn", "PN-UNKNOWN"),
                "serial_number": row.get("sn", "SN-UNKNOWN")
            }
        
        tests.append({
            "name": row["test_name"],
            "value": float(row["value"]) if row["value"].replace('.','').isdigit() else row["value"],
            "unit": row.get("unit"),
            "low_limit": float(row["low_limit"]) if row.get("low_limit") else None,
            "high_limit": float(row["high_limit"]) if row.get("high_limit") else None
        })
    
    return {"part_number": header["part_number"], "serial_number": header["serial_number"], "tests": tests}
```

### JSON Format

```python
def _parse_file(self, content: str) -> dict:
    import json
    data = json.loads(content)
    
    tests = []
    for test_name, test_data in data["tests"].items():
        tests.append({
            "name": test_name,
            "value": test_data["value"],
            "unit": test_data.get("unit"),
            "low_limit": test_data.get("low_limit"),
            "high_limit": test_data.get("high_limit")
        })
    
    return {
        "part_number": data["pn"],
        "serial_number": data["sn"],
        "tests": tests
    }
```

### XML Format

```python
def _parse_file(self, content: str) -> dict:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    
    tests = []
    for test in root.findall(".//Test"):
        tests.append({
            "name": test.get("name"),
            "value": float(test.find("Value").text),
            "unit": test.get("unit"),
            "low_limit": float(test.find("LowLimit").text) if test.find("LowLimit") is not None else None,
            "high_limit": float(test.find("HighLimit").text) if test.find("HighLimit") is not None else None
        })
    
    return {
        "part_number": root.find(".//PartNumber").text,
        "serial_number": root.find(".//SerialNumber").text,
        "tests": tests
    }
```

### Tab-Separated Text

```python
def _parse_file(self, content: str) -> dict:
    lines = content.split('\n')
    
    header = {}
    tests = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Header lines (KEY: VALUE)
        if ':' in line and '\t' not in line:
            key, value = line.split(':', 1)
            if key.strip().upper() == 'SERIAL':
                header['serial_number'] = value.strip()
            elif key.strip().upper() == 'PART':
                header['part_number'] = value.strip()
        
        # Test lines (tab-separated)
        elif '\t' in line:
            parts = line.split('\t')
            tests.append({
                "name": parts[0],
                "value": float(parts[1]) if parts[1].replace('.','').replace('-','').isdigit() else parts[1],
                "unit": parts[2] if len(parts) > 2 and parts[2] != '-' else None,
                "low_limit": float(parts[3]) if len(parts) > 3 and parts[3] != '-' else None,
                "high_limit": float(parts[4]) if len(parts) > 4 and parts[4] != '-' else None
            })
    
    return {"part_number": header.get("part_number", "UNKNOWN"), "serial_number": header.get("serial_number", "UNKNOWN"), "tests": tests}
```

---

## Common Mistakes to Avoid

### ❌ DON'T: Build reports manually
```python
report = UUTReport(...)
root = report.get_root_sequence_call()
root.add_numeric_step(...)  # Too many parameters, easy to mess up
```

### ✅ DO: Use ReportBuilder
```python
builder = ReportBuilder(pn, sn)
builder.add_step(name, value, unit, low_limit, high_limit)
report = builder.build()
```

### ❌ DON'T: Calculate status manually
```python
if value >= low_limit and value <= high_limit:
    status = "P"
else:
    status = "F"
builder.add_step(name, value, status=status)
```

### ✅ DO: Let the builder calculate it
```python
builder.add_step(name, value, low_limit=low_limit, high_limit=high_limit)
# Status calculated automatically
```

### ❌ DON'T: Manually create sequences
```python
root = report.get_root_sequence_call()
power_seq = root.add_sequence_call("Power Tests")
power_seq.add_numeric_step(...)
```

### ✅ DO: Use group parameter
```python
builder.add_step("VCC", 3.3, group="Power Tests")
builder.add_step("VDD", 1.8, group="Power Tests")
# Sequences created automatically
```

---

## Validation Checklist

Before submitting your converter code, verify:

- [ ] Uses `from pywats.tools import ReportBuilder`
- [ ] Only `_parse_file()` method contains custom logic
- [ ] Returns dict with `part_number`, `serial_number`, `tests`
- [ ] Each test has `name` and `value` (minimum)
- [ ] Uses `builder.add_step()` not manual `UUTReport` construction
- [ ] Lets builder infer types, operators, status
- [ ] Returns `ConverterResult.success_result(report=builder.build())`
- [ ] Has try/except with `ConverterResult.error_result()` on exception

---

## Complete Minimal Example

```python
from pywats.tools import ReportBuilder
from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.models import ConverterSource, ConverterResult

class MinimalConverter(FileConverter):
    @property
    def name(self) -> str:
        return "Minimal Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt"]
    
    def convert(self, source: ConverterSource, context) -> ConverterResult:
        try:
            # Parse
            lines = source.read_text().split('\n')
            pn = lines[0].split(':')[1].strip()
            sn = lines[1].split(':')[1].strip()
            
            # Build
            builder = ReportBuilder(pn, sn)
            for line in lines[2:]:
                if '\t' in line:
                    name, value = line.split('\t')
                    builder.add_step(name, float(value))
            
            # Return
            return ConverterResult.success_result(report=builder.build())
        except Exception as e:
            return ConverterResult.error_result(str(e), e)
```

That's it! **Only 20 lines of actual code.**

---

## Need Help?

- **Documentation:** See `docs/usage/REPORT_BUILDER.md`
- **Examples:** See `examples/report/report_builder_examples.py`
- **Template:** See `converters/simple_builder_converter.py`
