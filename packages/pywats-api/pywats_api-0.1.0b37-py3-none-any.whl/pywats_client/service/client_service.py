"""
Client Service - Main Service Controller

Equivalent to ClientSvc.cs in C# implementation.
Manages service lifecycle, coordinates all components, and provides health monitoring.
"""

import logging
import signal
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from enum import Enum

from pywats import pyWATS
from pywats.core.exceptions import PyWATSError

from ..core.config import ClientConfig
from .converter_pool import ConverterPool
from .pending_watcher import PendingWatcher

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status states"""
    STOPPED = "Stopped"
    START_PENDING = "StartPending"
    RUNNING = "Running"
    STOP_PENDING = "StopPending"
    PAUSED = "Paused"


class ClientService:
    """
    Main WATS Client Service Controller.
    
    Equivalent to ClientSvc.cs - manages service lifecycle and coordinates:
    - API connection
    - Converter pool (file processing)
    - Pending watcher (report queue)
    - Watchdog timer (health checks)
    - Ping timer (connectivity checks)
    - Registration timer (status updates)
    
    Usage:
        service = ClientService(instance_id="default")
        service.start()  # Blocks until stopped
    """
    
    def __init__(self, instance_id: str = "default") -> None:
        """
        Initialize service.
        
        Args:
            instance_id: Instance identifier for multi-instance support
        """
        self.instance_id = instance_id
        self.config = ClientConfig.load_for_instance(instance_id)
        
        # Service state
        self._status = ServiceStatus.STOPPED
        self._running = False
        self._stop_event = threading.Event()
        
        # API client (like TDM_ClientService api in C#)
        self.api: Optional[pyWATS] = None
        
        # Core components
        self.converter_pool: Optional[ConverterPool] = None
        self.pending_watcher: Optional[PendingWatcher] = None
        
        # Timers (like C# Timer objects)
        self._watchdog_timer: Optional[threading.Timer] = None
        self._ping_timer: Optional[threading.Timer] = None
        self._register_timer: Optional[threading.Timer] = None
        
        # IPC server for GUI communication
        self._ipc_server: Optional[any] = None
        
        # Qt application for IPC (needs to be in main thread)
        from PySide6.QtCore import QCoreApplication
        if not QCoreApplication.instance():
            self._qt_app = QCoreApplication([])
        else:
            self._qt_app = QCoreApplication.instance()
        
        # Config file watcher (hot-reload like C#)
        self._config_watcher: Optional[any] = None
        
        logger.info(f"WATS Client Service initialized [instance: {instance_id}]")
    
    @property
    def status(self) -> ServiceStatus:
        """Get current service status"""
        return self._status
    
    @property
    def api_status(self) -> str:
        """Get API connection status (like C# APIStatus property)"""
        if self.api:
            return "Online"  # TODO: Get actual status from pyWATS client
        return "Offline"
    
    def start(self) -> None:
        """
        Start the service (blocking).
        
        Equivalent to OnStart() in ClientSvc.cs:
        1. Initialize API and connect to server
        2. Start watchdog timer (60s health checks)
        3. Start ping timer (5min connectivity)
        4. Start registration timer (1hr status updates)
        5. Initialize PendingWatcher (report queue)
        6. Initialize Conversion system (converter pool)
        7. Setup config file monitoring
        """
        if self._running:
            logger.warning("Service already running")
            return
        
        logger.info(f"WATS Client Service [v.1.0.0] starting @{datetime.now().isoformat()}")
        self._set_status(ServiceStatus.START_PENDING)
        
        try:
            # 1. Initialize and connect to server (synchronous like C#)
            self._initialize_api()
            
            # 2. Set status to Running
            self._set_status(ServiceStatus.RUNNING)
            self._running = True
            
            # 3. Create and activate watchdog timer (60s)
            self._start_watchdog_timer()
            logger.info("Watchdog timer initialized (60s)")
            
            # 4. Create and activate ping timer (5min)
            self._start_ping_timer()
            logger.info("Ping timer configured (5min)")
            
            # 5. Create and activate registration timer (1hr)
            self._start_register_timer()
            logger.info("Update client timer configured (1hr)")
            
            # 6. Initialize PendingWatcher (async like C#)
            self.pending_watcher = PendingWatcher(
                api_client=self.api,
                reports_directory=self.config.get_reports_path(),
                initialize_async=True
            )
            logger.info("PendingWatcher started, asynchronous initialization")
            
            # 7. Initialize converter pool (async like C#)
            self.converter_pool = ConverterPool(
                config=self.config,
                api_client=self.api
            )
            # Start converters on background thread
            threading.Thread(
                target=self.converter_pool.initialize_converters,
                daemon=True
            ).start()
            
            # 8. Setup config file watcher
            self._setup_config_watcher()
            logger.info("Settings file listener started")
            
            # 9. Setup IPC server for GUI communication
            self._setup_ipc_server()
            
            logger.info("WATS Client Service started")
            
            # 10. Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 11. Run event loop (blocks until stop)
            self._run_event_loop()
            
        except Exception as e:
            logger.error(f"Service startup failed: {e}", exc_info=True)
            self._set_status(ServiceStatus.STOPPED)
            raise
    
    def stop(self) -> None:
        """
        Stop the service gracefully.
        
        Equivalent to OnStop() in ClientSvc.cs.
        """
        if not self._running:
            return
        
        logger.info("Stopping WATS Client Service")
        self._set_status(ServiceStatus.STOP_PENDING)
        
        # Stop all timers
        self._stop_all_timers()
        
        # Stop components
        if self.converter_pool:
            self.converter_pool.dispose()
            self.converter_pool = None
        
        if self.pending_watcher:
            self.pending_watcher.dispose()
            self.pending_watcher = None
        
        if self._ipc_server:
            self._ipc_server.stop()
            self._ipc_server = None
        
        # Disconnect API
        if self.api:
            # TODO: Call proper disconnect/dispose
            self.api = None
        
        # Stop Qt event loop
        if self._qt_app:
            self._qt_app.quit()
        
        # Signal stop event (for fallback)
        self._stop_event.set()
        
        self._running = False
        self._set_status(ServiceStatus.STOPPED)
        logger.info("WATS Client Service stopped")
    
    def _initialize_api(self) -> None:
        """
        Initialize API and connect to server.
        
        Equivalent to:
            api = new TDM_ClientService();
            api.InitializeAPI(InitializationMode.Syncronous, true);
        """
        logger.info("Initializing API...")
        
        try:
            # Get runtime credentials (with env var fallback)
            service_address, api_token = self.config.get_runtime_credentials()
            
            # Create API client
            self.api = pyWATS(
                base_url=service_address,
                token=api_token
            )
            
            # TODO: Call RegisterClient, GetCodes, etc. if needed
            # In C# this is done in TDM.InitializeAPI()
            
            logger.info("API initialized")
            
        except Exception as e:
            logger.error(f"API initialization failed: {e}", exc_info=True)
            # In C# version, service continues even if not activated/registered
            # We should do the same - degraded mode
    
    def _start_watchdog_timer(self) -> None:
        """
        Start watchdog timer (60s health checks).
        
        Equivalent to:
            wdt = new Timer(60000);
            wdt.Elapsed += wdt_Elapsed;
            wdt.Enabled = true;
        """
        def watchdog_check():
            if self._running:
                self._on_watchdog_elapsed()
                # Reschedule
                self._watchdog_timer = threading.Timer(60.0, watchdog_check)
                self._watchdog_timer.daemon = True
                self._watchdog_timer.start()
        
        self._watchdog_timer = threading.Timer(60.0, watchdog_check)
        self._watchdog_timer.daemon = True
        self._watchdog_timer.start()
    
    def _start_ping_timer(self) -> None:
        """
        Start ping timer (5min connectivity checks).
        
        Equivalent to:
            tmrPing = new Timer(300000);
            tmrPing.Elapsed += tmr5m_Elapsed;
        """
        def ping_check():
            if self._running:
                self._on_ping_elapsed()
                # Reschedule
                self._ping_timer = threading.Timer(300.0, ping_check)
                self._ping_timer.daemon = True
                self._ping_timer.start()
        
        self._ping_timer = threading.Timer(300.0, ping_check)
        self._ping_timer.daemon = True
        self._ping_timer.start()
    
    def _start_register_timer(self) -> None:
        """
        Start registration timer (1hr status updates).
        
        Equivalent to:
            tmrReg = new Timer(3600000);
            tmrReg.Elapsed += tmr1hr_Elapsed;
        """
        def register_check():
            if self._running:
                self._on_register_elapsed()
                # Reschedule
                self._register_timer = threading.Timer(3600.0, register_check)
                self._register_timer.daemon = True
                self._register_timer.start()
        
        self._register_timer = threading.Timer(3600.0, register_check)
        self._register_timer.daemon = True
        self._register_timer.start()
    
    def _stop_all_timers(self) -> None:
        """Stop all periodic timers"""
        for timer in [self._watchdog_timer, self._ping_timer, self._register_timer]:
            if timer:
                timer.cancel()
        
        self._watchdog_timer = None
        self._ping_timer = None
        self._register_timer = None
    
    def _on_watchdog_elapsed(self) -> None:
        """
        Watchdog timer callback (60s).
        
        Equivalent to wdt_Elapsed in ClientSvc.cs:
        - Check converter states
        - Check pending watcher state
        - Restart stuck components
        """
        try:
            logger.debug("Watchdog check")
            
            # Check converter pool health
            if self.converter_pool:
                self.converter_pool.check_state()
            
            # Check pending watcher health
            if self.pending_watcher:
                self.pending_watcher.check_state()
            
        except Exception as e:
            logger.error(f"Watchdog check error: {e}", exc_info=True)
    
    def _on_ping_elapsed(self) -> None:
        """
        Ping timer callback (5min).
        
        Equivalent to tmr5m_Elapsed in ClientSvc.cs:
        - Ping server to check connectivity
        - Trigger pending report submission if online
        """
        try:
            logger.debug("Ping check")
            
            # TODO: Call api.Ping() when available in pyWATS
            # if self.api and self.api.ping():
            #     # Server is online, trigger pending submission
            #     if self.pending_watcher:
            #         self.pending_watcher.trigger_submission()
            
        except Exception as e:
            logger.error(f"Ping check error: {e}", exc_info=True)
    
    def _on_register_elapsed(self) -> None:
        """
        Registration timer callback (1hr).
        
        Equivalent to tmr1hr_Elapsed in ClientSvc.cs:
        - Post client status to server
        - Update client registration
        """
        try:
            logger.debug("Registration check")
            
            # TODO: Call api.PostClientLog() or similar
            # TODO: Call api.UpdateClient() or similar
            
        except Exception as e:
            logger.error(f"Registration check error: {e}", exc_info=True)
    
    def _setup_config_watcher(self) -> None:
        """
        Setup config file watcher for hot-reload.
        
        Equivalent to:
            fswSettings = new FileSystemWatcher(Env.DataDir, Env.SettingsFileName);
            fswSettings.Changed += fswSettings_Changed;
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, callback):
                    self.callback = callback
                    self._reload_timer = None
                
                def on_modified(self, event):
                    if event.src_path.endswith('config.json'):
                        # Debounce: Schedule reload after 1 second
                        if self._reload_timer:
                            self._reload_timer.cancel()
                        self._reload_timer = threading.Timer(1.0, self.callback)
                        self._reload_timer.start()
            
            self._config_watcher = Observer()
            handler = ConfigFileHandler(self._reload_config)
            
            config_dir = self.config.config_path.parent
            self._config_watcher.schedule(handler, str(config_dir), recursive=False)
            self._config_watcher.start()
            
        except Exception as e:
            logger.warning(f"Failed to setup config watcher: {e}")
    
    def _reload_config(self) -> None:
        """
        Reload configuration from file.
        
        Equivalent to tmrReloadConfig_Elapsed in ClientSvc.cs.
        """
        try:
            logger.info("Configuration reload starting")
            
            # Reload config
            new_config = ClientConfig.load(self.config.config_path)
            
            # Update relevant components
            # Note: Some changes may require service restart
            # For now, just update the config reference
            self.config = new_config
            
            # TODO: Notify components of config change
            # if self.converter_pool:
            #     self.converter_pool.reload_config(new_config)
            
            logger.info("Configuration reload completed")
            
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}", exc_info=True)
    
    def _setup_ipc_server(self) -> None:
        """Setup IPC server for GUI communication"""
        try:
            from .ipc_server import IPCServer
            self._ipc_server = IPCServer(self.instance_id, self)
            self._ipc_server.start()
            logger.info(f"IPC server started: pyWATS_Service_{self.instance_id}")
        except Exception as e:
            logger.warning(f"Failed to start IPC server: {e}")
            # Not critical - service can run without IPC
    
    def _run_event_loop(self) -> None:
        """
        Main event loop (blocks until stop).
        
        Uses Qt event loop for IPC server support.
        In C# this is handled by ServiceBase infrastructure.
        """
        logger.info("Service event loop running (Qt)")
        
        # Run Qt event loop (blocks until quit)
        if self._qt_app:
            self._qt_app.exec()
        else:
            # Fallback to simple wait if Qt not available
            self._stop_event.wait()
        
        logger.info("Service event loop exiting")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals (SIGINT, SIGTERM)"""
        logger.info(f"Received signal {signum}, stopping service")
        self.stop()
    
    def _set_status(self, status: ServiceStatus) -> None:
        """Update service status"""
        if self._status != status:
            old_status = self._status
            self._status = status
            logger.info(f"Service status: {old_status.value} -> {status.value}")
            
            # TODO: Persist status to file/registry like C#
            # In C# this is SaveStatus() calling registry
    
    def get_status_dict(self) -> dict:
        """
        Get service status as dictionary (for IPC queries).
        
        Returns:
            Dictionary with service status information
        """
        return {
            'status': self.status.value,
            'api_status': self.api_status,
            'instance_id': self.instance_id,
            'config_file': str(self.config.config_path),
            'converters': self.converter_pool.get_statistics() if self.converter_pool else [],
            'queue_size': self.pending_watcher.queue_size() if self.pending_watcher else 0,
        }


def main(instance_id: str = "default"):
    """
    Service entry point.
    
    Usage:
        python -m pywats_client.service.client_service
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start service
    service = ClientService(instance_id)
    
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        service.stop()


if __name__ == '__main__':
    main()
