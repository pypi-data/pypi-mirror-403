"""
Platform Service Adapter Interface

Provides a clean abstraction for platform-specific service implementations.
This allows the core application to work with services without knowing
the underlying platform details.

Usage:
    adapter = get_service_adapter()
    adapter.install(instance_id="default")
    adapter.start()
    status = adapter.get_status()
"""

import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ServiceState(Enum):
    """Cross-platform service states"""
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"
    NOT_INSTALLED = "not_installed"


@dataclass
class ServiceStatus:
    """Cross-platform service status"""
    state: ServiceState
    name: str
    display_name: str
    instance_id: str = "default"
    pid: Optional[int] = None
    message: str = ""


class ServiceAdapter(ABC):
    """
    Abstract base class for platform-specific service adapters.
    
    Implementations:
    - WindowsNativeServiceAdapter: Uses pywin32 (visible in Task Manager)
    - WindowsNSSMAdapter: Uses NSSM wrapper
    - LinuxSystemdAdapter: Uses systemd
    - MacOSLaunchdAdapter: Uses launchd
    """
    
    @abstractmethod
    def install(
        self,
        instance_id: str = "default",
        startup: str = "auto",
        config_path: Optional[str] = None
    ) -> bool:
        """
        Install the service.
        
        Args:
            instance_id: Instance identifier
            startup: Startup type - "auto", "manual", "disabled"
            config_path: Path to configuration file
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def uninstall(self, instance_id: str = "default") -> bool:
        """
        Uninstall the service.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def start(self, instance_id: str = "default") -> bool:
        """Start the service"""
        pass
    
    @abstractmethod
    def stop(self, instance_id: str = "default") -> bool:
        """Stop the service"""
        pass
    
    @abstractmethod
    def restart(self, instance_id: str = "default") -> bool:
        """Restart the service"""
        pass
    
    @abstractmethod
    def get_status(self, instance_id: str = "default") -> ServiceStatus:
        """Get current service status"""
        pass
    
    @abstractmethod
    def is_installed(self, instance_id: str = "default") -> bool:
        """Check if service is installed"""
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name"""
        pass
    
    @property
    @abstractmethod
    def requires_admin(self) -> bool:
        """Whether this adapter requires admin privileges"""
        pass


# Platform-specific implementations

class WindowsNativeServiceAdapter(ServiceAdapter):
    """Windows Service using pywin32 - appears in Task Manager"""
    
    def __init__(self) -> None:
        # Lazy import to avoid loading pywin32 on non-Windows
        from .windows_native_service import (
            install_service, uninstall_service, start_service,
            stop_service, get_service_status, is_pywin32_available
        )
        if not is_pywin32_available():
            raise RuntimeError("pywin32 is required for native Windows service")
        self._install = install_service
        self._uninstall = uninstall_service
        self._start = start_service
        self._stop = stop_service
        self._get_status = get_service_status
    
    def install(self, instance_id="default", startup="auto", config_path=None) -> bool:
        return self._install(instance_id=instance_id, startup=startup)
    
    def uninstall(self, instance_id="default") -> bool:
        return self._uninstall(instance_id=instance_id)
    
    def start(self, instance_id="default") -> bool:
        return self._start(instance_id=instance_id)
    
    def stop(self, instance_id="default") -> bool:
        return self._stop(instance_id=instance_id)
    
    def restart(self, instance_id="default") -> bool:
        self.stop(instance_id)
        import time
        time.sleep(2)
        return self.start(instance_id)
    
    def get_status(self, instance_id="default") -> ServiceStatus:
        status_str = self._get_status(instance_id)
        state_map = {
            "Running": ServiceState.RUNNING,
            "Stopped": ServiceState.STOPPED,
            "Starting": ServiceState.STARTING,
            "Stopping": ServiceState.STOPPING,
            "Paused": ServiceState.PAUSED,
        }
        state = state_map.get(status_str, ServiceState.UNKNOWN)
        if status_str is None:
            state = ServiceState.NOT_INSTALLED
        
        from .windows_native_service import get_service_name
        name = get_service_name(instance_id)
        return ServiceStatus(
            state=state,
            name=name,
            display_name="pyWATS Client Service",
            instance_id=instance_id
        )
    
    def is_installed(self, instance_id="default") -> bool:
        return self._get_status(instance_id) is not None
    
    @property
    def platform_name(self) -> str:
        return "Windows (Native)"
    
    @property
    def requires_admin(self) -> bool:
        return True


class WindowsNSSMAdapter(ServiceAdapter):
    """Windows Service using NSSM wrapper"""
    
    def install(self, instance_id="default", startup="auto", config_path=None) -> bool:
        from .windows_service import WindowsServiceInstaller
        return WindowsServiceInstaller.install_with_nssm(
            instance_id=instance_id,
            config_path=config_path
        )
    
    def uninstall(self, instance_id="default") -> bool:
        from .windows_service import WindowsServiceInstaller
        return WindowsServiceInstaller.uninstall_with_nssm(instance_id)
    
    def start(self, instance_id="default") -> bool:
        import subprocess
        service_name = f"pyWATS_Service{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["net", "start", service_name], capture_output=True)
        return result.returncode == 0
    
    def stop(self, instance_id="default") -> bool:
        import subprocess
        service_name = f"pyWATS_Service{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["net", "stop", service_name], capture_output=True)
        return result.returncode == 0
    
    def restart(self, instance_id="default") -> bool:
        self.stop(instance_id)
        import time
        time.sleep(2)
        return self.start(instance_id)
    
    def get_status(self, instance_id="default") -> ServiceStatus:
        # Use sc query
        import subprocess
        service_name = f"pyWATS_Service{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return ServiceStatus(
                state=ServiceState.NOT_INSTALLED,
                name=service_name,
                display_name="pyWATS Client Service",
                instance_id=instance_id
            )
        
        # Parse state from output
        state = ServiceState.UNKNOWN
        if "RUNNING" in result.stdout:
            state = ServiceState.RUNNING
        elif "STOPPED" in result.stdout:
            state = ServiceState.STOPPED
        elif "START_PENDING" in result.stdout:
            state = ServiceState.STARTING
        elif "STOP_PENDING" in result.stdout:
            state = ServiceState.STOPPING
        elif "PAUSED" in result.stdout:
            state = ServiceState.PAUSED
        
        return ServiceStatus(
            state=state,
            name=service_name,
            display_name="pyWATS Client Service",
            instance_id=instance_id
        )
    
    def is_installed(self, instance_id="default") -> bool:
        status = self.get_status(instance_id)
        return status.state != ServiceState.NOT_INSTALLED
    
    @property
    def platform_name(self) -> str:
        return "Windows (NSSM)"
    
    @property
    def requires_admin(self) -> bool:
        return True


class LinuxSystemdAdapter(ServiceAdapter):
    """Linux Service using systemd"""
    
    def install(self, instance_id="default", startup="auto", config_path=None) -> bool:
        from .unix_service import LinuxServiceInstaller
        return LinuxServiceInstaller.install(
            instance_id=instance_id,
            config_path=config_path
        )
    
    def uninstall(self, instance_id="default") -> bool:
        from .unix_service import LinuxServiceInstaller
        return LinuxServiceInstaller.uninstall(instance_id)
    
    def start(self, instance_id="default") -> bool:
        import subprocess
        service_name = f"pywats-client{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["systemctl", "start", service_name], capture_output=True)
        return result.returncode == 0
    
    def stop(self, instance_id="default") -> bool:
        import subprocess
        service_name = f"pywats-client{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["systemctl", "stop", service_name], capture_output=True)
        return result.returncode == 0
    
    def restart(self, instance_id="default") -> bool:
        import subprocess
        service_name = f"pywats-client{'_' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["systemctl", "restart", service_name], capture_output=True)
        return result.returncode == 0
    
    def get_status(self, instance_id="default") -> ServiceStatus:
        import subprocess
        service_name = f"pywats-client{'_' + instance_id if instance_id != 'default' else ''}"
        
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True
        )
        
        state_map = {
            "active": ServiceState.RUNNING,
            "inactive": ServiceState.STOPPED,
            "activating": ServiceState.STARTING,
            "deactivating": ServiceState.STOPPING,
            "failed": ServiceState.STOPPED,
        }
        
        status_str = result.stdout.strip()
        state = state_map.get(status_str, ServiceState.UNKNOWN)
        
        # Check if installed
        check_result = subprocess.run(
            ["systemctl", "list-unit-files", service_name],
            capture_output=True, text=True
        )
        if service_name not in check_result.stdout:
            state = ServiceState.NOT_INSTALLED
        
        return ServiceStatus(
            state=state,
            name=service_name,
            display_name="pyWATS Client Service",
            instance_id=instance_id
        )
    
    def is_installed(self, instance_id="default") -> bool:
        status = self.get_status(instance_id)
        return status.state != ServiceState.NOT_INSTALLED
    
    @property
    def platform_name(self) -> str:
        return "Linux (systemd)"
    
    @property
    def requires_admin(self) -> bool:
        return True


class MacOSLaunchdAdapter(ServiceAdapter):
    """macOS Service using launchd"""
    
    def __init__(self, user_agent: bool = False) -> None:
        """
        Args:
            user_agent: If True, use LaunchAgent (user-level), else LaunchDaemon (system-level)
        """
        self.user_agent = user_agent
    
    def install(self, instance_id="default", startup="auto", config_path=None) -> bool:
        from .unix_service import MacOSServiceInstaller
        return MacOSServiceInstaller.install(
            instance_id=instance_id,
            config_path=config_path,
            user_agent=self.user_agent
        )
    
    def uninstall(self, instance_id="default") -> bool:
        from .unix_service import MacOSServiceInstaller
        return MacOSServiceInstaller.uninstall(
            instance_id=instance_id,
            user_agent=self.user_agent
        )
    
    def start(self, instance_id="default") -> bool:
        import subprocess
        plist_name = f"com.virinco.pywats-client{'.' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["launchctl", "start", plist_name], capture_output=True)
        return result.returncode == 0
    
    def stop(self, instance_id="default") -> bool:
        import subprocess
        plist_name = f"com.virinco.pywats-client{'.' + instance_id if instance_id != 'default' else ''}"
        result = subprocess.run(["launchctl", "stop", plist_name], capture_output=True)
        return result.returncode == 0
    
    def restart(self, instance_id="default") -> bool:
        self.stop(instance_id)
        import time
        time.sleep(1)
        return self.start(instance_id)
    
    def get_status(self, instance_id="default") -> ServiceStatus:
        import subprocess
        plist_name = f"com.virinco.pywats-client{'.' + instance_id if instance_id != 'default' else ''}"
        
        result = subprocess.run(
            ["launchctl", "list", plist_name],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return ServiceStatus(
                state=ServiceState.NOT_INSTALLED,
                name=plist_name,
                display_name="pyWATS Client Service",
                instance_id=instance_id
            )
        
        # Parse PID from output
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split('\t')
            pid_str = parts[0] if parts else "-"
            state = ServiceState.RUNNING if pid_str != "-" else ServiceState.STOPPED
            pid = int(pid_str) if pid_str != "-" else None
        else:
            state = ServiceState.UNKNOWN
            pid = None
        
        return ServiceStatus(
            state=state,
            name=plist_name,
            display_name="pyWATS Client Service",
            instance_id=instance_id,
            pid=pid
        )
    
    def is_installed(self, instance_id="default") -> bool:
        status = self.get_status(instance_id)
        return status.state != ServiceState.NOT_INSTALLED
    
    @property
    def platform_name(self) -> str:
        return f"macOS ({'LaunchAgent' if self.user_agent else 'LaunchDaemon'})"
    
    @property
    def requires_admin(self) -> bool:
        return not self.user_agent  # LaunchAgent doesn't need admin


def get_service_adapter(
    prefer_native: bool = True,
    user_level: bool = False
) -> ServiceAdapter:
    """
    Get the appropriate service adapter for the current platform.
    
    Args:
        prefer_native: On Windows, prefer native pywin32 over NSSM
        user_level: On macOS, use LaunchAgent instead of LaunchDaemon
        
    Returns:
        Platform-appropriate ServiceAdapter
        
    Raises:
        RuntimeError: If no suitable adapter available
    """
    if sys.platform == "win32":
        if prefer_native:
            try:
                return WindowsNativeServiceAdapter()
            except RuntimeError:
                # Fall back to NSSM if pywin32 not available
                pass
        return WindowsNSSMAdapter()
    
    elif sys.platform == "darwin":
        return MacOSLaunchdAdapter(user_agent=user_level)
    
    elif sys.platform.startswith("linux"):
        return LinuxSystemdAdapter()
    
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_available_adapters() -> list[tuple[str, type]]:
    """
    Get list of available adapters for the current platform.
    
    Returns:
        List of (name, adapter_class) tuples
    """
    adapters = []
    
    if sys.platform == "win32":
        # Check for pywin32
        try:
            from .windows_native_service import is_pywin32_available
            if is_pywin32_available():
                adapters.append(("native", WindowsNativeServiceAdapter))
        except ImportError:
            pass
        adapters.append(("nssm", WindowsNSSMAdapter))
    
    elif sys.platform == "darwin":
        adapters.append(("launchd", MacOSLaunchdAdapter))
    
    elif sys.platform.startswith("linux"):
        adapters.append(("systemd", LinuxSystemdAdapter))
    
    return adapters
