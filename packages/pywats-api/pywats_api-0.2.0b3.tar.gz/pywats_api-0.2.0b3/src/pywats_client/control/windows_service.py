"""
Windows Service Installation for pyWATS Client

Provides tools for installing pyWATS Client as a Windows Service using NSSM or sc.exe.
Service will auto-start on system boot.
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WindowsServiceInstaller:
    """
    Installs pyWATS Client as a Windows Service.
    
    Uses NSSM (Non-Sucking Service Manager) if available, otherwise falls back to sc.exe.
    """
    
    SERVICE_NAME = "pyWATS_Service"
    SERVICE_DISPLAY_NAME = "pyWATS Client Service"
    SERVICE_DESCRIPTION = "WATS Test Report Management Client - Background service for converter monitoring and report submission"
    
    @staticmethod
    def is_admin() -> bool:
        """Check if running with administrator privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def find_nssm() -> Optional[Path]:
        """Find NSSM executable"""
        # Check common locations
        common_paths = [
            Path("C:/Program Files/NSSM/nssm.exe"),
            Path("C:/Program Files (x86)/NSSM/nssm.exe"),
            Path.cwd() / "nssm.exe",
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        # Try to find via PATH
        try:
            result = subprocess.run(
                ["where", "nssm"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout:
                return Path(result.stdout.strip().split('\n')[0])
        except:
            pass
        
        return None
    
    @classmethod
    def install_with_nssm(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None,
        python_exe: Optional[str] = None
    ) -> bool:
        """
        Install service using NSSM.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            python_exe: Path to Python executable (auto-detected if None)
            
        Returns:
            True if installation successful
        """
        if not cls.is_admin():
            print("ERROR: Administrator privileges required")
            return False
        
        nssm_path = cls.find_nssm()
        if not nssm_path:
            print("ERROR: NSSM not found. Please install NSSM or use --use-sc option")
            print("Download from: https://nssm.cc/download")
            return False
        
        # Get Python executable
        if not python_exe:
            python_exe = sys.executable
        
        # Build service command
        service_args = [sys.executable, "-m", "pywats_client", "service"]
        
        if instance_id != "default":
            service_args.extend(["--instance-id", instance_id])
        
        if config_path:
            service_args.extend(["--config", config_path])
        
        # Service name
        service_name = cls.SERVICE_NAME
        if instance_id != "default":
            service_name = f"{cls.SERVICE_NAME}_{instance_id}"
        
        try:
            # Install service
            print(f"Installing service '{service_name}'...")
            subprocess.run(
                [str(nssm_path), "install", service_name] + service_args,
                check=True
            )
            
            # Set display name
            subprocess.run(
                [str(nssm_path), "set", service_name, "DisplayName", cls.SERVICE_DISPLAY_NAME],
                check=True
            )
            
            # Set description
            subprocess.run(
                [str(nssm_path), "set", service_name, "Description", cls.SERVICE_DESCRIPTION],
                check=True
            )
            
            # Set startup type to automatic
            subprocess.run(
                [str(nssm_path), "set", service_name, "Start", "SERVICE_AUTO_START"],
                check=True
            )
            
            # Set log files
            programdata = Path(sys.environ.get('PROGRAMDATA', 'C:\\ProgramData'))
            log_dir = programdata / 'Virinco' / 'pyWATS' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            subprocess.run(
                [str(nssm_path), "set", service_name, "AppStdout", str(log_dir / f"{service_name}.log")],
                check=True
            )
            subprocess.run(
                [str(nssm_path), "set", service_name, "AppStderr", str(log_dir / f"{service_name}_error.log")],
                check=True
            )
            
            print(f"✓ Service '{service_name}' installed successfully")
            print(f"  Display Name: {cls.SERVICE_DISPLAY_NAME}")
            print(f"  Instance ID: {instance_id}")
            print(f"  Logs: {log_dir}")
            print(f"\nTo start the service:")
            print(f"  net start {service_name}")
            print(f"  or: nssm start {service_name}")
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install service: {e}")
            return False
    
    @classmethod
    def uninstall_with_nssm(cls, instance_id: str = "default") -> bool:
        """
        Uninstall service using NSSM.
        
        Args:
            instance_id: Instance ID of the service
            
        Returns:
            True if uninstallation successful
        """
        if not cls.is_admin():
            print("ERROR: Administrator privileges required")
            return False
        
        nssm_path = cls.find_nssm()
        if not nssm_path:
            print("ERROR: NSSM not found")
            return False
        
        service_name = cls.SERVICE_NAME
        if instance_id != "default":
            service_name = f"{cls.SERVICE_NAME}_{instance_id}"
        
        try:
            # Stop service first
            print(f"Stopping service '{service_name}'...")
            subprocess.run(
                [str(nssm_path), "stop", service_name],
                check=False  # Don't fail if already stopped
            )
            
            # Remove service
            print(f"Removing service '{service_name}'...")
            subprocess.run(
                [str(nssm_path), "remove", service_name, "confirm"],
                check=True
            )
            
            print(f"✓ Service '{service_name}' removed successfully")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to remove service: {e}")
            return False
    
    @classmethod
    def install_with_sc(
        cls,
        instance_id: str = "default",
        config_path: Optional[str] = None
    ) -> bool:
        """
        Install service using sc.exe (Windows built-in).
        
        Note: This creates a simple service but requires more manual configuration.
        NSSM is recommended for better control.
        
        Args:
            instance_id: Instance ID for the service
            config_path: Path to config file
            
        Returns:
            True if installation successful
        """
        if not cls.is_admin():
            print("ERROR: Administrator privileges required")
            return False
        
        service_name = cls.SERVICE_NAME
        if instance_id != "default":
            service_name = f"{cls.SERVICE_NAME}_{instance_id}"
        
        # Build command
        bin_path = f'"{sys.executable}" -m pywats_client service'
        if instance_id != "default":
            bin_path += f' --instance-id {instance_id}'
        if config_path:
            bin_path += f' --config "{config_path}"'
        
        try:
            # Create service
            subprocess.run(
                [
                    "sc", "create", service_name,
                    f"binPath= {bin_path}",
                    f"DisplayName= {cls.SERVICE_DISPLAY_NAME}",
                    "start= auto"
                ],
                check=True
            )
            
            # Set description
            subprocess.run(
                ["sc", "description", service_name, cls.SERVICE_DESCRIPTION],
                check=True
            )
            
            print(f"✓ Service '{service_name}' created successfully")
            print(f"\nNote: sc.exe services may have limitations.")
            print("For best results, install NSSM from https://nssm.cc/download")
            print(f"\nTo start the service:")
            print(f"  net start {service_name}")
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create service: {e}")
            return False
    
    @classmethod
    def uninstall_with_sc(cls, instance_id: str = "default") -> bool:
        """
        Uninstall service using sc.exe.
        
        Args:
            instance_id: Instance ID of the service
            
        Returns:
            True if uninstallation successful
        """
        if not cls.is_admin():
            print("ERROR: Administrator privileges required")
            return False
        
        service_name = cls.SERVICE_NAME
        if instance_id != "default":
            service_name = f"{cls.SERVICE_NAME}_{instance_id}"
        
        try:
            # Stop service
            subprocess.run(
                ["sc", "stop", service_name],
                check=False
            )
            
            # Delete service
            subprocess.run(
                ["sc", "delete", service_name],
                check=True
            )
            
            print(f"✓ Service '{service_name}' deleted successfully")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to delete service: {e}")
            return False


def is_auto_start_enabled(instance_id: str = "default") -> bool:
    """
    Check if the service is set to auto-start on system boot.
    
    Args:
        instance_id: Instance ID of the service
        
    Returns:
        True if auto-start is enabled
    """
    service_name = WindowsServiceInstaller.SERVICE_NAME
    if instance_id != "default":
        service_name = f"{service_name}_{instance_id}"
    
    try:
        result = subprocess.run(
            ["sc", "qc", service_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            # Look for "START_TYPE" in output
            # AUTO_START (2) means auto-start is enabled
            return "AUTO_START" in result.stdout
    except Exception as e:
        logger.debug(f"Failed to check auto-start status: {e}")
    
    return False


def set_auto_start(enabled: bool, instance_id: str = "default") -> bool:
    """
    Enable or disable auto-start for the service.
    
    Args:
        enabled: True to enable auto-start, False to disable
        instance_id: Instance ID of the service
        
    Returns:
        True if the operation succeeded
    """
    if not WindowsServiceInstaller.is_admin():
        logger.warning("Administrator privileges required to change auto-start")
        return False
    
    service_name = WindowsServiceInstaller.SERVICE_NAME
    if instance_id != "default":
        service_name = f"{service_name}_{instance_id}"
    
    start_type = "auto" if enabled else "demand"
    
    try:
        result = subprocess.run(
            ["sc", "config", service_name, "start=", start_type],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info(f"Auto-start {'enabled' if enabled else 'disabled'} for {service_name}")
            return True
        else:
            logger.error(f"Failed to set auto-start: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to set auto-start: {e}")
        return False
