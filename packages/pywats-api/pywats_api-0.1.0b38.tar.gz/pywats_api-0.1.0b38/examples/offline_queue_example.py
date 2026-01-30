"""
Offline Queue Management Example

Demonstrates how to use the pyWATS offline queue for reliable report submission.
"""

from pywats import pyWATS
from pywats.queue import SimpleQueue, convert_to_wsjf, convert_from_wsxf

# ============================================================================
# Example 1: Submit with Offline Fallback
# ============================================================================

def example_submit_with_fallback():
    """Submit report, automatically queue if offline."""
    
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
    
    # Add test steps
    root = report.get_root_sequence_call()
    root.add_numeric_step(
        name="Voltage Test",
        value=5.02,
        low_limit=4.5,
        high_limit=5.5,
        unit="V"
    )
    
    # Submit with offline fallback
    # If online: submits immediately and returns report ID
    # If offline: saves to queue and returns None
    result = api.report.submit(report, offline_fallback=True)
    
    if result:
        print(f"✓ Report submitted successfully: {result}")
    else:
        print("⚠ Server offline - report queued for later submission")


# ============================================================================
# Example 2: Explicit Offline Submission
# ============================================================================

def example_explicit_offline():
    """Explicitly queue report for later submission."""
    
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
    
    # Explicitly save to queue (don't try to submit now)
    api.report.submit_offline(report)
    print("✓ Report queued for later submission")
    
    # Later, when online, process the queue
    results = api.report.process_queue()
    print(f"✓ Submitted {results['success']} reports")
    print(f"✗ Failed {results['failed']} reports")


# ============================================================================
# Example 3: Using SimpleQueue Directly
# ============================================================================

def example_simple_queue():
    """Use SimpleQueue class directly for more control."""
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token"
    )
    
    # Create queue
    queue = SimpleQueue(
        api=api,
        queue_dir="C:/WATS/Queue",
        max_retries=3,
        delete_completed=True
    )
    
    # Create and queue report
    report = api.report.create_uut_report(
        operator="John",
        part_number="PCBA-001",
        revision="A",
        serial_number="SN-12345",
        operation_type=100
    )
    
    queue.add(report)
    print(f"✓ Report queued ({queue.count_pending()} pending)")
    
    # Check queue status
    print(f"Pending reports: {queue.count_pending()}")
    print(f"Error reports: {queue.count_errors()}")
    
    # List pending reports
    for queued_report in queue.list_pending():
        print(f"  - {queued_report.file_name} (created: {queued_report.created_at})")
    
    # Process queue
    results = queue.process_all()
    print(f"✓ Submitted {results['success']} reports")
    print(f"✗ Failed {results['failed']} reports")
    print(f"⊘ Skipped {results['skipped']} reports (max retries)")


# ============================================================================
# Example 4: Auto-Process Queue in Background
# ============================================================================

def example_auto_process():
    """Automatically process queue every 5 minutes."""
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token"
    )
    
    queue = SimpleQueue(api, queue_dir="C:/WATS/Queue")
    
    # Start background processing (every 5 minutes)
    queue.start_auto_process(interval_seconds=300)
    print("✓ Auto-process started (runs every 5 minutes)")
    
    # Queue will automatically submit reports in background
    # Your main application can continue...
    
    # Later, stop auto-process
    queue.stop_auto_process()
    print("✓ Auto-process stopped")


# ============================================================================
# Example 5: Convert from WSXF/WSTF to WSJF
# ============================================================================

def example_format_conversion():
    """Convert between WATS report formats."""
    
    # Convert WSXF (XML) to WSJF (JSON)
    wsxf_data = """
    <Report xmlns="http://www.wats.com/XmlFormats/2009/Report">
        <PartNumber>PCBA-001</PartNumber>
        <SerialNumber>SN-12345</SerialNumber>
        ...
    </Report>
    """
    
    wsjf_json = convert_to_wsjf(convert_from_wsxf(wsxf_data))
    print(f"✓ Converted WSXF to WSJF: {len(wsjf_json)} bytes")
    
    # Save to queue
    api = pyWATS(base_url="...", token="...")
    queue = SimpleQueue(api, queue_dir="C:/WATS/Queue")
    
    # Queue will store in WSJF format
    import json
    report_dict = json.loads(wsjf_json)
    queue.add(report_dict)


# ============================================================================
# Example 6: Production Deployment Pattern
# ============================================================================

def example_production_pattern():
    """Recommended pattern for production test stations."""
    
    api = pyWATS(
        base_url="https://wats.server.com",
        token="your-api-token",
        retry_enabled=True,
        retry_config=RetryConfig(max_attempts=3)
    )
    
    # Always use offline fallback in production
    # This ensures reports are never lost due to network issues
    
    def run_test(serial_number: str):
        """Run test and submit report."""
        
        # Create report
        report = api.report.create_uut_report(
            operator="TestStation",
            part_number="PCBA-001",
            revision="A",
            serial_number=serial_number,
            operation_type=100
        )
        
        # ... run tests, add steps ...
        
        # Submit with offline fallback
        result = api.report.submit(report, offline_fallback=True)
        
        if result:
            print(f"✓ {serial_number}: Report submitted")
            return True
        else:
            print(f"⚠ {serial_number}: Queued (offline)")
            return False
    
    # Run multiple tests
    for sn in ["SN-001", "SN-002", "SN-003"]:
        run_test(sn)
    
    # At end of shift, process queue
    print("\nProcessing queue...")
    results = api.report.process_queue()
    print(f"Final results: {results}")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=== pyWATS Offline Queue Examples ===\n")
    
    # Uncomment to run specific examples
    # example_submit_with_fallback()
    # example_explicit_offline()
    # example_simple_queue()
    # example_auto_process()
    # example_format_conversion()
    # example_production_pattern()
    
    print("\n✓ See source code for usage examples")
