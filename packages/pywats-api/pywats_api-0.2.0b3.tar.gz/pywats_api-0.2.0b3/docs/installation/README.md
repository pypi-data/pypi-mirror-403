# Installation & Deployment Documentation

This directory contains guides for installing PyWATS components and deploying the client service.

## 🎯 What Do You Need?

Use this decision tree to find the right installation guide:

```
What are you building?
│
├─► Python scripts/automation → API Only
│   └─ Install: pip install pywats-api
│   └─ Guide: api.md
│
├─► Test station with queue/converters
│   │
│   ├─► With monitoring GUI → Client + GUI
│   │   └─ Install: pip install pywats-api[client]
│   │   └─ Guides: client.md + gui.md
│   │
│   └─► Headless/server → Client Service
│       └─ Install: pip install pywats-api[client-headless]
│       └─ Guide: client.md
│
└─► Production deployment → System Service
    └─ Choose your platform:
        ├─ Windows: windows-service.md
        ├─ Linux: linux-service.md
        ├─ macOS: macos-service.md
        └─ Docker: docker.md
```

---

## 📦 Installation by Component

### API Library

**[API Installation](api.md)** - Python SDK for direct WATS integration
- pip package only (~5 MB)
- No background services
- Use from scripts and applications

```bash
pip install pywats-api
```

### Client Service

**[Client Service](client.md)** - Background service with queue and converters
- Report queue with retry
- File watching and converters
- Offline support

```bash
# With GUI
pip install pywats-api[client]

# Headless (no GUI)
pip install pywats-api[client-headless]
```

### GUI Application

**[GUI Application](gui.md)** - Desktop app for monitoring and configuration
- Real-time queue monitoring
- Configuration interface
- Log viewer

```bash
pip install pywats-api[client]
```

---

## 🖥️ Service Deployment

Install the client as a system service for automatic startup:

| Platform | Guide | Method |
|----------|-------|--------|
| **Windows** | [windows-service.md](windows-service.md) | Native Service / NSSM |
| **Linux** | [linux-service.md](linux-service.md) | systemd |
| **macOS** | [macos-service.md](macos-service.md) | launchd |
| **Docker** | [docker.md](docker.md) | Container |

---

## 📦 Native Installers

Pre-built installers are available for systems without Python:

| Platform | Format | Download |
|----------|--------|----------|
| **Windows** | `.msi` | [GitHub Releases](https://github.com/olreppe/pyWATS/releases) |
| **macOS** | `.dmg` / `.pkg` | [GitHub Releases](https://github.com/olreppe/pyWATS/releases) |
| **Ubuntu/Debian** | `.deb` | [GitHub Releases](https://github.com/olreppe/pyWATS/releases) |
| **RHEL/Rocky/Alma** | `.rpm` | [GitHub Releases](https://github.com/olreppe/pyWATS/releases) |
| **Linux (any)** | AppImage | [GitHub Releases](https://github.com/olreppe/pyWATS/releases) |

**Building from source:** See [deployment/README.md](../../deployment/README.md)

---

## 📊 Quick Comparison

| Feature | API Only | Client Headless | Client + GUI |
|---------|----------|-----------------|--------------|
| **Size** | ~5 MB | ~8 MB | ~150 MB |
| **Python SDK** | ✓ | ✓ | ✓ |
| **Report Queue** | - | ✓ | ✓ |
| **Converters** | - | ✓ | ✓ |
| **File Watching** | - | ✓ | ✓ |
| **GUI** | - | - | ✓ |
| **Use Case** | Scripts | Servers, Pi | Desktop |

---

## 🚀 Quick Start

### Developers/Integrators

```bash
pip install pywats-api
```

```python
from pywats import pyWATS
api = pyWATS(base_url="...", token="...")
```

### Test Stations (Desktop)

```bash
pip install pywats-api[client]
python -m pywats_client service
python -m pywats_client gui  # In another terminal
```

### Test Stations (Headless)

```bash
pip install pywats-api[client-headless]
pywats-client config init
pywats-client start
```

---

## See Also

- **[../INDEX.md](../INDEX.md)** - Main documentation index
- **[../getting-started.md](../getting-started.md)** - Complete tutorial
- **[../client-architecture.md](../client-architecture.md)** - Client service internals
- **[../env-variables.md](../env-variables.md)** - Environment variable reference
