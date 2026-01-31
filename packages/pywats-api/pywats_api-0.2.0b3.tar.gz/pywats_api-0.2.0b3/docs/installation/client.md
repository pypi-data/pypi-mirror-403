# PyWATS Client Service

The PyWATS Client Service is a background process that handles automated test report processing, queuing, and upload to WATS.

## Overview

The client service provides:
- **Report Queue** - Reliable queuing with retry on failure
- **Offline Support** - Queue reports when disconnected, upload when online
- **Converters** - Transform test equipment output to WATS format
- **File Watching** - Auto-detect new reports in watch folders
- **Multi-Instance** - Run separate instances for different stations

**Best for:** Test station automation, production environments, embedded systems.

---

## Installation

### With GUI (Desktop Stations)

```bash
pip install pywats-api[client]
```

Includes desktop GUI for configuration and monitoring. See [GUI Guide](gui.md).

### Headless (Servers, Embedded)

```bash
pip install pywats-api[client-headless]
```

No GUI dependencies - CLI and HTTP API only. Ideal for:
- Linux servers
- Raspberry Pi
- Embedded systems
- Docker containers

**Requirements:**
- Python 3.10+
- ~8 MB disk space (headless) / ~150 MB (with GUI)

---

## Quick Start

### Start the Service

```bash
# Default instance
python -m pywats_client service

# Named instance
python -m pywats_client service --instance-id station1
```

### First-Time Configuration

**Interactive setup:**
```bash
pywats-client config init
```

**Non-interactive:**
```bash
pywats-client config init \
    --server-url https://wats.yourcompany.com \
    --username your-username \
    --password your-password \
    --station-name ICT-STATION-01 \
    --non-interactive
```

### Verify Connection

```bash
pywats-client status
```

---

## Architecture

### Async-First Design (v1.4+)

The client uses an **async-first architecture** with asyncio for efficient concurrent I/O:

| Component | Purpose | Concurrency |
|-----------|---------|-------------|
| **AsyncClientService** | Main service controller | Single asyncio event loop |
| **AsyncPendingQueue** | Report upload queue | 5 concurrent uploads |
| **AsyncConverterPool** | File conversion | 10 concurrent conversions |
| **File Watcher** | Detects new files in watch folders | Async events |
| **IPC Server** | GUI communication | Qt LocalSocket |

### Report Processing Flow

```
Test Equipment → [File Created] → [File Watcher]
                                       ↓
                          [AsyncConverterPool]
                           (10 concurrent)
                                       ↓
                          [AsyncPendingQueue]
                           (5 concurrent)
                                       ↓
                           [WATS Server]
```

**Benefits of async architecture:**
- **5x faster uploads** - Concurrent report submission
- **Lower memory** - Single thread vs multiple workers
- **Responsive GUI** - Non-blocking API calls
- **Efficient I/O** - asyncio multiplexing

---

## File Organization

### Data Directories

**Windows (Production):**
```
C:\ProgramData\Virinco\pyWATS\
├── config.json              # Configuration
├── logs\                    # Service logs
├── queue\                   # Report queue
│   ├── pending\            # Waiting for upload
│   ├── processing\         # Currently uploading
│   ├── completed\          # Successfully uploaded
│   └── failed\             # Failed uploads
├── converters\              # Custom converters
└── data\                    # Software packages
```

**Windows (User Development):**
```
%APPDATA%\pyWATS_Client\
```

**Linux/macOS:**
```
~/.config/pywats_client/     # User
/var/lib/pywats/             # System service
```

### Queue Folder Contents

| Folder | Purpose | Auto-Cleanup |
|--------|---------|--------------|
| `pending/` | Reports waiting for upload | No |
| `processing/` | Currently uploading | No |
| `completed/` | Successfully uploaded | After 7 days |
| `failed/` | Failed uploads | After 30 days |

---

## Configuration

### Configuration File

`config.json`:
```json
{
  "server_url": "https://wats.yourcompany.com",
  "api_token": "...",
  "station_name": "ICT-STATION-01",
  "station_location": "Production Line A",
  
  "queue": {
    "watch_folders": ["C:\\TestReports"],
    "upload_interval": 10,
    "retry_attempts": 3,
    "retry_delay": 60
  },
  
  "converters": {
    "enabled": ["WATSStandardXMLConverter", "TeradyneICTConverter"],
    "auto_detect": true
  },
  
  "logging": {
    "level": "INFO",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

### CLI Configuration

```bash
# View all settings
pywats-client config show

# Get specific value
pywats-client config get queue.upload_interval

# Set value
pywats-client config set queue.upload_interval 30

