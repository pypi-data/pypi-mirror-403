# PyWATS

[![PyPI version](https://badge.fury.io/py/pywats-api.svg)](https://badge.fury.io/py/pywats-api)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for interacting with the [WATS](https://servername.wats.com) test data management platform API.

> **⚠️ Beta Release**: This is a beta version. The API is stabilizing but may have changes before 1.0.

## Requirements

- **Python 3.10** or later
- **WATS Server 2025.3.9.824** or later

## Features

- **PyWATS Library** - Core API library for WATS integration
  - **Async-First Architecture** - Built on `httpx` with native async support
  - **Sync Compatibility** - Full sync API via thin wrappers (no code changes needed)
  - **9 Domain Services**: Product, Asset, Report, Production, Analytics, Software, RootCause, Process, SCIM
  - **170+ API Endpoints** - Centralized route management
  - Report creation and submission with comprehensive step types
  - OData filtering and pagination support
  - Structured logging with configurable verbosity
  - **Performance Optimizations** ⚡
    - **Enhanced TTL Caching** - Automatic expiration with background cleanup (100x faster cache hits)
    - **Connection Pooling** - HTTP/2 multiplexing with 100 max connections (3-5x faster bulk operations)
    - **Request Batching** - Time-window and size-based batching utilities (95% reduction in server calls)
    - **MessagePack Serialization** - 50% smaller payloads, 3x faster serialization (optional)
  - **Offline Queue** - File-based queue for reliable report submission when offline
    - WSJF format as standard
    - Format conversion from WSXF, WSTF, ATML
    - Automatic retry with configurable max attempts
    - Metadata tracking and statistics

- **PyWATS Client** - Desktop and headless client application
  - Connection management with multi-instance support
  - Converter configuration and management
  - Report queue management
  - **GUI Mode**: Qt-based desktop application (Windows, macOS, Linux)
  - **Service Mode**: Background Windows service or Unix daemon
  - **Headless Mode**: CLI and HTTP API for servers, Raspberry Pi, embedded systems

## Installation

### From PyPI (Recommended)

```bash
# Install core API library only
pip install pywats-api

# Install with GUI client (requires Qt)
pip install pywats-api[client]

# Install headless client (no Qt - for Raspberry Pi, servers)
pip install pywats-api[client-headless]
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/olreppe/pyWATS.git
cd pyWATS

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install in development mode
pip install -e ".[dev]"
```

## Configuration

Create a configuration with your WATS credentials:

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_base64_encoded_token"
)
```

Or use environment variables:

```env
WATS_BASE_URL=https://your-server.wats.com
WATS_AUTH_TOKEN=your_base64_encoded_token
```

## Quick Start

```python
from pywats import pyWATS, WATSFilter

# Initialize API
api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_token"
)

# Test connection
if api.test_connection():
    print(f"Connected! Server version: {api.get_version()}")

# Get products (sync)
products = api.product.get_products()
for p in products:
    print(f"{p.part_number}: {p.name}")
```

### Async Quick Start

For high-performance applications with concurrent requests:

```python
import asyncio
from pywats import AsyncWATS

async def main():
    async with AsyncWATS(
        base_url="https://your-server.wats.com",
        token="your_token"
    ) as api:
        # Concurrent requests - much faster!
        products, assets, version = await asyncio.gather(
            api.product.get_products(),
            api.asset.get_assets(top=10),
            api.analytics.get_version()
        )
        print(f"Fetched {len(products)} products, {len(assets)} assets")

asyncio.run(main())
```

### Performance Optimization Example

Use caching, batching, and connection pooling for high-performance applications:

```python
import asyncio
from pywats import AsyncWATS
from pywats.core.batching import batch_map

