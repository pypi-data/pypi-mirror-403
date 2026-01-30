"""
Serial Number Handler Settings Page

Configuration page for serial number handling settings.
Based on C# WATS Client Configurator SerialNumberView.

Settings include:
- Serial number type selection
- Reuse on duplicate request
- Reserve offline (pre-allocate serial numbers)
- Batch size and fetch threshold
- In-sequence ordering
- Start from serial number

Note: The actual serial number pool and taking/reserving is handled by the
service, not this GUI page. This page configures how the service handles
serial numbers.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SNHandlerPage(BasePage):
    """
    Serial Number Handler settings page.
    
    Configures serial number handling behavior for the pyWATS Client service.
    Based on C# WATS Client Configurator SerialNumberView.
    """
    
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
        return "Serial Number Handler"
    
    def _setup_ui(self) -> None:
        """Setup page UI for serial number handler settings"""
        
        # Serial Number Type Selection
        type_group = QGroupBox("Serial Number Type")
        type_layout = QVBoxLayout(type_group)
        
        self._type_combo = QComboBox()
        self._type_combo.setPlaceholderText("Select serial number type...")
        self._type_combo.setToolTip("Select the serial number type to configure")
        self._type_combo.currentIndexChanged.connect(self._emit_changed)
        type_layout.addWidget(self._type_combo)
        
        # Status row
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self._status_label = QLabel("Not initialized")
        self._status_label.setStyleSheet("color: #808080;")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        type_layout.addLayout(status_layout)
        
        self._layout.addWidget(type_group)
        
        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(10)
        
        # Row 1: Reuse checkbox | Batch size spinbox
        row1_widget = QWidget()
        row1_layout = QHBoxLayout(row1_widget)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        
        self._reuse_cb = QCheckBox("Reuse")
        self._reuse_cb.setToolTip(
            "Reuse serial numbers on duplicate requests.\n"
            "If enabled, requesting the same serial number returns the previously allocated one."
        )
        self._reuse_cb.stateChanged.connect(self._emit_changed)
        row1_layout.addWidget(self._reuse_cb)
        
        row1_layout.addSpacing(30)
        
        row1_layout.addWidget(QLabel("Batch size:"))
        self._batch_size_spin = QSpinBox()
        self._batch_size_spin.setRange(1, 1000)
        self._batch_size_spin.setValue(20)
        self._batch_size_spin.setToolTip("Number of serial numbers to fetch in each batch")
        self._batch_size_spin.valueChanged.connect(self._emit_changed)
        row1_layout.addWidget(self._batch_size_spin)
        
        row1_layout.addStretch()
        settings_layout.addRow(row1_widget)
        
        # Row 2: Reserve offline checkbox | Fetch when less than spinbox
        row2_widget = QWidget()
        row2_layout = QHBoxLayout(row2_widget)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        
        self._reserve_offline_cb = QCheckBox("Reserve offline")
        self._reserve_offline_cb.setToolTip(
            "Pre-allocate serial numbers for offline use.\n"
            "Reserved numbers are stored locally for use when server is unavailable."
        )
        self._reserve_offline_cb.stateChanged.connect(self._on_reserve_offline_changed)
        row2_layout.addWidget(self._reserve_offline_cb)
        
        row2_layout.addSpacing(30)
        
        row2_layout.addWidget(QLabel("Fetch when less than:"))
        self._fetch_threshold_spin = QSpinBox()
        self._fetch_threshold_spin.setRange(1, 100)
        self._fetch_threshold_spin.setValue(10)
        self._fetch_threshold_spin.setToolTip("Fetch more serial numbers when local pool drops below this count")
        self._fetch_threshold_spin.valueChanged.connect(self._emit_changed)
        row2_layout.addWidget(self._fetch_threshold_spin)
        
        row2_layout.addStretch()
        settings_layout.addRow(row2_widget)
        
        # Row 3: In sequence checkbox | Start from serial number
        row3_widget = QWidget()
        row3_layout = QHBoxLayout(row3_widget)
        row3_layout.setContentsMargins(0, 0, 0, 0)
        
        self._in_sequence_cb = QCheckBox("In sequence")
        self._in_sequence_cb.setToolTip(
            "Allocate serial numbers in strict sequential order.\n"
            "If disabled, serial numbers may be allocated out of order."
        )
        self._in_sequence_cb.stateChanged.connect(self._emit_changed)
        row3_layout.addWidget(self._in_sequence_cb)
        
        row3_layout.addSpacing(30)
        
        row3_layout.addWidget(QLabel("Start from:"))
        self._start_from_edit = QLineEdit()
        self._start_from_edit.setPlaceholderText("e.g., 00000000 or 00-00-00-00-00-00")
        self._start_from_edit.setToolTip("Starting serial number for initialization")
        self._start_from_edit.setMaximumWidth(200)
        self._start_from_edit.textChanged.connect(self._emit_changed)
        row3_layout.addWidget(self._start_from_edit)
        
        row3_layout.addStretch()
        settings_layout.addRow(row3_widget)
        
        self._layout.addWidget(settings_group)
        
        # Action Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self._initialize_btn = QPushButton("Initialize")
        self._initialize_btn.setToolTip("Initialize serial number handler with current settings")
        self._initialize_btn.clicked.connect(self._on_initialize)
        buttons_layout.addWidget(self._initialize_btn)
        
        self._cancel_reserved_btn = QPushButton("Cancel Reserved")
        self._cancel_reserved_btn.setToolTip("Cancel all reserved serial numbers")
        self._cancel_reserved_btn.setEnabled(False)
        self._cancel_reserved_btn.clicked.connect(self._on_cancel_reserved)
        buttons_layout.addWidget(self._cancel_reserved_btn)
        
        self._layout.addLayout(buttons_layout)
        
        # Local Serial Numbers Table (shows reserved/taken serials)
        local_group = QGroupBox("Local Serial Numbers")
        local_layout = QVBoxLayout(local_group)
        
        self._serials_table = QTableWidget()
        self._serials_table.setColumnCount(2)
        self._serials_table.setHorizontalHeaderLabels(["Serial Number", "Taken"])
        
        header = self._serials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self._serials_table.verticalHeader().setVisible(False)
        self._serials_table.setAlternatingRowColors(True)
        self._serials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._serials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        local_layout.addWidget(self._serials_table)
        
        self._layout.addWidget(local_group, 1)
        
        # Initial state
        self._update_ui_state()
    
    def _on_reserve_offline_changed(self, state: int) -> None:
        """Handle reserve offline checkbox change"""
        is_offline = self._reserve_offline_cb.isChecked()
        self._batch_size_spin.setEnabled(is_offline)
        self._fetch_threshold_spin.setEnabled(is_offline)
        self._emit_changed()
    
    def _update_ui_state(self) -> None:
        """Update UI state based on current configuration"""
        is_offline = self._reserve_offline_cb.isChecked()
        self._batch_size_spin.setEnabled(is_offline)
        self._fetch_threshold_spin.setEnabled(is_offline)
    
    def _on_initialize(self) -> None:
        """Initialize the serial number handler"""
        # This would send configuration to the service via IPC
        self._status_label.setText("Ready")
        self._status_label.setStyleSheet("color: #4ec9b0;")
        self._initialize_btn.setText("Re-initialize")
        self._cancel_reserved_btn.setEnabled(True)
    
    def _on_cancel_reserved(self) -> None:
        """Cancel all reserved serial numbers"""
        self._serials_table.setRowCount(0)
        self._status_label.setText("Not initialized")
        self._status_label.setStyleSheet("color: #808080;")
        self._initialize_btn.setText("Initialize")
        self._cancel_reserved_btn.setEnabled(False)
    
    def save_config(self) -> None:
        """Save serial number handler settings to config"""
        # Store in config's sn_handler section
        sn_config = {
            'type': self._type_combo.currentText(),
            'reuse': self._reuse_cb.isChecked(),
            'reserve_offline': self._reserve_offline_cb.isChecked(),
            'in_sequence': self._in_sequence_cb.isChecked(),
            'batch_size': self._batch_size_spin.value(),
            'fetch_threshold': self._fetch_threshold_spin.value(),
            'start_from': self._start_from_edit.text().strip(),
        }
        self.config.sn_handler = sn_config
    
    def load_config(self) -> None:
        """Load serial number handler settings from config"""
        sn_config = getattr(self.config, 'sn_handler', None) or {}
        
        # Load serial number types (would come from service)
        # For now, add common types
        self._type_combo.clear()
        self._type_combo.addItems([
            "MAC address",
            "RunningSN",
            "GUID",
            "Custom"
        ])
        
        # Set current type
        type_name = sn_config.get('type', '')
        if type_name:
            idx = self._type_combo.findText(type_name)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
        
        # Load settings
        self._reuse_cb.setChecked(sn_config.get('reuse', False))
        self._reserve_offline_cb.setChecked(sn_config.get('reserve_offline', False))
        self._in_sequence_cb.setChecked(sn_config.get('in_sequence', False))
        self._batch_size_spin.setValue(sn_config.get('batch_size', 20))
        self._fetch_threshold_spin.setValue(sn_config.get('fetch_threshold', 10))
        self._start_from_edit.setText(sn_config.get('start_from', ''))
        
        self._update_ui_state()
