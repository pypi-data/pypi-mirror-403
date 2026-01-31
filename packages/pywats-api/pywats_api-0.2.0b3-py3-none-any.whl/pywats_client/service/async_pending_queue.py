"""
Async Pending Queue - Concurrent report uploads with asyncio

Async-first implementation of the pending report queue.
Uses asyncio.Semaphore for concurrent uploads instead of sequential processing.

Benefits over sync PendingWatcher:
- Concurrent uploads (N at a time vs 1 at a time)
- Non-blocking file I/O
- Automatic retry with exponential backoff
- Graceful shutdown (complete in-flight uploads)

Performance improvement:
- 100 reports with 200ms latency: ~20s (sync) → ~4s (async with 5 concurrent)

See CLIENT_ASYNC_ARCHITECTURE.md for design details.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

if TYPE_CHECKING:
    from pywats import AsyncWATS

logger = logging.getLogger(__name__)


class AsyncPendingQueueState(Enum):
    """State of the pending queue"""
    CREATED = "Created"
    RUNNING = "Running"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    PAUSED = "Paused"


class AsyncPendingQueue:
    """
    Async pending report queue with concurrent uploads.
    
    Benefits:
    - Uploads N reports concurrently (default: 5)
    - Uses asyncio.Semaphore for backpressure
    - Automatic retry with exponential backoff
    - Graceful shutdown (complete in-flight uploads)
    
    File states (extensions):
    - .queued: Ready to upload
    - .processing: Currently uploading
    - .error: Upload failed (retry after delay)
    - .completed: Successfully uploaded
    
    Usage:
        queue = AsyncPendingQueue(api, reports_dir, max_concurrent=5)
        await queue.run()  # Runs until stopped
        await queue.stop()
    """
    
    # File patterns
    FILTER_QUEUED = "*.queued"
    FILTER_PROCESSING = "*.processing"
    FILTER_ERROR = "*.error"
    
    # Timeouts
    PROCESSING_TIMEOUT = timedelta(minutes=30)
    ERROR_RETRY_DELAY = timedelta(minutes=5)
    PERIODIC_CHECK_INTERVAL = 60.0  # seconds
    
    # Queue limits
    DEFAULT_MAX_QUEUE_SIZE = 10000  # Default max reports in queue (0 = unlimited)
    
    def __init__(
        self,
        api: 'AsyncWATS',
        reports_dir: Path,
        max_concurrent: int = 5,
        max_queue_size: int = 0
    ) -> None:
        """
        Initialize async pending queue.
        
        Args:
            api: AsyncWATS API client
            reports_dir: Directory containing queued report files
            max_concurrent: Maximum concurrent uploads
            max_queue_size: Maximum reports allowed in queue (0 = unlimited)
        """
        self.api = api
        self.reports_dir = Path(reports_dir)
        self._max_queue_size = max_queue_size
        self._max_concurrent = max_concurrent
        
        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0  # Track active uploads explicitly (not _semaphore._value)
        
        # State
        self.state = AsyncPendingQueueState.CREATED
        self._stop_event = asyncio.Event()
        self._active_uploads: set[asyncio.Task] = set()  # Use set to avoid race conditions
        
        # Event loop reference (for thread-safe signaling from watchdog)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # File watcher
        self._observer: Optional[Observer] = None
        self._new_file_event = asyncio.Event()
        
        # Statistics
        self._stats: Dict[str, Any] = {
            "total_submitted": 0,
            "successful": 0,
            "errors": 0,
            "retries": 0,
            "queued_files": 0,
            "stuck_files": 0,
            "active_uploads": 0,
            "max_queue_size": max_queue_size
        }
        
        # Ensure directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        limit_info = f", max_queue_size={max_queue_size}" if max_queue_size > 0 else ""
        logger.info(
            f"AsyncPendingQueue initialized "
            f"(dir={reports_dir}, max_concurrent={max_concurrent}{limit_info})"
        )
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        self._update_stats()
        return self._stats.copy()
    
    @property
    def is_running(self) -> bool:
        """Check if queue is running"""
        return self.state == AsyncPendingQueueState.RUNNING
    
    @property
    def queue_size(self) -> int:
        """Get current number of queued files"""
        return len(list(self.reports_dir.glob(self.FILTER_QUEUED)))
    
    @property
    def is_queue_full(self) -> bool:
        """Check if queue has reached maximum capacity"""
        if self._max_queue_size <= 0:
            return False  # No limit
        return self.queue_size >= self._max_queue_size
    
    def can_accept_report(self) -> tuple[bool, str]:
        """
        Check if queue can accept a new report.
        
        Returns:
            Tuple of (can_accept, reason_if_not)
        """
        if self._max_queue_size <= 0:
            return True, ""
        
        current = self.queue_size
        if current >= self._max_queue_size:
            return False, f"Queue full: {current}/{self._max_queue_size} reports"
        return True, ""
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    async def run(self) -> None:
        """
        Main queue processing loop.
        
        Watches for new files and submits them concurrently.
        """
        if self.state == AsyncPendingQueueState.RUNNING:
            logger.warning("Queue already running")
            return
        
        self.state = AsyncPendingQueueState.RUNNING
        self._stop_event.clear()
        
        # Store loop reference for thread-safe signaling from watchdog
        self._loop = asyncio.get_running_loop()
        
        logger.info("AsyncPendingQueue starting...")
        
        try:
            # Start file watcher
            self._start_watcher()
            
            # Initial submission of existing queued files
            await self.submit_all_pending()
            
            # Main loop: wait for new files or periodic check
            while not self._stop_event.is_set():
                try:
                    # Wait for new file event or timeout
                    await asyncio.wait_for(
                        self._new_file_event.wait(),
                        timeout=self.PERIODIC_CHECK_INTERVAL
                    )
                    self._new_file_event.clear()
                except asyncio.TimeoutError:
                    pass
                
                # Submit pending files
                await self.submit_all_pending()
                
                # Recover stuck files
                await self._recover_stuck_files()
                
                # Retry error files
                await self._retry_error_files()
                
        except asyncio.CancelledError:
            logger.info("Queue cancelled")
        finally:
            self.state = AsyncPendingQueueState.STOPPED
    
    async def stop(self) -> None:
        """
        Stop the queue gracefully.
        
        Waits for in-flight uploads to complete (with timeout).
        """
        if self.state == AsyncPendingQueueState.STOPPED:
            return
        
        logger.info("Stopping AsyncPendingQueue...")
        self.state = AsyncPendingQueueState.STOPPING
        self._stop_event.set()
        
        # Stop file watcher
        if self._observer:
            self._observer.stop()
            self._observer = None
        
        # Wait for active uploads (with timeout)
        active_tasks = list(self._active_uploads)  # Copy to avoid modification during iteration
        if active_tasks:
            logger.info(f"Waiting for {len(active_tasks)} uploads...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*active_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Upload tasks timed out, cancelling...")
                for task in active_tasks:
                    task.cancel()
        
        self._active_uploads.clear()
        self._loop = None  # Clear loop reference
        self.state = AsyncPendingQueueState.STOPPED
        logger.info("AsyncPendingQueue stopped")
    
    # =========================================================================
    # File Watching
    # =========================================================================
    
    def _start_watcher(self) -> None:
        """Start file system watcher for queued files"""
        handler = _QueueFileHandler(self)
        
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.reports_dir),
            recursive=False
        )
        self._observer.start()
        logger.debug("File watcher started")
    
    def _on_file_queued(self, file_path: Path) -> None:
        """Handle new queued file (called from watchdog thread - NOT async safe!)"""
        if file_path.suffix == '.queued':
            # IMPORTANT: This is called from watchdog's thread, not the asyncio thread.
            # asyncio.Event.set() is NOT thread-safe, so we must use call_soon_threadsafe
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._new_file_event.set)
            else:
                # Fallback for edge cases (loop not yet running)
                self._new_file_event.set()
    
    # =========================================================================
    # Submission
    # =========================================================================
    
    async def submit_all_pending(self) -> None:
        """Submit all pending (.queued) reports concurrently"""
        # Get all queued files, sorted by modification time
        queued_files = sorted(
            self.reports_dir.glob(self.FILTER_QUEUED),
            key=lambda p: p.stat().st_mtime
        )
        
        if not queued_files:
            return
        
        logger.info(f"Submitting {len(queued_files)} queued reports...")
        
        # Submit all files concurrently (semaphore limits actual concurrency)
        tasks = [
            asyncio.create_task(self._submit_with_limit(f))
            for f in queued_files
        ]
        
        # Add tasks to tracking set
        for task in tasks:
            self._active_uploads.add(task)
            # Auto-remove when done (avoids race condition)
            task.add_done_callback(lambda t: self._active_uploads.discard(t))
        
        # Wait for all to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _submit_with_limit(self, file_path: Path) -> None:
        """Submit single report with semaphore limiting"""
        async with self._semaphore:
            self._active_count += 1
            self._stats["active_uploads"] = self._active_count
            try:
                await self._submit_report(file_path)
            finally:
                self._active_count -= 1
                self._stats["active_uploads"] = self._active_count
    
    async def _submit_report(self, file_path: Path) -> None:
        """
        Submit a single report file.
        
        State machine:
        .queued -> .processing -> .completed (success)
        .queued -> .processing -> .error (failure)
        """
        if not file_path.exists():
            return
        
        # Rename to .processing (atomic state transition)
        processing_path = file_path.with_suffix('.processing')
        
        try:
            file_path.rename(processing_path)
        except FileNotFoundError:
            return  # File already processed by another worker
        except Exception as e:
            logger.error(f"Failed to rename {file_path.name}: {e}")
            return
        
        logger.debug(f"Submitting: {processing_path.name}")
        
        try:
            # Read report data (async I/O)
            content = await self._read_file(processing_path)
            report_data = json.loads(content)
            
            # Submit to WATS (async HTTP)
            await self.api.report.submit_raw(report_data)
            
            # Success - mark as completed
            completed_path = processing_path.with_suffix('.completed')
            processing_path.rename(completed_path)
            
            self._stats["total_submitted"] += 1
            self._stats["successful"] += 1
            
            logger.info(f"Submitted: {file_path.name}")
            
            # Optionally delete completed file
            # completed_path.unlink()
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path.name}: {e}")
            await self._mark_error(processing_path, f"Invalid JSON: {e}")
            
        except Exception as e:
            logger.error(f"Submit failed for {file_path.name}: {e}")
            await self._mark_error(processing_path, str(e))
    
    async def _mark_error(self, file_path: Path, error: str) -> None:
        """Mark a file as error (for retry later)"""
        error_path = file_path.with_suffix('.error')
        
        try:
            file_path.rename(error_path)
            
            # Write error info to sidecar file
            error_info_path = error_path.with_suffix('.error.info')
            info = {
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "attempts": 1
            }
            
            if HAS_AIOFILES:
                async with aiofiles.open(error_info_path, 'w') as f:
                    await f.write(json.dumps(info, indent=2))
            else:
                error_info_path.write_text(json.dumps(info, indent=2))
            
            self._stats["errors"] += 1
            
        except Exception as e:
            logger.error(f"Failed to mark error: {e}")
    
    # =========================================================================
    # Recovery
    # =========================================================================
    
    async def _recover_stuck_files(self) -> None:
        """
        Recover files stuck in .processing state.
        
        Files are considered stuck if in .processing for > 30 minutes.
        """
        processing_files = list(self.reports_dir.glob(self.FILTER_PROCESSING))
        stuck_count = 0
        
        for file_path in processing_files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age = datetime.now() - mtime
                
                if age > self.PROCESSING_TIMEOUT:
                    logger.warning(f"Recovering stuck file: {file_path.name}")
                    
                    # Move back to .queued for retry
                    queued_path = file_path.with_suffix('.queued')
                    file_path.rename(queued_path)
                    
                    stuck_count += 1
                    
            except Exception as e:
                logger.error(f"Recovery error for {file_path.name}: {e}")
        
        self._stats["stuck_files"] = stuck_count
    
    async def _retry_error_files(self) -> None:
        """
        Retry files in .error state after retry delay.
        """
        error_files = list(self.reports_dir.glob(self.FILTER_ERROR))
        
        for file_path in error_files:
            # Skip .error.info files
            if '.error.info' in file_path.name:
                continue
            
            try:
                # Check error info for retry timing
                info_path = file_path.with_suffix('.error.info')
                
                if info_path.exists():
                    info = json.loads(info_path.read_text())
                    error_time = datetime.fromisoformat(info.get('timestamp', ''))
                    attempts = info.get('attempts', 0)
                    
                    # Exponential backoff: 5min, 10min, 20min, etc.
                    retry_delay = self.ERROR_RETRY_DELAY * (2 ** (attempts - 1))
                    
                    if datetime.now() - error_time < retry_delay:
                        continue  # Not ready for retry yet
                    
                    # Max 5 retries
                    if attempts >= 5:
                        logger.warning(f"Max retries exceeded: {file_path.name}")
                        continue
                    
                    # Update attempt count
                    info['attempts'] = attempts + 1
                    info_path.write_text(json.dumps(info, indent=2))
                
                # Move back to .queued for retry
                logger.info(f"Retrying: {file_path.name}")
                queued_path = file_path.with_suffix('.queued')
                file_path.rename(queued_path)
                
                self._stats["retries"] += 1
                
            except Exception as e:
                logger.error(f"Retry error for {file_path.name}: {e}")
    
    # =========================================================================
    # Utilities
    # =========================================================================
    
    async def _read_file(self, file_path: Path) -> str:
        """Read file content asynchronously"""
        if HAS_AIOFILES:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            return await asyncio.to_thread(
                file_path.read_text,
                encoding='utf-8'
            )
    
    def _update_stats(self) -> None:
        """Update queue statistics"""
        try:
            self._stats["queued_files"] = len(
                list(self.reports_dir.glob(self.FILTER_QUEUED))
            )
        except Exception:
            pass


class _QueueFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler for queue directory.
    
    Signals when new .queued files appear.
    """
    
    def __init__(self, queue: AsyncPendingQueue) -> None:
        super().__init__()
        self.queue = queue
    
    def on_created(self, event) -> None:
        """Handle file creation"""
        if not event.is_directory:
            self.queue._on_file_queued(Path(event.src_path))
    
    def on_moved(self, event) -> None:
        """Handle file rename (e.g., .tmp -> .queued)"""
        if not event.is_directory:
            self.queue._on_file_queued(Path(event.dest_path))
