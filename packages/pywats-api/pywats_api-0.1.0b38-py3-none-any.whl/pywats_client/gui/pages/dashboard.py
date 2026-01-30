"""
Service Dashboard Page

Provides real-time monitoring of:
- Service status (running/stopped)
- Converter health and statistics
- Queue status and sync state
- Quick actions (start/stop service)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class StatusIndicator(QFrame):
    """Visual status indicator widget"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._status = "unknown"
        self._update_style()
    
    def set_status(self, status: str) -> None:
        """Set status: 'running', 'stopped', 'error', 'unknown'"""
        self._status = status
        self._update_style()
    
    def _update_style(self) -> None:
        colors = {
            "running": "#4ec9b0",  # Green
            "stopped": "#808080",  # Gray
            "error": "#f48771",    # Red
            "unknown": "#dcdcaa",  # Yellow
        }
        color = colors.get(self._status, "#808080")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                border: 1px solid #3c3c3c;
            }}
        """)

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """
    Service Dashboard - Main monitoring page
    
    Displays:
    - Service status and controls
    - Converter health overview
    - Queue and sync status
    - Quick statistics
    """
    
    # Signals
    service_action_requested = Signal(str)  # "start" or "stop"
    
    def __init__(
        self, 
        config: ClientConfig,
        main_window: Optional['MainWindow'] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        self._main_window = main_window
        super().__init__(config, parent)
        
        # Refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_status)
        self._refresh_timer.start(2000)  # Refresh every 2 seconds
        
        self._setup_ui()
        self._refresh_status()
    
    @property
    def page_title(self) -> str:
        return "Dashboard"
    
    def _setup_ui(self) -> None:
        """Setup dashboard UI"""
        
        # === Service Status Section ===
        service_group = QGroupBox("Service Status")
        service_layout = QVBoxLayout(service_group)
        
        # Status row
        status_row = QHBoxLayout()
        
        self._service_indicator = StatusIndicator()
        status_row.addWidget(self._service_indicator)
        
        self._service_status_label = QLabel("Checking...")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self._service_status_label.setFont(status_font)
        status_row.addWidget(self._service_status_label)
        
        status_row.addStretch()
        
        # Control buttons
        self._start_btn = QPushButton("Start Service")
        self._start_btn.clicked.connect(self._on_start_clicked)
        self._start_btn.setEnabled(False)
        status_row.addWidget(self._start_btn)
        
        self._stop_btn = QPushButton("Stop Service")
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._stop_btn.setEnabled(False)
        status_row.addWidget(self._stop_btn)
        
        service_layout.addLayout(status_row)
        
        # Service info
        info_layout = QHBoxLayout()
        
        self._uptime_label = QLabel("Uptime: --")
        self._uptime_label.setStyleSheet("color: #808080;")
        info_layout.addWidget(self._uptime_label)
        
        info_layout.addStretch()
        
        self._instance_label = QLabel(f"Instance: {self.config.instance_name}")
        self._instance_label.setStyleSheet("color: #808080;")
        info_layout.addWidget(self._instance_label)
        
        service_layout.addLayout(info_layout)
        
        self._layout.addWidget(service_group)
        
        # === Statistics Row ===
        stats_layout = QHBoxLayout()
        
        # Converters card
        converters_card = self._create_stat_card("Converters", "0 Active", "#4ec9b0")
        self._converters_value = converters_card.findChild(QLabel, "value")
        stats_layout.addWidget(converters_card)
        
        # Queue card
        queue_card = self._create_stat_card("Queue", "0 Pending", "#dcdcaa")
        self._queue_value = queue_card.findChild(QLabel, "value")
        stats_layout.addWidget(queue_card)
        
        # Reports card
        reports_card = self._create_stat_card("Reports", "0 Today", "#569cd6")
        self._reports_value = reports_card.findChild(QLabel, "value")
        stats_layout.addWidget(reports_card)
        
        # Success rate card
        success_card = self._create_stat_card("Success Rate", "-%", "#4ec9b0")
        self._success_value = success_card.findChild(QLabel, "value")
        stats_layout.addWidget(success_card)
        
        self._layout.addLayout(stats_layout)
        
        # === Converter Health Table ===
        health_group = QGroupBox("Converter Health")
        health_layout = QVBoxLayout(health_group)
        
        self._health_table = QTableWidget()
        self._health_table.setColumnCount(6)
        self._health_table.setHorizontalHeaderLabels([
            "Status", "Converter", "Watch Folder", "Processed", "Success", "Last Run"
        ])
        
        header = self._health_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)       # Converter
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Watch Folder
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Processed
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Success
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Last Run
        
        self._health_table.setColumnWidth(1, 200)
        self._health_table.verticalHeader().setVisible(False)
        self._health_table.setAlternatingRowColors(True)
        self._health_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._health_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        health_layout.addWidget(self._health_table)
        
        self._layout.addWidget(health_group, 1)
        
        # === Connection Status ===
        conn_group = QGroupBox("Server Connection")
        conn_layout = QHBoxLayout(conn_group)
        
        self._conn_indicator = StatusIndicator()
        conn_layout.addWidget(self._conn_indicator)
        
        self._conn_label = QLabel("Not connected")
        conn_layout.addWidget(self._conn_label)
        
        conn_layout.addStretch()
        
        self._sync_label = QLabel("Last sync: Never")
        self._sync_label.setStyleSheet("color: #808080;")
        conn_layout.addWidget(self._sync_label)
        
        self._layout.addWidget(conn_group)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a statistics card widget"""
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 0px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #808080; font-size: 11px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        return card
    
    def _on_start_clicked(self) -> None:
        """Handle Start Service button click"""
        logger.info("Start Service button clicked")
        self.service_action_requested.emit("start")
    
    def _on_stop_clicked(self) -> None:
        """Handle Stop Service button click"""
        logger.info("Stop Service button clicked")
        self.service_action_requested.emit("stop")
    
    def showEvent(self, event) -> None:
        """Called when the page becomes visible"""
        super().showEvent(event)
        logger.info("📺 Dashboard page is now VISIBLE")
    
    def _refresh_status(self) -> None:
        """Refresh all status indicators"""
        # Check service status via facade
        if self._facade:
            try:
                status_data = self._facade.get_service_status()
                self._update_service_status(status_data)
            except Exception:
                self._update_service_status({"running": False, "error": True})
        else:
            # No facade - running in standalone mode
            self._update_service_status({"running": False, "standalone": True})
        
        # Update converter health
        self._update_converter_health()
        
        # Update connection status
        self._update_connection_status()
    
    def _update_service_status(self, status: Dict[str, Any]) -> None:
        """Update service status display"""
        is_running = status.get("running", False)
        is_error = status.get("error", False)
        is_standalone = status.get("standalone", False)
        
        if is_standalone:
            self._service_indicator.set_status("unknown")
            self._service_status_label.setText("Standalone Mode")
            self._service_status_label.setStyleSheet("color: #dcdcaa;")
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._uptime_label.setText("Service mode not active")
        elif is_error:
            self._service_indicator.set_status("error")
            self._service_status_label.setText("Service Error")
            self._service_status_label.setStyleSheet("color: #f48771;")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)
        elif is_running:
            self._service_indicator.set_status("running")
            self._service_status_label.setText("Service Running")
            self._service_status_label.setStyleSheet("color: #4ec9b0;")
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)
            
            # Update uptime if available
            uptime = status.get("uptime_seconds", 0)
            if uptime > 0:
                hours = uptime // 3600
                minutes = (uptime % 3600) // 60
                self._uptime_label.setText(f"Uptime: {hours}h {minutes}m")
        else:
            self._service_indicator.set_status("stopped")
            self._service_status_label.setText("Service Stopped")
            self._service_status_label.setStyleSheet("color: #808080;")
            logger.info(f"Setting Start button enabled: True (was: {self._start_btn.isEnabled()})")
            self._start_btn.setEnabled(True)
            self._stop_btn.setEnabled(False)
            self._uptime_label.setText("Uptime: --")
    
    def _update_converter_health(self) -> None:
        """Update converter health table"""
        self._health_table.setRowCount(0)
        
        # Get converter stats from config
        active_count = 0
        
        for conv in self.config.converters:
            if not conv.enabled:
                continue
            
            active_count += 1
            row = self._health_table.rowCount()
            self._health_table.insertRow(row)
            
            # Status indicator
            status_item = QTableWidgetItem("●")
            status_item.setForeground(QColor("#4ec9b0"))
            self._health_table.setItem(row, 0, status_item)
            
            # Name
            name_item = QTableWidgetItem(conv.name)
            self._health_table.setItem(row, 1, name_item)
            
            # Watch folder
            watch_item = QTableWidgetItem(conv.watch_folder)
            watch_item.setForeground(QColor("#808080"))
            self._health_table.setItem(row, 2, watch_item)
            
            # Get stats from facade if available
            processed_count = "--"
            success_rate = "--%"
            last_run = "--"
            
            if self._facade:
                try:
                    # TODO: Add per-converter statistics to facade
                    pass
                except Exception:
                    pass
            
            processed_item = QTableWidgetItem(str(processed_count))
            self._health_table.setItem(row, 3, processed_item)
            
            success_item = QTableWidgetItem(success_rate)
            self._health_table.setItem(row, 4, success_item)
            
            last_run_item = QTableWidgetItem(last_run)
            last_run_item.setForeground(QColor("#808080"))
            self._health_table.setItem(row, 5, last_run_item)
        
        # Update stat cards with real data if facade available
        if self._facade:
            try:
                status = self._facade.get_service_status()
                self._converters_value.setText(f"{status.get('converters_active', active_count)} Active")
                self._queue_value.setText(f"{status.get('queue_pending', 0)} Pending")
                self._reports_value.setText(f"{status.get('reports_today', 0)} Today")
                # Calculate success rate if we have data
                # TODO: Track success rate
                self._success_value.setText("--%")
            except Exception:
                self._converters_value.setText(f"{active_count} Active")
                self._queue_value.setText("0 Pending")
                self._reports_value.setText("0 Today")
                self._success_value.setText("--%")
        else:
            self._converters_value.setText(f"{active_count} Active")
            self._queue_value.setText("0 Pending")
            self._reports_value.setText("0 Today")
            self._success_value.setText("--%")
    
    def _update_connection_status(self) -> None:
        """Update server connection status"""
        if self.config.service_address:
            # TODO: Check actual connection status
            self._conn_indicator.set_status("unknown")
            self._conn_label.setText(f"Configured: {self.config.service_address}")
            self._sync_label.setText("Last sync: Unknown")
        else:
            self._conn_indicator.set_status("stopped")
            self._conn_label.setText("Not configured")
            self._sync_label.setText("Configure server in Connection page")
    
    def save_config(self) -> None:
        """No config to save"""
        pass
    
    def load_config(self) -> None:
        """Load and display current status"""
        self._refresh_status()
