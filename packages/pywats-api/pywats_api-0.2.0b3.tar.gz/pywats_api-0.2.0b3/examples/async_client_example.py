"""
Async Client Service Example

Demonstrates using the AsyncClientService for efficient concurrent I/O.

This example shows:
1. Basic async service setup
2. Concurrent report uploads with AsyncPendingQueue
3. Concurrent file conversion with AsyncConverterPool
4. GUI integration with qasync

Requirements:
    pip install pywats qasync aiofiles
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Example 1: Basic Async Service (Headless)
# =============================================================================

async def run_headless_service():
    """
    Run the async client service in headless mode.
    
    This is ideal for:
    - Linux servers
    - Docker containers
    - Background services
    - CI/CD pipelines
    """
    from pywats_client.service import AsyncClientService
    
    logger.info("Starting headless async service...")
    
    # Create and run the service
    service = AsyncClientService()
    
    try:
        # Run until shutdown signal
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        await service.stop()
        logger.info("Service stopped")


# =============================================================================
# Example 2: Manual Async API Usage
# =============================================================================

async def manual_async_api_example():
    """
    Use AsyncWATS directly for async API calls.
    
    This is useful when you need fine-grained control over
    async operations without the full service infrastructure.
    """
    from pywats import AsyncWATS
    
    # Async context manager for automatic cleanup
    async with AsyncWATS(
        url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        # All API calls are non-blocking
        
        # Fetch multiple resources concurrently
        tasks = [
            api.report.get_reports(page=1, limit=10),
            api.production.lookup_production_unit(part_number="PN-001"),
            api.asset.get_assets(page=1, limit=10),
        ]
        
        # Wait for all to complete
        reports, unit, assets = await asyncio.gather(*tasks)
        
        logger.info(f"Fetched {len(reports)} reports")
        logger.info(f"Unit: {unit}")
        logger.info(f"Assets: {len(assets)}")


# =============================================================================
# Example 3: Custom Async Pending Queue
# =============================================================================

async def custom_pending_queue_example():
    """
    Configure AsyncPendingQueue with custom settings.
    
    The pending queue handles concurrent report uploads with:
    - Bounded concurrency (default: 5 concurrent uploads)
    - Queue capacity limits (default: 10,000 queued reports)
    - Automatic retry on failure
    - File system watching for new reports
    """
    from pywats import AsyncWATS
    from pywats_client.service import AsyncPendingQueue
    
    async with AsyncWATS(
        url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        # Create queue with custom settings
        queue = AsyncPendingQueue(
            api=api,
            reports_dir=Path("/var/lib/pywats/pending"),
            max_concurrent=10,      # Increase for high-throughput scenarios
            max_queue_size=50000,   # Increase for more queued reports
        )
        
        # Check queue capacity
        can_accept, reason = queue.can_accept_report()
        if not can_accept:
            logger.warning(f"Queue full: {reason}")
        
        # Run the queue
        logger.info(f"Starting pending queue (capacity: {queue.queue_size}/{queue._max_queue_size})...")
        try:
            await queue.run()
        except asyncio.CancelledError:
            await queue.stop()


# =============================================================================
# Example 4: Custom Async Converter Pool
# =============================================================================

async def custom_converter_pool_example():
    """
    Configure AsyncConverterPool with custom settings.
    
    The converter pool handles concurrent file conversion with:
    - Bounded concurrency (default: 10 concurrent conversions)
    - Multiple input directory watching
    - Support for all converter types (Python, DLL, process)
    """
    from pywats import AsyncWATS
    from pywats_client.service import AsyncConverterPool
    from pywats_client.core.config import ClientConfig
    
    # Load client configuration
    config = ClientConfig.load_for_instance("default")
    
    async with AsyncWATS(
        url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        # Create pool with custom concurrency
        pool = AsyncConverterPool(
            config=config,
            api=api,
            max_concurrent=20,  # Increase for many converters
        )
        
        # Run the pool
        logger.info("Starting converter pool...")
        try:
            await pool.run()
        except asyncio.CancelledError:
            await pool.stop()


# =============================================================================
# Example 5: GUI Integration with qasync
# =============================================================================

def run_gui_with_async():
    """
    Run async service alongside Qt GUI using qasync.
    
    qasync integrates asyncio with Qt's event loop, allowing
    non-blocking async operations in GUI applications.
    """
    import sys
    
    try:
        import qasync
        from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
    except ImportError:
        logger.error("qasync and PySide6 required: pip install qasync PySide6")
        return
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Async Client Demo")
    window.resize(400, 300)
    
    # Create button that triggers async operation
    button = QPushButton("Fetch Reports", window)
    button.setGeometry(100, 100, 200, 50)
    
    async def fetch_reports():
        """Async operation triggered by button click"""
        from pywats import AsyncWATS
        
        button.setEnabled(False)
        button.setText("Loading...")
        
        try:
            async with AsyncWATS(
                url="https://your-wats-server.com",
                token="your-api-token"
            ) as api:
                reports = await api.report.get_reports(page=1, limit=10)
                button.setText(f"Found {len(reports)} reports")
        except Exception as e:
            button.setText(f"Error: {e}")
        finally:
            button.setEnabled(True)
    
    def on_button_click():
        """Button click handler - schedules async task"""
        asyncio.ensure_future(fetch_reports())
    
    button.clicked.connect(on_button_click)
    
    window.show()
    
    # Run Qt + asyncio event loop
    with loop:
        loop.run_forever()


# =============================================================================
# Example 6: Concurrent Report Submission
# =============================================================================

async def concurrent_report_submission():
    """
    Submit multiple reports concurrently.
    
    This demonstrates the power of async - submitting many reports
    in parallel rather than sequentially.
    """
    from pywats import AsyncWATS
    from pywats.models.reports import UURReport
    import time
    
    async with AsyncWATS(
        url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        # Create sample reports
        reports = []
        for i in range(10):
            report = UURReport(
                pn="ASYNC-TEST-001",
                rev="1.0",
                sn=f"SN-{i:04d}",
                operator="async_example",
            )
            report.root.add_sequence_call("TestSequence")
            reports.append(report)
        
        # Submit all reports concurrently
        start_time = time.time()
        
        tasks = [api.report.submit_report(report) for report in reports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Count successes and failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))
        
        logger.info(f"Submitted {successes} reports successfully, {failures} failed")
        logger.info(f"Total time: {elapsed:.2f}s (vs ~{len(reports) * 0.5:.1f}s sequential)")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys
    
    examples = {
        "headless": run_headless_service,
        "api": manual_async_api_example,
        "queue": custom_pending_queue_example,
        "pool": custom_converter_pool_example,
        "gui": run_gui_with_async,
        "submit": concurrent_report_submission,
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in examples:
        print("Usage: python async_client_example.py <example>")
        print("\nAvailable examples:")
        print("  headless - Run headless async service")
        print("  api      - Manual async API usage")
        print("  queue    - Custom pending queue configuration")
        print("  pool     - Custom converter pool configuration")
        print("  gui      - GUI integration with qasync")
        print("  submit   - Concurrent report submission")
        sys.exit(1)
    
    example_name = sys.argv[1]
    example_func = examples[example_name]
    
    if example_name == "gui":
        # GUI example runs its own event loop
        example_func()
    else:
        # Run async examples
        asyncio.run(example_func())
