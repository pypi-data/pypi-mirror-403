"""
Report Domain: Attachments

This example demonstrates adding attachments to both UUT and UUR reports.

Attachments can include:
- Images (photos of defects, repairs, product)
- Documents (PDFs, test specifications)
- Binary data (oscilloscope captures, measurement files)
- Text logs (test logs, repair notes)

The attachment API is identical for UUT and UUR reports.

File I/O Architecture:
- pywats (API layer) is memory-only - use attach_bytes() with pre-loaded content
- pywats_client.io provides AttachmentIO for file operations
- See examples/attachment_io_example.py for file I/O patterns
"""
import os
from pathlib import Path
from pywats import pyWATS
from pywats.core import Station
from pywats_client.io import AttachmentIO  # For file operations

# =============================================================================
# Setup
# =============================================================================

station = Station(name="TEST-STATION-01", location="Lab A")

api = pyWATS(
    base_url=os.environ.get("WATS_BASE_URL", "https://demo.wats.com"),
    token=os.environ.get("WATS_TOKEN", ""),
    station=station
)


# =============================================================================
# Attaching Files (via pywats_client.io)
# =============================================================================

def attach_file_example():
    """
    Attach a file from disk to a report using pywats_client.io.
    
    The MIME type is automatically detected from the file extension.
    File I/O is handled by AttachmentIO, then content is passed to the API.
    """
    # Create a sample report
    report = api.report.create_uut_report(
        part_number="WIDGET-001",
        operation_code=100,
        serial_number="SN-2024-001"
    )
    
    # Load file using AttachmentIO, then attach bytes to report
    # info = AttachmentIO.read_file("test_photo.jpg")
    # report.attach_bytes(name=info.name, content=info.content, content_type=info.mime_type)
    
    # With explicit content type
    # info = AttachmentIO.read_file("data.bin")
    # report.attach_bytes(name=info.name, content=info.content, content_type="application/octet-stream")
    
    # With custom name
    # info = AttachmentIO.read_file("IMG_20240126_103000.jpg")
    # report.attach_bytes(name="Repair Photo", content=info.content, content_type=info.mime_type)
    
    return report


# =============================================================================
# Attaching Binary Data
# =============================================================================

def attach_bytes_example():
    """
    Attach binary content directly without writing to disk.
    
    Useful for dynamically generated content or data from instruments.
    """
    report = api.report.create_uut_report(
        part_number="WIDGET-001",
        operation_code=100,
        serial_number="SN-2024-002"
    )
    
    # Attach raw binary data
    measurement_data = bytes([0x00, 0x01, 0x02, 0x03, 0x04])
    report.attach_bytes(
        name="Raw Measurement",
        content=measurement_data,
        content_type="application/octet-stream"
    )
    
    # Attach a text log as bytes
    log_text = """
    Test Log - 2026-01-26
    =====================
    Step 1: Power on - OK
    Step 2: Self test - OK
    Step 3: Voltage check - FAIL
    """
    report.attach_bytes(
        name="Test Log",
        content=log_text.encode("utf-8"),
        content_type="text/plain"
    )
    
    # Attach JSON data
    import json
    config = {"setting1": True, "setting2": 42, "setting3": "value"}
    report.attach_bytes(
        name="Test Configuration",
        content=json.dumps(config, indent=2).encode("utf-8"),
        content_type="application/json"
    )
    
    return report


# =============================================================================
# Attaching to UUR Reports
# =============================================================================

def uur_attachments_example(failed_uut):
    """
    Attach files to a UUR (repair) report.
    
    The attachment API is identical for UUT and UUR reports.
    Use pywats_client.io.AttachmentIO to load files from disk.
    """
    uur = api.report.create_uur_report(
        failed_uut,
        operator="RepairTech"
    )
    
    # Add failure info first
    uur.add_failure_to_main_unit(
        category="Component",
        code="Defect Component",
        comment="Capacitor C12 failed"
    )
    
    # Attach repair documentation using AttachmentIO
    # Before photo
    # info = AttachmentIO.read_file("before_repair.jpg")
    # uur.attach_bytes(name="Before Repair", content=info.content, content_type=info.mime_type)
    
    # After photo  
    # info = AttachmentIO.read_file("after_repair.jpg")
    # uur.attach_bytes(name="After Repair", content=info.content, content_type=info.mime_type)
    
    # Repair log
    repair_notes = """
    Repair Report
    =============
    Date: 2026-01-26
    Technician: John Smith
    
    Diagnosis:
    - Unit failed voltage test
    - Traced to capacitor C12
    - Visual inspection confirmed bulging cap
    
    Repair:
    - Removed capacitor C12
    - Installed replacement (C12-NEW)
    - Verified repair with voltage test
    
    Result: PASS
    """
    uur.attach_bytes(
        name="Repair Notes",
        content=repair_notes.encode("utf-8"),
        content_type="text/plain"
    )
    
    return uur


# =============================================================================
# Supported Content Types
# =============================================================================

# Common MIME types supported (auto-detected from extension):
SUPPORTED_TYPES = {
    # Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    
    # Text
    ".txt": "text/plain",
    ".log": "text/plain",
    ".csv": "text/csv",
    ".xml": "application/xml",
    ".json": "application/json",
    
    # Binary
    ".bin": "application/octet-stream",
    ".dat": "application/octet-stream",
    ".zip": "application/zip",
}


# =============================================================================
# Best Practices
# =============================================================================

"""
Attachment Best Practices:
========================

1. Use descriptive names
   - Bad: "IMG_20240126.jpg"
   - Good: "Failed Component Photo"

2. Choose appropriate content type
   - Let AttachmentIO auto-detection handle common types
   - Specify explicitly for custom formats

3. Size considerations
   - Keep attachments reasonable size (<10MB typical)
   - Compress large files if possible

4. File I/O separation
   - pywats API is memory-only for testability and async-safety
   - Use pywats_client.io.AttachmentIO for file operations
   - Load files first, then pass bytes to the API

5. Organize multiple attachments
   - Use clear naming conventions
   - Group related attachments with prefixes

6. Pattern for file attachments
   ```python
   from pywats_client.io import AttachmentIO
   
   # Load file and attach to report
   info = AttachmentIO.read_file("screenshot.png")
   report.attach_bytes(
       name="Test Screenshot",
       content=info.content,
       content_type=info.mime_type
   )
   ```

7. See examples/attachment_io_example.py for more file I/O patterns
"""
