"""
Software Distribution Settings Page

Configuration page for software distribution settings.
Based on C# WATS Client Configurator SWDistView.

This page configures where software packages from WATS will be installed.
The actual downloading and installation is handled by the service.

Settings include:
- Root folder for software installation
- File transfer chunk size (advanced)
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QSpinBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from .base import BasePage
from ...core.config import ClientConfig

if TYPE_CHECKING:
    from ..main_window import MainWindow


class SoftwarePage(BasePage):
    """
    Software Distribution settings page.
    
    Configures software distribution behavior for the pyWATS Client service.
    Based on C# WATS Client Configurator SWDistView.
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
        return "Software Distribution"
    
    def _setup_ui(self) -> None:
        """Setup page UI for software distribution settings"""
        
        # Root Folder Setting
        root_group = QGroupBox("Software Distribution")
        root_layout = QVBoxLayout(root_group)
        
        # Root folder row
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Root folder:"))
        
        self._root_folder_edit = QLineEdit()
        self._root_folder_edit.setPlaceholderText("Select folder for software installations...")
        self._root_folder_edit.setToolTip(
            "Root directory where software packages will be installed.\n"
            "The folder must exist and be empty."
        )
        self._root_folder_edit.textChanged.connect(self._emit_changed)
        folder_layout.addWidget(self._root_folder_edit, 1)
        
        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.clicked.connect(self._on_browse)
        folder_layout.addWidget(self._browse_btn)
        
        root_layout.addLayout(folder_layout)
        
        # Description
        desc_label = QLabel(
            "The root folder is where software packages from WATS will be installed.\n"
            "Each package will be placed in a subdirectory under this folder.\n"
            "The folder must exist and be empty when first configured."
        )
        desc_label.setStyleSheet("color: #808080; font-size: 11px;")
        desc_label.setWordWrap(True)
        root_layout.addWidget(desc_label)
        
        self._layout.addWidget(root_group)
        
        # Advanced Options (collapsed by default)
        advanced_group = QGroupBox("Advanced Options")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Chunk size
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel("File transfer chunk size:"))
        
        self._chunk_size_spin = QSpinBox()
        self._chunk_size_spin.setRange(1024, 10485760)  # 1KB to 10MB
        self._chunk_size_spin.setValue(65536)  # 64KB default
        self._chunk_size_spin.setSingleStep(1024)
        self._chunk_size_spin.setSuffix(" bytes")
        self._chunk_size_spin.setToolTip(
            "Size of each chunk when transferring files.\n"
            "Larger chunks may be faster but use more memory."
        )
        self._chunk_size_spin.valueChanged.connect(self._emit_changed)
        chunk_layout.addWidget(self._chunk_size_spin)
        
        chunk_layout.addStretch()
        advanced_layout.addLayout(chunk_layout)
        
        # Chunk size description
        chunk_desc = QLabel(
            "The chunk size controls how large each piece of a file transfer is.\n"
            "Default: 65536 bytes (64 KB). Increase for faster transfers on reliable connections."
        )
        chunk_desc.setStyleSheet("color: #808080; font-size: 11px;")
        chunk_desc.setWordWrap(True)
        advanced_layout.addWidget(chunk_desc)
        
        self._layout.addWidget(advanced_group)
        
        # Add stretch to push everything to top
        self._layout.addStretch()
    
    def _on_browse(self) -> None:
        """Browse for root folder"""
        current = self._root_folder_edit.text() or str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Software Distribution Root Folder",
            current
        )
        
        if folder:
            folder_path = Path(folder)
            
            # Validate folder
            if not folder_path.exists():
                QMessageBox.warning(
                    self, "Invalid Folder",
                    "The selected folder does not exist."
                )
                return
            
            # Check if empty (only for new configuration)
            if self._root_folder_edit.text() != folder:
                contents = list(folder_path.iterdir())
                if contents:
                    reply = QMessageBox.question(
                        self, "Folder Not Empty",
                        "The selected folder is not empty.\n\n"
                        "For new configurations, an empty folder is recommended.\n"
                        "Use this folder anyway?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            
            self._root_folder_edit.setText(folder)
    
    def save_config(self) -> None:
        """Save software distribution settings to config"""
        self.config.sw_dist_root = self._root_folder_edit.text().strip()
        self.config.sw_dist_chunk_size = self._chunk_size_spin.value()
    
    def load_config(self) -> None:
        """Load software distribution settings from config"""
        root = getattr(self.config, 'sw_dist_root', '') or ''
        self._root_folder_edit.setText(root)
        
        chunk_size = getattr(self.config, 'sw_dist_chunk_size', 65536)
        self._chunk_size_spin.setValue(chunk_size)

