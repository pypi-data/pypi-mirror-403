"""
ReportBuilder Examples

Demonstrates various ways to use the ReportBuilder for creating test reports.
"""

from datetime import datetime
from pywats.tools.report_builder import ReportBuilder, quick_report

# =============================================================================
# Example 1: Simple Flat Report
# =============================================================================

def example_simple_report():
    """Simplest possible report - just add steps"""
    
    builder = ReportBuilder(
        part_number="MODULE-100",
        serial_number="MOD-2025-001"
    )
    
    # Add whatever steps you have
    builder.add_step("Voltage Test", 5.02, unit="V", low_limit=4.5, high_limit=5.5)
    builder.add_step("Current Test", 1.25, unit="A")
    builder.add_step("Power OK", True)
    builder.add_step("Serial Read", "ABC123")
    
    report = builder.build()
    return report


# =============================================================================
# Example 2: Grouped/Hierarchical Report
# =============================================================================

def example_grouped_report():
    """Report with logical groupings using the 'group' parameter"""
    
    builder = ReportBuilder(
        part_number="PCB-MAIN-001",
        serial_number="PCB-2025-0042",
        operator="Jane Doe",
        station="FCT-STATION-02"
    )
    
    # Power tests group
    builder.add_step("VCC Voltage", 3.31, unit="V", low_limit=3.0, high_limit=3.6, group="Power Tests")
    builder.add_step("VDD Voltage", 1.82, unit="V", low_limit=1.7, high_limit=1.9, group="Power Tests")
    builder.add_step("Power OK", True, group="Power Tests")
    
    # Communication tests group
    builder.add_step("UART Test", True, group="Communication")
    builder.add_step("I2C Test", True, group="Communication")
    builder.add_step("SPI Test", True, group="Communication")
    
    # Calibration group
    builder.add_step("Offset Cal", [1.2, 1.3, 1.1], unit="mV", group="Calibration")
    builder.add_step("Gain Cal", [0.98, 1.01, 0.99], group="Calibration")
    
    report = builder.build()
    return report


# =============================================================================
# Example 3: From Dictionary (CSV/JSON Converter Pattern)
# =============================================================================

def example_from_dicts():
    """Build report from parsed data structures (CSV, JSON, etc.)"""
    
    # Simulated CSV parsing result
    test_results = [
        {
            "TestName": "Voltage Test",
            "MeasuredValue": "5.02",
            "Unit": "V",
            "LowLimit": "4.5",
            "HighLimit": "5.5",
            "Result": "PASS",
            "Group": "Power Tests"
        },
        {
            "TestName": "Current Test",
            "MeasuredValue": "1.25",
            "Unit": "A",
            "LowLimit": "1.0",
            "HighLimit": "2.0",
            "Result": "PASS",
            "Group": "Power Tests"
        },
        {
            "TestName": "Temperature",
            "MeasuredValue": "25.3",
            "Unit": "C",
            "Result": "PASS"
        }
    ]
    
    builder = ReportBuilder("PN-TEST-001", "SN-TEST-001")
    
    for test in test_results:
        builder.add_step_from_dict(
            test,
            name_key="TestName",
            value_key="MeasuredValue",
            unit_key="Unit",
            low_limit_key="LowLimit",
            high_limit_key="HighLimit",
            status_key="Result",
            group_key="Group"
        )
    
    report = builder.build()
    return report


# =============================================================================
# Example 4: Quick Report (One-Liner)
# =============================================================================

def example_quick_report():
    """Use the quick_report helper for simplest case"""
    
    steps = [
        {"name": "Voltage", "value": 5.0, "unit": "V", "low_limit": 4.5, "high_limit": 5.5},
        {"name": "Current", "value": 1.2, "unit": "A"},
        {"name": "Status", "value": True},
        {"name": "Serial", "value": "ABC123"}
    ]
    
    report = quick_report(
        part_number="WIDGET-001",
        serial_number="W-2025-001",
        steps=steps,
        operator="Quick Test",
        station="Auto-Station"
    )
    
    return report


# =============================================================================
# Example 5: With Metadata (Misc Info & Sub-Units)
# =============================================================================

def example_with_metadata():
    """Report with additional metadata"""
    
    builder = ReportBuilder(
        part_number="ASSEMBLY-500",
        serial_number="ASM-2025-0123",
        revision="C",
        operator="Production Line 3",
        station="Final Test Station",
        location="Factory Floor",
        process_code=100  # Final Acceptance Test
    )
    
    # Add test steps
    builder.add_step("Visual Inspection", "PASS")
    builder.add_step("Functional Test", True)
    builder.add_step("Output Voltage", 12.05, unit="V", low_limit=11.5, high_limit=12.5)
    
    # Add misc info (searchable metadata)
    builder.add_misc_info("Batch Number", "BATCH-2025-Q1-042")
    builder.add_misc_info("Ambient Temperature", "22°C")
    builder.add_misc_info("Humidity", "45%")
    builder.add_misc_info("Inspector", "John Smith")
    
    # Add sub-units (components)
    builder.add_sub_unit(
        part_type="Power Supply Module",
        part_number="PSU-24V-100W",
        serial_number="PSU-20250124-0042"
    )
    builder.add_sub_unit(
        part_type="Control Board",
        part_number="CTRL-MAIN-REV-D",
        serial_number="CTRL-20250120-0156"
    )
    
    report = builder.build()
    return report


# =============================================================================
# Example 6: Messy Data Handling (Forgiving Parsing)
# =============================================================================

