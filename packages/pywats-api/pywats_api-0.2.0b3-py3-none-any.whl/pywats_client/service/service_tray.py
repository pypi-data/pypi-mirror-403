"""
Service System Tray Icon

Provides system tray functionality for the pyWATS Client service.
Shows service status, pending uploads, and provides quick actions.

Note: This is a GUI component that legitimately requires Qt (PySide6).
It uses the async IPC client for communication with the headless service.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtGui import QAction, QIcon

from .async_ipc_client import AsyncIPCClient

logger = logging.getLogger(__name__)


class ServiceTrayIcon(QObject):
    """
    System tray icon for pyWATS Client service.
    
    Features:
    - Shows service status and upload stats in tooltip
    - Click to show status popup
    - Right-click menu with:
      - Open Configurator (launch GUI)
      - Stop Service
      - Restart Service
      - Exit Tray Icon
    """
    
    def __init__(self, instance_id: str = "default", parent=None) -> None:
        super().__init__(parent)
        
        self.instance_id = instance_id
        self._ipc_client = AsyncIPCClient(instance_id)
        self._tray_icon: Optional[QSystemTrayIcon] = None
        
        # Status update timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._on_status_timer)
        
        # Last known status
        self._service_connected = False
        self._last_status = {}
        
        self._setup_tray_icon()
    
    def _setup_tray_icon(self) -> None:
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available")
            return
        
        self._tray_icon = QSystemTrayIcon(self)
        
        # Set icon
        icon_path = Path(__file__).parent.parent / "gui" / "resources" / "favicon.ico"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                self._tray_icon.setIcon(icon)
            else:
                logger.warning(f"Failed to load tray icon from {icon_path}")
        else:
            logger.warning(f"Tray icon file not found: {icon_path}")
        
        # Create context menu
        menu = QMenu()
        
        # Open Configurator action
        open_gui_action = QAction("Open Configurator", self)
        open_gui_action.triggered.connect(self._open_configurator)
        menu.addAction(open_gui_action)
        
        menu.addSeparator()
        
        # Service control actions
        restart_action = QAction("Restart Service", self)
        restart_action.triggered.connect(self._restart_service)
        menu.addAction(restart_action)
        
        stop_action = QAction("Stop Service", self)
        stop_action.triggered.connect(self._stop_service)
        menu.addAction(stop_action)
        
        menu.addSeparator()
        
        # Exit tray icon action
        exit_action = QAction("Exit Tray Icon", self)
        exit_action.triggered.connect(self._exit_tray)
        menu.addAction(exit_action)
        
        self._tray_icon.setContextMenu(menu)
        
        # Click to show status popup
        self._tray_icon.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self._tray_icon.show()
        logger.info("System tray icon initialized")
    
    def start(self) -> None:
        """Start the tray icon with status updates"""
        # Connect to service (async)
        asyncio.create_task(self._async_connect_to_service())
        
        # Start status update timer (5s)
        self._status_timer.start(5000)
    
    def _on_status_timer(self) -> None:
        """Handle status timer - trigger async update"""
        asyncio.create_task(self._async_update_status())
    
    async def _async_connect_to_service(self) -> None:
        """Connect to the service via async IPC"""
        if await self._ipc_client.connect(timeout=0.5):
            self._service_connected = True
            logger.info(f"Connected to service instance: {self.instance_id}")
            # Initial status update
            await self._async_update_status()
        else:
            self._service_connected = False
            logger.warning(f"Service not running for instance: {self.instance_id}")
            if self._tray_icon:
                self._tray_icon.setToolTip("pyWATS Client - Service Not Running")
    
    async def _async_update_status(self) -> None:
        """Update tray icon tooltip with current status"""
        if not self._service_connected:
            # Try reconnecting
            await self._async_connect_to_service()
            if not self._service_connected:
                return
        
        try:
            status = await self._ipc_client.get_status()
            if status:
                self._last_status = {
                    "api_status": status.api_status,
                    "service_status": status.status,
                    "pending_count": status.pending_count
                }
                
                # Build tooltip with status info
                api_status = status.api_status
                service_status = status.status
                pending = status.pending_count
                
                tooltip = (
                    f"pyWATS Client - {service_status}\n"
                    f"API: {api_status}\n"
                    f"Pending: {pending}"
                )
                if self._tray_icon:
                    self._tray_icon.setToolTip(tooltip)
            else:
                self._service_connected = False
                await self._ipc_client.disconnect()
                if self._tray_icon:
                    self._tray_icon.setToolTip("pyWATS Client - Connection Lost")
        except Exception as e:
            logger.debug(f"Status update failed: {e}")
            self._service_connected = False
            if self._tray_icon:
                self._tray_icon.setToolTip("pyWATS Client - Connection Lost")
    
    def _connect_to_service(self) -> None:
        """Connect to the service via IPC (sync wrapper - deprecated)"""
        asyncio.create_task(self._async_connect_to_service())

    def _update_status(self) -> None:
        """Update status (sync wrapper - deprecated)"""
        asyncio.create_task(self._async_update_status())
    
    def _on_tray_activated(self, reason) -> None:
        """Handle tray icon activation (click)"""
        from PySide6.QtWidgets import QSystemTrayIcon
        
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - show status popup
            self._show_status_popup()
    
    def _show_status_popup(self) -> None:
        """Show popup with detailed status"""
        if not self._service_connected:
            message = "Service is not running."
        else:
            api_status = self._last_status.get("api_status", "Unknown")
            service_status = self._last_status.get("service_status", "Unknown")
            
            # TODO: Add converter stats when implemented
            pending = 0
            uploaded = 0
            suspended = 0
            
            message = (
                f"Service Status: {service_status}\n"
                f"API Status: {api_status}\n\n"
                f"Converters:\n"
                f"  Pending: {pending}\n"
                f"  Uploaded: {uploaded}\n"
                f"  Suspended: {suspended}"
            )
        
        self._tray_icon.showMessage(
            "pyWATS Client Status",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000  # 3 seconds
        )
    
    def _open_configurator(self) -> None:
        """Launch the Configurator GUI as a separate process"""
        import subprocess
        
        try:
            # Use pythonw.exe on Windows to avoid console window
            python_exe = sys.executable
            creation_flags = 0
            
            if sys.platform == 'win32':
                # Try pythonw.exe for no console window
                if python_exe.endswith('python.exe'):
                    pythonw = python_exe.replace('python.exe', 'pythonw.exe')
                    if Path(pythonw).exists():
                        python_exe = pythonw
                # Create detached process on Windows
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            
            # Build command - only add instance-id if not default
            cmd = [python_exe, "-m", "pywats_client", "gui"]
            if self.instance_id and self.instance_id != "default":
                cmd.extend(["--instance-id", self.instance_id])
            
            # Launch GUI in separate process
            subprocess.Popen(
                cmd,
                creationflags=creation_flags,
                start_new_session=True if sys.platform != 'win32' else False
            )
            logger.info(f"Launched Configurator GUI (instance: {self.instance_id})")
            
        except Exception as e:
            logger.error(f"Failed to launch GUI: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to launch Configurator:\n{e}"
            )
    
    def _restart_service(self) -> None:
        """Restart the service"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None,
            "Restart Service",
            "Restart the pyWATS Client service?\n\nThis will temporarily pause file monitoring and uploads.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement service restart via IPC
            QMessageBox.information(
                None,
                "Not Implemented",
                "Service restart will be implemented in a future update.\n\n"
                "For now, please stop the service manually and restart it."
            )
    
    def _stop_service(self) -> None:
        """Stop the service"""
        from PySide6.QtWidgets import QMessageBox
        
        if not self._service_connected:
            QMessageBox.warning(
                None,
                "Service Not Connected",
                "Cannot stop service: not connected."
            )
            return
        
        reply = QMessageBox.question(
            None,
            "Stop Service",
            "Stop the pyWATS Client service?\n\n"
            "This will:\n"
            "• Stop all file watching\n"
            "• Stop all converter workers\n"
            "• Close the service process",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            asyncio.create_task(self._async_stop_service())
    
    async def _async_stop_service(self) -> None:
        """Async stop service implementation"""
        try:
            success = await self._ipc_client.request_stop()
            if success:
                QMessageBox.information(
                    None,
                    "Service Stopped",
                    "Service stopped successfully."
                )
                self._service_connected = False
                if self._tray_icon:
                    self._tray_icon.setToolTip("pyWATS Client - Service Stopped")
            else:
                QMessageBox.warning(
                    None,
                    "Stop Failed",
                    "Failed to stop service."
                )
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error",
                f"Error stopping service: {e}"
            )
    
    def _exit_tray(self) -> None:
        """Exit the tray icon application"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None,
            "Exit Tray Icon",
            "Exit the tray icon?\n\nThe service will continue running in the background.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._status_timer.stop()
            if self._tray_icon:
                self._tray_icon.hide()
            QApplication.quit()


def main(instance_id: str = "default"):
    """
    Run the system tray icon application.
    
    Args:
        instance_id: Instance identifier
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running with no windows
    
    # Setup qasync for async IPC
    try:
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
    except ImportError:
        logger.warning("qasync not available, IPC status updates may not work")
        loop = None
    
    tray = ServiceTrayIcon(instance_id)
    tray.start()
    
    if loop:
        with loop:
            return loop.run_forever()
    else:
        return app.exec()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