# Add watch folder
pywats-client config add-watch-folder "C:\TestReports\Station1"
```

### Environment Variables

Override config via environment:

| Variable | Description |
|----------|-------------|
| `PYWATS_SERVER_URL` | WATS server URL |
| `PYWATS_API_TOKEN` | Auth token |
| `PYWATS_STATION_NAME` | Station identifier |
| `PYWATS_LOG_LEVEL` | Logging level |
| `PYWATS_WATCH_FOLDERS` | Colon-separated paths |

---

## Converters

Converters transform test equipment output into WATS format.

### Built-in Converters

**WATS Standard Formats:**

| Converter | Format | File Patterns |
|-----------|--------|---------------|
| `WATSStandardXMLConverter` | WSXF/WRML | `*.xml` |
| `WATSStandardJsonConverter` | WSJF | `*.json` |
| `WATSStandardTextConverter` | WSTF | `*.txt` |

**Industry Standards:**

| Converter | Standard | File Patterns | Notes |
|-----------|----------|---------------|-------|
| `ATMLConverter` | IEEE ATML (1671/1636.1) | `*.xml`, `*.atml` | ATML 2.02, 5.00, 6.01 + TestStand AddOn |

**Test Equipment:**

| Converter | Equipment | File Patterns |
|-----------|-----------|---------------|
| `TeradyneICTConverter` | Teradyne i3070 | `*.txt`, `*.log` |
| `TeradyneSpectrumICTConverter` | Teradyne Spectrum | `*.txt`, `*.log` |
| `SeicaXMLConverter` | Seica Flying Probe | `*.xml` |
| `KlippelConverter` | Klippel Audio/Acoustic | `*.txt` + data folder |
| `SPEAConverter` | SPEA ATE | `*.txt` |
| `XJTAGConverter` | XJTAG Boundary Scan | `*.zip` |

**Special:**

| Converter | Purpose |
|-----------|---------|
| `AIConverter` | Auto-detects file type and delegates to best matching converter |

### Custom Converters

Place custom converters in the converters folder:

```python
# converters/my_converter.py
from pywats_client.converters import BaseConverter, ConverterInfo
from pywats.report import UUTReport

class MyConverter(BaseConverter):
    @classmethod
    def get_info(cls) -> ConverterInfo:
        return ConverterInfo(
            name="MyConverter",
            description="Converts my test equipment output",
            file_patterns=["*.myext"],
            version="1.0.0"
        )
    
    def convert(self, file_path: str) -> UUTReport:
        # Parse file and create report
        report = UUTReport(
            part_number="...",
            serial_number="...",
            operation_code="TEST",
            result="P"
        )
        return report
```

See [LLM Converter Guide](../llm-converter-guide.md) for detailed examples.

---

## Queue Management

### CLI Commands

```bash
# View queue status
pywats-client queue status

# List pending reports
pywats-client queue list

# Retry failed reports
pywats-client queue retry-failed

# Clear completed reports
pywats-client queue clear-completed

# Manual upload
pywats-client upload --file /path/to/report.xml
```

### Queue API

For programmatic access:

```python
from pywats_client.core.queue import ReportQueue

queue = ReportQueue(config_path)

# Add report
queue.add("path/to/report.xml")

# Get status
status = queue.get_status()
print(f"Pending: {status.pending_count}")

# Process queue
await queue.process_all()
```

---

## Multi-Instance Support

Run separate instances for different stations:

```bash
# Instance 1
pywats-client --instance station1 config init
pywats-client --instance station1 service

# Instance 2
pywats-client --instance station2 config init  
pywats-client --instance station2 service
```

Each instance has separate:
- Configuration file
- Queue folder
- Log file
- Watch folders

---

## Headless Mode

### CLI Control

```bash
# Start foreground
pywats-client start

# Start as daemon (Linux/macOS)
pywats-client start --daemon

# Check status
pywats-client status

# Stop daemon
pywats-client stop

# Restart
pywats-client restart
```

### HTTP API Control

```bash
# Start with HTTP API
pywats-client start --api --api-port 8765
```

Available endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Service status |
| `/queue` | GET | Queue status |
| `/queue/pending` | GET | List pending reports |
| `/restart` | POST | Restart service |
| `/stop` | POST | Stop service |
| `/config` | GET | View configuration |

```bash
# Examples
curl http://localhost:8765/status
curl http://localhost:8765/queue
curl -X POST http://localhost:8765/restart
```

---

## Running as System Service

For production deployments, run as a system service:

- **[Windows Service](windows-service.md)** - NSSM setup, auto-start
- **[Linux Service](linux-service.md)** - Systemd configuration
- **[macOS Service](macos-service.md)** - Launchd daemon
- **[Docker](docker.md)** - Container deployment

---

## Troubleshooting

### Service Won't Start

```bash
# Check Python version
python --version  # Should be 3.10+

# Check installation
pip show pywats-api

# View logs
cat ~/.config/pywats_client/pywats_client.log
```

### Reports Not Uploading

1. **Check connection:**
   ```bash
   pywats-client status
   ```

2. **Check queue:**
   ```bash
   pywats-client queue status
   ```

3. **Enable debug logging:**
   ```bash
   pywats-client config set logging.level DEBUG
   pywats-client restart
   ```

4. **Manual upload test:**
   ```bash
   pywats-client upload --file /path/to/report.xml --verbose
   ```

### Converter Not Detecting Files

1. **Check watch folders:**
   ```bash
   pywats-client config get queue.watch_folders
   ```

2. **Check file patterns:**
   ```bash
   pywats-client converters list
   ```

3. **Test converter manually:**
   ```bash
   pywats-client convert --file /path/to/file.txt --converter MyConverter
   ```

### Finding Configuration

```bash
# Show config path
pywats-client config show --format json | grep config_path

# Or check default locations:
# Windows: %APPDATA%\pyWATS_Client\config.json
# Linux/macOS: ~/.config/pywats_client/config.json
```

---

## Security

### Credential Storage

- Passwords encrypted using platform-specific encryption
- **Windows**: DPAPI (Data Protection API)
- **Linux/macOS**: System keyring or file encryption

### Network Security

- All WATS communication uses HTTPS
- Credentials never logged
- API tokens rotated on password change

### File Permissions

```bash
# Linux/macOS - restrict config access
chmod 600 ~/.config/pywats_client/config.json
```

---

## See Also

- **[API Installation](api.md)** - SDK-only installation
- **[GUI Guide](gui.md)** - Desktop application
- **[../client-architecture.md](../client-architecture.md)** - Architecture details
- **[../llm-converter-guide.md](../llm-converter-guide.md)** - Writing converters
- **[../getting-started.md](../getting-started.md)** - Complete tutorial
