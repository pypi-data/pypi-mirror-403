"""
Qt Application Entry Point

Provides the main GUI application runner with asyncio integration via qasync.
"""

import sys
import asyncio
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalSocket, QLocalServer

try:
    import qasync
    HAS_QASYNC = True
except ImportError:
    HAS_QASYNC = False

from .main_window import MainWindow
from .login_window import LoginWindow
from ..core.config import ClientConfig, get_default_config_path
from ..core.connection_config import ConnectionState, migrate_legacy_config


def run_gui(config: Optional[ClientConfig] = None, config_path: Optional[Path] = None, instance_id: Optional[str] = None) -> int:
    """
    Run the pyWATS Client GUI application.
    
    Flow:
    1. Check for existing instance (single-instance support)
    2. Load configuration
    3. Check connection state
    4. Show login if not authenticated
    5. Launch main window if authenticated
    
    Args:
        config: ClientConfig instance (optional)
        config_path: Path to configuration file (optional)
        instance_id: Instance ID for multi-instance support (optional)
    
    Returns:
        Exit code
    """
    # Set application metadata
    QCoreApplication.setOrganizationName("WATS")
    QCoreApplication.setApplicationName("WATS Client")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    # Create Qt application
    qt_app = QApplication(sys.argv)
    
    # Check for existing instance and try to activate it
    server_name = f"pyWATS_Client_{instance_id or 'default'}"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    
    if socket.waitForConnected(500):
        # Another instance is running - send activation signal and exit
        socket.write(b"ACTIVATE")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return 0
    
    # No existing instance - create local server to listen for activation requests
    server = QLocalServer()
    QLocalServer.removeServer(server_name)  # Clean up any stale server
    
    if not server.listen(server_name):
        # Failed to create server, but continue anyway
        server = None
    
    # Set Windows taskbar icon (AppUserModelID)
    if sys.platform == 'win32':
        import ctypes
        myappid = 'WATS.Client.1.0.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "favicon.ico"
    if icon_path.exists():
        qt_app.setWindowIcon(QIcon(str(icon_path)))
    
    # Apply dark theme
    qt_app.setStyle("Fusion")
    
    # Load or create configuration
    if config:
        pass  # Use provided config
    elif config_path:
        config = ClientConfig.load_or_create(Path(config_path))
    else:
        config = ClientConfig.load_or_create(get_default_config_path(instance_id))
    
    # Migrate legacy config if needed
    if not hasattr(config, 'connection') or not config.connection:
        config_dict = config.to_dict()
        migrated_dict = migrate_legacy_config(config_dict)
        from ..core.connection_config import ConnectionConfig
        config.connection = ConnectionConfig.from_dict(migrated_dict['connection'])
        config.save()
    
    # Check if authentication is required
    connection_config = getattr(config, 'connection', None)
    needs_auth = (
        connection_config is None or
        not connection_config.is_authenticated() or
        connection_config.get_state() == ConnectionState.NOT_CONNECTED
    )
    
    if needs_auth:
        # Show login dialog
        config = LoginWindow.show_login_dialog(config)
        
        if not config:
            # User cancelled login
            return 0
    
    # Create and show main window
    # Service layer runs separately as a service process
    # GUI connects to service via IPC
    window = MainWindow(config, None)  # config, parent
    
    # Connect server to handle activation requests from other instances
    if server:
        def on_new_connection():
            client_socket = server.nextPendingConnection()
            if client_socket:
                client_socket.waitForReadyRead(1000)
                data = client_socket.readAll().data()
                if data == b"ACTIVATE":
                    # Show and activate the window
                    window.show()
                    window.raise_()
                    window.activateWindow()
                    if window.isMinimized():
                        window.showNormal()
                client_socket.disconnectFromServer()
        
        server.newConnection.connect(on_new_connection)
    
    window.show()
    
    # Run event loop with asyncio integration
    if HAS_QASYNC:
        # Use qasync for asyncio integration - this enables asyncio.create_task() in GUI code
        loop = qasync.QEventLoop(qt_app)
        asyncio.set_event_loop(loop)
        
        with loop:
            return loop.run_forever()
    else:
        # Fallback to standard Qt event loop (no async support)
        return qt_app.exec()
