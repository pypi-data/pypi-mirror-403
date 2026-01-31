# Platform Compatibility Guide

> **Last Updated**: January 29, 2026  
> **pyWATS Version**: 0.2.0b1 (Beta)

This document describes the supported platforms, deployment modes, and compatibility considerations for pyWATS.

---

## Quick Compatibility Matrix

| Platform | Library | Client GUI | Client Headless | Service/Daemon |
|----------|---------|------------|-----------------|----------------|
| **Windows 10/11** | ✅ Full | ✅ Full | ✅ Full | ✅ Native Service |
| **Windows Server 2019/2022** | ✅ Full | ⚠️ GUI may require features | ✅ Full | ✅ Native Service |
| **Windows IoT Enterprise LTSC** | ✅ Full | ⚠️ UWF workarounds | ✅ Full | ✅ Native Service |
| **Ubuntu 22.04/24.04 LTS** | ✅ Full | ✅ Full | ✅ Full | ✅ systemd |
| **Debian 11/12** | ✅ Full | ✅ Full | ✅ Full | ✅ systemd |
| **RHEL 8/9** | ✅ Full | ✅ Full | ✅ Full | ✅ systemd + SELinux |
| **Rocky Linux 8/9** | ✅ Full | ✅ Full | ✅ Full | ✅ systemd + SELinux |
| **AlmaLinux 8/9** | ✅ Full | ✅ Full | ✅ Full | ✅ systemd + SELinux |
| **macOS 12+ (Monterey+)** | ✅ Full | ✅ Full | ✅ Full | ✅ launchd |
| **Raspberry Pi OS (64-bit)** | ✅ Full | ⚠️ Qt may be slow | ✅ Recommended | ✅ systemd |
| **Docker** | ✅ Full | ❌ No GUI | ✅ Full | ✅ Container |
| **Kubernetes** | ✅ Full | ❌ No GUI | ✅ Full | ✅ Pod |

**Legend:**
- ✅ **Full** - Fully supported and tested
- ⚠️ **Limited** - Works with noted limitations
- ❌ **No** - Not supported for this platform

---

## Detailed Platform Support

### Windows

#### Windows 10/11 Professional/Enterprise
**Status**: ✅ Primary development platform

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| GUI Client | ✅ Full (Qt6) |
| Headless Client | ✅ Full |
| Windows Service | ✅ Native with pywin32 |
| Pre-shutdown Handling | ✅ SERVICE_CONTROL_PRESHUTDOWN |
| Event Log Integration | ✅ Windows Event Log |
| Auto-start on Boot | ✅ Delayed Auto-Start |
| Auto-recovery on Crash | ✅ Service Recovery Options |

**Requirements:**
- Python 3.10+ (64-bit recommended)
- Visual C++ Redistributable 2019+
- Administrator rights for service installation

**Installation:**
```powershell
pip install pywats-api[client]
pywats-client install-service
```

#### Windows Server 2019/2022
**Status**: ✅ Fully supported

Same as Windows 10/11 with additional notes:
- Server Core: Use headless mode (`pywats-api[client-headless]`)
- Desktop Experience: Full GUI available
- Remote Desktop: GUI works over RDP

#### Windows IoT Enterprise LTSC (2019/2021)
**Status**: ⚠️ Supported with workarounds

**Special Considerations:**
- **Unified Write Filter (UWF)**: Add exclusions for config directories
- **AppLocker**: Create exception rules for Python and pyWATS
- **Windows Defender**: Add exclusions for performance

See [WINDOWS_IOT_LTSC.md](WINDOWS_IOT_LTSC.md) for detailed setup guide.

---

### Linux

#### Ubuntu 22.04/24.04 LTS
**Status**: ✅ Primary Linux platform

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| GUI Client | ✅ Full (Qt6) |
| Headless Client | ✅ Full |
| systemd Service | ✅ Full integration |
| Health Endpoint | ✅ HTTP /health |
| DEB Package | ✅ Available |
| Unattended Install | ✅ dpkg + debconf |

**Requirements:**
- Python 3.10+ (ships with 22.04+)
- libxcb and Qt dependencies for GUI
- systemd for service mode

**Installation (PyPI):**
```bash
sudo apt update
sudo apt install python3-pip python3-venv
pip install pywats-api[client-headless]
```

**Installation (DEB Package):**
```bash
sudo dpkg -i pywats-client_*.deb
sudo systemctl enable pywats-client
sudo systemctl start pywats-client
```

#### Debian 11 (Bullseye) / 12 (Bookworm)
**Status**: ✅ Fully supported

Same as Ubuntu with Debian-specific notes:
- Debian 11: Python 3.9 (upgrade to 3.10+ required)
- Debian 12: Python 3.11 (native support)

#### RHEL 8/9, Rocky Linux 8/9, AlmaLinux 8/9
**Status**: ✅ Fully supported (SELinux-ready)

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| GUI Client | ✅ Full (Qt6) |
| Headless Client | ✅ Full |
| systemd Service | ✅ Full integration |
| SELinux | ✅ Policy module included |
| RPM Package | ✅ Available |
| FIPS Mode | ⚠️ May require OpenSSL config |

**Requirements:**
- Python 3.9+ (RHEL 8) or 3.11+ (RHEL 9)
- EPEL repository for additional dependencies
- SELinux in enforcing mode supported

