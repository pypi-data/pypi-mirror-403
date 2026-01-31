"""
Async Converter Pool - Concurrent file conversion with asyncio

Async-first implementation of the converter pool.
Uses asyncio.Semaphore for bounded concurrency instead of thread pool.

Benefits over sync ConverterPool:
- Single-threaded (no thread overhead)
- Concurrent I/O via asyncio
- Automatic backpressure via semaphore
- Efficient batch processing
- **Sandboxed execution** for untrusted converters

See CLIENT_ASYNC_ARCHITECTURE.md for design details.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import sandbox for secure converter execution
from ..converters.sandbox import (
    ConverterSandbox,
    SandboxConfig,
    ResourceLimits,
    SandboxError,
    SandboxTimeoutError,
    SandboxSecurityError,
)

if TYPE_CHECKING:
    from pywats import AsyncWATS
    from ..core.config import ClientConfig
    from ..converters.base import Converter

logger = logging.getLogger(__name__)


class AsyncConversionItemState(Enum):
    """State of an async conversion item"""
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    ERROR = "Error"
    CANCELLED = "Cancelled"


class AsyncConversionItem:
    """
    Represents a file to be converted asynchronously.
    """
    
    def __init__(
        self,
        file_path: Path,
        converter: 'Converter'
    ) -> None:
        self.file_path = file_path
        self.converter = converter
        self.state = AsyncConversionItemState.PENDING
        self.queued_at = datetime.now()
        self.process_start: Optional[datetime] = None
        self.process_end: Optional[datetime] = None
        self.error: Optional[str] = None
        self.file_date = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ) if file_path.exists() else None
    
    @property
    def processing_time(self) -> Optional[float]:
        """Get processing time in seconds"""
        if self.process_start and self.process_end:
            return (self.process_end - self.process_start).total_seconds()
        return None


class AsyncConverterPool:
    """
    Async converter pool using asyncio.Queue and semaphore-limited workers.
    
    Benefits:
    - Single-threaded (no thread overhead)
    - Concurrent I/O via asyncio
    - Automatic backpressure via semaphore
    - Efficient batch processing
    
    Usage:
        pool = AsyncConverterPool(config, api, max_concurrent=10)
        await pool.run()  # Runs until stopped
        await pool.stop()
    """
    
    def __init__(
        self,
        config: 'ClientConfig',
        api: 'AsyncWATS',
        max_concurrent: int = 10,
        enable_sandbox: bool = True,
        sandbox_config: Optional[SandboxConfig] = None,
    ) -> None:
        """
        Initialize async converter pool.
        
        Args:
            config: Client configuration
            api: AsyncWATS API client
            max_concurrent: Maximum concurrent conversions
            enable_sandbox: Enable sandboxed execution for converters (default: True)
            sandbox_config: Custom sandbox configuration (uses defaults if not provided)
        """
        self.config = config
        self.api = api
        self._max_concurrent = max_concurrent
        
        # Sandbox for secure converter execution
        self._enable_sandbox = enable_sandbox
        self._sandbox: Optional[ConverterSandbox] = None
        self._sandbox_config = sandbox_config
        
        # Processing queue and semaphore
        self._queue: asyncio.Queue[AsyncConversionItem] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0  # Track active conversions explicitly (not _semaphore._value)
        
        # Event loop reference (for thread-safe signaling from watchdog)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Converter instances
        self._converters: List['Converter'] = []
        
        # File watchers
        self._observers: List[Observer] = []
        
        # State
        self._running = False
        self._stop_event = asyncio.Event()
        self._active_tasks: List[asyncio.Task] = []
        
        # Statistics
        self._stats: Dict[str, Any] = {
            "total_processed": 0,
            "successful": 0,
            "errors": 0,
            "sandbox_errors": 0,
            "queue_size": 0,
            "active_conversions": 0,
            "sandbox_enabled": enable_sandbox,
        }
        
        logger.info(
            f"AsyncConverterPool initialized (max_concurrent={max_concurrent}, "
            f"sandbox={'enabled' if enable_sandbox else 'disabled'})"
        )
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        self._stats["queue_size"] = self._queue.qsize()
        self._stats["active_conversions"] = self._active_count
        return self._stats.copy()
    
    @property
    def is_running(self) -> bool:
        """Check if pool is running"""
        return self._running
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    async def run(self) -> None:
        """
        Main processing loop.
        
        Starts file watchers and processes conversion queue.
        """
        if self._running:
            logger.warning("Pool already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        # Store loop reference for thread-safe signaling from watchdog
        self._loop = asyncio.get_running_loop()
        
        logger.info("AsyncConverterPool starting...")
        
        try:
            # Load converters from config
            await self._load_converters()
            
            # Start file watchers
            await self._start_watchers()
            
            # Process queue until stopped
            while not self._stop_event.is_set():
                try:
                    # Wait for item with timeout (allows checking stop event)
                    item = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                    
                    # Process with semaphore limiting concurrency
                    task = asyncio.create_task(
                        self._process_with_limit(item)
                    )
                    self._active_tasks.append(task)
                    
                    # Clean up completed tasks
                    self._active_tasks = [
                        t for t in self._active_tasks if not t.done()
                    ]
                    
                except asyncio.TimeoutError:
                    # Check for archive queue processing (after 10s idle)
                    if self._queue.empty():
                        await self._process_archive_queues()
                    continue
                    
        except asyncio.CancelledError:
            logger.info("Pool cancelled")
        finally:
            self._running = False
    
    async def stop(self) -> None:
        """
        Stop the pool gracefully.
        
        Waits for in-flight conversions to complete (with timeout).
        """
        if not self._running:
            return
        
        logger.info("Stopping AsyncConverterPool...")
        self._stop_event.set()
        
        # Stop file watchers
        for observer in self._observers:
            observer.stop()
        self._observers.clear()
        
        # Wait for active tasks (with timeout)
        if self._active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Conversion tasks timed out, cancelling...")
                for task in self._active_tasks:
                    task.cancel()
        
        self._active_tasks.clear()
        self._loop = None  # Clear loop reference
        
        # Shutdown sandbox if active
        if self._sandbox:
            try:
                await self._sandbox.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down sandbox: {e}")
            self._sandbox = None
        
        self._running = False
        logger.info("AsyncConverterPool stopped")
    
    async def reload_config(self, config: 'ClientConfig') -> None:
        """
        Reload configuration.
        
        Updates converters and watchers.
        """
        logger.info("Reloading converter pool config...")
        self.config = config
        
        # Reload converters
        await self._load_converters()
        
        # Restart watchers
        await self._restart_watchers()
    
    # =========================================================================
    # Converter Management
    # =========================================================================
    
    async def _load_converters(self) -> None:
        """Load converters from configuration"""
        self._converters.clear()
        
        try:
            # Get converter configs from config.converters property
            converter_configs = self.config.converters
            
            for conv_config in converter_configs:
                try:
                    converter = await self._create_converter(conv_config)
                    if converter:
                        self._converters.append(converter)
                        logger.info(f"Loaded converter: {converter.name}")
                except Exception as e:
                    logger.error(f"Failed to load converter: {e}")
            
            logger.info(f"Loaded {len(self._converters)} converters")
            
        except Exception as e:
            logger.error(f"Failed to load converters: {e}")
    
    async def _create_converter(
        self,
        config: Dict[str, Any]
    ) -> Optional['Converter']:
        """Create a converter instance from configuration"""
        # Import converter base
        from ..converters.base import Converter
        from ..converters.registry import get_converter_class
        
        converter_type = config.get("type")
        if not converter_type:
            return None
        
        # Get converter class
        converter_class = get_converter_class(converter_type)
        if not converter_class:
            logger.warning(f"Unknown converter type: {converter_type}")
            return None
        
        # Create instance
        return converter_class(config)
    
    # =========================================================================
    # File Watching
    # =========================================================================
    
    async def _start_watchers(self) -> None:
        """Start file system watchers for all converters"""
        for converter in self._converters:
            try:
                observer = self._create_watcher(converter)
                if observer:
                    observer.start()
                    self._observers.append(observer)
                    logger.info(f"Started watcher for {converter.name}")
            except Exception as e:
                logger.error(f"Failed to start watcher for {converter.name}: {e}")
    
    async def _restart_watchers(self) -> None:
        """Restart all file watchers"""
        # Stop existing
        for observer in self._observers:
            observer.stop()
            observer.join(timeout=5)
        self._observers.clear()
        
        # Start new
        await self._start_watchers()
    
    def _create_watcher(self, converter: 'Converter') -> Optional[Observer]:
        """Create a file system watcher for a converter"""
        watch_path = converter.watch_path
        if not watch_path or not watch_path.exists():
            return None
        
        # Create event handler
        handler = _FileEventHandler(self, converter)
        
        # Create observer
        observer = Observer()
        observer.schedule(
            handler,
            str(watch_path),
            recursive=converter.watch_recursive
        )
        
        return observer
    
    def _on_file_created(
        self,
        file_path: Path,
        converter: 'Converter'
    ) -> None:
        """Handle new file detected (called from watchdog thread - NOT async safe!)"""
        # Validate file matches converter pattern
        if not converter.matches_file(file_path):
            return
        
        # Queue for conversion - use thread-safe method
        item = AsyncConversionItem(file_path, converter)
        
        # IMPORTANT: This is called from watchdog's thread, not the asyncio thread.
        # We must use call_soon_threadsafe to safely add to the asyncio queue
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(
                lambda: self._queue.put_nowait(item) if not self._queue.full() else logger.warning(f"Queue full, cannot queue: {file_path.name}")
            )
            logger.debug(f"Queued (thread-safe): {file_path.name}")
        else:
            # Fallback for edge cases
            try:
                self._queue.put_nowait(item)
                logger.debug(f"Queued: {file_path.name}")
            except asyncio.QueueFull:
                logger.warning(f"Queue full, cannot queue: {file_path.name}")
    
    # =========================================================================
    # Conversion Processing
    # =========================================================================
    
    async def _process_with_limit(self, item: AsyncConversionItem) -> None:
        """Process conversion item with semaphore limiting"""
        async with self._semaphore:
            self._active_count += 1
            try:
                await self._process_item(item)
            finally:
                self._active_count -= 1
    
    async def _process_item(self, item: AsyncConversionItem) -> None:
        """
        Process a single conversion item.
        
        Steps:
        1. Read file (async I/O) - only for non-sandboxed execution
        2. Convert (sandboxed subprocess OR thread pool)
        3. Submit to WATS (async HTTP)
        4. Handle post-processing
        """
        item.state = AsyncConversionItemState.PROCESSING
        item.process_start = datetime.now()
        
        logger.info(f"Processing: {item.file_path.name}")
        
        try:
            # Determine if sandbox should be used for this converter
            use_sandbox = self._enable_sandbox and self._should_use_sandbox(item.converter)
            
            if use_sandbox:
                # Sandboxed execution (secure subprocess)
                report = await self._convert_sandboxed(item)
            else:
                # Legacy execution (thread pool - trusted converters only)
                report = await self._convert_unsandboxed(item)
            
            if report is None:
                logger.warning(f"Converter returned no report: {item.file_path.name}")
                item.state = AsyncConversionItemState.ERROR
                item.error = "Converter returned no report"
                self._stats["errors"] += 1
                return
            
            # 3. Submit to WATS (async HTTP)
            await self.api.report.submit(report)
            
            # 4. Post-processing (move/delete/archive file)
            await self._post_process(item)
            
            item.state = AsyncConversionItemState.COMPLETED
            item.process_end = datetime.now()
            
            self._stats["total_processed"] += 1
            self._stats["successful"] += 1
            
            logger.info(
                f"Completed: {item.file_path.name} "
                f"({item.processing_time:.2f}s)"
            )
            
        except Exception as e:
            item.state = AsyncConversionItemState.ERROR
            item.error = str(e)
            item.process_end = datetime.now()
            
            self._stats["total_processed"] += 1
            self._stats["errors"] += 1
            
            logger.error(f"Conversion failed: {item.file_path.name}: {e}")
            
            # Handle error (move to error folder, etc.)
            await self._handle_error(item, e)
    
    def _should_use_sandbox(self, converter: 'Converter') -> bool:
        """
        Determine if sandbox should be used for this converter.
        
        Returns True unless converter explicitly opts out (trusted_mode=True).
        """
        # Check if converter has trusted_mode attribute (opt-out for built-in converters)
        if hasattr(converter, 'trusted_mode') and converter.trusted_mode:
            return False
        
        # Check if converter has a source file (required for sandbox)
        if hasattr(converter, 'source_path') and converter.source_path:
            return True
        
        # For dynamically loaded converters, use sandbox
        return True
    
    async def _ensure_sandbox(self) -> ConverterSandbox:
        """Get or create the sandbox instance."""
        if self._sandbox is None:
            self._sandbox = ConverterSandbox(
                default_config=self._sandbox_config
            )
        return self._sandbox
    
    async def _convert_sandboxed(self, item: AsyncConversionItem) -> Optional[Dict[str, Any]]:
        """
        Execute converter in sandboxed subprocess.
        
        Provides:
        - Process isolation
        - Resource limits
        - Filesystem restrictions
        - Import blocking
        """
        sandbox = await self._ensure_sandbox()
        converter = item.converter
        
        # Get converter source path (required for sandboxing)
        converter_path = getattr(converter, 'source_path', None)
        if not converter_path:
            logger.warning(
                f"Converter {converter.name} has no source_path, "
                f"falling back to unsandboxed execution"
            )
            return await self._convert_unsandboxed(item)
        
        converter_class = converter.__class__.__name__
        
        try:
            result = await sandbox.run_converter(
                converter_path=Path(converter_path),
                converter_class=converter_class,
                input_path=item.file_path,
                args={
                    "user_settings": getattr(converter, 'user_settings', {}),
                }
            )
            
            # Extract report from result
            if result.get("status") == "Success":
                return result.get("report")
            else:
                error = result.get("error", "Unknown error")
                raise SandboxError(f"Conversion failed: {error}")
                
        except SandboxSecurityError as e:
            self._stats["sandbox_errors"] += 1
            logger.error(f"Security violation in converter {converter.name}: {e}")
            raise
        
        except SandboxTimeoutError as e:
            self._stats["sandbox_errors"] += 1
            logger.error(f"Converter {converter.name} timed out: {e}")
            raise
        
        except SandboxError as e:
            self._stats["sandbox_errors"] += 1
            logger.error(f"Sandbox error in converter {converter.name}: {e}")
            raise
    
    async def _convert_unsandboxed(self, item: AsyncConversionItem) -> Optional[Dict[str, Any]]:
        """
        Execute converter in thread pool (legacy mode).
        
        WARNING: Only use for trusted, built-in converters.
        This provides no isolation or security.
        """
        # Read file content
        content = await self._read_file(item.file_path)
        
        # Run converter in thread pool
        report = await asyncio.to_thread(
            item.converter.convert,
            content,
            item.file_path
        )
        
        return report
    
    async def _read_file(self, file_path: Path) -> str:
        """Read file content asynchronously"""
        if HAS_AIOFILES:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            # Fallback to thread pool
            return await asyncio.to_thread(
                file_path.read_text,
                encoding='utf-8'
            )
    
    async def _post_process(self, item: AsyncConversionItem) -> None:
        """
        Handle post-conversion processing.
        
        Actions based on converter config:
        - Delete: Remove source file
        - Move: Move to archive folder
        - Nothing: Leave in place
        """
        from ..converters.models import PostProcessAction
        
        action = item.converter.post_process_action
        
        if action == PostProcessAction.DELETE:
            await asyncio.to_thread(item.file_path.unlink, missing_ok=True)
            
        elif action == PostProcessAction.MOVE:
            archive_path = item.converter.archive_path
            if archive_path:
                archive_path.mkdir(parents=True, exist_ok=True)
                dest = archive_path / item.file_path.name
                await asyncio.to_thread(item.file_path.rename, dest)
    
    async def _handle_error(
        self,
        item: AsyncConversionItem,
        error: Exception
    ) -> None:
        """Handle conversion error"""
        error_path = item.converter.error_path
        if error_path:
            error_path.mkdir(parents=True, exist_ok=True)
            dest = error_path / item.file_path.name
            try:
                await asyncio.to_thread(item.file_path.rename, dest)
            except Exception as e:
                logger.error(f"Failed to move error file: {e}")
    
    async def _process_archive_queues(self) -> None:
        """Process archive queues for all converters (during idle)"""
        for converter in self._converters:
            try:
                await asyncio.to_thread(converter.process_archive_queue)
            except Exception as e:
                logger.error(f"Archive queue error for {converter.name}: {e}")


class _FileEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler for file system changes.
    
    Bridges watchdog (sync) events to async queue.
    """
    
    def __init__(
        self,
        pool: AsyncConverterPool,
        converter: 'Converter'
    ) -> None:
        super().__init__()
        self.pool = pool
        self.converter = converter
    
    def on_created(self, event) -> None:
        """Handle file creation"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            self.pool._on_file_created(file_path, self.converter)
    
    def on_moved(self, event) -> None:
        """Handle file rename/move"""
        if not event.is_directory:
            # Check if moved TO our watch directory
            dest_path = Path(event.dest_path)
            if self.converter.matches_file(dest_path):
                self.pool._on_file_created(dest_path, self.converter)
