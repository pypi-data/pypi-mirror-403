"""
Simple Queue for Offline Report Submission

Provides file-based queue for storing reports when offline.
All reports are stored in WSJF (WATS JSON Format).

For production deployments with robust file watching, converters,
and advanced retry logic, use pywats_client.ClientService instead.
"""

import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

from .formats import WSJFConverter
from ..shared.stats import QueueProcessingResult

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    """Status of a queued report."""
    PENDING = "pending"      # Waiting to be submitted
    SUBMITTING = "submitting"  # Currently being submitted
    ERROR = "error"          # Submission failed
    COMPLETED = "completed"  # Successfully submitted


@dataclass
class QueuedReport:
    """Represents a report in the queue."""
    
    file_path: Path
    status: QueueStatus
    created_at: datetime
    attempts: int = 0
    last_error: Optional[str] = None
    last_attempt: Optional[datetime] = None
    
    @property
    def file_name(self) -> str:
        """Get the file name."""
        return self.file_path.name
    
    @property
    def is_pending(self) -> bool:
        """Check if report is pending."""
        return self.status == QueueStatus.PENDING
    
    @property
    def is_error(self) -> bool:
        """Check if report has errors."""
        return self.status == QueueStatus.ERROR


class SimpleQueue:
    """
    Simple file-based queue for offline report submission.
    
    .. deprecated::
        SimpleQueue has file operations in the API layer which violates
        the "memory-only" design principle. Use instead:
        
        - pywats.queue.MemoryQueue: Pure in-memory queue (recommended for API)
        - pywats_client.queue.PersistentQueue: File-backed queue (recommended for client)
    
    Reports are stored in WSJF format with extensions:
    - .pending.wsjf - Pending submission
    - .submitting.wsjf - Currently being submitted
    - .error.wsjf - Submission failed
    - .completed.wsjf - Successfully submitted (deleted by default)
    
    Example:
        >>> from pywats import pyWATS
        >>> from pywats.queue import SimpleQueue
        >>> 
        >>> api = pyWATS(...)
        >>> queue = SimpleQueue(api, queue_dir="C:/WATS/Queue")
        >>> 
        >>> # Add report to queue
        >>> report = api.report.create_uut_report(...)
        >>> queue.add(report)
        >>> 
        >>> # Process queue
        >>> results = queue.process_all()
        >>> print(f"Submitted {results['success']} reports")
        >>> 
        >>> # Auto-process in background
        >>> queue.start_auto_process(interval_seconds=300)
    """
    
    def __init__(
        self,
        api,
        queue_dir: Union[str, Path],
        max_retries: int = 3,
        delete_completed: bool = True,
    ) -> None:
        """
        Initialize the queue.
        
        Args:
            api: pyWATS API instance
            queue_dir: Directory to store queued reports
            max_retries: Maximum retry attempts for failed reports
            delete_completed: Delete completed reports (default: True)
        """
        self._api = api
        self._queue_dir = Path(queue_dir)
        self._max_retries = max_retries
        self._delete_completed = delete_completed
        self._auto_process_task: Optional[asyncio.Task] = None
        
        # Create queue directory
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized SimpleQueue at {self._queue_dir}")
    
    def add(
        self,
        report_data: Union[Dict[str, Any], object],
        file_name: Optional[str] = None,
    ) -> Path:
        """
        Add a report to the queue.
        
        Args:
            report_data: Report dictionary or pydantic model
            file_name: Optional custom file name (without extension)
            
        Returns:
            Path to the queued file
            
        Example:
            >>> report = api.report.create_uut_report(...)
            >>> file_path = queue.add(report)
            >>> print(f"Queued at {file_path}")
        """
        # Convert to WSJF
        wsjf_data = WSJFConverter.to_wsjf(report_data)
        
        # Generate file name
        if file_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = f"report_{timestamp}"
        
        # Save to file
        file_path = self._queue_dir / f"{file_name}.pending.wsjf"
        file_path.write_text(wsjf_data, encoding='utf-8')
        
        logger.info(f"Added report to queue: {file_path}")
        return file_path
    
    def list_pending(self) -> List[QueuedReport]:
        """
        List all pending reports.
        
        Returns:
            List of pending reports
        """
        reports = []
        
        for file_path in self._queue_dir.glob("*.pending.wsjf"):
            reports.append(QueuedReport(
                file_path=file_path,
                status=QueueStatus.PENDING,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                attempts=0,
            ))
        
        return sorted(reports, key=lambda r: r.created_at)
    
    def list_errors(self) -> List[QueuedReport]:
        """
        List all reports with errors.
        
        Returns:
            List of reports with errors
        """
        reports = []
        
        for file_path in self._queue_dir.glob("*.error.wsjf"):
            # Read metadata if exists
            meta_path = file_path.with_suffix('.meta.json')
            meta = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                except:
                    pass
            
            reports.append(QueuedReport(
                file_path=file_path,
                status=QueueStatus.ERROR,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                attempts=meta.get('attempts', 0),
                last_error=meta.get('last_error'),
                last_attempt=datetime.fromisoformat(meta['last_attempt']) if meta.get('last_attempt') else None,
            ))
        
        return sorted(reports, key=lambda r: r.created_at)
    
    def count_pending(self) -> int:
        """Get count of pending reports."""
        return len(list(self._queue_dir.glob("*.pending.wsjf")))
    
    def count_errors(self) -> int:
        """Get count of error reports."""
        return len(list(self._queue_dir.glob("*.error.wsjf")))
    
    def process_all(self, include_errors: bool = True) -> QueueProcessingResult:
        """
        Process all reports in the queue.
        
        Args:
            include_errors: Also retry error reports (default: True)
            
        Returns:
            QueueProcessingResult with success/failure counts
            
        Example:
            >>> result = queue.process_all()
            >>> print(f"Success: {result.success}, Failed: {result.failed}")
            >>> print(f"Success rate: {result.success_rate:.1f}%")
        """
        result = QueueProcessingResult()
        
        # Process pending reports
        for queued_report in self.list_pending():
            if self._process_single(queued_report):
                result.success += 1
            else:
                result.failed += 1
        
        # Process error reports if requested
        if include_errors:
            for queued_report in self.list_errors():
                if queued_report.attempts < self._max_retries:
                    if self._process_single(queued_report):
                        result.success += 1
                    else:
                        result.failed += 1
                else:
                    result.skipped += 1
                    logger.warning(f"Skipping {queued_report.file_name} (max retries exceeded)")
        
        return result
    
    def _process_single(self, queued_report: QueuedReport) -> bool:
        """
        Process a single queued report.
        
        Args:
            queued_report: The report to process
            
        Returns:
            True if successful, False otherwise
        """
        file_path = queued_report.file_path
        
        try:
            # Mark as submitting
            submitting_path = file_path.with_name(
                file_path.name.replace('.pending.wsjf', '.submitting.wsjf')
                .replace('.error.wsjf', '.submitting.wsjf')
            )
            file_path.rename(submitting_path)
            
            # Read report data
            wsjf_data = submitting_path.read_text(encoding='utf-8')
            report_dict = WSJFConverter.from_wsjf(wsjf_data)
            
            # Submit to server
            self._api.report.submit(report_dict)
            
            # Success - mark as completed
            if self._delete_completed:
                submitting_path.unlink()
                # Delete metadata if exists
                meta_path = submitting_path.with_suffix('.meta.json')
                if meta_path.exists():
                    meta_path.unlink()
            else:
                completed_path = submitting_path.with_name(
                    submitting_path.name.replace('.submitting.wsjf', '.completed.wsjf')
                )
                submitting_path.rename(completed_path)
            
            logger.info(f"Successfully submitted {file_path.name}")
            return True
            
        except Exception as ex:
            # Failed - mark as error
            error_path = submitting_path.with_name(
                submitting_path.name.replace('.submitting.wsjf', '.error.wsjf')
            )
            submitting_path.rename(error_path)
            
            # Save metadata
            meta = {
                'attempts': queued_report.attempts + 1,
                'last_error': str(ex),
                'last_attempt': datetime.now().isoformat(),
            }
            meta_path = error_path.with_suffix('.meta.json')
            meta_path.write_text(json.dumps(meta, indent=2))
            
            logger.error(f"Failed to submit {file_path.name}: {ex}")
            return False
    
    def start_auto_process(self, interval_seconds: int = 300) -> None:
        """
        Start automatic background processing of the queue.
        
        Args:
            interval_seconds: Interval between processing runs (default: 300 = 5 minutes)
            
        Example:
            >>> queue.start_auto_process(interval_seconds=300)
            >>> # Queue will be processed every 5 minutes
        """
        if self._auto_process_task is not None:
            logger.warning("Auto-process already running")
            return
        
        async def auto_process_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    logger.info("Auto-processing queue...")
                    results = self.process_all()
                    logger.info(f"Auto-process results: {results}")
                except Exception as ex:
                    logger.error(f"Error in auto-process: {ex}")
        
        self._auto_process_task = asyncio.create_task(auto_process_loop())
        logger.info(f"Started auto-process (interval: {interval_seconds}s)")
    
    def stop_auto_process(self) -> None:
        """Stop automatic background processing."""
        if self._auto_process_task is not None:
            self._auto_process_task.cancel()
            self._auto_process_task = None
            logger.info("Stopped auto-process")
    
    def clear_completed(self) -> None:
        """Remove all completed reports."""
        count = 0
        for file_path in self._queue_dir.glob("*.completed.wsjf"):
            file_path.unlink()
            count += 1
        logger.info(f"Cleared {count} completed reports")
    
    def clear_errors(self) -> None:
        """Remove all error reports."""
        count = 0
        for file_path in self._queue_dir.glob("*.error.wsjf"):
            file_path.unlink()
            # Delete metadata
            meta_path = file_path.with_suffix('.meta.json')
            if meta_path.exists():
                meta_path.unlink()
            count += 1
        logger.info(f"Cleared {count} error reports")
