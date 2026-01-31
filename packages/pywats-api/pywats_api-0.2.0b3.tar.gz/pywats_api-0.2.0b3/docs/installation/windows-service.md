# Windows Service Installation

This guide explains how to install pyWATS Client as a Windows Service that auto-starts on system boot.

## Overview

The pyWATS Client can run as a Windows Service in the background, automatically starting when Windows boots. This is the recommended setup for production environments.

**Folder Structure:**
- **Installation**: `C:\Program Files\Virinco\pyWATS\` (binaries)
- **Data/Config**: `C:\ProgramData\Virinco\pyWATS\` (configuration, logs, queues)
- **Service Name**: `pyWATS_Service` (appears in Task Manager/Services)

This matches the existing WATS Client installation pattern.

## Prerequisites

### Required
- Windows 10/11 or Windows Server 2016+
- Python 3.10 or later
- Administrator privileges

### Recommended: NSSM (Non-Sucking Service Manager)

NSSM provides the best Windows Service experience with:
- Easy service installation/removal
- Automatic log rotation
- Crash recovery
- Better process management

**Download NSSM:**
1. Visit: https://nssm.cc/download
2. Download the latest version (2.24+)
3. Extract `nssm.exe` to `C:\Program Files\NSSM\` or any PATH location

**Alternative:** The installer can use `sc.exe` (built into Windows), but this has limitations.

## Installation

### Option 1: Using NSSM (Recommended)

1. **Install pyWATS Client** (if not already installed):
   ```powershell
   pip install pywats-api[client]
   ```

2. **Install the service** (run as Administrator):
   ```powershell
   python -m pywats_client install-service
   ```

   This will:
   - Create service `pyWATS_Service`
   - Set auto-start on boot
   - Configure logging to `C:\ProgramData\Virinco\pyWATS\logs\`
   - Use default configuration

3. **Start the service**:
   ```powershell
   net start pyWATS_Service
   ```
   or
   ```powershell
   nssm start pyWATS_Service
   ```

### Option 2: Native Windows Service (Recommended for Enterprise)

The native Windows service uses pywin32 and provides:
- **Appears in Task Manager** → Services tab
- **Automatic restart on failure** (5s/5s/30s delays)
- **Delayed auto-start** (waits for network services)
- **Windows Event Log integration** (events in Event Viewer)

```powershell
# Install native service (run as Administrator)
python -m pywats_client install-service --native

# Start the service
net start pyWATS_Service
```

**Features automatically configured:**
- Service recovery: restarts after 5s on first two failures, 30s thereafter
- Delayed start: waits for network to be ready before starting
- Event logging: service events written to Windows Event Log

### Option 3: Using sc.exe (Fallback)

If NSSM is not available:

```powershell
python -m pywats_client install-service --use-sc
net start pyWATS_Service
```

**Note:** `sc.exe` has limitations (no automatic log rotation, limited crash recovery).

## Multi-Instance Installation

For multi-station setups where you need multiple services (one per test station):

```powershell
# Install service for Station A
python -m pywats_client install-service --instance-id station_a --config "C:\ProgramData\Virinco\pyWATS\config_station_a.json"

# Install service for Station B
python -m pywats_client install-service --instance-id station_b --config "C:\ProgramData\Virinco\pyWATS\config_station_b.json"
```

Each instance will have:
- Service name: `pyWATS_Service_station_a`, `pyWATS_Service_station_b`
- Separate logs: `pyWATS_Service_station_a.log`, `pyWATS_Service_station_b.log`
- Independent configuration files

## Service Management

### Check Service Status

```powershell
# Using sc.exe
sc query pyWATS_Service

# Using NSSM
nssm status pyWATS_Service

# Using services.msc GUI
services.msc
```

### Start/Stop/Restart

```powershell
# Start
net start pyWATS_Service

# Stop
net stop pyWATS_Service

# Restart
net stop pyWATS_Service && net start pyWATS_Service

# Or with NSSM
nssm restart pyWATS_Service
```

### View Logs

Logs are written to `C:\ProgramData\Virinco\pyWATS\logs\`:
- `pyWATS_Service.log` - Standard output
- `pyWATS_Service_error.log` - Error output

```powershell
# View latest logs
Get-Content "C:\ProgramData\Virinco\pyWATS\logs\pyWATS_Service.log" -Tail 50

# Monitor live
Get-Content "C:\ProgramData\Virinco\pyWATS\logs\pyWATS_Service.log" -Wait
```

### Uninstall Service

```powershell
# Stop and remove
python -m pywats_client uninstall-service

