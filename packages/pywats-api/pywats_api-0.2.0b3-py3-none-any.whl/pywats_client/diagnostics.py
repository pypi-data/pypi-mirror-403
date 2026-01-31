"""
System Diagnostics Module for pyWATS Client

Provides comprehensive pre-flight checks and system diagnostics to help
identify installation and configuration issues before they cause problems.

Usage:
    python -m pywats_client diagnose
    python -m pywats_client diagnose --json
    python -m pywats_client diagnose --fix
"""

import sys
import os
import platform
import json
import socket
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class CheckStatus(Enum):
    """Status of a diagnostic check"""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Result of a single diagnostic check"""
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_hint: Optional[str] = None
    fix_command: Optional[str] = None


@dataclass
class DiagnosticsReport:
    """Complete diagnostics report"""
    timestamp: str
    platform: str
    python_version: str
    pywats_version: str
    overall_status: CheckStatus
    checks: List[CheckResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['overall_status'] = self.overall_status.value
        result['checks'] = [
            {**asdict(c), 'status': c.status.value}
            for c in self.checks
        ]
        return result


class SystemDiagnostics:
    """
    Comprehensive system diagnostics for pyWATS Client.
    
    Checks:
    - Python version compatibility
    - Required packages installed
    - Optional packages (Qt, pywin32)
    - Network connectivity
    - WATS server reachability
    - File system permissions
    - Service manager availability
    - SELinux status (Linux)
    - Firewall status
    """
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        config_dir: Optional[Path] = None,
        verbose: bool = False
    ):
        self.server_url = server_url or os.environ.get('PYWATS_SERVER_URL')
        self.config_dir = config_dir or Path.home() / ".pywats_client"
        self.verbose = verbose
        self.checks: List[CheckResult] = []
    
    def run_all_checks(self) -> DiagnosticsReport:
        """Run all diagnostic checks and return report"""
        from datetime import datetime
        
        self.checks = []
        
        # Core checks
        self._check_python_version()
        self._check_required_packages()
        self._check_optional_packages()
        
        # File system checks
        self._check_config_directory()
        self._check_log_directory()
        
        # Network checks
        self._check_network_connectivity()
        self._check_wats_server()
        
        # Platform-specific checks
        if sys.platform == 'win32':
            self._check_windows_service()
            self._check_windows_firewall()
        elif sys.platform == 'linux':
            self._check_systemd()
            self._check_selinux()
        elif sys.platform == 'darwin':
            self._check_launchd()
        
        # Determine overall status
        statuses = [c.status for c in self.checks]
        if CheckStatus.FAIL in statuses:
            overall = CheckStatus.FAIL
        elif CheckStatus.WARN in statuses:
            overall = CheckStatus.WARN
        else:
            overall = CheckStatus.PASS
        
        # Get pyWATS version
        try:
            from pywats import __version__ as pywats_version
        except ImportError:
            pywats_version = "not installed"
        
        return DiagnosticsReport(
            timestamp=datetime.now().isoformat(),
            platform=f"{platform.system()} {platform.release()}",
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            pywats_version=pywats_version,
            overall_status=overall,
            checks=self.checks,
            summary={
                'pass': sum(1 for c in self.checks if c.status == CheckStatus.PASS),
                'warn': sum(1 for c in self.checks if c.status == CheckStatus.WARN),
                'fail': sum(1 for c in self.checks if c.status == CheckStatus.FAIL),
                'skip': sum(1 for c in self.checks if c.status == CheckStatus.SKIP),
            }
        )
    
    def _add_check(self, result: CheckResult) -> None:
        """Add a check result"""
        self.checks.append(result)
    
    # =========================================================================
    # Core Checks
    # =========================================================================
    
    def _check_python_version(self) -> None:
        """Check Python version is 3.10+"""
        version = sys.version_info
        if version >= (3, 10):
            self._add_check(CheckResult(
                name="Python Version",
                status=CheckStatus.PASS,
                message=f"Python {version.major}.{version.minor}.{version.micro}"
            ))
        else:
            self._add_check(CheckResult(
                name="Python Version",
                status=CheckStatus.FAIL,
                message=f"Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)",
                fix_hint="Upgrade to Python 3.10 or later",
                fix_command="https://www.python.org/downloads/"
            ))
    
    def _check_required_packages(self) -> None:
        """Check required packages are installed"""
        required = ['httpx', 'pydantic', 'pywats']
        missing = []
        installed = []
        
        for pkg in required:
            try:
                __import__(pkg)
                installed.append(pkg)
            except ImportError:
                missing.append(pkg)
        
        if not missing:
            self._add_check(CheckResult(
                name="Required Packages",
                status=CheckStatus.PASS,
                message=f"All {len(required)} required packages installed",
                details=", ".join(installed)
            ))
        else:
            self._add_check(CheckResult(
                name="Required Packages",
                status=CheckStatus.FAIL,
                message=f"Missing packages: {', '.join(missing)}",
                fix_hint="Install missing packages",
                fix_command=f"pip install {' '.join(missing)}"
            ))
    
    def _check_optional_packages(self) -> None:
        """Check optional packages"""
        optional_checks = [
            ('PySide6', 'GUI support'),
            ('watchdog', 'File monitoring'),
            ('msgpack', 'MessagePack serialization'),
        ]
        
        if sys.platform == 'win32':
            optional_checks.append(('win32serviceutil', 'Windows Service support'))
        
        for pkg, description in optional_checks:
            try:
                __import__(pkg)
                self._add_check(CheckResult(
                    name=f"Optional: {description}",
                    status=CheckStatus.PASS,
                    message=f"{pkg} available"
                ))
            except ImportError:
                self._add_check(CheckResult(
                    name=f"Optional: {description}",
                    status=CheckStatus.WARN,
                    message=f"{pkg} not installed",
                    fix_hint=f"Install for {description}",
                    fix_command=f"pip install {pkg}"
                ))
    
    # =========================================================================
    # File System Checks
    # =========================================================================
    
    def _check_config_directory(self) -> None:
        """Check config directory exists and is writable"""
        config_dir = self.config_dir
        
        if config_dir.exists():
            # Check writable
            test_file = config_dir / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                self._add_check(CheckResult(
                    name="Config Directory",
                    status=CheckStatus.PASS,
                    message=f"Writable: {config_dir}"
                ))
            except PermissionError:
                self._add_check(CheckResult(
                    name="Config Directory",
                    status=CheckStatus.FAIL,
                    message=f"Not writable: {config_dir}",
                    fix_hint="Fix directory permissions",
                    fix_command=f"chmod 755 {config_dir}" if sys.platform != 'win32' else None
                ))
        else:
            # Try to create
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                self._add_check(CheckResult(
                    name="Config Directory",
                    status=CheckStatus.PASS,
                    message=f"Created: {config_dir}"
                ))
            except PermissionError:
                self._add_check(CheckResult(
                    name="Config Directory",
                    status=CheckStatus.FAIL,
                    message=f"Cannot create: {config_dir}",
                    fix_hint="Create directory manually with proper permissions"
                ))
    
    def _check_log_directory(self) -> None:
        """Check log directory"""
        if sys.platform == 'win32':
            log_dir = self.config_dir / "logs"
        else:
            log_dir = Path("/var/log/pywats")
            if not log_dir.exists():
                # Fall back to user directory
                log_dir = self.config_dir / "logs"
        
        if log_dir.exists():
            self._add_check(CheckResult(
                name="Log Directory",
                status=CheckStatus.PASS,
                message=f"Exists: {log_dir}"
            ))
        else:
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                self._add_check(CheckResult(
                    name="Log Directory",
                    status=CheckStatus.PASS,
                    message=f"Created: {log_dir}"
                ))
            except PermissionError:
                self._add_check(CheckResult(
                    name="Log Directory",
                    status=CheckStatus.WARN,
                    message=f"Cannot create system log directory, using user directory",
                    details=str(log_dir)
                ))
    
    # =========================================================================
    # Network Checks
    # =========================================================================
    
    def _check_network_connectivity(self) -> None:
        """Check basic network connectivity"""
        test_hosts = [
            ('8.8.8.8', 53, 'DNS (Google)'),
            ('1.1.1.1', 53, 'DNS (Cloudflare)'),
        ]
        
        connected = False
        for host, port, name in test_hosts:
            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
                connected = True
                break
            except (socket.timeout, socket.error):
                continue
        
        if connected:
            self._add_check(CheckResult(
                name="Network Connectivity",
                status=CheckStatus.PASS,
                message="Internet connection available"
            ))
        else:
            self._add_check(CheckResult(
                name="Network Connectivity",
                status=CheckStatus.FAIL,
                message="No internet connection detected",
                fix_hint="Check network configuration, proxy settings, or firewall"
            ))
    
    def _check_wats_server(self) -> None:
        """Check WATS server connectivity"""
        if not self.server_url:
            self._add_check(CheckResult(
                name="WATS Server",
                status=CheckStatus.SKIP,
                message="No server URL configured",
                fix_hint="Set PYWATS_SERVER_URL environment variable or configure in settings"
            ))
            return
        
        try:
            import httpx
            from urllib.parse import urlparse
            
            parsed = urlparse(self.server_url)
            
            # Try health endpoint first
            with httpx.Client(timeout=10.0, verify=True) as client:
                try:
                    response = client.get(f"{self.server_url.rstrip('/')}/api/health")
                    if response.status_code < 500:
                        self._add_check(CheckResult(
                            name="WATS Server",
                            status=CheckStatus.PASS,
                            message=f"Reachable: {parsed.netloc}",
                            details=f"Status: {response.status_code}"
                        ))
                        return
                except httpx.HTTPError:
                    pass
                
                # Try version endpoint
                try:
                    response = client.get(f"{self.server_url.rstrip('/')}/api/version")
                    if response.status_code < 500:
                        self._add_check(CheckResult(
                            name="WATS Server",
                            status=CheckStatus.PASS,
                            message=f"Reachable: {parsed.netloc}"
                        ))
                        return
                except httpx.HTTPError:
                    pass
            
            # Connection failed
            self._add_check(CheckResult(
                name="WATS Server",
                status=CheckStatus.FAIL,
                message=f"Cannot reach: {parsed.netloc}",
                fix_hint="Verify server URL, check firewall, or try: curl " + self.server_url
            ))
            
        except ImportError:
            self._add_check(CheckResult(
                name="WATS Server",
                status=CheckStatus.SKIP,
                message="httpx not installed, cannot check server"
            ))
        except Exception as e:
            self._add_check(CheckResult(
                name="WATS Server",
                status=CheckStatus.FAIL,
                message=f"Error: {str(e)}",
                fix_hint="Check server URL format and network connectivity"
            ))
    
    # =========================================================================
    # Windows-Specific Checks
    # =========================================================================
    
    def _check_windows_service(self) -> None:
        """Check Windows Service support"""
        if sys.platform != 'win32':
            return
        
        try:
            import win32serviceutil
            import win32service
            
            # Check if pyWATS service exists
            try:
                status = win32serviceutil.QueryServiceStatus('pyWATSClient')
                state_map = {
                    win32service.SERVICE_STOPPED: 'Stopped',
                    win32service.SERVICE_START_PENDING: 'Starting',
                    win32service.SERVICE_STOP_PENDING: 'Stopping',
                    win32service.SERVICE_RUNNING: 'Running',
                }
                state = state_map.get(status[1], 'Unknown')
                self._add_check(CheckResult(
                    name="Windows Service",
                    status=CheckStatus.PASS,
                    message=f"pyWATS Client service: {state}"
                ))
            except Exception:
                self._add_check(CheckResult(
                    name="Windows Service",
                    status=CheckStatus.WARN,
                    message="pyWATS Client service not installed",
                    fix_hint="Install service with: pywats-client install-service"
                ))
        except ImportError:
            self._add_check(CheckResult(
                name="Windows Service",
                status=CheckStatus.WARN,
                message="pywin32 not installed (required for Windows Service)",
                fix_hint="Install pywin32",
                fix_command="pip install pywin32"
            ))
    
    def _check_windows_firewall(self) -> None:
        """Check Windows Firewall status"""
        if sys.platform != 'win32':
            return
        
        try:
            import subprocess
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'ON' in result.stdout:
                self._add_check(CheckResult(
                    name="Windows Firewall",
                    status=CheckStatus.WARN,
                    message="Firewall is ON - ensure outbound HTTPS (443) is allowed",
                    fix_hint="Add firewall exception if connections fail"
                ))
            else:
                self._add_check(CheckResult(
                    name="Windows Firewall",
                    status=CheckStatus.PASS,
                    message="Firewall check complete"
                ))
        except Exception:
            self._add_check(CheckResult(
                name="Windows Firewall",
                status=CheckStatus.SKIP,
                message="Could not check firewall status"
            ))
    
    # =========================================================================
    # Linux-Specific Checks
    # =========================================================================
    
    def _check_systemd(self) -> None:
        """Check systemd availability"""
        if sys.platform != 'linux':
            return
        
        systemctl = shutil.which('systemctl')
        if systemctl:
            try:
                import subprocess
                # Check if pywats service exists
                result = subprocess.run(
                    ['systemctl', 'is-active', 'pywats-client'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self._add_check(CheckResult(
                        name="systemd Service",
                        status=CheckStatus.PASS,
                        message="pywats-client service is active"
                    ))
                else:
                    # Check if unit file exists
                    result = subprocess.run(
                        ['systemctl', 'cat', 'pywats-client'],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self._add_check(CheckResult(
                            name="systemd Service",
                            status=CheckStatus.WARN,
                            message="pywats-client service installed but not running",
                            fix_command="sudo systemctl start pywats-client"
                        ))
                    else:
                        self._add_check(CheckResult(
                            name="systemd Service",
                            status=CheckStatus.WARN,
                            message="pywats-client service not installed",
                            fix_hint="Install using DEB/RPM package or create unit file"
                        ))
            except Exception:
                self._add_check(CheckResult(
                    name="systemd Service",
                    status=CheckStatus.PASS,
                    message="systemd available"
                ))
        else:
            self._add_check(CheckResult(
                name="systemd Service",
                status=CheckStatus.WARN,
                message="systemd not found (init system may differ)"
            ))
    
    def _check_selinux(self) -> None:
        """Check SELinux status"""
        if sys.platform != 'linux':
            return
        
        # Check if SELinux is present
        if not Path('/etc/selinux').exists():
            self._add_check(CheckResult(
                name="SELinux",
                status=CheckStatus.SKIP,
                message="SELinux not installed"
            ))
            return
        
        try:
            import subprocess
            result = subprocess.run(
                ['getenforce'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            mode = result.stdout.strip()
            
            if mode == 'Enforcing':
                # Check if pywats policy is loaded
                result = subprocess.run(
                    ['semodule', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if 'pywats' in result.stdout:
                    self._add_check(CheckResult(
                        name="SELinux",
                        status=CheckStatus.PASS,
                        message="Enforcing mode with pywats policy loaded"
                    ))
                else:
                    self._add_check(CheckResult(
                        name="SELinux",
                        status=CheckStatus.WARN,
                        message="Enforcing mode - pywats policy NOT loaded",
                        fix_hint="Install SELinux policy module",
                        fix_command="cd selinux/ && sudo ./install-selinux.sh"
                    ))
            elif mode == 'Permissive':
                self._add_check(CheckResult(
                    name="SELinux",
                    status=CheckStatus.WARN,
                    message="Permissive mode - will work but not production-ready"
                ))
            else:
                self._add_check(CheckResult(
                    name="SELinux",
                    status=CheckStatus.PASS,
                    message=f"SELinux: {mode}"
                ))
                
        except FileNotFoundError:
            self._add_check(CheckResult(
                name="SELinux",
                status=CheckStatus.SKIP,
                message="getenforce command not found"
            ))
        except Exception as e:
            self._add_check(CheckResult(
                name="SELinux",
                status=CheckStatus.SKIP,
                message=f"Could not check: {str(e)}"
            ))
    
    # =========================================================================
    # macOS-Specific Checks
    # =========================================================================
    
    def _check_launchd(self) -> None:
        """Check launchd availability"""
        if sys.platform != 'darwin':
            return
        
        plist_paths = [
            Path.home() / 'Library/LaunchAgents/com.virinco.pywats-client.plist',
            Path('/Library/LaunchDaemons/com.virinco.pywats-client.plist'),
        ]
        
        for plist in plist_paths:
            if plist.exists():
                try:
                    import subprocess
                    result = subprocess.run(
                        ['launchctl', 'list', 'com.virinco.pywats-client'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        self._add_check(CheckResult(
                            name="launchd Service",
                            status=CheckStatus.PASS,
                            message="pywats-client service is loaded"
                        ))
                    else:
                        self._add_check(CheckResult(
                            name="launchd Service",
                            status=CheckStatus.WARN,
                            message="pywats-client plist exists but not loaded",
                            fix_command=f"launchctl load {plist}"
                        ))
                    return
                except Exception:
                    pass
        
        self._add_check(CheckResult(
            name="launchd Service",
            status=CheckStatus.WARN,
            message="pywats-client service not installed",
            fix_hint="See MACOS_SERVICE.md for installation instructions"
        ))


def run_diagnostics(
    server_url: Optional[str] = None,
    output_json: bool = False,
    verbose: bool = False
) -> int:
    """
    Run system diagnostics and print results.
    
    Args:
        server_url: WATS server URL to check
        output_json: Output as JSON instead of human-readable
        verbose: Show detailed output
        
    Returns:
        Exit code (0 = all pass, 1 = warnings, 2 = failures)
    """
    diag = SystemDiagnostics(server_url=server_url, verbose=verbose)
    report = diag.run_all_checks()
    
    if output_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        # Human-readable output
        print("\n" + "=" * 60)
        print("  pyWATS System Diagnostics")
        print("=" * 60)
        print(f"\nPlatform: {report.platform}")
        print(f"Python:   {report.python_version}")
        print(f"pyWATS:   {report.pywats_version}")
        print(f"Time:     {report.timestamp}")
        print()
        
        # Status symbols
        symbols = {
            CheckStatus.PASS: "✅",
            CheckStatus.WARN: "⚠️ ",
            CheckStatus.FAIL: "❌",
            CheckStatus.SKIP: "⏭️ ",
        }
        
        for check in report.checks:
            symbol = symbols[check.status]
            print(f"{symbol} {check.name}: {check.message}")
            
            if verbose and check.details:
                print(f"    Details: {check.details}")
            
            if check.status in (CheckStatus.WARN, CheckStatus.FAIL):
                if check.fix_hint:
                    print(f"    💡 {check.fix_hint}")
                if check.fix_command:
                    print(f"    🔧 {check.fix_command}")
        
        print()
        print("-" * 60)
        print(f"Summary: {report.summary['pass']} pass, "
              f"{report.summary['warn']} warn, "
              f"{report.summary['fail']} fail, "
              f"{report.summary['skip']} skip")
        
        overall_symbol = symbols[report.overall_status]
        print(f"\nOverall: {overall_symbol} {report.overall_status.value.upper()}")
        print("=" * 60 + "\n")
    
    # Return exit code based on status
    if report.overall_status == CheckStatus.FAIL:
        return 2
    elif report.overall_status == CheckStatus.WARN:
        return 1
    return 0


def main():
    """CLI entry point for diagnose command"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run pyWATS system diagnostics"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--server-url',
        type=str,
        help='WATS server URL to check (or set PYWATS_SERVER_URL)'
    )
    
    args = parser.parse_args()
    
    sys.exit(run_diagnostics(
        server_url=args.server_url,
        output_json=args.json,
        verbose=args.verbose
    ))


if __name__ == '__main__':
    main()
