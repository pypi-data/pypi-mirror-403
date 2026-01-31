# Windows IoT Enterprise LTSC Installation Guide

This guide covers installing pyWATS Client on **Windows 10/11 IoT Enterprise LTSC** (Long-Term Servicing Channel) systems commonly used in factory floor environments.

---

## Overview

Windows IoT Enterprise LTSC is designed for fixed-purpose devices like industrial PCs, test stations, and manufacturing equipment. It has unique constraints compared to standard Windows:

| Feature | Standard Windows | IoT LTSC |
|---------|-----------------|----------|
| Feature Updates | Every 6-12 months | None (10-year support) |
| Microsoft Store | Available | Often disabled |
| PowerShell | Unrestricted | May be restricted |
| Write Filters | Not included | UWF/FBWF available |
| Default Shell | explorer.exe | May be custom kiosk |

---

## Prerequisites

### 1. Python Installation

Since the Microsoft Store is typically disabled on IoT LTSC, install Python from python.org:

```powershell
# Download Python 3.11 installer
# https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# Silent install (run as Administrator)
python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

# Verify installation
python --version
```

**Alternative: Embedded Python**

For minimal footprint, use Python embedded distribution:

```powershell
# Download embedded Python
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" `
    -OutFile "python-embed.zip"

# Extract to C:\Python311
Expand-Archive -Path "python-embed.zip" -DestinationPath "C:\Python311"

# Enable pip (edit python311._pth, uncomment import site)
# Then install pip
C:\Python311\python.exe -m ensurepip
```

### 2. Execution Policy

IoT LTSC may have restricted PowerShell execution policy:

```powershell
# Check current policy
Get-ExecutionPolicy

# If restricted, use cmd.exe for installation instead
# Or temporarily allow scripts (requires admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

---

## Write Filter Considerations

### Unified Write Filter (UWF)

Many IoT LTSC deployments use **Unified Write Filter** to protect the system volume. Changes to filtered volumes are lost on reboot.

**Check UWF Status:**
```powershell
uwfmgr.exe get-config
```

**Option 1: Install to Unfiltered Volume**

If you have a separate data drive (e.g., D:), install pyWATS there:

```powershell
# Create virtual environment on unfiltered drive
python -m venv D:\pywats\.venv
D:\pywats\.venv\Scripts\activate
pip install pywats-api[client-headless]
```

**Option 2: Commit Changes to Protected Volume**

```powershell
# Disable UWF temporarily (requires reboot)
uwfmgr.exe filter disable

# --- Reboot, install pyWATS, then: ---

# Re-enable UWF
uwfmgr.exe filter enable

# --- Reboot to activate protection ---
```

**Option 3: Add pyWATS Files to Exclusion List**

```powershell
# Exclude pyWATS installation directory
uwfmgr.exe file add-exclusion "C:\pywats"

# Exclude Python installation
uwfmgr.exe file add-exclusion "C:\Python311"

# Exclude configuration directory
uwfmgr.exe file add-exclusion "C:\ProgramData\pyWATS"
```

### File-Based Write Filter (FBWF) - Legacy

Older IoT images may use FBWF instead of UWF:

```powershell
# Check FBWF status
fbwfmgr /displayconfig

# Disable for installation
fbwfmgr /disable
# Reboot, install, then:
fbwfmgr /enable
```

---

## AppLocker / Application Control

IoT LTSC systems may have AppLocker policies that block unsigned executables.

### Check AppLocker Status

```powershell
Get-AppLockerPolicy -Effective | Format-List
```

### Add pyWATS Exceptions

Work with your IT administrator to add exceptions for:

1. **Python executable**: `C:\Python311\python.exe`
2. **pip packages**: `C:\Python311\Lib\site-packages\*`
3. **pyWATS scripts**: `C:\pywats\.venv\Scripts\*`

Example AppLocker rule (requires Group Policy):
```xml
<FilePathRule Id="..." Name="pyWATS Client" Description="Allow pyWATS execution" UserOrGroupSid="S-1-1-0" Action="Allow">
  <Conditions>
    <FilePathCondition Path="C:\pywats\*"/>
  </Conditions>
</FilePathRule>
```

---

## Windows Defender Exclusions

On resource-constrained IoT devices, add exclusions to prevent performance impact:

```powershell
# Add exclusions (run as Administrator)
Add-MpPreference -ExclusionPath "C:\pywats"
Add-MpPreference -ExclusionPath "C:\Python311"
Add-MpPreference -ExclusionProcess "python.exe"
Add-MpPreference -ExclusionProcess "pythonw.exe"
```

---

## Installation Steps

### 1. Install pyWATS (Headless Mode Recommended)

IoT LTSC typically runs without a desktop. Use the headless client:

```powershell
# Create virtual environment
python -m venv C:\pywats\.venv

# Activate
C:\pywats\.venv\Scripts\activate

# Install headless client (no GUI dependencies)
pip install pywats-api[client-headless]
```

### 2. Configure pyWATS

```powershell
# Create configuration directory
New-Item -ItemType Directory -Force -Path "C:\ProgramData\pyWATS\config"

# Create configuration file
@"
{
  "server": {
    "url": "https://wats.yourcompany.com",
    "token": "YOUR_API_TOKEN"
  },
  "client": {
    "watch_folder": "C:\\TestReports\\pending",
    "archive_folder": "C:\\TestReports\\archive"
  }
}
"@ | Out-File -FilePath "C:\ProgramData\pyWATS\config\config.json" -Encoding UTF8
```

### 3. Install as Windows Service

```powershell
# Silent installation for automated deployment
python -m pywats_client install-service `
    --silent `
    --server-url "https://wats.yourcompany.com" `
    --api-token "YOUR_API_TOKEN" `
    --watch-folder "C:\TestReports\pending"
```

### 4. Verify Service

```powershell
# Check service status
Get-Service pyWATS_Service

# View in services.msc (if GUI available)
services.msc
```

---

## Kiosk Mode / Custom Shell

If the IoT device runs in kiosk mode with a custom shell:

### Assigned Access (Single-App Kiosk)

pyWATS runs as a background service, so it works alongside any kiosk app.

### Shell Launcher

If using Shell Launcher, ensure the pyWATS service is configured to start:

```powershell
# Service starts automatically regardless of shell
Get-Service pyWATS_Service | Select-Object StartType
# Should be: Automatic (Delayed Start)
```

---

## Network Configuration

### Static IP (Common in Factories)

```powershell
# Configure static IP
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.100 -PrefixLength 24 -DefaultGateway 192.168.1.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 192.168.1.1
```

### Firewall Rules

```powershell
# Allow outbound HTTPS to WATS server
New-NetFirewallRule -DisplayName "pyWATS Outbound" `
    -Direction Outbound `
    -Protocol TCP `
    -RemotePort 443 `
    -Action Allow `
    -Program "C:\Python311\python.exe"
```

---

## Troubleshooting

### Service Won't Start

```powershell
# Check Windows Event Log
Get-EventLog -LogName Application -Source pyWATS -Newest 10

# Check service status details
sc.exe query pyWATS_Service
sc.exe queryex pyWATS_Service
```

### UWF Blocking File Writes

```
Error: Permission denied writing to C:\ProgramData\pyWATS\logs
```

**Solution:** Add the logs directory to UWF exclusions:
```powershell
uwfmgr.exe file add-exclusion "C:\ProgramData\pyWATS\logs"
```

### Python Not Found After Reboot

If UWF is enabled and Python was installed on a protected volume:

```powershell
# Commit Python installation
uwfmgr.exe file commit "C:\Python311"
```

### pywin32 DLL Errors

```
ImportError: DLL load failed while importing win32api
```

**Solution:** Run post-install script:
```powershell
python C:\pywats\.venv\Scripts\pywin32_postinstall.py -install
```

---

## Deployment Script Example

Complete silent deployment script for IT automation:

```powershell
# deploy_pywats.ps1 - Run as Administrator
param(
    [string]$WatsUrl = "https://wats.yourcompany.com",
    [string]$ApiToken,
    [string]$WatchFolder = "C:\TestReports\pending"
)

$ErrorActionPreference = "Stop"

# 1. Check for UWF and warn
$uwfEnabled = (uwfmgr.exe get-config | Select-String "Filter state.*ON")
if ($uwfEnabled) {
    Write-Warning "UWF is enabled. Ensure pyWATS directories are excluded."
}

# 2. Create directories
New-Item -ItemType Directory -Force -Path "C:\pywats"
New-Item -ItemType Directory -Force -Path $WatchFolder

# 3. Create virtual environment
python -m venv C:\pywats\.venv

# 4. Install pyWATS
& C:\pywats\.venv\Scripts\pip.exe install pywats-api[client-headless]

# 5. Install service silently
& C:\pywats\.venv\Scripts\python.exe -m pywats_client install-service `
    --silent `
    --server-url $WatsUrl `
    --api-token $ApiToken `
    --watch-folder $WatchFolder

# 6. Start service
Start-Service pyWATS_Service

# 7. Verify
$svc = Get-Service pyWATS_Service
if ($svc.Status -eq "Running") {
    Write-Host "✓ pyWATS installed and running" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Service failed to start" -ForegroundColor Red
    exit 1
}
```

---

## Related Documentation

- [Windows Service Installation](WINDOWS_SERVICE.md)
- [Client Configuration](CLIENT_INSTALLATION.md)
- [Troubleshooting](ERROR_CATALOG.md)

---

*Last Updated: 2026-01-26*