def example_messy_data():
    """Demonstrates how the builder handles messy/inconsistent data"""
    
    builder = ReportBuilder("TEST-PN", "TEST-SN")
    
    # Different status formats - all work
    builder.add_step("Test 1", 5.0, status="PASS")
    builder.add_step("Test 2", 5.0, status="P")
    builder.add_step("Test 3", 5.0, status="Passed")
    builder.add_step("Test 4", 5.0, status=True)
    builder.add_step("Test 5", 5.0, status="1")
    
    # Limits as strings (auto-converted)
    builder.add_step("Test 6", "5.02", unit="V", low_limit="4.5", high_limit="5.5")
    
    # Boolean from string
    builder.add_step("Test 7", "TRUE")
    builder.add_step("Test 8", "PASS")
    
    # Missing values - uses sensible defaults
    builder.add_step("Test 9", 100)  # No limits = LOG, auto-pass
    builder.add_step("Test 10")  # No value = string step with "N/A"
    
    # Auto-infers status from limits
    builder.add_step("Auto Pass", 5.0, low_limit=4.0, high_limit=6.0)  # In range = pass
    builder.add_step("Auto Fail", 10.0, low_limit=4.0, high_limit=6.0)  # Out of range = fail
    
    report = builder.build()
    return report


# =============================================================================
# Example 7: LLM-Friendly Usage (Minimal Thinking Required)
# =============================================================================

def example_llm_usage():
    """
    Example showing how an LLM or converter script can use this
    without understanding WATS report structure.
    """
    
    # LLM just needs to know: part number, serial, and add_step
    builder = ReportBuilder("PART-NUM", "SERIAL-NUM")
    
    # LLM can throw any data at it
    builder.add_step("Some Test", 42.0)  # Works
    builder.add_step("Another Test", True)  # Works
    builder.add_step("String Test", "Hello")  # Works
    builder.add_step("Multi Values", [1, 2, 3, 4, 5])  # Works
    builder.add_step("With Limits", 5.0, low_limit=4.0, high_limit=6.0)  # Works
    builder.add_step("Grouped", 100, group="MyGroup")  # Works
    
    # Build and done
    report = builder.build()
    return report


# =============================================================================
# Example 8: Converter Pattern (ICT Data)
# =============================================================================

def example_ict_converter():
    """
    Realistic example: converting ICT (In-Circuit Test) data.
    Shows how a converter would use the builder.
    """
    
    # Simulated ICT test data
    ict_data = {
        "header": {
            "part_number": "PCB-ICT-001",
            "serial_number": "ICT-20250124-0042",
            "revision": "B",
            "operator": "ICT Station 3",
            "test_date": "2025-01-24T14:30:00",
            "result": "PASS"
        },
        "tests": [
            # Resistance tests
            {"group": "Resistance", "name": "R1", "value": 1000.5, "unit": "Ω", "min": 900, "max": 1100},
            {"group": "Resistance", "name": "R2", "value": 4702.3, "unit": "Ω", "min": 4500, "max": 5000},
            
            # Capacitance tests
            {"group": "Capacitance", "name": "C1", "value": 10.2, "unit": "µF", "min": 9.0, "max": 11.0},
            {"group": "Capacitance", "name": "C2", "value": 0.098, "unit": "µF", "min": 0.08, "max": 0.12},
            
            # Diode tests
            {"group": "Diodes", "name": "D1 Forward", "value": 0.65, "unit": "V", "min": 0.5, "max": 0.8},
            {"group": "Diodes", "name": "D1 Reverse", "value": True},
            
            # IC presence tests
            {"group": "IC Tests", "name": "U1 Present", "value": True},
            {"group": "IC Tests", "name": "U2 Present", "value": True},
        ]
    }
    
    # Build report
    builder = ReportBuilder(
        part_number=ict_data["header"]["part_number"],
        serial_number=ict_data["header"]["serial_number"],
        revision=ict_data["header"]["revision"],
        operator=ict_data["header"]["operator"],
        result=ict_data["header"]["result"]
    )
    
    # Add all tests
    for test in ict_data["tests"]:
        builder.add_step(
            name=test["name"],
            value=test["value"],
            unit=test.get("unit"),
            low_limit=test.get("min"),
            high_limit=test.get("max"),
            group=test.get("group")
        )
    
    report = builder.build()
    return report


# =============================================================================
# Example 9: Failed Report
# =============================================================================

def example_failed_report():
    """Report with failures - overall result auto-calculated as failed"""
    
    builder = ReportBuilder(
        part_number="FAIL-TEST",
        serial_number="FAIL-001"
    )
    
    # Passing tests
    builder.add_step("Test 1", 5.0, low_limit=4.0, high_limit=6.0, group="Power")
    builder.add_step("Test 2", True, group="Power")
    
    # FAILING test - out of limits
    builder.add_step("Test 3", 10.0, low_limit=4.0, high_limit=6.0, group="Power")
    
    # More passing tests
    builder.add_step("Test 4", 3.3, low_limit=3.0, high_limit=3.6, group="Voltage")
    
    report = builder.build()
    # report.result will be "F" because Test 3 failed
    return report


# =============================================================================
# Run Examples
# =============================================================================

if __name__ == "__main__":
    # To use these examples with the pyWATS API:
    
    from pywats import pyWATS
    
    # Initialize API
    api = pyWATS(
        base_url="https://your-wats-server.com",
        token="your-api-token"
    )
    
    # Run any example
    report = example_simple_report()
    
    # Submit to WATS
    response = api.report.submit_report(report)
    print(f"Report submitted: {response}")
    
    # Or try other examples:
    # report = example_grouped_report()
    # report = example_from_dicts()
    # report = quick_report(...)
    # report = example_ict_converter()