# For specific instance
python -m pywats_client uninstall-service --instance-id station_a
```

## Configuration

### Default Configuration

The service uses configuration from:
- Default: `C:\ProgramData\Virinco\pyWATS\config.json`
- Custom: Specify with `--config` during installation

### Changing Configuration

**Option 1: Using GUI**
1. Run the pyWATS Client GUI
2. It will discover the running service
3. Make configuration changes in the GUI
4. Changes are sent via IPC to the service

**Option 2: Edit config.json**
1. Stop the service: `net stop pyWATS_Service`
2. Edit: `C:\ProgramData\Virinco\pyWATS\config.json`
3. Start the service: `net start pyWATS_Service`

**Option 3: Reinstall with new config**
```powershell
python -m pywats_client uninstall-service
python -m pywats_client install-service --config "C:\path\to\new\config.json"
net start pyWATS_Service
```

## Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```powershell
   Get-Content "C:\ProgramData\Virinco\pyWATS\logs\pyWATS_Service_error.log"
   ```

2. **Test service command manually**:
   ```powershell
   python -m pywats_client service --instance-id default
   ```
   
   This runs the service in foreground mode for debugging.

3. **Verify Python path**:
   ```powershell
   where python
   ```
   
   NSSM uses the Python executable from your PATH. Make sure it's correct.

### Permission Errors

The service runs under the SYSTEM account by default. If you need access to network shares or user-specific resources:

```powershell
# Change service account (NSSM)
nssm set pyWATS_Service ObjectName "DOMAIN\Username" "Password"

# Or use sc.exe
sc config pyWATS_Service obj= "DOMAIN\Username" password= "Password"
```

### Service Crashes

NSSM automatically restarts crashed services. Check logs for crash details:
```powershell
Get-Content "C:\ProgramData\Virinco\pyWATS\logs\pyWATS_Service_error.log" -Tail 100
```

To disable auto-restart (for debugging):
```powershell
nssm set pyWATS_Service AppExit Default Exit
```

### Multiple Instances Conflict

If you see errors about ports or IPC endpoints already in use:

1. Each instance needs a unique `--instance-id`
2. Check running services:
   ```powershell
   sc query type= service state= all | findstr "pyWATS"
   ```

3. Stop conflicting instances:
   ```powershell
   net stop pyWATS_Service
   net stop pyWATS_Service_station_a
   ```

## Silent Installation (IT Deployment)

For scripted deployment via GPO, SCCM, or automation tools:

### Basic Silent Install

```powershell
# Install silently with native service
python -m pywats_client install-service --native --silent

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Error "Installation failed with exit code $LASTEXITCODE"
    exit 1
}
```

### Silent Install with Configuration

```powershell
python -m pywats_client install-service --native --silent `
    --server-url "https://wats.company.com" `
    --api-token "your-api-token" `
    --watch-folder "C:\TestReports"
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Missing requirements (Python version, pywin32) |
| 10 | Service already installed |
| 11 | Service not installed (uninstall) |
| 14 | Permission denied (need Administrator) |
| 41 | Server unreachable |

### Example Deployment Script

```powershell
# deploy_pywats.ps1 - Silent deployment script

param(
    [string]$ServerUrl = "https://wats.company.com",
    [string]$ApiToken,
    [string]$WatchFolder = "C:\TestReports"
)

# Ensure admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Administrator privileges required"
    exit 14
}

# Install Python package (if needed)
pip install pywats-api[client] --quiet

# Install service
python -m pywats_client install-service --native --silent `
    --server-url $ServerUrl `
    --api-token $ApiToken `
    --watch-folder $WatchFolder

if ($LASTEXITCODE -ne 0) {
    Write-Error "Service installation failed: exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Start service
net start pyWATS_Service
Write-Host "pyWATS Service installed and started successfully"
```

## Event Log

When using `--native`, the service writes to Windows Event Log:

```powershell
# View pyWATS events in Event Viewer
Get-EventLog -LogName Application -Source "pyWATS" -Newest 20
```

Events include:
- Service installation/uninstallation
- Service start/stop
- Errors and warnings

## Advanced Configuration

### Custom Service Name

```powershell
# Edit WindowsServiceInstaller.SERVICE_NAME in:
# src/pywats_client/control/windows_service.py
```

### Environment Variables

```powershell
# Set environment variables for the service
nssm set pyWATS_Service AppEnvironmentExtra PYTHONPATH=C:\custom\path
```

### Delayed Start

```powershell
# Start service 2 minutes after boot
sc config pyWATS_Service start= delayed-auto
```

## GUI Discovery

When you open the pyWATS Client GUI:

1. **Discovery**: GUI scans for running service instances
2. **Instance Selector**: Shows all discovered services
3. **Connect**: Select an instance to view/configure
4. **Status**: Live status updates via IPC

The GUI never auto-starts services - they must be started separately (manually or via Windows Service).

## Comparison with Manual Start

| Method | Auto-Start | Survives Reboot | Crash Recovery | Service Management |
|--------|------------|-----------------|----------------|-------------------|
| **Windows Service** | ✓ | ✓ | ✓ (NSSM) | services.msc, sc.exe |
| **Manual (GUI)** | ✗ | ✗ | ✗ | Task Manager |
| **Task Scheduler** | ✓ | ✓ | ✗ | taskschd.msc |
| **Startup Folder** | ✓ | ✓ | ✗ | Manual |

**Recommendation:** Use Windows Service for production environments.

## See Also

- [Getting Started](../getting-started.md) - Basic client usage
- [Client Installation](client.md) - Installation guide
- [NSSM Documentation](https://nssm.cc/usage) - Full NSSM options
