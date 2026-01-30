"""
Instance Selector Widget

Displays discovered service instances and allows switching between them.
Shows running status and connection state for each instance.
"""

import logging
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush

from ...service.ipc_client import ServiceDiscovery, InstanceInfo

logger = logging.getLogger(__name__)


class InstanceSelector(QWidget):
    """
    Widget for selecting between multiple service instances.
    
    Displays list of discovered instances with status indicators.
    Automatically refreshes to detect new/stopped instances.
    
    Signals:
        instance_selected: Emitted when user selects an instance (instance_id)
    """
    
    instance_selected = Signal(str)  # instance_id
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize instance selector.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._current_instance_id: Optional[str] = None
        self._instances: List[InstanceInfo] = []
        self._refresh_timer: Optional[QTimer] = None
        
        self._setup_ui()
        self._start_refresh_timer()
    
    def _setup_ui(self) -> None:
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header = QLabel("Service Instances")
        header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(header)
        
        # Instance list
        self._list_widget = QListWidget()
        self._list_widget.setMinimumWidth(150)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list_widget, stretch=1)
        
        # Status label
        self._status_label = QLabel("No services running")
        self._status_label.setStyleSheet("color: #888; font-size: 9pt;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        # Start Service button (shown when no instances running)
        self._start_service_btn = QPushButton("Start Service")
        self._start_service_btn.clicked.connect(self._on_start_service)
        self._start_service_btn.setToolTip("Start default service instance")
        layout.addWidget(self._start_service_btn)
        
        # Initial refresh
        self.refresh()
    
    def _start_refresh_timer(self) -> None:
        """Start automatic refresh timer"""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def refresh(self) -> None:
        """Refresh instance list"""
        try:
            # Discover instances
            instances = ServiceDiscovery.discover_instances(timeout_ms=500)
            
            self._instances = instances
            self._update_list()
            
            if instances:
                self._status_label.setText(f"Found {len(instances)} instance(s)")
                self._start_service_btn.hide()
                
                # Auto-select first instance if none selected
                if not self._current_instance_id and instances:
                    self._select_instance(instances[0].instance_id)
            else:
                self._status_label.setText("No services running\nUse: python -m pywats_client service")
                self._start_service_btn.show()
        
        except Exception as e:
            logger.error(f"Error refreshing instances: {e}")
            self._status_label.setText(f"Error: {str(e)[:50]}")
    
    def _update_list(self) -> None:
        """Update the list widget with current instances"""
        self._list_widget.clear()
        
        for instance in self._instances:
            item = QListWidgetItem()
            
            # Format display text
            status_icon = "●" if instance.status != "offline" else "○"
            text = f"{status_icon} {instance.instance_id}"
            
            if instance.connection_state and instance.connection_state != "unknown":
                text += f" ({instance.connection_state})"
            
            item.setText(text)
            item.setData(Qt.UserRole, instance.instance_id)
            
            # Color based on status
            if instance.status == "online" or instance.status.lower() == "running":
                item.setForeground(QBrush(QColor("#4EC9B0")))  # Green
            elif instance.status == "offline":
                item.setForeground(QBrush(QColor("#888")))  # Gray
            else:
                item.setForeground(QBrush(QColor("#CE9178")))  # Orange
            
            self._list_widget.addItem(item)
            
            # Select if current
            if instance.instance_id == self._current_instance_id:
                item.setSelected(True)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click"""
        instance_id = item.data(Qt.UserRole)
        if instance_id:
            self._select_instance(instance_id)
    
    def _select_instance(self, instance_id: str) -> None:
        """Select an instance"""
        if self._current_instance_id != instance_id:
            self._current_instance_id = instance_id
            logger.info(f"Selected instance: {instance_id}")
            self.instance_selected.emit(instance_id)
    
    def _on_start_service(self) -> None:
        """Handle start service button click"""
        import subprocess
        import sys
        
        try:
            # Start service in background
            if sys.platform == "win32":
                # Windows: Start detached process
                subprocess.Popen(
                    [sys.executable, "-m", "pywats_client", "service"],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Unix: Start with nohup
                subprocess.Popen(
                    [sys.executable, "-m", "pywats_client", "service"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            self._status_label.setText("Starting service...")
            
            # Refresh after a delay
            QTimer.singleShot(2000, self.refresh)
        
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            self._status_label.setText(f"Failed to start: {str(e)[:30]}")
    
    def get_current_instance_id(self) -> Optional[str]:
        """Get currently selected instance ID"""
        return self._current_instance_id
    
    def get_instances(self) -> List[InstanceInfo]:
        """Get list of discovered instances"""
        return self._instances.copy()
    
    def stop_refresh(self) -> None:
        """Stop automatic refresh timer"""
        if self._refresh_timer:
            self._refresh_timer.stop()
    
    def start_refresh(self) -> None:
        """Start automatic refresh timer"""
        if self._refresh_timer and not self._refresh_timer.isActive():
            self._refresh_timer.start(5000)
    
    def closeEvent(self, event) -> None:
        """Handle widget close"""
        self.stop_refresh()
        super().closeEvent(event)
