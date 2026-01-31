# PyWATS GUI Application

The PyWATS GUI provides a desktop application for monitoring and configuring your WATS client service.

## Overview

The GUI application offers:
- **Real-time Monitoring** - View queue status, upload progress, connection state
- **Configuration Interface** - Configure server, converters, and settings
- **Log Viewer** - Monitor application and service logs
- **Converter Management** - Enable/disable and configure converters

**Important:** The GUI is a companion application for the [client service](client.md). The service handles the actual work (queue processing, uploads); the GUI provides visibility and configuration.

---

## Installation

```bash
pip install pywats-api[client]
```

**Requirements:**
- Python 3.10+
- Display/monitor (X11/Wayland on Linux)
- ~150 MB disk space

**Dependencies (automatically installed):**
- `PySide6` - Qt6 GUI framework
- `watchdog` - File monitoring
- `aiofiles` - Async file operations
- Plus all API dependencies

---

## Quick Start

### Starting the Service and GUI

The recommended workflow is to run the service first, then connect the GUI:

**Step 1: Start the service**
```bash
python -m pywats_client service --instance-id default
```

**Step 2: Launch GUI** (in another terminal)
```bash
python -m pywats_client gui --instance-id default
```

The GUI will connect to the running service via IPC.

### First-Time Setup

1. Launch the GUI
2. Go to **Setup** tab
3. Enter your WATS server details:
   - **Server URL**: `https://your-server.wats.com`
   - **Username**: Your WATS username
   - **Password**: Your WATS password
   - **Station Name**: Identifier for this test station
4. Click **Test Connection**
5. Click **Save**

---

## GUI Tabs

### 📊 Dashboard

Main overview showing:
- Connection status (connected/disconnected)
- Queue statistics (pending, processing, completed, failed)
- Recent uploads with timestamps
- Service health indicators

### ⚙️ Setup

Configure WATS server connection:
- Server URL
- Credentials
- Station name and location
- Connection test button

### 📁 Queue

View and manage the report queue:
- Pending reports waiting for upload
- Processing status
- Failed reports with error details
- Retry/delete options

### 🔄 Converters

Manage report converters:
- View installed converters
- Enable/disable converters
- Configure converter settings
- View converter status and errors

### 📋 Logs

Real-time log viewer:
- Filter by log level (DEBUG, INFO, WARNING, ERROR)
- Search functionality
- Auto-scroll toggle
- Export logs

### 📦 Software

Software distribution panel (if enabled):
- Available packages
- Download status
- Version information

---

## Configuration

### GUI Settings

The GUI stores its own settings separately from the service:

**Windows:**
```
%APPDATA%\pyWATS_Client\gui_settings.json
```

**Linux/macOS:**
```
~/.config/pywats_client/gui_settings.json
```

### Customizable Options

```json
{
  "window_geometry": {
    "width": 1200,
    "height": 800,
    "x": 100,
    "y": 100
  },
  "theme": "system",
  "log_viewer": {
    "max_lines": 10000,
    "auto_scroll": true,
    "show_timestamps": true
  },
  "refresh_interval": 1000,
  "notifications": {
    "upload_complete": true,
    "upload_failed": true,
    "connection_lost": true
  }
}
```

### Themes

The GUI supports system theme detection:

```bash
# Force light theme
python -m pywats_client gui --theme light

# Force dark theme  
python -m pywats_client gui --theme dark

# Use system preference (default)
python -m pywats_client gui --theme system
```

---

## Command Line Options

```bash
python -m pywats_client gui [OPTIONS]

Options:
  --instance-id TEXT    Client instance to connect to (default: "default")
  --config-path PATH    Path to config file
  --theme TEXT          Theme: light, dark, system
  --minimized           Start minimized to system tray
  --help               Show help message
```

### Examples

```bash
# Connect to default instance
python -m pywats_client gui

# Connect to specific instance
python -m pywats_client gui --instance-id station2

# Start minimized
python -m pywats_client gui --minimized

# Custom config location
python -m pywats_client gui --config-path /path/to/config.json
```

---

## System Tray

The GUI can minimize to the system tray:

- **Double-click** tray icon to restore window
- **Right-click** for context menu:
  - Show/Hide window
  - View status
  - Open logs folder
  - Exit

### Tray Notifications

When minimized, the GUI shows notifications for:
- Upload completed
- Upload failed
- Connection lost/restored
- Service stopped

Notifications can be disabled in settings.

---

## Troubleshooting

### GUI Won't Start

**Check Qt installation:**
```bash
python -c "from PySide6 import QtWidgets; print('Qt OK')"
```

**If import fails:**
```bash
pip uninstall PySide6
pip install PySide6
```

**Linux: Check display server:**
```bash
echo $DISPLAY  # Should show :0 or similar
```

### GUI Can't Connect to Service

1. **Verify service is running:**
   ```bash
   python -m pywats_client status --instance-id default
   ```

2. **Start service if needed:**
   ```bash
   python -m pywats_client service --instance-id default
   ```

3. **Check instance ID matches:**
   ```bash
   # Both must use same instance-id
   python -m pywats_client service --instance-id mystation
   python -m pywats_client gui --instance-id mystation
   ```

### Blank or Frozen UI

1. Check log file for errors:
   - Windows: `%APPDATA%\pyWATS_Client\pywats_client.log`
   - Linux: `~/.config/pywats_client/pywats_client.log`

2. Try resetting GUI settings:
   ```bash
   # Remove GUI settings (will use defaults)
   rm ~/.config/pywats_client/gui_settings.json
   ```

### High DPI Display Issues

```bash
# Force DPI scaling
export QT_AUTO_SCREEN_SCALE_FACTOR=1
python -m pywats_client gui

# Or set specific scale
export QT_SCALE_FACTOR=1.5
python -m pywats_client gui
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit application |
| `Ctrl+L` | Focus log search |
| `Ctrl+R` | Refresh all panels |
| `Ctrl+,` | Open settings |
| `F5` | Refresh queue |
| `F11` | Toggle fullscreen |
| `Ctrl+M` | Minimize to tray |

---

## Without GUI (Headless Alternative)

If you don't need a GUI, install the headless version instead:

```bash
pip install pywats-api[client-headless]
```

This provides all service functionality via CLI and HTTP API:

```bash
# Check status
pywats-client status

# View queue
pywats-client queue list

# Control via HTTP API
curl http://localhost:8765/status
```

See [Client Service Guide](client.md) for headless operation.

---

## See Also

- **[Client Service Guide](client.md)** - Background service documentation
- **[Windows Service](windows-service.md)** - Auto-start on Windows
- **[Linux Service](linux-service.md)** - Systemd service setup
- **[../getting-started.md](../getting-started.md)** - Complete tutorial
- **[../client-architecture.md](../client-architecture.md)** - Architecture details
