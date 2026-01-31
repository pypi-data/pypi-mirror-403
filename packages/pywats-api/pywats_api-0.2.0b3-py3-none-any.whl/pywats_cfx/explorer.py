#!/usr/bin/env python
"""
CFX Sample Explorer CLI.

Interactive tool to explore CFX message samples, test adapters,
and understand the event mapping to WATS.

Usage:
    python -m pywats_cfx.explorer
    python -m pywats_cfx.explorer --list
    python -m pywats_cfx.explorer --sample units_tested_ict
    python -m pywats_cfx.explorer --convert units_tested_ict
    python -m pywats_cfx.explorer --generate test --passed --serial SN-001
"""

import argparse
import json
import sys
from typing import Any

# Import samples
from pywats_cfx.samples import (
    UNITS_TESTED_ICT,
    UNITS_TESTED_FCT,
    UNITS_TESTED_MULTI_MEASUREMENT,
    UNITS_INSPECTED_AOI,
    UNITS_INSPECTED_SPI,
    WORK_STARTED_SAMPLE,
    WORK_COMPLETED_PASSED,
    WORK_COMPLETED_FAILED,
    UNITS_ARRIVED_SAMPLE,
    UNITS_DEPARTED_SAMPLE,
    UNITS_DISQUALIFIED_SAMPLE,
    MATERIALS_INSTALLED_SMT,
    MATERIALS_INSTALLED_THROUGH_HOLE,
    MATERIALS_LOADED_FEEDER,
    FAULT_OCCURRED_TEMPERATURE,
    FAULT_OCCURRED_FEEDER,
    FAULT_CLEARED_SAMPLE,
    STATION_STATE_CHANGED_SAMPLES,
    CFXSampleGenerator,
)

# Import adapters
from pywats_cfx.adapters import (
    CFXTestResultAdapter,
    CFXMaterialAdapter,
    CFXProductionAdapter,
    CFXResourceAdapter,
)

from pywats_cfx.models import parse_cfx_message


# Sample registry
SAMPLES = {
    # Test samples
    "units_tested_ict": ("UnitsTested - ICT Pass", UNITS_TESTED_ICT),
    "units_tested_fct": ("UnitsTested - FCT Fail", UNITS_TESTED_FCT),
    "units_tested_multi": ("UnitsTested - Multiple Measurements", UNITS_TESTED_MULTI_MEASUREMENT),
    "units_inspected_aoi": ("UnitsInspected - AOI with Defects", UNITS_INSPECTED_AOI),
    "units_inspected_spi": ("UnitsInspected - SPI Pass", UNITS_INSPECTED_SPI),
    
    # Production samples
    "work_started": ("WorkStarted - 3 Units", WORK_STARTED_SAMPLE),
    "work_completed_pass": ("WorkCompleted - Passed", WORK_COMPLETED_PASSED),
    "work_completed_fail": ("WorkCompleted - Aborted", WORK_COMPLETED_FAILED),
    "units_arrived": ("UnitsArrived", UNITS_ARRIVED_SAMPLE),
    "units_departed": ("UnitsDeparted", UNITS_DEPARTED_SAMPLE),
    "units_disqualified": ("UnitsDisqualified", UNITS_DISQUALIFIED_SAMPLE),
    
    # Material samples
    "materials_smt": ("MaterialsInstalled - SMT", MATERIALS_INSTALLED_SMT),
    "materials_th": ("MaterialsInstalled - Through-Hole", MATERIALS_INSTALLED_THROUGH_HOLE),
    "materials_loaded": ("MaterialsLoaded - Feeder", MATERIALS_LOADED_FEEDER),
    
    # Resource samples
    "fault_temp": ("FaultOccurred - Temperature", FAULT_OCCURRED_TEMPERATURE),
    "fault_feeder": ("FaultOccurred - Feeder", FAULT_OCCURRED_FEEDER),
    "fault_cleared": ("FaultCleared", FAULT_CLEARED_SAMPLE),
}


def print_json(data: Any, indent: int = 2) -> None:
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


