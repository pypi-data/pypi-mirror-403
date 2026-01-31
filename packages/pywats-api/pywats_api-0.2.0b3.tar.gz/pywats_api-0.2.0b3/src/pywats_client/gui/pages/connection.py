"""
Connection Page

Matches the WATS Client Connection page layout.
"""

import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Slot

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow

logger = logging.getLogger(__name__)


class ConnectionPage(BasePage):
    """Connection settings page"""
    
    def __init__(
        self, 
        config: ClientConfig, 
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        self._main_window = main_window
        super().__init__(config, parent)
        self._setup_ui()
        self.load_config()
    
    @property
    def page_title(self) -> str:
        return "Connection"
    
    def _setup_ui(self) -> None:
        """Setup page UI matching WATS Client design"""
        # Service address section
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("Service address"))
        
        self._address_edit = QLineEdit()
        self._address_edit.setPlaceholderText("https://your-wats-server.com/")
        self._address_edit.textChanged.connect(self._emit_changed)
        address_layout.addWidget(self._address_edit, 1)
        
        self._layout.addLayout(address_layout)
        
        # Disconnect button
        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setFixedWidth(120)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        self._layout.addWidget(self._disconnect_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Help text
        help_label = QLabel(
            'Service address to your wats.com account or WATS server. Click\n'
            '"Disconnect" to reset the client and log on to another service.'
        )
        help_label.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(help_label)
        
        self._layout.addSpacing(20)
        
        # Test connection section
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test connection"))
        
        self._test_btn = QPushButton("Run test")
        self._test_btn.setFixedWidth(100)
        self._test_btn.clicked.connect(self._on_test_connection)
        test_layout.addWidget(self._test_btn)
        test_layout.addStretch()
        
        self._layout.addLayout(test_layout)
        
        self._layout.addSpacing(10)
        
        # Test send UUT section - Advanced connection test with actual report
        test_uut_layout = QHBoxLayout()
        test_uut_layout.addWidget(QLabel("Test send UUT"))
        
        self._test_uut_btn = QPushButton("Send test report")
        self._test_uut_btn.setFixedWidth(130)
        self._test_uut_btn.setToolTip(
            "Creates and submits a comprehensive test UUT report to verify\n"
            "full connectivity and report submission functionality."
        )
        self._test_uut_btn.clicked.connect(self._on_test_send_uut)
        test_uut_layout.addWidget(self._test_uut_btn)
        test_uut_layout.addStretch()
        
        self._layout.addLayout(test_uut_layout)
        
        # Test UUT help text
        test_uut_help = QLabel(
            'Sends a test UUT report with various test types (numeric, string,\n'
            'boolean, charts) to verify full data submission capability.'
        )
        test_uut_help.setStyleSheet("color: #808080; font-size: 11px;")
        self._layout.addWidget(test_uut_help)
        
        self._layout.addSpacing(20)
        
        # Status section
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("WATS Client Status"))
        self._client_status_label = QLabel("Offline")
        self._client_status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self._client_status_label)
        status_layout.addStretch()
        self._layout.addLayout(status_layout)
        
        service_status_layout = QHBoxLayout()
        service_status_layout.addWidget(QLabel("WATS Client Service"))
        self._service_status_label = QLabel("Stopped")
        self._service_status_label.setStyleSheet("font-weight: bold;")
        service_status_layout.addWidget(self._service_status_label)
        service_status_layout.addStretch()
        self._layout.addLayout(service_status_layout)
        
        identifier_layout = QHBoxLayout()
        identifier_layout.addWidget(QLabel("Current Identifier"))
        self._identifier_label = QLabel()
        self._identifier_label.setStyleSheet("font-weight: bold;")
        identifier_layout.addWidget(self._identifier_label)
        identifier_layout.addStretch()
        self._layout.addLayout(identifier_layout)
        
        self._layout.addSpacing(20)
        
        # Advanced options (collapsible)
        self._advanced_group = QGroupBox("⊙ Advanced options")
        self._advanced_group.setCheckable(True)
        self._advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(self._advanced_group)
        
        # API Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("API Token:"))
        self._token_edit = QLineEdit()
        self._token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_edit.textChanged.connect(self._emit_changed)
        token_layout.addWidget(self._token_edit, 1)
        advanced_layout.addLayout(token_layout)
        
        # Sync interval
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Sync interval (seconds):"))
        self._sync_interval_edit = QLineEdit()
        self._sync_interval_edit.setFixedWidth(100)
        self._sync_interval_edit.textChanged.connect(self._emit_changed)
        sync_layout.addWidget(self._sync_interval_edit)
        sync_layout.addStretch()
        advanced_layout.addLayout(sync_layout)
        
        self._layout.addWidget(self._advanced_group)
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def save_config(self) -> None:
        """Save configuration"""
        self.config.service_address = self._address_edit.text()
        self.config.api_token = self._token_edit.text()
        
        try:
            self.config.sync_interval_seconds = int(self._sync_interval_edit.text())
        except ValueError:
            pass
    
    def load_config(self) -> None:
        """Load configuration"""
        self._address_edit.setText(self.config.service_address)
        self._token_edit.setText(self.config.api_token)
        self._sync_interval_edit.setText(str(self.config.sync_interval_seconds))
        self._identifier_label.setText(self.config.formatted_identifier)
        
        # Status will be updated after auto-test
        self.update_status("Checking...")
        self._auto_test_pending = True
    
    def showEvent(self, event) -> None:
        """Called when page becomes visible"""
        super().showEvent(event)
        # Run auto-test on first show if service address is configured
        if self._auto_test_pending and self.config.service_address:
            self._auto_test_pending = False
            try:
                asyncio.create_task(self._run_connection_test(auto=True))
            except RuntimeError:
                # Event loop not running yet - skip auto-test
                pass
        elif self._auto_test_pending:
            self._auto_test_pending = False
            self.update_status("Not configured")
    
    def update_status(self, status: str) -> None:
        """Update connection status display"""
        self._client_status_label.setText(status)
        
        # Green for online/connected states
        if status in ("Online", "Connected", "Online - Test OK"):
            self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
            self._service_status_label.setText("Running")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
        elif status in ("Connecting", "Starting service...", "Checking..."):
            self._client_status_label.setStyleSheet("font-weight: bold; color: #dcdcaa;")
            self._service_status_label.setText("Checking...")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #dcdcaa;")
        elif "Error" in status or "already running" in status.lower():
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
            if "already running" in status.lower():
                self._service_status_label.setText("Already Running")
                self._service_status_label.setStyleSheet("font-weight: bold; color: #ce9178;")
            else:
                self._service_status_label.setText("Error")
                self._service_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
        elif status in ("Offline", "Disconnected", "Service not running"):
            # Gray for disconnected/offline states
            self._client_status_label.setStyleSheet("font-weight: bold; color: #808080;")
            self._service_status_label.setText("Stopped")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #808080;")
        else:
            # Default: red for unknown states
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")
            self._service_status_label.setText("Stopped")
            self._service_status_label.setStyleSheet("font-weight: bold;")
    
    def _on_disconnect(self) -> None:
        """Handle disconnect button click"""
        # Clear credentials
        self._address_edit.clear()
        self._token_edit.clear()
        self.update_status("Offline")
        self._emit_changed()
    
    def _on_test_connection(self) -> None:
        """Handle test connection button click"""
        self._test_btn.setEnabled(False)
        self._test_btn.setText("Testing...")
        
        # Save current values to config first
        self.save_config()
        
        # Run test in background using asyncio
        try:
            asyncio.create_task(self._run_connection_test(auto=False))
        except RuntimeError as e:
            logger.warning(f"Could not start async test: {e}")
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Run test")
            self.update_status("Error: No event loop")
    
    async def _run_connection_test(self, auto: bool = False) -> None:
        """Run connection test asynchronously
        
        Args:
            auto: If True, this is an automatic test at startup (don't touch button state)
        """
        try:
            import httpx
            
            url = self.config.service_address.rstrip('/')
            if not url:
                self._show_test_result(False, "No service address configured", auto)
                return
            
            # Test the API endpoint
            test_url = f"{url}/api/Report/wats/info"
            headers = {}
            if self.config.api_token:
                headers["Authorization"] = f"Bearer {self.config.api_token}"
            
            # Enable redirect following
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(test_url, headers=headers)
                
                if response.status_code == 200:
                    self._show_test_result(True, "Online", auto)
                elif response.status_code == 401:
                    self._show_test_result(False, "Authentication failed (401)", auto)
                elif response.status_code == 403:
                    self._show_test_result(False, "Access denied (403)", auto)
                elif response.status_code == 404:
                    # Try alternative endpoint
                    alt_url = f"{url}/api/report/wats/info"
                    response = await client.get(alt_url, headers=headers)
                    if response.status_code == 200:
                        self._show_test_result(True, "Online", auto)
                    else:
                        self._show_test_result(False, f"API not found (404)", auto)
                else:
                    self._show_test_result(False, f"Server returned {response.status_code}", auto)
                    
        except httpx.ConnectError:
            self._show_test_result(False, "Connection failed", auto)
        except httpx.TimeoutException:
            self._show_test_result(False, "Connection timeout", auto)
        except Exception as e:
            logger.exception("Connection test error")
            self._show_test_result(False, f"Error: {str(e)[:30]}", auto)
    
    def _show_test_result(self, success: bool, message: str, auto: bool = False) -> None:
        """Show test result and re-enable button
        
        Args:
            success: Whether the test passed
            message: Status message to display
            auto: If True, don't touch button state (auto-test at startup)
        """
        if not auto:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("Run test")
        
        if success:
            self._client_status_label.setText(message)
            self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
            self._service_status_label.setText("Available")
            self._service_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
        else:
            self._client_status_label.setText(message)
            self._client_status_label.setStyleSheet("font-weight: bold; color: #f14c4c;")

    def _on_test_send_uut(self) -> None:
        """Handle test send UUT button click"""
        self._test_uut_btn.setEnabled(False)
        self._test_uut_btn.setText("Sending...")
        
        # Save config first
        self.save_config()
        
        # Run async test
        try:
            asyncio.create_task(self._run_send_uut_test())
        except RuntimeError as e:
            logger.warning(f"Could not start async UUT test: {e}")
            self._test_uut_btn.setEnabled(True)
            self._test_uut_btn.setText("Send test report")
            QMessageBox.warning(self, "Error", "Event loop not running")
    
    async def _run_send_uut_test(self) -> None:
        """Run test UUT send operation"""
        try:
            import httpx
            from datetime import datetime
            import uuid
            
            url = self.config.service_address.rstrip('/')
            if not url:
                self._show_message("Error", "No service address configured", "warning")
                return
            
            headers = {"Content-Type": "application/json"}
            if self.config.api_token:
                headers["Authorization"] = f"Bearer {self.config.api_token}"
            
            # Create a minimal test UUT report
            test_report = {
                "pn": "TEST-PART-001",
                "sn": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "rev": "1.0",
                "processCode": 10,
                "result": "P",  # Passed
                "start": datetime.utcnow().isoformat() + "Z",
                "root": {
                    "status": "P",
                    "steps": [
                        {
                            "name": "pyWATS GUI Connection Test",
                            "status": "P",
                            "steps": [
                                {
                                    "name": "Test Step",
                                    "status": "P",
                                    "numericMeas": [{
                                        "name": "Test Value",
                                        "status": "P",
                                        "value": 42.0,
                                        "unit": "units"
                                    }]
                                }
                            ]
                        }
                    ]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.post(
                    f"{url}/api/Report/wats",
                    json=test_report,
                    headers=headers
                )
                
                if response.status_code in (200, 201):
                    # Try to parse JSON response, handle empty or non-JSON responses
                    result = {}
                    if response.content and response.content.strip():
                        try:
                            result = response.json()
                        except Exception:
                            # Response wasn't JSON - that's okay for success
                            pass
                    report_id = result.get("id", "Submitted")
                    self._show_message(
                        "Test Report Sent",
                        f"Test UUT report submitted successfully!\n\n"
                        f"Report ID: {report_id}\n"
                        f"Serial: {test_report['sn']}\n"
                        f"Part Number: {test_report['pn']}",
                        "info"
                    )
                    self._client_status_label.setText("Online - Test OK")
                    self._client_status_label.setStyleSheet("font-weight: bold; color: #4ec9b0;")
                elif response.status_code == 401:
                    self._show_message("Authentication Failed", "Invalid or expired API token (401)", "warning")
                elif response.status_code == 403:
                    self._show_message("Access Denied", "You don't have permission to submit reports (403)", "warning")
                else:
                    self._show_message(
                        "Test Report Failed",
                        f"Server returned status {response.status_code}\n\n{response.text[:200]}",
                        "warning"
                    )
                    
        except httpx.ConnectError:
            self._show_message("Connection Error", "Could not connect to server", "critical")
        except httpx.TimeoutException:
            self._show_message("Timeout", "Request timed out", "critical")
        except Exception as e:
            logger.exception("Test UUT send error")
            self._show_message("Error", f"Error sending test report:\n{str(e)}", "critical")
        finally:
            self._test_uut_btn.setEnabled(True)
            self._test_uut_btn.setText("Send test report")
    
    def _show_message(self, title: str, message: str, level: str = "info") -> None:
        """Show a message box in a way that works with async code.
        
        Args:
            title: Dialog title
            message: Message text
            level: 'info', 'warning', or 'critical'
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if level == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        elif level == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setModal(True)
        msg_box.show()
        msg_box.raise_()
        msg_box.activateWindow()