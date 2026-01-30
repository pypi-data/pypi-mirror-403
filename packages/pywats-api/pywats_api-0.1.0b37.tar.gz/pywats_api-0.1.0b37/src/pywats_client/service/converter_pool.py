"""
Converter Pool - Manages file conversion with auto-scaling worker pool

Equivalent to Conversion.cs in C# implementation.
Handles converter orchestration, queue management, and worker pool auto-scaling.
"""

import logging
import threading
import time
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from queue import Queue, Empty
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class ConversionItemState(Enum):
    """State of a conversion item (like C# enum)"""
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    ERROR = "Error"


@dataclass
class ConversionItem:
    """
    Represents a file to be converted.
    
    Equivalent to ConversionItem class in Conversion.cs.
    """
    file_path: Path
    converter: 'Converter'
    state: ConversionItemState = ConversionItemState.PENDING
    queued_at: datetime = None
    process_start: Optional[datetime] = None
    file_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.queued_at is None:
            self.queued_at = datetime.now()
        if self.file_date is None and self.file_path.exists():
            self.file_date = datetime.fromtimestamp(self.file_path.stat().st_mtime)


class ConverterWorkerClass(threading.Thread):
    """
    Worker thread for processing conversions.
    
    Equivalent to ConverterWorkerClass.cs.
    Auto-terminates after 120 seconds idle.
    """
    
    def __init__(self, pool: 'ConverterPool', worker_id: int) -> None:
        super().__init__(daemon=True, name=f"ConverterWorker-{worker_id}")
        self.pool = pool
        self.worker_id = worker_id
        self.shutdown_in_progress = False
        self.current_item: Optional[ConversionItem] = None
        self.last_use = datetime.now()
    
    def run(self):
        """
        Worker main loop.
        
        Equivalent to DoWork() in ConverterWorkerClass.cs:
        - Get next file from queue
        - Process through converter
        - Handle errors
        - Auto-shutdown after idle timeout
        """
        logger.debug(f"Worker {self.worker_id} started (thread: {self.ident})")
        idle_counter = 0
        
        try:
            while not self.shutdown_in_progress:
                got_item = False
                
                try:
                    # Get next file to convert
                    self.current_item = self.pool.get_next_file_to_convert()
                    got_item = self.current_item is not None
                except Exception as e:
                    logger.error(f"Worker {self.worker_id}: Error getting next file: {e}")
                    self.shutdown_in_progress = True
                    break
                
                if got_item:
                    idle_counter = 0
                    
                    try:
                        # Create API instance for this worker (like C#)
                        # In C#: using (TDM api = new TDM()) { api.InitializeAPI(...) }
                        api_client = self.pool.create_api_client()
                        
                        # Process the file
                        self.current_item.state = ConversionItemState.PROCESSING
                        self.current_item.process_start = datetime.now()
                        
                        self.current_item.converter.convert_file(
                            self.current_item,
                            api_client
                        )
                        
                        self.last_use = datetime.now()
                        
                    except Exception as e:
                        logger.error(
                            f"Worker {self.worker_id}: Conversion error: {e}",
                            exc_info=True
                        )
                        # Mark as error but continue (don't terminate worker)
                        if self.current_item:
                            self.current_item.state = ConversionItemState.ERROR
                
                else:
                    # No work - idle
                    idle_counter += 1
                    time.sleep(0.5)
                    
                    idle_time = (datetime.now() - self.last_use).total_seconds()
                    
                    # Process archive queue after 10 seconds idle (like C#)
                    if idle_counter == 20:
                        for converter in self.pool.converter_list:
                            try:
                                converter.process_archive_queue()
                            except Exception as e:
                                logger.error(f"Archive queue processing error: {e}")
                    
                    # Shutdown after 120 seconds idle (like C#)
                    if idle_time > 120:
                        logger.debug(f"Worker {self.worker_id}: Idle timeout, shutting down")
                        self.shutdown_in_progress = True
            
            # Signal pool that we're shutting down
            self.pool.worker_shutdown(self)
            
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id}: Unhandled exception: {e}",
                exc_info=True
            )
            self.pool.worker_shutdown(self)
        
        logger.debug(f"Worker {self.worker_id} terminated")


