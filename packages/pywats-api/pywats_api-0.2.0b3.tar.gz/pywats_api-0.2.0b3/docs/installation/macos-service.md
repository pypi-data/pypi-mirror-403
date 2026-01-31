# macOS launchd Service Installation

This guide explains how to install pyWATS Client as a macOS launchd service that auto-starts on system boot.

## Overview

The pyWATS Client can run as a launchd daemon/agent in the background, automatically starting when macOS boots or when you log in.

**Service Types:**
- **Launch Daemon**: Starts at boot (system-wide, requires sudo)
- **Launch Agent**: Starts at login (user-specific, no sudo required)

**Folder Structure:**
- **Daemons**: `/Library/LaunchDaemons/` (system-wide)
- **Agents**: `/Library/LaunchAgents/` (user-level)
- **Data (Daemon)**: `/var/lib/pywats/`
- **Data (Agent)**: `~/.config/pywats_client/`
- **Logs (Daemon)**: `/var/log/pywats/`
- **Logs (Agent)**: `~/Library/Logs/pyWATS/`

## Prerequisites

### Required
- macOS 10.10 (Yosemite) or later
- Python 3.10 or later
- Administrator privileges (for Launch Daemon)

## Installation

### Option 1: Launch Daemon (System-Wide, Recommended)

Runs at boot, before any user logs in. Best for production test stations.

```bash
# Install pyWATS Client
pip3 install pywats-api[client]

# Install as Launch Daemon (requires sudo)
sudo python3 -m pywats_client install-service

# Service starts automatically after installation
# Or start manually:
sudo launchctl start com.wats.pywats.service
```

This creates:
- Plist: `/Library/LaunchDaemons/com.wats.pywats.service.plist`
- Auto-start: Enabled (runs at boot)
- Logs: `/var/log/pywats/pywats-service.log`
- Data: `/var/lib/pywats/`

### Option 2: Launch Agent (User-Level)

Runs when you log in. Good for development.

```bash
# Install pyWATS Client
pip3 install pywats-api[client]

# Install as Launch Agent (no sudo needed)
python3 -m pywats_client install-service --user-agent

# Service starts automatically at login
# Or start manually:
launchctl start com.wats.pywats.service
```

This creates:
- Plist: `/Library/LaunchAgents/com.wats.pywats.service.plist`
- Auto-start: At login
- Logs: `~/Library/Logs/pyWATS/pywats-service.log`
- Data: `~/.config/pywats_client/`

## Multi-Instance Installation

For multi-station setups where you need multiple services (one per test station):

```bash
# Create config files
sudo mkdir -p /var/lib/pywats
sudo cp config.json /var/lib/pywats/config_station_a.json
sudo cp config.json /var/lib/pywats/config_station_b.json

# Install service for Station A
sudo python3 -m pywats_client install-service \
    --instance-id station_a \
    --config /var/lib/pywats/config_station_a.json

# Install service for Station B
sudo python3 -m pywats_client install-service \
    --instance-id station_b \
    --config /var/lib/pywats/config_station_b.json
```

Each instance will have:
- Plist: `com.wats.pywats.service.station_a.plist`, `com.wats.pywats.service.station_b.plist`
- Separate configurations
- Independent logging

## Service Management

### Check Service Status

```bash
# List all launchd services (system)
sudo launchctl list | grep pywats

# List user services
launchctl list | grep pywats

# Check specific service
sudo launchctl list com.wats.pywats.service
```

### Start/Stop

**Launch Daemon (system-wide):**
```bash
# Start
sudo launchctl start com.wats.pywats.service

# Stop
sudo launchctl stop com.wats.pywats.service

# Note: Service will auto-restart if killed
# To prevent restart, unload the plist
sudo launchctl unload /Library/LaunchDaemons/com.wats.pywats.service.plist
```

**Launch Agent (user-level):**
```bash
# Start
launchctl start com.wats.pywats.service

# Stop
launchctl stop com.wats.pywats.service

# Unload
launchctl unload /Library/LaunchAgents/com.wats.pywats.service.plist
```

### View Logs

**Launch Daemon logs:**
```bash
# View logs
sudo tail -f /var/log/pywats/pywats-service.log

# View errors
sudo tail -f /var/log/pywats/pywats-service-error.log

# View with Console.app
open -a Console /var/log/pywats/
```

**Launch Agent logs:**
```bash
# View logs
tail -f ~/Library/Logs/pyWATS/pywats-service.log

# View errors
tail -f ~/Library/Logs/pyWATS/pywats-service-error.log

# View with Console.app
open -a Console ~/Library/Logs/pyWATS/
```

### Uninstall Service

**Launch Daemon:**
```bash
# Stop and remove
sudo python3 -m pywats_client uninstall-service

# For specific instance
sudo python3 -m pywats_client uninstall-service --instance-id station_a

# Verify removal
sudo launchctl list | grep pywats
```

**Launch Agent:**
```bash
# Stop and remove
python3 -m pywats_client uninstall-service --user-agent

# Verify removal
launchctl list | grep pywats
```

## Configuration

### Default Configuration

The service uses configuration from:
- Daemon: `/var/lib/pywats/config.json`
- Agent: `~/.config/pywats_client/config.json`
- Custom: Specify with `--config` during installation

### Changing Configuration

**Option 1: Using GUI**
1. Run the pyWATS Client GUI
2. It will discover the running service
3. Make configuration changes in the GUI
4. Changes are sent via IPC to the service

