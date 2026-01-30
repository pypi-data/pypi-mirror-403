"""
pyWATS Client Entry Point

Simplified usage (single test station - recommended):
    python -m pywats_client                 # Start service (background)
    python -m pywats_client gui             # Open configuration GUI

Service management:
    pywats-client install-service           # Install as Windows Service
    pywats-client install-service --native  # Install as native Windows Service (visible in Task Manager)
    pywats-client uninstall-service         # Remove Windows Service
    pywats-client status                    # Show service status

Advanced (multi-station simulation):
    pywats-client service --instance-id station1
    pywats-client gui --instance-id station1

Note: Multi-instance mode is for advanced use cases only (testing, development).
Most users should use the default single-instance mode.
"""

import sys
import asyncio
import argparse
import os
from pathlib import Path
from typing import Optional


# Import exit codes
from .control.exit_codes import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_MISSING_REQUIREMENTS,
    EXIT_ALREADY_INSTALLED,
    EXIT_NOT_INSTALLED,
    EXIT_INSTALL_FAILED,
    EXIT_UNINSTALL_FAILED,
    EXIT_PERMISSION_DENIED,
    EXIT_CONFIG_ERROR,
    EXIT_SERVER_UNREACHABLE,
)


# Global silent mode flag (suppresses output when True)
_silent_mode = False


def _set_silent_mode(silent: bool) -> None:
    """Set global silent mode flag"""
    global _silent_mode
    _silent_mode = silent


def _print(msg: str) -> None:
    """Print message unless in silent mode"""
    if not _silent_mode:
        print(msg)


def _check_gui_available() -> bool:
    """Check if Qt GUI is available"""
    try:
        import PySide6
        return True
    except ImportError:
        return False


def _check_admin_privileges() -> bool:
    """Check if running with admin/root privileges"""
    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def _check_python_version() -> bool:
    """Check if Python version meets requirements (>=3.10)"""
    return sys.version_info >= (3, 10)


def _check_server_connectivity(server_url: str, timeout: float = 5.0) -> bool:
    """
    Check if WATS server is reachable.
    
    Args:
        server_url: URL of the WATS server
        timeout: Connection timeout in seconds
        
    Returns:
        True if server is reachable
    """
    try:
        import httpx
        # Just check if we can connect, don't need valid response
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{server_url.rstrip('/')}/api/health")
            return response.status_code < 500
    except Exception:
        # Try basic connection
        try:
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(server_url)
            host = parsed.hostname or server_url
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            return True
        except Exception:
            return False


def _run_preflight_checks(
    require_admin: bool = True,
    check_server: Optional[str] = None,
    require_pywin32: bool = False,
) -> int:
    """
    Run pre-flight checks before installation.
    
    Args:
        require_admin: Whether admin privileges are required
        check_server: Server URL to check connectivity (None to skip)
        require_pywin32: Whether pywin32 is required
        
    Returns:
        EXIT_SUCCESS if all checks pass, otherwise appropriate error code
    """
    # Check Python version
    if not _check_python_version():
        _print(f"ERROR: Python 3.10 or later required (found {sys.version_info.major}.{sys.version_info.minor})")
        return EXIT_MISSING_REQUIREMENTS
    
    # Check admin privileges
    if require_admin and not _check_admin_privileges():
        _print("ERROR: Administrator privileges required")
        if sys.platform == "win32":
            _print("Run from an elevated command prompt (Run as Administrator)")
        else:
            _print("Run with sudo")
        return EXIT_PERMISSION_DENIED
    
    # Check pywin32 if required
    if require_pywin32:
        try:
            import win32serviceutil
        except ImportError:
            _print("ERROR: pywin32 is required for native Windows service")
            _print("Install with: pip install pywin32")
            return EXIT_MISSING_REQUIREMENTS
    
    # Check server connectivity if requested
    if check_server:
        _print(f"Checking connectivity to {check_server}...")
        if not _check_server_connectivity(check_server):
            _print(f"WARNING: Cannot reach server at {check_server}")
            _print("Service will be installed but may not work until server is reachable")
            # Don't fail on this - just warn (server might be on VPN, etc.)
    
    return EXIT_SUCCESS