**Installation (PyPI):**
```bash
sudo dnf install python3 python3-pip
pip install pywats-api[client-headless]
```

**Installation (RPM Package):**
```bash
sudo rpm -i pywats-client-*.rpm
sudo systemctl enable pywats-client
sudo systemctl start pywats-client
```

**SELinux Setup:**
```bash
cd selinux/
sudo ./install-selinux.sh
```

---

### macOS

#### macOS 12+ (Monterey, Ventura, Sonoma, Sequoia)
**Status**: ✅ Fully supported

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| GUI Client | ✅ Full (Qt6) |
| Headless Client | ✅ Full |
| launchd Service | ✅ Full integration |
| Apple Silicon (M1/M2/M3) | ✅ Native ARM64 |
| Intel | ✅ x86_64 |

**Requirements:**
- Python 3.10+ (Homebrew recommended)
- Xcode Command Line Tools
- Code signing for Gatekeeper (optional)

**Installation:**
```bash
brew install python@3.12
pip install pywats-api[client]
```

See [MACOS_SERVICE.md](MACOS_SERVICE.md) for launchd setup.

---

### Embedded / IoT

#### Raspberry Pi 4/5 (64-bit OS)
**Status**: ✅ Recommended for headless

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| GUI Client | ⚠️ Works but slow |
| Headless Client | ✅ Recommended |
| systemd Service | ✅ Full integration |

**Notes:**
- Use 64-bit Raspberry Pi OS
- Headless mode recommended for performance
- 4GB+ RAM recommended for GUI

**Installation:**
```bash
pip install pywats-api[client-headless]
```

See [HEADLESS_GUIDE.md](src/pywats_client/control/HEADLESS_GUIDE.md) for embedded setup.

---

### Containers

#### Docker
**Status**: ✅ Production-ready

| Feature | Support Level |
|---------|---------------|
| pyWATS Library | ✅ Full |
| Headless Client | ✅ Full |
| Multi-arch | ✅ amd64 + arm64 |
| Health Checks | ✅ HTTP /health |
| Security Scanning | ✅ Trivy in CI |

**Images Available:**
- `ghcr.io/olreppe/pywats-api:latest` - API library only
- `ghcr.io/olreppe/pywats-client:latest` - Headless client

**Quick Start:**
```bash
docker run -d \
  -e PYWATS_SERVER_URL=https://your-server.wats.com \
  -e PYWATS_API_TOKEN=your-token \
  -v /reports:/app/reports \
  ghcr.io/olreppe/pywats-client:latest
```

See [DOCKER.md](DOCKER.md) for complete container guide.

#### Kubernetes
**Status**: ✅ Production-ready

- Horizontal Pod Autoscaler support
- Liveness/Readiness probes via /health endpoint
- ConfigMap/Secret for configuration
- Persistent Volume Claims for report storage

---

### Virtual Machine Appliance
**Status**: ✅ Available

Pre-built appliance for easy deployment:

| Format | Use Case |
|--------|----------|
| OVA | VMware ESXi, vSphere, VirtualBox |
| QCOW2 | KVM, Proxmox, OpenStack |
| VHD | Hyper-V, Azure |

**Features:**
- Ubuntu 22.04 LTS base
- pyWATS pre-installed
- First-boot configuration wizard
- Automatic updates via apt

---

## Python Version Support

| Python Version | Support Status |
|---------------|----------------|
| 3.9 | ⚠️ Deprecated (works, not tested) |
| 3.10 | ✅ Minimum supported |
| 3.11 | ✅ Recommended |
| 3.12 | ✅ Full support |
| 3.13 | ⚠️ Untested (expected to work) |

---

## Architecture Support

| Architecture | Library | Client |
|-------------|---------|--------|
| x86_64 (AMD64) | ✅ Full | ✅ Full |
| ARM64 (AArch64) | ✅ Full | ✅ Full |
| ARM32 | ⚠️ Should work | ❌ Not tested |

---

## Network Requirements

### Outbound Connections

| Destination | Port | Protocol | Purpose |
|-------------|------|----------|---------|
| WATS Server | 443 | HTTPS | API communication |
| PyPI | 443 | HTTPS | Package installation |
| GitHub | 443 | HTTPS | Updates (optional) |

### Inbound Connections (Optional)

| Port | Protocol | Purpose |
|------|----------|---------|
| 8080 | HTTP | Health endpoint |
| 8765 | HTTP | Control API (headless) |

### Proxy Support

pyWATS supports HTTP/HTTPS proxies via environment variables:
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1,.internal.domain
```

---

## WATS Server Compatibility

| WATS Server Version | pyWATS Support |
|--------------------|----------------|
| < 2025.3.9.824 | ❌ Not supported |
| 2025.3.9.824+ | ✅ Full support |
| 2026.x | ✅ Full support |

---

## Related Documentation

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Getting Started](GETTING_STARTED.md) - Quick start tutorial
- [Docker Guide](DOCKER.md) - Container deployment
- [Windows IoT LTSC](WINDOWS_IOT_LTSC.md) - IoT-specific guidance
- [Linux Service](LINUX_SERVICE.md) - systemd configuration
- [macOS Service](MACOS_SERVICE.md) - launchd configuration
- [Headless Guide](src/pywats_client/control/HEADLESS_GUIDE.md) - Embedded/server deployment