def list_samples() -> None:
    """List all available samples."""
    print("\n📋 Available CFX Samples:")
    print("=" * 60)
    
    categories = {
        "Test & Inspection": ["units_tested_ict", "units_tested_fct", "units_tested_multi", 
                              "units_inspected_aoi", "units_inspected_spi"],
        "Production Flow": ["work_started", "work_completed_pass", "work_completed_fail",
                           "units_arrived", "units_departed", "units_disqualified"],
        "Materials": ["materials_smt", "materials_th", "materials_loaded"],
        "Resource/Faults": ["fault_temp", "fault_feeder", "fault_cleared"],
    }
    
    for category, keys in categories.items():
        print(f"\n{category}:")
        for key in keys:
            if key in SAMPLES:
                desc, _ = SAMPLES[key]
                print(f"  • {key:25} - {desc}")
    
    print("\n" + "=" * 60)
    print("Usage: python -m pywats_cfx.explorer --sample <name>")
    print("       python -m pywats_cfx.explorer --convert <name>")


def show_sample(name: str) -> None:
    """Show a specific sample."""
    if name not in SAMPLES:
        print(f"❌ Unknown sample: {name}")
        print("Use --list to see available samples")
        return
    
    desc, data = SAMPLES[name]
    print(f"\n📄 {desc}")
    print(f"   Message: {data.get('MessageName', 'Unknown')}")
    print("=" * 60)
    print_json(data)


def convert_sample(name: str) -> None:
    """Convert a sample through the adapter and show the result."""
    if name not in SAMPLES:
        print(f"❌ Unknown sample: {name}")
        return
    
    desc, data = SAMPLES[name]
    message_name = data.get("MessageName", "")
    
    print(f"\n🔄 Converting: {desc}")
    print(f"   Source: {message_name}")
    print("=" * 60)
    
    try:
        # Parse the message
        cfx_message = parse_cfx_message(data)
        
        # Determine adapter
        events = []
        
        if "Testing.UnitsTested" in message_name:
            adapter = CFXTestResultAdapter(source_endpoint="sample")
            from pywats_cfx.models import UnitsTested
            if isinstance(cfx_message, UnitsTested):
                events = adapter.from_units_tested(cfx_message)
        
        elif "Assembly.UnitsInspected" in message_name:
            adapter = CFXTestResultAdapter(source_endpoint="sample")
            from pywats_cfx.models import UnitsInspected
            if isinstance(cfx_message, UnitsInspected):
                events = adapter.from_units_inspected(cfx_message)
        
        elif "Assembly.MaterialsInstalled" in message_name:
            adapter = CFXMaterialAdapter(source_endpoint="sample")
            from pywats_cfx.models import MaterialsInstalled
            if isinstance(cfx_message, MaterialsInstalled):
                events = adapter.from_materials_installed(cfx_message)
        
        elif "WorkStarted" in message_name:
            adapter = CFXProductionAdapter(source_endpoint="sample")
            from pywats_cfx.models import WorkStarted
            if isinstance(cfx_message, WorkStarted):
                events = adapter.from_work_started(cfx_message)
        
        elif "WorkCompleted" in message_name:
            adapter = CFXProductionAdapter(source_endpoint="sample")
            from pywats_cfx.models import WorkCompleted
            if isinstance(cfx_message, WorkCompleted):
                events = adapter.from_work_completed(cfx_message)
        
        elif "FaultOccurred" in message_name:
            adapter = CFXResourceAdapter(source_endpoint="sample")
            from pywats_cfx.models import FaultOccurred
            if isinstance(cfx_message, FaultOccurred):
                event = adapter.from_fault_occurred(cfx_message)
                events = [event]
        
        elif "StationStateChanged" in message_name:
            adapter = CFXResourceAdapter(source_endpoint="sample")
            from pywats_cfx.models import StationStateChanged
            if isinstance(cfx_message, StationStateChanged):
                event = adapter.from_station_state_changed(cfx_message)
                events = [event]
        
        else:
            print(f"⚠️  No adapter for message type: {message_name}")
            return
        
        # Show results
        print(f"\n✅ Converted to {len(events)} event(s):\n")
        
        for i, event in enumerate(events, 1):
            print(f"--- Event {i} ---")
            print(f"Type: {event.event_type.value}")
            print(f"ID:   {event.metadata.event_id}")
            print(f"Source: {event.metadata.source}")
            print(f"Correlation: {event.metadata.correlation_id}")
            print("\nPayload (→ WATS):")
            print_json(event.payload)
            print()
        
        # Show WATS mapping hints
        print("\n" + "=" * 60)
        print("🎯 WATS Mapping Hints:")
        if "TEST_RESULT" in str(event.event_type) or "INSPECTION" in str(event.event_type):
            print("   → Create UUTReport via api.report.submit()")
            print("   → payload['unit_id'] → serial_number")
            print("   → payload['part_number'] → part_number")
            print("   → payload['result'] → status (Passed/Failed)")
            print("   → payload['steps'] → add_numeric_limit_step() etc.")
        elif "MATERIAL" in str(event.event_type):
            print("   → Link components via api.product")
            print("   → payload['components'] → component traceability")
        elif "FAULT" in str(event.event_type):
            print("   → Create asset fault via api.asset.create_fault()")
            print("   → payload['fault_code'] → fault identifier")
            print("   → payload['severity'] → priority")
        elif "WORK" in str(event.event_type):
            print("   → Track production via api.production")
            print("   → payload['unit_id'] → serial tracking")
        
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        import traceback
        traceback.print_exc()