async def main():
    async with AsyncWATS(
        base_url="https://your-server.wats.com",
        token="your_token"
    ) as api:
        # Built-in caching for static data (95% reduction in server calls)
        processes = await api.process.get_processes()  # First call - from server
        processes = await api.process.get_processes()  # Second call - from cache (100x faster!)
        
        # Check cache statistics
        stats = api.process.cache_stats
        print(f"Cache hit rate: {stats['hit_rate']:.1%}")
        
        # Batch processing with automatic concurrency control
        serial_numbers = [f"SN-{i:05d}" for i in range(1000)]
        
        async def fetch_unit(sn: str):
            return await api.production.get_unit(sn, "WIDGET-001")
        
        # Process 1000 units in batches (5-10x faster than sequential)
        units = await batch_map(
            items=serial_numbers,
            func=fetch_unit,
            batch_size=50,
            max_concurrent=10
        )
        print(f"Processed {len(units)} units")

asyncio.run(main())
```

See [PERFORMANCE_OPTIMIZATIONS.md](docs/PERFORMANCE_OPTIMIZATIONS.md) for complete guide.

### Query Reports

```python
# Query recent reports (OData filter)
headers = api.report.query_uut_headers(
    odata_filter="partNumber eq 'WIDGET-001'",
    top=10
)

# Or use helper methods
headers = api.report.get_headers_by_serial("SN-12345")
headers = api.report.get_todays_headers()
```

### Enable Debug Logging

```python
from pywats import pyWATS, enable_debug_logging

# Quick debug mode - shows all library operations
enable_debug_logging()

# Or configure logging your way
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('pywats').setLevel(logging.DEBUG)

# Now use the API with detailed logging
api = pyWATS(base_url="...", token="...")
```

See [LOGGING_STRATEGY.md](LOGGING_STRATEGY.md) for comprehensive logging documentation.

## Running the GUI Client

**Important:** The GUI is for configuration only. You must run the service first:

```bash
# Start the background service (runs 24/7)
python -m pywats_client service --instance-id default

# Then launch GUI for configuration (in a separate terminal)
python -m pywats_client gui --instance-id default
```

**Or simply run:**
```bash
# Default behavior: starts service
python -m pywats_client

# Then launch GUI when needed
python -m pywats_client gui
```

### Service Installation (Production)

For production deployments, install pyWATS as a system service that auto-starts on boot:

**Windows:**
```bash
# Install as Windows Service (requires admin)
python -m pywats_client install-service
net start pyWATS_Service
```

**Linux (systemd):**
```bash
# Install as systemd service (requires sudo)
sudo python3 -m pywats_client install-service
sudo systemctl start pywats-service
```

**macOS:**
```bash
# Install as Launch Daemon (requires sudo)
sudo python3 -m pywats_client install-service

# Or as user-level Launch Agent (no sudo)
python3 -m pywats_client install-service --user-agent
```

See platform-specific guides:
- [Windows Service Setup](docs/WINDOWS_SERVICE.md) - NSSM/sc.exe installation
- [Linux Service Setup](docs/LINUX_SERVICE.md) - systemd for Ubuntu/Debian/RHEL
- [macOS Service Setup](docs/MACOS_SERVICE.md) - launchd daemon/agent

### GUI Configuration

The GUI supports modular tab configuration and logging control:

- **Tab Visibility**: Show/hide tabs (Software, SN Handler, etc.) based on your needs
- **Logging Integration**: Automatic PyWATS library logging when debug mode is enabled
- **Multiple Instances**: Run multiple client instances with separate configurations
- **Service Discovery**: Automatically discovers and connects to running service instances

See [GUI Configuration Guide](src/pywats_client/GUI_CONFIGURATION.md) for detailed setup instructions.

## Running Headless (Raspberry Pi, Servers)

For systems without display or Qt support:

```bash
# Initialize configuration
pywats-client config init

# Test connection
pywats-client test-connection

# Run service in foreground
python -m pywats_client service

# Run with HTTP control API
python -m pywats_client service --api --api-port 8765

