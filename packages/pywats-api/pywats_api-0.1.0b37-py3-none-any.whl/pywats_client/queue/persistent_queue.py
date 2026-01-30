"""
Persistent Queue for pyWATS Client

Extends the pure MemoryQueue with file-based persistence.
Uses the centralized file_utils for safe, atomic file operations.

Design:
    - Inherits from MemoryQueue for in-memory operations
    - Adds file persistence via hooks
    - Uses atomic writes to prevent corruption
    - Supports recovery from crash
    - Thread-safe and process-safe (with file locking)

Architecture:
    ┌─────────────────────────────────────────┐
    │  pywats.queue.MemoryQueue (Pure API)    │
    │  - In-memory only                       │
    │  - Thread-safe                          │
    │  - No file I/O                          │
    └──────────────────┬──────────────────────┘
                       │ extends
    ┌──────────────────▼──────────────────────┐
    │  pywats_client.queue.PersistentQueue    │
    │  - Adds file persistence                │
    │  - Uses file_utils for atomic writes    │
    │  - Supports crash recovery              │
    └─────────────────────────────────────────┘
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import asdict

from pywats.queue import MemoryQueue, QueueItem, QueueItemStatus, QueueHooks
from pywats.queue.formats import WSJFConverter

from ..core.file_utils import (
    SafeFileWriter,
    SafeFileReader,
    safe_delete,
    safe_rename,
    ensure_directory,
)

logger = logging.getLogger(__name__)


class PersistentQueue(MemoryQueue):
    """
    File-backed persistent queue extending MemoryQueue.
    
    Reports are stored in WSJF format with status-based extensions:
    - .pending.wsjf - Pending submission
    - .processing.wsjf - Currently being processed
    - .failed.wsjf - Processing failed
    - .completed.wsjf - Successfully processed
    
    Each item also has a metadata file:
    - .pending.meta.json - Metadata (attempts, errors, etc.)
    
    Example:
        >>> from pywats_client.queue import PersistentQueue
        >>> from pywats import pyWATS
        >>> 
        >>> api = pyWATS(...)
        >>> queue = PersistentQueue(queue_dir="C:/WATS/Queue")
        >>> 
        >>> # Add report to queue
        >>> report = api.report.create_uut_report(...)
        >>> item = queue.add(report)
        >>> 
        >>> # Process queue
        >>> for item in queue.list_pending():
        ...     item.mark_processing()
        ...     queue.update(item)
        ...     try:
        ...         api.report.submit(item.data)
        ...         item.mark_completed()
        ...     except Exception as e:
        ...         item.mark_failed(str(e))
        ...     queue.update(item)
    
    Recovery:
        On initialization, the queue loads all existing items from disk.
        Items marked as 'processing' are reset to 'pending' (crash recovery).
    """
    
    def __init__(
        self,
        queue_dir: Union[str, Path],
        max_size: Optional[int] = None,
        default_max_attempts: int = 3,
        delete_completed: bool = True,
        auto_load: bool = True,
    ) -> None:
        """
        Initialize the persistent queue.
        
        Args:
            queue_dir: Directory to store queued reports
            max_size: Maximum queue size (None = unlimited)
            default_max_attempts: Default retry attempts for new items
            delete_completed: Auto-delete completed items from disk
            auto_load: Load existing items from disk on init
        """
        super().__init__(max_size=max_size, default_max_attempts=default_max_attempts)
        
        self._queue_dir = Path(queue_dir)
        self._delete_completed = delete_completed
        
        # Ensure directory exists
        ensure_directory(self._queue_dir)
        
        # Load existing items
        if auto_load:
            self._load_from_disk()
        
        logger.info(f"Initialized PersistentQueue at {self._queue_dir}")
    
    @property
    def queue_dir(self) -> Path:
        """Get the queue directory path."""
        return self._queue_dir
    
    def add(
        self,
        data: Any,
        item_id: Optional[str] = None,
        max_attempts: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueueItem:
        """
        Add an item to the queue with file persistence.
        
        Args:
            data: The payload data (report dict, pydantic model, etc.)
            item_id: Optional custom ID
            max_attempts: Override default max attempts
            metadata: Optional metadata
            
        Returns:
            The created QueueItem
        """
        # Add to memory queue first
        item = super().add(data, item_id, max_attempts, metadata)
        
        # Persist to disk
        self._save_item(item)
        
        return item
    
    def update(self, item: QueueItem) -> None:
        """
        Update an item's status with file persistence.
        
        Args:
            item: The QueueItem to update
        """
        # Get old status for file rename
        old_item = self.get(item.id)
        old_status = old_item.status if old_item else None
        
        # Update in memory
        super().update(item)
        
        # Update on disk
        self._update_item_on_disk(item, old_status)
    
    def remove(self, item_id: str) -> bool:
        """
        Remove an item from the queue and disk.
        
        Args:
            item_id: ID of item to remove
            
        Returns:
            True if item was removed
        """
        # Get item info before removal
        item = self.get(item_id)
        
        # Remove from memory
        result = super().remove(item_id)
        
        # Remove from disk
        if result and item:
            self._delete_item_from_disk(item)
        
        return result
    
    def clear(self, status: Optional[QueueItemStatus] = None) -> int:
        """
        Clear items from the queue and disk.
        
        Args:
            status: Only clear items with this status (None = all items)
            
        Returns:
            Number of items cleared
        """
        # Get items to clear before removal
        if status is None:
            items_to_clear = list(self._items.values())
        else:
            items_to_clear = self.list_by_status(status)
        
        # Clear from memory
        count = super().clear(status)
        
        # Clear from disk
        for item in items_to_clear:
            self._delete_item_from_disk(item)
        
        return count
    
    def _load_from_disk(self) -> None:
        """Load existing items from disk on startup."""
        loaded = 0
        recovered = 0
        
        # Load items for each status
        for status in QueueItemStatus:
            pattern = f"*.{status.value}.wsjf"
            
            for data_path in self._queue_dir.glob(pattern):
                try:
                    item = self._load_item_from_file(data_path, status)
                    if item:
                        # Recovery: reset processing items to pending
                        if item.status == QueueItemStatus.PROCESSING:
                            item.reset_to_pending()
                            recovered += 1
                        
                        self._items[item.id] = item
                        self._order.append(item.id)
                        loaded += 1
                        
                except Exception as ex:
                    logger.warning(f"Failed to load {data_path}: {ex}")
        
        if loaded > 0:
            logger.info(f"Loaded {loaded} items from disk ({recovered} recovered from processing)")
    
    def _load_item_from_file(self, data_path: Path, status: QueueItemStatus) -> Optional[QueueItem]:
        """Load a single item from disk."""
        # Read WSJF data
        wsjf_data = SafeFileReader.read_text_safe(data_path)
        if wsjf_data is None:
            return None
        
        # Parse report data
        try:
            report_data = WSJFConverter.from_wsjf(wsjf_data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {data_path}")
            return None
        
        # Extract item ID from filename
        # Format: report_20240115_120000_abc123.pending.wsjf
        item_id = data_path.stem.replace(f".{status.value}", "")
        
        # Read metadata if exists
        meta_path = data_path.with_suffix('.meta.json')
        metadata = SafeFileReader.read_json_safe(meta_path, default={})
        
        # Create QueueItem
        item = QueueItem(
            id=item_id,
            data=report_data,
            status=status,
            created_at=datetime.fromtimestamp(data_path.stat().st_ctime),
            updated_at=datetime.fromtimestamp(data_path.stat().st_mtime),
            attempts=metadata.get('attempts', 0),
            max_attempts=metadata.get('max_attempts', self._default_max_attempts),
            last_error=metadata.get('last_error'),
            metadata=metadata.get('custom', {}),
        )
        
        return item
    
    def _save_item(self, item: QueueItem) -> None:
        """Save an item to disk."""
        # Generate file paths
        data_path = self._get_data_path(item)
        meta_path = self._get_meta_path(item)
        
        # Convert data to WSJF
        wsjf_data = WSJFConverter.to_wsjf(item.data)
        
        # Write data file atomically
        result = SafeFileWriter.write_text_atomic(data_path, wsjf_data)
        if not result.success:
            logger.error(f"Failed to save item {item.id}: {result.error}")
            return
        
        # Write metadata file
        meta = {
            'id': item.id,
            'status': item.status.value,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
            'attempts': item.attempts,
            'max_attempts': item.max_attempts,
            'last_error': item.last_error,
            'custom': item.metadata,
        }
        SafeFileWriter.write_json_atomic(meta_path, meta)
        
        logger.debug(f"Saved item {item.id} to {data_path}")
    
    def _update_item_on_disk(self, item: QueueItem, old_status: Optional[QueueItemStatus]) -> None:
        """Update an item on disk (may involve rename if status changed)."""
        if old_status and old_status != item.status:
            # Status changed - need to rename files
            old_data_path = self._get_data_path_for_status(item.id, old_status)
            old_meta_path = self._get_meta_path_for_status(item.id, old_status)
            
            new_data_path = self._get_data_path(item)
            new_meta_path = self._get_meta_path(item)
            
            # Rename data file
            if old_data_path.exists():
                safe_rename(old_data_path, new_data_path, overwrite=True)
            else:
                # Data file missing - recreate
                wsjf_data = WSJFConverter.to_wsjf(item.data)
                SafeFileWriter.write_text_atomic(new_data_path, wsjf_data)
            
            # Rename or recreate metadata
            if old_meta_path.exists():
                safe_rename(old_meta_path, new_meta_path, overwrite=True)
            
            # Update metadata content
            meta = {
                'id': item.id,
                'status': item.status.value,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat(),
                'attempts': item.attempts,
                'max_attempts': item.max_attempts,
                'last_error': item.last_error,
                'custom': item.metadata,
            }
            SafeFileWriter.write_json_atomic(new_meta_path, meta)
            
            logger.debug(f"Renamed item {item.id} from {old_status.value} to {item.status.value}")
            
            # Handle completed items
            if item.status == QueueItemStatus.COMPLETED and self._delete_completed:
                self._delete_item_from_disk(item)
        else:
            # Status unchanged - just update metadata
            meta_path = self._get_meta_path(item)
            meta = {
                'id': item.id,
                'status': item.status.value,
                'created_at': item.created_at.isoformat(),
                'updated_at': item.updated_at.isoformat(),
                'attempts': item.attempts,
                'max_attempts': item.max_attempts,
                'last_error': item.last_error,
                'custom': item.metadata,
            }
            SafeFileWriter.write_json_atomic(meta_path, meta)
    
    def _delete_item_from_disk(self, item: QueueItem) -> None:
        """Delete an item's files from disk."""
        data_path = self._get_data_path(item)
        meta_path = self._get_meta_path(item)
        
        safe_delete(data_path)
        safe_delete(meta_path)
        
        logger.debug(f"Deleted item {item.id} from disk")
    
    def _get_data_path(self, item: QueueItem) -> Path:
        """Get the data file path for an item."""
        return self._get_data_path_for_status(item.id, item.status)
    
    def _get_data_path_for_status(self, item_id: str, status: QueueItemStatus) -> Path:
        """Get the data file path for an item with specific status."""
        return self._queue_dir / f"{item_id}.{status.value}.wsjf"
    
    def _get_meta_path(self, item: QueueItem) -> Path:
        """Get the metadata file path for an item."""
        return self._get_meta_path_for_status(item.id, item.status)
    
    def _get_meta_path_for_status(self, item_id: str, status: QueueItemStatus) -> Path:
        """Get the metadata file path for an item with specific status."""
        return self._queue_dir / f"{item_id}.{status.value}.meta.json"
    
    # Convenience methods for batch operations
    def process_pending(
        self,
        processor: callable,
        include_failed: bool = True,
    ) -> Dict[str, int]:
        """
        Process all pending items with a processor function.
        
        Args:
            processor: Function that takes (item_data) and returns True on success
            include_failed: Also process failed items that can retry
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        items_to_process = self.list_pending()
        
        if include_failed:
            for item in self.list_failed():
                if item.can_retry:
                    items_to_process.append(item)
                else:
                    results["skipped"] += 1
        
        for item in items_to_process:
            item.mark_processing()
            self.update(item)
            
            try:
                if processor(item.data):
                    item.mark_completed()
                    results["success"] += 1
                else:
                    item.mark_failed("Processor returned False")
                    results["failed"] += 1
            except Exception as ex:
                item.mark_failed(str(ex))
                results["failed"] += 1
            
            self.update(item)
        
        return results
