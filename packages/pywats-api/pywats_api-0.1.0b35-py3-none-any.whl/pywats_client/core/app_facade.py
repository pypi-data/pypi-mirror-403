"""
App Facade - Clean interface between GUI and application layer.

This module provides the AppFacade class that:
1. Hides application internals from GUI components
2. Provides safe access to API client and services
3. Integrates with EventBus for event-driven updates
4. Reduces coupling between GUI pages and pyWATSApplication
5. Provides async execution utilities for non-blocking GUI operations

Usage:
    # In MainWindow
    facade = AppFacade(app)
    page = SomePage(facade)
    
    # In Page (sync pattern - still works)
    self.facade.subscribe(AppEvent.CONNECTION_CHANGED, self._on_connection)
    if api := self.facade.api:
        api.asset.get("asset-001")
    
    # In Page (async pattern - recommended for large operations)
    self.facade.run_async(
        self.facade.api.asset.get_assets(),
        name="load_assets",
        on_complete=lambda r: self._update_table(r.result)
    )

Author: pyWATS Team
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, TypeVar

from .event_bus import AppEvent, event_bus
from .async_runner import AsyncTaskRunner, TaskResult

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats_client.services.connection import ConnectionService
    from pywats_client.services.process_sync import ProcessSyncService
    from pywats_client.services.report_queue import ReportQueueService
    from pywats_client.services.converter_manager import ConverterManager
    from pywats_client.app import pyWATSApplication, ApplicationStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AppFacade:
    """
    Clean facade providing GUI access to application functionality.
    
    The facade pattern decouples GUI components from the application layer,
    providing:
    - Safe access to API client (with None checks)
    - Event subscription shortcuts
    - Domain service shortcuts (asset, product, etc.)
    - Status and connection information
    - Async execution utilities for non-blocking operations
    
    Thread Safety:
        The facade itself is thread-safe for read operations.
        Event callbacks use Qt's signal mechanism for thread-safe delivery.
        Async operations run in a background thread with safe signal delivery.
    
    Example:
        ```python
        class MyPage(BasePage):
            def __init__(self, facade: AppFacade):
                self.facade = facade
                
                # Subscribe to events
                self.facade.subscribe(AppEvent.API_CLIENT_READY, self._on_api_ready)
                
            def _on_api_ready(self, data: dict):
                # Async API access (recommended for non-blocking UI)
                self.facade.run_async(
                    self._load_products(),
                    name="load_products",
                    on_complete=self._on_products_loaded
                )
            
            async def _load_products(self):
                if api := self.facade.api:
                    return await api.product.get_all_async()
                return []
            
            def _on_products_loaded(self, result: TaskResult):
                if result.is_success:
                    self._products = result.result
                    self._update_table()
        ```
    """
    
    def __init__(self, app: "pyWATSApplication") -> None:
        """
        Initialize facade with application reference.
        
        Args:
            app: The pyWATSApplication instance to wrap
        """
        self._app = app
        self._async_runner: Optional[AsyncTaskRunner] = None
        logger.debug("AppFacade initialized")
    
    # =========================================================================
    # Async Execution Support
    # =========================================================================
    
    @property
    def async_runner(self) -> AsyncTaskRunner:
        """
        Get the async task runner for executing async operations.
        
        Creates the runner lazily on first access.
        
        Returns:
            AsyncTaskRunner instance
        """
        if self._async_runner is None:
            self._async_runner = AsyncTaskRunner()
        return self._async_runner
    
    def run_async(
        self,
        coro: Awaitable[T],
        name: str = "task",
        on_complete: Optional[Callable[["TaskResult[T]"], None]] = None,
        on_error: Optional[Callable[["TaskResult[T]"], None]] = None
    ) -> str:
        """
        Run an async coroutine in the background without blocking the GUI.
        
        This is the recommended way to execute API calls from GUI pages.
        Results are delivered via callbacks or signals.
        
        Args:
            coro: The async coroutine to execute
            name: Human-readable task name for logging/tracking
            on_complete: Callback function for successful completion
            on_error: Callback function for errors
        
        Returns:
            Task ID that can be used to cancel or track the task
        
        Example:
            # Simple usage with callback
            self.facade.run_async(
                self.facade.api.asset.get_assets(),
                name="load_assets",
                on_complete=lambda r: self._update_table(r.result),
                on_error=lambda r: self._show_error(str(r.error))
            )
            
            # Signal-based usage
            self.facade.async_runner.task_completed.connect(self._on_task_done)
            self.facade.run_async(api.asset.get_assets(), name="load_assets")
        """
        return self.async_runner.run(coro, name, on_complete, on_error)
    
    def cancel_async(self, task_id: str) -> bool:
        """
        Cancel a running async task.
        
        Args:
            task_id: ID of the task to cancel
        
        Returns:
            True if cancellation was requested
        """
        if self._async_runner:
            return self._async_runner.cancel(task_id)
        return False
    
    def cancel_all_async(self) -> int:
        """
        Cancel all running async tasks.
        
        Returns:
            Number of tasks cancelled
        """
        if self._async_runner:
            return self._async_runner.cancel_all()
        return 0
    
    @property
    def has_running_tasks(self) -> bool:
        """Check if there are any running async tasks"""
        if self._async_runner:
            return self._async_runner.has_running_tasks()
        return False
    
    # =========================================================================
    # Event Bus Integration
    # =========================================================================
    
    def subscribe(
        self, 
        event: AppEvent, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to an application event.
        
        Convenience method that delegates to the global EventBus.
        Callbacks are invoked on the main thread via Qt signals.
        
        Args:
            event: The event type to subscribe to
            callback: Function to call when event occurs
        """
        event_bus.subscribe(event, callback)
    
    def unsubscribe(
        self, 
        event: AppEvent, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Unsubscribe from an application event.
        
        Args:
            event: The event type to unsubscribe from
            callback: The callback function to remove
        """
        event_bus.unsubscribe(event, callback)
    
    def subscribe_connection(
        self, 
        callback: Callable[[bool, Optional[str]], None]
    ) -> None:
        """
        Subscribe to connection status changes.
        
        Args:
            callback: Function(is_online: bool, last_error: Optional[str])
        """
        event_bus.connection_changed.connect(callback)
    
    def subscribe_status(
        self, 
        callback: Callable[[str, str], None]
    ) -> None:
        """
        Subscribe to application status changes.
        
        Args:
            callback: Function(old_status: str, new_status: str)
        """
        event_bus.app_status_changed.connect(callback)
    
    def subscribe_api_ready(
        self, 
        callback: Callable[[bool], None]
    ) -> None:
        """
        Subscribe to API client availability changes.
        
        Args:
            callback: Function(is_ready: bool)
        """
        event_bus.api_client_ready.connect(callback)
    
    # =========================================================================
    # API Client Access
    # =========================================================================
    
    @property
    def api(self) -> Optional["pyWATS"]:
        """
        Get the WATS API client.
        
        Returns None if the application hasn't started or is disconnected.
        Always check for None before using.
        
        Returns:
            pyWATS client or None if not available
            
        Example:
            if api := self.facade.api:
                products = api.product.get_all()
        """
        return self._app.wats_client
    
    @property
    def has_api(self) -> bool:
        """
        Check if API client is available.
        
        Returns:
            True if API client exists and can be used
        """
        return self._app.wats_client is not None
    
    # =========================================================================
    # Domain Service Shortcuts
    # =========================================================================
    
    @property
    def asset(self):
        """
        Get the Asset domain service.
        
        Returns:
            Asset service or None if API not ready
        """
        if api := self.api:
            return api.asset
        return None
    
    @property
    def product(self):
        """
        Get the Product domain service.
        
        Returns:
            Product service or None if API not ready
        """
        if api := self.api:
            return api.product
        return None
    
    @property
    def report(self):
        """
        Get the Report domain service.
        
        Returns:
            Report service or None if API not ready
        """
        if api := self.api:
            return api.report
        return None
    
    @property
    def analytics(self):
        """
        Get the Analytics domain service.
        
        Returns:
            Analytics service or None if API not ready
        """
        if api := self.api:
            return api.analytics
        return None
    
    @property
    def software(self):
        """
        Get the Software domain service.
        
        Returns:
            Software service or None if API not ready
        """
        if api := self.api:
            return api.software
        return None
    
    @property
    def rootcause(self):
        """
        Get the Root Cause domain service.
        
        Returns:
            Root Cause service or None if API not ready
        """
        if api := self.api:
            return api.rootcause
        return None
    
    @property
    def process(self):
        """
        Get the Process domain service.
        
        Returns:
            Process service or None if API not ready
        """
        if api := self.api:
            return api.process
        return None
    
    @property
    def production(self):
        """
        Get the Production domain service.
        
        Returns:
            Production service or None if API not ready
        """
        if api := self.api:
            return api.production
        return None
    
    # =========================================================================
    # Application Services
    # =========================================================================
    
    @property
    def connection_service(self) -> Optional["ConnectionService"]:
        """Get the connection monitoring service."""
        return self._app.connection
    
    @property
    def process_sync_service(self) -> Optional["ProcessSyncService"]:
        """Get the process synchronization service."""
        return self._app.process_sync
    
    @property
    def report_queue_service(self) -> Optional["ReportQueueService"]:
        """Get the offline report queue service."""
        return self._app.report_queue
    
    @property
    def converter_manager(self) -> Optional["ConverterManager"]:
        """Get the converter manager."""
        return self._app.converter_manager
    
    # =========================================================================
    # Status and Connection
    # =========================================================================
    
    @property
    def status(self) -> "ApplicationStatus":
        """
        Get current application status.
        
        Returns:
            Current ApplicationStatus enum value
        """
        return self._app.status
    
    @property
    def is_online(self) -> bool:
        """
        Check if connected to WATS server.
        
        Returns:
            True if currently connected
        """
        return self._app.is_online()
    
    @property
    def connection_status(self) -> Optional[str]:
        """
        Get human-readable connection status.
        
        Returns:
            Connection status string or None
        """
        return self._app.get_connection_status()
    
    @property
    def last_error(self) -> Optional[str]:
        """
        Get last error message.
        
        Returns:
            Error message string or None
        """
        return self._app.get_last_error()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get offline queue status information.
        
        Returns:
            Dictionary with queue status:
            - pending_reports: Number of reports waiting
            - pending_files: Number of files waiting
        """
        return self._app.get_queue_status()
    
    # =========================================================================
    # Application Configuration
    # =========================================================================
    
    @property
    def config(self):
        """
        Get application configuration (read-only access).
        
        Returns:
            ClientConfig instance
        """
        return self._app.config
    
    @property
    def server_url(self) -> str:
        """Get the configured server URL."""
        return self._app.config.server_url
    
    @property
    def instance_id(self) -> str:
        """Get the current instance ID."""
        return self._app.config.instance_id
