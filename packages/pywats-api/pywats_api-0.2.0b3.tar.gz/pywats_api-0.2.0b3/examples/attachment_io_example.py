"""
Attachment File I/O Example

Demonstrates how to work with attachments using the pywats_client.io module.

The pywats API (pywats/) is memory-only - it does not perform file I/O.
For file operations, use pywats_client.io which provides:
- AttachmentIO.from_file() - Load attachments from files
- AttachmentIO.save() - Save attachments to files
- AttachmentIO.read_file() - Read file info without creating attachment

This separation ensures:
- Clean testability (no filesystem mocks needed for API tests)
- Async-safe operations (no blocking I/O in async contexts)
- Platform isolation (file handling logic in one place)
"""

from pathlib import Path

# API layer - memory only
from pywats import pyWATS, Attachment

# Client layer - file I/O
from pywats_client.io import AttachmentIO, load_attachment, save_attachment


# ============================================================================
# Example 1: Load Attachment from File
# ============================================================================

def example_load_from_file():
    """Load an attachment from a file using AttachmentIO."""
    
    # Create attachment from file
    attachment = AttachmentIO.from_file("report.pdf")
    
    print(f"Loaded: {attachment.name}")
    print(f"Type: {attachment.content_type}")
    print(f"Size: {attachment.size} bytes")
    
    # Or use the convenience function
    attachment = load_attachment("screenshot.png")
    
    # With custom options
    attachment = AttachmentIO.from_file(
        "temp_data.bin",
        name="measurement_results.bin",
        content_type="application/octet-stream",
        delete_after=True  # Delete source file after loading
    )


# ============================================================================
# Example 2: Attach Files to Reports
# ============================================================================

def example_attach_to_report():
    """Attach files to a report using the proper workflow."""
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token"
    )
    
    # Create report
    report = api.report.create_uut_report(
        operator="John",
        part_number="PCBA-001",
        revision="A",
        serial_number="SN-12345",
        operation_type=100
    )
    
    # Method 1: Use AttachmentIO to create attachment, then add to step
    root = report.get_root_sequence_call()
    step = root.add_numeric_step(
        name="Voltage Test",
        value=5.02,
        low_limit=4.5,
        high_limit=5.5,
        unit="V"
    )
    
    # Load file and attach
    attachment = AttachmentIO.from_file("oscilloscope_capture.png")
    step.add_attachment(attachment)
    
    # Method 2: Read file info and use attach_bytes directly
    file_info = AttachmentIO.read_file("test_log.txt")
    step.add_attachment(Attachment.from_bytes(
        name=file_info.name,
        content=file_info.content,
        content_type=file_info.mime_type
    ))
    
    # Method 3: For UUR reports
    uur_report = api.report.create_uur_report(
        operator="Jane",
        part_number="PCBA-001",
        revision="A",
        serial_number="SN-12345"
    )
    
    # Read file manually and attach as bytes
    info = AttachmentIO.read_file("repair_photo.jpg")
    uur_report.attach_bytes(
        name=info.name,
        content=info.content,
        content_type=info.mime_type
    )


# ============================================================================
# Example 3: Save Attachments to Files
# ============================================================================

def example_save_attachments():
    """Download and save attachments from a report."""
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token"
    )
    
    # Get a report with attachments
    report = api.report.get("report-id-here")
    
    # Save all attachments to a directory
    if hasattr(report, 'attachments') and report.attachments:
        output_dir = Path("downloaded_attachments")
        
        saved_paths = AttachmentIO.save_multiple(
            report.attachments,
            output_dir,
            overwrite=True
        )
        
        for path in saved_paths:
            print(f"Saved: {path}")
    
    # Or save a single attachment
    if report.attachments:
        attachment = report.attachments[0]
        path = AttachmentIO.save(attachment, f"output/{attachment.name}")
        print(f"Saved to: {path}")
        
        # Convenience function
        path = save_attachment(attachment, "backup.bin", overwrite=True)


# ============================================================================
# Example 4: In-Memory Attachments (No File I/O)
# ============================================================================

def example_memory_only():
    """
    Create attachments without any file I/O.
    
    This works with just pywats (no pywats_client needed).
    """
    from pywats import Attachment
    
    # Create from bytes directly
    screenshot_data = b"\x89PNG\r\n\x1a\n..."  # PNG header + data
    attachment = Attachment.from_bytes(
        name="screenshot.png",
        content=screenshot_data,
        content_type="image/png"
    )
    
    # Create from a string
    log_content = "Test started at 10:00\nVoltage: 5.02V\nPASS"
    attachment = Attachment.from_bytes(
        name="test_log.txt",
        content=log_content.encode("utf-8"),
        content_type="text/plain"
    )
    
    # Get bytes back out
    data = attachment.get_bytes()
    print(f"Attachment size: {len(data)} bytes")


# ============================================================================
# Example 5: Batch Processing with File I/O
# ============================================================================

def example_batch_processing():
    """Process multiple files with attachments."""
    from pathlib import Path
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token"
    )
    
    # Process all files in a directory
    input_dir = Path("test_artifacts")
    
    for file_path in input_dir.glob("*.png"):
        # Create report for each test
        report = api.report.create_uut_report(
            operator="AutoTest",
            part_number="WIDGET-001",
            revision="A",
            serial_number=file_path.stem,  # Use filename as SN
            operation_type=100
        )
        
        # Load and attach the screenshot
        attachment = AttachmentIO.from_file(
            file_path,
            delete_after=True  # Clean up after processing
        )
        
        root = report.get_root_sequence_call()
        step = root.add_pass_step("Visual Inspection")
        step.add_attachment(attachment)
        
        # Submit
        report_id = api.report.submit(report)
        print(f"Submitted {file_path.name}: {report_id}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Attachment I/O Examples")
    print("=" * 60)
    print()
    print("This module demonstrates proper file I/O patterns:")
    print("  - pywats (API layer): Memory-only, no file operations")
    print("  - pywats_client.io: File I/O operations")
    print()
    print("Run individual examples by uncommenting them below.")
    
    # Uncomment to run:
    # example_load_from_file()
    # example_attach_to_report()
    # example_save_attachments()
    # example_memory_only()
    # example_batch_processing()
