"""
Simple Test Converter - Template using ReportBuilder

This demonstrates the EASIEST way to create a converter using the ReportBuilder.
Perfect for LLMs to monitor, autocorrect, or implement new converters.

Key Benefits:
- No need to understand WATS report structure
- Just call add_step() with whatever data you have
- Automatic type inference, status calculation, grouping
- Handles messy data gracefully

LLM Instructions:
-----------------
To create a new converter:

1. Parse your file format into a simple structure
2. Create ReportBuilder with part_number and serial_number
3. For each test, call add_step() with name, value, and optional limits/unit
4. Call build() to get the report
5. Return ConverterResult.success_result()

That's it! The builder handles everything else.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# ReportBuilder - the easy way to build reports
from pywats.tools.report_builder import ReportBuilder

# Converter infrastructure
from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.context import ConverterContext
from pywats_client.converters.models import (
    ConverterSource,
    ConverterResult,
    ValidationResult,
    ArgumentDefinition,
    ArgumentType,
)


class SimpleTestConverter(FileConverter):
    """
    Example converter using ReportBuilder.
    
    This converter demonstrates the SIMPLE pattern for building reports:
    1. Parse file
    2. Create ReportBuilder
    3. Add steps
    4. Build and return
    
    Expected file format (simple tab-separated):
        # Header
        SERIAL: SN12345
        PART: PN-ABC-001
        REVISION: 1.0
        OPERATOR: JohnDoe
        
        # Tests (Name<TAB>Value<TAB>Unit<TAB>Low<TAB>High<TAB>Status)
        Voltage Test	5.02	V	4.5	5.5	PASS
        Current Test	1.25	A	1.0	2.0	PASS
        Power OK	TRUE	-	-	-	PASS
    """
    
    # =========================================================================
    # Converter Identity
    # =========================================================================
    
    @property
    def name(self) -> str:
        return "Simple Test Converter (ReportBuilder)"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Example converter using ReportBuilder for simplicity"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt", "*_test.txt", "simple_*.txt"]
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> ValidationResult:
        """Check if this file can be converted"""
        
        # Quick validation - just check for required header
        content = source.read_text()
        
        if "SERIAL:" in content and "PART:" in content:
            return ValidationResult(
                can_convert=True,
                confidence=0.9,
                message="Valid simple test file detected"
            )
        
        return ValidationResult(
            can_convert=False,
            confidence=0.0,
            message="Missing required headers (SERIAL, PART)"
        )
    
    # =========================================================================
    # Conversion
    # =========================================================================
    
    def convert(
        self,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Convert file to WATS report using ReportBuilder"""
        
        try:
            # Step 1: Parse file
            parsed_data = self._parse_file(source.read_text())
            
            # Step 2: Create ReportBuilder
            builder = ReportBuilder(
                part_number=parsed_data["header"]["part_number"],
                serial_number=parsed_data["header"]["serial_number"],
                revision=parsed_data["header"].get("revision", "A"),
                operator=parsed_data["header"].get("operator"),
                station=parsed_data["header"].get("station"),
            )
            
            # Step 3: Add all test steps
            for test in parsed_data["tests"]:
                builder.add_step(
                    name=test["name"],
                    value=test["value"],
                    unit=test.get("unit"),
                    low_limit=test.get("low_limit"),
                    high_limit=test.get("high_limit"),
                    status=test.get("status"),
                    group=test.get("group")  # Optional grouping
                )
            
            # Step 4: Build report
            report = builder.build()
            
            # Step 5: Return success
            return ConverterResult.success_result(
                report=report,
                message=f"Converted {len(parsed_data['tests'])} test steps"
            )
            
        except Exception as e:
            return ConverterResult.error_result(
                message=f"Conversion failed: {str(e)}",
                error=e
            )
    
    # =========================================================================
    # File Parsing (Format-Specific)
    # =========================================================================
    
    def _parse_file(self, content: str) -> Dict[str, Any]:
        """
        Parse the simple test file format.
        
        This is the ONLY part you need to customize for your format.
        The ReportBuilder handles everything else.
        """
        lines = content.split("\n")
        
        header = {}
        tests = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse header fields
            if ":" in line and not "\t" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Map to standard names
                if key == "serial":
                    header["serial_number"] = value
                elif key == "part":
                    header["part_number"] = value
                elif key == "revision" or key == "rev":
                    header["revision"] = value
                elif key == "operator":
                    header["operator"] = value
                elif key == "station":
                    header["station"] = value
            
            # Parse test lines (tab-separated)
            elif "\t" in line:
                parts = line.split("\t")
                
                if len(parts) >= 2:
                    test = {
                        "name": parts[0].strip(),
                        "value": self._parse_value(parts[1].strip()),
                    }
                    
                    # Optional fields
                    if len(parts) > 2 and parts[2].strip() not in ["-", ""]:
                        test["unit"] = parts[2].strip()
                    
                    if len(parts) > 3 and parts[3].strip() not in ["-", ""]:
                        test["low_limit"] = self._parse_number(parts[3].strip())
                    
                    if len(parts) > 4 and parts[4].strip() not in ["-", ""]:
                        test["high_limit"] = self._parse_number(parts[4].strip())
                    
                    if len(parts) > 5 and parts[5].strip() not in ["-", ""]:
                        test["status"] = parts[5].strip()
                    
                    tests.append(test)
        
        return {
            "header": header,
            "tests": tests
        }
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse value - handles bool, numeric, or string"""
        
        # Boolean
        if value_str.upper() in ["TRUE", "FALSE", "PASS", "FAIL"]:
            return value_str.upper() in ["TRUE", "PASS"]
        
        # Numeric
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # String
        return value_str
    
    def _parse_number(self, num_str: str) -> Optional[float]:
        """Parse numeric string to float"""
        try:
            return float(num_str)
        except (ValueError, TypeError):
            return None


# =============================================================================
# LLM TEMPLATE: Use this as a starting point for new converters
# =============================================================================

"""
LLM Instructions for Creating New Converters:
----------------------------------------------

