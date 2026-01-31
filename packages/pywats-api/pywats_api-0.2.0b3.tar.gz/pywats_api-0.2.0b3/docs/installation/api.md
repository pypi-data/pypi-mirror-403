# PyWATS API Installation

Install the core PyWATS API library for direct integration with WATS from your Python applications.

## Overview

The API package provides:
- Python SDK for all WATS domains (Report, Product, Production, Asset, etc.)
- Sync and async client support
- Data validation with Pydantic 2.0+
- No GUI dependencies

**Best for:** Scripts, automation, server-side integrations, custom applications.

---

## Installation

```bash
pip install pywats-api
```

**Requirements:**
- Python 3.10+
- ~5 MB disk space

**Dependencies (automatically installed):**
- `httpx` - HTTP client
- `pydantic` - Data validation
- `python-dateutil` - Date utilities

---

## Quick Start

### Basic Connection

```python
from pywats import pyWATS

# Initialize client
api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_base64_encoded_token"
)

# Test connection
if api.test_connection():
    print("Connected to WATS!")
```

### Using Environment Variables

Set credentials once, use everywhere:

```bash
# Windows
set PYWATS_SERVER_URL=https://your-server.wats.com
set PYWATS_API_TOKEN=your_base64_encoded_token

# Linux/macOS
export PYWATS_SERVER_URL=https://your-server.wats.com
export PYWATS_API_TOKEN=your_base64_encoded_token
```

Then in Python:

```python
from pywats import pyWATS

# Reads from environment automatically
api = pyWATS()
```

### Async Client

For high-performance applications:

```python
import asyncio
from pywats import pyWATS

async def main():
    async with pyWATS(async_mode=True) as api:
        products = await api.product.get_products()
        print(f"Found {len(products)} products")

asyncio.run(main())
```

---

## API Domains

The API is organized into domain modules:

| Domain | Import | Use Case |
|--------|--------|----------|
| **Report** | `api.report` | Create/query test reports (UUT/UUR) |
| **Product** | `api.product` | Manage products, revisions, BOMs |
| **Production** | `api.production` | Serial numbers, unit lifecycle |
| **Asset** | `api.asset` | Equipment tracking, calibration |
| **Analytics** | `api.analytics` | Yield analysis, statistics |
| **Software** | `api.software` | Package distribution |
| **RootCause** | `api.rootcause` | Issue tracking, defects |
| **Process** | `api.process` | Operation types, processes |
| **SCIM** | `api.scim` | User provisioning |

### Example: Create a Test Report

```python
from pywats import pyWATS
from pywats.report import UUTReport

api = pyWATS()

# Create report
report = UUTReport(
    part_number="PCB-001",
    serial_number="SN12345",
    operation_code="ICT",
    result="P"
)

# Add a numeric measurement
report.add_numeric_limit_step(
    name="Voltage Check",
    value=3.3,
    low_limit=3.0,
    high_limit=3.6,
    unit="V"
)

# Submit
result = api.report.submit_uut_report(report)
print(f"Report ID: {result.id}")
```

---

## Authentication

### Token Generation

1. Log into WATS web interface
2. Navigate to **Settings → API Access**
3. Generate a new API token
4. Copy the base64-encoded token

### Token Format

The token is a base64-encoded string containing your credentials:

```python
import base64

# Create token from username:password
credentials = "username:password"
token = base64.b64encode(credentials.encode()).decode()
print(token)  # dXNlcm5hbWU6cGFzc3dvcmQ=
```

---

## Configuration Options

### Client Initialization

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-server.wats.com",  # WATS server URL
    token="...",                               # Auth token
    timeout=30,                                # Request timeout (seconds)
    verify_ssl=True,                           # SSL certificate verification
    async_mode=False,                          # Use async client
)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYWATS_SERVER_URL` | WATS server base URL | Required |
| `PYWATS_API_TOKEN` | Base64-encoded auth token | Required |
| `PYWATS_TIMEOUT` | Request timeout (seconds) | 30 |
| `PYWATS_VERIFY_SSL` | Verify SSL certificates | true |
| `PYWATS_LOG_LEVEL` | Logging level | INFO |

---

## Upgrading

```bash
pip install --upgrade pywats-api
```

Check current version:

```bash
pip show pywats-api
```

Or in Python:

```python
import pywats
print(pywats.__version__)
```

---

## Troubleshooting

### Import Errors

```bash
# Verify installation
pip show pywats-api

# Check Python version
python --version  # Should be 3.10+

# Reinstall
pip uninstall pywats-api
pip install pywats-api
```

### Connection Issues

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_token"
)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection
try:
    api.test_connection()
except Exception as e:
    print(f"Connection failed: {e}")
```

### SSL Certificate Errors

For development/testing only:

```python
api = pyWATS(
    base_url="https://...",
    token="...",
    verify_ssl=False  # ⚠️ Not for production!
)
```

---

## Next Steps

- **[Getting Started Guide](../getting-started.md)** - Comprehensive tutorial
- **[Quick Reference](../quick-reference.md)** - Common patterns and snippets
- **[Domain Documentation](../domains/)** - Detailed API reference

---

## Need More?

| If you need... | Install... | Guide |
|----------------|------------|-------|
| Background service with queue | `pip install pywats-api[client-headless]` | [Service Guide](client.md) |
| Desktop GUI for monitoring | `pip install pywats-api[client]` | [GUI Guide](gui.md) |
| Development tools | `pip install pywats-api[dev]` | [Getting Started](../getting-started.md) |

---

## See Also

- **[../INDEX.md](../INDEX.md)** - Main documentation index
- **[../architecture.md](../architecture.md)** - System architecture overview
- **[../env-variables.md](../env-variables.md)** - Environment variable reference