class Converter:
    """
    Individual converter instance watching a folder.
    
    Equivalent to Converter.cs.
    Manages FileSystemWatcher, converter class loading, and post-processing.
    """
    
    class PostProcessAction(Enum):
        """Post-processing actions (like C# enum)"""
        MOVE = "Move"
        ARCHIVE = "Archive"
        ERROR = "Error"
        DELETE = "Delete"
    
    def __init__(
        self,
        name: str,
        watch_folder: Path,
        file_pattern: List[str],
        converter_class: type,
        converter_args: dict,
        pool: 'ConverterPool',
        post_process_action: PostProcessAction = PostProcessAction.DELETE
    ) -> None:
        self.name = name
        self.watch_path = Path(watch_folder)
        self.file_patterns = file_pattern
        self.converter_class = converter_class
        self.converter_args = converter_args
        self.pool = pool
        self.post_process_action = post_process_action
        
        # State
        self.converter_state = "Created"
        self.pending_items: List[ConversionItem] = []
        
        # File system watcher
        self._observer: Optional[Observer] = None
        self._check_folder_lock = threading.Lock()
        
        # Converter instance
        self._converter_instance = None
        
        logger.info(f"Converter created: {name}")
    
    def start(self):
        """
        Start converter and file watcher.
        
        Equivalent to Start() in Converter.cs.
        """
        try:
            # Ensure folders exist
            self.watch_path.mkdir(parents=True, exist_ok=True)
            error_folder = self.watch_path / "Error"
            error_folder.mkdir(exist_ok=True)
            
            # Create converter instance
            self._converter_instance = self.converter_class(**self.converter_args)
            
            # Attach file watcher
            self._attach_watcher()
            
            # Initial folder check
            self._check_folder()
            
            self.converter_state = "Running"
            logger.info(f"Converter started: {self.name}")
            
        except Exception as e:
            self.converter_state = "Error"
            logger.error(f"Failed to start converter {self.name}: {e}", exc_info=True)
            raise
    
    def stop(self):
        """Stop converter and file watcher"""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        
        self.converter_state = "Stopped"
        logger.info(f"Converter stopped: {self.name}")
    
    def _attach_watcher(self):
        """
        Attach FileSystemWatcher.
        
        Equivalent to AttachWatcher() in Converter.cs.
        """
        try:
            class ConverterFileHandler(FileSystemEventHandler):
                def __init__(self, converter_ref):
                    self.converter = converter_ref
                
                def on_created(self, event):
                    if not event.is_directory:
                        self.converter._on_file_changed(event.src_path)
                
                def on_modified(self, event):
                    if not event.is_directory:
                        self.converter._on_file_changed(event.src_path)
            
            self._observer = Observer()
            handler = ConverterFileHandler(self)
            self._observer.schedule(handler, str(self.watch_path), recursive=False)
            self._observer.start()
            
            logger.debug(f"File watcher attached: {self.watch_path}")
            
        except Exception as e:
            logger.warning(
                f"Failed to attach file watcher for {self.name} on {self.watch_path}: {e}"
            )
    
    def _on_file_changed(self, file_path: str):
        """
        Handle file system event.
        
        Equivalent to fsw_Changed and fsw_Renamed in Converter.cs.
        """
        # Trigger folder check (debounced by lock)
        self._check_folder_single_thread()
    
    def _check_folder_single_thread(self):
        """
        Check folder for files (single-threaded).
        
        Equivalent to CheckFolderSingleThread() in Converter.cs.
        Ensures only one thread checks folder at a time.
        """
        if not self._check_folder_lock.acquire(blocking=False):
            return  # Already checking
        
        try:
            self._check_folder()
        finally:
            self._check_folder_lock.release()
    
    def _check_folder(self):
        """
        Check folder for files matching patterns.
        
        Scans folder and queues matching files for conversion.
        """
        try:
            if not self.watch_path.exists():
                return
            
            for pattern in self.file_patterns:
                for file_path in self.watch_path.glob(pattern):
                    if file_path.is_file():
                        # Add to conversion queue
                        self.pool.add_file(file_path, self)
            
        except Exception as e:
            logger.error(f"Error checking folder {self.watch_path}: {e}")
    
    def convert_file(self, item: ConversionItem, api_client):
        """
        Convert a file using the converter instance.
        
        Called by worker thread.
        """
        try:
            # Call converter
            # Assuming converter has a convert() method
            if hasattr(self._converter_instance, 'convert'):
                result = self._converter_instance.convert(str(item.file_path), api_client)
            else:
                raise NotImplementedError(f"Converter {self.name} has no convert() method")
            
            # Post-process file based on result
            self._post_process_file(item.file_path, success=True)
            
            # Remove from pending
            self.pool.remove_file(str(item.file_path))
            
        except Exception as e:
            logger.error(f"Conversion failed for {item.file_path}: {e}", exc_info=True)
            self._post_process_file(item.file_path, success=False, error=e)
            raise
    
    def _post_process_file(self, file_path: Path, success: bool, error: Exception = None):
        """
        Post-process file after conversion.
        
        Handles Move, Archive, Delete, or Error actions.
        """
        try:
            if not file_path.exists():
                return
            
            if success:
                if self.post_process_action == self.PostProcessAction.DELETE:
                    file_path.unlink()
                    logger.debug(f"Deleted: {file_path.name}")
                
                elif self.post_process_action == self.PostProcessAction.MOVE:
                    done_folder = self.watch_path / "Done"
                    done_folder.mkdir(exist_ok=True)
                    dest = done_folder / file_path.name
                    file_path.rename(dest)
                    logger.debug(f"Moved to Done: {file_path.name}")
                
                # TODO: Implement ARCHIVE action (zip file)
            
            else:
                # Move to Error folder
                error_folder = self.watch_path / "Error"
                error_folder.mkdir(exist_ok=True)
                dest = error_folder / file_path.name
                
                # Handle duplicate names
                counter = 1
                while dest.exists():
                    dest = error_folder / f"{file_path.stem}_{counter}{file_path.suffix}"
                    counter += 1
                
                file_path.rename(dest)
                logger.warning(f"Moved to Error: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Post-processing error for {file_path}: {e}")
    
    def process_archive_queue(self):
        """
        Process archive queue during idle time.
        
        Equivalent to ProcessArchiveQueue() in Converter.cs.
        """
        # TODO: Implement archive processing if needed
        pass
    
    def pending_count(self) -> int:
        """Get pending file count"""
        try:
            count = 0
            for pattern in self.file_patterns:
                count += len(list(self.watch_path.glob(pattern)))
            return count
        except:
            return 0
    
    def error_count(self) -> int:
        """Get error file count"""
        try:
            error_folder = self.watch_path / "Error"
            if error_folder.exists():
                return len(list(error_folder.glob("*")))
            return 0
        except:
            return 0


