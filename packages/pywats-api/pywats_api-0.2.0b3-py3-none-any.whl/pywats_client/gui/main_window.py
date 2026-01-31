"""
Main Window for WATS Client GUI

Implements the main application window with navigation sidebar
and content pages matching the WATS Client design.
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, TYPE_CHECKING, cast
from pathlib import Path

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QListWidget, QListWidgetItem, QLabel, QFrame, QSizePolicy,
    QMenu, QMessageBox, QApplication, QPushButton
)
from PySide6.QtCore import Qt, QSize, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QCloseEvent

from .styles import DARK_STYLESHEET
from .settings_dialog import SettingsDialog
from .pages import (
    BasePage, DashboardPage, SetupPage, ConnectionPage, APISettingsPage,
    ConvertersPage, SNHandlerPage, SoftwarePage, LogPage
)
from ..core.config import ClientConfig
from ..service.async_ipc_client import AsyncIPCClient, discover_services_async


class SidebarMode(Enum):
    """Sidebar display modes"""
    ADVANCED = "advanced"   # All items visible, full width
    COMPACT = "compact"     # Essential items only, full width  
    MINIMIZED = "minimized" # Icons only, narrow width


class MainWindow(QMainWindow):
    """
    Main application window for WATS Client.
    
    Features:
    - Navigation sidebar with page selection
    - Stacked widget for page content
    - System tray integration
    - Status bar with connection info
    - Integration with pyWATSApplication service layer
    """
    
    # Signals for async updates
    connection_status_changed = Signal(str)
    application_status_changed = Signal(str)
    
    # Pages hidden in Compact mode (advanced features)
    ADVANCED_PAGES = {"Assets", "Software", "RootCause", "Products", "Production"}
    
    def __init__(
        self, 
        config: ClientConfig, 
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        
        self.config = config
        
        # Async IPC client for communicating with service (pure asyncio, no Qt dependency)
        self._ipc_client: Optional[AsyncIPCClient] = None
        self._current_instance_id: str = config.instance_id
        self._service_connected = False
        self._tray_icon = None  # System tray icon (optional)
        
        # Setup UI
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        # Start async IPC connection on init
        # Uses asyncio.create_task() which works with qasync event loop
        self._ipc_client = AsyncIPCClient(self._current_instance_id)
        self._service_connected = False
        self._connection_pending = True  # Will connect when event loop starts
        
        # Status timer for periodic updates
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._on_status_timer)
        self._status_timer.start(5000)  # Every 5 seconds
        
        # Show status in title
        self._update_window_title()
    
    def showEvent(self, event):
        """Handle window show event - start async connection when event loop is running."""
        super().showEvent(event)
        
        # Start async connection on first show (event loop is running at this point)
        if self._connection_pending:
            self._connection_pending = False
            # Use QTimer.singleShot to schedule after event loop is fully ready
            QTimer.singleShot(0, self._start_async_connection)
    
    def _start_async_connection(self):
        """Start the async IPC connection (called from event loop)."""
        try:
            asyncio.create_task(self._async_connect_to_service())
        except RuntimeError as e:
            logger.warning(f"Could not start async connection: {e}")
            # Fallback: try again later via status timer
    
    def _start_service_process(self) -> bool:
        """
        Start the service process in the background.
        
        Returns:
            True if process was started, False on error
        """
        import subprocess
        import sys
        
        try:
            logger.info(f"Starting service process for instance: {self._current_instance_id}")
            
            if sys.platform == "win32":
                # Windows: Start detached process
                subprocess.Popen(
                    [sys.executable, "-m", "pywats_client", "service", "--instance", self._current_instance_id],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Unix: Start with new session
                subprocess.Popen(
                    [sys.executable, "-m", "pywats_client", "service", "--instance", self._current_instance_id],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    def _connect_to_service(self) -> None:
        """
        Connect to the service process via IPC (sync wrapper).
        
        Triggers async connection - actual connection happens asynchronously.
        """
        asyncio.create_task(self._async_connect_to_service())
    
    async def _async_connect_to_service(self) -> None:
        """
        Async connection to the service process via IPC.
        
        If service is not running, automatically starts it and retries connection.
        """
        if self._ipc_client is None:
            self._ipc_client = AsyncIPCClient(self._current_instance_id)
        
        if await self._ipc_client.connect():
            logger.info(f"Connected to service instance: {self._current_instance_id}")
            self._service_connected = True
            self._update_window_title()
            await self._async_update_status()
        else:
            # Service not running - try to start it
            logger.info(f"Service not running for instance: {self._current_instance_id}, starting...")
            self.connection_status_changed.emit("Starting service...")
            self.application_status_changed.emit("Starting")
            
            if self._start_service_process():
                # Wait for service to start and retry connection
                await asyncio.sleep(2.0)
                await self._async_retry_connect(0)
            else:
                logger.error("Failed to start service process")
                self._service_connected = False
                self._update_window_title()
                self.connection_status_changed.emit("Failed to start service")
                self.application_status_changed.emit("Error")
    
    async def _async_retry_connect(self, attempts: int = 0) -> None:
        """
        Async retry connecting to service after starting it.
        
        Args:
            attempts: Number of attempts made so far
        """
        max_attempts = 5
        
        if await self._ipc_client.connect():
            logger.info(f"Connected to service after {attempts + 1} attempt(s)")
            self._service_connected = True
            self._update_window_title()
            await self._async_update_status()
            self.connection_status_changed.emit("Connected")
        elif attempts < max_attempts:
            # Retry after delay
            logger.debug(f"Service not ready, retrying... (attempt {attempts + 1}/{max_attempts})")
            await asyncio.sleep(1.0)
            await self._async_retry_connect(attempts + 1)
        else:
            # Give up
            logger.error(f"Could not connect to service after {max_attempts} attempts")
            self._service_connected = False
            self._update_window_title()
            self.connection_status_changed.emit("Service not responding")
            self.application_status_changed.emit("Error")
    
    def _on_status_timer(self) -> None:
        """Handle status timer tick - triggers async update"""
        try:
            asyncio.create_task(self._async_update_status())
        except RuntimeError:
            # No event loop running yet - skip this tick
            pass
    
    def _retry_connect_to_service(self, attempts: int = 0) -> None:
        """
        Retry connecting to service after starting it (sync wrapper - deprecated).
        
        Note: Use _async_retry_connect() for new code.
        """
        try:
            asyncio.create_task(self._async_retry_connect(attempts))
        except RuntimeError:
            # No event loop running - skip
            pass
    
    def _setup_window(self) -> None:
        """Configure window properties"""
        self._update_window_title()
        self.setMinimumSize(800, 600)
        self.resize(1000, 750)
        
        # Set window icon for taskbar
        from PySide6.QtGui import QIcon
        icon_path = Path(__file__).parent / "resources" / "favicon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def _setup_ui(self) -> None:
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self._create_sidebar(main_layout)
        
        # Create content area
        self._create_content_area(main_layout)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_sidebar(self, layout: QHBoxLayout) -> None:
        """Create navigation sidebar with collapsible modes"""
        # Track sidebar mode
        self._sidebar_mode = SidebarMode.ADVANCED
        
        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet("background-color: #252526;")
        
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/Title area with mode toggle
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(15, 15, 15, 15)
        
        # Logo icon - use favicon
        from PySide6.QtGui import QPixmap
        self._logo_icon = QLabel()
        icon_path = Path(__file__).parent / "resources" / "favicon.ico"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                28, 28, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self._logo_icon.setPixmap(pixmap)
        else:
            self._logo_icon.setText("🐝")
            self._logo_icon.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(self._logo_icon)
        
        self._title_label = QLabel("WATS Client")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        logo_layout.addWidget(self._title_label)
        logo_layout.addStretch()
        
        sidebar_layout.addWidget(logo_frame)
        
        # Navigation list
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("navList")
        
        # Build nav items - store all items for filtering by mode
        self._all_nav_items = self._build_nav_items()
        self._update_nav_list()
        
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self._nav_list, 1)
        
        # Footer with Settings button
        self._footer_frame = QFrame()
        footer_layout = QVBoxLayout(self._footer_frame)
        footer_layout.setContentsMargins(15, 10, 15, 15)
        footer_layout.setSpacing(10)
        
        # Settings button row
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(0, 0, 0, 5)
        
        self._settings_btn = QPushButton("⚙  Settings")
        self._settings_btn.setObjectName("settingsButton")
        self._settings_btn.setStyleSheet("""
            QPushButton#settingsButton {
                background-color: transparent;
                border: none;
                color: #808080;
                text-align: left;
                padding: 8px 10px;
                font-size: 13px;
            }
            QPushButton#settingsButton:hover {
                background-color: #2a2d2e;
                color: #ffffff;
            }
        """)
        self._settings_btn.clicked.connect(self._open_settings_dialog)
        settings_row.addWidget(self._settings_btn)
        settings_row.addStretch()
        
        footer_layout.addLayout(settings_row)
        
        from .. import __version__
        self._footer_label = QLabel(f"pyWATS Client | v{__version__}")
        self._footer_label.setObjectName("footerLabel")
        footer_layout.addWidget(self._footer_label)
        
        # Mode toggle button at bottom of footer
        self._mode_btn = QPushButton("◀")
        self._mode_btn.setObjectName("modeButton")
        self._mode_btn.setToolTip("Toggle sidebar mode (Advanced/Compact/Minimized)")
        self._mode_btn.setFixedHeight(32)
        self._mode_btn.setStyleSheet("""
            QPushButton#modeButton {
                background-color: #2a2d2e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #808080;
                font-size: 14px;
                padding: 4px;
            }
            QPushButton#modeButton:hover {
                color: #ffffff;
                background-color: #3c3c3c;
                border-color: #4c4c4c;
            }
        """)
        self._mode_btn.clicked.connect(self._toggle_sidebar_mode)
        footer_layout.addWidget(self._mode_btn)
        
        sidebar_layout.addWidget(self._footer_frame)
        
        layout.addWidget(self._sidebar)
    
    def _create_menu_bar(self) -> None:
        """Create menu bar with File and Help menus"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Restart GUI action
        restart_action = QAction("&Restart GUI", self)
        restart_action.setShortcut("Ctrl+R")
        restart_action.triggered.connect(self._restart_gui)
        file_menu.addAction(restart_action)
        
        file_menu.addSeparator()
        
        # Stop Service action
        stop_service_action = QAction("&Stop Service", self)
        stop_service_action.setShortcut("Ctrl+Shift+S")
        stop_service_action.triggered.connect(self._stop_service)
        file_menu.addAction(stop_service_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def _update_window_title(self) -> None:
        """Update window title with service status"""
        status = "Connected" if self._service_connected else "Disconnected"
        self.setWindowTitle(f"WATS Client - {self.config.instance_name} [{status}]")
    
    def _restart_gui(self) -> None:
        """Restart the GUI application"""
        reply = QMessageBox.question(
            self,
            "Restart GUI",
            "Restart the GUI? The service will continue running.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get the application and restart
            app = QApplication.instance()
            if app:
                # Schedule restart after current event processing
                QTimer.singleShot(0, lambda: self._do_restart(app))
    
    def _do_restart(self, app: QApplication) -> None:
        """Perform the actual restart"""
        import sys
        import os
        
        # Close this window
        self.close()
        
        # Restart using same arguments
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def _stop_service(self) -> None:
        """Stop the service via IPC"""
        if not self._ipc_client or not self._service_connected:
            QMessageBox.warning(
                self,
                "Service Not Connected",
                "Cannot stop service: not connected to service."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Stop Service",
            "Stop the pyWATS Client service?\n\nThis will:\n• Stop all file watching\n• Stop all converter workers\n• Close the service process\n\nThe GUI will remain open but disconnected.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self._async_stop_service())
    
    async def _async_stop_service(self) -> None:
        """Async stop service via IPC"""
        try:
            success = await self._ipc_client.request_stop()
            if success:
                QMessageBox.information(
                    self,
                    "Service Stopped",
                    "Service stopped successfully."
                )
                self._service_connected = False
                self._update_window_title()
                self.connection_status_changed.emit("Service stopped")
                self.application_status_changed.emit("Stopped")
            else:
                QMessageBox.warning(
                    self,
                    "Stop Failed",
                    "Failed to stop service."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error stopping service: {e}"
            )
    
    def _build_nav_items(self) -> list:
        """Build list of all navigation items based on config"""
        # Core navigation items that are always shown
        nav_items = [
            "Dashboard",
            "General",
            "Connection",
            "API Settings",
            "Log",
        ]
        
        # Add optional operational tabs based on configuration
        # Note: Location and Proxy Settings are now in Settings dialog only
        if self.config.show_converters_tab:
            nav_items.append("Converters")
        if self.config.show_sn_handler_tab:
            nav_items.append("SN Handler")
        if self.config.show_software_tab:
            nav_items.append("Software")
        
        return nav_items
    
    def _update_nav_list(self) -> None:
        """Update navigation list based on current sidebar mode"""
        self._nav_list.clear()
        
        for name in self._all_nav_items:
            # In Compact mode, skip advanced pages
            if self._sidebar_mode == SidebarMode.COMPACT and name in self.ADVANCED_PAGES:
                continue
            
            if self._sidebar_mode == SidebarMode.MINIMIZED:
                # Abbreviated text
                item = QListWidgetItem(name[:3])
                item.setToolTip(name)
            else:
                # Full text - no icons, bigger font
                item = QListWidgetItem(name)
            
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setSizeHint(QSize(0, 50))  # Increased from 45
            self._nav_list.addItem(item)
        
        # Select first item
        if self._nav_list.count() > 0:
            self._nav_list.setCurrentRow(0)
    
    def _toggle_sidebar_mode(self) -> None:
        """Cycle through sidebar modes: Advanced -> Compact -> Minimized -> Advanced"""
        if self._sidebar_mode == SidebarMode.ADVANCED:
            self._sidebar_mode = SidebarMode.COMPACT
            self._mode_btn.setText("◀")
            self._mode_btn.setToolTip("Compact mode (essential items) - click for Minimized")
        elif self._sidebar_mode == SidebarMode.COMPACT:
            self._sidebar_mode = SidebarMode.MINIMIZED
            self._mode_btn.setText("▶")
            self._mode_btn.setToolTip("Minimized mode (icons only) - click for Advanced")
        else:
            self._sidebar_mode = SidebarMode.ADVANCED
            self._mode_btn.setText("◀")
            self._mode_btn.setToolTip("Advanced mode (all items) - click for Compact")
        
        self._apply_sidebar_mode()
    
    def _apply_sidebar_mode(self) -> None:
        """Apply current sidebar mode styling and layout"""
        if self._sidebar_mode == SidebarMode.MINIMIZED:
            self._sidebar.setFixedWidth(60)
            self._logo_icon.hide()
            self._title_label.hide()
            self._settings_btn.setText("⚙")
            self._footer_label.hide()
            self._mode_btn.setText("▶")
        else:
            self._sidebar.setFixedWidth(200)
            self._logo_icon.show()
            self._title_label.show()
            self._settings_btn.setText("⚙  Settings")
            self._footer_label.show()
            if self._sidebar_mode == SidebarMode.ADVANCED:
                self._mode_btn.setText("◀")
            else:  # COMPACT
                self._mode_btn.setText("◀")
        
        self._update_nav_list()
    
    def _create_content_area(self, layout: QHBoxLayout) -> None:
        """Create main content area"""
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Stacked widget for pages
        self._page_stack = QStackedWidget()
        
        # Create pages matching reference design (from screenshots)
        # Build page dict dynamically based on config visibility settings
        # Note: SetupPage is now shown as "General" in navigation
        # Note: Location and Proxy Settings are now in Settings dialog only
        # Note: Pages use IPC client from main window to communicate with service
        self._pages: Dict[str, BasePage] = {
            "Dashboard": DashboardPage(self.config, self),
            "General": SetupPage(self.config, self),
            "Connection": ConnectionPage(self.config, self),
            "API Settings": APISettingsPage(self.config, self),
            "Log": LogPage(self.config, self),
        }
        
        # Add optional operational pages based on configuration
        if self.config.show_converters_tab:
            # Use new unified converters page (V2) with system/user distinction
            self._pages["Converters"] = ConvertersPage(self.config, self)
        if self.config.show_sn_handler_tab:
            self._pages["SN Handler"] = SNHandlerPage(self.config, self)
        if self.config.show_software_tab:
            self._pages["Software"] = SoftwarePage(self.config, self)
        
        for page in self._pages.values():
            self._page_stack.addWidget(page)
            # Connect config change signal to enable Apply button
            if hasattr(page, 'config_changed'):
                page.config_changed.connect(self._on_config_changed)
            # Connect service action signal from Dashboard
            if hasattr(page, 'service_action_requested'):
                logger.info(f"Connecting service_action_requested signal from {page.__class__.__name__}")
                page.service_action_requested.connect(self._on_service_action)
        
        content_layout.addWidget(self._page_stack, 1)
        
        # Add stretch to push buttons to bottom
        content_layout.addStretch()
        
        # Apply/Cancel buttons at bottom
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 5)
        button_layout.addStretch()
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("primaryButton")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self._apply_btn)
        
        self._ok_btn = QPushButton("Ok")
        self._ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self._ok_btn)
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)
        
        content_layout.addWidget(button_frame)
        
        layout.addWidget(content_frame, 1)
        
        # Select first page
        self._nav_list.setCurrentRow(0)
    
    def _create_status_bar(self) -> None:
        """Create status bar with station indicator"""
        status_bar = self.statusBar()
        
        # Connection status
        self._status_label = QLabel("Disconnected")
        status_bar.addWidget(self._status_label)
        
        status_bar.addWidget(QLabel(" | "))
        
        # Station indicator (shows effective station name)
        station_label = QLabel("Station:")
        status_bar.addWidget(station_label)
        
        self._station_status_label = QLabel(self._get_effective_station_display())
        self._station_status_label.setToolTip("Active station name for reports")
        status_bar.addWidget(self._station_status_label)
    
    def _get_effective_station_display(self) -> str:
        """Get the effective station name for status bar display."""
        station_name = self.config.get_effective_station_name()
        if self.config.multi_station_enabled:
            return f"📍 {station_name}"
        return station_name
    
    def _update_station_status(self) -> None:
        """Update station display in status bar."""
        if hasattr(self, '_station_status_label'):
            self._station_status_label.setText(self._get_effective_station_display())
    
    def _apply_styles(self) -> None:
        """Apply dark theme stylesheet"""
        self.setStyleSheet(DARK_STYLESHEET)
    
    def _connect_signals(self) -> None:
        """Connect signals and slots"""
        self.connection_status_changed.connect(self._on_connection_status_ui)
        self.application_status_changed.connect(self._on_application_status_ui)
        
        # Connect page change signals
        for page in self._pages.values():
            if hasattr(page, 'config_changed'):
                page.config_changed.connect(self._on_config_changed)
        
        # Connect setup page connection signal (page is named "General" in navigation)
        if "General" in self._pages:
            setup_page = cast(SetupPage, self._pages["General"])
            setup_page.connection_changed.connect(self._on_connection_request)
            # Connect station change signal to update status bar
            if hasattr(setup_page, 'station_changed'):
                setup_page.station_changed.connect(self._update_station_status)
    
    @Slot(bool)
    def _on_connection_request(self, should_connect: bool) -> None:
        """
        Handle connection request from setup page.
        In IPC mode, the service runs independently.
        """
        logger.warning("Connection request received but service runs independently. Use service commands.")
        pass
    
    # Navigation handling
    
    @Slot(int)
    def _on_nav_changed(self, index: int) -> None:
        """Handle navigation item selection"""
        item = self._nav_list.item(index)
        if not item:
            return
        
        page_name = item.data(Qt.ItemDataRole.UserRole)
        if page_name and page_name in self._pages:
            page_index = list(self._pages.keys()).index(page_name)
            self._page_stack.setCurrentIndex(page_index)
    
    def _open_settings_dialog(self) -> None:
        """Open the settings dialog"""
        dialog = SettingsDialog(self.config, parent=self)
        dialog.settings_changed.connect(self._on_settings_dialog_closed)
        dialog.exec()
    
    def _on_settings_dialog_closed(self) -> None:
        """Handle settings dialog changes"""
        # Notify all pages that config may have changed
        for page in self._pages.values():
            if hasattr(page, 'load_config'):
                page.load_config()
        
        # Save client config
        self.config.save()
    
    # Button handlers
    
    def _on_apply(self) -> None:
        """Handle Apply button click - save changes and disable button"""
        self._save_config()
        self._apply_btn.setEnabled(False)
    
    def _on_ok(self) -> None:
        """Handle Ok button click"""
        self._save_config()
        self.close()
    
    def _on_cancel(self) -> None:
        """Handle Cancel button click"""
        self.close()
    
    def _on_config_changed(self) -> None:
        """Handle configuration changes"""
        self._apply_btn.setEnabled(True)
    
    def _on_service_action(self, action: str) -> None:
        """Handle service control actions from Dashboard"""
        logger.info(f"Service action requested: {action}")
        
        if not self._ipc_client or not self._service_connected:
            QMessageBox.warning(
                self,
                "Service Not Running",
                "The service is not currently running.\n\n"
                "Start it with:\npython -m pywats_client service"
            )
            return
        
        if action == "stop":
            asyncio.create_task(self._async_stop_service_action())
        elif action == "start":
            # Service should already be running if we have IPC connection
            QMessageBox.information(
                self,
                "Service Running",
                "The service is already running."
            )
        else:
            logger.warning(f"Unknown service action: {action}")
    
    async def _async_stop_service_action(self) -> None:
        """Async stop service action"""
        try:
            await self._ipc_client.request_stop()
            self.connection_status_changed.emit("Service stopping...")
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop service: {e}")
    
    def _save_config(self) -> None:
        """Save configuration from all pages"""
        for page in self._pages.values():
            if hasattr(page, 'save_config'):
                page.save_config()
        
        self.config.save()
    
    # Status handling
    
    @Slot(str)
    def _on_connection_status_ui(self, status: str) -> None:
        """Update UI for connection status change"""
        self._status_label.setText(status)
        
        # Note: Don't update Connection page here - that page shows API status
        # which is separate from the service/IPC status shown in main window
    
    @Slot(str)
    def _on_application_status_ui(self, status: str) -> None:
        """Update UI for application status change"""
        # Update window title with status
        title = f"WATS Client - {self.config.instance_name}"
        if status not in ["Stopped", "Running"]:
            title += f" [{status}]"
        self.setWindowTitle(title)
    
    def _update_status(self) -> None:
        """Periodic status update via IPC (sync wrapper)"""
        asyncio.create_task(self._async_update_status())
    
    async def _async_update_status(self) -> None:
        """Async periodic status update via IPC"""
        if not self._ipc_client:
            # No IPC client - try to reconnect
            await self._async_connect_to_service()
            if not self._ipc_client or not self._service_connected:
                self.connection_status_changed.emit("Service not running")
                self.application_status_changed.emit("Stopped")
                return
        
        try:
            # Check if connected
            if not self._ipc_client.connected:
                # Try to reconnect
                if not await self._ipc_client.connect():
                    self._service_connected = False
                    self.connection_status_changed.emit("Service not running")
                    self.application_status_changed.emit("Stopped")
                    return
                self._service_connected = True
            
            # Ping service first to check if still alive
            if not await self._ipc_client.ping():
                # Service died, try to reconnect
                logger.warning("Service not responding, attempting reconnect...")
                self._service_connected = False
                await self._ipc_client.disconnect()
                await self._async_connect_to_service()
                return
            
            # Get status from service via IPC
            status = await self._ipc_client.get_status()
            
            if status:
                # Update application status
                app_status = status.status
                self.application_status_changed.emit(app_status)
                
                # Update API connection status
                api_status = status.api_status
                if api_status.lower() == "online":
                    self.connection_status_changed.emit("Online")
                elif api_status.lower() == "offline":
                    self.connection_status_changed.emit("Offline (Queuing)")
                else:
                    self.connection_status_changed.emit(api_status)
                
                # Update queue status if available
                queue_size = status.pending_count
                if queue_size > 0:
                    self._status_label.setToolTip(f"{queue_size} reports queued")
                else:
                    self._status_label.setToolTip("")
            else:
                # Service not responding
                self.connection_status_changed.emit("Service unavailable")
                self.application_status_changed.emit("Error")
                self._service_connected = False
        
        except Exception as e:
            logger.error(f"Error updating status via IPC: {e}")
            self.connection_status_changed.emit("IPC error")
            self._service_connected = False
    
    # Window events
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event"""
        if self.config.minimize_to_tray and self._tray_icon:
            event.ignore()
            self.hide()
            self._tray_icon.showMessage(
                "WATS Client",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self._quit_application()
            event.accept()
    
    def _quit_application(self) -> None:
        """Quit the application"""
        # Stop status timer first
        if self._status_timer:
            self._status_timer.stop()
        
        # Disconnect from service (but don't stop it - service runs independently)
        if self._ipc_client:
            # Use create_task for async disconnect
            asyncio.create_task(self._async_disconnect())
        
        QApplication.quit()
    
    async def _async_disconnect(self) -> None:
        """Async disconnect from IPC"""
        if self._ipc_client:
            await self._ipc_client.disconnect()
            self._ipc_client = None
    
    # Public methods for pages
    
    async def test_connection(self) -> bool:
        """
        Test connection to WATS server via IPC.
        
        Note: This tests if the service can reach the WATS API,
        not the GUI-to-service IPC connection.
        """
        if not self._ipc_client or not self._service_connected:
            return False
        
        try:
            # Get status from service - if api_status is 'online', connection works
            status = self._ipc_client.get_status()
            if status:
                api_status = status.get("api_status", "").lower()
                return api_status == "online"
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
        
        return False
    
    async def start_services(self) -> bool:
        """
        Start application services.
        
        In IPC mode, the service must be started externally:
        python -m pywats_client service --instance-id <instance>
        
        This method checks if service is running.
        """
        if not self._service_connected:
            QMessageBox.information(
                self,
                "Start Service",
                f"Service is not running for instance '{self._current_instance_id}'.\n\n"
                "Start it with:\n"
                f"python -m pywats_client service --instance-id {self._current_instance_id}"
            )
            return False
        return True
    
    async def stop_services(self) -> None:
        """
        Stop application services via IPC.
        
        Sends stop command to service process.
        """
        if self._ipc_client and self._service_connected:
            try:
                self._ipc_client.stop_service()
                self._service_connected = False
            except Exception as e:
                logger.error(f"Failed to stop service: {e}")
    
    def refresh_converters(self) -> None:
        """
        Refresh converters from service.
        
        In IPC mode, converters are managed by the service.
        Get fresh status to update converter list.
        """
        if self._ipc_client and self._service_connected:
            self._update_status()