# Install as system service (auto-start on boot)
sudo python3 -m pywats_client install-service
```

### CLI Commands

```bash
pywats-client config show          # Show configuration
pywats-client config set key value # Set config value
pywats-client status               # Show service status
pywats-client converters list      # List converters
```

### HTTP Control API

When running with `--api`, manage the service remotely:

```bash
curl http://localhost:8765/status    # Get status
curl http://localhost:8765/config    # Get configuration
curl -X POST http://localhost:8765/restart  # Restart services
```

See [Headless Operation Guide](src/pywats_client/control/HEADLESS_GUIDE.md) for complete documentation.

## Project Structure

```
pyWATS/
├── src/
│   ├── pywats/              # Core library
│   │   ├── domains/         # Domain services (async + sync wrappers)
│   │   │   ├── analytics/   # Statistics, yield, Unit Flow
│   │   │   ├── asset/       # Equipment tracking, calibration
│   │   │   ├── process/     # Operation types, caching
│   │   │   ├── product/     # Products, revisions, BOMs
│   │   │   ├── production/  # Serial numbers, unit lifecycle
│   │   │   ├── report/      # Test reports, measurements
│   │   │   ├── rootcause/   # Issue tracking, defects
│   │   │   ├── scim/        # User provisioning
│   │   │   └── software/    # Package distribution
│   │   ├── core/            # HTTP client, routes, sync_runner
│   │   ├── models/          # Report models (UUT/UUR)
│   │   ├── async_wats.py    # AsyncWATS main class
│   │   └── sync_wats.py     # SyncWATS wrapper (pyWATS alias)
│   └── pywats_client/       # Client application
│       ├── core/            # Core client functionality
│       ├── gui/             # Qt GUI components (optional)
│       ├── control/         # Headless control (CLI, HTTP API)
│       └── services/        # Background services
├── converters/              # User converter plugins
├── docs/                    # Documentation
├── examples/                # Usage examples by domain
└── pyproject.toml           # Project configuration
```

## Documentation

### Official Documentation

Complete guides shipped with the package:

- **[Documentation Index](docs/INDEX.md)** - Complete documentation overview

#### Domain API Reference

- **[Product Domain](docs/PRODUCT.md)** - Products, revisions, BOMs, box build templates
- **[Asset Domain](docs/ASSET.md)** - Equipment tracking, calibration, maintenance  
- **[Production Domain](docs/PRODUCTION.md)** - Unit lifecycle, serial numbers, assembly
- **[Report Domain](docs/REPORT.md)** - Test reports, measurements, step types
- **[Analytics Domain](docs/ANALYTICS.md)** - Yield analysis, measurements, Unit Flow
- **[Software Domain](docs/SOFTWARE.md)** - Package management, versioning, distribution
- **[RootCause Domain](docs/ROOTCAUSE.md)** - Issue tracking, defect management
- **[Process Domain](docs/PROCESS.md)** - Operation types, caching

#### Client Documentation

- **[GUI Configuration](src/pywats_client/GUI_CONFIGURATION.md)** - Configure GUI tabs, logging
- **[Headless Operation](src/pywats_client/control/HEADLESS_GUIDE.md)** - Raspberry Pi, servers, embedded

### Additional Resources

Documentation available in the GitHub repository (not shipped with package):

- [Internal Documentation](docs/internal/) - Architecture, design docs, AI agent knowledge
- [Internal: Architecture Overview](docs/internal/ARCHITECTURE.md) - System design and architecture
- [Internal: WATS Domain Knowledge](docs/internal/WATS_DOMAIN_KNOWLEDGE.md) - Core WATS concepts
- [Logging Strategy](LOGGING_STRATEGY.md) - Logging configuration and best practices

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Contributing

This project is maintained by [Virinco AS](https://virinco.com).

### For Maintainers: Releasing a New Beta Version

**There is only ONE command to release:**

```powershell
.\scripts\bump.ps1
```

See [RELEASE.md](RELEASE.md) for complete details. Never manually edit versions or create tags.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [WATS Website](https://wats.com)
- [Virinco](https://virinco.com)
- [GitHub Repository](https://github.com/olreppe/pyWATS)
- [Changelog](CHANGELOG.md)
