"""
Linux/macOS Service Installation for pyWATS Client

Provides tools for installing pyWATS Client as a system service:
- Linux: systemd service
- macOS: launchd daemon

Service will auto-start on system boot.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

from .exit_codes import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_MISSING_REQUIREMENTS,
    EXIT_ALREADY_INSTALLED,
    EXIT_NOT_INSTALLED,
    EXIT_PERMISSION_DENIED,
)

logger = logging.getLogger(__name__)


class LinuxServiceInstaller:
    """
    Installs pyWATS Client as a systemd service on Linux.
    
    Works with Ubuntu, Debian, RHEL, CentOS, Fedora, and other systemd-based distributions.
    
    Features:
    - Silent installation mode for automated deployment
    - Exit codes compatible with scripted deployments
    - Production-hardened systemd unit file
    - Watchdog integration for health monitoring
    """
    
    SERVICE_NAME = "pywats-service"
    SYSTEMD_DIR = Path("/etc/systemd/system")
    
    @staticmethod
    def is_root() -> bool:
        """Check if running as root"""
        return os.geteuid() == 0
    
    @staticmethod
    def has_systemd() -> bool:
        """Check if systemd is available"""
        return Path("/run/systemd/system").exists()
    
    @classmethod
    def _get_service_name(cls, instance_id: str = "default") -> str:
        """Get service name for an instance"""
        if instance_id == "default":
            return cls.SERVICE_NAME
        return f"{cls.SERVICE_NAME}@{instance_id}"
    
    @classmethod
    def _get_service_unit_file(cls, instance_id: str = "default") -> Path:
        """Get path to systemd unit file"""
        return cls.SYSTEMD_DIR / f"{cls._get_service_name(instance_id)}.service"
    
    @classmethod
    def is_service_installed(cls, instance_id: str = "default") -> bool:
        """
        Check if the service is already installed.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if service is installed
        """
        unit_file = cls._get_service_unit_file(instance_id)
        return unit_file.exists()
    
    @classmethod
    def get_service_status(cls, instance_id: str = "default") -> Optional[str]:
        """
        Get the current status of the service.
        
        Returns:
            Status string or None if service not found
        """
        if not cls.is_service_installed(instance_id):
            return None
        
        try:
            service_name = cls._get_service_name(instance_id)
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return None
    
    @classmethod
    def _create_systemd_unit(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None,
        python_exe: Optional[str] = None,
        user: Optional[str] = None
    ) -> str:
        """
        Create systemd unit file content.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            python_exe: Path to Python executable
            user: User to run service as (defaults to current user)
            
        Returns:
            Unit file content as string
        """
        if not python_exe:
            python_exe = sys.executable
        
        if not user:
            import pwd
            user = pwd.getpwuid(os.getuid()).pw_name
        
        # Build service command
        exec_start = f"{python_exe} -m pywats_client service"
        
        if instance_id != "default":
            exec_start += f" --instance-id {instance_id}"
        
        if config_path:
            exec_start += f' --config "{config_path}"'
        
        # Data directory
        if user == "root":
            working_dir = "/var/lib/pywats"
            state_dir = "/var/lib/pywats"
            log_dir = "/var/log/pywats"
            runtime_dir = "/run/pywats"
        else:
            home = Path.home()
            working_dir = str(home / ".config" / "pywats_client")
            state_dir = working_dir
            log_dir = state_dir
            runtime_dir = f"/run/user/{os.getuid()}/pywats"
        
        # Service description
        description = "pyWATS Client Service"
        if instance_id != "default":
            description = f"pyWATS Client Service ({instance_id})"
        
        # Production-hardened systemd unit file
        unit_content = f"""[Unit]
Description={description}
Documentation=https://github.com/olreppe/pyWATS
After=network-online.target
Wants=network-online.target

# Ordering for proper shutdown
Before=shutdown.target reboot.target

[Service]
Type=notify
User={user}
Group={user}
WorkingDirectory={working_dir}
ExecStart={exec_start}
ExecReload=/bin/kill -HUP $MAINPID

# Restart behavior (production hardened)
Restart=on-failure
RestartSec=5s
RestartPreventExitStatus=0

# Watchdog - service must call sd_notify(WATCHDOG=1) regularly
WatchdogSec=60s
WatchdogSignal=SIGKILL

