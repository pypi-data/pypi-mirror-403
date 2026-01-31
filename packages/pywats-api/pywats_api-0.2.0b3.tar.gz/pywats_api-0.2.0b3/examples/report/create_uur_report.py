"""
Report Domain: Create UUR Report

This example demonstrates creating UUR (Unit Under Repair) reports.

UUR reports document repair activities on units that have failed testing.
They link back to the original failed UUT report and track:
- What failure was found (failure category/code)
- What was repaired
- Component replacements
- Attachments (photos, logs, etc.)

Best Practice: Create UUR via service factory from a failed UUT report.
"""
import os
from datetime import datetime
from pywats import pyWATS
from pywats.core import Station

# =============================================================================
# Setup
# =============================================================================

station = Station(name="REPAIR-STATION-01", location="Repair Center")

api = pyWATS(
    base_url=os.environ.get("WATS_BASE_URL", "https://demo.wats.com"),
    token=os.environ.get("WATS_TOKEN", ""),
    station=station
)


# =============================================================================
# Pattern 1: Create UUR from Failed UUT Report (Recommended)
# =============================================================================

def repair_from_failed_uut(failed_uut):
    """
    Create a repair report from a failed UUT report.
    
    This is the recommended pattern - the UUR automatically links
    to the failed UUT and copies relevant metadata.
    """
    # Create UUR linked to the failed UUT
    uur = api.report.create_uur_report(
        failed_uut,
        operator="RepairTech",
        comment="Investigating failure"
    )
    
    # Add failure documentation (required)
    # Uses category/code from server's fail code configuration
    uur.add_failure_to_main_unit(
        category="Component",
        code="Defect Component",
        comment="Capacitor C12 exceeded voltage spec",
        component_ref="C12"
    )
    
    # Add repair information via misc info
    uur.add_misc_info("Symptom", "Unit failed voltage test at step 3")
    uur.add_misc_info("RootCause", "Degraded capacitor C12")
    uur.add_misc_info("Action", "Replaced capacitor C12")
    
    # Set execution time (repair duration in seconds)
    uur.execution_time = 1800.0  # 30 minutes
    
    # Submit
    result = api.report.submit_report(uur)
    print(f"Repair report submitted: {result}")
    return uur


# =============================================================================
# Pattern 2: Create UUR from UUT GUID
# =============================================================================

def repair_from_uut_guid(uut_guid: str, part_number: str, serial_number: str):
    """
    Create repair report when you have the UUT GUID but not the full report.
    
    Useful when looking up a failed unit from the database.
    """
    from uuid import UUID
    
    uur = api.report.create_uur_report(
        UUID(uut_guid),
        part_number=part_number,
        serial_number=serial_number,
        test_operation_code=100,  # Original test operation
        repair_process_code=500,  # Repair process
        operator="RepairTech"
    )
    
    # Document the failure
    uur.add_failure_to_main_unit(
        category="Assembly",
        code="Cold Solder Joint",
        comment="Poor solder joint on U3 pin 12",
        component_ref="U3"
    )
    
    return uur


# =============================================================================
# Pattern 3: Standalone UUR (No Linked UUT)
# =============================================================================

def standalone_repair(part_number: str, serial_number: str):
    """
    Create a standalone repair report without a linked UUT.
    
    Used for field repairs or repairs without a failed test report.
    """
    uur = api.report.create_uur_report(
        part_number, 100,  # part_number, test_operation_code
        serial_number=serial_number,
        repair_process_code=500,
        operator="FieldTech",
        comment="Field repair - customer site"
    )
    
    # Document failure
    uur.add_failure_to_main_unit(
        category="Component",
        code="No Fault Found",
        comment="Customer reported intermittent issue, no fault found"
    )
    
    return uur


# =============================================================================
# Adding Sub-Unit Failures
# =============================================================================

def repair_with_sub_units(failed_uut):
    """
    Document failures on sub-units (daughter boards, modules, etc.)
    """
    uur = api.report.create_uur_report(
        failed_uut,
        operator="RepairTech"
    )
    
    # Add failure to main unit
    main = uur.get_main_unit()
    main.add_failure(
        category="Component",
        code="Defect Component",
        comment="Main board power regulator failed",
        component_ref="U1"
    )
    
    # Add a sub-unit and its failure
    sub = uur.add_sub_unit(
        pn="DAUGHTER-BOARD-001",
        sn="DB-SN-12345",
        rev="B",
        part_type="DaughterBoard"
    )
    sub.add_failure(
        category="Solder",
        code="Cold Solder Joint",
        comment="Cold joint on connector J2",
        component_ref="J2"
    )
    
    return uur


# =============================================================================
# Adding Attachments
# =============================================================================

def repair_with_attachments(failed_uut):
    """
    Add attachments to document the repair.
    """
    uur = api.report.create_uur_report(
        failed_uut,
        operator="RepairTech"
    )
    
    # Document failure
    uur.add_failure_to_main_unit(
        category="Component",
        code="Defect Component",
        comment="Replaced damaged IC"
    )
    
    # Attach a photo of the repair using pywats_client.io
    # from pywats_client.io import AttachmentIO
    # info = AttachmentIO.read_file("repair_photo.jpg")
    # uur.attach_bytes(name="Repair Photo", content=info.content, content_type=info.mime_type)
    
    # Attach binary data (e.g., oscilloscope capture)
    measurement_data = b"\x00\x01\x02\x03"  # Example binary data
    uur.attach_bytes(
        name="Scope Capture",
        content=measurement_data,
        content_type="application/octet-stream"
    )
    
    # Attach a text log
    log_content = """
    Repair Log - 2026-01-26
    =======================
    10:00 - Started diagnosis
    10:15 - Identified failed IC U5
    10:30 - Removed old IC
    10:45 - Installed new IC
    11:00 - Verified repair, all tests pass
    """
    uur.attach_bytes(
        name="Repair Log",
        content=log_content.encode("utf-8"),
        content_type="text/plain"
    )
    
    return uur


# =============================================================================
# Complete Repair Workflow Example
# =============================================================================

def complete_repair_workflow(serial_number: str):
    """
    Complete example: Find failed UUT, create repair, submit.
    """
    # Find the failed UUT report
    failed_reports = api.report.get_reports(
        serial_number=serial_number,
        result="Failed"
    )
    
    if not failed_reports:
        print(f"No failed reports found for {serial_number}")
        return None
    
    failed_uut = failed_reports[0]
    print(f"Found failed UUT: {failed_uut.id}")
    
    # Create repair report
    uur = api.report.create_uur_report(
        failed_uut,
        operator=os.environ.get("USER", "RepairTech"),
        comment="Standard repair workflow"
    )
    
    # Document failure
    uur.add_failure_to_main_unit(
        category="Component",
        code="Defect Component",
        comment="Replaced failed component"
    )
    
    # Add repair metadata
    uur.add_misc_info("RepairType", "Standard")
    uur.add_misc_info("WorkOrder", "WO-2026-001")
    
    # Submit repair
    result = api.report.submit_report(uur)
    print(f"Repair submitted: {result}")
    
    return uur


# =============================================================================
# Usage Examples (commented out to prevent accidental execution)
# =============================================================================

# Example 1: Create UUR from failed UUT
# failed_uut = api.report.get_report_by_id("some-uuid")
# repair_from_failed_uut(failed_uut)

# Example 2: Standalone repair
# standalone_repair("WIDGET-001", "SN-2024-001234")

# Example 3: Complete workflow
# complete_repair_workflow("SN-2024-001234")
