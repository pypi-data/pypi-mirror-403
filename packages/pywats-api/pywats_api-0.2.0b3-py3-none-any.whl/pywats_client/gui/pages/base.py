"""
Base Page Widget

Base class for all configuration pages.

Supports both config-only and facade-based initialization patterns.

Async Support:
    Pages can execute async operations without blocking the UI using the
    run_async() method or by connecting to the facade's AsyncTaskRunner signals.

Error Handling:
    Pages inherit centralized error handling via ErrorHandlingMixin:
    - handle_error(error, context) - Show appropriate dialog based on exception type
    - show_success(message) - Show success message
    - show_warning(message) - Show warning message
    - show_error(message) - Show error message
    - confirm_action(message) - Show confirmation dialog
"""

from typing import Awaitable, Callable, Dict, Any, List, Optional, TYPE_CHECKING, TypeVar
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
)
from PySide6.QtCore import Signal, Qt

from ...core.config import ClientConfig
from ...core.event_bus import AppEvent, event_bus
from ...core.async_runner import TaskResult, AsyncTaskRunner
from ..error_mixin import ErrorHandlingMixin

if TYPE_CHECKING:
    from ..async_api_runner import AsyncAPIRunner

T = TypeVar('T')


class BasePage(QWidget, ErrorHandlingMixin):
    """
    Base class for configuration pages.
    
    Provides common functionality for all pages:
    - Title display
    - Config change signal
    - Save/load config methods
    - Async operation support with loading indicators
    - Centralized error handling (via ErrorHandlingMixin)
    
    In IPC mode (new architecture):
        Pages communicate with service via MainWindow's IPC client.
        Access service via: self.parent()._ipc_client
    
    Usage:
        page = MyPage(config, parent)
        # Access service via IPC through main window
    
    Error Handling (from ErrorHandlingMixin):
        try:
            result = api.do_something()
        except Exception as e:
            self.handle_error(e, "doing something")  # Shows appropriate dialog
    
    Async Example:
        def _on_refresh(self):
            self.run_async(
                self._load_data(),
                name="load_data",
                on_complete=self._on_data_loaded
            )
    """
    
    # Emitted when configuration is changed
    config_changed = Signal()
    
    # Emitted when async loading state changes (is_loading, task_name)
    loading_changed = Signal(bool, str)
    
    def __init__(
        self, 
        config: ClientConfig, 
        parent: Optional[QWidget] = None,
        async_api_runner: Optional['AsyncAPIRunner'] = None
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.async_api: Optional['AsyncAPIRunner'] = async_api_runner
        self._event_subscriptions: List[tuple[AppEvent, Callable]] = []
        self._running_tasks: Dict[str, str] = {}  # task_id -> name
        self._async_runner: Optional[AsyncTaskRunner] = None
        self._setup_base_ui()
    
    def _setup_base_ui(self) -> None:
        """Setup base UI layout"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(15)
        
        # Title row with optional loading indicator
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self._title_label = QLabel(self.page_title)
        self._title_label.setObjectName("titleLabel")
        title_row.addWidget(self._title_label)
        
        title_row.addStretch()
        
        # Loading indicator (hidden by default)
        self._loading_indicator = QProgressBar()
        self._loading_indicator.setObjectName("loadingIndicator")
        self._loading_indicator.setRange(0, 0)  # Indeterminate
        self._loading_indicator.setFixedWidth(100)
        self._loading_indicator.setFixedHeight(16)
        self._loading_indicator.hide()
        self._loading_indicator.setStyleSheet("""
            QProgressBar#loadingIndicator {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QProgressBar#loadingIndicator::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        title_row.addWidget(self._loading_indicator)
        
        self._loading_label = QLabel()
        self._loading_label.setObjectName("loadingLabel")
        self._loading_label.setStyleSheet("color: #808080; font-size: 11px;")
        self._loading_label.hide()
        title_row.addWidget(self._loading_label)
        
        self._layout.addLayout(title_row)
        
        # Separator
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        self._layout.addWidget(separator)
    
    @property
    def page_title(self) -> str:
        """Override in subclass to set page title"""
        return "Page"
    
    # =========================================================================
    # Async Operation Support
    # =========================================================================
    
    @property
    def async_runner(self) -> AsyncTaskRunner:
        """
        Get or create the async task runner for this page.
        """
        if self._async_runner is None:
            self._async_runner = AsyncTaskRunner(parent=self)
            # Connect to task lifecycle signals
            self._async_runner.task_started.connect(self._on_task_started)
            self._async_runner.task_finished.connect(self._on_task_finished)
        
        return self._async_runner
    
    def run_async(
        self,
        coro: Awaitable[T],
        name: str = "task",
        on_complete: Optional[Callable[["TaskResult[T]"], None]] = None,
        on_error: Optional[Callable[["TaskResult[T]"], None]] = None,
        show_loading: bool = True
    ) -> str:
        """
        Run an async operation without blocking the UI.
        
        Args:
            coro: The async coroutine to execute
            name: Human-readable task name (shown in loading indicator)
            on_complete: Callback for successful completion
            on_error: Callback for errors
            show_loading: Whether to show loading indicator
        
        Returns:
            Task ID that can be used to cancel the task
        
        Example:
            def _on_refresh(self):
                self.run_async(
                    self._fetch_assets(),
                    name="Loading assets...",
                    on_complete=self._on_assets_loaded
                )
            
            async def _fetch_assets(self):
                return await self.facade.api.asset.get_assets()
        """
        task_id = self.async_runner.run(coro, name, on_complete, on_error)
        
        if show_loading:
            self._running_tasks[task_id] = name
            self._update_loading_state()
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running async task"""
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
            self._update_loading_state()
        return self.async_runner.cancel(task_id)
    
    def cancel_all_tasks(self) -> int:
        """Cancel all running async tasks"""
        self._running_tasks.clear()
        self._update_loading_state()
        return self.async_runner.cancel_all()
    
    @property
    def is_loading(self) -> bool:
        """Check if any async tasks are running"""
        return len(self._running_tasks) > 0
    
    def _on_task_started(self, task_id: str, name: str) -> None:
        """Handle task start (internal)"""
        pass
    
    def _on_task_finished(self, result: TaskResult) -> None:
        """Handle task completion (internal)"""
        if result.task_id in self._running_tasks:
            del self._running_tasks[result.task_id]
            self._update_loading_state()
    
    def _update_loading_state(self) -> None:
        """Update the loading indicator visibility"""
        is_loading = len(self._running_tasks) > 0
        
        if is_loading:
            # Get the first task name for display
            task_name = next(iter(self._running_tasks.values()), "Loading...")
            self._loading_label.setText(task_name)
            self._loading_indicator.show()
            self._loading_label.show()
        else:
            self._loading_indicator.hide()
            self._loading_label.hide()
        
        # Emit signal for custom handling
        task_name = next(iter(self._running_tasks.values()), "") if is_loading else ""
        self.loading_changed.emit(is_loading, task_name)
    
    def set_loading(self, is_loading: bool, message: str = "Loading...") -> None:
        """
        Manually set the loading state.
        
        Useful for sync operations or custom loading behavior.
        
        Args:
            is_loading: Whether loading is in progress
            message: Loading message to display
        """
        if is_loading:
            self._loading_label.setText(message)
            self._loading_indicator.show()
            self._loading_label.show()
        else:
            self._loading_indicator.hide()
            self._loading_label.hide()
        
        self.loading_changed.emit(is_loading, message if is_loading else "")
    
    # =========================================================================
    # Event Subscription Helpers
    # =========================================================================
    
    def subscribe_event(
        self, 
        event: AppEvent, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to an application event.
        
        Events are automatically unsubscribed when the page is destroyed.
        
        Args:
            event: The event type to subscribe to
            callback: Function to call when event occurs
        """
        event_bus.subscribe(event, callback)
        self._event_subscriptions.append((event, callback))
    
    def unsubscribe_event(
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
        try:
            self._event_subscriptions.remove((event, callback))
        except ValueError:
            pass  # Not in list
    
    def unsubscribe_all_events(self) -> None:
        """
        Unsubscribe from all events this page subscribed to.
        
        Called automatically during cleanup.
        """
        for event, callback in self._event_subscriptions:
            event_bus.unsubscribe(event, callback)
        self._event_subscriptions.clear()
    
    # =========================================================================
    # Qt Lifecycle
    # =========================================================================
    
    def closeEvent(self, event) -> None:
        """Clean up when page is closed."""
        self.unsubscribe_all_events()
        self.cancel_all_tasks()
        super().closeEvent(event)
    
    def deleteLater(self) -> None:
        """Clean up before deletion."""
        self.unsubscribe_all_events()
        self.cancel_all_tasks()
        super().deleteLater()
    
    # =========================================================================
    # Configuration Methods
    # =========================================================================
    
    def save_config(self) -> None:
        """Override in subclass to save configuration"""
        pass
    
    def load_config(self) -> None:
        """Override in subclass to load configuration"""
        pass
    
    def _emit_changed(self) -> None:
        """Emit config changed signal"""
        self.config_changed.emit()