**Option 2: Edit config.json**
```bash
# Stop the service
sudo launchctl stop com.wats.pywats.service

# Edit configuration (Daemon)
sudo nano /var/lib/pywats/config.json

# Or for Agent
nano ~/.config/pywats_client/config.json

# Restart the service
sudo launchctl start com.wats.pywats.service
```

**Option 3: Reinstall with new config**
```bash
sudo python3 -m pywats_client uninstall-service
sudo python3 -m pywats_client install-service --config /path/to/new/config.json
```

## Troubleshooting

### Service Won't Start

1. **Check if plist is loaded**:
   ```bash
   sudo launchctl list | grep pywats
   ```

2. **Check logs**:
   ```bash
   sudo tail -100 /var/log/pywats/pywats-service-error.log
   ```

3. **Test service command manually**:
   ```bash
   # Run in foreground for debugging
   python3 -m pywats_client service --instance-id default
   ```

4. **Verify Python path**:
   ```bash
   which python3
   python3 --version
   ```

5. **Check plist syntax**:
   ```bash
   plutil /Library/LaunchDaemons/com.wats.pywats.service.plist
   ```

### Permission Errors

If the service can't access files:

```bash
# Check ownership (Daemon)
ls -la /var/lib/pywats/

# Fix permissions
sudo chown -R root:wheel /var/lib/pywats/
sudo chmod -R 755 /var/lib/pywats/

# For Agent
ls -la ~/.config/pywats_client/
```

### Service Keeps Restarting

The service is configured to auto-restart on failure. Check why it's failing:

```bash
# View recent errors
sudo tail -100 /var/log/pywats/pywats-service-error.log

# Check system logs
log show --predicate 'subsystem == "com.apple.launchd"' --last 10m | grep pywats

# Disable auto-restart temporarily
sudo launchctl unload /Library/LaunchDaemons/com.wats.pywats.service.plist
```

### Port Already in Use

If you see "Address already in use" errors:

```bash
# Check what's using the port
sudo lsof -i :8765

# Kill the conflicting process or change port in config
```

### Service Doesn't Auto-Start at Boot

1. **Verify plist location**:
   ```bash
   ls -l /Library/LaunchDaemons/com.wats.pywats.service.plist
   ```

2. **Check RunAtLoad**:
   ```bash
   plutil -p /Library/LaunchDaemons/com.wats.pywats.service.plist | grep RunAtLoad
   # Should show: "RunAtLoad" => 1
   ```

3. **Reload plist**:
   ```bash
   sudo launchctl unload /Library/LaunchDaemons/com.wats.pywats.service.plist
   sudo launchctl load /Library/LaunchDaemons/com.wats.pywats.service.plist
   ```

## Advanced Configuration

### Custom Environment Variables

Edit the plist file:

```bash
sudo nano /Library/LaunchDaemons/com.wats.pywats.service.plist
```

Add environment variables:
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PYTHONPATH</key>
    <string>/custom/path</string>
    <key>PYWATS_LOG_LEVEL</key>
    <string>DEBUG</string>
</dict>
```

Then reload:
```bash
sudo launchctl unload /Library/LaunchDaemons/com.wats.pywats.service.plist
sudo launchctl load /Library/LaunchDaemons/com.wats.pywats.service.plist
```

### Run on Schedule

Instead of continuous running, run periodically:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### Resource Limits

Add limits to prevent runaway processes:

```xml
<key>SoftResourceLimits</key>
<dict>
    <key>NumberOfFiles</key>
    <integer>1024</integer>
</dict>

<key>HardResourceLimits</key>
<dict>
    <key>NumberOfFiles</key>
    <integer>2048</integer>
</dict>
```

### Network Dependency

Ensure network is available before starting:

The default plist already includes this via `StandardOutPath` and `StandardErrorPath`, which ensures the filesystem is ready.

## GUI Discovery

When you open the pyWATS Client GUI on macOS:

1. **Discovery**: GUI scans for running service instances via IPC
2. **Instance Selector**: Shows all discovered services
3. **Connect**: Select an instance to view/configure
4. **Status**: Live status updates via IPC

The GUI never auto-starts services - they must be started separately via launchd.

## Comparison with Other Methods

| Method | Auto-Start | Survives Reboot | Crash Recovery | Service Management |
|--------|------------|-----------------|----------------|-------------------|
| **launchd Daemon** | ✓ (boot) | ✓ | ✓ | launchctl |
| **launchd Agent** | ✓ (login) | ✓ | ✓ | launchctl |
| **Manual (GUI)** | ✗ | ✗ | ✗ | Terminal |
| **Login Item** | ✓ (login) | ✓ | ✗ | System Preferences |
| **cron @reboot** | ✓ | ✓ | ✗ | crontab |

**Recommendation:** Use Launch Daemon for production test stations.

## macOS Version Notes

### macOS 13+ (Ventura)

Fully supported. May require additional privacy permissions.

```bash
# Grant Full Disk Access if needed
System Settings → Privacy & Security → Full Disk Access
```

### macOS 12 (Monterey)

Fully supported.

### macOS 11 (Big Sur)

Fully supported.

### macOS 10.15 (Catalina)

Supported. May prompt for security approval on first run.

## See Also

- [Getting Started](../getting-started.md) - Basic client usage
- [Client Installation](client.md) - Installation guide
- [Apple launchd documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
