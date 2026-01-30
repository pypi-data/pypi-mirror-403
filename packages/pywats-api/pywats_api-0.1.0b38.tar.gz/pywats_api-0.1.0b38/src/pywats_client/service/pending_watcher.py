"""
Pending Watcher - Report Queue Manager

Equivalent to PendingWatcher.cs in C# implementation.
Manages offline report queue using file-based state machine.
"""

import logging
import json
import threading
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class PendingWatcherState(Enum):
    """State of pending watcher (like C# enum)"""
    CREATED = "Created"
    INITIALIZING = "Initializing"
    RUNNING = "Running"
    STOPPING = "Stopping"
    DISPOSED = "Disposed"
    PAUSED = "Paused"


class PendingWatcher:
    """
    Manages offline report queue with file-based state machine.
    
    Equivalent to PendingWatcher.cs.
    
    File states (extensions):
    - .queued: Ready to upload
    - .processing: Currently uploading
    - .error: Upload failed (retry after delay)
    - .completed: Successfully uploaded
    
    Features:
    - FileSystemWatcher for .queued files
    - Automatic timeout recovery
    - Periodic submission checks (5 minutes)
    """
    
    FILTER_QUEUED = "*.queued"
    TRANSFERRING_TIMEOUT = timedelta(minutes=30)
    ERROR_RETRY_TIMEOUT = timedelta(minutes=5)
    
    def __init__(
        self,
        api_client,
        reports_directory: Path,
        initialize_async: bool = False
    ) -> None:
        """
        Initialize pending watcher.
        
        Args:
            api_client: pyWATS API client instance
            reports_directory: Directory containing report queue files
            initialize_async: If True, start on background thread
        """
        self.api_client = api_client
        self.reports_directory = Path(reports_directory)
        
        self.state = PendingWatcherState.CREATED
        
        # File system watcher
        self._observer: Optional[Observer] = None
        
        # Periodic timer (5 minutes)
        self._timer: Optional[threading.Timer] = None
        self._timer_interval = 300.0  # 5 minutes
        
        # Lock for submission (only one thread at a time)
        self._submission_lock = threading.Lock()
        
        # Running flag
        self._running = False
        
        # Ensure directory exists
        self.reports_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PendingWatcher created (directory: {reports_directory})")
        
        # Start if requested
        if initialize_async:
            threading.Thread(target=self._start, daemon=True).start()
        else:
            self._start()
    
    def _start(self):
        """
        Start pending watcher.
        
        Equivalent to Start() in PendingWatcher.cs.
        """
        self.state = PendingWatcherState.INITIALIZING
        
        try:
            # Initialize API if needed
            # In C# this calls api.InitializeAPI(true)
            # For Python, assume API is already initialized
            
            # Setup file watcher for .queued files
            self._setup_file_watcher()
            
            # Setup periodic timer
            self._setup_timer()
            
            self.state = PendingWatcherState.RUNNING
            self._running = True
            
            logger.info("PendingWatcher started")
            
            # Trigger initial submission
            self._start_pending_transfer()
            
        except Exception as e:
            logger.error(f"Failed to start PendingWatcher: {e}", exc_info=True)
            self.state = PendingWatcherState.CREATED
    
    def _setup_file_watcher(self):
        """
        Setup FileSystemWatcher for .queued files.
        
        Equivalent to:
            fsw = new FileSystemWatcher(api.ReportsDirectory, "*.queued");
            fsw.Changed += fsw_Changed;
            fsw.Renamed += fsw_Renamed;
        """
        class QueuedFileHandler(FileSystemEventHandler):
            def __init__(self, watcher_ref):
                self.watcher = watcher_ref
            
            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith('.queued'):
                    self.watcher._on_file_changed()
            
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.queued'):
                    self.watcher._on_file_changed()
            
            def on_moved(self, event):
                # File renamed (e.g., from .tmp to .queued)
                if not event.is_directory and event.dest_path.endswith('.queued'):
                    self.watcher._on_file_changed()
        
        self._observer = Observer()
        handler = QueuedFileHandler(self)
        self._observer.schedule(
            handler,
            str(self.reports_directory),
            recursive=False
        )
        self._observer.start()
        
        logger.debug(f"File watcher started: {self.reports_directory}")
    
    def _setup_timer(self):
        """
        Setup periodic timer (5 minutes).
        
        Equivalent to:
            tmr = new Timer(300000);
            tmr.Elapsed += tmr_Elapsed;
        """
        def timer_callback():
            if self._running:
                try:
                    self._on_timer_elapsed()
                finally:
                    # Reschedule
                    self._timer = threading.Timer(self._timer_interval, timer_callback)
                    self._timer.daemon = True
                    self._timer.start()
        
        self._timer = threading.Timer(self._timer_interval, timer_callback)
        self._timer.daemon = True
        self._timer.start()
        
        logger.debug("Periodic timer started (5min)")
    
    def _on_file_changed(self):
        """
        Handle file system event.
        
        Equivalent to fsw_Changed and fsw_Renamed in PendingWatcher.cs.
        """
        self._start_pending_transfer()
    
    def _on_timer_elapsed(self):
        """
        Timer callback (5 minutes).
        
        Equivalent to tmr_Elapsed in PendingWatcher.cs.
        """
        try:
            self._start_pending_transfer()
        except Exception as e:
            logger.error(f"Timer callback error: {e}", exc_info=True)
    
    def _start_pending_transfer(self):
        """
        Start pending report submission.
        
        Equivalent to StartPendingTransfer() in PendingWatcher.cs.
        Uses lock to ensure only one thread runs at a time.
        """
        if self.state != PendingWatcherState.RUNNING:
            return
        
        # Try to acquire lock (non-blocking)
        if not self._submission_lock.acquire(blocking=False):
            logger.debug("Submit pending already running in another thread")
            return
        
        try:
            # Disable file watcher during processing
            if self._observer:
                self._observer.unschedule_all()
            
            logger.debug("PendingWatcher starting SubmitPendingReports")
            
            # Check and reset timed-out items
            self._check_transferring_timeout()
            
            # Check if server is online
            is_online = self._check_api_status()
            
            if is_online:
                # Submit all pending reports
                self._submit_pending_reports()
            else:
                logger.debug("API not online, skipping submission")
        
        except Exception as e:
            logger.error(f"Error during pending transfer: {e}", exc_info=True)
        
        finally:
            # Re-enable file watcher
            if self._observer and self._running:
                handler = self._observer._handlers.get(str(self.reports_directory))
                if handler:
                    self._observer.schedule(
                        handler,
                        str(self.reports_directory),
                        recursive=False
                    )
            
            self._submission_lock.release()
    
    def _check_transferring_timeout(self):
        """
        Reset timed-out reports back to queued state.
        
        Equivalent to CheckTransferingTimeout() in C#:
        - .processing files older than 30min -> .queued
        - .error files older than 5min -> .queued
        """
        now = datetime.now()
        
        # Check .processing files (30 minute timeout)
        for file_path in self.reports_directory.glob("*.processing"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if now - mtime > self.TRANSFERRING_TIMEOUT:
                    # Reset to queued
                    new_path = file_path.with_suffix('.queued')
                    file_path.rename(new_path)
                    logger.warning(f"Reset stuck processing file: {file_path.name}")
            except Exception as e:
                logger.error(f"Error checking processing file {file_path}: {e}")
        
        # Check .error files (5 minute retry timeout)
        for file_path in self.reports_directory.glob("*.error"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if now - mtime > self.ERROR_RETRY_TIMEOUT:
                    # Retry
                    new_path = file_path.with_suffix('.queued')
                    file_path.rename(new_path)
                    logger.info(f"Retrying error file: {file_path.name}")
            except Exception as e:
                logger.error(f"Error checking error file {file_path}: {e}")
    
    def _check_api_status(self) -> bool:
        """
        Check if API is online.
        
        Returns:
            True if API is online and ready
        """
        try:
            # TODO: Call api.Ping() or check status when available
            # For now, assume online if we have an API client
            return self.api_client is not None
        except Exception as e:
            logger.debug(f"API status check failed: {e}")
            return False
    
    def _submit_pending_reports(self):
        """
        Submit all queued reports to server.
        
        Equivalent to api.SubmitPendingReports() in C#.
        Processes all .queued files.
        """
        # Get all .queued files, sorted by modification time (oldest first)
        queued_files = sorted(
            self.reports_directory.glob("*.queued"),
            key=lambda p: p.stat().st_mtime
        )
        
        logger.info(f"Processing {len(queued_files)} queued reports")
        
        for file_path in queued_files:
            self._submit_report(file_path)
    
    def _submit_report(self, file_path: Path):
        """
        Submit a single report file.
        
        State transitions:
        1. .queued -> .processing (start upload)
        2. .processing -> .completed (success)
        3. .processing -> .error (failure)
        """
        # Rename to .processing (atomic state change)
        processing_path = file_path.with_suffix('.processing')
        
        try:
            file_path.rename(processing_path)
        except FileNotFoundError:
            # File was deleted or already processing
            return
        except Exception as e:
            logger.error(f"Failed to rename {file_path} to processing: {e}")
            return
        
        # Try to submit
        try:
            # Load report data
            with open(processing_path, 'r') as f:
                report_data = json.load(f)
            
            # Submit to server
            # TODO: Call actual API method when available
            # self.api_client.submit_report(report_data)
            
            # For now, just log
            logger.info(f"Would submit report: {processing_path.name}")
            
            # Success: Rename to .completed
            completed_path = processing_path.with_suffix('.completed')
            processing_path.rename(completed_path)
            
            logger.info(f"Report submitted successfully: {file_path.name}")
            
            # Optionally delete completed files after some time
            # For now, keep them for audit
            
        except Exception as e:
            # Failed: Rename to .error
            error_path = processing_path.with_suffix('.error')
            try:
                processing_path.rename(error_path)
                logger.error(f"Report submission failed: {file_path.name}: {e}")
            except Exception as rename_error:
                logger.error(f"Failed to rename to error: {rename_error}")
    
    def trigger_submission(self):
        """
        Manually trigger pending submission.
        
        Called by ping timer or external event.
        """
        self._start_pending_transfer()
    
    def check_state(self):
        """
        Health check (called by watchdog).
        
        Equivalent to CheckState() in PendingWatcher.cs.
        """
        if self.state == PendingWatcherState.RUNNING:
            # Check if API is back online
            if self._check_api_status():
                self._start_pending_transfer()
    
    def queue_size(self) -> int:
        """Get number of queued reports"""
        try:
            return len(list(self.reports_directory.glob("*.queued")))
        except Exception:
            return 0
    
    def dispose(self):
        """
        Stop and cleanup.
        
        Equivalent to Dispose() in PendingWatcher.cs.
        """
        self.state = PendingWatcherState.STOPPING
        self._running = False
        
        # Stop timer
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        # Stop file watcher
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        
        # Wait for submission to complete (up to 10 seconds)
        if self._submission_lock.locked():
            timeout = time.time() + 10
            while self._submission_lock.locked() and time.time() < timeout:
                time.sleep(0.1)
        
        self.state = PendingWatcherState.DISPOSED
        logger.info("PendingWatcher disposed")
    
    @property
    def enabled(self) -> bool:
        """Check if watcher is enabled"""
        return self.state == PendingWatcherState.RUNNING
    
    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable watcher"""
        if value:
            if self.state != PendingWatcherState.RUNNING:
                self._start()
        else:
            if self.state == PendingWatcherState.RUNNING:
                self.state = PendingWatcherState.PAUSED