def _run_gui_mode(config):
    """Run in GUI mode"""
    if not _check_gui_available():
        print("Error: GUI mode requires PySide6")
        print("Install with: pip install pywats-api[client]")
        print("Or run in headless mode: pywats-client --no-gui")
        sys.exit(1)
    
    from .gui.app import run_gui
    run_gui(config)


def _run_service_mode(instance_id: str = "default"):
    """
    Run in service mode (background process).
    
    This is the recommended way to run pyWATS Client.
    Service runs independently and can be controlled via IPC from GUI.
    """
    from .service.client_service import ClientService
    
    print(f"Starting pyWATS Client Service [instance: {instance_id}]")
    service = ClientService(instance_id)
    
    try:
        service.start()  # Blocks until stopped
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        service.stop()


def _run_headless_mode(config):
    """Run in simple headless mode (deprecated - redirects to service mode)"""
    print("Note: Headless mode now uses service mode.")
    print()
    
    from .service.client_service import ClientService
    
    # Use default instance
    service = ClientService("default")
    
    try:
        service.start()  # Blocks until stopped
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        service.stop()


def main():
    """Main entry point"""
    # Check if this is a CLI subcommand or service mode
    # CLI commands: config, status, test-connection, converters, service, gui, tray
    cli_commands = ["config", "status", "test-connection", "converters", "service", "gui", "tray"]
    
    # Handle 'service' command - run background service
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        parser = argparse.ArgumentParser(
            prog="pywats-client service",
            description="Run pyWATS Client as background service"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            default="default",
            help="Instance ID for multi-station mode (default: default, hidden for normal use)"
        )
        args = parser.parse_args(sys.argv[2:])
        
        # Only show instance ID if not default
        if args.instance_id != "default":
            print(f"Starting pyWATS Client Service [multi-station instance: {args.instance_id}]")
        else:
            print("Starting pyWATS Client Service...")
        
        _run_service_mode(args.instance_id)
        return
    
    # Handle 'gui' command - run GUI only (connects to service)
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        parser = argparse.ArgumentParser(
            prog="pywats-client gui",
            description="Run pyWATS Client GUI (Configurator)"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            default="default",
            help="Instance ID for multi-station mode (default: default)"
        )
        args = parser.parse_args(sys.argv[2:])
        
        if not _check_gui_available():
            print("Error: GUI mode requires PySide6")
            print("Install with: pip install pywats-api[client]")
            sys.exit(1)
        
        from .gui.app import run_gui
        from .core.config import get_default_config_path, ClientConfig
        
        # Load config for instance
        config_path = get_default_config_path(args.instance_id)
        config = ClientConfig.load_or_create(config_path)
        
        run_gui(config, instance_id=args.instance_id)
        return
    
    # Handle 'tray' command - run system tray icon
    if len(sys.argv) > 1 and sys.argv[1] == "tray":
        parser = argparse.ArgumentParser(
            prog="pywats-client tray",
            description="Run pyWATS Client system tray icon"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            default="default",
            help="Instance ID to connect to (default: default)"
        )
        args = parser.parse_args(sys.argv[2:])
        
        if not _check_gui_available():
            print("Error: Tray icon requires PySide6")
            print("Install with: pip install pywats-api[client]")
            sys.exit(1)
        
        from .service.service_tray import main as tray_main
        sys.exit(tray_main(args.instance_id))
    
    # Handle Service installation commands (Windows/Linux/macOS)
    if len(sys.argv) > 1 and sys.argv[1] == "install-service":
        if sys.platform == "win32":
            installer_type = "windows"
        elif sys.platform == "darwin":
            from .control.unix_service import MacOSServiceInstaller as ServiceInstaller
            installer_type = "macos"
        elif sys.platform.startswith("linux"):
            from .control.unix_service import LinuxServiceInstaller as ServiceInstaller
            installer_type = "linux"
        else:
            print(f"ERROR: Unsupported platform: {sys.platform}")
            sys.exit(EXIT_ERROR)
        
        parser = argparse.ArgumentParser(
            prog="pywats-client install-service",
            description="Install pyWATS Client as a system service"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            default="default",
            help="Instance ID for the service (default: default)"
        )
        parser.add_argument(
            "--config",
            type=str,
            help="Path to configuration file"
        )
        
        # Silent installation flags (for IT deployment scripts)
        parser.add_argument(
            "--silent", "-s",
            action="store_true",
            help="Silent mode - no prompts or output (for scripted deployment)"
        )
        parser.add_argument(
            "--server-url",
            type=str,
            help="WATS server URL for initial configuration (silent install)"
        )
        parser.add_argument(
            "--api-token",
            type=str,
            help="API token for authentication (silent install)"
        )
        parser.add_argument(
            "--watch-folder",
            type=str,
            help="Folder to watch for test reports (silent install)"
        )
        parser.add_argument(
            "--skip-preflight",
            action="store_true",
            help="Skip pre-flight validation checks"
        )
        
        if installer_type == "windows":
            parser.add_argument(
                "--native",
                action="store_true",
                help="Use native Windows Service (requires pywin32, appears in Task Manager)"
            )
            parser.add_argument(
                "--use-nssm",
                action="store_true",
                help="Use NSSM wrapper (default if --native not specified)"
            )
            parser.add_argument(
                "--use-sc",
                action="store_true",
                help="Use sc.exe instead of NSSM (not recommended)"
            )
        elif installer_type == "linux":
            parser.add_argument(
                "--user",
                type=str,
                help="User to run service as (default: current user)"
            )
        elif installer_type == "macos":
            parser.add_argument(
                "--user-agent",
                action="store_true",
                help="Install as Launch Agent instead of Daemon (no root required)"
            )
        
        args = parser.parse_args(sys.argv[2:])
        
        # Enable silent mode if requested
        if args.silent:
            _set_silent_mode(True)
        
        # Run pre-flight checks unless skipped
        if not args.skip_preflight:
            require_admin = installer_type != "macos" or not getattr(args, 'user_agent', False)
            preflight_result = _run_preflight_checks(
                require_admin=require_admin,
                check_server=args.server_url,
                require_pywin32=(installer_type == "windows" and getattr(args, 'native', False)),
            )
            if preflight_result != EXIT_SUCCESS:
                sys.exit(preflight_result)
        
        # Create initial configuration if silent install with config options
        if args.server_url or args.api_token or args.watch_folder:
            from .core.config import ClientConfig, get_default_config_path
            
            config_path = Path(args.config) if args.config else get_default_config_path(args.instance_id)
            
            # Load existing or create new config
            if config_path.exists():
                config = ClientConfig.load_or_create(config_path)
            else:
                config = ClientConfig()
            
            # Apply silent install overrides
            if args.server_url:
                config.service_address = args.server_url
            if args.api_token:
                config.api_token = args.api_token
            if args.watch_folder:
                config.watch_folders = [args.watch_folder]
            
            # Save configuration
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config.save(config_path)
            _print(f"Configuration saved to: {config_path}")
        
        # Perform installation
        if installer_type == "windows":
            if getattr(args, 'native', False):
                # Native Windows Service using pywin32
                from .control.windows_native_service import install_service, is_pywin32_available, is_service_installed
                if not is_pywin32_available():
                    _print("ERROR: Native Windows service requires pywin32")
                    _print("Install with: pip install pywin32")
                    sys.exit(EXIT_MISSING_REQUIREMENTS)
                
                # Check if already installed
                if is_service_installed(args.instance_id):
                    _print(f"ERROR: Service already installed (instance: {args.instance_id})")
                    _print("Use 'uninstall-service' first to remove the existing service")
                    sys.exit(EXIT_ALREADY_INSTALLED)
                
                success = install_service(instance_id=args.instance_id, silent=args.silent)
            elif args.use_sc:
                from .control.windows_service import WindowsServiceInstaller
                success = WindowsServiceInstaller.install_with_sc(
                    instance_id=args.instance_id,
                    config_path=args.config
                )
            else:
                # Default: NSSM wrapper
                from .control.windows_service import WindowsServiceInstaller
                success = WindowsServiceInstaller.install_with_nssm(
                    instance_id=args.instance_id,
                    config_path=args.config
                )
        elif installer_type == "linux":
            exit_code = ServiceInstaller.install(
                instance_id=args.instance_id,
                config_path=args.config,
                user=getattr(args, 'user', None),
                silent=args.silent
            )
            # install() now returns exit code, not bool
            sys.exit(exit_code)
        elif installer_type == "macos":
            exit_code = ServiceInstaller.install(
                instance_id=args.instance_id,
                config_path=args.config,
                user_agent=getattr(args, 'user_agent', False),
                silent=args.silent
            )
            # install() now returns exit code, not bool
            sys.exit(exit_code)
        
        if success:
            _print("Service installed successfully")
            sys.exit(EXIT_SUCCESS)
        else:
            _print("Service installation failed")
            sys.exit(EXIT_INSTALL_FAILED)
    
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall-service":
        if sys.platform == "win32":
            installer_type = "windows"
        elif sys.platform == "darwin":
            from .control.unix_service import MacOSServiceInstaller as ServiceInstaller
            installer_type = "macos"
        elif sys.platform.startswith("linux"):
            from .control.unix_service import LinuxServiceInstaller as ServiceInstaller
            installer_type = "linux"
        else:
            print(f"ERROR: Unsupported platform: {sys.platform}")
            sys.exit(EXIT_ERROR)
        
        parser = argparse.ArgumentParser(
            prog="pywats-client uninstall-service",
            description="Uninstall pyWATS Client system service"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            default="default",
            help="Instance ID of the service to remove (default: default)"
        )
        parser.add_argument(
            "--silent", "-s",
            action="store_true",
            help="Silent mode - no prompts or output (for scripted deployment)"
        )
        
        if installer_type == "windows":
            parser.add_argument(
                "--native",
                action="store_true",
                help="Remove native Windows Service (installed with --native)"
            )
            parser.add_argument(
                "--use-sc",
                action="store_true",
                help="Use sc.exe instead of NSSM (not recommended)"
            )
        elif installer_type == "macos":
            parser.add_argument(
                "--user-agent",
                action="store_true",
                help="Uninstall Launch Agent instead of Daemon"
            )
        
        args = parser.parse_args(sys.argv[2:])
        
        # Enable silent mode if requested
        if args.silent:
            _set_silent_mode(True)
        
        if installer_type == "windows":
            if getattr(args, 'native', False):
                from .control.windows_native_service import uninstall_service, is_service_installed
                
                # Check if service exists before trying to uninstall
                if not is_service_installed(args.instance_id):
                    _print(f"ERROR: Service not installed (instance: {args.instance_id})")
                    sys.exit(EXIT_NOT_INSTALLED)
                
                success = uninstall_service(instance_id=args.instance_id, silent=args.silent)
            elif args.use_sc:
                from .control.windows_service import WindowsServiceInstaller
                success = WindowsServiceInstaller.uninstall_with_sc(
                    instance_id=args.instance_id
                )
            else:
                from .control.windows_service import WindowsServiceInstaller
                success = WindowsServiceInstaller.uninstall_with_nssm(
                    instance_id=args.instance_id
                )
        elif installer_type == "linux":
            exit_code = ServiceInstaller.uninstall(
                instance_id=args.instance_id,
                silent=args.silent
            )
            # uninstall() now returns exit code, not bool
            sys.exit(exit_code)
        elif installer_type == "macos":
            exit_code = ServiceInstaller.uninstall(
                instance_id=args.instance_id,
                user_agent=getattr(args, 'user_agent', False),
                silent=args.silent
            )
            # uninstall() now returns exit code, not bool
            sys.exit(exit_code)
        
        if success:
            _print("Service uninstalled successfully")
            sys.exit(EXIT_SUCCESS)
        else:
            _print("Service uninstall failed")
            sys.exit(EXIT_UNINSTALL_FAILED)
    
    # Handle 'service' subcommand separately (runs headless service)
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        from .control.service import HeadlessService, ServiceConfig
        from .core.config import ClientConfig
        
        # Parse service-specific arguments
        parser = argparse.ArgumentParser(
            prog="pywats-client service",
            description="Run pyWATS Client in service mode (background daemon)"
        )
        parser.add_argument(
            "--config", "-c",
            type=str,
            help="Path to configuration file"
        )
        parser.add_argument(
            "--instance-id",
            type=str,
            help="Instance ID for multi-station mode"
        )
        parser.add_argument(
            "--daemon", "-d",
            action="store_true",
            help="Run as daemon (Unix only)"
        )
        parser.add_argument(
            "--api",
            action="store_true",
            help="Enable HTTP control API"
        )
        parser.add_argument(
            "--api-port",
            type=int,
            default=8765,
            help="HTTP API port (default: 8765)"
        )
        parser.add_argument(
            "--api-host",
            default="127.0.0.1",
            help="HTTP API host (default: 127.0.0.1)"
        )
        
        args = parser.parse_args(sys.argv[2:])  # Skip 'service' subcommand
        
        # Load config
        if args.config:
            config_path = Path(args.config)
            config = ClientConfig.load_or_create(config_path)
        else:
            config_dir = Path.home() / ".pywats_client"
            if args.instance_id:
                config_path = config_dir / f"config_{args.instance_id}.json"
            else:
                config_path = config_dir / "config.json"
            config = ClientConfig.load_or_create(config_path)
        
        # Apply instance ID override
        if args.instance_id:
            config.instance_id = args.instance_id
        
        # Create service config
        service_config = ServiceConfig(
            enable_api=args.api,
            api_host=args.api_host,
            api_port=args.api_port,
            daemon=args.daemon
        )
        
        # Run service
        print(f"Starting pyWATS Client Service (instance: {config.instance_id})")
        service = HeadlessService(config, service_config)
        service.run()
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        # Route to CLI handler
        from .control.cli import cli_main
        sys.exit(cli_main())
    
    # Legacy argument parsing for backward compatibility
    parser = argparse.ArgumentParser(
        description="pyWATS Client - WATS Test Report Management",
        epilog="""
CLI Commands (use 'pywats-client <command> --help' for details):
  service      Run in service mode (background daemon)
  config       Configuration management
  status       Show service status
  start        Start the service (with --daemon or --api options)
  stop         Stop a running daemon
  converters   Converter management
"""
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in headless mode without GUI"
    )
    parser.add_argument(
        "--instance-name",
        type=str,
        help="Instance name for this client"
    )
    parser.add_argument(
        "--service-address",
        type=str,
        help="WATS service address"
    )
    parser.add_argument(
        "--api-token",
        type=str,
        help="API token for authentication"
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit"
    )
    # New headless service options
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run as daemon (implies --no-gui)"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Enable HTTP control API (implies --no-gui)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8765,
        help="HTTP API port (default: 8765)"
    )
    parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="HTTP API host (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        from . import __version__
        print(f"pyWATS Client v{__version__}")
        sys.exit(0)
    
    # Load or create configuration
    from .core.config import ClientConfig
    
    if args.config:
        config_path = Path(args.config)
        config = ClientConfig.load_or_create(config_path)
    else:
        # Use default config location
        config_dir = Path.home() / ".pywats_client"
        config_path = config_dir / "config.json"
        config = ClientConfig.load_or_create(config_path)
    
    # Apply command line overrides
    if args.instance_name:
        config.instance_name = args.instance_name
    if args.service_address:
        config.service_address = args.service_address
    if args.api_token:
        config.api_token = args.api_token
    
    # Determine run mode
    # Default is service mode (not GUI) since GUI is just for configuration
    use_gui = not args.no_gui and not args.daemon and not args.api
    
    if use_gui:
        # Explicit GUI mode requested
        print("Note: Starting in GUI mode for configuration.")
        print("For background service, run: python -m pywats_client service")
        print()
        _run_gui_mode(config)
    elif args.daemon or args.api:
        # Full headless service with API support
        from .control.service import HeadlessService, ServiceConfig
        
        service_config = ServiceConfig(
            enable_api=args.api,
            api_host=args.api_host,
            api_port=args.api_port,
            daemon=args.daemon,
        )
        
        service = HeadlessService(config, service_config)
        service.run()
    else:
        # Default: Run service mode (single instance)
        # No need to mention instance_id for default case
        print("Starting pyWATS Client Service...")
        print("To configure, launch GUI: python -m pywats_client gui")
        print()
        _run_service_mode("default")


if __name__ == "__main__":
    main()