1. Copy this file as a template
2. Update the class name and metadata (name, version, description, file_patterns)
3. Customize _parse_file() for your file format
4. Everything else stays the same!

Example for CSV format:
```python
def _parse_file(self, content: str) -> Dict[str, Any]:
    import csv
    lines = content.split('\\n')
    reader = csv.DictReader(lines)
    
    header = {
        "part_number": "PN-FROM-CSV",  # Extract from CSV
        "serial_number": "SN-FROM-CSV"
    }
    
    tests = []
    for row in reader:
        tests.append({
            "name": row["test_name"],
            "value": float(row["value"]),
            "unit": row.get("unit"),
            "low_limit": float(row.get("low_limit")) if row.get("low_limit") else None,
            "high_limit": float(row.get("high_limit")) if row.get("high_limit") else None,
        })
    
    return {"header": header, "tests": tests}
```

Example for JSON format:
```python
def _parse_file(self, content: str) -> Dict[str, Any]:
    import json
    data = json.loads(content)
    
    header = {
        "part_number": data["pn"],
        "serial_number": data["sn"],
        "revision": data.get("rev", "A")
    }
    
    tests = []
    for test_name, test_data in data["tests"].items():
        tests.append({
            "name": test_name,
            "value": test_data["value"],
            "unit": test_data.get("unit"),
            "low_limit": test_data.get("low_limit"),
            "high_limit": test_data.get("high_limit"),
        })
    
    return {"header": header, "tests": tests}
```

Example for XML format:
```python
def _parse_file(self, content: str) -> Dict[str, Any]:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    
    header = {
        "part_number": root.find(".//PartNumber").text,
        "serial_number": root.find(".//SerialNumber").text
    }
    
    tests = []
    for test_elem in root.findall(".//Test"):
        tests.append({
            "name": test_elem.get("name"),
            "value": float(test_elem.find("Value").text),
            "unit": test_elem.get("unit"),
        })
    
    return {"header": header, "tests": tests}
```

That's it! The ReportBuilder handles:
- Type inference (bool, numeric, string, multi-value)
- Status calculation (pass/fail from limits)
- Comparison operator selection
- Sequence grouping (if you provide 'group' field)
- Overall result calculation
- Proper WATS report structure
"""