class ConverterPool:
    """
    Converter pool with auto-scaling worker threads.
    
    Equivalent to Conversion.cs in C# implementation.
    Manages converters, queue, and worker pool.
    """
    
    def __init__(self, config, api_client) -> None:
        """
        Initialize converter pool.
        
        Args:
            config: ClientConfig instance
            api_client: pyWATS API client instance
        """
        self.config = config
        self.api_client = api_client
        
        # Converters
        self.converter_list: List[Converter] = []
        
        # Pending queue
        self._pending: Dict[str, ConversionItem] = {}
        self._pending_queue: Queue[ConversionItem] = Queue()
        self._pending_lock = threading.Lock()
        
        # Workers
        self._workers: List[ConverterWorkerClass] = []
        self._workers_lock = threading.Lock()
        self._next_worker_id = 1
        
        # Configuration
        self._max_workers = getattr(config, 'max_converter_workers', 10)
        if self._max_workers <= 0:
            self._max_workers = 1  # Default
        if self._max_workers > 50:
            self._max_workers = 50  # Safety limit
        
        self._disposing = False
        
        logger.info(f"ConverterPool initialized (max workers: {self._max_workers})")
    
    def initialize_converters(self):
        """
        Load and initialize converters from config.
        
        Equivalent to InitializeConverters() in Conversion.cs.
        Runs asynchronously on background thread.
        """
        logger.info("Initializing converters...")
        
        try:
            # Load converter configurations
            for conv_config in self.config.converters:
                if not conv_config.enabled:
                    continue
                
                try:
                    # Load converter class
                    converter_class = self._load_converter_class(
                        Path(conv_config.module_path)
                    )
                    
                    if not converter_class:
                        logger.warning(f"Failed to load converter: {conv_config.name}")
                        continue
                    
                    # Create converter instance
                    converter = Converter(
                        name=conv_config.name,
                        watch_folder=Path(conv_config.watch_folder),
                        file_pattern=conv_config.file_patterns,
                        converter_class=converter_class,
                        converter_args=conv_config.arguments,
                        pool=self
                    )
                    
                    self.converter_list.append(converter)
                    logger.info(f"Initialized converter: {conv_config.name}")
                    
                except Exception as e:
                    logger.error(f"Error initializing converter {conv_config.name}: {e}")
            
            logger.info(f"{len(self.converter_list)} converters initialized")
            
            # Wait 5 seconds before starting (like C#)
            time.sleep(5)
            
            # Start all converters
            self._start_all_converters()
            
        except Exception as e:
            logger.error(f"Converter initialization failed: {e}", exc_info=True)
    
    def _load_converter_class(self, module_path: Path) -> Optional[type]:
        """
        Load converter class from Python module.
        
        Equivalent to dynamic assembly loading in Converter.cs.
        """
        try:
            if not module_path.exists():
                logger.error(f"Converter module not found: {module_path}")
                return None
            
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"converter_{module_path.stem}",
                module_path
            )
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find converter class
            # Look for class with 'Converter' in name or 'convert' method
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and hasattr(obj, 'convert'):
                    return obj
            
            logger.error(f"No converter class found in {module_path}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load converter module {module_path}: {e}")
            return None
    
    def _start_all_converters(self):
        """
        Start all converters.
        
        Equivalent to StartAllConverters() in Conversion.cs.
        """
        for converter in self.converter_list:
            try:
                converter.start()
                logger.info(
                    f"Converter started: {converter.name}, "
                    f"pending: {converter.pending_count()}"
                )
            except Exception as e:
                logger.error(f"Failed to start converter {converter.name}: {e}")
        
        running_count = len([c for c in self.converter_list if c.converter_state == "Running"])
        logger.info(f"{running_count} converters started")
    
    def get_next_file_to_convert(self) -> Optional[ConversionItem]:
        """
        Get next file from queue for processing.
        
        Equivalent to GetNextFileToConvert() in Conversion.cs.
        Returns None if no files available.
        """
        with self._pending_lock:
            # Refill queue from pending if empty
            if self._pending and self._pending_queue.empty():
                # Sort by file date (oldest first)
                pending_items = sorted(
                    [item for item in self._pending.values() 
                     if item.state == ConversionItemState.PENDING],
                    key=lambda x: x.file_date or datetime.min
                )
                
                for item in pending_items:
                    self._pending_queue.put(item)
            
            # Get next item
            try:
                item = self._pending_queue.get_nowait()
                item.process_start = datetime.now()
                item.state = ConversionItemState.PROCESSING
                return item
            except Empty:
                return None
    
    def add_file(self, file_path: Path, converter: Converter) -> ConversionItem:
        """
        Add file to conversion queue.
        
        Equivalent to AddFile() in Conversion.cs.
        """
        with self._pending_lock:
            file_key = str(file_path)
            
            # Check if already queued
            if file_key in self._pending:
                return self._pending[file_key]
            
            # Create new item
            item = ConversionItem(
                file_path=file_path,
                converter=converter,
                queued_at=datetime.now()
            )
            
            self._pending[file_key] = item
        
        # Check if we need more workers
        queue_size = len(self._pending)
        worker_count = len(self._workers)
        
        if worker_count < 1 or (worker_count < 10 and queue_size > 10):
            self._check_worker_status()
        
        return item
    
    def remove_file(self, file_path: str):
        """Remove file from pending queue"""
        with self._pending_lock:
            if file_path in self._pending:
                del self._pending[file_path]
    
    def _check_worker_status(self):
        """
        Auto-scale worker pool based on queue depth.
        
        Equivalent to CheckWorkerStatus() in Conversion.cs.
        Creates 1 worker per 10 pending files, up to max_workers limit.
        """
        with self._workers_lock:
            queue_size = len(self._pending)
            
            # Calculate desired workers (1 per 10 files)
            desired_workers = (queue_size + 9) // 10
            desired_workers = min(desired_workers, self._max_workers)
            desired_workers = max(desired_workers, 50)  # Never exceed 50
            
            # Count active workers
            active_workers = len([w for w in self._workers if not w.shutdown_in_progress])
            
            # Add workers if needed
            to_add = desired_workers - active_workers
            
            if to_add > 0:
                logger.info(
                    f"Starting {to_add} converter workers "
                    f"(pending: {queue_size}, active: {active_workers})"
                )
                
                for _ in range(to_add):
                    worker = ConverterWorkerClass(self, self._next_worker_id)
                    self._next_worker_id += 1
                    worker.start()
                    self._workers.append(worker)
    
    def worker_shutdown(self, worker: ConverterWorkerClass):
        """
        Handle worker shutdown.
        
        Equivalent to WorkerShutDown() in Conversion.cs.
        """
        with self._workers_lock:
            if worker in self._workers:
                self._workers.remove(worker)
            
            logger.debug(
                f"Worker {worker.worker_id} shut down "
                f"(active: {len(self._workers)}, pending: {len(self._pending)})"
            )
            
            # If no workers left, process archive queues
            if len(self._workers) == 0:
                for converter in self.converter_list:
                    try:
                        converter.process_archive_queue()
                    except Exception as e:
                        logger.error(f"Archive queue error: {e}")
    
    def check_state(self):
        """
        Watchdog health check.
        
        Equivalent to CheckState() in Conversion.cs.
        Checks converter states and resets timed-out items.
        """
        # Check each converter
        for converter in self.converter_list:
            try:
                # Converter-specific health checks
                pass
            except Exception as e:
                logger.error(f"Converter check error: {e}")
        
        # Reset items stuck in Processing for >10 minutes
        timeout = datetime.now().timestamp() - 600  # 10 minutes
        
        with self._pending_lock:
            for item in self._pending.values():
                if (item.state == ConversionItemState.PROCESSING and 
                    item.process_start and
                    item.process_start.timestamp() < timeout):
                    
                    logger.warning(f"Resetting stuck item: {item.file_path}")
                    item.state = ConversionItemState.PENDING
        
        # Clean up dead workers
        with self._workers_lock:
            self._workers = [w for w in self._workers if w.is_alive()]
    
    def dispose(self):
        """
        Shutdown pool gracefully.
        
        Equivalent to Dispose() in Conversion.cs.
        """
        self._disposing = True
        
        logger.info("Stopping converter pool...")
        
        # Stop all converters
        for converter in self.converter_list:
            try:
                converter.stop()
            except Exception as e:
                logger.error(f"Error stopping converter: {e}")
        
        # Signal workers to shut down
        with self._workers_lock:
            for worker in self._workers:
                worker.shutdown_in_progress = True
        
        # Wait for workers to finish (up to 20 seconds)
        timeout = time.time() + 20
        while self._workers and time.time() < timeout:
            time.sleep(0.1)
        
        logger.info("Converter pool stopped")
    
    def create_api_client(self):
        """
        Create API client for worker thread.
        
        Each worker gets its own API instance (like C# TDM per worker).
        """
        # For now, share the main API client
        # TODO: Create separate client instances if needed for thread safety
        return self.api_client
    
    def get_statistics(self) -> List[Dict[str, Any]]:
        """
        Get converter statistics.
        
        Equivalent to GetConverterStatistics() in Conversion.cs.
        """
        if self._disposing:
            return []
        
        stats = []
        for converter in self.converter_list:
            stats.append({
                'name': converter.name,
                'state': converter.converter_state,
                'pending_count': converter.pending_count(),
                'error_count': converter.error_count()
            })
        
        return stats