# Resource limits (appropriate for factory floor systems)
LimitNOFILE=65535
LimitNPROC=4096
MemoryMax=512M
CPUQuota=80%

# Timeout settings
TimeoutStartSec=30s
TimeoutStopSec=30s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=pywats-client

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths={state_dir} {log_dir}
RuntimeDirectory=pywats
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictRealtime=true
LockPersonality=true

# Capability restrictions (only network needed)
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=

# System call filtering
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# Environment
Environment="PYTHONUNBUFFERED=1"
Environment="PYWATS_SERVICE=1"

[Install]
WantedBy=multi-user.target
"""
        return unit_content
    
    @classmethod
    def install(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None,
        python_exe: Optional[str] = None,
        user: Optional[str] = None,
        silent: bool = False
    ) -> int:
        """
        Install systemd service.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            python_exe: Path to Python executable
            user: User to run service as
            silent: Suppress output (for scripted deployments)
            
        Returns:
            Exit code (0=success, non-zero=error)
        """
        def _print(msg: str):
            if not silent:
                print(msg)
        
        # Check if already installed
        if cls.is_service_installed(instance_id):
            _print(f"Service already installed for instance '{instance_id}'")
            return EXIT_ALREADY_INSTALLED
        
        # Check root privileges
        if not cls.is_root():
            _print("ERROR: Root privileges required (use sudo)")
            return EXIT_PERMISSION_DENIED
        
        # Check systemd availability
        if not cls.has_systemd():
            _print("ERROR: systemd not found. This system may not use systemd.")
            _print("Please install pyWATS manually or use your system's init system.")
            return EXIT_MISSING_REQUIREMENTS
        
        # Create unit file
        unit_file = cls._get_service_unit_file(instance_id)
        unit_content = cls._create_systemd_unit(instance_id, config_path, python_exe, user)
        
        try:
            # Create working directory if needed
            if user:
                import pwd
                pw = pwd.getpwnam(user)
                if user == "root":
                    work_dir = Path("/var/lib/pywats")
                else:
                    work_dir = Path(pw.pw_dir) / ".config" / "pywats_client"
                
                if not work_dir.exists():
                    _print(f"Creating working directory: {work_dir}")
                    work_dir.mkdir(parents=True, exist_ok=True)
                    os.chown(work_dir, pw.pw_uid, pw.pw_gid)
            
            # Write unit file
            _print(f"Creating systemd unit file: {unit_file}")
            unit_file.write_text(unit_content)
            unit_file.chmod(0o644)
            
            # Reload systemd
            _print("Reloading systemd daemon...")
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            # Enable service
            service_name = cls._get_service_name(instance_id)
            _print(f"Enabling service '{service_name}'...")
            subprocess.run(["systemctl", "enable", service_name], check=True)
            
            _print(f"✓ Service '{service_name}' installed successfully")
            _print(f"  Unit file: {unit_file}")
            _print(f"  Instance ID: {instance_id}")
            _print(f"  User: {user or 'current user'}")
            _print(f"\nTo start the service:")
            _print(f"  sudo systemctl start {service_name}")
            _print(f"\nTo view logs:")
            _print(f"  sudo journalctl -u {service_name} -f")
            
            return EXIT_SUCCESS
        
        except subprocess.CalledProcessError as e:
            _print(f"ERROR: Command failed: {e}")
            return EXIT_ERROR
        except PermissionError as e:
            _print(f"ERROR: Permission denied: {e}")
            return EXIT_PERMISSION_DENIED
        except Exception as e:
            _print(f"ERROR: Failed to install service: {e}")
            return EXIT_ERROR
    
    @classmethod
    def uninstall(cls, instance_id: str = "default", silent: bool = False) -> int:
        """
        Uninstall systemd service.
        
        Args:
            instance_id: Instance ID of the service
            silent: Suppress output (for scripted deployments)
            
        Returns:
            Exit code (0=success, non-zero=error)
        """
        def _print(msg: str):
            if not silent:
                print(msg)
        
        # Check if service exists
        if not cls.is_service_installed(instance_id):
            _print(f"Service not installed for instance '{instance_id}'")
            return EXIT_NOT_INSTALLED
        
        # Check root privileges
        if not cls.is_root():
            _print("ERROR: Root privileges required (use sudo)")
            return EXIT_PERMISSION_DENIED
        
        unit_file = cls._get_service_unit_file(instance_id)
        service_name = cls._get_service_name(instance_id)
        
        try:
            # Stop service
            _print(f"Stopping service '{service_name}'...")
            subprocess.run(["systemctl", "stop", service_name], check=False)
            
            # Disable service
            _print(f"Disabling service '{service_name}'...")
            subprocess.run(["systemctl", "disable", service_name], check=False)
            
            # Remove unit file
            if unit_file.exists():
                _print(f"Removing unit file: {unit_file}")
                unit_file.unlink()
            
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "reset-failed"], check=False)
            
            _print(f"✓ Service '{service_name}' removed successfully")
            return EXIT_SUCCESS
        
        except PermissionError as e:
            _print(f"ERROR: Permission denied: {e}")
            return EXIT_PERMISSION_DENIED
        except Exception as e:
            _print(f"ERROR: Failed to remove service: {e}")
            return EXIT_ERROR


class MacOSServiceInstaller:
    """
    Installs pyWATS Client as a launchd daemon on macOS.
    
    Creates a Launch Daemon (runs at boot) or Launch Agent (runs at login).
    
    Features:
    - Silent installation mode for automated deployment
    - Exit codes compatible with scripted deployments
    - Auto-restart on failure via KeepAlive
    """
    
    SERVICE_LABEL = "com.virinco.pywats.service"
    LAUNCH_DAEMONS_DIR = Path("/Library/LaunchDaemons")
    LAUNCH_AGENTS_DIR = Path("/Library/LaunchAgents")
    
    @staticmethod
    def is_root() -> bool:
        """Check if running as root"""
        return os.geteuid() == 0
    
    @classmethod
    def _get_label(cls, instance_id: str = "default") -> str:
        """Get service label for an instance"""
        if instance_id == "default":
            return cls.SERVICE_LABEL
        return f"{cls.SERVICE_LABEL}.{instance_id}"
    
    @classmethod
    def _get_plist_path(cls, instance_id: str = "default", user_agent: bool = False) -> Path:
        """Get path to launchd plist file"""
        base_dir = cls.LAUNCH_AGENTS_DIR if user_agent else cls.LAUNCH_DAEMONS_DIR
        label = cls._get_label(instance_id)
        return base_dir / f"{label}.plist"
    
    @classmethod
    def is_service_installed(cls, instance_id: str = "default", user_agent: bool = False) -> bool:
        """
        Check if the service is already installed.
        
        Args:
            instance_id: Instance identifier
            user_agent: Check Launch Agent instead of Daemon
            
        Returns:
            True if service is installed
        """
        plist_path = cls._get_plist_path(instance_id, user_agent)
        return plist_path.exists()
    
    @classmethod
    def get_service_status(cls, instance_id: str = "default") -> Optional[str]:
        """
        Get the current status of the service.
        
        Returns:
            Status string or None if service not found
        """
        label = cls._get_label(instance_id)
        try:
            result = subprocess.run(
                ["launchctl", "list", label],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "running"
            return "stopped"
        except Exception:
            return None
    
    @classmethod
    def _create_plist_content(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None,
        python_exe: Optional[str] = None,
        user_agent: bool = False
    ) -> str:
        """
        Create launchd plist file content.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            python_exe: Path to Python executable
            user_agent: If True, create Launch Agent instead of Daemon
            
        Returns:
            Plist file content as string
        """
        if not python_exe:
            python_exe = sys.executable
        
        # Build command arguments
        args = [python_exe, "-m", "pywats_client", "service"]
        
        if instance_id != "default":
            args.extend(["--instance-id", instance_id])
        
        if config_path:
            args.extend(["--config", config_path])
        
        # Label
        label = cls._get_label(instance_id)
        
        # Working directory and log paths
        if user_agent:
            home = Path.home()
            working_dir = str(home / ".config" / "pywats_client")
            log_dir = str(home / "Library" / "Logs" / "pyWATS")
        else:
            working_dir = "/var/lib/pywats"
            log_dir = "/var/log/pywats"
        
        # Create log directory
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        stdout_log = f"{log_dir}/pywats-service.log"
        stderr_log = f"{log_dir}/pywats-service-error.log"
        
        # Format arguments for plist
        args_xml = "\n".join(f"        <string>{arg}</string>" for arg in args)
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
"""
        return plist_content
    
    @classmethod
    def install(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None,
        python_exe: Optional[str] = None,
        user_agent: bool = False,
        silent: bool = False
    ) -> int:
        """
        Install launchd service.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            python_exe: Path to Python executable
            user_agent: If True, install as Launch Agent (user-level)
            silent: Suppress output (for scripted deployments)
            
        Returns:
            Exit code (0=success, non-zero=error)
        """
        def _print(msg: str):
            if not silent:
                print(msg)
        
        # Check if already installed
        if cls.is_service_installed(instance_id, user_agent):
            _print(f"Service already installed for instance '{instance_id}'")
            return EXIT_ALREADY_INSTALLED
        
        # Check root privileges for system daemon
        if not user_agent and not cls.is_root():
            _print("ERROR: Root privileges required for system daemon (use sudo)")
            _print("Or use --user-agent to install as user-level Launch Agent")
            return EXIT_PERMISSION_DENIED
        
        # Create plist file
        plist_path = cls._get_plist_path(instance_id, user_agent)
        plist_content = cls._create_plist_content(instance_id, config_path, python_exe, user_agent)
        
        try:
            # Create parent directory if needed
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write plist file
            _print(f"Creating launchd plist: {plist_path}")
            plist_path.write_text(plist_content)
            plist_path.chmod(0o644)
            
            # Load service
            label = cls._get_label(instance_id)
            
            _print(f"Loading service '{label}'...")
            subprocess.run(["launchctl", "load", str(plist_path)], check=True)
            
            service_type = "Launch Agent" if user_agent else "Launch Daemon"
            _print(f"✓ {service_type} '{label}' installed successfully")
            _print(f"  Plist: {plist_path}")
            _print(f"  Instance ID: {instance_id}")
            _print(f"\nTo start the service:")
            _print(f"  sudo launchctl start {label}")
            _print(f"\nTo view logs:")
            if user_agent:
                _print(f"  tail -f ~/Library/Logs/pyWATS/pywats-service.log")
            else:
                _print(f"  sudo tail -f /var/log/pywats/pywats-service.log")
            
            return EXIT_SUCCESS
        
        except subprocess.CalledProcessError as e:
            _print(f"ERROR: Command failed: {e}")
            return EXIT_ERROR
        except PermissionError as e:
            _print(f"ERROR: Permission denied: {e}")
            return EXIT_PERMISSION_DENIED
        except Exception as e:
            _print(f"ERROR: Failed to install service: {e}")
            return EXIT_ERROR
    
    @classmethod
    def uninstall(cls, instance_id: str = "default", user_agent: bool = False, silent: bool = False) -> int:
        """
        Uninstall launchd service.
        
        Args:
            instance_id: Instance ID of the service
            user_agent: If True, uninstall Launch Agent
            silent: Suppress output (for scripted deployments)
            
        Returns:
            Exit code (0=success, non-zero=error)
        """
        def _print(msg: str):
            if not silent:
                print(msg)
        
        # Check if service exists
        if not cls.is_service_installed(instance_id, user_agent):
            _print(f"Service not installed for instance '{instance_id}'")
            return EXIT_NOT_INSTALLED
        
        # Check root privileges for system daemon
        if not user_agent and not cls.is_root():
            _print("ERROR: Root privileges required (use sudo)")
            return EXIT_PERMISSION_DENIED
        
        plist_path = cls._get_plist_path(instance_id, user_agent)
        label = cls._get_label(instance_id)
        
        try:
            # Unload service
            _print(f"Unloading service '{label}'...")
            subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
            
            # Remove plist file
            if plist_path.exists():
                _print(f"Removing plist: {plist_path}")
                plist_path.unlink()
            
            _print(f"✓ Service '{label}' removed successfully")
            return EXIT_SUCCESS
        
        except PermissionError as e:
            _print(f"ERROR: Permission denied: {e}")
            return EXIT_PERMISSION_DENIED
        except Exception as e:
            _print(f"ERROR: Failed to remove service: {e}")
            return EXIT_ERROR
