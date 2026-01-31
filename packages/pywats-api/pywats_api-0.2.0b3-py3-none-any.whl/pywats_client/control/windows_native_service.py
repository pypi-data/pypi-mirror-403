"""
Native Windows Service using pywin32

This module provides a proper Windows Service that appears in:
- services.msc (Windows Services manager)
- Task Manager → Services tab
- sc.exe queries

This is the recommended approach for production Windows deployments.
For development or cross-platform, use the NSSM wrapper instead.

Installation:
    python -m pywats_client install-service --native
    
Control:
    net start pyWATS_Service
    net stop pyWATS_Service
    
Removal:
    python -m pywats_client uninstall-service --native
"""

import sys
import os
import logging
import time
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Event Log constants
EVENT_LOG_APPLICATION = "Application"
EVENT_SOURCE_NAME = "pyWATS"

# Check for pywin32 availability
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import win32evtlogutil
    import win32evtlog
    import socket
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False
    # Create stub classes for type hints when pywin32 not available
    class win32serviceutil:
        class ServiceFramework:
            pass
    

class PyWATSService(win32serviceutil.ServiceFramework if HAS_PYWIN32 else object):
    """
    Native Windows Service for pyWATS Client.
    
    This service:
    - Registers with Windows Service Control Manager (SCM)
    - Appears in Task Manager and services.msc
    - Supports standard service commands (start, stop, pause, continue)
    - Handles pre-shutdown for graceful cleanup on system restart
    - Auto-starts on system boot (if configured)
    - Runs under SYSTEM or specified user account
    
    The service wraps the ClientService class which handles:
    - API connection
    - File monitoring (PendingWatcher)
    - Converter processing
    - Report queue management
    """
    
    # Service configuration
    _svc_name_ = "pyWATS_Service"
    _svc_display_name_ = "pyWATS Client Service"
    _svc_description_ = (
        "WATS Test Report Management - Background service for monitoring "
        "test result files, converting reports, and uploading to WATS server."
    )
    
    # Accept pre-shutdown notifications for graceful shutdown on system restart
    # This gives us extra time to complete pending operations before Windows shuts down
    _svc_deps_ = []  # No dependencies
    
    # Controls we accept - include PRESHUTDOWN for graceful system shutdown handling
    if HAS_PYWIN32:
        _svc_reg_class_ = win32serviceutil.ServiceFramework._svc_reg_class_
    
    # Instance ID for multi-station support (default is single station)
    _instance_id = "default"
    
    def __init__(self, args) -> None:
        """Initialize the Windows Service"""
        if not HAS_PYWIN32:
            raise RuntimeError("pywin32 is required for native Windows service")
        
        win32serviceutil.ServiceFramework.__init__(self, args)
        
        # Create stop event
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)
        
        # Service components (initialized on start)
        self._service = None
        self._running = False
        
        # Get instance ID from environment or registry
        self._instance_id = os.environ.get('PYWATS_INSTANCE_ID', 'default')
        
        socket.setdefaulttimeout(60)
        
        # Accept additional service controls including pre-shutdown
        if HAS_PYWIN32:
            self.accepted_controls = (
                win32service.SERVICE_ACCEPT_STOP |
                win32service.SERVICE_ACCEPT_SHUTDOWN |
                win32service.SERVICE_ACCEPT_PRESHUTDOWN
            )
    
    def SvcOtherEx(self, control: int, event_type: int, data) -> None:
        """
        Handle extended service control requests.
        
        This method handles SERVICE_CONTROL_PRESHUTDOWN which is sent
        before system shutdown/restart, giving us more time for cleanup.
        
        Args:
            control: The service control code
            event_type: Event type (usually 0)
            data: Additional data (usually None)
        """
        if control == win32service.SERVICE_CONTROL_PRESHUTDOWN:
            # Pre-shutdown: System is about to restart/shutdown
            # We have up to 3 minutes (default) for graceful cleanup
            logger.info("Received pre-shutdown notification - initiating graceful shutdown")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                0xF000,  # Custom event ID for pre-shutdown
                (self._svc_name_, "Pre-shutdown notification received")
            )
            # Trigger the same shutdown as SvcStop
            self.SvcStop()
    
    def SvcStop(self):
        """
        Called when the service receives a stop command.
        
        Windows expects this to return quickly, so we:
        1. Report STOP_PENDING status
        2. Signal the stop event
        3. Let SvcDoRun handle graceful shutdown
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self._stop_event)
        self._running = False
        
        # Log to Windows Event Log
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )
    
    def SvcDoRun(self):
        """
        Main service entry point - called when service starts.
        
        This method must not return until the service should stop.
        """
        # Log startup to Windows Event Log
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self._running = True
            self._main()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service failed: {e}")
            logger.exception("Service crashed")
            raise
    
    def _main(self):
        """
        Main service loop.
        
        Initializes and runs the pyWATS ClientService.
        """
        try:
            # Import here to avoid loading heavy modules at service registration
            from pywats_client.service.client_service import ClientService
            
            logger.info(f"Starting pyWATS Service (instance: {self._instance_id})")
            
            # Create client service
            self._service = ClientService(instance_id=self._instance_id)
            
            # Start service in a thread (ClientService.start() blocks)
            import threading
            service_thread = threading.Thread(
                target=self._service.start,
                daemon=True,
                name="ClientService"
            )
            service_thread.start()
            
            # Wait for stop signal
            while self._running:
                # Check stop event every 1 second
                result = win32event.WaitForSingleObject(self._stop_event, 1000)
                if result == win32event.WAIT_OBJECT_0:
                    # Stop event signaled
                    break
            
            # Graceful shutdown
            logger.info("Stopping pyWATS Service...")
            if self._service:
                self._service.stop()
            
            # Wait for service thread to finish
            service_thread.join(timeout=10)
            
            logger.info("pyWATS Service stopped")
            
        except Exception as e:
            logger.exception(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")
            raise


def is_pywin32_available() -> bool:
    """Check if pywin32 is installed and functional"""
    return HAS_PYWIN32


def get_service_name(instance_id: str = "default") -> str:
    """Get service name for an instance"""
    if instance_id == "default":
        return "pyWATS_Service"
    return f"pyWATS_Service_{instance_id}"


def is_service_installed(instance_id: str = "default") -> bool:
    """
    Check if the service is already installed.
    
    Args:
        instance_id: Instance identifier
        
    Returns:
        True if service is installed
    """
    if not HAS_PYWIN32:
        return False
    
    try:
        service_name = get_service_name(instance_id)
        # Try to query service status - will raise if not found
        win32serviceutil.QueryServiceStatus(service_name)
        return True
    except Exception:
        return False


def is_admin() -> bool:
    """Check if running with administrator privileges"""
    if not HAS_PYWIN32:
        return False
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


# =============================================================================
# Windows Event Log Functions
# =============================================================================

def register_event_source(silent: bool = False) -> bool:
    """
    Register pyWATS as an event source in Windows Event Log.
    
    This allows pyWATS to write entries to the Application event log
    with a proper source name that appears in Event Viewer.
    
    Args:
        silent: If True, suppress output
        
    Returns:
        True if registration successful
    """
    if not HAS_PYWIN32:
        return False
    
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    try:
        # Register event source - uses the pywin32 message DLL
        # This creates registry entries under:
        # HKLM\SYSTEM\CurrentControlSet\Services\EventLog\Application\pyWATS
        win32evtlogutil.AddSourceToRegistry(
            EVENT_SOURCE_NAME,
            msgDLL=None,  # Use default message DLL
            eventLogType=EVENT_LOG_APPLICATION
        )
        _print(f"  ✓ Event source '{EVENT_SOURCE_NAME}' registered")
        return True
    except Exception as e:
        # May fail if already registered, which is fine
        if "already exists" in str(e).lower():
            return True
        _print(f"  Warning: Could not register event source: {e}")
        return False


def unregister_event_source(silent: bool = False) -> bool:
    """
    Unregister pyWATS event source from Windows Event Log.
    
    Args:
        silent: If True, suppress output
        
    Returns:
        True if unregistration successful
    """
    if not HAS_PYWIN32:
        return False
    
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    try:
        win32evtlogutil.RemoveSourceFromRegistry(
            EVENT_SOURCE_NAME,
            EVENT_LOG_APPLICATION
        )
        _print(f"  ✓ Event source '{EVENT_SOURCE_NAME}' removed")
        return True
    except Exception as e:
        # May fail if not registered, which is fine during uninstall
        return True


def log_event(
    message: str,
    event_type: str = "info",
    event_id: int = 1
) -> bool:
    """
    Write an entry to the Windows Event Log.
    
    This function can be called from anywhere in pyWATS to log
    important events that administrators can view in Event Viewer.
    
    Args:
        message: The message to log
        event_type: "info", "warning", or "error"
        event_id: Event ID number (default: 1)
        
    Returns:
        True if logging successful
        
    Example:
        from pywats_client.control.windows_native_service import log_event
        log_event("Service started successfully", "info")
        log_event("Connection failed", "error")
    """
    if not HAS_PYWIN32:
        return False
    
    try:
        # Map event type to Windows constant
        type_map = {
            "info": win32evtlog.EVENTLOG_INFORMATION_TYPE,
            "warning": win32evtlog.EVENTLOG_WARNING_TYPE,
            "error": win32evtlog.EVENTLOG_ERROR_TYPE,
        }
        event_type_const = type_map.get(event_type.lower(), win32evtlog.EVENTLOG_INFORMATION_TYPE)
        
        win32evtlogutil.ReportEvent(
            EVENT_SOURCE_NAME,
            event_id,
            eventType=event_type_const,
            strings=[message]
        )
        return True
    except Exception as e:
        logger.debug(f"Could not write to Event Log: {e}")
        return False


def install_service(
    instance_id: str = "default",
    startup: str = "auto",
    username: Optional[str] = None,
    password: Optional[str] = None,
    silent: bool = False
) -> bool:
    """
    Install pyWATS as a native Windows Service.
    
    Args:
        instance_id: Instance identifier (default: "default")
        startup: Startup type - "auto", "manual", or "disabled"
        username: Service account username (None for LocalSystem)
        password: Service account password
        silent: If True, suppress all output
        
    Returns:
        True if installation successful
    """
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    if not HAS_PYWIN32:
        _print("ERROR: pywin32 is required for native Windows service")
        _print("Install with: pip install pywin32")
        return False
    
    if not is_admin():
        _print("ERROR: Administrator privileges required")
        _print("Please run as Administrator")
        return False
    
    try:
        # Configure service name for instance
        service_name = get_service_name(instance_id)
        display_name = f"pyWATS Client Service"
        if instance_id != "default":
            display_name = f"pyWATS Client Service ({instance_id})"
        
        # Get Python executable path
        python_exe = sys.executable
        
        # Get this module's path
        module_path = Path(__file__).resolve()
        
        # Build service command
        # We need to run this module directly for the service
        service_cmd = f'"{python_exe}" "{module_path}"'
        
        # Set instance ID via environment for multi-instance
        if instance_id != "default":
            os.environ['PYWATS_INSTANCE_ID'] = instance_id
        
        _print(f"Installing service: {service_name}")
        _print(f"  Display name: {display_name}")
        _print(f"  Instance ID: {instance_id}")
        _print(f"  Startup type: {startup}")
        
        # Map startup type
        startup_map = {
            "auto": win32service.SERVICE_AUTO_START,
            "manual": win32service.SERVICE_DEMAND_START,
            "disabled": win32service.SERVICE_DISABLED
        }
        startup_type = startup_map.get(startup, win32service.SERVICE_AUTO_START)
        
        # Temporarily modify class attributes for this instance
        PyWATSService._svc_name_ = service_name
        PyWATSService._svc_display_name_ = display_name
        PyWATSService._instance_id = instance_id
        
        # Install service
        win32serviceutil.InstallService(
            PyWATSService._svc_reg_class_,
            service_name,
            display_name,
            startType=startup_type,
            userName=username,
            password=password,
            description=PyWATSService._svc_description_
        )
        
        _print(f"\n✓ Service '{service_name}' installed successfully")
        _print(f"\nTo start the service:")
        _print(f"  net start {service_name}")
        _print(f"  or: sc start {service_name}")
        _print(f"\nTo view in Services:")
        _print(f"  services.msc")
        
        # Configure service recovery options (auto-restart on failure)
        _configure_service_recovery(service_name, silent=silent)
        
        # Configure delayed auto-start if startup is "auto"
        if startup == "auto":
            _configure_delayed_start(service_name, silent=silent)
        
        # Configure pre-shutdown timeout for graceful shutdown on system restart
        _configure_preshutdown_timeout(service_name, timeout_ms=180000, silent=silent)
        
        # Register Windows Event Log source
        register_event_source(silent=silent)
        
        # Log installation to Event Log
        log_event(f"pyWATS Service installed (instance: {instance_id})", "info")
        
        return True
        
    except Exception as e:
        _print(f"ERROR: Failed to install service: {e}")
        logger.exception("Service installation failed")
        return False


def _configure_service_recovery(service_name: str, silent: bool = False) -> bool:
    """
    Configure service recovery options for auto-restart on failure.
    
    Recovery policy:
    - First failure: Restart after 5 seconds
    - Second failure: Restart after 5 seconds  
    - Subsequent failures: Restart after 30 seconds
    - Reset failure count after 24 hours (86400 seconds)
    
    Args:
        service_name: Name of the Windows service
        silent: If True, suppress output
        
    Returns:
        True if configuration successful
    """
    import subprocess
    
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    try:
        # sc.exe failure <service> reset= <seconds> actions= <action>/<delay_ms>/...
        # actions: restart, run, reboot (we use restart)
        # delays in milliseconds: 5000ms = 5s, 30000ms = 30s
        cmd = [
            "sc.exe", "failure", service_name,
            "reset=", "86400",  # Reset failure count after 24 hours
            "actions=", "restart/5000/restart/5000/restart/30000"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True  # Needed for sc.exe on some systems
        )
        
        if result.returncode == 0:
            _print("  ✓ Service recovery configured (auto-restart on failure)")
            return True
        else:
            _print(f"  Warning: Could not configure service recovery: {result.stderr}")
            return False
            
    except Exception as e:
        _print(f"  Warning: Could not configure service recovery: {e}")
        return False


def _configure_delayed_start(service_name: str, silent: bool = False) -> bool:
    """
    Configure service for delayed auto-start.
    
    Delayed start means the service starts after other auto-start services,
    which helps ensure network services are available.
    
    Args:
        service_name: Name of the Windows service
        silent: If True, suppress output
        
    Returns:
        True if configuration successful
    """
    import subprocess
    
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    try:
        # sc.exe config <service> start= delayed-auto
        cmd = ["sc.exe", "config", service_name, "start=", "delayed-auto"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            _print("  ✓ Delayed auto-start configured (starts after network ready)")
            return True
        else:
            _print(f"  Warning: Could not configure delayed start: {result.stderr}")
            return False
            
    except Exception as e:
        _print(f"  Warning: Could not configure delayed start: {e}")
        return False


def _configure_preshutdown_timeout(service_name: str, timeout_ms: int = 180000, silent: bool = False) -> bool:
    """
    Configure pre-shutdown timeout for graceful shutdown on system restart.
    
    When Windows is shutting down or restarting, services receive a pre-shutdown
    notification. This timeout specifies how long the service has to complete
    cleanup before being forcefully terminated.
    
    Args:
        service_name: Name of the Windows service
        timeout_ms: Timeout in milliseconds (default: 180000 = 3 minutes)
        silent: If True, suppress output
        
    Returns:
        True if configuration successful
    """
    import subprocess
    
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    try:
        # Use registry to set SERVICE_CONFIG_PRESHUTDOWN_INFO
        # Path: HKLM\SYSTEM\CurrentControlSet\Services\<service>\PreshutdownTimeout
        import winreg
        
        key_path = f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "PreshutdownTimeout", 0, winreg.REG_DWORD, timeout_ms)
        
        timeout_sec = timeout_ms // 1000
        _print(f"  ✓ Pre-shutdown timeout configured ({timeout_sec}s for graceful shutdown)")
        return True
        
    except Exception as e:
        _print(f"  Warning: Could not configure pre-shutdown timeout: {e}")
        return False


def uninstall_service(instance_id: str = "default", silent: bool = False) -> bool:
    """
    Uninstall the Windows Service.
    
    Args:
        instance_id: Instance identifier
        silent: If True, suppress all output
        
    Returns:
        True if uninstallation successful
    """
    def _print(msg: str) -> None:
        if not silent:
            print(msg)
    
    if not HAS_PYWIN32:
        _print("ERROR: pywin32 is required")
        return False
    
    if not is_admin():
        _print("ERROR: Administrator privileges required")
        return False
    
    try:
        service_name = get_service_name(instance_id)
        
        # Log uninstallation to Event Log before removing
        log_event(f"pyWATS Service uninstalling (instance: {instance_id})", "info")
        
        _print(f"Stopping service '{service_name}'...")
        try:
            win32serviceutil.StopService(service_name)
            time.sleep(2)  # Give it time to stop
        except Exception:
            pass  # Service might not be running
        
        _print(f"Removing service '{service_name}'...")
        win32serviceutil.RemoveService(service_name)
        
        # Note: We don't unregister the event source here because
        # other instances might still be using it, and it doesn't
        # cause any harm to leave it registered.
        
        _print(f"\n✓ Service '{service_name}' removed successfully")
        return True
        
    except Exception as e:
        _print(f"ERROR: Failed to remove service: {e}")
        return False


def get_service_status(instance_id: str = "default") -> Optional[str]:
    """
    Get the current status of the Windows Service.
    
    Returns:
        Status string or None if service not found
    """
    if not HAS_PYWIN32:
        return None
    
    try:
        import win32serviceutil
        service_name = get_service_name(instance_id)
        
        status = win32serviceutil.QueryServiceStatus(service_name)
        state = status[1]
        
        state_map = {
            win32service.SERVICE_STOPPED: "Stopped",
            win32service.SERVICE_START_PENDING: "Starting",
            win32service.SERVICE_STOP_PENDING: "Stopping",
            win32service.SERVICE_RUNNING: "Running",
            win32service.SERVICE_CONTINUE_PENDING: "Continuing",
            win32service.SERVICE_PAUSE_PENDING: "Pausing",
            win32service.SERVICE_PAUSED: "Paused",
        }
        
        return state_map.get(state, "Unknown")
        
    except Exception:
        return None


def start_service(instance_id: str = "default") -> bool:
    """Start the Windows Service"""
    if not HAS_PYWIN32:
        return False
    
    try:
        service_name = get_service_name(instance_id)
        win32serviceutil.StartService(service_name)
        return True
    except Exception as e:
        print(f"ERROR: Failed to start service: {e}")
        return False


def stop_service(instance_id: str = "default") -> bool:
    """Stop the Windows Service"""
    if not HAS_PYWIN32:
        return False
    
    try:
        service_name = get_service_name(instance_id)
        win32serviceutil.StopService(service_name)
        return True
    except Exception as e:
        print(f"ERROR: Failed to stop service: {e}")
        return False


# Entry point for service execution
if __name__ == '__main__':
    if HAS_PYWIN32:
        if len(sys.argv) == 1:
            # Running as service
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(PyWATSService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            # Command line handling (install, remove, etc.)
            win32serviceutil.HandleCommandLine(PyWATSService)
    else:
        print("ERROR: pywin32 is required for Windows service functionality")
        print("Install with: pip install pywin32")
        sys.exit(1)