def generate_sample(
    sample_type: str,
    serial: str = None,
    passed: bool = True,
) -> None:
    """Generate a custom sample."""
    gen = CFXSampleGenerator(station_id="DEMO-STATION-01")
    
    if sample_type == "test":
        sample = gen.units_tested(
            serial_number=serial,
            test_method="FCT",
            passed=passed,
            measurements=[
                {"name": "Voltage", "value": 5.02 if passed else 5.8, "low": 4.5, "high": 5.5, "unit": "V"},
                {"name": "Current", "value": 0.5, "low": 0.3, "high": 0.7, "unit": "A"},
            ]
        )
    elif sample_type == "fault":
        sample = gen.fault_occurred(
            fault_code="DEMO_FAULT",
            description="Demo fault for testing",
            severity="Warning",
        )
    elif sample_type == "materials":
        sample = gen.materials_installed(
            serial_number=serial,
            components=[
                {"ref": "U1", "part_number": "MCU-001", "manufacturer": "STM", "lot": "LOT-001"},
                {"ref": "R1", "part_number": "RES-10K", "manufacturer": "Yageo", "lot": "LOT-002"},
            ]
        )
    else:
        print(f"❌ Unknown type: {sample_type}")
        print("Available: test, fault, materials")
        return
    
    print(f"\n🔧 Generated {sample_type} sample:")
    print("=" * 60)
    print_json(sample)


def main():
    parser = argparse.ArgumentParser(
        description="CFX Sample Explorer - Explore and test IPC-CFX messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                      List all samples
  %(prog)s --sample units_tested_ict   Show ICT test sample
  %(prog)s --convert units_tested_fct  Convert and show WATS mapping
  %(prog)s --generate test --passed    Generate passing test
  %(prog)s --generate test --failed    Generate failing test
        """
    )
    
    parser.add_argument("--list", "-l", action="store_true",
                       help="List available samples")
    parser.add_argument("--sample", "-s", type=str,
                       help="Show a specific sample")
    parser.add_argument("--convert", "-c", type=str,
                       help="Convert sample through adapter")
    parser.add_argument("--generate", "-g", type=str,
                       choices=["test", "fault", "materials"],
                       help="Generate a custom sample")
    parser.add_argument("--serial", type=str,
                       help="Serial number for generated sample")
    parser.add_argument("--passed", action="store_true", default=True,
                       help="Generate passing result (default)")
    parser.add_argument("--failed", action="store_true",
                       help="Generate failing result")
    
    args = parser.parse_args()
    
    if args.list:
        list_samples()
    elif args.sample:
        show_sample(args.sample)
    elif args.convert:
        convert_sample(args.convert)
    elif args.generate:
        passed = not args.failed
        generate_sample(args.generate, args.serial, passed)
    else:
        # Interactive mode hint
        print("\n🔍 CFX Sample Explorer")
        print("=" * 40)
        print("Use --list to see available samples")
        print("Use --help for all options")
        print()
        list_samples()


if __name__ == "__main__":
    main()
